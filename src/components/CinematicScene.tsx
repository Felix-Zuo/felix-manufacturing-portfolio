"use client";

import {
  motion,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";
import type { ReactNode } from "react";
import { useRef } from "react";

import styles from "./CinematicScene.module.css";

type SceneDuration = "hero" | "standard" | "long" | "extraLong";
type SceneAlign = "left" | "right" | "center";

type CinematicSceneProps = {
  align?: SceneAlign;
  children: ReactNode;
  className?: string;
  duration?: SceneDuration;
  id?: string;
  index: string;
  label: string;
};

const durationClasses: Record<SceneDuration, string> = {
  hero: styles.hero,
  standard: styles.standard,
  long: styles.long,
  extraLong: styles.extraLong,
};

const alignClasses: Record<SceneAlign, string> = {
  left: "",
  right: styles.alignRight,
  center: styles.alignCenter,
};

export function CinematicScene({
  align = "left",
  children,
  className = "",
  duration = "standard",
  id,
  index,
  label,
}: CinematicSceneProps) {
  const ref = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const progress = useSpring(scrollYProgress, { damping: 26, stiffness: 86, mass: 0.7 });
  const opacity = useTransform(progress, [0, 0.12, 0.84, 1], [0, 1, 1, 0]);
  const y = useTransform(progress, [0, 0.2, 0.75, 1], [110, 0, 0, -90]);
  const scale = useTransform(progress, [0, 0.25, 0.5, 0.78, 1], [0.9, 0.99, 1.018, 1, 0.95]);
  const rotateX = useTransform(progress, [0, 0.24, 0.76, 1], [7, 0, 0, -5]);
  const rotateY = useTransform(
    progress,
    [0, 0.24, 0.76, 1],
    align === "right" ? [-7, 0, 0, 5] : [7, 0, 0, -5],
  );
  const filter = useTransform(
    progress,
    [0, 0.14, 0.86, 1],
    ["blur(6px)", "blur(0px)", "blur(0px)", "blur(4px)"],
  );

  return (
    <section
      className={`${styles.scene} ${durationClasses[duration]} ${alignClasses[align]} ${className}`}
      data-cinematic-scene
      data-scene-label={label}
      id={id}
      ref={ref}
    >
      <div className={styles.sticky}>
        <div className={styles.inner}>
          <div aria-hidden="true" className={styles.chrome}>
            <span>Frame {index}</span>
            <i />
            <span>{label}</span>
          </div>
          <motion.div
            className={styles.content}
            style={
              reduceMotion
                ? undefined
                : { filter, opacity, rotateX, rotateY, scale, y }
            }
          >
            {children}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export function BulletTimeCard({
  children,
  className = "",
  direction = 1,
}: {
  children: ReactNode;
  className?: string;
  direction?: -1 | 1;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.96", "start 0.48"],
  });
  const progress = useSpring(scrollYProgress, { damping: 24, stiffness: 78, mass: 0.75 });
  const opacity = useTransform(progress, [0, 0.4, 1], [0, 0.72, 1]);
  const y = useTransform(progress, [0, 1], [54, 0]);
  const scale = useTransform(progress, [0, 0.78, 1], [0.92, 1.012, 1]);
  const rotateY = useTransform(progress, [0, 1], [direction * 8, 0]);

  return (
    <motion.div
      className={`${styles.card} ${className}`}
      ref={ref}
      style={reduceMotion ? undefined : { opacity, rotateY, scale, y }}
      transition={{ duration: 0.35 }}
      whileHover={reduceMotion ? undefined : { scale: 1.012 }}
    >
      {children}
    </motion.div>
  );
}
