#!/usr/bin/env python3
"""
Production startup script for Asset Validation API
Use this for hosting/deployment
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Production configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting Asset Validation API in PRODUCTION mode...")
    print(f"📡 Server will be available at: http://{host}:{port}")
    print("🔒 Running with production settings")
    print("\n" + "="*50)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Disable auto-reload in production
        log_level="info",
        access_log=True
    )