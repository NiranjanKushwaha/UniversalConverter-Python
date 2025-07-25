#!/usr/bin/env python3
"""
Universal File Converter API Server Startup Script
"""

import uvicorn
import sys
import os

def main():
    """Start the FastAPI server"""
    print("🚀 Starting Universal File Converter API...")
    print("📁 Current directory:", os.getcwd())
    print("🐍 Python version:", sys.version)
    
    # Check if required directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("converted", exist_ok=True)
    print("✅ Created upload and conversion directories")
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
