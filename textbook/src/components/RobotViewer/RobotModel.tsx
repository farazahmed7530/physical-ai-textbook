/**
 * RobotModel Component - Interactive 3D Robot Arm
 * Built with Three.js primitives for reliable rendering
 */

import { useFrame } from "@react-three/fiber";
import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import type { JointState, RobotModelProps } from "./types";

// Joint configuration for the robot arm
const JOINT_CONFIG = [
  { name: "base_joint", min: -Math.PI, max: Math.PI, axis: "y" },
  { name: "shoulder_joint", min: -Math.PI / 2, max: Math.PI / 2, axis: "x" },
  { name: "elbow_joint", min: -2.35, max: 2.35, axis: "x" },
  { name: "wrist_joint", min: -Math.PI, max: Math.PI, axis: "y" },
];

// Colors
const COLORS = {
  base: "#4a4a5c",
  turntable: "#64ffda",
  upperArm: "#8a8a9c",
  forearm: "#ff8c42",
  wrist: "#64ffda",
  gripper: "#4a4a5c",
};

export const RobotModel: React.FC<RobotModelProps> = ({
  jointAngles,
  onJointsLoaded,
}) => {
  const baseRef = useRef<THREE.Group>(null);
  const turntableRef = useRef<THREE.Group>(null);
  const upperArmRef = useRef<THREE.Group>(null);
  const forearmRef = useRef<THREE.Group>(null);
  const wristRef = useRef<THREE.Group>(null);

  // Initialize joints on mount
  useEffect(() => {
    const joints: JointState[] = JOINT_CONFIG.map((config) => ({
      name: config.name,
      angle: 0,
      min: config.min,
      max: config.max,
    }));
    onJointsLoaded?.(joints);
  }, [onJointsLoaded]);

  // Update joint rotations
  useFrame(() => {
    if (turntableRef.current && jointAngles.base_joint !== undefined) {
      turntableRef.current.rotation.y = jointAngles.base_joint;
    }
    if (upperArmRef.current && jointAngles.shoulder_joint !== undefined) {
      upperArmRef.current.rotation.x = jointAngles.shoulder_joint;
    }
    if (forearmRef.current && jointAngles.elbow_joint !== undefined) {
      forearmRef.current.rotation.x = jointAngles.elbow_joint;
    }
    if (wristRef.current && jointAngles.wrist_joint !== undefined) {
      wristRef.current.rotation.y = jointAngles.wrist_joint;
    }
  });

  return (
    <group ref={baseRef} position={[0, 0, 0]}>
      {/* Base - Fixed cylinder */}
      <mesh position={[0, 0.025, 0]}>
        <cylinderGeometry args={[0.15, 0.15, 0.05, 32]} />
        <meshStandardMaterial color={COLORS.base} />
      </mesh>

      {/* Turntable - Rotates around Y axis (base_joint) */}
      <group ref={turntableRef} position={[0, 0.05, 0]}>
        <mesh position={[0, 0.04, 0]}>
          <cylinderGeometry args={[0.1, 0.1, 0.08, 32]} />
          <meshStandardMaterial color={COLORS.turntable} />
        </mesh>

        {/* Upper Arm pivot point */}
        <group ref={upperArmRef} position={[0, 0.08, 0]}>
          {/* Upper Arm */}
          <mesh position={[0, 0.15, 0]}>
            <boxGeometry args={[0.06, 0.3, 0.06]} />
            <meshStandardMaterial color={COLORS.upperArm} />
          </mesh>

          {/* Forearm pivot point */}
          <group ref={forearmRef} position={[0, 0.3, 0]}>
            {/* Forearm */}
            <mesh position={[0, 0.125, 0]}>
              <boxGeometry args={[0.05, 0.25, 0.05]} />
              <meshStandardMaterial color={COLORS.forearm} />
            </mesh>

            {/* Wrist pivot point */}
            <group ref={wristRef} position={[0, 0.25, 0]}>
              {/* Wrist */}
              <mesh position={[0, 0.03, 0]}>
                <cylinderGeometry args={[0.03, 0.03, 0.06, 16]} />
                <meshStandardMaterial color={COLORS.wrist} />
              </mesh>

              {/* End Effector / Gripper */}
              <group position={[0, 0.06, 0]}>
                {/* Gripper base */}
                <mesh position={[0, 0.01, 0]}>
                  <boxGeometry args={[0.08, 0.02, 0.04]} />
                  <meshStandardMaterial color={COLORS.gripper} />
                </mesh>
                {/* Left finger */}
                <mesh position={[0.03, 0.04, 0]}>
                  <boxGeometry args={[0.02, 0.06, 0.04]} />
                  <meshStandardMaterial color={COLORS.forearm} />
                </mesh>
                {/* Right finger */}
                <mesh position={[-0.03, 0.04, 0]}>
                  <boxGeometry args={[0.02, 0.06, 0.04]} />
                  <meshStandardMaterial color={COLORS.forearm} />
                </mesh>
              </group>
            </group>
          </group>
        </group>
      </group>
    </group>
  );
};

export default RobotModel;
