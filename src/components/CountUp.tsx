"use client";

import { useEffect, useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";

import type { MetricCount } from "@/data/types";

const DURATION_MS = 1600;

function easeOutExpo(t: number) {
  return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

function render(template: string, n: number) {
  return template.replace("{n}", n.toLocaleString("en-US"));
}

export function CountUp({ count, fallback, className }: { count: MetricCount; fallback: string; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const reduceMotion = useReducedMotion();
  const [done, setDone] = useState(false);
  const [display, setDisplay] = useState(() => render(count.template, count.from));

  useEffect(() => {
    if (!inView) return;
    let frame: number;
    const start = performance.now();
    const step = (now: number) => {
      // Reduced motion: skip the tween, settle on the final value in one frame.
      const t = reduceMotion ? 1 : Math.min((now - start) / DURATION_MS, 1);
      const eased = easeOutExpo(t);
      const value = Math.round(count.from + (count.to - count.from) * eased);
      setDisplay(render(count.template, value));
      if (t < 1) {
        frame = requestAnimationFrame(step);
      } else {
        setDone(true);
      }
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [inView, reduceMotion, count.from, count.to, count.template]);

  return (
    <span ref={ref} className={className}>
      {done ? (count.final ?? fallback) : display}
    </span>
  );
}
