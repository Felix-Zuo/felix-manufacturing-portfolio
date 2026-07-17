export type CinematicMediaProfile = "desktop" | "mobile";

export type CinematicAssetKey =
  | "journey"
  | "control-room"
  | "scene-notice"
  | "scene-system"
  | "scene-visibility"
  | "takt-live"
  | `hold-${string}`;

export type CinematicAssetSpec = {
  bytes?: number;
  key: CinematicAssetKey;
  type: "image" | "video";
  url: string;
};

export const CINEMATIC_CHAPTER_IDS = [
  "origin",
  "impact",
  "process",
  "notice",
  "takt",
  "visibility",
  "system",
  "close",
] as const;

const DESKTOP_HOLD_BYTES: Readonly<Record<string, number>> = {
  close: 262_836,
  impact: 434_292,
  notice: 433_734,
  origin: 495_794,
  process: 523_233,
  system: 468_327,
  takt: 393_514,
  visibility: 438_049,
};

const MOBILE_HOLD_BYTES: Readonly<Record<string, number>> = {
  close: 192_268,
  impact: 224_181,
  notice: 260_425,
  origin: 341_591,
  process: 369_179,
  system: 280_534,
  takt: 268_241,
  visibility: 243_807,
};

export function createCinematicAssetManifest(
  profile: CinematicMediaProfile,
  mainUrl?: string,
): readonly CinematicAssetSpec[] {
  const mobile = profile === "mobile";
  const holdBytes = mobile ? MOBILE_HOLD_BYTES : DESKTOP_HOLD_BYTES;
  const profileName = mobile ? "mobile" : "desktop";

  return [
    {
      bytes: mobile ? 7_928_586 : 11_846_094,
      key: "journey",
      type: "video",
      url:
        mainUrl ??
        `/media/felix-journey-stream-${profileName}.mp4`,
    },
    ...CINEMATIC_CHAPTER_IDS.map(
      (chapter): CinematicAssetSpec => ({
        bytes: holdBytes[chapter],
        key: `hold-${chapter}`,
        type: "video",
        url: `/media/holds/${chapter}-${profileName}.mp4`,
      }),
    ),
    {
      bytes: mobile ? 165_912 : 274_973,
      key: "control-room",
      type: "video",
      url: mobile
        ? "/media/control-room-loop-720p.webm"
        : "/media/control-room-loop.webm",
    },
    {
      bytes: 1_045_941,
      key: "takt-live",
      type: "video",
      url: "/evidence/takt-live-workbench.mp4",
    },
    {
      bytes: 122_136,
      key: "scene-notice",
      type: "image",
      url: "/evidence/notice-cinematic.png",
    },
    {
      bytes: 118_531,
      key: "scene-visibility",
      type: "image",
      url: "/evidence/visibility-cinematic.png",
    },
    {
      bytes: 145_323,
      key: "scene-system",
      type: "image",
      url: "/evidence/lab-cinematic.png",
    },
  ];
}
