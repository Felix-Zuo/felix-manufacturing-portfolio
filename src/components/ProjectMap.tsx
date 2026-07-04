"use client";

import { useRef } from "react";
import { motion, useScroll, useSpring } from "framer-motion";

import { projectCycle } from "@/data/profile";
import { Reveal } from "./Reveal";

export function ProjectMap() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.85", "end 0.35"],
  });
  const progress = useSpring(scrollYProgress, { stiffness: 90, damping: 24 });

  return (
    <div ref={ref} className="relative">
      <div className="absolute left-0 right-0 top-0 hidden h-px bg-slate-800 lg:block" aria-hidden="true">
        {/* Scroll-linked progress (not autonomous motion), so it stays active under reduced motion. */}
        <motion.div
          className="h-full origin-left bg-gradient-to-r from-amber-400 via-amber-400/80 to-emerald-400"
          style={{ scaleX: progress }}
        />
      </div>
      <ol className="grid gap-x-6 gap-y-10 pt-0 sm:grid-cols-2 lg:grid-cols-5 lg:pt-10">
        {projectCycle.map((step, index) => (
          <Reveal delay={index * 0.04} key={step.label}>
            <li className="relative border-l hairline pl-4 lg:border-l-0 lg:pl-0">
              <span
                className="absolute -left-px top-0 h-6 w-px bg-amber-400 lg:hidden"
                aria-hidden="true"
              />
              <p className="mono-label text-slate-600">{String(index + 1).padStart(2, "0")}</p>
              <h3 className="mt-2 text-sm font-semibold text-slate-100">{step.label}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">{step.detail}</p>
            </li>
          </Reveal>
        ))}
      </ol>
    </div>
  );
}
