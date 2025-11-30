import type * as Preset from "@docusaurus/preset-classic";
import type { Config } from "@docusaurus/types";
import { themes as prismThemes } from "prism-react-renderer";

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

// GitHub Pages configuration - update these for your repository
const organizationName =
  process.env.GITHUB_REPOSITORY_OWNER || "farazahmed7530";
const projectName = "physical-ai-textbook";

const config: Config = {
  title: "Physical AI & Humanoid Robotics",
  tagline:
    "A comprehensive textbook for learning Physical AI and Humanoid Robotics",
  favicon: "img/favicon.ico",

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true,
  },

  // Production URL for GitHub Pages
  url: `https://${organizationName}.github.io`,
  // Base URL pathname - for GitHub Pages this is typically /<projectName>/
  baseUrl: `/${projectName}/`,

  // GitHub pages deployment config
  organizationName,
  projectName,
  trailingSlash: false,
  deploymentBranch: "gh-pages",

  onBrokenLinks: "throw",

  // Internationalization
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // Markdown configuration for Mermaid diagrams
  markdown: {
    mermaid: true,
  },

  // Themes for Mermaid support
  themes: ["@docusaurus/theme-mermaid"],

  // Static directory configuration
  staticDirectories: ["static"],

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          routeBasePath: "/", // Serve docs at the root
          editUrl: `https://github.com/${organizationName}/${projectName}/tree/main/textbook/`,
        },
        blog: false, // Disable blog for textbook
        theme: {
          customCss: "./src/css/custom.css",
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/social-card.jpg",
    colorMode: {
      defaultMode: "light",
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: "Physical AI & Humanoid Robotics",
      logo: {
        alt: "Physical AI Textbook Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "textbookSidebar",
          position: "left",
          label: "Textbook",
        },
        {
          to: "/playground",
          label: "🤖 Robot Playground",
          position: "left",
        },
        {
          href: `https://github.com/${organizationName}/${projectName}`,
          label: "GitHub",
          position: "right",
        },
        {
          type: "custom-authButtons",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Textbook",
          items: [
            {
              label: "Introduction",
              to: "/",
            },
            {
              label: "Fundamentals",
              to: "/fundamentals/humanoid-robotics",
            },
          ],
        },
        {
          title: "Resources",
          items: [
            {
              label: "GitHub",
              href: `https://github.com/${organizationName}/${projectName}`,
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics Textbook. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ["python", "bash", "json", "yaml"],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
