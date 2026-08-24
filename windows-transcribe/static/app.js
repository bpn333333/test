"use strict";

const $ = (id) => document.getElementById(id);

const el = {
  device: $("device"), model: $("model"), language: $("language"),
  compute: $("compute"), prompt: $("prompt"),
  silence: $("silence"), min: $("min_seconds"), max: $("max_seconds"),
  threshold: $("threshold"), noise: $("noise_factor"),
  live: $("live"), record: $("record"), stop: $("stop"),
  upload: $("upload"), uploadLabel: $("upload-label"),
  pill: $("pill"), source: $("source"),
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
  return {
    device: el.device.value || null,
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

async function loadDevices() {
  const res = await fetch("/api/devices");
  const data = await res.json();
  if (data.error) {
    el.device.replaceChildren(new Option("取り込めません", ""));
    el.device.disabled = true;
    el.live.disabled = true;
    el.record.disabled = true;
    toast(data.error, "error");
    return;
  }
  el.device.replaceChildren();
  for (const dev of data.devices) {
    const label = `${dev.name}${dev.default ? "（既定）" : ""}`;
    const option = new Option(label, dev.name);
    option.title = `${dev.name} — ${dev.rate} Hz / ${dev.channels} ch`;
    if (dev.default) option.selected = true;
    el.device.append(option);
  }
}

function connect() {
  const socket = new WebSocket(`ws://${location.host}/ws`);

  socket.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    switch (msg.type) {
      case "state":
        setMode(msg.mode, msg.detail);
        if (msg.source) el.source.textContent = msg.source;
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

loadDevices();
connect();
