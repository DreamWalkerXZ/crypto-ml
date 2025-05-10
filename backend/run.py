import uvicorn
import logging
import sys

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """
    Main entry point for the FastAPI application.
    Configures and starts the Uvicorn server with the following settings:
    - Host: 0.0.0.0 (accessible from any network interface)
    - Port: 8000
    - Reload: Enabled for development
    - Log level: info
    """
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 