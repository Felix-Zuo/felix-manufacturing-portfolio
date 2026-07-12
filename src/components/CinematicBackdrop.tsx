"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useReducedMotion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

type TimelineState = {
  index: number;
  local: number;
  sceneCount: number;
  velocity: number;
};

type TimelineRef = {
  current: TimelineState;
};

const SCENE_SPACING = 14;
const NODE_COLORS = ["#fbbf24", "#60a5fa", "#34d399", "#f59e0b"];

function cinematicEase(value: number) {
  const t = THREE.MathUtils.clamp(value, 0, 1);

  if (t < 0.28) {
    return THREE.MathUtils.smoothstep(t / 0.28, 0, 1) * 0.42;
  }

  if (t < 0.72) {
    return 0.42 + ((t - 0.28) / 0.44) * 0.16;
  }

  return 0.58 + THREE.MathUtils.smootherstep((t - 0.72) / 0.28, 0, 1) * 0.42;
}

function ParticleField({ depth }: { depth: number }) {
  const positions = useMemo(() => {
    const values = new Float32Array(180 * 3);

    for (let index = 0; index < 180; index += 1) {
      const seed = index + 1;
      values[index * 3] = Math.sin(seed * 12.9898) * 6.6;
      values[index * 3 + 1] = ((seed * 37) % 60) / 10 - 2.1;
      values[index * 3 + 2] = 7 - ((seed * 53) % Math.floor(depth * 10)) / 10;
    }

    return values;
  }, [depth]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#8fa1bb" opacity={0.34} size={0.025} transparent />
    </points>
  );
}

