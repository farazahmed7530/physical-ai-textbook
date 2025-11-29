---
title: Physical AI Textbook API
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Physical AI Textbook API

FastAPI backend for the Physical AI & Humanoid Robotics textbook with RAG chatbot.

## Features
- RAG-powered chatbot for textbook Q&A
- User authentication
- Content personalization
- Urdu translation

## API Endpoints
- `GET /health` - Health check
- `POST /api/chat` - Chat with the textbook
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/personalize` - Personalize content
- `POST /api/translate` - Translate to Urdu
