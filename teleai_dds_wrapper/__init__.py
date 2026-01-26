from . import commonInfo
from ._bootstrap import _check_and_start_roudi
<<<<<<< HEAD
=======
from .wrapper.wrapper import TeleaiCommonPub_1, TeleaiCommonSub_1, TeleaiCommonSub_1q
>>>>>>> 36f58be (readme)
from pathlib import Path

package_root = Path(__file__).parent.resolve()
ROUDI_EXECUTABLE = "iox-roudi"
EXPECTED_CONFIG_PATH = f"{package_root}/configs/shm_confil.toml"
_check_and_start_roudi(ROUDI_EXECUTABLE, EXPECTED_CONFIG_PATH)

__version__ = "0.1.1"
__version_info__ = tuple(map(int, __version__.split('.')))

