# Physical AI Textbook Backend

FastAPI backend for the Physical AI & Humanoid Robotics textbook platform.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file and configure:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Configuration settings
│   ├── routers/         # API route handlers
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   └── utils/           # Utility functions
├── tests/               # Test files
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project configuration
└── .env.example         # Environment template
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
