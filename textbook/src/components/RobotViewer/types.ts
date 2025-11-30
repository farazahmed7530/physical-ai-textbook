/**
 * Types for the Interactive 3D Robot Viewer Component
 */

export interface JointState {
  name: string;
  angle: number;
  min: number;
  max: number;
}

export interface RobotViewerProps {
  urdfPath?: string;
  width?: string | number;
  height?: string | number;
  showControls?: boolean;
  initialJointAngles?: Record<string, number>;
  onJointChange?: (jointName: string, angle: number) => void;
}

export interface JointControlsProps {
  joints: JointState[];
  onJointChange: (jointName: string, angle: number) => void;
}

export interface RobotModelProps {
  urdfPath?: string;
  jointAngles: Record<string, number>;
  onJointsLoaded?: (joints: JointState[]) => void;
}