function World({ sceneCount, timeline }: { sceneCount: number; timeline: TimelineRef }) {
  const coreRef = useRef<THREE.Group>(null);
  const nodeRefs = useRef<Array<THREE.Group | null>>([]);
  const pulseRefs = useRef<Array<THREE.Mesh | null>>([]);
  const cinematicTime = useRef(0);
  const pathDepth = Math.max((sceneCount - 1) * SCENE_SPACING + 24, 80);

  useFrame((frameState, delta) => {
    const camera = frameState.camera;
    const timelineValue = timeline.current;
    const easedLocal = cinematicEase(timelineValue.local);
    const scenePosition = Math.min(
      sceneCount - 1,
      timelineValue.index + easedLocal,
    );
    const focus = 1 - Math.min(1, Math.abs(timelineValue.local - 0.5) * 2);
    const timeScale = THREE.MathUtils.lerp(0.16, 1, 1 - focus);
    const targetZ = 8 - scenePosition * SCENE_SPACING;
    const side = timelineValue.index % 2 === 0 ? -1 : 1;
    const targetX = side * Math.sin(timelineValue.local * Math.PI) * 0.9;
    const targetY = 1.05 + Math.sin(scenePosition * 0.8) * 0.18;

    cinematicTime.current += delta * timeScale;
    camera.position.x = THREE.MathUtils.damp(camera.position.x, targetX, 3.8, delta);
    camera.position.y = THREE.MathUtils.damp(camera.position.y, targetY, 3.8, delta);
    camera.position.z = THREE.MathUtils.damp(camera.position.z, targetZ, 4.4, delta);
    camera.lookAt(targetX * -0.12, 0.15, targetZ - 8.2);

    if (camera instanceof THREE.PerspectiveCamera) {
      camera.fov = THREE.MathUtils.damp(camera.fov, 46 - focus * 3.5, 3.2, delta);
      camera.updateProjectionMatrix();
    }

    if (coreRef.current) {
      coreRef.current.rotation.z = cinematicTime.current * 0.11;
    }

    nodeRefs.current.forEach((node, index) => {
      if (!node) return;
      const nodeFocus = Math.max(0, 1 - Math.abs(scenePosition - index));
      const nodeScale = 1 + nodeFocus * 0.13;
      node.scale.setScalar(THREE.MathUtils.damp(node.scale.x, nodeScale, 5, delta));
      node.rotation.z += delta * (0.018 + nodeFocus * 0.045) * timeScale;
    });

    pulseRefs.current.forEach((pulse, index) => {
      if (!pulse) return;
      const phase = (cinematicTime.current * 0.055 + index / pulseRefs.current.length) % 1;
      pulse.position.z = 5 - phase * pathDepth;
      pulse.position.x = index % 2 === 0 ? -2.35 : 2.35;
    });
  });

  return (
    <>
      <color attach="background" args={["#05080f"]} />
      <fog attach="fog" args={["#05080f", 12, 40]} />
      <ambientLight intensity={0.32} color="#8fa1bb" />
      <directionalLight color="#fbbf24" intensity={1.1} position={[4, 6, 8]} />
      <pointLight color="#60a5fa" intensity={18} distance={26} position={[-4, 1, 4]} />

      <gridHelper
        args={[pathDepth + 40, 72, "#274469", "#172033"]}
        position={[0, -2, -pathDepth / 2 + 7]}
      />
      <gridHelper
        args={[pathDepth + 40, 72, "#274469", "#111c2e"]}
        position={[-7, 0, -pathDepth / 2 + 7]}
        rotation={[0, 0, Math.PI / 2]}
      />
      <gridHelper
        args={[pathDepth + 40, 72, "#274469", "#111c2e"]}
        position={[7, 0, -pathDepth / 2 + 7]}
        rotation={[0, 0, Math.PI / 2]}
      />

      <mesh position={[-2.35, -1.72, -pathDepth / 2 + 6]}>
        <boxGeometry args={[0.035, 0.035, pathDepth]} />
        <meshStandardMaterial color="#60a5fa" emissive="#2563eb" emissiveIntensity={1.8} />
      </mesh>
      <mesh position={[2.35, -1.72, -pathDepth / 2 + 6]}>
        <boxGeometry args={[0.035, 0.035, pathDepth]} />
        <meshStandardMaterial color="#60a5fa" emissive="#2563eb" emissiveIntensity={1.8} />
      </mesh>
      <mesh position={[0, -1.86, -pathDepth / 2 + 6]}>
        <boxGeometry args={[0.018, 0.018, pathDepth]} />
        <meshStandardMaterial color="#fbbf24" emissive="#f59e0b" emissiveIntensity={2.2} />
      </mesh>

      <group ref={coreRef}>
        {Array.from({ length: sceneCount }, (_, index) => {
          const color = NODE_COLORS[index % NODE_COLORS.length];
          const z = -index * SCENE_SPACING;

          return (
            <group
              key={`node-${index}`}
              position={[0, 0, z]}
              ref={(node) => {
                nodeRefs.current[index] = node;
              }}
            >
              <mesh>
                <torusGeometry args={[2.5, 0.018, 8, 96]} />
                <meshBasicMaterial color={color} opacity={0.5} transparent />
              </mesh>
              <mesh rotation={[0, 0, Math.PI / 4]}>
                <torusGeometry args={[1.95, 0.012, 8, 72]} />
                <meshBasicMaterial color={color} opacity={0.25} transparent />
              </mesh>
              <mesh>
                <boxGeometry args={[4.9, 2.8, 0.04]} />
                <meshBasicMaterial color={color} opacity={0.12} transparent wireframe />
              </mesh>
              <mesh rotation={[0.45, 0.35, 0]}>
                <octahedronGeometry args={[0.38, 0]} />
                <meshStandardMaterial
                  color={color}
                  emissive={color}
                  emissiveIntensity={1.4}
                  metalness={0.82}
                  roughness={0.2}
                />
              </mesh>
              {[-1.45, -0.72, 0.72, 1.45].map((x, stationIndex) => (
                <mesh key={`${index}-${x}`} position={[x, -1.28, 0.08]}>
                  <boxGeometry args={[0.34, 0.24 + stationIndex * 0.07, 0.28]} />
                  <meshStandardMaterial
                    color={stationIndex === 2 ? "#fbbf24" : "#1f3655"}
                    emissive={stationIndex === 2 ? "#f59e0b" : "#0f2847"}
                    emissiveIntensity={stationIndex === 2 ? 1.5 : 0.7}
                    metalness={0.72}
                    roughness={0.32}
                  />
                </mesh>
              ))}
            </group>
          );
        })}
      </group>

      {Array.from({ length: 18 }, (_, index) => (
        <mesh
          key={`pulse-${index}`}
          ref={(node) => {
            pulseRefs.current[index] = node;
          }}
        >
          <sphereGeometry args={[index % 5 === 0 ? 0.07 : 0.035, 8, 8]} />
          <meshBasicMaterial color={index % 5 === 0 ? "#fbbf24" : "#60a5fa"} />
        </mesh>
      ))}

      <ParticleField depth={pathDepth} />
    </>
  );
}

