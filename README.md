# Unified Social Media API

A scalable Python-based backend service that enables developers and businesses to publish content across multiple social media platforms using a single unified API. The system centralizes authentication, publishing workflows, token management, analytics, and engagement tracking into one extensible backend architecture.

---

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Supported Platforms](#supported-platforms)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Authentication Flow](#authentication-flow)
- [Publishing Workflow](#publishing-workflow)
- [Mock OAuth Testing](#mock-oauth-testing)
- [Production Configuration](#production-configuration)
- [Database Models](#database-models)
- [Development Commands](#development-commands)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The Unified Social Media API simplifies multi-platform social media management by providing a single backend interface for publishing content and managing integrations.

Instead of maintaining separate integrations for each social media provider, the platform offers:

- Unified publishing endpoints
- Centralized OAuth authentication
- Shared token management
- Aggregated analytics and engagement metrics
- Modular platform adapters
- Scalable asynchronous architecture

The API acts as a middleware layer between client applications and external social media services.

---

## Core Features

### Unified Publishing

Publish content to multiple social media platforms simultaneously using a single API request.

### OAuth 2.0 Authentication

Secure authentication workflows for all supported platforms.

### Token Management

- Secure token storage
- Token refresh handling
- Expiration tracking
- Connection monitoring

### Mock OAuth Mode

Test authentication flows locally without requiring production developer credentials.

### Centralized Analytics

Aggregate and normalize:

- Likes
- Comments
- Shares
- Reactions
- Reach
- Impressions
- Engagement metrics

### Asynchronous Architecture

Built with asynchronous Python patterns to improve scalability and performance.

---

## Architecture

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

The architecture isolates platform-specific implementations into adapters, making the system maintainable and easy to extend.

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend Framework | FastAPI |
| Programming Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 |
| Development Database | SQLite |
| Production Database | PostgreSQL |
| Database Migrations | Alembic |
| Authentication | OAuth 2.0 |
| Token Security | JWT |
| HTTP Client | httpx |
| Validation | Pydantic |
| ASGI Server | Uvicorn |

---

## Supported Platforms

| Platform | Capabilities |
|---|---|
| Facebook | Publishing, analytics, engagement |
| Instagram | Media publishing, engagement |
| Twitter/X | Tweet publishing and interactions |
| LinkedIn | Professional content publishing |
| YouTube | Video uploads and analytics |
| WhatsApp Business | Messaging integration |

---

## Prerequisites

Ensure the following tools are installed before running the project:

- Python 3.11+
- Git
- pip
- Virtual environment support

Optional for production environments:

- PostgreSQL
- Docker
- Redis

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/lucy-ann/Unified-Social-API.git
cd Unified-Social-API
```

---

### 2. Create and Activate a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

#### Windows

```bash
copy .env.example .env
```

#### macOS/Linux

```bash
cp .env.example .env
```

---

## Environment Configuration

Example `.env` configuration:

```env
APP_NAME="Unified Social Media API"
DEBUG=true

SECRET_KEY="change-this-in-production"

API_V1_PREFIX="/api/v1"

DATABASE_URL="sqlite+aiosqlite:///./unified_social.db"
DATABASE_SYNC_URL="sqlite:///./unified_social.db"

MOCK_OAUTH=true
```

### Important Environment Variables

| Variable | Description |
|---|---|
| `APP_NAME` | Application name |
| `DEBUG` | Enables debug mode |
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Async database connection |
| `DATABASE_SYNC_URL` | Sync database connection |
| `MOCK_OAUTH` | Enables mock OAuth mode |

---

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

Application URL:

```text
http://localhost:8000
```

---

## API Documentation

FastAPI automatically generates API documentation.

| Service | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Project Structure

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

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/auth/{platform}/connect` | Start OAuth flow |
| GET | `/api/v1/auth/{platform}/callback` | OAuth callback |
| GET | `/api/v1/auth/{platform}/tokens` | Retrieve token status |

Supported platform values:

```text
facebook
instagram
twitter
linkedin
youtube
whatsapp
```

---

### Publishing Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/publish/` | Publish content |


---

### Example Publish Request

```bash
curl -X POST "http://localhost:8000/api/v1/publish/" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["facebook", "twitter", "linkedin"],
    "content": "Hello from Unified Social API",
    "media_url": null
  }'
```

---

## Authentication Flow

The platform implements the OAuth 2.0 Authorization Code Flow.

```text
User
  │
  ▼
/connect Endpoint
  │
  ▼
Platform Authentication
  │
  ▼
Authorization Approval
  │
  ▼
Callback Endpoint
  │
  ▼
Token Storage
```

---

## Publishing Workflow

```text
Client Request
      │
      ▼
Publish Service
      │
      ├── Validate Request
      ├── Check Tokens
      ├── Select Platforms
      ├── Dispatch Requests
      └── Aggregate Responses
```

Each adapter internally handles platform-specific payload formatting and API communication.

---

## Mock OAuth Testing

Mock OAuth mode allows developers to test authentication flows without requiring production credentials or app approvals.

### Benefits

- Local development support
- Faster integration testing
- Simulated authentication responses
- No external platform approvals required

### Enable Mock OAuth

```env
MOCK_OAUTH=true
```

### Example OAuth Test URL

```text
http://localhost:8000/api/v1/auth/facebook/connect
```

---

## Production Configuration

### Disable Mock OAuth

```env
MOCK_OAUTH=false
```

### Add Production Credentials

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

### Register Redirect URIs

```text
http://localhost:8000/api/v1/auth/facebook/callback
http://localhost:8000/api/v1/auth/twitter/callback
http://localhost:8000/api/v1/auth/linkedin/callback
http://localhost:8000/api/v1/auth/instagram/callback
http://localhost:8000/api/v1/auth/youtube/callback
http://localhost:8000/api/v1/auth/whatsapp/callback
```

---

## Database Models

### User Model

Stores:

- User profile data
- Authentication metadata

### Token Model

Stores:

- Access tokens
- Refresh tokens
- Expiration timestamps
- Platform associations

### Post Model

Stores:

- Published content
- Platform mappings
- Publishing status

### Analytics Model

Stores:

- Engagement metrics
- Reach and impressions
- Likes and comments
- Platform analytics

---

## Development Commands

### Run Tests

```bash
pytest
```

### Format Code

```bash
black app/
isort app/
```

### Type Checking

```bash
mypy app/
```

---

## Troubleshooting

### Module Not Found

Ensure dependencies are installed and the virtual environment is activated:

```bash
pip install -r requirements.txt
```

---

### Port Already in Use

Run the server on another port:

```bash
uvicorn app.main:app --reload --port 8001
```

---

### Database Issues

Delete the local SQLite database and restart the application.

#### Windows

```bash
del unified_social.db
```

#### macOS/Linux

```bash
rm unified_social.db
```

---

### Mock OAuth Not Working

Verify the following configuration:

```env
MOCK_OAUTH=true
```

Restart the application after updating environment variables.

---

## Contributing

### Development Setup

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Contribution Workflow

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push the branch
5. Open a pull request

---

