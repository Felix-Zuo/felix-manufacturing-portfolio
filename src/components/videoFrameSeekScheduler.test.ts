import assert from "node:assert/strict";
import test from "node:test";

const schedulerModulePath: string = "./videoFrameSeekScheduler.ts";
const {
  VideoFrameSeekScheduler,
  frameIndexToTime,
  mediaProgressToFrameIndex,
} = await import(schedulerModulePath);

class VideoFrameCallbackVideo {
  private time = 0;
  private nextCallbackId = 1;
  readonly seekTimes: number[] = [];
  readonly callbacks = new Map<number, VideoFrameRequestCallback>();

  get currentTime() {
    return this.time;
  }

  set currentTime(value: number) {
    this.time = value;
    this.seekTimes.push(value);
  }

  requestVideoFrameCallback(callback: VideoFrameRequestCallback) {
    const id = this.nextCallbackId;
    this.nextCallbackId += 1;
    this.callbacks.set(id, callback);
    return id;
  }

  cancelVideoFrameCallback(id: number) {
    this.callbacks.delete(id);
  }

  presentNextFrame() {
    const entry = this.callbacks.entries().next().value as
      | [number, VideoFrameRequestCallback]
      | undefined;
    assert.ok(entry);
    const [id, callback] = entry;
    this.callbacks.delete(id);
    callback(0, { mediaTime: this.time } as VideoFrameCallbackMetadata);
  }

  addEventListener() {}
  removeEventListener() {}
}

class SeekedFallbackVideo {
  private time = 0;
  private seekedListener: EventListener | null = null;
  readonly seekTimes: number[] = [];

  get currentTime() {
    return this.time;
  }

  set currentTime(value: number) {
    this.time = value;
    this.seekTimes.push(value);
  }

  addEventListener(type: string, listener: EventListener) {
    if (type === "seeked") this.seekedListener = listener;
  }

  removeEventListener(type: string, listener: EventListener) {
    if (type === "seeked" && this.seekedListener === listener) {
      this.seekedListener = null;
    }
  }

  dispatchSeeked() {
    assert.ok(this.seekedListener);
    this.seekedListener(new Event("seeked"));
  }
}

test("quantizes media progress to the 24fps frame timeline", () => {
  assert.equal(mediaProgressToFrameIndex(0, 912), 0);
  assert.equal(mediaProgressToFrameIndex(10.49 / 911, 912), 10);
  assert.equal(mediaProgressToFrameIndex(10.51 / 911, 912), 11);
  assert.equal(mediaProgressToFrameIndex(1, 912), 911);
  assert.equal(frameIndexToTime(24, 24, 38), 1);
  assert.equal(frameIndexToTime(911, 24, 38), 911 / 24);
});

test("coalesces targets and waits for a decoded frame before seeking again", () => {
  const video = new VideoFrameCallbackVideo();
  const scheduler = new VideoFrameSeekScheduler(
    video as unknown as HTMLVideoElement,
    { fps: 24, frameCount: 912 },
  );

  scheduler.schedule(120 / 911, 38);
  scheduler.schedule(120 / 911, 38);
  scheduler.schedule(121 / 911, 38);
  scheduler.schedule(122 / 911, 38);

  assert.deepEqual(video.seekTimes, [120 / 24]);
  video.presentNextFrame();
  assert.deepEqual(video.seekTimes, [120 / 24, 122 / 24]);

  video.presentNextFrame();
  scheduler.schedule(122 / 911, 38);
  assert.deepEqual(video.seekTimes, [120 / 24, 122 / 24]);
});

test("fallback waits for seeked and a paint before releasing the latest target", () => {
  const video = new SeekedFallbackVideo();
  const animationFrames: FrameRequestCallback[] = [];
  const scheduler = new VideoFrameSeekScheduler(
    video as unknown as HTMLVideoElement,
    {
      cancelAnimationFrame: () => {},
      fps: 24,
      frameCount: 912,
      requestAnimationFrame: (callback: FrameRequestCallback) => {
        animationFrames.push(callback);
        return animationFrames.length;
      },
    },
  );

  scheduler.schedule(80 / 911, 38);
  scheduler.schedule(90 / 911, 38);
  assert.deepEqual(video.seekTimes, [80 / 24]);

  video.dispatchSeeked();
  assert.deepEqual(video.seekTimes, [80 / 24]);
  animationFrames.shift()?.(0);
  assert.deepEqual(video.seekTimes, [80 / 24, 90 / 24]);
});

test("reset drops source-specific state and cancels the pending frame callback", () => {
  const video = new VideoFrameCallbackVideo();
  const scheduler = new VideoFrameSeekScheduler(
    video as unknown as HTMLVideoElement,
    { fps: 24, frameCount: 912 },
  );

  scheduler.schedule(200 / 911, 38);
  assert.equal(video.callbacks.size, 1);

  scheduler.reset();
  assert.equal(video.callbacks.size, 0);

  scheduler.schedule(200 / 911, 38);
  assert.deepEqual(video.seekTimes, [200 / 24, 200 / 24]);
  assert.equal(video.callbacks.size, 1);
});
