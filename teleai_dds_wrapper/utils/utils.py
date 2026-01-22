from pathlib import Path

from .logging_utils import logger

PACKAGE_ROOT = Path(__file__).parent.resolve()
IOX_CONFIG_PATH = PACKAGE_ROOT / "assets" / "shm_config.toml"
CYCLONEDDS_XML_PATH = PACKAGE_ROOT / "assets" / "cyclonedds.xml"
IOX_ROUDI_BIN = PACKAGE_ROOT / "bin" / "iox-roudi"

def get_cyclonedds_uri():
    return f"file://{CYCLONEDDS_XML_PATH}"