from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
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

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class AssetCreate(BaseModel):
    tag: str
    name: str
    category: str
    assigned_to: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    status: str = "Active"

class AssetUpdate(BaseModel):
    tag: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    assigned_to: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    status: Optional[str] = None

class AssetValidation(BaseModel):
    assetcode: int
    empcode: str
    auditby: str
    auditstatus: str
    invalidreason: Optional[str] = None

class BulkImportResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[dict]

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

def get_current_user(current_user: str = Depends(verify_token)):
    try:
        user = supabase.table("users").select("*").eq("username", current_user).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="User not found")
        return user.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

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

# Admin Asset Management Endpoints
@app.post("/admin/assets")
async def create_asset(asset: AssetCreate, admin_user: dict = Depends(require_admin)):
    try:
        # Check if asset tag already exists
        existing_asset = supabase.table("assets").select("*").eq("tag", asset.tag).execute()
        if existing_asset.data:
            raise HTTPException(status_code=400, detail="Asset tag already exists")
        
        new_asset = {
            "tag": asset.tag,
            "name": asset.name,
            "category": asset.category,
            "assigned_to": asset.assigned_to,
            "location": asset.location,
            "purchase_date": asset.purchase_date,
            "purchase_cost": asset.purchase_cost,
            "status": asset.status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("assets").insert(new_asset).execute()
        return {"message": "Asset created successfully", "asset": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/assets/{asset_id}")
async def update_asset(asset_id: int, asset: AssetUpdate, admin_user: dict = Depends(require_admin)):
    try:
        # Check if asset exists
        existing_asset = supabase.table("assets").select("*").eq("id", asset_id).execute()
        if not existing_asset.data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check if new tag already exists (if tag is being updated)
        if asset.tag and asset.tag != existing_asset.data[0]["tag"]:
            tag_check = supabase.table("assets").select("*").eq("tag", asset.tag).execute()
            if tag_check.data:
                raise HTTPException(status_code=400, detail="Asset tag already exists")
        
        # Build update data
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        for field, value in asset.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        result = supabase.table("assets").update(update_data).eq("id", asset_id).execute()
        return {"message": "Asset updated successfully", "asset": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/assets/{asset_id}")
async def delete_asset(asset_id: int, admin_user: dict = Depends(require_admin)):
    try:
        # Check if asset exists
        existing_asset = supabase.table("assets").select("*").eq("id", asset_id).execute()
        if not existing_asset.data:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        result = supabase.table("assets").delete().eq("id", asset_id).execute()
        return {"message": "Asset deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin User Management Endpoints
@app.get("/admin/users")
async def list_users(admin_user: dict = Depends(require_admin)):
    try:
        users = supabase.table("users").select("id, username, email, role, created_at").execute()
        return {"users": users.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/users")
async def create_user(user: UserCreate, admin_user: dict = Depends(require_admin)):
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("username", user.username).execute()
        if existing_user.data:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email exists
        existing_email = supabase.table("users").select("*").eq("email", user.email).execute()
        if existing_email.data:
            raise HTTPException(status_code=400, detail="Email already exists")
        
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
        
        # Return user without password hash
        user_data = result.data[0]
        user_data.pop("password_hash", None)
        
        return {"message": "User created successfully", "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate, admin_user: dict = Depends(require_admin)):
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if new username already exists (if username is being updated)
        if user.username and user.username != existing_user.data[0]["username"]:
            username_check = supabase.table("users").select("*").eq("username", user.username).execute()
            if username_check.data:
                raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if new email already exists (if email is being updated)
        if user.email and user.email != existing_user.data[0]["email"]:
            email_check = supabase.table("users").select("*").eq("email", user.email).execute()
            if email_check.data:
                raise HTTPException(status_code=400, detail="Email already exists")
        
        # Build update data
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        for field, value in user.dict(exclude_unset=True).items():
            if value is not None:
                if field == "password":
                    update_data["password_hash"] = hash_password(value)
                else:
                    update_data[field] = value
        
        result = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        # Return user without password hash
        user_data = result.data[0]
        user_data.pop("password_hash", None)
        
        return {"message": "User updated successfully", "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, admin_user: dict = Depends(require_admin)):
    try:
        # Check if user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if existing_user.data[0]["username"] == admin_user["username"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        result = supabase.table("users").delete().eq("id", user_id).execute()
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin Bulk Import Endpoint
@app.post("/admin/assets/bulk-import", response_model=BulkImportResponse)
async def bulk_import_assets(file: UploadFile = File(...), admin_user: dict = Depends(require_admin)):
    try:
        import csv
        import io
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Expected CSV columns: tag, name, category, assigned_to, location, purchase_date, purchase_cost, status
        required_fields = ['tag', 'name', 'category']
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
            try:
                # Validate required fields
                missing_fields = [field for field in required_fields if not row.get(field, '').strip()]
                if missing_fields:
                    errors.append({
                        "row": row_num,
                        "error": f"Missing required fields: {', '.join(missing_fields)}",
                        "data": row
                    })
                    error_count += 1
                    continue
                
                # Check if asset tag already exists
                existing_asset = supabase.table("assets").select("*").eq("tag", row['tag'].strip()).execute()
                if existing_asset.data:
                    errors.append({
                        "row": row_num,
                        "error": f"Asset tag '{row['tag'].strip()}' already exists",
                        "data": row
                    })
                    error_count += 1
                    continue
                
                # Prepare asset data
                asset_data = {
                    "tag": row['tag'].strip(),
                    "name": row['name'].strip(),
                    "category": row['category'].strip(),
                    "assigned_to": row.get('assigned_to', '').strip() or None,
                    "location": row.get('location', '').strip() or None,
                    "purchase_date": row.get('purchase_date', '').strip() or None,
                    "purchase_cost": float(row['purchase_cost']) if row.get('purchase_cost', '').strip() else None,
                    "status": row.get('status', 'Active').strip() or 'Active',
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Insert asset
                result = supabase.table("assets").insert(asset_data).execute()
                success_count += 1
                
            except ValueError as ve:
                errors.append({
                    "row": row_num,
                    "error": f"Invalid data format: {str(ve)}",
                    "data": row
                })
                error_count += 1
            except Exception as e:
                errors.append({
                    "row": row_num,
                    "error": f"Database error: {str(e)}",
                    "data": row
                })
                error_count += 1
        
        return BulkImportResponse(
            success_count=success_count,
            error_count=error_count,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)