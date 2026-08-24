"use strict";

const $ = (id) => document.getElementById(id);

const el = {
  source: $("source-select"), refresh: $("refresh"),
  model: $("model"), language: $("language"),
  compute: $("compute"), prompt: $("prompt"),
  silence: $("silence"), min: $("min_seconds"), max: $("max_seconds"),
  threshold: $("threshold"), noise: $("noise_factor"),
  live: $("live"), record: $("record"), stop: $("stop"),
  upload: $("upload"), uploadLabel: $("upload-label"),
  pill: $("pill"), sourceName: $("source"),
  meter: $("meter"), meterFill: $("meter-fill"), meterTime: $("meter-time"),
  segments: $("segments"), empty: $("empty"), downloads: $("downloads"),
  copy: $("copy"), toast: $("toast"),
};

let mode = "idle";

// ---------------------------------------------------------------- 表示

const LABELS = { idle: "待機中", live: "リアルタイム", record: "録音中", file: "文字起こし中" };

function setMode(next, detail) {
  mode = next;
  el.pill.dataset.mode = next;
  el.pill.textContent = detail ? `${LABELS[next] || next} — ${detail}` : (LABELS[next] || next);

  const busy = next !== "idle";
  el.live.disabled = busy;
  el.record.disabled = busy;
  el.stop.disabled = !busy;
  el.upload.disabled = busy;
  el.uploadLabel.style.opacity = busy ? ".45" : "";
  el.uploadLabel.style.pointerEvents = busy ? "none" : "";

  const capturing = next === "live" || next === "record";
  el.meter.hidden = !capturing;
  if (!capturing) el.meterFill.style.width = "0%";
}

function toast(message, kind) {
  el.toast.textContent = message;
  el.toast.dataset.kind = kind || "info";
  el.toast.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.toast.hidden = true; }, kind === "error" ? 8000 : 3000);
}

