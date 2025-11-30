/**
 * RobotModel Component - Loads and renders URDF robot model
 * Uses urdf-loader to parse URDF files and render in Three.js
 */

import { useThree } from "@react-three/fiber";
import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import type { URDFJoint, URDFRobot } from "urdf-loader";
import URDFLoader from "urdf-loader";
import type { JointState, RobotModelProps } from "./types";

export const RobotModel: React.FC<RobotModelProps> = ({
  urdfPath,
  jointAngles,
  onJointsLoaded,
}) => {
  const robotRef = useRef<URDFRobot | null>(null);
  const groupRef = useRef<THREE.Group>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const { scene } = useThree();

  // Load URDF model
  useEffect(() => {
    const loader = new URDFLoader();

    // Set the package path for mesh loading (relative to public folder)
    loader.packages = {
      "": "/urdf/",
    };

    loader.load(urdfPath, (robot: URDFRobot) => {
      robotRef.current = robot;

      // Center the robot
      const box = new THREE.Box3().setFromObject(robot);
      const center = box.getCenter(new THREE.Vector3());
      robot.position.sub(center);
      robot.position.y -= box.min.y - center.y;

      // Add robot to the group
      if (groupRef.current) {
        // Clear previous robot if any
        while (groupRef.current.children.length > 0) {
          groupRef.current.remove(groupRef.current.children[0]);
        }
        groupRef.current.add(robot);
      }

      // Extract joint information
      const joints: JointState[] = [];
      Object.entries(robot.joints).forEach(([name, joint]) => {
        const urdfJoint = joint as URDFJoint;
        if (
          urdfJoint.jointType === "revolute" ||
          urdfJoint.jointType === "continuous"
        ) {
          joints.push({
            name,
            angle: urdfJoint.angle || 0,
            min: urdfJoint.limit?.lower ?? -Math.PI,
            max: urdfJoint.limit?.upper ?? Math.PI,
          });
        }
      });

      if (onJointsLoaded) {
        onJointsLoaded(joints);
      }

      setIsLoaded(true);
    });

    return () => {
      if (robotRef.current && groupRef.current) {
        groupRef.current.remove(robotRef.current);
      }
    };
  }, [urdfPath, onJointsLoaded]);

  // Update joint angles when they change
  useEffect(() => {
    if (robotRef.current && isLoaded) {
      Object.entries(jointAngles).forEach(([jointName, angle]) => {
        const joint = robotRef.current?.joints[jointName] as
          | URDFJoint
          | undefined;
        if (joint && typeof joint.setJointValue === "function") {
          joint.setJointValue(angle);
        }
      });
    }
  }, [jointAngles, isLoaded]);

  return <group ref={groupRef} />;
};

export default RobotModel;
