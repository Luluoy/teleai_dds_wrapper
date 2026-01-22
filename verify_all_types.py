import threading
import time
import numpy as np
import random
import sys

# 必须从 wrapper 导入
from teleai_dds_wrapper.wrapper import TeleaiCommonPub_1, TeleaiCommonSub_1

# 导入生成的 IDL 模块 (根据你的实际路径调整)
from teleai_dds_wrapper.commonInfo.msg.dds_._commoninfo import (
    commonCamera_224,
    commonCamera_640480,
    float_7d,
    uint_7d,
    uint_1d,
    float_1d,
    uint_100d,
    roboticArm_double_control_info,
    roboticArm_double_state_info,
    roboticArm_double_all_state_info
)


def generate_data(msg_type):

    if msg_type == commonCamera_224:
        return commonCamera_224(image=bytes(np.random.randint(0, 255, 150528, dtype=np.uint8)))
    elif msg_type == commonCamera_640480:
        return commonCamera_640480(image=bytes(np.random.randint(0, 255, 921600, dtype=np.uint8)))
    

    elif msg_type == float_7d:
        return float_7d(data=[random.random() for _ in range(7)])
    elif msg_type == uint_7d:
        return uint_7d(data=[random.random() for _ in range(7)])
    elif msg_type == uint_1d:
        return uint_1d(data=b'\x01')
    elif msg_type == float_1d:
        return float_1d(data=[random.random()])
    elif msg_type == uint_100d:
        return uint_100d(data=bytes(np.random.randint(0, 255, 100, dtype=np.uint8)))
    

    elif msg_type == roboticArm_double_control_info:
        return roboticArm_double_control_info(
            left_arm_joint_delta=float_7d(data=[0.1]*7),
            right_arm_joint_delta=float_7d(data=[0.1]*7),
            left_gripper_action=uint_1d(data=b'\x01'),
            right_gripper_action=uint_1d(data=b'\x00')
        )
    elif msg_type == roboticArm_double_state_info:
        return roboticArm_double_state_info(
            left_arm_q=float_7d(data=[0.1]*7),
            right_arm_q=float_7d(data=[0.1]*7),
            left_gripper=float_1d(data=[1.0]),
            right_gripper=float_1d(data=[0.0])
        )
    elif msg_type == roboticArm_double_all_state_info:
        return roboticArm_double_all_state_info(
            left_arm_q=float_7d(data=[0.1]*7),
            right_arm_q=float_7d(data=[0.1]*7),
            left_arm_dq=float_7d(data=[0.01]*7),
            right_arm_dq=float_7d(data=[0.01]*7),
            left_arm_tau=float_7d(data=[0.5]*7),
            right_arm_tau=float_7d(data=[0.5]*7),
            left_gripper=float_1d(data=[1.0]),
            right_gripper=float_1d(data=[0.0]),
            left_gripper_vel=float_1d(data=[0.1]),
            right_gripper_vel=float_1d(data=[0.1])
        )
    return None

def pub_task(wrapper_pub, msg_type, stop_event):
    while not stop_event.is_set():
        start_t = time.time()
        
        msg = generate_data(msg_type)
        if msg:
            wrapper_pub.write(msg)
        
        elapsed = time.time() - start_t
        time.sleep(max(1/60.0 - elapsed, 0))

def run_verification(msg_type):
    topic_name = f"rt/verify/{msg_type.__name__}"
    print(f"--- Verifying: {msg_type.__name__} ---")

    # 1. 启动 Subscriber Wrapper
    # 注意：根据你的 wrapper 代码，Sub 启动后会自动开启线程监听
    sub_wrapper = TeleaiCommonSub_1(0, topic_name, msg_type)

    # 2. 启动 Publisher Wrapper
    pub_wrapper = TeleaiCommonPub_1(0, topic_name, msg_type)

    # 3. 启动发布线程
    stop_event = threading.Event()
    pub_thread = threading.Thread(target=pub_task, args=(pub_wrapper, msg_type, stop_event))
    pub_thread.start()

    # 4. 等待数据流建立
    print("  Waiting for connection...")
    try:
        start_wait = time.time()
        while sub_wrapper.msg is None:
            if time.time() - start_wait > 5.0:
                raise TimeoutError("Timeout waiting for first message")
            time.sleep(0.1)
    except TimeoutError:
        print("  [FAIL] Connection timeout.")
        stop_event.set()
        pub_thread.join()
        return

    # 5. 采样检查 (运行约 2 秒)
    check_count = 0
    latencies = []
    start_check_time = time.time()
    last_processed_ts = 0

    while time.time() - start_check_time < 2.0:
        msg_data, src_ts = sub_wrapper.read()

        if msg_data is not None and src_ts != last_processed_ts:
            last_processed_ts = src_ts
            check_count += 1
            now_ns = time.time_ns()
            latency_ms = (now_ns - src_ts) / 1_000_000.0
            latencies.append(latency_ms)

        time.sleep(0.01) # 100Hz 采样检查

    # 6. 停止发布
    stop_event.set()
    pub_thread.join()
    
    # 7. 结果分析
    if check_count > 0:
        avg_lat = np.mean(latencies)
        print(f"  Messages Received: {check_count}")
        print(f"  Avg Latency:       {avg_lat:.4f} ms")
        
        # 简单的数据完整性检查 (以数组长度为例)
        valid_content = True
        if hasattr(msg_data, 'image'):
            if msg_type == commonCamera_224 and len(msg_data.image) != 150528: valid_content = False
        elif hasattr(msg_data, 'data'):
            if msg_type == float_7d and len(msg_data.data) != 7: valid_content = False
            
        if valid_content:
            print("  [PASS] Data content verified.")
        else:
            print("  [FAIL] Data content length mismatch.")

        if avg_lat > 20.0:
             print("  [WARN] Latency is high (>20ms).")
    else:
        print("  [FAIL] No unique messages processed.")
    
    print("\n")

def main():
    types_to_test = [
        float_7d,
        uint_7d,
        uint_1d,
        float_1d,
        uint_100d,
        roboticArm_double_control_info,
        roboticArm_double_state_info,
        roboticArm_double_all_state_info,
        commonCamera_224,
        commonCamera_640480
    ]

    print("Starting Wrapper Verification...")
    print("=" * 40)

    for t in types_to_test:
        run_verification(t)
        time.sleep(0.5)

    print("All tests finished.")

if __name__ == "__main__":
    main()