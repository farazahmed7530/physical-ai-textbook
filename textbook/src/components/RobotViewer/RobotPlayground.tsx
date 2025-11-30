/**
 * RobotPlayground Component - Interactive 3D Robot Viewer with Code Display
 * Shows URDF/Python code alongside the 3D view with highlighting when joints change
 */

import React, { useCallback, useState } from "react";
import RobotViewer from "./RobotViewer";
import styles from "./playground.module.css";

// URDF code snippets for each joint
const urdfJointSnippets: Record<string, string> = {
  base_joint: `<!-- Base Joint - Rotation around vertical axis -->
<joint name="base_joint" type="revolute">
  <parent link="base_link"/>
  <child link="turntable_link"/>
  <origin xyz="0 0 0.05" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-3.14159" upper="3.14159"
         effort="100" velocity="1.0"/>
</joint>`,

  shoulder_joint: `<!-- Shoulder Joint - Rotation for upper arm -->
<joint name="shoulder_joint" type="revolute">
  <parent link="turntable_link"/>
  <child link="upper_arm_link"/>
  <origin xyz="0 0 0.08" rpy="0 0 0"/>
  <axis xyz="0 1 0"/>
  <limit lower="-1.57079" upper="1.57079"
         effort="100" velocity="1.0"/>
</joint>`,

  elbow_joint: `<!-- Elbow Joint - Rotation for forearm -->
<joint name="elbow_joint" type="revolute">
  <parent link="upper_arm_link"/>
  <child link="forearm_link"/>
  <origin xyz="0 0 0.3" rpy="0 0 0"/>
  <axis xyz="0 1 0"/>
  <limit lower="-2.35619" upper="2.35619"
         effort="50" velocity="1.0"/>
</joint>`,

  wrist_joint: `<!-- Wrist Joint - Rotation for end effector -->
<joint name="wrist_joint" type="revolute">
  <parent link="forearm_link"/>
  <child link="wrist_link"/>
  <origin xyz="0 0 0.25" rpy="0 0 0"/>
  <axis xyz="0 0 1"/>
  <limit lower="-3.14159" upper="3.14159"
         effort="20" velocity="2.0"/>
</joint>`,
};

// Python code snippets for joint control
const pythonJointSnippets: Record<string, string> = {
  base_joint: `# Control base_joint rotation (yaw)
from sensor_msgs.msg import JointState

joint_msg = JointState()
joint_msg.name = ['base_joint']
joint_msg.position = [angle]  # radians
self.joint_pub.publish(joint_msg)`,

  shoulder_joint: `# Control shoulder_joint (pitch)
from sensor_msgs.msg import JointState

joint_msg = JointState()
joint_msg.name = ['shoulder_joint']
joint_msg.position = [angle]  # radians
self.joint_pub.publish(joint_msg)`,

  elbow_joint: `# Control elbow_joint (pitch)
from sensor_msgs.msg import JointState

joint_msg = JointState()
joint_msg.name = ['elbow_joint']
joint_msg.position = [angle]  # radians
self.joint_pub.publish(joint_msg)`,

  wrist_joint: `# Control wrist_joint (roll)
from sensor_msgs.msg import JointState

joint_msg = JointState()
joint_msg.name = ['wrist_joint']
joint_msg.position = [angle]  # radians
self.joint_pub.publish(joint_msg)`,
};

// Default code when no joint is selected
const defaultUrdfCode = `<?xml version="1.0"?>
<robot name="simple_robot_arm">
  <!-- A 4-DOF robot arm with:
       - base_joint: vertical rotation
       - shoulder_joint: upper arm pitch
       - elbow_joint: forearm pitch
       - wrist_joint: end effector roll
  -->

  <!-- Manipulate a joint to see its URDF -->
</robot>`;

const defaultPythonCode = `#!/usr/bin/env python3
"""Robot Joint Control with ROS 2"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

class JointController(Node):
    def __init__(self):
        super().__init__('joint_controller')
        self.joint_pub = self.create_publisher(
            JointState, '/joint_states', 10
        )

# Manipulate a joint to see control code`;

export interface RobotPlaygroundProps {
  urdfPath: string;
  height?: number;
  defaultTab?: "urdf" | "python";
}

export const RobotPlayground: React.FC<RobotPlaygroundProps> = ({
  urdfPath,
  height = 400,
  defaultTab = "urdf",
}) => {
  const [activeJoint, setActiveJoint] = useState<string | null>(null);
  const [currentAngle, setCurrentAngle] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<"urdf" | "python">(defaultTab);

  // Handle joint changes from the viewer
  const handleJointChange = useCallback((jointName: string, angle: number) => {
    setActiveJoint(jointName);
    setCurrentAngle(angle);
  }, []);

  // Get the appropriate code snippet
  const getCodeSnippet = (): string => {
    if (!activeJoint) {
      return activeTab === "urdf" ? defaultUrdfCode : defaultPythonCode;
    }

    const snippets =
      activeTab === "urdf" ? urdfJointSnippets : pythonJointSnippets;
    return (
      snippets[activeJoint] ||
      (activeTab === "urdf" ? defaultUrdfCode : defaultPythonCode)
    );
  };

  // Convert radians to degrees for display
  const radToDeg = (rad: number): string => ((rad * 180) / Math.PI).toFixed(1);

  return (
    <div className={styles.playgroundContainer}>
      <div className={styles.viewerSection}>
        <RobotViewer
          urdfPath={urdfPath}
          height={height}
          showControls={true}
          onJointChange={handleJointChange}
        />
      </div>

      <div className={styles.codeSection}>
        <div className={styles.codeHeader}>
          <div className={styles.tabContainer}>
            <button
              className={`${styles.tab} ${
                activeTab === "urdf" ? styles.activeTab : ""
              }`}
              onClick={() => setActiveTab("urdf")}
            >
              URDF
            </button>
            <button
              className={`${styles.tab} ${
                activeTab === "python" ? styles.activeTab : ""
              }`}
              onClick={() => setActiveTab("python")}
            >
              Python
            </button>
          </div>
          {activeJoint && (
            <div className={styles.jointInfo}>
              <span className={styles.jointName}>{activeJoint}</span>
              <span className={styles.jointAngle}>
                {radToDeg(currentAngle)}°
              </span>
            </div>
          )}
        </div>

        <div className={styles.codeContainer}>
          <pre className={styles.codeBlock}>
            <code
              className={
                activeTab === "urdf" ? "language-xml" : "language-python"
              }
            >
              {getCodeSnippet()}
            </code>
          </pre>
        </div>

        <div className={styles.codeFooter}>
          {activeJoint ? (
            <p className={styles.hint}>
              ✨ Showing code for <strong>{activeJoint}</strong> - move other
              joints to see their code
            </p>
          ) : (
            <p className={styles.hint}>
              👆 Move a joint slider to see the corresponding{" "}
              {activeTab === "urdf" ? "URDF definition" : "Python control code"}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default RobotPlayground;
