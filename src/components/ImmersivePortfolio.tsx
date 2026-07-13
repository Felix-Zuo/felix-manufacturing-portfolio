"use client";

import { RoundedBox, useTexture } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  Bloom,
  ChromaticAberration,
  EffectComposer,
  Noise,
  Vignette,
} from "@react-three/postprocessing";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowDown,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Mail,
  Pause,
  Play,
} from "lucide-react";
import Link from "next/link";
import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from "react";
import * as THREE from "three";

import { profile } from "@/data/profile";

import styles from "./ImmersivePortfolio.module.css";

type TimelineState = {
  current: number;
  target: number;
  velocity: number;
};

type TimelineRef = MutableRefObject<TimelineState>;

type Chapter = {
  action?: {
    external?: boolean;
    href: string;
    label: string;
  };
  align: "left" | "right";
  eyebrow: string;
  id: string;
  label: string;
  metrics?: Array<{ label: string; value: string }>;
  progress: number;
  summary: string;
  title: string;
};

const chapters: Chapter[] = [
  {
    align: "left",
    eyebrow: "Manufacturing project coordination",
    id: "origin",
    label: "Entry",
    progress: 0,
    summary:
      "A continuous journey through trial production, workflow control, and operations visibility.",
    title: "Manufacturing project chaos, turned into measurable improvement.",
  },
  {
    align: "right",
    eyebrow: "Measured impact",
    id: "impact",
    label: "Signal",
    metrics: [
      { label: "Notice preparation", value: "< 1 min" },
      { label: "Trial adjustment", value: "3 d to 1 d" },
      { label: "Scrap reduction", value: "about 90%" },
    ],
    progress: 0.13,
    summary:
      "Real workflow outcomes, represented with public-safe evidence and synthetic data.",
    title: "Outcomes first. Tools second.",
  },
  {
    align: "left",
    eyebrow: "Trial production / internal grinding",
    id: "project-map",
    label: "Process",
    progress: 0.24,
    summary:
      "A clean grinding cell isolates the critical operation: controlled contact, visible evidence, and a slower decision moment before ramp-up.",
    title: "Observe the process before changing it.",
  },
  {
    action: {
      href: "/case-studies/production-notice-workflow-standardization",
      label: "Open case study",
    },
    align: "right",
    eyebrow: "Case 01 / workflow control",
    id: "case-studies",
    label: "Notice",
    progress: 0.37,
    summary:
      "Structured inputs turn repeated cross-system checking into a reviewable release packet while final control stays human.",
    title: "Production Notice Workflow Standardization",
  },
  {
    action: {
      href: "/case-studies/trial-production-takt-simulation-changeover-improvement",
      label: "Open case study",
    },
    align: "left",
    eyebrow: "Case 02 / flow simulation",
    id: "portfolio-lab",
    label: "Takt",
    progress: 0.53,
    summary:
      "Full-line simulation exposes bottlenecks, buffers, waiting, and blocking before physical trial-and-error consumes more time and material.",
    title: "Trial Production Takt Simulation",
  },
  {
    action: {
      href: "/case-studies/supply-production-delivery-operations-visibility",
      label: "Open case study",
    },
    align: "right",
    eyebrow: "Case 03 / operations visibility",
    id: "methodology",
    label: "Visibility",
    progress: 0.69,
    summary:
      "Scattered spreadsheet exports become a consistent operating view for supply, production, delivery, and exception closure.",
    title: "Supply-Production-Delivery Visibility",
  },
  {
    action: {
      external: true,
      href: profile.github,
      label: "Explore GitHub",
    },
    align: "left",
    eyebrow: "Connected systems",
    id: "about",
    label: "System",
    progress: 0.84,
    summary:
      "Operations intelligence, manufacturing data literacy, Six Sigma learning, and evidence-first agent verification extend the same control logic.",
    title: "One operating method, several public tools.",
  },
  {
    action: {
      href: `mailto:${profile.email}`,
      label: "Email Felix",
    },
    align: "right",
    eyebrow: "Contact / final frame",
    id: "contact",
    label: "Close",
    progress: 0.96,
    summary:
      "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
    title: "Build the next improvement loop.",
  },
];

