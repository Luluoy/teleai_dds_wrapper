import psutil
import subprocess
import time
import os
import signal

# ================= 配置区域 =================
# iox-roudi 的可执行文件路径（如果在 PATH 中，直接写 "iox-roudi"）
ROUDI_EXECUTABLE = "iox-roudi"

# 你期望的配置文件绝对路径
EXPECTED_CONFIG_PATH = "/home/coder/code/dds_iox/teleai_dds_wrapper/configs/shm_confil.toml"

# 日志前缀
TAG = "[RouDi Monitor]"
# ===========================================

def get_running_roudi_process():
    """
    查找正在运行的 iox-roudi 进程。
    返回: psutil.Process 对象 或 None
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # 检查进程名是否包含 iox-roudi
            if proc.info['name'] and 'iox-roudi' in proc.info['name']:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def is_config_match(proc, config_path):
    """
    检查进程的启动参数是否包含指定的配置文件路径
    """
    try:
        cmdline = proc.info['cmdline']
        # cmdline 是一个列表，例如 ['/usr/bin/iox-roudi', '-c', '/path/to/config.toml']
        
        # 简单检查：配置文件路径是否在命令行参数中
        # 注意：Iceoryx 通常使用 -c 或 --config 指定配置
        if config_path in cmdline:
            return True
        
        # 如果你只关心它是否运行，不关心参数，可以跳过此检查
        print(f"{TAG} Found process PID {proc.pid}, but config doesn't match.")
        print(f"{TAG} Current cmdline: {cmdline}")
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def start_roudi(executable, config_path):
    """
    启动 iox-roudi 进程
    """
    print(f"{TAG} Starting {executable} with config {config_path}...")
    
    # 构建启动命令
    cmd = [executable, "-c", config_path]
    
    try:
        # 使用 Popen 非阻塞启动
        # stdout/stderr 可以重定向到文件或 subprocess.DEVNULL
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL, # 或者 open('roudi.log', 'w')
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid # 让它在新的会话中运行，防止随脚本退出而退出
        )
        print(f"{TAG} Start command issued.")
        # 给它一点时间初始化
        time.sleep(2) 
    except FileNotFoundError:
        print(f"{TAG} Error: Executable '{executable}' not found in PATH.")
    except Exception as e:
        print(f"{TAG} Failed to start process: {e}")

def main():
    print(f"{TAG} Checking system status...")
    
    # 1. 查找进程
    roudi_proc = get_running_roudi_process()
    
    should_start = False
    
    if roudi_proc:
        print(f"{TAG} iox-roudi is running (PID: {roudi_proc.info['pid']}).")
        
        # 2. 检查配置是否匹配
        if not is_config_match(roudi_proc, EXPECTED_CONFIG_PATH):
            print(f"{TAG} Config mismatch! Killing old process...")
            try:
                roudi_proc.terminate() # 尝试优雅关闭
                roudi_proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                print(f"{TAG} Process stuck, forcing kill...")
                roudi_proc.kill()
            
            should_start = True
        else:
            print(f"{TAG} Configuration matches. Everything is OK.")
    else:
        print(f"{TAG} iox-roudi is NOT running.")
        should_start = True
        
    # 3. 如果需要，启动进程
    if should_start:
        start_roudi(ROUDI_EXECUTABLE, EXPECTED_CONFIG_PATH)
        
        # 再次确认
        time.sleep(1)
        if get_running_roudi_process():
            print(f"{TAG} Recovery successful. RouDi is up.")
        else:
            print(f"{TAG} Recovery failed.")

if __name__ == "__main__":
    # 请确保将 EXPECTED_CONFIG_PATH 修改为你真实的路径
    if not os.path.exists(EXPECTED_CONFIG_PATH):
        print(f"{TAG} Warning: Config file not found at {EXPECTED_CONFIG_PATH}")
    
    main()