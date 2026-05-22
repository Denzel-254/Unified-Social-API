# Unified Social Media API

> A scalable Python-based backend service that enables users to publish content once and distribute it across multiple social media platforms from a single unified API.  
> The platform also centralizes analytics, engagement metrics, comments, likes, reactions, and token management into one dashboard-ready backend system.

---

# 📚 Table of Contents

- [Overview](#-overview)
- [Core Features](#-core-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Supported Platforms](#-supported-platforms)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Environment Configuration](#-environment-configuration)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Authentication Flow](#-authentication-flow)
- [Testing with Mock OAuth](#-testing-with-mock-oauth)
- [Publishing Workflow](#-publishing-workflow)
- [Switching to Production Credentials](#-switching-to-production-credentials)
- [Database Models](#-database-models)
- [Development Roadmap](#-development-roadmap)
- [Troubleshooting](#-troubleshooting)
- [Development Commands](#-development-commands)
- [Contributing](#-contributing)
- [License](#-license)

---

#  Overview

The **Unified Social Media API** is designed to solve the problem of managing multiple social media platforms independently.

Instead of building separate integrations for Facebook, Instagram, Twitter/X, LinkedIn, YouTube, and WhatsApp Business, this system provides:

- One unified publishing endpoint
- Centralized OAuth authentication
- Shared token management
- Unified analytics aggregation
- Multi-platform engagement tracking

The API acts as a middleware layer between client applications and external social media platforms.

---

#  Core Features

## ✅ Unified Publishing

Publish a single piece of content to multiple social platforms simultaneously using one API request.

## ✅ OAuth Authentication

Secure OAuth 2.0 authentication flow implementation for all supported platforms.

## ✅ Token Management

- Secure token storage
- Token refresh handling
- Expiration tracking
- Connection status monitoring

## ✅ Mock OAuth Mode

Test the entire authentication system without requiring real developer credentials.

## ✅ Centralized Analytics

Aggregate:
- Likes
- Shares
- Comments
- Engagement metrics
- Reach and impressions

into one unified backend structure.

## ✅ Async Architecture

Built using asynchronous Python patterns for scalability and performance.

---

# 🏗 Architecture

The system follows a modular backend architecture:

```text
Client Application
        │
        ▼
FastAPI REST API
        │
        ├── Authentication Layer
        ├── Publishing Layer
        ├── Analytics Layer
        ├── Token Management
        └── Platform Adapters
                │
                ├── Facebook API
                ├── Instagram API
                ├── Twitter/X API
                ├── LinkedIn API
                ├── YouTube API
                └── WhatsApp Business API
```

The architecture separates platform-specific logic into adapters, making the system scalable and easy to extend.

---

# 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI |
| Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 |
| Database (Development) | SQLite |
| Database (Production) | PostgreSQL |
| Migrations | Alembic |
| Authentication | OAuth 2.0 |
| Token Security | JWT |
| HTTP Client | httpx |
| Validation | Pydantic |
| ASGI Server | Uvicorn |

---

# 🌐 Supported Platforms

| Platform | Features |
|----------|----------|
| Facebook | Posts, analytics, comments |
| Instagram | Images, reels, engagement |
| Twitter/X | Tweets, replies |
| LinkedIn | Professional posts, reactions |
| YouTube | Video uploads |
| WhatsApp Business | Messaging support |

---

# 📦 Prerequisites

Before running the project, ensure you have:

- Python 3.11+
- Git
- pip
- Virtual environment support

Optional for production:
- Docker Desktop
- PostgreSQL
- Redis

---

# ⚡ Quick Start

## 1. Clone the Repository

```bash
git clone https://github.com/lucy-ann/Unified-Social-API.git
cd Unified-Social-API
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Copy the environment template:

### Windows

```bash
copy .env.example .env
```

### Mac/Linux

```bash
cp .env.example .env
```

---

# ⚙ Environment Configuration

Example `.env` configuration:

```env
APP_NAME="Unified Social Media API"
DEBUG=true

SECRET_KEY="change-this-in-production"

API_V1_PREFIX="/api/v1"

# SQLite for development
DATABASE_URL="sqlite+aiosqlite:///./unified_social.db"
DATABASE_SYNC_URL="sqlite:///./unified_social.db"

# OAuth Testing
MOCK_OAUTH=true
```

---

## Important Environment Variables

| Variable | Description |
|----------|-------------|
| `APP_NAME` | Application name |
| `DEBUG` | Enable debug mode |
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Async database connection |
| `DATABASE_SYNC_URL` | Sync database connection |
| `MOCK_OAUTH` | Enable mock OAuth mode |

---

# ▶ Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Server will run at:

```text
http://localhost:8000
```

---

# 📖 API Documentation

FastAPI automatically generates Swagger documentation.

| Service | URL |
|---------|-----|
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

# 📁 Project Structure

```text
Unified-Social-API/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── mock_auth.py
│   │       └── publish.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── oauth.py
│   │   └── mock_oauth.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── post.py
│   │   └── analytics.py
│   │
│   ├── services/
│   │   ├── token_service.py
│   │   └── user_service.py
│   │
│   └── main.py
│
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

---

# 🔌 API Endpoints

# Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/auth/{platform}/connect` | Start OAuth flow |
| GET | `/api/v1/auth/{platform}/callback` | OAuth callback |
| GET | `/api/v1/auth/{platform}/tokens` | Check token status |

Supported values for `{platform}`:

```text
facebook
instagram
twitter
linkedin
youtube
whatsapp
```

---

# 📤 Publishing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/publish/` | Publish content |
| GET | `/api/v1/publish/test` | Test endpoint |

---

# 📤 Example Publish Request

```bash
curl -X POST "http://localhost:8000/api/v1/publish/" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["facebook", "twitter", "linkedin"],
    "content": "Hello from Unified Social API 🚀",
    "media_url": null
  }'
```

---

# 🔐 Authentication Flow

The authentication system follows the OAuth 2.0 authorization code flow.

## OAuth Workflow

```text
User
  │
  ▼
/connect endpoint
  │
  ▼
Platform Login Page
  │
  ▼
Authorization Approval
  │
  ▼
Callback Endpoint
  │
  ▼
Access Token Storage
```

---

# 🧪 Testing with Mock OAuth

Mock OAuth allows developers to test integrations without waiting for platform approvals.

## Benefits

- No developer accounts required
- No API review delays
- Instant testing
- Simulated tokens
- Realistic authentication flow

---

# 🧪 Testing OAuth

## Start the Server

```bash
uvicorn app.main:app --reload
```

---

## Test Facebook OAuth

Open in browser:

```text
http://localhost:8000/api/v1/auth/facebook/connect
```

---

## Test Other Platforms

```text
http://localhost:8000/api/v1/auth/twitter/connect
http://localhost:8000/api/v1/auth/linkedin/connect
http://localhost:8000/api/v1/auth/instagram/connect
```

---

# 🔎 Check Token Status

```bash
curl http://localhost:8000/api/v1/auth/facebook/tokens
```

Example response:

```json
{
  "platform": "facebook",
  "connected": true,
  "platform_user_id": "mock_facebook_12345",
  "expires_at": "2026-05-22T15:30:00",
  "is_expired": false
}
```

---

# 📤 Publishing Workflow

The unified publishing system follows this process:

```text
Client Request
      │
      ▼
Publish Service
      │
      ├── Validate Payload
      ├── Check Tokens
      ├── Select Platforms
      ├── Dispatch Requests
      └── Aggregate Responses
```

Each platform adapter handles platform-specific formatting internally.

---

# 🔐 Switching to Production Credentials

## Step 1: Disable Mock Mode

```env
MOCK_OAUTH=false
```

---

## Step 2: Add Real Credentials

```env
META_APP_ID="your_meta_app_id"
META_APP_SECRET="your_meta_secret"

TWITTER_API_KEY="your_twitter_key"
TWITTER_API_SECRET="your_twitter_secret"

LINKEDIN_CLIENT_ID="your_linkedin_id"
LINKEDIN_CLIENT_SECRET="your_linkedin_secret"

YOUTUBE_CLIENT_ID="your_google_client_id"
YOUTUBE_CLIENT_SECRET="your_google_client_secret"
```

---

## Step 3: Register Redirect URIs

```text
http://localhost:8000/api/v1/auth/facebook/callback
http://localhost:8000/api/v1/auth/twitter/callback
http://localhost:8000/api/v1/auth/linkedin/callback
http://localhost:8000/api/v1/auth/instagram/callback
http://localhost:8000/api/v1/auth/youtube/callback
http://localhost:8000/api/v1/auth/whatsapp/callback
```

---

# 🗄 Database Models

## User Model

Stores:
- User profile data
- Authentication metadata

## Token Model

Stores:
- Access tokens
- Refresh tokens
- Expiration dates
- Platform associations

## Post Model

Stores:
- Published content
- Platform mappings
- Publishing status

## Analytics Model

Stores:
- Engagement metrics
- Impressions
- Likes
- Comments
- Reach statistics

---

# 📊 Development Roadmap

| Day | Status | Deliverables |
|----|--------|--------------|
| Day 1 | ✅ Complete | Project setup & database |
| Day 2 | ✅ Complete | OAuth & mock mode |
| Day 3 | 🚧 In Progress | Facebook & Instagram adapters |
| Day 4 | ⏳ Pending | Twitter/X & LinkedIn |
| Day 5 | ⏳ Pending | YouTube & WhatsApp |
| Day 6 | ⏳ Pending | Unified publish service |
| Day 7 | ⏳ Pending | Analytics aggregation |
| Day 8 | ⏳ Pending | Comments & engagement |
| Day 9 | ⏳ Pending | Rate limiting & error handling |
| Day 10 | ⏳ Pending | Testing & final documentation |

---

# 🐛 Troubleshooting

## Issue: Module Not Found

```bash
pip install -r requirements.txt
```

Ensure your virtual environment is activated.

---

## Issue: Port Already in Use

```bash
uvicorn app.main:app --reload --port 8001
```

---

## Issue: Database Errors

Delete the local SQLite database:

### Windows

```bash
del unified_social.db
```

### Mac/Linux

```bash
rm unified_social.db
```

---

## Issue: Mock OAuth Not Working

Check:

```env
MOCK_OAUTH=true
```

Then restart the server.

---

# 🧪 Development Commands

## Run Tests

```bash
pytest
```

---

## Format Code

```bash
black app/
isort app/
```

---

## Type Checking

```bash
mypy app/
```

---

#  Contributing

## Development Setup

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

---



# 📝 License

This project is intended for educational and development purposes.

---

#  Acknowledgments

Special thanks to:

- FastAPI
- SQLAlchemy
- Authlib
- Uvicorn
- All supported platform APIs

---

#  Project Vision

The goal of this project is to simplify multi-platform social media management by providing developers and businesses with a single unified integration layer.

---



# ✅ Current Project Status

| Feature | Status |
|---------|--------|
| OAuth Flows | ✅ Complete |
| Token Storage | ✅ Complete |
| Mock OAuth | ✅ Complete |
| Publishing Preview | ✅ Complete |
| Database Models | ✅ Complete |
| README Documentation | ✅ Complete |

