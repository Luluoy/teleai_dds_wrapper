from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.qos import Qos, Policy
from cyclonedds.util import duration
import cyclonedds.idl as idl
from teleai_dds_wrapper.utils import get_nano, nano_sleep

import threading
from collections import deque

from teleai_dds_wrapper.utils import logger

class TeleaiCommonPub_1(object):
    def __init__(self, domain_id:int, topic:str, struct_type:idl.IdlStruct, qos:Qos=None):
        if not qos:
            qos = Qos(
                Policy.Reliability.Reliable(max_blocking_time=duration(milliseconds=0)),
                Policy.Durability.Volatile,
<<<<<<< HEAD
                Policy.History.KeepLast(1),
=======
                Policy.History.KeepLast(3),
>>>>>>> 36f58be (readme)
                Policy.Deadline(duration(seconds=3600*24))
            )
        self._topic = topic
        self._struct_type = struct_type
        self._dp = DomainParticipant(domain_id)
        self._tp = Topic(self._dp, topic, struct_type)
        self._dw = DataWriter(self._dp, self._tp, qos)
        logger.info(f"Pub for {topic} start.")

    def write(self, info:idl.IdlStruct)->bool | None:
        # assert type(info) == self._struct_type, f"Pub for {self._topic} except type: {self._struct_type}, but {type(info)} was given."
        self.pre_communication()
        self._dw.write(info)
        self.post_communication()

    def pre_communication(self):
        pass
    def post_communication(self):
        pass

class TeleaiCommonSub_1(object):
    def __init__(self, domain_id:int, topic:str, struct_type:idl.IdlStruct, qos:Qos=None):
        if not qos:
            qos = Qos(
                Policy.Reliability.Reliable(max_blocking_time=duration(milliseconds=0)),
                Policy.Durability.Volatile,
<<<<<<< HEAD
                Policy.History.KeepLast(1),
=======
                Policy.History.KeepLast(3),
>>>>>>> 36f58be (readme)
                Policy.Deadline(duration(seconds=3600*24))
            )
        self._topic = topic
        self._struct_type = struct_type
        self._dp = DomainParticipant(domain_id)
        self._tp = Topic(self._dp, topic, struct_type)
        self._dr = DataReader(self._dp, self._tp, qos)

        self.msg = None

        self.lock = threading.Lock()
        self._read_cmd_thread = threading.Thread(target=self._listen_cmd)
        self._read_cmd_thread.daemon = True
        self._read_cmd_thread.start()
        
        self.last_recv_time:int = 0
        self.timeout_nano = duration(milliseconds=1000)
        logger.info(f"Sub for {topic} start.")

    def read(self)->idl.IdlStruct | None:
        with self.lock:
            return self.msg, self.last_recv_time
    
    def _listen_cmd(self):
        for sample in self._dr.take_iter():
            info = getattr(sample, "sample_info", None)
            if info is not None and not info.valid_data:
                continue
            msg = getattr(sample, "data", sample)

            self.last_recv_time = info.source_timestamp
            with self.lock:
                self.pre_communication()
                self.msg = msg
                self.post_communication()
            nano_sleep(duration(microseconds=100))
  
    def isTimeout(self) -> bool:
        return (get_nano() - self.last_recv_time) > self.timeout_nano
    
    def post_communication(self):
        pass

    def pre_communication(self):
        pass

    def wait_for_connection(self):
        while self.msg is None:
            nano_sleep(duration(seconds=0.1))
        nano_sleep(duration(seconds=0.1))

class TeleaiCommonSub_1q(object):
    def __init__(self, domain_id:int, topic:str, struct_type:idl.IdlStruct, qos:Qos=None):
        if not qos:
            qos = Qos(
                Policy.Reliability.Reliable(max_blocking_time=duration(milliseconds=0)),
                Policy.Durability.Volatile,
<<<<<<< HEAD
                Policy.History.KeepLast(1),
=======
                Policy.History.KeepLast(3),
>>>>>>> 36f58be (readme)
                Policy.Deadline(duration(seconds=3600*24))
            )
        self._topic = topic
        self._struct_type = struct_type
        self._dp = DomainParticipant(domain_id)
        self._tp = Topic(self._dp, topic, struct_type)
        self._dr = DataReader(self._dp, self._tp, qos)

<<<<<<< HEAD
        self.msg = None

        self.q = deque()
=======
        self.q = deque(maxlen=1)
>>>>>>> 36f58be (readme)
        self._read_cmd_thread = threading.Thread(target=self._listen_cmd)
        self._read_cmd_thread.daemon = True
        self._read_cmd_thread.start()
        
        self.last_recv_time:int = 0
        self.timeout_nano = duration(milliseconds=1000)
        logger.info(f"Sub for {topic} start.")

    def read(self)->idl.IdlStruct | None:
<<<<<<< HEAD
        self.q.pop_left() if self.q else None
=======
        if self.q:
            return self.q.pop_left()  
        else: 
            return None
>>>>>>> 36f58be (readme)
    
    def _listen_cmd(self):
        for sample in self._dr.take_iter():
            info = getattr(sample, "sample_info", None)
            if info is not None and not info.valid_data:
                continue
            msg = getattr(sample, "data", sample)

            self.last_recv_time = info.source_timestamp
            self.pre_communication()
            self.q.append(msg)
            self.post_communication()
            nano_sleep(duration(milliseconds=1))
  
    def isTimeout(self) -> bool:
        return (get_nano() - self.last_recv_time) > self.timeout_nano
    
    def post_communication(self):
        pass

    def pre_communication(self):
        pass

    def wait_for_connection(self):
<<<<<<< HEAD
        while self.msg is None:
            nano_sleep(duration(seconds=0.1))
        nano_sleep(duration(seconds=0.1))
=======
        while not self.q:
            nano_sleep(duration(seconds=0.1))
        nano_sleep(duration(seconds=0.1))
        logger.info(f"Sub for {self._topic} connected")
>>>>>>> 36f58be (readme)
