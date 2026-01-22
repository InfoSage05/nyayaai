"""Main entry point for NyayaAI."""
import uvicorn
from api.main import app 
from config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
