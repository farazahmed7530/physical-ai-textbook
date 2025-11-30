import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

/**
 * Physical AI & Humanoid Robotics Textbook Sidebar Configuration
 *
 * Organized by topic progression from fundamentals to advanced concepts
 */
const sidebars: SidebarsConfig = {
  textbookSidebar: [
    "intro",
    {
      type: "category",
      label: "Module 0: Introduction to Physical AI",
      collapsed: false,
      items: [
        "introduction/physical-ai",
        "introduction/humanoid-landscape",
        "introduction/sensor-systems",
      ],
    },
    {
      type: "category",
      label: "Module 1: ROS 2 Fundamentals",
      collapsed: false,
      items: [
        "ros2/architecture-core-concepts",
        "ros2/python-integration",
        "ros2/urdf-robot-description",
        "ros2/package-development",
      ],
    },
    {
      type: "category",
      label: "Module 2: Digital Twin (Gazebo & Unity)",
      collapsed: false,
      items: [
        "digital-twin/gazebo-simulation",
        "digital-twin/robot-description-formats",
        "digital-twin/sensor-simulation",
        "digital-twin/unity-visualization",
      ],
    },
    {
      type: "category",
      label: "Module 3: NVIDIA Isaac Platform",
      collapsed: false,
      items: [
        "isaac/isaac-sdk-sim",
        "isaac/perception",
        "isaac/reinforcement-learning",
        "isaac/sim-to-real",
      ],
    },
    {
      type: "category",
      label: "Fundamentals",
      collapsed: false,
      items: [
        "fundamentals/humanoid-robotics",
        "fundamentals/sensors-perception",
      ],
    },
    {
      type: "category",
      label: "Core Concepts",
      collapsed: false,
      items: [
        "core/motion-planning",
        "core/computer-vision",
        "core/natural-language",
      ],
    },
    {
      type: "category",
      label: "Advanced Topics",
      collapsed: true,
      items: [
        "advanced/reinforcement-learning",
        "advanced/human-robot-interaction",
        "advanced/safety-ethics",
      ],
    },
    {
      type: "category",
      label: "Practical Applications",
      collapsed: true,
      items: [
        "practical/first-robot-project",
        "practical/industry-applications",
        "practical/future-physical-ai",
      ],
    },
  ],
};

export default sidebars;
