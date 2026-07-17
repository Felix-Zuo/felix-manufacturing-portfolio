"use client";

import { useEffect, useMemo, useState } from "react";

import type {
  CinematicAssetKey,
  CinematicAssetSpec,
} from "./cinematicAssets";

type CinematicPreloadState = {
  degraded: boolean;
  error: string | null;
  loadedBytes: number;
  progress: number;
  ready: boolean;
  totalBytes: number;
  urls: Readonly<Partial<Record<CinematicAssetKey, string>>>;
};

const EMPTY_STATE: CinematicPreloadState = {
  degraded: false,
  error: null,
  loadedBytes: 0,
  progress: 0,
  ready: false,
  totalBytes: 0,
  urls: {},
};

const CONCURRENCY = 3;
const PROGRESS_UPDATE_INTERVAL = 80;

function originalUrls(assets: readonly CinematicAssetSpec[]) {
  return Object.fromEntries(
    assets.map((asset) => [asset.key, asset.url]),
  ) as Partial<Record<CinematicAssetKey, string>>;
}

export function useCinematicPreloader(
  assets: readonly CinematicAssetSpec[],
  enabled: boolean,
) {
  const manifestIdentity = useMemo(
    () => assets.map(({ bytes, key, url }) => `${key}:${bytes ?? 0}:${url}`).join("|"),
    [assets],
  );
  const [state, setState] = useState<CinematicPreloadState>(() => ({
    ...EMPTY_STATE,
    ready: !enabled,
    urls: enabled ? {} : originalUrls(assets),
  }));

  useEffect(() => {
    if (!enabled || assets.length === 0) {
      return;
    }

    const abortController = new AbortController();
    const createdObjectUrls: string[] = [];
    const resolvedUrls: Partial<Record<CinematicAssetKey, string>> = {};
    const totalBytes = assets.reduce(
      (total, asset) => total + Math.max(asset.bytes ?? 1, 1),
      0,
    );
    let loadedBytes = 0;
    let lastProgressUpdate = 0;
    let nextAssetIndex = 0;
    const failures: string[] = [];

    const publishProgress = (force = false) => {
      const now = performance.now();
      if (!force && now - lastProgressUpdate < PROGRESS_UPDATE_INTERVAL) return;
      lastProgressUpdate = now;
      const progress = Math.min(loadedBytes / Math.max(totalBytes, 1), 0.995);
      setState((current) => ({
        ...current,
        loadedBytes,
        progress,
        totalBytes,
      }));
    };

    const loadAsset = async (asset: CinematicAssetSpec) => {
      const response = await fetch(asset.url, {
        cache: "force-cache",
        signal: abortController.signal,
      });
      if (!response.ok) {
        throw new Error(`${asset.url} returned ${response.status}`);
      }

      const declaredBytes = Math.max(asset.bytes ?? 1, 1);
      const reader = response.body?.getReader();
      if (!reader) {
        const blob = await response.blob();
        loadedBytes += declaredBytes;
        publishProgress(true);
        const objectUrl = URL.createObjectURL(blob);
        createdObjectUrls.push(objectUrl);
        resolvedUrls[asset.key] = objectUrl;
        return;
      }

      const chunks: ArrayBuffer[] = [];
      let assetLoadedBytes = 0;
      while (true) {
        const result = await reader.read();
        if (result.done) break;
        const chunk = new Uint8Array(result.value.byteLength);
        chunk.set(result.value);
        chunks.push(chunk.buffer);
        assetLoadedBytes += result.value.byteLength;
        const creditedBytes = Math.min(assetLoadedBytes, declaredBytes);
        const previousCreditedBytes = Math.min(
          assetLoadedBytes - result.value.byteLength,
          declaredBytes,
        );
        loadedBytes += creditedBytes - previousCreditedBytes;
        publishProgress();
      }

      if (assetLoadedBytes < declaredBytes) {
        loadedBytes += declaredBytes - assetLoadedBytes;
      }
      publishProgress(true);
      const contentType =
        response.headers.get("content-type") ??
        (asset.type === "image" ? "image/png" : "video/mp4");
      const objectUrl = URL.createObjectURL(
        new Blob(chunks, { type: contentType }),
      );
      createdObjectUrls.push(objectUrl);
      resolvedUrls[asset.key] = objectUrl;
    };

    const worker = async () => {
      while (!abortController.signal.aborted) {
        const assetIndex = nextAssetIndex;
        nextAssetIndex += 1;
        const asset = assets[assetIndex];
        if (!asset) return;

        try {
          await loadAsset(asset);
        } catch (error) {
          if (abortController.signal.aborted) return;
          failures.push(error instanceof Error ? error.message : String(error));
          resolvedUrls[asset.key] = asset.url;
          loadedBytes += Math.max(asset.bytes ?? 1, 1);
          publishProgress(true);
        }
      }
    };

    queueMicrotask(() => {
      if (abortController.signal.aborted) return;
      setState({
        ...EMPTY_STATE,
        totalBytes,
      });
    });

    void Promise.all(
      Array.from(
        { length: Math.min(CONCURRENCY, assets.length) },
        () => worker(),
      ),
    ).then(() => {
      if (abortController.signal.aborted) return;
      setState({
        degraded: failures.length > 0,
        error: failures[0] ?? null,
        loadedBytes: totalBytes,
        progress: 1,
        ready: true,
        totalBytes,
        urls: resolvedUrls,
      });
    });

    return () => {
      abortController.abort();
      createdObjectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [assets, enabled, manifestIdentity]);

  return state;
}
