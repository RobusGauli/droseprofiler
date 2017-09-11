import websockets
import asyncio
import argparse
import platform

from serverprofiler.node import Node


class Slave:
    '''This represents the slave node in the monitoring cluster
        Main purpose -> register itself to the master server as the slave node
        -> recv the command from client, connect directly to the client socket
        -> master acts as the bridge between the client and this node
    '''
    DEFAULT_MASTER_HOST = '0.0.0.0'
    DEFAULT_MASTER_PORT = 5000
    MODE_HEADERS = [('mode', 'slave'), ('id', 'slave_one')]
    
    @classmethod
    def from_cli(cls):
        config = cls.load_from_cli()
        self = cls(config=config)
        return self

       


    def prepare_mode_headers(self):
        return [('mode', 'slave'), ('id', self.slave_id), ('cpu', platform.platform())]
    
    @classmethod
    def load_from_cli(cls):
        config = {}
        for key, val in vars(cls._get_args()).items():
            if val:
                key = 'MASTER_%s' % key.upper()
                config[key] = val
        return config

    
    @classmethod
    def _get_args(cls):
        parser = argparse.ArgumentParser(
            description='Slave Node for server profiler'
        )
        parser.add_argument(
            '-host',
            action='store',
            type=str,
            default=None,
            dest='host',
            help='Host to regsiter to.'
        )

        parser.add_argument(
            '-p', '--port',
            action='store',
            type=int,
            default=None,
            dest='port',
            help='Master port number'
        )
        parser.add_argument(
            '-id',
            action='store',
            type=str,
            dest='id',
            help='Unique slave id',
            required=True
        )
        
        return parser.parse_args()

        
    def __init__(self, config=None):
        self.node = Node()
        self.config = config
        self.ws = None
        
        self.master_host = config.get('MASTER_HOST') or self.DEFAULT_MASTER_HOST
        self.master_port = config.get('MASTER_PORT') or self.DEFAULT_MASTER_PORT
        self.slave_id = config.get('MASTER_ID') or 'Unknown'
        self.headers = self.prepare_mode_headers()
    
    

    async def handler(self):
        async with websockets.connect('ws://%s:%s/' % (self.master_host, self.master_port),
            extra_headers=self.headers) as ws:
            self.ws = ws
            await self._manage_client_session()
            while True:
                #just to keep the connection alive and yield the connection 
                await asyncio.sleep(0)
    
    async def _manage_client_session(self):
        self.ws.loop.create_task(self._manage_client_consumption())
        self.ws.loop.create_task(self._manage_client_production())

    async def _manage_client_consumption(self):
        while True:
            received = await self.ws.recv()
            print(received)
            await self.ws.send(self.slave_id + self.node.get_info())


    async def _manage_client_production(self):
        while True:
            
            await asyncio.sleep(0)
    
    
    def run(self):
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.handler())

    


if __name__ == '__main__':
    s = Slave.from_cli()
    s.run()

