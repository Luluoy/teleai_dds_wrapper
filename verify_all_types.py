import threading
import time
import numpy as np
import random
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.qos import Qos, Policy
from cyclonedds.util import duration

# Import your generated modules
from commonInfo.msg.dds_._commoninfo import (
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

# Configuration
DOMAIN_ID = 0
TEST_DURATION_PER_TYPE = 2.0  # Seconds to test each type
PUBLISH_RATE = 60.0           # Hz

# Shared flag to control threads
running = True

# Helper to generate dummy data for specific types
def generate_data(msg_type, timestamp):
    if msg_type == commonCamera_224:
        return commonCamera_224(
            image=bytes(np.random.randint(0, 255, 150528, dtype=np.uint8)),
            timestamp=timestamp
        )
    elif msg_type == commonCamera_640480:
        return commonCamera_640480(
            image=bytes(np.random.randint(0, 255, 921600, dtype=np.uint8)),
            timestamp=timestamp
        )
    elif msg_type == float_7d:
        return float_7d(data=[random.random() for _ in range(7)], timestamp=timestamp)
    elif msg_type == uint_7d:
        return uint_7d(data=[random.random() for _ in range(7)], timestamp=timestamp)
    elif msg_type == uint_1d:
        return uint_1d(data=b'\x01', timestamp=timestamp)
    elif msg_type == float_1d:
        return float_1d(data=[random.random()], timestamp=timestamp)
    elif msg_type == uint_100d:
        return uint_100d(data=bytes(np.random.randint(0, 255, 100, dtype=np.uint8)))
    
    # Complex nested types
    elif msg_type == roboticArm_double_control_info:
        return roboticArm_double_control_info(
            left_arm_joint_delta=float_7d(data=[0.1]*7, timestamp=timestamp),
            right_arm_joint_delta=float_7d(data=[0.2]*7, timestamp=timestamp),
            left_gripper_action=uint_1d(data=b'\x01', timestamp=timestamp),
            right_gripper_action=uint_1d(data=b'\x00', timestamp=timestamp),
            timestamp=timestamp
        )
    elif msg_type == roboticArm_double_state_info:
        return roboticArm_double_state_info(
            left_arm_q=float_7d(data=[0.1]*7, timestamp=timestamp),
            right_arm_q=float_7d(data=[0.2]*7, timestamp=timestamp),
            left_gripper=float_1d(data=[1.0], timestamp=timestamp),
            right_gripper=float_1d(data=[0.0], timestamp=timestamp),
            timestamp=timestamp
        )
    elif msg_type == roboticArm_double_all_state_info:
        return roboticArm_double_all_state_info(
            left_arm_q=float_7d(data=[0.1]*7, timestamp=timestamp),
            right_arm_q=float_7d(data=[0.2]*7, timestamp=timestamp),
            left_arm_dq=float_7d(data=[0.01]*7, timestamp=timestamp),
            right_arm_dq=float_7d(data=[0.02]*7, timestamp=timestamp),
            left_arm_tau=float_7d(data=[0.5]*7, timestamp=timestamp),
            right_arm_tau=float_7d(data=[0.6]*7, timestamp=timestamp),
            left_gripper=float_1d(data=[1.0], timestamp=timestamp),
            right_gripper=float_1d(data=[0.0], timestamp=timestamp),
            left_gripper_vel=float_1d(data=[0.1], timestamp=timestamp),
            right_gripper_vel=float_1d(data=[0.2], timestamp=timestamp),
            timestamp=timestamp
        )
    return None

# Publisher Thread
def publisher_thread(msg_type, topic_name):
    dp = DomainParticipant(DOMAIN_ID)
    qos = Qos(Policy.Reliability.BestEffort) # Using BestEffort for high throughput test
    topic = Topic(dp, topic_name, msg_type)
    writer = DataWriter(dp, topic, qos)

    global running
    print(f"[Pub] Starting {msg_type.__name__}...")
    
    while running:
        start_time = time.time()
        msg = generate_data(msg_type, start_time)
        writer.write(msg)
        
        elapsed = time.time() - start_time
        sleep_time = max((1.0/PUBLISH_RATE) - elapsed, 0)
        time.sleep(sleep_time)

# Subscriber Thread
def subscriber_thread(msg_type, topic_name, results_dict):
    dp = DomainParticipant(DOMAIN_ID)
    qos = Qos(Policy.Reliability.BestEffort)
    topic = Topic(dp, topic_name, msg_type)
    reader = DataReader(dp, topic, qos)

    global running
    print(f"[Sub] Listening for {msg_type.__name__}...")

    total_latency = 0.0
    count = 0
    
    # Specific verification logic based on type
    while running:
        # --- Strict Sub Logic from Request ---
        for sample in reader.take():
            info = getattr(sample, "sample_info", None)
            if info is not None and not info.valid_data:
                continue
            print(abs(info.source_timestamp-time.time_ns()) / 1e6)
            # import pdb;pdb.set_trace()
            msg = getattr(sample, "data", sample)
            # -------------------------------------
            
            now = time.time()
            
            # Extract timestamp if available (uint_100d doesn't have it in your IDL)
            ts = getattr(msg, 'timestamp', None)
            if ts is not None:
                latency = (now - ts) * 1000.0
                total_latency += latency
            
            # Simple data integrity check (sampling first element or length)
            valid = True
            if hasattr(msg, 'image'):
                valid = len(msg.image) > 0
            elif hasattr(msg, 'data'):
                 valid = len(msg.data) > 0
            
            if valid:
                count += 1

        time.sleep(0.01)
    
    results_dict['count'] = count
    results_dict['avg_latency'] = (total_latency / count) if count > 0 else 0.0

def run_test(msg_type_class):
    global running
    running = True
    topic_name = f"rt/verify/{msg_type_class.__name__}"
    results = {}

    # Start threads
    pub_t = threading.Thread(target=publisher_thread, args=(msg_type_class, topic_name))
    sub_t = threading.Thread(target=subscriber_thread, args=(msg_type_class, topic_name, results))
    
    sub_t.start()
    time.sleep(0.5) # Give sub time to init
    pub_t.start()

    # Run for duration
    time.sleep(TEST_DURATION_PER_TYPE)

    # Stop threads
    running = False
    pub_t.join()
    sub_t.join()

    # Report
    print(f"\n--- Result: {msg_type_class.__name__} ---")
    print(f"Messages Received: {results.get('count', 0)}")
    print(f"Avg Latency:       {results.get('avg_latency', 0):.4f} ms")
    if results.get('avg_latency', 0) > 10.0:
        print("WARNING: High Latency detected!")
    print("-" * 40 + "\n")

def main():
    types_to_test = [
        # Basic Arrays
        float_7d,
        uint_7d,
        uint_1d,
        float_1d,
        uint_100d,
        
        # Complex Nested Structs
        roboticArm_double_control_info,
        roboticArm_double_state_info,
        roboticArm_double_all_state_info,
        
        # Heavy Images
        commonCamera_224,
        commonCamera_640480 # Uncomment to test (heavy load)
    ]

    print("Starting System Verification for All IDL Types...")
    print(f"Target Rate: {PUBLISH_RATE} Hz")
    print("=" * 60)

    for t in types_to_test:
        run_test(t)
        time.sleep(0.5) # Cooldown between tests

    print("All tests completed.")

if __name__ == "__main__":
    main()