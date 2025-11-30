/**
 * RobotViewer Component - Interactive 3D Robot Viewer
 * Main component that combines Three.js canvas, URDF model, and joint controls
 */

import { Grid, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import React, { Suspense, useCallback, useState } from "react";
import JointControls from "./JointControls";
import RobotModel from "./RobotModel";
import styles from "./styles.module.css";
import type { JointState, RobotViewerProps } from "./types";

// Scene lighting component
const SceneLighting: React.FC = () => {
  return (
    <>
      {/* Ambient light for overall illumination */}
      <ambientLight intensity={0.4} />
      {/* Main directional light (sun-like) */}
      <directionalLight
        position={[5, 10, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      {/* Fill light from opposite side */}
      <directionalLight position={[-5, 5, -5]} intensity={0.3} />
      {/* Rim light for depth */}
      <pointLight position={[0, 5, -10]} intensity={0.5} />
    </>
  );
};

// Ground grid component
const GroundGrid: React.FC = () => {
  return (
    <Grid
      args={[10, 10]}
      cellSize={0.5}
      cellThickness={0.5}
      cellColor="#3a3a5c"
      sectionSize={2}
      sectionThickness={1}
      sectionColor="#64ffda"
      fadeDistance={15}
      fadeStrength={1}
      followCamera={false}
      infiniteGrid={true}
    />
  );
};

// Loading fallback component
const LoadingFallback: React.FC = () => {
  return (
    <mesh>
      <boxGeometry args={[0.5, 0.5, 0.5]} />
      <meshStandardMaterial color="#64ffda" wireframe />
    </mesh>
  );
};

export const RobotViewer: React.FC<RobotViewerProps> = ({
  urdfPath,
  width = "100%",
  height = 500,
  showControls = true,
  initialJointAngles = {},
  onJointChange,
}) => {
  const [joints, setJoints] = useState<JointState[]>([]);
  const [jointAngles, setJointAngles] =
    useState<Record<string, number>>(initialJointAngles);
  const [isLoading, setIsLoading] = useState(true);

  // Handle joints loaded from URDF
  const handleJointsLoaded = useCallback(
    (loadedJoints: JointState[]) => {
      setJoints(loadedJoints);

      // Initialize joint angles if not provided
      const initialAngles: Record<string, number> = { ...initialJointAngles };
      loadedJoints.forEach((joint) => {
        if (!(joint.name in initialAngles)) {
          initialAngles[joint.name] = joint.angle;
        }
      });
      setJointAngles(initialAngles);
      setIsLoading(false);
    },
    [initialJointAngles]
  );

  // Handle joint angle change from controls
  const handleJointChange = useCallback(
    (jointName: string, angle: number) => {
      setJointAngles((prev) => ({
        ...prev,
        [jointName]: angle,
      }));

      // Update joints state for display
      setJoints((prev) =>
        prev.map((joint) =>
          joint.name === jointName ? { ...joint, angle } : joint
        )
      );

      // Call external callback if provided
      if (onJointChange) {
        onJointChange(jointName, angle);
      }
    },
    [onJointChange]
  );

  return (
    <div className={styles.robotViewerContainer}>
      <div
        className={styles.canvasContainer}
        style={{
          width,
          height: typeof height === "number" ? `${height}px` : height,
        }}
      >
        {isLoading && (
          <div className={styles.loadingOverlay}>Loading robot model...</div>
        )}
        <Canvas
          className={styles.canvas}
          camera={{ position: [2, 2, 2], fov: 50 }}
          shadows
        >
          <SceneLighting />
          <GroundGrid />

          <Suspense fallback={<LoadingFallback />}>
            <RobotModel
              urdfPath={urdfPath}
              jointAngles={jointAngles}
              onJointsLoaded={handleJointsLoaded}
            />
          </Suspense>

          {/* Camera orbit controls */}
          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            minDistance={0.5}
            maxDistance={10}
            target={[0, 0.5, 0]}
          />
        </Canvas>

        <div className={styles.instructions}>
          Drag to rotate • Scroll to zoom • Right-click to pan
        </div>
      </div>

      {showControls && (
        <JointControls joints={joints} onJointChange={handleJointChange} />
      )}
    </div>
  );
};

export default RobotViewer;