export function CinematicBackdrop({ sceneCount }: { sceneCount: number }) {
  const reduceMotion = useReducedMotion();
  const [activeScene, setActiveScene] = useState(0);
  const timeline = useRef<TimelineState>({
    index: 0,
    local: 0,
    sceneCount,
    velocity: 0,
  });

  useEffect(() => {
    const sceneElements = Array.from(
      document.querySelectorAll<HTMLElement>("[data-cinematic-scene]"),
    );
    let bounds: Array<{ top: number; height: number }> = [];
    let animationFrame = 0;
    let lastScrollY = window.scrollY;
    let lastTimestamp = performance.now();
    let lastScene = -1;

    const measure = () => {
      bounds = sceneElements.map((element) => ({
        top: element.getBoundingClientRect().top + window.scrollY,
        height: Math.max(element.offsetHeight, window.innerHeight),
      }));
    };

    const update = () => {
      animationFrame = 0;
      const anchor = window.scrollY + window.innerHeight * 0.12;
      let sceneIndex = 0;

      for (let index = 0; index < bounds.length; index += 1) {
        if (anchor >= bounds[index].top) sceneIndex = index;
      }

      const scene = bounds[sceneIndex];
      const now = performance.now();
      const elapsed = Math.max(now - lastTimestamp, 16);
      const velocity = Math.abs(window.scrollY - lastScrollY) / elapsed;

      if (scene) {
        const scrollableDistance = Math.max(scene.height - window.innerHeight, 1);
        timeline.current = {
          index: sceneIndex,
          local: THREE.MathUtils.clamp((window.scrollY - scene.top) / scrollableDistance, 0, 1),
          sceneCount: bounds.length || sceneCount,
          velocity,
        };
      }

      if (lastScene !== sceneIndex) {
        lastScene = sceneIndex;
        setActiveScene(sceneIndex);
      }

      lastScrollY = window.scrollY;
      lastTimestamp = now;
    };

    const queueUpdate = () => {
      if (animationFrame) return;
      animationFrame = window.requestAnimationFrame(update);
    };

    const resizeObserver = new ResizeObserver(() => {
      measure();
      queueUpdate();
    });

    measure();
    update();
    resizeObserver.observe(document.body);
    window.addEventListener("scroll", queueUpdate, { passive: true });
    window.addEventListener("resize", measure);

    return () => {
      if (animationFrame) window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      window.removeEventListener("scroll", queueUpdate);
      window.removeEventListener("resize", measure);
    };
  }, [sceneCount]);

  return (
    <div aria-hidden="true" className="cinematic-backdrop">
      {!reduceMotion && (
        <Canvas
          camera={{ far: 220, fov: 46, near: 0.1, position: [0, 1.05, 8] }}
          dpr={[1, 1.5]}
          fallback={<div className="cinematic-webgl-fallback" />}
          gl={{ alpha: false, antialias: false, powerPreference: "high-performance" }}
          performance={{ min: 0.55 }}
        >
          <World sceneCount={sceneCount} timeline={timeline} />
        </Canvas>
      )}
      <div className="cinematic-atmosphere" />
      <div className="cinematic-vignette" />
      <div className="cinematic-scene-rail">
        <span>{String(activeScene + 1).padStart(2, "0")}</span>
        <div>
          {Array.from({ length: sceneCount }, (_, index) => (
            <i className={index === activeScene ? "is-active" : ""} key={index} />
          ))}
        </div>
        <span>{String(sceneCount).padStart(2, "0")}</span>
      </div>
    </div>
  );
}
