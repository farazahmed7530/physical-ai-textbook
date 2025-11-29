# Physical AI & Humanoid Robotics Textbook

A comprehensive textbook for learning Physical AI and Humanoid Robotics, built with [Docusaurus](https://docusaurus.io/).

## Features

- 📚 12 chapters covering fundamentals to advanced topics
- 🎨 Mermaid diagrams for visual explanations
- 💻 Code examples in Python
- 🌙 Dark mode support
- 📱 Responsive design for all devices
- 🤖 AI Chat Assistant integration (coming soon)

## Getting Started

### Prerequisites

- Node.js 20 or higher
- npm or yarn

### Installation

```bash
npm install
```

### Local Development

```bash
npm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

### Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

To deploy manually:

```bash
npm run deploy
```

## Project Structure

```
textbook/
├── docs/                    # Textbook content (MDX files)
│   ├── intro.md            # Welcome page
│   ├── introduction/       # Chapter 1
│   ├── fundamentals/       # Chapters 2-3
│   ├── core/               # Chapters 4-6
│   ├── advanced/           # Chapters 7-9
│   └── practical/          # Chapters 10-12
├── src/
│   ├── css/                # Custom styles
│   └── components/         # React components
├── static/                 # Static assets
├── docusaurus.config.ts    # Site configuration
└── sidebars.ts             # Sidebar navigation
```

## Configuration

Update `docusaurus.config.ts` to customize:
- Site title and tagline
- GitHub organization/username
- Theme colors
- Navigation items

## License

This project is licensed under the MIT License.
