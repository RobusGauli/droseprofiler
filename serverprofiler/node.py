'''This module represents the any node/slave in the cluster'''
import os
import psutil
import platform
import itertools
import pwd
import json


user_name = lambda: pwd.getpwuid(os.getuid()).pw_name

uname = os.uname()

class Node(object):

    platform_name = platform.platform()

    p_num_cores = psutil.cpu_count(logical=False)
    l_num_cores = psutil.cpu_count(logical=True)

    _process_attrs = 'name username pid cpu_percent memory_percent status'.split()

    @staticmethod
    def filter_process(gen, name):
        for p in gen:
            if p.username() == name:
                yield p

    def __init__(self, alias=None):
        self.name = alias or self.platform_name
    
    def _cpu(self):
        '''return those variables that changes'''
        stats = psutil.cpu_stats()

        cpu_info = {
            'cu': psutil.cpu_percent(interval=0.0, percpu=False),
            'cupc': psutil.cpu_percent(interval=0.0, percpu=True),
            "cs": stats.ctx_switches,
            "ci": stats.interrupts,
            "sc": stats.syscalls
        }
        return cpu_info


    def _memory(self):
        mem = psutil.virtual_memory()

        memory_info = {
            't': mem.total // (1024 * 1024),
            'a': mem.available // (1024 * 1024),
            'p': mem.percent
        }
        return memory_info
    
    def _processes(self):
        for process in self.filter_process(psutil.process_iter(), user_name()):
            try:
                pinfo = process.as_dict(attrs=self._process_attrs)
            except psutil.NoSuchProcess:
                pass
            else:
                yield pinfo
    
    def _network(self):
        _net = psutil.net_io_counters()
        _n = {
            'bs': format(_net.bytes_sent / (1024 * 1024), '0.2f'),
            'br': format(_net.bytes_recv / (1024 * 1024), '0.2f'),
            'ps': _net.packets_sent,
            'pr': _net.packets_recv
        }
        return _n
    
    def get_info(self) -> str:
        return json.dumps({
            'id': self.name,
            'payload': {
                'cpu': self._cpu(),
                'memory': self._memory(),
                'processes': list(itertools.islice(self._processes(), 20)),
                'network': self._network(),
                'platform': self.platform_name,
                'p_cores': self.p_num_cores,
                'l_cors': self.l_num_cores
            },
            'status': 'success' 
        })
    
    def get_process_info(self, pid):
        
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return json.dumps({
                'id': self.name,
                'payload': None,
                'status': 'fail',
                'errormessage': 'Process does not eixsts.'
            })
        else:
            return json.dumps({
                'id': self.name,
                'payload': process.as_dict(),
                'status': 'success'
            })
        

