import logging
import os
from app.core.config import settings

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