function focusWindow(progress: number, center: number, radius: number) {
  const distance = Math.abs(progress - center);
  if (distance >= radius) return 0;
  const normalized = 1 - distance / radius;
  return normalized * normalized * (3 - 2 * normalized);
}

function dampedFilmProgress(raw: number) {
  const holds = [0.24, 0.37, 0.53, 0.69, 0.84];
  let result = raw;

  holds.forEach((hold) => {
    const distance = raw - hold;
    const influence = Math.exp(-(distance * distance) / 0.0015);
    result -= distance * influence * 0.2;
  });

  return THREE.MathUtils.clamp(result, 0, 1);
}

function advanceTimeline(state: TimelineState, responsiveness: number, delta: number) {
  state.current = THREE.MathUtils.damp(state.current, state.target, responsiveness, delta);
  return state.current;
}

function updatePerspectiveFov(camera: THREE.PerspectiveCamera, targetFov: number, delta: number) {
  camera.fov = THREE.MathUtils.damp(camera.fov, targetFov, 4, delta);
  camera.updateProjectionMatrix();
}

function Bearing({ scale = 1 }: { scale?: number }) {
  const balls = useMemo(
    () =>
      Array.from({ length: 12 }, (_, index) => {
        const angle = (index / 12) * Math.PI * 2;
        return [Math.cos(angle) * 0.78, Math.sin(angle) * 0.78, 0] as const;
      }),
    [],
  );

  return (
    <group scale={scale}>
      <mesh castShadow>
        <torusGeometry args={[1.03, 0.23, 20, 72]} />
        <meshStandardMaterial color="#aeb7c2" metalness={0.88} roughness={0.2} />
      </mesh>
      <mesh castShadow>
        <torusGeometry args={[0.52, 0.16, 18, 64]} />
        <meshStandardMaterial color="#d6dde4" metalness={0.9} roughness={0.17} />
      </mesh>
      {balls.map((position, index) => (
        <mesh castShadow key={index} position={position}>
          <sphereGeometry args={[0.115, 12, 12]} />
          <meshStandardMaterial color="#8a949f" metalness={0.94} roughness={0.14} />
        </mesh>
      ))}
    </group>
  );
}

function ArmSegment({
  end,
  radius = 0.16,
  start,
}: {
  end: [number, number, number];
  radius?: number;
  start: [number, number, number];
}) {
  const transform = useMemo(() => {
    const a = new THREE.Vector3(...start);
    const b = new THREE.Vector3(...end);
    const midpoint = a.clone().add(b).multiplyScalar(0.5);
    const direction = b.clone().sub(a);
    const quaternion = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      direction.clone().normalize(),
    );

    return { length: direction.length(), midpoint, quaternion };
  }, [end, start]);

  return (
    <mesh castShadow position={transform.midpoint} quaternion={transform.quaternion}>
      <cylinderGeometry args={[radius, radius * 1.08, transform.length, 16]} />
      <meshStandardMaterial color="#c6ccd2" metalness={0.58} roughness={0.34} />
    </mesh>
  );
}

