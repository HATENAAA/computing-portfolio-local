const $ = (id) => document.getElementById(id),
  labels = {
    uploading: "上传中",
    queued: "排队中",
    running: "分析中",
    completed: "分析完成",
    cancelled: "已取消",
    failed: "分析失败",
  };
let list = [],
  lastPayload = "",
  loading = false;
const size = (n) =>
  n < 1024 * 1024
    ? (n / 1024).toFixed(0) + " KB"
    : (n / 1024 / 1024).toFixed(1) + " MB";
function el(tag, text, cls) {
  const x = document.createElement(tag);
  if (text !== undefined) x.textContent = text;
  if (cls) x.className = cls;
  return x;
}
function link(text, href, cls) {
  const a = el("a", text, cls);
  a.href = href;
  return a;
}
function render() {
  const active = list.filter((j) =>
    ["uploading", "queued", "running"].includes(j.status),
  );
  $("done-count").textContent = list.filter(
    (j) => j.status === "completed",
  ).length;
  $("active-count").textContent = active.length;
  $("storage-total").textContent = size(
    list.reduce((n, j) => n + (j.storage_bytes || 0), 0),
  );
  const query = $("search-jobs").value.toLowerCase(),
    filter = $("status-filter").value,
    rows = list.filter(
      (j) =>
        j.filename.toLowerCase().includes(query) &&
        (filter === "all" ||
          (filter === "active" && active.includes(j)) ||
          (filter === "failed" && ["failed", "cancelled"].includes(j.status)) ||
          filter === j.status),
    );
  $("jobs").replaceChildren();
  if (!rows.length) {
    const empty = el("div", undefined, "queue-empty");
    empty.append(
      el("span", "▧"),
      el("h3", list.length ? "没有符合条件的任务" : "暂无分析任务"),
      el(
        "p",
        list.length
          ? "换一个关键词或筛选条件。"
          : "在新建视频任务中选择文件，分析完成后会保留报告、代表帧和逐帧时间线。",
      ),
    );
    $("jobs").append(empty);
    return;
  }
  for (const job of rows) {
    const row = el("article", undefined, "job-card"),
      head = el("div", undefined, "job-head"),
      name = el("div", undefined, "job-name");
    name.append(
      el("span", job.filename.split(".").pop().toUpperCase(), "file-type"),
      el("h3", job.filename),
    );
    head.append(
      name,
      el("span", labels[job.status] || job.status, "job-status " + job.status),
    );
    row.append(head);
    const meta = el("p", undefined, "job-meta");
    meta.textContent =
      (job.decision_engine === "model"
        ? "ONNX 模型 · 含规则对照"
        : job.decision_engine === "cpp" ? "C++ 区域与运动" : "旧版颜色与边缘") +
      " · " +
      size(job.storage_bytes || 0) +
      (job.source_retained ? " · 可回放" : "");
    row.append(meta);
    const actions = el("div", undefined, "job-actions");
    if (["uploading", "queued", "running"].includes(job.status)) {
      const p = el("progress");
      p.max = 1;
      if (job.progress !== null) p.value = job.progress;
      row.append(p);
      const cancel = el("button", job.cancel ? "正在取消…" : "取消任务");
      cancel.disabled = !!job.cancel;
      cancel.onclick = () => mutate("/" + job.id + "/cancel", "POST");
      actions.append(
        el(
          "span",
          job.status === "running" && job.progress !== null
            ? "约 " + Math.round(job.progress * 100) + "%"
            : "等待处理",
          "job-detail",
        ),
        cancel,
      );
    }
    if (job.status === "completed") {
      const detail = el("div", undefined, "job-detail");
      detail.append(
        el("b", (job.events ?? 0) + " 个候选事件"),
        el(
          "span",
          (job.sampled_frames ?? 0) +
            " 帧 · " +
            (job.duration_analyzed_s || 0).toFixed(1) +
            " 秒" +
            (job.truncated ? " · 仅分析前段" : ""),
        ),
      );
      actions.append(
        detail,
        link("打开复核 →", "/review/" + job.id, "open-review"),
      );
      const menu = document.createElement("details");
      menu.className = "job-menu";
      const summary = el("summary", "···");
      summary.setAttribute("aria-label", "任务文件与清理");
      const pop = el("div", undefined, "job-popover");
      for (const [file, label] of [
        ["review.html", "查看独立报告"],
        ["timeline.csv", "导出时间线 CSV"],
        ["video-report.json", "导出原始 JSON"],
      ])
        pop.append(link(label, "/api/videos/" + job.id + "/files/" + file));
      menu.append(summary, pop);
      actions.append(menu);
      addDelete(job, pop);
    }
    if (job.error) row.append(el("p", job.error, "job-error"));
    if (["failed", "cancelled"].includes(job.status)) addDelete(job, actions);
    row.append(actions);
    $("jobs").append(row);
  }
}
function addDelete(job, host) {
  const button = el("button", "删除任务与文件", "delete-job");
  button.onclick = async () => {
    if (
      !confirm(
        "删除“" +
          job.filename +
          "”的本机报告、保留视频与标注记录？此操作不能撤销。",
      )
    )
      return;
    button.disabled = true;
    await mutate("/" + job.id, "DELETE");
  };
  host.append(button);
}
async function mutate(path, method) {
  try {
    const r = await fetch("/api/videos" + path, { method });
    const v = await r.json();
    if (!r.ok)
      throw new Error(typeof v.detail === "string" ? v.detail : "操作失败");
    $("message").textContent =
      method === "DELETE" ? "本机任务、文件与标注已清理。" : "已请求取消任务。";
    await load(true);
  } catch (e) {
    $("message").textContent = e.message;
    render();
  }
}
async function load(force = false) {
  if (loading) return;
  if (document.hidden && !force) return;
  loading = true;
  try {
    const r = await fetch("/api/videos");
    if (!r.ok) throw new Error("无法读取任务");
    const v = await r.json(),
      payload = JSON.stringify(v);
    if (force || payload !== lastPayload) {
      list = v;
      lastPayload = payload;
      render();
    }
  } catch {
    $("message").textContent = "任务服务暂时无法连接，请稍后刷新。";
  } finally {
    loading = false;
  }
}
$("search-jobs").oninput = render;
$("status-filter").onchange = render;
$("refresh-jobs").onclick = () => load(true);
$("video").onchange = () => {
  $("selected-file").textContent = $("video").files[0]?.name || "选择一段视频";
};
$("video-engine").onchange = () => {
  const model = $("video-engine").value === "model";
  $("video-confirm-label").textContent=$("video-engine").value==='cpp'?'滑窗内命中 / 帧':'连续确认 / 帧';
  $("model-settings").hidden = !model;
  $("rule-settings").hidden = model;
  $("video-edge").disabled=$("video-engine").value==='cpp';$("video-edge").closest("label").hidden=$("video-engine").value==='cpp';
  $("engine-help").textContent = model
    ? "模型结果用于形成事件；同时保留规则得分与分歧帧统计。"
    : $("video-engine").value==='cpp'?"C++ 提取局部颜色与变化；滑窗确认事件，不使用全画面边缘比例。":"旧版规则保留作实验对照。";
};
async function modelStatus() {
  try {
    const r = await fetch("/api/model/status"),
      v = await r.json();
    $("model-option").disabled = !v.configured;
    $("model-status").textContent = v.configured
      ? "● 本机 ONNX 模型可用"
      : "○ C++ 区域与运动 · ONNX 模型未配置（可选）";
    $("model-status").classList.toggle("ready", !!v.configured);
  } catch {
    $("model-status").textContent = "模型状态暂时无法读取";
  }
}
$("upload").onsubmit = async (e) => {
  e.preventDefault();
  const file = $("video").files[0];
  if (!file) return;
  if (file.size > 50 * 1024 * 1024) {
    $("message").textContent = "视频不能超过 50 MB。";
    return;
  }
  const b = $("submit");
  b.disabled = true;
  $("message").textContent = "正在上传，请稍候…";
  try {
    const data = new FormData();
    data.append("file", file);
    for (const [field, id] of [
      ["edge_ratio", "video-edge"],
      ["brightness", "video-brightness"],
      ["decision_engine", "video-engine"],
      ["confidence", "video-confidence"],
      ["sample_hz", "sample-hz"],
      ["on_frames", "on-frames"],
      ["off_frames", "off-frames"],
    ])
      data.append(field, $(id).value);
    data.append("retain_source", $("retain-source").checked);
    const r = await fetch("/api/videos", { method: "POST", body: data }),
      v = await r.json();
    if (!r.ok)
      throw new Error(
        typeof v.detail === "string" ? v.detail : "参数无效，请检查数值范围。",
      );
    $("message").textContent = "任务已创建，可在分析记录中跟踪进度。";
    await load(true);
  } catch (e) {
    $("message").textContent = e.message;
  } finally {
    b.disabled = false;
  }
};
load(true);
modelStatus();
setInterval(load, 1500);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) load(true);
});

$("video-engine").onchange();
