export class TrainingSession {
  constructor(now = () => performance.now()) {
    this.now = now;
    this.state = "idle";
    this.elapsed = 0;
    this.hits = 0;
    this.startedAt = null;
  }
  start(duration) {
    if (this.state === "running" || this.state === "paused") return;
    if (!Number.isInteger(duration) || duration < 1 || duration > 3600)
      throw new RangeError(
        "Duration must be an integer from 1 to 3600 seconds",
      );
    this.duration = duration * 1000;
    this.elapsed = 0;
    this.hits = 0;
    this.startedAt = new Date().toISOString();
    this.mark = this.now();
    this.state = "running";
  }
  milliseconds() {
    return Math.min(
      this.duration || 0,
      this.elapsed + (this.state === "running" ? this.now() - this.mark : 0),
    );
  }
  pause() {
    if (this.state !== "running") return;
    this.elapsed = this.milliseconds();
    this.state = "paused";
  }
  resume() {
    if (this.state !== "paused") return;
    this.mark = this.now();
    this.state = "running";
  }
  hit() {
    if (this.state === "running" && this.milliseconds() < this.duration)
      this.hits++;
  }
  finish() {
    if (!["running", "paused"].includes(this.state)) return;
    this.elapsed = this.milliseconds();
    this.state = "finished";
    return {
      activeSeconds: Math.round(this.elapsed / 1000),
      hits: this.hits,
      startedAt: this.startedAt,
    };
  }
  snapshot() {
    if (!["running", "paused"].includes(this.state)) return null;
    return {
      durationSeconds: this.duration / 1000,
      elapsedMs: this.milliseconds(),
      hits: this.hits,
      startedAt: this.startedAt,
    };
  }
  restore(value) {
    if (
      !value ||
      !Number.isInteger(value.durationSeconds) ||
      value.durationSeconds < 1 ||
      value.durationSeconds > 3600 ||
      !Number.isFinite(value.elapsedMs) ||
      value.elapsedMs < 0 ||
      value.elapsedMs > value.durationSeconds * 1000 ||
      !Number.isInteger(value.hits) ||
      value.hits < 0 ||
      value.hits > 10000 ||
      typeof value.startedAt !== "string" ||
      !Number.isFinite(Date.parse(value.startedAt))
    )
      throw new TypeError("Invalid session checkpoint");
    this.duration = value.durationSeconds * 1000;
    this.elapsed = value.elapsedMs;
    this.hits = value.hits;
    this.startedAt = value.startedAt;
    this.mark = this.now();
    // A reopened page never counts time spent away as training.
    this.state = "paused";
  }
}
