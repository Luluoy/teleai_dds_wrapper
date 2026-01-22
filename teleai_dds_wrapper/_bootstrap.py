import psutil
import subprocess
import time
from teleai_dds_wrapper.utils import logger
import os

def _get_running_roudi_process():
    """
    find iox-roudi process.
    return: psutil.Process | None
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'iox-roudi' in proc.info['name']:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def _is_config_match(proc, config_path):
    """
    Check roudi toml.
    """
    try:
        cmdline = proc.info['cmdline']
        if config_path in cmdline:
            return True
        logger.info(f"[RouDi Monitor] Found process PID {proc.pid}, but config doesn't match.")
        logger.info(f"[RouDi Monitor] Current cmdline: {cmdline}")
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def _start_roudi(executable, config_path):
    """
    Start iox-roudi process.
    """
    if not os.path.exists(config_path):
        print(f"[RouDi Monitor] Warning: Config file not found at {config_path}")
    logger.info(f"[RouDi Monitor] Starting {executable} with config {config_path}...")
    
    cmd = [executable, "-c", config_path]
    
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid
        )
        logger.info(f"[RouDi Monitor] Start command issued.")
        time.sleep(1)
    except FileNotFoundError:
        logger.error(f"[RouDi Monitor] Error: Executable '{executable}' not found in PATH.")
    except Exception as e:
        logger.error(f"[RouDi Monitor] Failed to start process: {e}")

def _check_and_start_roudi(ROUDI_EXECUTABLE, EXPECTED_CONFIG_PATH):
    logger.info(f"[RouDi Monitor] Checking system status...")
    roudi_proc = _get_running_roudi_process()
    should_start = False
    
    if roudi_proc:
        logger.info(f"[RouDi Monitor] iox-roudi is running (PID: {roudi_proc.info['pid']}).")
        if not _is_config_match(roudi_proc, EXPECTED_CONFIG_PATH):
            logger.warning(f"[RouDi Monitor] Config mismatch! Killing old process...")
            try:
                roudi_proc.terminate()
                roudi_proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                logger.warning(f"[RouDi Monitor] Process stuck, forcing kill...")
                roudi_proc.kill()
            
            should_start = True
        else:
            logger.info(f"[RouDi Monitor] Configuration matches. Everything is OK.")
    else:
        logger.warning(f"[RouDi Monitor] iox-roudi is NOT running.")
        should_start = True
        
    if should_start:
        _start_roudi(ROUDI_EXECUTABLE, EXPECTED_CONFIG_PATH)
        
        time.sleep(1)
        if _get_running_roudi_process():
            logger.info(f"[RouDi Monitor] Recovery successful. RouDi is up.")
        else:
            logger.error(f"[RouDi Monitor] Recovery failed.")