function MechanicalArm({ flip = false }: { flip?: boolean }) {
  const sign = flip ? -1 : 1;
  const points: Array<[number, number, number]> = [
    [0, 0, 0],
    [-0.12 * sign, 0.72, 0.05],
    [-0.48 * sign, 1.4, -0.08],
    [-0.82 * sign, 2.12, 0.08],
  ];

  return (
    <group>
      <mesh castShadow position={[0, 0.12, 0]}>
        <cylinderGeometry args={[0.35, 0.44, 0.22, 24]} />
        <meshStandardMaterial color="#1b222a" metalness={0.76} roughness={0.27} />
      </mesh>
      {points.slice(0, -1).map((point, index) => (
        <ArmSegment end={points[index + 1]} key={index} radius={index === 0 ? 0.14 : 0.1} start={point} />
      ))}
      {points.slice(1).map((point, index) => (
        <group key={index} position={point} rotation={[Math.PI / 2, 0, 0]}>
          <mesh castShadow>
            <cylinderGeometry args={[0.2, 0.2, 0.26, 20]} />
            <meshStandardMaterial color="#202830" metalness={0.82} roughness={0.24} />
          </mesh>
          <mesh position={[0, 0.18, 0]}>
            <cylinderGeometry args={[0.06, 0.06, 0.03, 14]} />
            <meshStandardMaterial color="#f5b83d" emissive="#a8640b" emissiveIntensity={1.2} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function ProjectDisplay({ href, image }: { href: string; image: string }) {
  const texture = useTexture(image);
  const displayTexture = useMemo(() => {
    const clone = texture.clone();
    clone.colorSpace = THREE.SRGBColorSpace;
    clone.anisotropy = 8;
    clone.needsUpdate = true;
    return clone;
  }, [texture]);

  useEffect(() => () => displayTexture.dispose(), [displayTexture]);

  const openProject = useCallback(() => {
    window.location.assign(href);
  }, [href]);

  return (
    <group>
      <RoundedBox args={[4.7, 2.98, 0.24]} castShadow radius={0.08} smoothness={3}>
        <meshStandardMaterial color="#141b23" metalness={0.74} roughness={0.25} />
      </RoundedBox>
      <mesh
        onClick={openProject}
        onPointerOut={() => {
          document.body.style.cursor = "";
        }}
        onPointerOver={() => {
          document.body.style.cursor = "pointer";
        }}
        position={[0, 0, 0.128]}
      >
        <planeGeometry args={[4.42, 2.63]} />
        <meshBasicMaterial map={displayTexture} toneMapped={false} />
      </mesh>
      <mesh position={[-2.18, 1.29, 0.16]}>
        <sphereGeometry args={[0.035, 10, 10]} />
        <meshBasicMaterial color="#45d59b" />
      </mesh>
    </group>
  );
}

function ScreenRig({
  chapterProgress,
  flip,
  href,
  image,
  position,
  rotationY,
  timeline,
}: {
  chapterProgress: number;
  flip: boolean;
  href: string;
  image: string;
  position: [number, number, number];
  rotationY: number;
  timeline: TimelineRef;
}) {
  const rigRef = useRef<THREE.Group>(null);
  const displayRef = useRef<THREE.Group>(null);
  const { size } = useThree();
  const sign = flip ? -1 : 1;

  useFrame(({ clock }, delta) => {
    const focus = focusWindow(timeline.current.current, chapterProgress, 0.075);
    const time = clock.getElapsedTime();

    if (rigRef.current) {
      const targetRotation = rotationY + (1 - focus) * sign * 0.18;
      rigRef.current.rotation.y = THREE.MathUtils.damp(
        rigRef.current.rotation.y,
        targetRotation,
        4,
        delta,
      );
    }

    if (displayRef.current) {
      displayRef.current.position.y = 2.36 + Math.sin(time * 0.55) * 0.035 * (1 - focus);
      displayRef.current.rotation.z = THREE.MathUtils.damp(
        displayRef.current.rotation.z,
        sign * (1 - focus) * 0.025,
        4,
        delta,
      );
    }
  });

  return (
    <group position={position} ref={rigRef} rotation={[0, rotationY, 0]}>
      {size.width >= 700 && <MechanicalArm flip={flip} />}
      <pointLight color="#b8d8ef" distance={8} intensity={3.6} position={[0, 2, 2]} />
      <group position={[1.42 * sign, 2.36, -0.42]} ref={displayRef}>
        <ProjectDisplay href={href} image={image} />
      </group>
    </group>
  );
}

function SparkField({ timeline }: { timeline: TimelineRef }) {
  const geometryRef = useRef<THREE.BufferGeometry>(null);
  const timeRef = useRef(0);
  const count = 58;
  const seeds = useMemo(
    () =>
      Array.from({ length: count }, (_, index) => ({
        delay: ((index * 47) % 97) / 97,
        lift: 0.45 + ((index * 29) % 70) / 100,
        spread: (((index * 61) % 100) / 100 - 0.5) * 1.5,
      })),
    [],
  );
  const positions = useMemo(() => new Float32Array(count * 3), []);

  useFrame((_, delta) => {
    const focus = focusWindow(timeline.current.current, 0.24, 0.075);
    const timeScale = THREE.MathUtils.lerp(1, 0.14, focus);
    timeRef.current += delta * timeScale;

    seeds.forEach((seed, index) => {
      const life = (timeRef.current * 1.7 + seed.delay) % 1;
      positions[index * 3] = life * seed.spread;
      positions[index * 3 + 1] = life * seed.lift - life * life * 0.62;
      positions[index * 3 + 2] = life * (0.45 + seed.spread * 0.16);
    });

    const attribute = geometryRef.current?.getAttribute("position");
    if (attribute) attribute.needsUpdate = true;
  });

  return (
    <points position={[-0.92, 0.32, 0.72]}>
      <bufferGeometry ref={geometryRef}>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        blending={THREE.AdditiveBlending}
        color="#ffb126"
        depthWrite={false}
        opacity={0.92}
        size={0.019}
        sizeAttenuation
        transparent
      />
    </points>
  );
}

function GrindingCell({ timeline }: { timeline: TimelineRef }) {
  const wheelRef = useRef<THREE.Mesh>(null);
  const bearingRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    const focus = focusWindow(timeline.current.current, 0.24, 0.075);
    const timeScale = THREE.MathUtils.lerp(1, 0.12, focus);
    if (wheelRef.current) wheelRef.current.rotation.z += delta * 9 * timeScale;
    if (bearingRef.current) bearingRef.current.rotation.z -= delta * 1.4 * timeScale;
  });

  return (
    <group position={[7.1, -1.7, -27]} rotation={[0, -1, 0]}>
      <RoundedBox args={[5.2, 4.5, 3.1]} castShadow position={[0, 2.2, 0]} radius={0.12} smoothness={3}>
        <meshStandardMaterial color="#d2d7da" metalness={0.32} roughness={0.38} />
      </RoundedBox>
      <RoundedBox args={[4.3, 2.9, 0.18]} position={[0, 2.25, 1.58]} radius={0.08} smoothness={3}>
        <meshStandardMaterial color="#11181f" metalness={0.64} roughness={0.26} />
      </RoundedBox>
      <group position={[0, 2.12, 1.74]}>
        <group ref={bearingRef} rotation={[0, 0, 0.18]}>
          <Bearing scale={0.72} />
        </group>
        <mesh castShadow position={[-0.91, 0.34, 0.38]} ref={wheelRef} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.22, 24]} />
          <meshStandardMaterial color="#6e7780" metalness={0.48} roughness={0.7} />
        </mesh>
        <SparkField timeline={timeline} />
        <pointLight color="#ff9d26" distance={3.5} intensity={3.4} position={[-0.9, 0.32, 0.9]} />
      </group>
      <mesh castShadow position={[0, 0.18, 0]}>
        <boxGeometry args={[5.7, 0.36, 3.5]} />
        <meshStandardMaterial color="#202830" metalness={0.68} roughness={0.31} />
      </mesh>
      <mesh position={[1.8, 3.77, 1.7]}>
        <boxGeometry args={[0.46, 0.12, 0.08]} />
        <meshStandardMaterial color="#55dca7" emissive="#147a59" emissiveIntensity={1.8} />
      </mesh>
    </group>
  );
}

function RailWorld({ curve }: { curve: THREE.CatmullRomCurve3 }) {
  const leftCurve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        curve.getSpacedPoints(28).map((point) => point.clone().add(new THREE.Vector3(-0.46, -1.84, 0))),
        false,
        "catmullrom",
        0.35,
      ),
    [curve],
  );
  const rightCurve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        curve.getSpacedPoints(28).map((point) => point.clone().add(new THREE.Vector3(0.46, -1.84, 0))),
        false,
        "catmullrom",
        0.35,
      ),
    [curve],
  );
  const signalCurve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        curve.getSpacedPoints(28).map((point) => point.clone().add(new THREE.Vector3(0, -1.71, 0))),
        false,
        "catmullrom",
        0.35,
      ),
    [curve],
  );

  return (
    <group>
      {[leftCurve, rightCurve].map((rail, index) => (
        <mesh castShadow key={index}>
          <tubeGeometry args={[rail, 180, 0.065, 8, false]} />
          <meshStandardMaterial color="#77818b" metalness={0.94} roughness={0.2} />
        </mesh>
      ))}
      <mesh>
        <tubeGeometry args={[signalCurve, 180, 0.018, 6, false]} />
        <meshStandardMaterial color="#f2ad32" emissive="#d0770c" emissiveIntensity={3.2} />
      </mesh>
    </group>
  );
}