function clock(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

function addSegment(seg, fresh) {
  el.empty.hidden = true;
  el.downloads.hidden = false;
  const li = document.createElement("li");
  if (fresh) li.className = "fresh";
  const time = document.createElement("time");
  time.textContent = seg.stamp;
  const p = document.createElement("p");
  p.textContent = seg.text;
  li.append(time, p);
  el.segments.append(li);
  li.scrollIntoView({ block: "nearest", behavior: fresh ? "smooth" : "auto" });
}

function resetSegments() {
  el.segments.replaceChildren();
  el.empty.hidden = false;
  el.downloads.hidden = true;
}

// ---------------------------------------------------------------- 設定

function settings() {
  const [compute_device, compute_type] = el.compute.value.split("|");
  // 収録元は "d:<デバイス名>" か "p:<PID>" のどちらか
  const picked = el.source.value || "";
  const isWindow = picked.startsWith("p:");
  return {
    device: isWindow ? null : picked.slice(2) || null,
    process_id: isWindow ? picked.slice(2) : null,
    window_title: isWindow ? (titles.get(picked.slice(2)) || null) : null,
    model: el.model.value,
    language: el.language.value,
    compute_device, compute_type,
    prompt: el.prompt.value.trim() || null,
    silence: el.silence.value,
    min_seconds: el.min.value,
    max_seconds: el.max.value,
    threshold: el.threshold.value,
    noise_factor: el.noise.value,
  };
}

async function post(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${path} が失敗しました (${res.status})`);
  }
  return res.json();
}

// ---------------------------------------------------------------- 起動

const titles = new Map();   // PID -> ウィンドウのタイトル

async function fetchWindows() {
  try {
    const res = await fetch("/api/windows");
    if (res.status === 404) {
      // 静的ファイルだけ新しく、サーバが古いまま動いているとこうなる
      return { windows: [], error: "アプリを再起動してください（サーバが古いままです）" };
    }
    if (!res.ok) return { windows: [], error: `一覧を取得できません (${res.status})` };
    return await res.json();
  } catch (err) {
    return { windows: [], error: err.message };
  }
}

function disabledOption(label) {
  const option = new Option(label, "");
  option.disabled = true;
  return option;
}

function group(label) {
  const g = document.createElement("optgroup");
  g.label = label;
  return g;
}

async function loadSources() {
  const keep = el.source.value;
  const [devices, windows] = await Promise.all([
    fetch("/api/devices").then((r) => r.json()),
    fetchWindows(),
  ]);

  el.source.replaceChildren();
  titles.clear();

  if (devices.error) {
    el.source.append(new Option("取り込めません", ""));
    el.source.disabled = true;
    el.live.disabled = true;
    el.record.disabled = true;
    toast(devices.error, "error");
    return;
  }

  const deviceGroup = group("デバイス全体");
  for (const dev of devices.devices) {
    const option = new Option(`${dev.name}${dev.default ? "（既定）" : ""}`, `d:${dev.name}`);
    option.title = `${dev.name} — ${dev.rate} Hz / ${dev.channels} ch`;
    if (dev.default) option.selected = true;
    deviceGroup.append(option);
  }
  el.source.append(deviceGroup);

  // ウィンドウのグループは常に出す。空のまま消すと、失敗したのか
  // 対象が無いのか区別がつかない
  const windowGroup = group("ウィンドウ（そのアプリの音だけ）");
  if (windows.error) {
    windowGroup.append(disabledOption(`利用できません — ${windows.error}`));
  } else if (!windows.windows.length) {
    windowGroup.append(disabledOption("対象のウィンドウがありません（↻ で更新）"));
  } else {
    for (const win of windows.windows) {
      const suffix = win.windows > 1 ? `（${win.windows} 窓）` : "";
      const option = new Option(`${win.title}${suffix} — ${win.process}`, `p:${win.pid}`);
      option.title = `${win.process} / PID ${win.pid}\nプロセス単位で分離します`;
      titles.set(String(win.pid), win.title);
      windowGroup.append(option);
    }
  }
  el.source.append(windowGroup);

  // 再読み込み前の選択を保てるなら保つ
  if (keep && [...el.source.options].some((o) => o.value === keep)) {
    el.source.value = keep;
  }
}

function connect() {
  const socket = new WebSocket(`ws://${location.host}/ws`);

  socket.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    switch (msg.type) {
      case "state":
        setMode(msg.mode, msg.detail);
        if (msg.source) el.sourceName.textContent = msg.source;
        if (msg.history) {
          resetSegments();
          msg.history.forEach((seg) => addSegment(seg, false));
        }
        break;
      case "segment":
        addSegment(msg, true);
        break;
      case "level":
        // RMS はごく小さい値なので、目に見える範囲へ対数で引き伸ばす
        el.meterFill.style.width =
          `${Math.min(100, Math.max(0, (20 * Math.log10(msg.rms + 1e-6) + 60) * 1.8))}%`;
        el.meterTime.textContent = clock(msg.elapsed);
        break;
      case "warning":
        toast(msg.message, "error");
        break;
      case "info":
        toast(`${msg.language} / ${msg.duration.toFixed(1)} 秒 を処理します`);
        break;
      case "recorded":
        toast(`録音を保存しました: ${msg.name}`);
        break;
      case "error":
        setMode("error", "");
        toast(msg.message, "error");
        break;
    }
  });

  socket.addEventListener("close", () => setTimeout(connect, 1500));
}

// ---------------------------------------------------------------- 操作

el.live.addEventListener("click", async () => {
  resetSegments();
  try { await post("/api/live/start", settings()); }
  catch (err) { toast(err.message, "error"); }
});

el.record.addEventListener("click", async () => {
  resetSegments();
  try { await post("/api/record/start", settings()); }
  catch (err) { toast(err.message, "error"); }
});

el.stop.addEventListener("click", async () => {
  el.stop.disabled = true;
  try { await post("/api/stop"); }
  catch (err) { toast(err.message, "error"); }
});

el.upload.addEventListener("change", async () => {
  const file = el.upload.files[0];
  if (!file) return;
  resetSegments();
  const form = new FormData();
  form.append("file", file);
  form.append("body", JSON.stringify(settings()));
  try {
    const res = await fetch("/api/upload", { method: "POST", body: form });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `アップロードに失敗しました (${res.status})`);
    }
  } catch (err) {
    toast(err.message, "error");
  }
  el.upload.value = "";
});

el.copy.addEventListener("click", async () => {
  const text = [...el.segments.querySelectorAll("p")].map((p) => p.textContent).join("\n");
  try {
    await navigator.clipboard.writeText(text);
    toast("コピーしました");
  } catch {
    toast("コピーできませんでした。txt をダウンロードしてください", "error");
  }
});

el.refresh.addEventListener("click", async () => {
  el.refresh.disabled = true;
  try { await loadSources(); toast("一覧を更新しました"); }
  catch (err) { toast(err.message, "error"); }
  finally { el.refresh.disabled = false; }
});

loadSources();
connect();
