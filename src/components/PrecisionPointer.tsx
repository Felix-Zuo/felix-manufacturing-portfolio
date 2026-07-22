"use client";

import {
  useCallback,
  useEffect,
  useRef,
  type PointerEvent as ReactPointerEvent,
  type RefObject,
} from "react";

import styles from "./PrecisionPointer.module.css";

type PrecisionPointerFrame = {
  nx: number;
  ny: number;
  root: HTMLElement;
  x: number;
  y: number;
};

type PrecisionPointerOptions = {
  enabled?: boolean;
  onFrame?: (frame: PrecisionPointerFrame) => void;
  onLeave?: (root: HTMLElement) => void;
};

const INTERACTIVE_SELECTOR =
  "a[href], button:not(:disabled), [role='button']:not([aria-disabled='true'])";

function clearPointerState(root: HTMLElement) {
  root.removeAttribute("data-pointer-present");
  root.removeAttribute("data-pointer-interactive");
  root.removeAttribute("data-pointer-mode");
}

export function usePrecisionPointer(
  rootRef: RefObject<HTMLElement | null>,
  options: PrecisionPointerOptions = {},
) {
  const frameRef = useRef<number | null>(null);
  const { enabled = true, onFrame, onLeave } = options;

  const resetPointer = useCallback(() => {
    if (frameRef.current !== null) {
      window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    const root = rootRef.current;
    if (!root) return;
    clearPointerState(root);
    onLeave?.(root);
  }, [onLeave, rootRef]);

  useEffect(() => {
    if (!enabled) resetPointer();
  }, [enabled, resetPointer]);

  useEffect(() => resetPointer, [resetPointer]);

  const handlePointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (event.pointerType === "touch" || !enabled) {
        return;
      }
      const root = rootRef.current;
      if (!root) return;

      const bounds = root.getBoundingClientRect();
      const width = Math.max(bounds.width, 1);
      const height = Math.max(bounds.height, 1);
      const x = Math.min(Math.max(event.clientX - bounds.left, 0), width);
      const y = Math.min(Math.max(event.clientY - bounds.top, 0), height);
      const nx = x / width - 0.5;
      const ny = y / height - 0.5;
      const target = event.target as HTMLElement;
      const interactiveTarget = target.closest<HTMLElement>(INTERACTIVE_SELECTOR);
      const mode = interactiveTarget?.dataset.pointerRole
        ?? (interactiveTarget ? "action" : "scene");

      if (frameRef.current !== null) {
        window.cancelAnimationFrame(frameRef.current);
      }
      frameRef.current = window.requestAnimationFrame(() => {
        root.style.setProperty("--pointer-x", `${x.toFixed(2)}px`);
        root.style.setProperty("--pointer-y", `${y.toFixed(2)}px`);
        root.style.setProperty("--pointer-depth-x", `${(nx * 7).toFixed(2)}px`);
        root.style.setProperty("--pointer-depth-y", `${(ny * 5).toFixed(2)}px`);
        root.dataset.pointerMode = mode;
        root.toggleAttribute("data-pointer-present", true);
        root.toggleAttribute("data-pointer-interactive", Boolean(interactiveTarget));
        onFrame?.({ nx, ny, root, x, y });
        frameRef.current = null;
      });
    },
    [enabled, onFrame, rootRef],
  );

  return {
    handlePointerLeave: resetPointer,
    handlePointerMove,
    resetPointer,
  };
}

export function PrecisionPointer() {
  return (
    <span aria-hidden="true" className={styles.field}>
      <span className={styles.depthPlane} />
      <span className={styles.lens} />
      <span className={styles.reticle}>
        <span className={styles.horizontalAxis} />
        <span className={styles.verticalAxis} />
        <span className={styles.centerPoint} />
      </span>
    </span>
  );
}
