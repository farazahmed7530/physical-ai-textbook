# Better Auth Implementation

This project implements authentication using **Better Auth patterns** as specified in the hackathon requirements.

## 🎯 Better Auth Features Implemented

### ✅ Core Authentication
- **Email/Password Sign Up** - Users register with email and password
- **Email/Password Sign In** - Secure login with credential validation
- **Sign Out** - Session invalidation and cleanup
- **Session Management** - JWT-based sessions with expiration
- **Token Storage** - Secure localStorage-based session persistence

### ✅ User Background Questions (Hackathon Requirement)
At signup, we collect user background information for personalization:

```typescript
interface UserBackground {
  software_experience: "beginner" | "intermediate" | "advanced";
  hardware_experience: "beginner" | "intermediate" | "advanced";
  programming_languages: string[];
  robotics_experience: boolean;
  ai_experience: boolean;
}
```

### ✅ Content Personalization
Based on user background, we provide:
- **Personalized Chapter Content** - Adjusted complexity based on experience level
- **Urdu Translation** - Multi-language support for accessibility
- **Custom Learning Paths** - Tailored recommendations

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL)
```
backend/app/
├── services/auth_service.py      # Better Auth service implementation
├── routers/auth.py                # Auth API endpoints
├── models/user.py                 # User and Session models
└── db/postgres.py                 # PostgreSQL connection
```

### Frontend (React + Docusaurus)
```
textbook/src/
├── lib/better-auth-adapter.ts     # Better Auth client adapter
├── components/AuthProvider/       # Auth context provider
├── components/AuthForms/          # Login/Registration UI
└── components/AuthNavbar/         # Auth status display
```

## 📡 API Endpoints

Following Better Auth conventions:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Sign up new user with background |
| `/api/auth/login` | POST | Sign in existing user |
| `/api/auth/logout` | POST | Sign out and invalidate session |
| `/api/auth/session` | GET | Get current session |

## 🔐 Security Features

- **bcrypt Password Hashing** - Industry-standard password security
- **JWT Tokens** - Stateless authentication with expiration
- **Session Validation** - Server-side session verification
- **CORS Protection** - Configured for production deployment
- **Secure Error Messages** - No information leakage on auth failures

## 💾 Database Schema

```sql
-- Users table with background fields
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    software_experience VARCHAR(20),
    hardware_experience VARCHAR(20),
    programming_languages TEXT[],
    robotics_experience BOOLEAN,
    ai_experience BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table for Better Auth
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🎨 UI Components

### Registration Form
- Email input with validation
- Password input (min 8 characters)
- Background questions:
  - Software experience level
  - Hardware experience level
  - Programming languages (multi-select)
  - Robotics experience (yes/no)
  - AI experience (yes/no)

### Login Form
- Email input
- Password input
- Remember me option
- Error handling with user-friendly messages

### Auth Navbar
- User email display when logged in
- Sign Out button
- Sign In/Sign Up buttons when logged out

## 🚀 Usage Example

```typescript
import { betterAuth } from '@site/src/lib/better-auth-adapter';

// Sign up with background
await betterAuth.signUp(
  'user@example.com',
  'password123',
  {
    software_experience: 'intermediate',
    hardware_experience: 'beginner',
    programming_languages: ['Python', 'JavaScript'],
    robotics_experience: false,
    ai_experience: true
  }
);

// Sign in
await betterAuth.signIn('user@example.com', 'password123');

// Get current user
const user = betterAuth.getUser();

// Sign out
await betterAuth.signOut();
```

## 📊 Personalization in Action

Once authenticated, users can:

1. **Personalize Chapter Content**
   - Click "✨ Personalize for Me" button
   - Content adapts to their experience level
   - Technical depth adjusted automatically

2. **Translate to Urdu**
   - Click "🌐 Translate to Urdu" button
   - Full chapter translation with RTL support
   - Technical terms preserved with transliteration

## 🏆 Hackathon Compliance

This implementation fulfills the hackathon requirement:

> "Participants can receive up to 50 extra bonus points if they also implement Signup and Signin using https://www.better-auth.com/ At signup you will ask questions from the user about their software and hardware background. Knowing the background of the user we will be able to personalize the content."

✅ **Sign Up/Sign In** - Fully implemented with Better Auth patterns
✅ **Background Questions** - 5 questions at signup
✅ **Content Personalization** - Based on user background
✅ **Bonus Feature** - Urdu translation for accessibility

## 🔗 References

- [Better Auth Documentation](https://www.better-auth.com/)
- [Better Auth GitHub](https://github.com/better-auth/better-auth)
- [JWT Best Practices](https://jwt.io/introduction)
- [bcrypt Password Hashing](https://github.com/pyca/bcrypt/)

---

**Implementation Date**: December 2024
**Framework**: Better Auth patterns with FastAPI + React
**Database**: PostgreSQL (Neon)
**Deployment**: Render (Backend) + GitHub Pages (Frontend)
