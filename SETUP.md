# Asset Validation API Setup Guide

## Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Update your `.env` file with your actual values:**
   ```bash
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key

   # JWT Configuration
   SECRET_KEY=your-super-secret-jwt-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Admin User Configuration (for testing/setup scripts)
   ADMIN_USERNAME=your-admin-username
   ADMIN_EMAIL=admin@yourcompany.com
   ADMIN_PASSWORD=your-secure-admin-password
   ```

## Database Setup

Ensure your Supabase database has the following tables:

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'auditor',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Assets Table
```sql
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    assigned_to VARCHAR(100),
    location VARCHAR(255),
    purchase_date DATE,
    purchase_cost DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'Active',
    last_audit TIMESTAMP WITH TIME ZONE,
    last_auditor VARCHAR(100),
    audit_status VARCHAR(50),
    audit_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Installation & Running

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Create your first admin user:**
   ```bash
   python create_admin.py
   ```

4. **Test the admin functionality:**
   ```bash
   python test_admin_api.py
   ```

## API Documentation

Once running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Admin Endpoints

### Asset Management
- `POST /admin/assets` - Create new asset
- `PUT /admin/assets/{id}` - Update asset
- `DELETE /admin/assets/{id}` - Delete asset
- `POST /admin/assets/bulk-import` - Bulk import from CSV

### User Management
- `GET /admin/users` - List all users
- `POST /admin/users` - Create new user
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Delete user

## CSV Import Format

For bulk asset import, use this CSV format:

```csv
tag,name,category,assigned_to,location,purchase_date,purchase_cost,status
LAP001,Dell Laptop XPS 13,IT Equipment,john.doe,Office Floor 1,2024-01-15,1200.00,Active
MON001,Samsung Monitor,IT Equipment,jane.smith,Office Floor 2,2024-02-01,350.00,Active
```

Required fields: `tag`, `name`, `category`
Optional fields: `assigned_to`, `location`, `purchase_date`, `purchase_cost`, `status`

## Security Notes

- Never commit your `.env` file to version control
- Use strong passwords for admin accounts
- Change the SECRET_KEY in production
- Configure CORS properly for production use
- Use HTTPS in production environments