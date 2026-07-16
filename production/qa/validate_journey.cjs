/* eslint-disable @typescript-eslint/no-require-imports -- NODE_PATH exposes the bundled Playwright runtime only to CommonJS. */
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const baseUrl = process.env.JOURNEY_URL || "http://127.0.0.1:3000/";
const outputDir = path.resolve(__dirname, "..", "renders", "browser-qa");
fs.mkdirSync(outputDir, { recursive: true });

const failures = [];
const report = { baseUrl, desktop: {}, mobile: {}, reducedMotion: {} };

function assert(condition, message) {
  if (!condition) failures.push(message);
}

async function collectRuntimeErrors(page, bucket) {
  page.on("console", (message) => {
    if (message.type() === "error") bucket.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => bucket.push(`pageerror: ${error.message}`));
}

async function waitForVideo(page) {
  await page.waitForSelector("video");
  await page.waitForFunction(() => {
    const video = document.querySelector("video");
    return video && video.readyState >= HTMLMediaElement.HAVE_METADATA && video.duration > 0;
  });
}

async function snapshotState(page) {
  return page.evaluate(() => {
    const root = document.querySelector("section[data-scene]");
    const video = document.querySelector("video");
    if (!root || !video) throw new Error("journey root or video is missing");
    const overflowing = [...document.querySelectorAll("button, a")]
      .filter((node) => node instanceof HTMLElement)
      .filter((node) => !node.closest('[data-scene-hotspot="true"]'))
      .filter((node) => node.scrollWidth > node.clientWidth + 1)
      .map((node) => node.getAttribute("aria-label") || node.textContent?.trim() || node.tagName);
    return {
      bodyOverflow: document.documentElement.scrollWidth - window.innerWidth,
      currentSrc: video.currentSrc,
      currentTime: video.currentTime,
      duration: video.duration,
      finale: root.getAttribute("data-finale"),
      magneticStop: root.getAttribute("data-magnetic-stop"),
      progress: Number.parseFloat(root.style.getPropertyValue("--journey-progress") || "0"),
      reducedMotion: root.getAttribute("data-reduced-motion"),
      scene: root.getAttribute("data-scene"),
      videoHeight: video.videoHeight,
      videoWidth: video.videoWidth,
      overflowingControls: overflowing,
    };
  });
}

async function main() {
  const browser = await chromium.launch({ channel: "msedge", headless: true });
  try {
    const desktopContext = await browser.newContext({
      reducedMotion: "no-preference",
      viewport: { width: 1440, height: 900 },
    });
    const desktop = await desktopContext.newPage();
    const desktopErrors = [];
    await collectRuntimeErrors(desktop, desktopErrors);
    const response = await desktop.goto(baseUrl, { waitUntil: "networkidle" });
    assert(response && response.ok(), `desktop HTTP failed: ${response?.status()}`);
    await waitForVideo(desktop);
    await desktop.locator("section[data-scene]").focus();
    const initial = await snapshotState(desktop);
    assert(initial.videoWidth === 960 && initial.videoHeight === 540, "desktop video is not 960x540");
    assert(Math.abs(initial.duration - 38) < 0.01, `desktop duration is ${initial.duration}`);
    assert(initial.bodyOverflow <= 1, `desktop horizontal overflow is ${initial.bodyOverflow}px`);

    await desktop.mouse.move(720, 450);
    await desktop.mouse.wheel(0, 100);
    await desktop.waitForTimeout(650);
    const oneNotch = await snapshotState(desktop);
    const notchSeconds = oneNotch.currentTime - initial.currentTime;
    assert(notchSeconds > 0.08 && notchSeconds < 0.45, `one wheel notch advanced ${notchSeconds.toFixed(3)}s`);

    for (let index = 0; index < 28; index += 1) {
      await desktop.mouse.wheel(0, 100);
      await desktop.waitForTimeout(45);
      const state = await snapshotState(desktop);
      if (state.magneticStop === "132") break;
    }
    await desktop.waitForTimeout(700);
    const atStop = await snapshotState(desktop);
    assert(atStop.magneticStop === "132", `first magnetic stop was ${atStop.magneticStop}`);
    assert(Math.abs(atStop.currentTime - 131 / 24) < 0.12, `F132 stop time was ${atStop.currentTime.toFixed(3)}s`);

    await desktop.mouse.wheel(0, 100);
    await desktop.waitForTimeout(700);
    const released = await snapshotState(desktop);
    assert(released.magneticStop !== "132", "F132 magnetic stop did not release");
    assert(released.currentTime > atStop.currentTime, "timeline did not advance after stop release");

    await desktop.screenshot({ path: path.join(outputDir, "desktop-journey.png"), fullPage: true });
    await desktop.keyboard.press("End");
    await desktop.waitForTimeout(1800);
    const finale = await snapshotState(desktop);
    assert(finale.finale === "true", "End key did not reveal the portfolio summary");
    assert(await desktop.getByRole("heading", { name: "Execution made visible." }).isVisible(), "final summary heading is hidden");
    await desktop.screenshot({ path: path.join(outputDir, "desktop-finale.png"), fullPage: true });
    report.desktop = { initial, oneNotch, notchSeconds, atStop, released, finale, runtimeErrors: desktopErrors };
    assert(desktopErrors.length === 0, `desktop runtime errors: ${desktopErrors.join(" | ")}`);
    await desktopContext.close();

    const mobileContext = await browser.newContext({
      deviceScaleFactor: 1,
      isMobile: true,
      reducedMotion: "no-preference",
      viewport: { width: 390, height: 844 },
    });
    const mobile = await mobileContext.newPage();
    const mobileErrors = [];
    await collectRuntimeErrors(mobile, mobileErrors);
    await mobile.goto(baseUrl, { waitUntil: "networkidle" });
    await waitForVideo(mobile);
    await mobile.locator("section[data-scene]").focus();
    await mobile.mouse.wheel(0, 100);
    await mobile.waitForTimeout(650);
    const mobileState = await snapshotState(mobile);
    assert(mobileState.videoWidth === 540 && mobileState.videoHeight === 960, "mobile video is not 540x960");
    assert(mobileState.currentSrc.includes("felix-journey-mobile.mp4"), `mobile source is ${mobileState.currentSrc}`);
    assert(mobileState.bodyOverflow <= 1, `mobile horizontal overflow is ${mobileState.bodyOverflow}px`);
    assert(mobileState.overflowingControls.length === 0, `mobile controls overflow: ${mobileState.overflowingControls.join(", ")}`);
    await mobile.screenshot({ path: path.join(outputDir, "mobile-journey.png"), fullPage: true });
    report.mobile = { state: mobileState, runtimeErrors: mobileErrors };
    assert(mobileErrors.length === 0, `mobile runtime errors: ${mobileErrors.join(" | ")}`);
    await mobileContext.close();

    const reducedContext = await browser.newContext({
      reducedMotion: "reduce",
      viewport: { width: 1440, height: 900 },
    });
    const reduced = await reducedContext.newPage();
    const reducedErrors = [];
    await collectRuntimeErrors(reduced, reducedErrors);
    await reduced.goto(baseUrl, { waitUntil: "networkidle" });
    await reduced.waitForSelector("section[data-scene]");
    const reducedState = await snapshotState(reduced);
    assert(reducedState.reducedMotion === "true", "reduced-motion mode did not activate");
    assert(reducedState.bodyOverflow <= 1, `reduced-motion horizontal overflow is ${reducedState.bodyOverflow}px`);
    await reduced.screenshot({ path: path.join(outputDir, "reduced-motion.png"), fullPage: true });
    report.reducedMotion = { state: reducedState, runtimeErrors: reducedErrors };
    assert(reducedErrors.length === 0, `reduced-motion runtime errors: ${reducedErrors.join(" | ")}`);
    await reducedContext.close();
  } finally {
    await browser.close();
  }

  report.ok = failures.length === 0;
  report.failures = failures;
  console.log(`JOURNEY_BROWSER_QA=${JSON.stringify(report)}`);
  if (failures.length) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