function CleanFactoryEnvelope() {
  const frames = [-6, -24, -42, -60, -78, -96, -114, -132];

  return (
    <group>
      <mesh receiveShadow position={[0, -2.02, -63]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[23, 168]} />
        <meshStandardMaterial color="#182027" metalness={0.48} roughness={0.4} />
      </mesh>
      {frames.map((z) => (
        <group key={z} position={[0, 0, z]}>
          <mesh castShadow position={[-7.6, 2.4, 0]}>
            <boxGeometry args={[0.32, 8.8, 0.42]} />
            <meshStandardMaterial color="#313940" metalness={0.72} roughness={0.32} />
          </mesh>
          <mesh castShadow position={[7.6, 2.4, 0]}>
            <boxGeometry args={[0.32, 8.8, 0.42]} />
            <meshStandardMaterial color="#313940" metalness={0.72} roughness={0.32} />
          </mesh>
          <mesh castShadow position={[0, 6.65, 0]}>
            <boxGeometry args={[15.5, 0.3, 0.42]} />
            <meshStandardMaterial color="#3a4248" metalness={0.72} roughness={0.32} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function FinalPortal() {
  return (
    <group position={[0, 0.4, -138]}>
      <mesh>
        <torusGeometry args={[3.2, 0.08, 12, 72]} />
        <meshStandardMaterial color="#d9e1e8" emissive="#8ea5bd" emissiveIntensity={1.2} metalness={0.72} roughness={0.22} />
      </mesh>
      <mesh>
        <torusGeometry args={[2.7, 0.025, 8, 72]} />
        <meshStandardMaterial color="#49d6a0" emissive="#16996b" emissiveIntensity={2.8} />
      </mesh>
      <pointLight color="#8cc9ff" distance={22} intensity={18} position={[0, 0, 2]} />
    </group>
  );
}

function IndustrialJourney({ reducedMotion, timeline }: { reducedMotion: boolean; timeline: TimelineRef }) {
  const { camera, size } = useThree();
  const lookMatrix = useMemo(() => new THREE.Matrix4(), []);
  const targetQuaternion = useMemo(() => new THREE.Quaternion(), []);
  const rollQuaternion = useMemo(() => new THREE.Quaternion(), []);
  const cameraCurve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        [
          new THREE.Vector3(0, 1.65, 11),
          new THREE.Vector3(-0.6, 1.45, 2),
          new THREE.Vector3(1.8, 1.2, -9),
          new THREE.Vector3(1.4, 1.45, -20),
          new THREE.Vector3(-0.9, 1.5, -34),
          new THREE.Vector3(-1.6, 1.7, -50),
          new THREE.Vector3(1.2, 1.5, -68),
          new THREE.Vector3(1.55, 1.7, -86),
          new THREE.Vector3(-1.25, 1.5, -103),
          new THREE.Vector3(-1.1, 1.75, -119),
          new THREE.Vector3(0, 1.05, -133),
        ],
        false,
        "catmullrom",
        0.42,
      ),
    [],
  );
  const lookTargets = useMemo(
    () => [
      { position: new THREE.Vector3(5.75, 0.6, -26.1), progress: 0.24 },
      { position: new THREE.Vector3(-5.8, 0.25, -52), progress: 0.37 },
      { position: new THREE.Vector3(5.8, 0.25, -75), progress: 0.53 },
      { position: new THREE.Vector3(-5.8, 0.25, -99), progress: 0.69 },
      { position: new THREE.Vector3(5.8, 0.25, -121), progress: 0.84 },
    ],
    [],
  );

  useFrame((_, delta) => {
    const responsiveness = reducedMotion ? 20 : 5.2;
    const raw = advanceTimeline(timeline.current, responsiveness, delta);
    const progress = dampedFilmProgress(raw);
    const currentPosition = cameraCurve.getPointAt(progress);
    const forward = cameraCurve.getPointAt(Math.min(progress + 0.035, 1));
    const target = forward.clone();
    let strongestFocus = 0;

    lookTargets.forEach((lookTarget) => {
      const focus = focusWindow(raw, lookTarget.progress, 0.075);
      if (focus > strongestFocus) strongestFocus = focus;
      target.lerp(lookTarget.position, focus * 0.7);
    });

    const mobileOffset = size.width < 700 ? 0.42 : 0;
    currentPosition.y += mobileOffset;
    camera.position.lerp(currentPosition, 1 - Math.exp(-delta * responsiveness));
    lookMatrix.lookAt(camera.position, target, camera.up);
    targetQuaternion.setFromRotationMatrix(lookMatrix);
    const roll = Math.sin(progress * Math.PI * 5) * 0.018 * (1 - strongestFocus);
    rollQuaternion.setFromAxisAngle(new THREE.Vector3(0, 0, 1), roll);
    targetQuaternion.multiply(rollQuaternion);
    camera.quaternion.slerp(targetQuaternion, 1 - Math.exp(-delta * 5.4));

    if (camera instanceof THREE.PerspectiveCamera) {
      const velocityStretch = Math.min(timeline.current.velocity * 1.4, 2.6);
      const targetFov = 44 + velocityStretch - strongestFocus * 3.5;
      updatePerspectiveFov(camera, targetFov, delta);
    }
  });

  return (
    <>
      <color attach="background" args={["#070a0d"]} />
      <fog attach="fog" args={["#070a0d", 14, 56]} />
      <ambientLight color="#b9c7d5" intensity={0.96} />
      <hemisphereLight color="#dbe8f4" groundColor="#202a31" intensity={1.8} />
      <directionalLight castShadow color="#f7f2e8" intensity={1.15} position={[4, 10, 8]} shadow-mapSize-height={1024} shadow-mapSize-width={1024} />
      <directionalLight color="#7fa9ce" intensity={0.48} position={[-8, 4, -20]} />

      <CleanFactoryEnvelope />
      <RailWorld curve={cameraCurve} />
      <GrindingCell timeline={timeline} />
      <ScreenRig
        chapterProgress={0.37}
        flip={false}
        href="/case-studies/production-notice-workflow-standardization"
        image="/evidence/notice-workbench-product.png"
        position={[-6.15, -1.75, -52]}
        rotationY={0.36}
        timeline={timeline}
      />
      <ScreenRig
        chapterProgress={0.53}
        flip
        href="/case-studies/trial-production-takt-simulation-changeover-improvement"
        image="/evidence/takt-simulator-product.png"
        position={[6.15, -1.75, -75]}
        rotationY={-0.36}
        timeline={timeline}
      />
      <ScreenRig
        chapterProgress={0.69}
        flip={false}
        href="/case-studies/supply-production-delivery-operations-visibility"
        image="/evidence/excel-ops-product.png"
        position={[-6.05, -1.75, -99]}
        rotationY={0.36}
        timeline={timeline}
      />
      <ScreenRig
        chapterProgress={0.84}
        flip
        href="https://github.com/Felix-Zuo/factory-ops-intelligence-platform"
        image="/evidence/ops-platform-product.png"
        position={[6.05, -1.75, -121]}
        rotationY={-0.36}
        timeline={timeline}
      />
      <FinalPortal />

      {!reducedMotion && (
        <EffectComposer multisampling={0}>
          <Bloom intensity={0.38} luminanceSmoothing={0.18} luminanceThreshold={1.22} mipmapBlur />
          <ChromaticAberration offset={new THREE.Vector2(0.00022, 0.00022)} radialModulation />
          <Noise opacity={0.018} />
          <Vignette darkness={0.68} eskil={false} offset={0.18} />
        </EffectComposer>
      )}
    </>
  );
}

function ChapterAction({ action }: { action: NonNullable<Chapter["action"]> }) {
  const content = (
    <>
      {action.label}
      <ArrowUpRight aria-hidden="true" size={15} />
    </>
  );

  if (action.external) {
    return (
      <a className={styles.chapterAction} href={action.href} rel="noreferrer" target="_blank">
        {content}
      </a>
    );
  }

  if (action.href.startsWith("mailto:")) {
    return (
      <a className={styles.chapterAction} href={action.href}>
        <Mail aria-hidden="true" size={15} />
        {action.label}
      </a>
    );
  }

  return (
    <Link className={styles.chapterAction} href={action.href}>
      {content}
    </Link>
  );
}

function ChapterHud({ chapter }: { chapter: Chapter }) {
  return (
    <AnimatePresence mode="wait">
      <motion.section
        animate={{ filter: "blur(0px)", opacity: 1, x: 0 }}
        className={`${styles.chapter} ${chapter.align === "right" ? styles.chapterRight : ""}`}
        exit={{ filter: "blur(6px)", opacity: 0, x: chapter.align === "right" ? 36 : -36 }}
        initial={{ filter: "blur(6px)", opacity: 0, x: chapter.align === "right" ? 36 : -36 }}
        key={chapter.id}
        transition={{ duration: 0.52, ease: [0.2, 0.72, 0.2, 1] }}
      >
        <p className={styles.chapterEyebrow}>{chapter.eyebrow}</p>
        {chapter.id === "origin" && <p className={styles.subtleName}>Felix Zuo</p>}
        <h1 className={styles.chapterTitle}>{chapter.title}</h1>
        <p className={styles.chapterSummary}>{chapter.summary}</p>
        {chapter.metrics && (
          <dl className={styles.metrics}>
            {chapter.metrics.map((metric) => (
              <div key={metric.label}>
                <dt>{metric.label}</dt>
                <dd>{metric.value}</dd>
              </div>
            ))}
          </dl>
        )}
        <div className={styles.chapterControls}>
          {chapter.action && <ChapterAction action={chapter.action} />}
          {chapter.id === "origin" && (
            <button
              className={styles.chapterAction}
              onClick={() => document.getElementById("case-studies")?.scrollIntoView({ behavior: "smooth" })}
              type="button"
            >
              Enter the journey
              <ArrowDown aria-hidden="true" size={15} />
            </button>
          )}
        </div>
      </motion.section>
    </AnimatePresence>
  );
}

export function ImmersivePortfolio() {
  const trackRef = useRef<HTMLElement>(null);
  const timeline = useRef<TimelineState>({ current: 0, target: 0, velocity: 0 });
  const reduceMotion = useReducedMotion() ?? false;
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const activeChapter = chapters[activeIndex];

  const scrollToChapter = useCallback(
    (index: number) => {
      const track = trackRef.current;
      if (!track) return;
      const chapter = chapters[THREE.MathUtils.clamp(index, 0, chapters.length - 1)];
      if (reduceMotion) {
        timeline.current.current = chapter.progress;
        timeline.current.target = chapter.progress;
        setActiveIndex(index);
        return;
      }
      const range = Math.max(track.offsetHeight - window.innerHeight, 1);
      window.scrollTo({
        behavior: reduceMotion ? "auto" : "smooth",
        top: track.offsetTop + range * chapter.progress,
      });
    },
    [reduceMotion],
  );

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    let animationFrame = 0;
    let lastY = window.scrollY;
    let lastTime = performance.now();

    const update = () => {
      animationFrame = 0;
      const range = Math.max(track.offsetHeight - window.innerHeight, 1);
      const raw = THREE.MathUtils.clamp((window.scrollY - track.offsetTop) / range, 0, 1);
      const now = performance.now();
      const elapsed = Math.max(now - lastTime, 16);
      const velocity = Math.abs(window.scrollY - lastY) / elapsed;
      timeline.current.target = paused ? timeline.current.target : raw;
      timeline.current.velocity = THREE.MathUtils.lerp(timeline.current.velocity, velocity, 0.28);
      const chapterProgress = paused ? timeline.current.target : raw;

      let nextIndex = 0;
      chapters.forEach((chapter, index) => {
        if (chapterProgress >= chapter.progress - 0.035) nextIndex = index;
      });
      setActiveIndex((current) => (current === nextIndex ? current : nextIndex));
      lastY = window.scrollY;
      lastTime = now;
    };

    const queueUpdate = () => {
      if (!animationFrame) animationFrame = window.requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", queueUpdate, { passive: true });
    window.addEventListener("resize", queueUpdate);
    return () => {
      if (animationFrame) window.cancelAnimationFrame(animationFrame);
      window.removeEventListener("scroll", queueUpdate);
      window.removeEventListener("resize", queueUpdate);
    };
  }, [paused]);

  return (
    <main className={`${styles.immersiveHome} immersive-home`} ref={trackRef}>
      {chapters.slice(1).map((chapter) => (
        <span
          aria-hidden="true"
          className={styles.anchor}
          id={chapter.id}
          key={chapter.id}
          style={{ top: `${chapter.progress * 100}%` }}
        />
      ))}

      <div className={styles.stage}>
        <div aria-hidden="true" className={styles.canvasWrap}>
          <Canvas
            camera={{ far: 180, fov: 43, near: 0.08, position: [0, 1.65, 11] }}
            dpr={[1, 1.45]}
            fallback={<div className={styles.webglFallback} />}
            gl={{ alpha: false, antialias: true, powerPreference: "high-performance" }}
            onCreated={({ gl }) => {
              gl.outputColorSpace = THREE.SRGBColorSpace;
              gl.toneMapping = THREE.ACESFilmicToneMapping;
              gl.toneMappingExposure = 1.08;
            }}
            performance={{ min: 0.55 }}
            shadows
          >
            <Suspense fallback={null}>
              <IndustrialJourney reducedMotion={reduceMotion} timeline={timeline} />
            </Suspense>
          </Canvas>
        </div>

        <div aria-hidden="true" className={styles.frameShade} />
        <div className={styles.hud}>
          <div className={styles.filmMeta}>
            <span>FZ / 01</span>
            <span>{activeChapter.label}</span>
            <span>{String(activeIndex + 1).padStart(2, "0")} / {String(chapters.length).padStart(2, "0")}</span>
          </div>

          <ChapterHud chapter={activeChapter} />

          <div className={styles.timelineControl}>
            <button
              aria-label="Previous chapter"
              disabled={activeIndex === 0}
              onClick={() => scrollToChapter(activeIndex - 1)}
              title="Previous chapter"
              type="button"
            >
              <ChevronLeft aria-hidden="true" size={17} />
            </button>
            <div className={styles.progressRail}>
              {chapters.map((chapter, index) => (
                <button
                  aria-label={`Go to ${chapter.label}`}
                  className={index === activeIndex ? styles.activeChapter : ""}
                  key={chapter.id}
                  onClick={() => scrollToChapter(index)}
                  title={chapter.label}
                  type="button"
                />
              ))}
            </div>
            <button
              aria-label={paused ? "Resume camera" : "Pause camera"}
              onClick={() => setPaused((current) => !current)}
              title={paused ? "Resume camera" : "Pause camera"}
              type="button"
            >
              {paused ? <Play aria-hidden="true" size={15} /> : <Pause aria-hidden="true" size={15} />}
            </button>
            <button
              aria-label="Next chapter"
              disabled={activeIndex === chapters.length - 1}
              onClick={() => scrollToChapter(activeIndex + 1)}
              title="Next chapter"
              type="button"
            >
              <ChevronRight aria-hidden="true" size={17} />
            </button>
          </div>

          <div className={styles.cornerLinks}>
            <a aria-label="Email Felix" href={`mailto:${profile.email}`} title="Email Felix">
              <Mail aria-hidden="true" size={16} />
            </a>
            <a aria-label="Felix Zuo on GitHub" href={profile.github} rel="noreferrer" target="_blank" title="GitHub portfolio">
              <GitBranch aria-hidden="true" size={16} />
            </a>
          </div>

          <p className={styles.scrollCue}>Scroll to move the camera</p>
        </div>

      </div>
    </main>
  );
}

useTexture.preload("/evidence/notice-workbench-product.png");
useTexture.preload("/evidence/takt-simulator-product.png");
useTexture.preload("/evidence/excel-ops-product.png");
useTexture.preload("/evidence/ops-platform-product.png");
