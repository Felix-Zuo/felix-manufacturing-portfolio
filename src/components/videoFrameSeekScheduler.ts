export type VideoFrameSeekSchedulerOptions = {
  cancelAnimationFrame?: (handle: number) => void;
  fps: number;
  frameCount: number;
  requestAnimationFrame?: (callback: FrameRequestCallback) => number;
};

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

export function mediaProgressToFrameIndex(
  progress: number,
  frameCount: number,
) {
  const lastFrameIndex = Math.max(Math.round(frameCount) - 1, 0);
  return Math.round(clamp(progress, 0, 1) * lastFrameIndex);
}

export function frameIndexToTime(
  frameIndex: number,
  fps: number,
  duration: number,
) {
  if (!Number.isFinite(duration) || duration <= 0) return 0;

  const frameDuration = 1 / fps;
  const maximumTime = Math.max(duration - frameDuration, 0);
  return clamp(Math.round(frameIndex) / fps, 0, maximumTime);
}

const defaultRequestAnimationFrame = (callback: FrameRequestCallback) =>
  window.requestAnimationFrame(callback);

const defaultCancelAnimationFrame = (handle: number) =>
  window.cancelAnimationFrame(handle);

/** Coalesces scrub requests and releases each seek only after its frame is ready. */
export class VideoFrameSeekScheduler {
  private readonly video: HTMLVideoElement;
  private readonly fps: number;
  private readonly frameCount: number;
  private readonly requestAnimationFrame: (callback: FrameRequestCallback) => number;
  private readonly cancelAnimationFrame: (handle: number) => void;
  private desiredFrame: number | null = null;
  private settledFrame: number | null = null;
  private inFlightFrame: number | null = null;
  private duration = 0;
  private generation = 0;
  private videoFrameCallbackId: number | null = null;
  private fallbackAnimationFrameId: number | null = null;
  private removeSeekedListener: (() => void) | null = null;
  private disposed = false;

  constructor(
    video: HTMLVideoElement,
    options: VideoFrameSeekSchedulerOptions,
  ) {
    this.video = video;
    this.fps = options.fps;
    this.frameCount = options.frameCount;
    this.requestAnimationFrame =
      options.requestAnimationFrame ?? defaultRequestAnimationFrame;
    this.cancelAnimationFrame =
      options.cancelAnimationFrame ?? defaultCancelAnimationFrame;
  }

  schedule(progress: number, duration: number) {
    if (this.disposed || !Number.isFinite(duration) || duration <= 0) return;

    this.desiredFrame = mediaProgressToFrameIndex(progress, this.frameCount);
    this.duration = duration;
    this.flush();
  }

  reset() {
    this.generation += 1;
    this.clearCompletionWaiters();
    this.desiredFrame = null;
    this.settledFrame = null;
    this.inFlightFrame = null;
    this.duration = 0;
  }

  dispose() {
    this.reset();
    this.disposed = true;
  }

  private flush() {
    const frame = this.desiredFrame;
    if (
      this.disposed ||
      frame === null ||
      this.inFlightFrame !== null ||
      frame === this.settledFrame
    ) {
      return;
    }

    const generation = this.generation;
    const targetTime = frameIndexToTime(frame, this.fps, this.duration);
    let hasVideoFrameCallback =
      typeof this.video.requestVideoFrameCallback === "function";

    this.inFlightFrame = frame;

    if (hasVideoFrameCallback) {
      try {
        this.videoFrameCallbackId = this.video.requestVideoFrameCallback(() => {
          this.videoFrameCallbackId = null;
          this.complete(frame, generation);
        });
      } catch {
        hasVideoFrameCallback = false;
      }
    }

    if (!hasVideoFrameCallback) {
      this.waitForSeeked(frame, generation);
    }

    try {
      this.video.currentTime = targetTime;
    } catch {
      this.clearCompletionWaiters();
      this.inFlightFrame = null;
      return;
    }
  }

  private waitForSeeked(frame: number, generation: number) {
    const onSeeked = () => {
      this.removeSeekedListener?.();
      this.fallbackAnimationFrameId = this.requestAnimationFrame(() => {
        this.fallbackAnimationFrameId = null;
        this.complete(frame, generation);
      });
    };

    this.video.addEventListener("seeked", onSeeked, { once: true });
    this.removeSeekedListener = () => {
      this.video.removeEventListener("seeked", onSeeked);
      this.removeSeekedListener = null;
    };
  }

  private complete(frame: number, generation: number) {
    if (
      this.disposed ||
      generation !== this.generation ||
      this.inFlightFrame !== frame
    ) {
      return;
    }

    this.clearCompletionWaiters();
    this.settledFrame = frame;
    this.inFlightFrame = null;
    this.flush();
  }

  private clearCompletionWaiters() {
    if (
      this.videoFrameCallbackId !== null &&
      typeof this.video.cancelVideoFrameCallback === "function"
    ) {
      this.video.cancelVideoFrameCallback(this.videoFrameCallbackId);
    }
    if (this.fallbackAnimationFrameId !== null) {
      this.cancelAnimationFrame(this.fallbackAnimationFrameId);
    }

    this.videoFrameCallbackId = null;
    this.fallbackAnimationFrameId = null;
    this.removeSeekedListener?.();
  }
}
