import numpy as np
# import cv2

import time
import cv2

from teleai_dds_wrapper.wrapper import TeleaiCommonSub_1q
from teleai_dds_wrapper.commonInfo.msg.dds_._commoninfo import commonCamera_640480

def main():
    sub = TeleaiCommonSub_1q(domain_id=0,
                            topic = "rt/commonCamera_t",
                            struct_type=commonCamera_640480
                            )
    print("sub waiting.")
    sub.wait_for_connection()
    print("sub start.")


    cnt = 0
    while True:
        start = time.perf_counter()
        msg = sub.read()
    
        img_bytes = msg.image
        img_array = np.frombuffer(img_bytes, dtype=np.uint8).reshape((480, 640, 3))
        
        # print((time.time_ns() - nanots) / 1e6)
        # cv2.imshow('Received RealSense Stream', img_array)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     cv2.destroyAllWindows()
        #     return -1
        if cnt >= 99:
            cv2.imwrite("test.png", img_array)
            break
        cnt += 1
        time.sleep(max(1/30 - (time.perf_counter() - start), 0))

if __name__ == "__main__":
    main()