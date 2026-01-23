"""Main entry point for NyayaAI."""
import uvicorn
from config.settings import settings

if __name__ == "__main__":
    # Use import string for reload mode (required by uvicorn)
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
