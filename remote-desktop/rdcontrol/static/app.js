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
      } else {
        drawFrame(event.data);
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
  let scrollAnchor = null;
  let scrollRemainder = 0;

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
        scrollAnchor = centroid(event.touches);
        scrollRemainder = 0;
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

      if (scrollAnchor && event.touches.length >= 2) {
        const center = centroid(event.touches);
        scrollRemainder += center.clientY - scrollAnchor.clientY;
        scrollAnchor = center;
        const notches = Math.trunc(scrollRemainder / SCROLL_STEP_PX);
        if (notches !== 0) {
          scrollRemainder -= notches * SCROLL_STEP_PX;
          const point = normalize(center);
          if (inside(point)) {
            send({ t: "scroll", x: point.x, y: point.y, dx: 0, dy: notches });
          }
        }
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
      if (event.touches.length === 0) {
        scrollAnchor = null;
        scrollRemainder = 0;
      }
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
    scrollAnchor = null;
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

  el("fullscreen").addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      stage.requestFullscreen().catch(() => setStatus("全画面表示を開始できませんでした", "err"));
    }
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
