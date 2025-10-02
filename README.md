# Asset Validation API

A FastAPI-based backend for asset validation and management with JWT authentication and Supabase integration.

## Features

- 🔐 JWT Authentication (register/login)
- 📦 Asset Management
- ✅ Asset Validation & Auditing
- 📊 Dashboard Endpoints
- 🔍 Search Functionality
- 🗄️ Supabase Database Integration
- 📚 Auto-generated API Documentation

## Quick Start

### 1. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Supabase credentials and JWT secret
```

### 4. Run Development Server
```bash
python start.py
```

### 5. Run Production Server
```bash
python production.py
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Assets
- `GET /assets/tag/{tag}` - Get asset by tag
- `POST /assets/validate` - Validate asset

### Dashboard
- `GET /dashboard/assets` - Get all assets
- `GET /dashboard/categories` - Get asset categories
- `GET /dashboard/audit-history` - Get audit history
- `GET /dashboard/search?q={query}` - Search assets

### System
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Testing

Run the test script to verify the API:
```bash
# Start the server first
python start.py

# In another terminal
python test_api.py
```

## Deployment

### Environment Variables
Make sure to set these in production:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `SECRET_KEY` - Strong JWT secret key
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

### Production Deployment
```bash
# Use production script
python production.py

# Or with custom settings
HOST=0.0.0.0 PORT=8080 python production.py
```

## Database Schema

The API expects these Supabase tables:

### users
- `id` (uuid, primary key)
- `username` (text, unique)
- `email` (text)
- `password_hash` (text)
- `role` (text)
- `created_at` (timestamp)

### assets
- `id` (int, primary key)
- `tag` (text, unique)
- `name` (text)
- `category` (text)
- `status` (text)
- `assigned_to` (text)
- `last_audit` (timestamp)
- `last_auditor` (text)
- `audit_status` (text)
- `audit_notes` (text)
- `updated_at` (timestamp)

## Security Notes

⚠️ **Important for Production:**
1. Change the `SECRET_KEY` in your `.env` file
2. Configure CORS origins properly (not `["*"]`)
3. Use HTTPS in production
4. Set up proper database security rules in Supabase
5. Use environment variables for sensitive data

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Supabase** - Backend-as-a-Service database
- **JWT** - JSON Web Tokens for authentication
- **bcrypt** - Password hashing
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation# asset-id-backend
