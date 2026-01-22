from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.sub import DataReader
from cyclonedds.qos import Qos, Policy
from cyclonedds.util import duration
import cyclonedds.idl as idl
import time
import threading

from teleai_dds_wrapper.utils import logger

class TeleaiCommonPub_1(object):
    def __init__(self, domain_id:int, topic:str, struct_type:idl.IdlStruct, qos:Qos=None):
        if not qos:
            qos = Qos(
                Policy.Reliability.Reliable(max_blocking_time=duration(milliseconds=0)),
                Policy.Durability.Volatile,
                Policy.History.KeepLast(3),
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
                Policy.History.KeepLast(3),
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
        
        self.last_recv_time = 0.
        self.timeout_ms = 1000.
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
            time.sleep(0.001)
  
    def isTimeout(self) -> bool:
        return time.time_ns() - self.last_recv_time/1e6 > self.timeout_ms / 1000.
    
    def post_communication(self):
        pass

    def pre_communication(self):
        pass

    def wait_for_connection(self):
        while self.msg is None:
            time.sleep(0.1)
        time.sleep(0.1)
