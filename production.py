import os
from main import app

# Production configuration
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    
    # Run with production settings
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=2,
        access_log=True,
        log_level="info"
    )