import numpy as np
# import cv2

import time
from teleai_dds_wrapper.wrapper import TeleaiCommonPub_1
from teleai_dds_wrapper.commonInfo.msg.dds_._commoninfo import commonCamera_640480

import pyrealsense2 as rs

def main():
    
    pub = TeleaiCommonPub_1(domain_id = 0,
                            topic = "rt/commonCamera_t",
                            struct_type=commonCamera_640480,
                            )
    pipeline = rs.pipeline()
    config = rs.config()
    # config.enable_device("f1422216")
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    try:
        pipeline.start(config)
    except Exception as e:
        print(f"致命错误: 无法启动 RealSense。请检查 USB 穿透或线缆连接。细节: {e}")
        return

    print("pub start.")

    while True:
        # start = time.perf_counter()
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        img = bytes(color_frame.get_data())
        info = commonCamera_640480(
            image=img,
        )
        pub.write(info)
        
        # time.sleep(max(1/60 - abs(time.perf_counter() - start), 0))

if __name__ == "__main__":
    main()

