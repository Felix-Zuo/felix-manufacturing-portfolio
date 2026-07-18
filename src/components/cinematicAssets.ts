export type CinematicMediaProfile = "desktop" | "mobile";

export type CinematicAssetKey =
  | "journey"
  | "control-room"
  | "scene-notice"
  | "scene-system"
  | "scene-visibility"
  | "takt-live";

export type CinematicAssetSpec = {
  bytes?: number;
  key: CinematicAssetKey;
  type: "image" | "video";
  url: string;
};

export function createCinematicAssetManifest(
  profile: CinematicMediaProfile,
  mainUrl?: string,
): readonly CinematicAssetSpec[] {
  const mobile = profile === "mobile";
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
