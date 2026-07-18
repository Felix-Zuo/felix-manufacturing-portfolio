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
  close: 468_347,
  impact: 558_498,
  notice: 479_472,
  origin: 517_875,
  process: 483_460,
  system: 476_864,
  takt: 402_923,
  visibility: 454_642,
};

const MOBILE_HOLD_BYTES: Readonly<Record<string, number>> = {
  close: 277_999,
  impact: 299_335,
  notice: 258_063,
  origin: 348_730,
  process: 560_688,
  system: 287_729,
  takt: 396_068,
  visibility: 247_419,
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
      bytes: mobile ? 13_189_855 : 20_294_056,
      key: "journey",
      type: "video",
      url:
        mainUrl ??
        `/media/felix-journey-stream-${profileName}.mp4?v=10`,
    },
    ...CINEMATIC_CHAPTER_IDS.map(
      (chapter): CinematicAssetSpec => ({
        bytes: holdBytes[chapter],
        key: `hold-${chapter}`,
        type: "video",
        url: `/media/holds/${chapter}-${profileName}.mp4?v=10`,
      }),
    ),
    {
      bytes: mobile ? 201_016 : 352_812,
      key: "control-room",
      type: "video",
      url: mobile
        ? "/media/control-room-loop-720p.webm?v=10"
        : "/media/control-room-loop.webm?v=10",
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
