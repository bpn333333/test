/*
 * rdcontrol クライアント。
 *
 * - サーバーから届く JPEG バイナリを canvas に描画する
 * - canvas 上のマウス操作とキー入力を正規化してサーバーへ送る
 *
 * 座標は常に 0.0〜1.0 に正規化して送る。こうしておくと、送信解像度を
 * 途中で変えてもサーバー側の座標計算が変わらない。
 */
(() => {
  "use strict";

  const token = new URLSearchParams(location.search).get("token") || "";
  const el = (id) => document.getElementById(id);

  const canvas = el("screen");
  const ctx = canvas.getContext("2d", { alpha: false });
  const stage = el("stage");
  const overlay = el("overlay");
  const statusEl = el("status");
  const modeEl = el("mode");
  const statsEl = el("stats");
  const monitorSel = el("monitor");
  const keyboardToggle = el("keyboardToggle");
  const cursorEl = el("cursor");
  const softInput = el("softInput");
  const softKeyboardButton = el("softKeyboard");
  const zoomResetButton = el("zoomReset");
  const panModeButton = el("panMode");
  const audioButton = el("audioToggle");
  const fullscreenButton = el("fullscreen");
  const exitImmersiveButton = el("exitImmersive");

  const FRAME_TAG = 1;
  const AUDIO_TAG = 2;
  const AUDIO_RATE = 24000;          // サーバーが送ってくる音の標本化周波数

  const MOUSE_MOVE_INTERVAL_MS = 33; // 約 30 回/秒に間引く
  const BUTTONS = ["left", "middle", "right"];

  let socket = null;
  let connected = false;
  let canControl = false;
  let reconnectDelay = 500;
  let keyboardEnabled = false;
  let lastMoveSent = 0;
  let pendingMove = null;
  let framesInWindow = 0;
  let bytesInWindow = 0;
  let remoteCursor = null;   // サーバーから届いた実際のカーソル位置(正規化)

  /* ---------- 接続 ---------- */

  function connect() {
    const scheme = location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${scheme}://${location.host}/ws?token=${encodeURIComponent(token)}`);
    socket.binaryType = "arraybuffer";

    socket.addEventListener("open", () => {
      connected = true;
      reconnectDelay = 500;
      setStatus("接続済み", "ok");
    });

    socket.addEventListener("message", (event) => {
      if (typeof event.data === "string") {
        handleControlMessage(JSON.parse(event.data));
        return;
      }
      // バイナリは先頭 1 バイトが種別(1 = 画面、2 = 音声)
      const kind = new Uint8Array(event.data, 0, 1)[0];
      const body = event.data.slice(1);
      if (kind === FRAME_TAG) {
        drawFrame(body);
      } else if (kind === AUDIO_TAG) {
        playAudio(body);
      }
    });

    socket.addEventListener("close", (event) => {
      connected = false;
      canControl = false;
      releaseLocalState();
      if (event.code === 4401) {
        setStatus("認証に失敗しました", "err");
        showOverlay("トークンが正しくありません。\nサーバー起動時に表示された URL を開き直してください。");
        return; // 再接続しても無駄なので止める
      }
      if (event.code === 4429) {
        setStatus("接続数が上限に達しています", "err");
        showOverlay("同時接続数の上限に達しました。他のタブを閉じてから再読み込みしてください。");
        return;
      }
      setStatus("切断されました。再接続します…", "err");
      showOverlay("切断されました。再接続しています…");
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 10000);
    });

    socket.addEventListener("error", () => setStatus("通信エラー", "err"));
  }

  function send(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  }

  function handleControlMessage(message) {
    switch (message.t) {
      case "hello":
        canControl = message.has_control && !message.view_only;
        modeEl.hidden = canControl;
        stage.classList.toggle("stage--viewonly", !canControl);
        if (message.input_error) {
          modeEl.title = message.input_error;
        }
        audioButton.hidden = message.audio === false;
        fillMonitors(message.monitors, message.monitor);
        el("quality").value = message.quality;
        el("fps").value = message.fps;
        el("scale").value = Math.round(message.scale * 100);
        syncOutputs();
        break;
      case "config":
        el("quality").value = message.quality;
        el("fps").value = message.fps;
        el("scale").value = Math.round(message.scale * 100);
        monitorSel.value = String(message.monitor);
        syncOutputs();
        break;
      case "monitors":
        // PC 側でディスプレイの数や解像度が変わった
        fillMonitors(message.monitors, message.monitor);
        setStatus("ディスプレイの構成が変わりました", "ok");
        break;
      case "audio":
        audioButton.setAttribute("aria-pressed", String(Boolean(message.enabled)));
        if (!message.enabled && message.message) {
          setStatus(`音声を再生できません: ${message.message}`, "err");
          if (audioContext) audioContext.suspend();
        }
        break;
      case "cursor":
        // 画面キャプチャにポインタは写らないため、位置を受け取って重ねて描く
        remoteCursor = message.visible ? { x: message.x, y: message.y } : null;
        placeCursor();
        break;
      case "error":
        setStatus(message.message, "err");
        break;
      default:
        break;
    }
  }

  /* ---------- 描画 ---------- */

  function drawFrame(buffer) {
    const blob = new Blob([buffer], { type: "image/jpeg" });
    createImageBitmap(blob)
      .then((bitmap) => {
        if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
          canvas.width = bitmap.width;
          canvas.height = bitmap.height;
        }
        ctx.drawImage(bitmap, 0, 0);
        bitmap.close();
        overlay.hidden = true;
        placeCursor();   // 解像度が変わるとカーソルの位置もずれる
        framesInWindow += 1;
        bytesInWindow += buffer.byteLength;
      })
      .catch(() => {
        /* 壊れたフレームは黙って捨てて次を待つ */
      });
  }

  setInterval(() => {
    if (!connected) {
      statsEl.textContent = "—";
      return;
    }
    const kbps = Math.round((bytesInWindow * 8) / 1000);
    statsEl.textContent = `${framesInWindow} fps / ${kbps} kbps`;
    framesInWindow = 0;
    bytesInWindow = 0;
  }, 1000);

  /* ---------- 音声の再生 ---------- */

  // iOS は「利用者の操作の中で」音の再生を始めないと鳴らないため、ボタン経由で開始する。
  let audioContext = null;
  let audioPlayHead = 0;      // 次のかたまりを鳴らし始める時刻

  async function startAudio() {
    if (!audioContext) {
      const AudioCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtor) {
        setStatus("このブラウザは音声再生に対応していません", "err");
        return false;
      }
      audioContext = new AudioCtor();
    }
    await audioContext.resume();
    audioPlayHead = 0;
    send({ t: "audio", enabled: true });
    return true;
  }

  function stopAudio() {
    send({ t: "audio", enabled: false });
    if (audioContext) audioContext.suspend();
  }

  function playAudio(buffer) {
    if (!audioContext || audioContext.state !== "running") return;
    const pcm = new Int16Array(buffer);
    if (pcm.length === 0) return;

    // 標本化周波数を指定して作れば、端末側が自動で合わせて再生する
    const audioBuffer = audioContext.createBuffer(1, pcm.length, AUDIO_RATE);
    const channel = audioBuffer.getChannelData(0);
    for (let i = 0; i < pcm.length; i += 1) {
      channel[i] = pcm[i] / 32768;
    }
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    // 少し先に置いて鳴らす。通信の揺らぎで途切れるのを防ぐ。
    const now = audioContext.currentTime;
    if (audioPlayHead < now + 0.02) {
      audioPlayHead = now + 0.12;
    }
    source.start(audioPlayHead);
    audioPlayHead += audioBuffer.duration;
  }

  audioButton.addEventListener("click", async () => {
    const turningOn = audioButton.getAttribute("aria-pressed") !== "true";
    if (turningOn) {
      if (await startAudio()) audioButton.setAttribute("aria-pressed", "true");
    } else {
      stopAudio();
      audioButton.setAttribute("aria-pressed", "false");
    }
  });

  /* ---------- 表示の拡大・移動 ---------- */

  // 画面そのものは canvas の CSS transform で拡大する。サーバーへ送る座標は
  // getBoundingClientRect() から計算しており、これは transform 後の位置を返すため、
  // 拡大しても操作位置の計算は変えなくてよい。
  const MIN_ZOOM = 1;
  const MAX_ZOOM = 5;

  let zoom = 1;
  let panX = 0;
  let panY = 0;

  function layoutBox() {
    // transform を適用する前の(レイアウト上の)位置と大きさ
    return {
      left: canvas.offsetLeft,
      top: canvas.offsetTop,
      width: canvas.offsetWidth,
      height: canvas.offsetHeight,
    };
  }

  function clampPan() {
    const box = layoutBox();
    const stageRect = stage.getBoundingClientRect();
    const scaledWidth = box.width * zoom;
    const scaledHeight = box.height * zoom;

    // 拡大した画像の端が表示領域の内側に入り込まないように、移動量を制限する
    // (右端・下端が画面の端より内側に来たら、それ以上は動かさない)
    const minX = Math.min(0, stageRect.width - box.left - scaledWidth);
    const minY = Math.min(0, stageRect.height - box.top - scaledHeight);
    panX = Math.min(0, Math.max(minX, panX));
    panY = Math.min(0, Math.max(minY, panY));
  }

  function applyTransform() {
    if (zoom === 1) {
      panX = 0;
      panY = 0;
    } else {
      clampPan();
    }
    canvas.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    zoomResetButton.textContent = `⤢ ${Math.round(zoom * 100)}%`;
    placeCursor();
  }

  function setZoom(nextZoom, anchorClientX, anchorClientY) {
    const clamped = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, nextZoom));
    if (clamped === zoom) return;

    const box = layoutBox();
    const stageRect = stage.getBoundingClientRect();
    // 指の位置(anchor)にある画像上の点が動かないように移動量を調整する
    const originX = stageRect.left + box.left;
    const originY = stageRect.top + box.top;
    const localX = (anchorClientX - originX - panX) / zoom;
    const localY = (anchorClientY - originY - panY) / zoom;

    zoom = clamped;
    panX = anchorClientX - originX - localX * zoom;
    panY = anchorClientY - originY - localY * zoom;
    applyTransform();
  }

  function resetZoom() {
    zoom = 1;
    applyTransform();
  }

  // Safari(WebKit)はピンチ操作を独自の gesture イベントとして扱い、
  // ページ自体の拡大に使ってしまう。こちらで受け取って打ち消し、
  // 表示の拡大に振り向ける。event.scale は操作開始時を 1 とした倍率。
  const hasGestureEvents = typeof window.GestureEvent !== "undefined";
  let gestureActive = false;
  let gestureStartZoom = 1;
  let gestureLastPoint = null;

  if (hasGestureEvents) {
    stage.addEventListener("gesturestart", (event) => {
      event.preventDefault();
      gestureActive = true;
      gestureStartZoom = zoom;
      gestureLastPoint = { x: event.clientX, y: event.clientY };
    });

    stage.addEventListener("gesturechange", (event) => {
      event.preventDefault();
      if (gestureLastPoint) {
        // 指をつまんだまま動かした分だけ、表示位置も動かす
        panX += event.clientX - gestureLastPoint.x;
        panY += event.clientY - gestureLastPoint.y;
      }
      gestureLastPoint = { x: event.clientX, y: event.clientY };
      setZoom(gestureStartZoom * event.scale, event.clientX, event.clientY);
      applyTransform();
    });

    stage.addEventListener("gestureend", (event) => {
      event.preventDefault();
      gestureActive = false;
      gestureLastPoint = null;
    });
  }

  zoomResetButton.addEventListener("click", resetZoom);

  // 1 本指で表示位置を動かすモード。拡大したあと、指 2 本での操作が
  // うまくいかない端末でも確実に動かせるようにするための逃げ道。
  let panMode = false;
  let panDragFrom = null;

  panModeButton.addEventListener("click", () => {
    panMode = !panMode;
    panModeButton.setAttribute("aria-pressed", String(panMode));
    stage.classList.toggle("stage--panning", panMode);
  });
  window.addEventListener("resize", applyTransform);

  /* ---------- カーソル表示 ---------- */

  function placeCursor() {
    if (!remoteCursor) {
      cursorEl.hidden = true;
      return;
    }
    const canvasRect = canvas.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    if (canvasRect.width === 0) return;
    cursorEl.style.left = `${canvasRect.left - stageRect.left + remoteCursor.x * canvasRect.width}px`;
    cursorEl.style.top = `${canvasRect.top - stageRect.top + remoteCursor.y * canvasRect.height}px`;
    cursorEl.hidden = false;
  }

  // 表示サイズが変わるとカーソルの位置もずれるので置き直す
  window.addEventListener("resize", placeCursor);
  document.addEventListener("fullscreenchange", placeCursor);

  /* ---------- 座標変換 ---------- */

  function normalize(event) {
    const rect = canvas.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return null;
    return {
      x: (event.clientX - rect.left) / rect.width,
      y: (event.clientY - rect.top) / rect.height,
    };
  }

  function inside(point) {
    return point && point.x >= 0 && point.x <= 1 && point.y >= 0 && point.y <= 1;
  }

  /* ---------- マウス ---------- */

  canvas.addEventListener("mousemove", (event) => {
    if (!canControl) return;
    const point = normalize(event);
    if (!inside(point)) return;
    const now = performance.now();
    if (now - lastMoveSent >= MOUSE_MOVE_INTERVAL_MS) {
      lastMoveSent = now;
      pendingMove = null;
      send({ t: "mouse_move", x: point.x, y: point.y });
    } else {
      // 間引いた分は最後の位置だけ後追いで送る(取りこぼし防止)
      pendingMove = point;
    }
  });

  setInterval(() => {
    if (canControl && pendingMove) {
      send({ t: "mouse_move", x: pendingMove.x, y: pendingMove.y });
      pendingMove = null;
      lastMoveSent = performance.now();
    }
  }, MOUSE_MOVE_INTERVAL_MS);

  canvas.addEventListener("mousedown", (event) => {
    if (!canControl) return;
    event.preventDefault();
    const point = normalize(event);
    if (!inside(point)) return;
    canvas.focus();
    send({ t: "mouse_down", x: point.x, y: point.y, button: BUTTONS[event.button] || "left" });
  });

  window.addEventListener("mouseup", (event) => {
    if (!canControl) return;
    const point = normalize(event);
    if (!point) return;
    send({
      t: "mouse_up",
      x: Math.min(1, Math.max(0, point.x)),
      y: Math.min(1, Math.max(0, point.y)),
      button: BUTTONS[event.button] || "left",
    });
  });

  canvas.addEventListener("contextmenu", (event) => event.preventDefault());

  canvas.addEventListener(
    "wheel",
    (event) => {
      if (!canControl) return;
      event.preventDefault();
      const point = normalize(event);
      if (!inside(point)) return;
      // deltaMode 0 はピクセル単位。おおよそ 1 ノッチ = 100px として換算する。
      const unit = event.deltaMode === 0 ? 100 : 1;
      const dx = -Math.trunc(event.deltaX / unit) || (event.deltaX ? -Math.sign(event.deltaX) : 0);
      const dy = -Math.trunc(event.deltaY / unit) || (event.deltaY ? -Math.sign(event.deltaY) : 0);
      send({ t: "scroll", x: point.x, y: point.y, dx, dy });
    },
    { passive: false }
  );

  /* ---------- タッチ操作(iPhone / iPad / Android)---------- */

  // タップ = 左クリック、長押し = 右クリック、指を滑らせる = ドラッグ、
  // 2 本指 = スクロール。マウスと違って「押さずに動かす」ができないので、
  // 押し下げは「ドラッグと判定できてから」送る。
  const LONG_PRESS_MS = 550;
  const DRAG_THRESHOLD_PX = 8;
  const SCROLL_STEP_PX = 40;

  let touchOrigin = null;      // 最初に触れた位置
  let touchLast = null;        // 直近の位置(指を離すときに使う)
  let touchDragging = false;
  let longPressTimer = null;
  let longPressFired = false;
  let scrollRemainder = 0;
  let gesture = null;      // 2 本指の操作(ズーム / 移動 / スクロール)の状態

  // 2 本指の操作は、指の間隔が変われば拡大、位置だけ動けば移動かスクロールと判断する
  const GESTURE_THRESHOLD_PX = 12;

  function fingerDistance(touches) {
    return Math.hypot(
      touches[0].clientX - touches[1].clientX,
      touches[0].clientY - touches[1].clientY
    );
  }

  function centroid(touches) {
    let x = 0;
    let y = 0;
    for (const touch of touches) {
      x += touch.clientX;
      y += touch.clientY;
    }
    return { clientX: x / touches.length, clientY: y / touches.length };
  }

  function cancelLongPress() {
    if (longPressTimer !== null) {
      clearTimeout(longPressTimer);
      longPressTimer = null;
    }
  }

  function endTouchGesture() {
    cancelLongPress();
    touchOrigin = null;
    touchLast = null;
    touchDragging = false;
    longPressFired = false;
  }

  canvas.addEventListener(
    "touchstart",
    (event) => {
      if (!canControl) return;
      event.preventDefault();

      if (event.touches.length >= 2) {
        // 2 本指に切り替わった。ドラッグ中なら先に離しておく。
        if (touchDragging && touchLast) {
          send({ t: "mouse_up", x: touchLast.x, y: touchLast.y, button: "left" });
        }
        endTouchGesture();
        const center = centroid(event.touches);
        const spread = fingerDistance(event.touches);
        gesture = {
          mode: null,
          startDistance: spread,
          lastDistance: spread,
          startCentroid: center,
          lastCentroid: center,
        };
        scrollRemainder = 0;
        return;
      }

      if (panMode) {
        panDragFrom = { x: event.touches[0].clientX, y: event.touches[0].clientY };
        return;
      }

      const point = normalize(event.touches[0]);
      if (!inside(point)) return;
      touchOrigin = {
        ...point,
        clientX: event.touches[0].clientX,
        clientY: event.touches[0].clientY,
      };
      touchLast = point;
      touchDragging = false;
      longPressFired = false;
      send({ t: "mouse_move", x: point.x, y: point.y });

      longPressTimer = setTimeout(() => {
        longPressFired = true;
        longPressTimer = null;
        send({ t: "mouse_down", x: point.x, y: point.y, button: "right" });
        send({ t: "mouse_up", x: point.x, y: point.y, button: "right" });
      }, LONG_PRESS_MS);
    },
    { passive: false }
  );

  canvas.addEventListener(
    "touchmove",
    (event) => {
      if (!canControl) return;
      event.preventDefault();

      if (gesture && event.touches.length >= 2) {
        // Safari では拡大・移動を gesture イベント側で処理しているので、
        // ここで二重に反応させない(ピンチ中に相手の画面がスクロールしてしまう)
        if (gestureActive) return;
        const center = centroid(event.touches);
        const spread = fingerDistance(event.touches);
        const movedX = center.clientX - gesture.lastCentroid.clientX;
        const movedY = center.clientY - gesture.lastCentroid.clientY;

        if (gesture.mode === null) {
          const spreadChange = Math.abs(spread - gesture.startDistance);
          const centroidMove = Math.hypot(
            center.clientX - gesture.startCentroid.clientX,
            center.clientY - gesture.startCentroid.clientY
          );
          if (spreadChange > GESTURE_THRESHOLD_PX && !hasGestureEvents) {
            // Safari では拡大は gesture イベント側で処理する
            gesture.mode = "zoom";
          } else if (centroidMove > GESTURE_THRESHOLD_PX) {
            // 等倍のままなら相手の画面をスクロール、拡大中なら表示位置を動かす
            gesture.mode = zoom > 1 ? "pan" : "scroll";
          }
        }

        if (gesture.mode === "zoom") {
          if (gesture.lastDistance > 0) {
            panX += movedX;
            panY += movedY;
            setZoom(zoom * (spread / gesture.lastDistance), center.clientX, center.clientY);
            applyTransform();
          }
        } else if (gesture.mode === "pan") {
          panX += movedX;
          panY += movedY;
          applyTransform();
        } else if (gesture.mode === "scroll") {
          scrollRemainder += movedY;
          const notches = Math.trunc(scrollRemainder / SCROLL_STEP_PX);
          if (notches !== 0) {
            scrollRemainder -= notches * SCROLL_STEP_PX;
            const point = normalize(center);
            if (inside(point)) {
              send({ t: "scroll", x: point.x, y: point.y, dx: 0, dy: notches });
            }
          }
        }

        gesture.lastDistance = spread;
        gesture.lastCentroid = center;
        return;
      }

      if (panMode) {
        if (!panDragFrom) return;
        panX += event.touches[0].clientX - panDragFrom.x;
        panY += event.touches[0].clientY - panDragFrom.y;
        panDragFrom = { x: event.touches[0].clientX, y: event.touches[0].clientY };
        applyTransform();
        return;
      }

      if (!touchOrigin) return;
      const touch = event.touches[0];
      const point = normalize(touch);
      if (!inside(point)) return;
      touchLast = point;

      const moved = Math.hypot(
        touch.clientX - touchOrigin.clientX,
        touch.clientY - touchOrigin.clientY
      );
      if (!touchDragging && !longPressFired && moved > DRAG_THRESHOLD_PX) {
        cancelLongPress();
        touchDragging = true;
        send({ t: "mouse_down", x: touchOrigin.x, y: touchOrigin.y, button: "left" });
      }
      send({ t: "mouse_move", x: point.x, y: point.y });
    },
    { passive: false }
  );

  canvas.addEventListener(
    "touchend",
    (event) => {
      if (!canControl) return;
      event.preventDefault();
      if (event.touches.length < 2) {
        gesture = null;
        scrollRemainder = 0;
      }
      if (event.touches.length === 0) panDragFrom = null;
      if (!touchOrigin) return;

      const point = touchLast || touchOrigin;
      if (touchDragging) {
        send({ t: "mouse_up", x: point.x, y: point.y, button: "left" });
      } else if (!longPressFired) {
        // 動かさずに離した = タップ。左クリックとして送る。
        send({ t: "mouse_down", x: point.x, y: point.y, button: "left" });
        send({ t: "mouse_up", x: point.x, y: point.y, button: "left" });
      }
      endTouchGesture();
    },
    { passive: false }
  );

  canvas.addEventListener("touchcancel", () => {
    if (touchDragging && touchLast) {
      send({ t: "mouse_up", x: touchLast.x, y: touchLast.y, button: "left" });
    }
    endTouchGesture();
    gesture = null;
  });

  /* ---------- キーボード ---------- */

  // ブラウザ自身が握っていて奪えない組み合わせ。転送を試みず素通りさせる。
  const BROWSER_RESERVED = new Set(["F5", "F11", "F12"]);
  const heldKeys = new Set();

  function keyEventPayload(event) {
    return { key: event.key, code: event.code };
  }

  window.addEventListener("keydown", (event) => {
    if (!keyboardEnabled || !canControl) return;
    if (BROWSER_RESERVED.has(event.key)) return;
    event.preventDefault();
    if (event.repeat) {
      send({ t: "key_down", ...keyEventPayload(event) });
      return;
    }
    heldKeys.add(event.code || event.key);
    send({ t: "key_down", ...keyEventPayload(event) });
  });

  window.addEventListener("keyup", (event) => {
    if (!keyboardEnabled || !canControl) return;
    if (BROWSER_RESERVED.has(event.key)) return;
    event.preventDefault();
    heldKeys.delete(event.code || event.key);
    send({ t: "key_up", ...keyEventPayload(event) });
  });

  // タブが隠れた・フォーカスを失ったときは押しっぱなしを解除する
  window.addEventListener("blur", releaseLocalState);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) releaseLocalState();
  });

  function releaseLocalState() {
    heldKeys.forEach((code) => send({ t: "key_up", key: code, code }));
    heldKeys.clear();
  }

  keyboardToggle.addEventListener("click", () => {
    keyboardEnabled = !keyboardEnabled;
    keyboardToggle.setAttribute("aria-pressed", String(keyboardEnabled));
    keyboardToggle.textContent = `キーボード転送: ${keyboardEnabled ? "ON" : "OFF"}`;
    if (!keyboardEnabled) releaseLocalState();
  });

  // ショートカット送信ボタン("Control+c" のような表記を順番に押して離す)
  document.querySelectorAll("[data-combo]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!canControl) return;
      const parts = button.dataset.combo.split("+");
      parts.forEach((part) => send({ t: "key_down", key: part, code: "" }));
      [...parts].reverse().forEach((part) => send({ t: "key_up", key: part, code: "" }));
    });
  });

  /* ---------- スマホのソフトキーボード ---------- */

  // スマホには物理キーのイベントが無いので、見えない入力欄にフォーカスして
  // OS のキーボードを出し、入力された文字列をそのまま送る。日本語入力(IME)は
  // 変換確定まで待つ必要があるため、composition イベントで区切る。
  let composing = false;

  function sendText(text) {
    if (!canControl || !text) return;
    send({ t: "text", text });
  }

  function sendKeyPress(key) {
    if (!canControl) return;
    send({ t: "key_down", key, code: "" });
    send({ t: "key_up", key, code: "" });
  }

  function setSoftKeyboard(open) {
    softKeyboardButton.setAttribute("aria-pressed", String(open));
    if (open) {
      softInput.value = "";
      softInput.focus();       // ユーザー操作の中で呼ぶ必要がある(iOS の制約)
    } else {
      softInput.blur();
    }
  }

  softKeyboardButton.addEventListener("click", () => {
    setSoftKeyboard(softKeyboardButton.getAttribute("aria-pressed") !== "true");
  });

  softInput.addEventListener("blur", () => {
    softKeyboardButton.setAttribute("aria-pressed", "false");
  });

  softInput.addEventListener("compositionstart", () => {
    composing = true;
  });

  softInput.addEventListener("compositionend", (event) => {
    composing = false;
    sendText(event.data || softInput.value);
    softInput.value = "";
  });

  softInput.addEventListener("beforeinput", (event) => {
    if (composing) return;
    if (event.inputType === "deleteContentBackward") {
      event.preventDefault();
      sendKeyPress("Backspace");
    } else if (event.inputType === "insertLineBreak" || event.inputType === "insertParagraph") {
      event.preventDefault();
      sendKeyPress("Enter");
    }
  });

  softInput.addEventListener("input", () => {
    if (composing) return;
    const text = softInput.value;
    if (text) {
      sendText(text);
      softInput.value = "";     // 溜めずに毎回送る
    }
  });

  // マウスのある端末では不要なので出さない(物理キーボードをそのまま使える)
  if (window.matchMedia("(pointer: coarse)").matches) {
    softKeyboardButton.hidden = false;
    zoomResetButton.hidden = false;   // ピンチで拡大したときに等倍へ戻す
    panModeButton.hidden = false;
  }

  /* ---------- 画質・モニタ設定 ---------- */

  function syncOutputs() {
    el("qualityOut").value = el("quality").value;
    el("fpsOut").value = el("fps").value;
    el("scaleOut").value = `${el("scale").value}%`;
  }

  function sendConfig() {
    syncOutputs();
    send({
      t: "config",
      quality: Number(el("quality").value),
      fps: Number(el("fps").value),
      scale: Number(el("scale").value) / 100,
    });
  }

  ["quality", "fps", "scale"].forEach((id) => {
    el(id).addEventListener("input", syncOutputs);
    el(id).addEventListener("change", sendConfig);
  });

  function fillMonitors(monitors, current) {
    monitorSel.innerHTML = "";
    (monitors || []).forEach((monitor) => {
      const option = document.createElement("option");
      option.value = String(monitor.index);
      option.textContent = monitor.index === 0 ? `全体 (${monitor.width}x${monitor.height})` : monitor.label;
      monitorSel.appendChild(option);
    });
    monitorSel.value = String(current);
  }

  monitorSel.addEventListener("change", () => {
    send({ t: "config", monitor: Number(monitorSel.value) });
  });

  /* ---------- 全画面 ---------- */

  // iPhone の Safari は要素の全画面表示に対応していない。対応環境では本来の
  // 全画面にし、そうでなければ上下のバーを隠して画面いっぱいに使う。
  function supportsFullscreen() {
    return typeof stage.requestFullscreen === "function";
  }

  function setImmersive(on) {
    document.body.classList.toggle("immersive", on);
    exitImmersiveButton.hidden = !on;
    fullscreenButton.setAttribute("aria-pressed", String(on));
    // 表示領域の大きさが変わるので、拡大とカーソルの位置を計算し直す
    applyTransform();
  }

  function enterFullscreen() {
    setImmersive(true);
    if (supportsFullscreen() && !document.fullscreenElement) {
      stage.requestFullscreen().catch(() => {
        /* 拒否されても、バーを隠した表示は有効なままにする */
      });
    } else if (!supportsFullscreen() && !window.navigator.standalone) {
      setStatus("共有 → ホーム画面に追加 で開くと、より広く使えます", "ok");
    }
  }

  function exitFullscreen() {
    setImmersive(false);
    if (document.fullscreenElement) document.exitFullscreen();
  }

  fullscreenButton.addEventListener("click", () => {
    if (document.body.classList.contains("immersive")) {
      exitFullscreen();
    } else {
      enterFullscreen();
    }
  });

  exitImmersiveButton.addEventListener("click", exitFullscreen);

  document.addEventListener("fullscreenchange", () => {
    // 端末側の操作で全画面が解除されたときに表示を合わせる
    if (!document.fullscreenElement && supportsFullscreen()) setImmersive(false);
  });

  /* ---------- 表示ヘルパ ---------- */

  function setStatus(text, kind) {
    statusEl.textContent = text;
    statusEl.className = `status status--${kind}`;
  }

  function showOverlay(text) {
    overlay.textContent = text;
    overlay.hidden = false;
  }

  // 定期的な ping で、途中の機器に切られたコネクションを早めに検知する
  setInterval(() => send({ t: "ping" }), 15000);

  if (!token) {
    setStatus("トークンがありません", "err");
    showOverlay("URL にトークンが含まれていません。\nサーバー起動時に表示された URL を開いてください。");
  } else {
    connect();
  }
})();
