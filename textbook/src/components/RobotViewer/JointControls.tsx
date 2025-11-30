/**
 * JointControls Component - Slider controls for robot joint manipulation
 * Displays real-time joint angle values
 */

import React from "react";
import styles from "./styles.module.css";
import type { JointControlsProps } from "./types";

// Convert radians to degrees for display
const radToDeg = (rad: number): number => (rad * 180) / Math.PI;

// Convert degrees to radians for internal use
const degToRad = (deg: number): number => (deg * Math.PI) / 180;

export const JointControls: React.FC<JointControlsProps> = ({
  joints,
  onJointChange,
}) => {
  if (joints.length === 0) {
    return (
      <div className={styles.controlsPanel}>
        <p className={styles.loadingText}>Loading joint controls...</p>
      </div>
    );
  }

  return (
    <div className={styles.controlsPanel}>
      <h3 className={styles.controlsTitle}>Joint Controls</h3>
      {joints.map((joint) => (
        <div key={joint.name} className={styles.jointControl}>
          <label className={styles.jointLabel}>
            <span className={styles.jointName}>{joint.name}</span>
            <span className={styles.jointValue}>
              {radToDeg(joint.angle).toFixed(1)}°
            </span>
          </label>
          <input
            type="range"
            className={styles.jointSlider}
            min={radToDeg(joint.min)}
            max={radToDeg(joint.max)}
            step={1}
            value={radToDeg(joint.angle)}
            onChange={(e) => {
              const newAngle = degToRad(parseFloat(e.target.value));
              onJointChange(joint.name, newAngle);
            }}
          />
          <div className={styles.jointRange}>
            <span>{radToDeg(joint.min).toFixed(0)}°</span>
            <span>{radToDeg(joint.max).toFixed(0)}°</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default JointControls;
