import logging
from pathlib import Path

# --- Logging Setup ---
LOG_FILE_PATH = str((Path(__file__).parent / "mcp_server_activity.log").resolve())
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, mode="a"),
    ],
)
logger: logging.Logger = logging.getLogger(name=__name__)
