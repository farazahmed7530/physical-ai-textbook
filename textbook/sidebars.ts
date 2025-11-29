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
      label: "Introduction & Fundamentals",
      collapsed: false,
      items: [
        "introduction/physical-ai",
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
