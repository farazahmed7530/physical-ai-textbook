# Physical AI & Humanoid Robotics Textbook

[![Better Auth](https://img.shields.io/badge/Auth-Better%20Auth-blue)](https://www.better-auth.com/)
[![Docusaurus](https://img.shields.io/badge/Built%20with-Docusaurus-green)](https://docusaurus.io/)
[![Three.js](https://img.shields.io/badge/3D-Three.js-black)](https://threejs.org/)

A comprehensive textbook for learning Physical AI and Humanoid Robotics, built with [Docusaurus](https://docusaurus.io/).

## 🎯 Hackathon Features

- 🔐 **Better Auth Integration** - Secure authentication with background questions ([See Details](./BETTER_AUTH.md))
- ✨ **AI-Powered Personalization** - Content adapts to user experience level
- 🌐 **Urdu Translation** - Full chapter translation with RTL support
- 🤖 **3D Robot Playground** - Interactive Three.js robot simulation
- 💬 **RAG Chatbot** - AI assistant with textbook knowledge
- 📊 **Interactive Mind Maps** - Visual learning aids with Mermaid

## Features

- 📚 13 chapters covering fundamentals to advanced topics
- 🎨 Mermaid diagrams and mind maps for visual explanations
- 💻 Code examples in Python with live demos
- 🌙 Dark mode support
- 📱 Responsive design for all devices
- 🤖 Interactive 3D robot simulations

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
