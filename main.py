from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from supabase import create_client, Client

app = FastAPI(title="Asset Validation API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase_url = os.getenv("SUPABASE_URL", "https://ekbhrshoupapmitdzbou.supabase.co")
supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVrYmhyc2hvdXBhcG1pdGR6Ym91Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg0NjkxMDMsImV4cCI6MjA3NDA0NTEwM30.MhCGoYF2BkuiYp9VHYIa7os5ygws7IJGtAC1sDFfm8Y")
supabase: Client = create_client(supabase_url, supabase_key)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Asset Validation API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "auditor"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class AssetValidation(BaseModel):
    assetcode: int
    empcode: str
    auditby: str
    auditstatus: str
    invalidreason: Optional[str] = None

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth endpoints
@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("username", user.username).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password and create user
        hashed_password = hash_password(user.password)
        new_user = {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "role": user.role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("users").insert(new_user).execute()
        
        # Create token
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    try:
        # Get user from database
        db_user = supabase.table("users").select("*").eq("username", user.username).execute()
        
        if not db_user.data or not verify_password(user.password, db_user.data[0]["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_data = db_user.data[0]
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Asset endpoints
@app.get("/assets/tag/{tag}")
async def get_asset_by_tag(tag: str, current_user: str = Depends(verify_token)):
    try:
        # Get asset from unified table
        asset = supabase.table("assets").select("*").eq("tag", tag).eq("status", "Active").execute()
        if not asset.data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"asset": asset.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assets/validate")
async def validate_asset(validation: AssetValidation, current_user: str = Depends(verify_token)):
    try:
        # Update asset with audit information
        update_data = {
            "last_audit": datetime.now(timezone.utc).isoformat(),
            "last_auditor": validation.auditby,
            "audit_status": validation.auditstatus,
            "audit_notes": validation.invalidreason,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("assets").update(update_data).eq("id", validation.assetcode).execute()
        return {"message": "Validation recorded successfully", "data": result.data[0] if result.data else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoints
@app.get("/dashboard/assets")
async def get_all_assets(category: Optional[str] = None, current_user: str = Depends(verify_token)):
    try:
        query = supabase.table("assets").select("*")
        if category:
            query = query.eq("category", category)
        
        assets = query.order("name").execute()
        return {"assets": assets.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/categories")
async def get_asset_categories(current_user: str = Depends(verify_token)):
    try:
        # Get unique categories
        categories = supabase.table("assets").select("category").execute()
        unique_categories = list(set([item["category"] for item in categories.data if item["category"]]))
        return {"categories": sorted(unique_categories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/audit-history")
async def get_audit_history(asset_id: Optional[int] = None, current_user: str = Depends(verify_token)):
    try:
        query = supabase.table("assets").select("id, tag, name, category, assigned_to, last_audit, last_auditor, audit_status, audit_notes")
        if asset_id:
            query = query.eq("id", asset_id)
        
        assets = query.order("last_audit", desc=True).execute()
        return {"audit_history": assets.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/search")
async def search_assets(q: str, current_user: str = Depends(verify_token)):
    try:
        # Try full-text search first, fallback to basic search
        try:
            assets = supabase.table("assets").select("*").text_search("search_vector", q).execute()
        except:
            # Fallback to basic search using ilike
            assets = supabase.table("assets").select("*").or_(f"name.ilike.%{q}%,tag.ilike.%{q}%,category.ilike.%{q}%").execute()
        return {"assets": assets.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)