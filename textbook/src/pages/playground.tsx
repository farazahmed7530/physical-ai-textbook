/**
 * Robot Playground Page - Full-screen interactive 3D robot viewer
 * Allows users to explore and manipulate a robot arm model
 */

import BrowserOnly from "@docusaurus/BrowserOnly";
import Layout from "@theme/Layout";
import React from "react";

// Styles for the playground page
const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "calc(100vh - 60px)",
    padding: "20px",
    background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
  },
  header: {
    marginBottom: "20px",
    color: "#fff",
  },
  title: {
    fontSize: "2rem",
    fontWeight: 700,
    color: "#64ffda",
    margin: "0 0 8px 0",
  },
  subtitle: {
    fontSize: "1rem",
    color: "rgba(255, 255, 255, 0.7)",
    margin: 0,
  },
  viewerContainer: {
    flex: 1,
    minHeight: "500px",
    borderRadius: "12px",
    overflow: "hidden",
    boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
  },
  loadingContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    background: "#0f0f1a",
    color: "#64ffda",
    fontSize: "1.2rem",
  },
  infoSection: {
    marginTop: "20px",
    padding: "16px",
    background: "rgba(100, 255, 218, 0.1)",
    borderRadius: "8px",
    border: "1px solid rgba(100, 255, 218, 0.2)",
  },
  infoTitle: {
    color: "#64ffda",
    fontSize: "1rem",
    fontWeight: 600,
    margin: "0 0 8px 0",
  },
  infoText: {
    color: "rgba(255, 255, 255, 0.8)",
    fontSize: "0.9rem",
    margin: 0,
    lineHeight: 1.6,
  },
  jointList: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "12px",
    marginTop: "12px",
  },
  jointItem: {
    background: "rgba(255, 255, 255, 0.05)",
    padding: "10px 14px",
    borderRadius: "6px",
    color: "#fff",
  },
  jointName: {
    fontWeight: 600,
    color: "#64ffda",
  },
  jointDesc: {
    fontSize: "0.85rem",
    color: "rgba(255, 255, 255, 0.6)",
    marginTop: "4px",
  },
};

// Joint descriptions for the robot arm
const jointDescriptions = [
  {
    name: "base_joint",
    description: "Rotates the entire arm around the vertical axis (yaw)",
  },
  {
    name: "shoulder_joint",
    description: "Tilts the upper arm forward and backward (pitch)",
  },
  {
    name: "elbow_joint",
    description: "Bends the forearm up and down (pitch)",
  },
  {
    name: "wrist_joint",
    description: "Rotates the end effector around its axis (roll)",
  },
];

// Loading component
const LoadingPlaceholder: React.FC = () => (
  <div style={styles.loadingContainer}>Loading 3D Robot Viewer...</div>
);

// The actual playground content with RobotViewer
const PlaygroundContent: React.FC = () => {
  // Dynamically import RobotViewer to avoid SSR issues with Three.js
  const RobotViewer = React.lazy(
    () => import("@site/src/components/RobotViewer")
  );

  return (
    <React.Suspense fallback={<LoadingPlaceholder />}>
      <RobotViewer
        urdfPath="/physical-ai-textbook/urdf/robot_arm/robot_arm.urdf"
        height="100%"
        showControls={true}
      />
    </React.Suspense>
  );
};

export default function PlaygroundPage(): React.ReactElement {
  return (
    <Layout
      title="Robot Playground"
      description="Interactive 3D Robot Playground - Explore and manipulate robot models"
    >
      <div style={styles.container}>
        <header style={styles.header}>
          <h1 style={styles.title}>🤖 Robot Playground</h1>
          <p style={styles.subtitle}>
            Interactive 3D robot viewer - manipulate joints and explore robot
            kinematics
          </p>
        </header>

        <div style={styles.viewerContainer}>
          <BrowserOnly fallback={<LoadingPlaceholder />}>
            {() => <PlaygroundContent />}
          </BrowserOnly>
        </div>

        <div style={styles.infoSection}>
          <h3 style={styles.infoTitle}>About This Robot Arm</h3>
          <p style={styles.infoText}>
            This is a 4-DOF (Degrees of Freedom) robot arm model defined in URDF
            format. Use the joint controls on the right to manipulate each joint
            and observe how the robot moves. This demonstrates the concepts
            covered in the URDF and Robot Description chapter.
          </p>
          <div style={styles.jointList}>
            {jointDescriptions.map((joint) => (
              <div key={joint.name} style={styles.jointItem}>
                <div style={styles.jointName}>{joint.name}</div>
                <div style={styles.jointDesc}>{joint.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
