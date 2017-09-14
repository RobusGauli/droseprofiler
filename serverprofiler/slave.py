import websockets
import asyncio
import argparse
import platform
import json
import functools

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
        
        self = cls(config=None)
        return self

       


    def prepare_mode_headers(self):
        return [('mode', 'slave'), ('id', self.slave_id), ('cpu', platform.platform())]
    
    @classmethod
    def load_from_cli(cls):
        config = {}
        for key, val in vars(cls._get_args()).items():
            if val:
                key = 'MASTER_%s' % key.upper() if key != 'id' else 'SLAVE_%s' % key.upper()
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
        self.config = config or self.load_from_cli()
        #connection to the master node
        self.ws = None
        
        self.master_host = self.config.get('MASTER_HOST') or self.DEFAULT_MASTER_HOST
        self.master_port = self.config.get('MASTER_PORT') or self.DEFAULT_MASTER_PORT
        self.slave_id = self.config.get('SLAVE_ID') or 'Unknown'
        self.headers = self.prepare_mode_headers()
        self.action_dispatcher = None
        # self.register = {}
        # self.action_manager()
        # print(self.register)
        
    
    

    async def handler(self):
        async with websockets.connect('ws://%s:%s/' % (self.master_host, self.master_port),
            extra_headers=self.headers) as ws:
            self.action_dispatcher = ActionDispatcher(ws)

            consumer_task = asyncio.ensure_future(self._manage_client_consumption(ws))
            producer_task = asyncio.ensure_future(self._manage_client_production(ws))
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
    
            # while True:
            #     #just to keep the connection alive and yield the connection 
            #     # msg = await self.ws.recv()
            #     # #print(msg)
            #     # await self.ws.send(self.node.get_info())
            #     #await self.ws.ping()
            #     await asyncio.sleep(0)
    
    
        
    async def _manage_client_consumption(self, ws):
        while True:
            
            received = await ws.recv()
            try:
                r = json.loads(received)
            except json.JSONDecodeError:
                continue
            await self.action_dispatcher.dispatch(r['route'])
            # if route:
            #     print(self.register[route])
            #     await self.register[route](ws)

    async def _manage_client_production(self, ws):
        while True:
            
            #making it to 0 will get the cpu consumption to 100%
            await asyncio.sleep(2)
    
    # def action_manager(self):

    #     @self.route('/info')
    #     async def get_info(ws):
    #         await ws.send('ho from theinner function')
        
        
        
    

    # def route(self, route):
        
    #     def wrapper(func):
    #         self.register[route] = func   
    #     return wrapper         


    def run(self):
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.handler())
        

    


class ActionDispatcher:

    def __init__(self, master_ws):
        self.master_ws = master_ws
        self.register = {}
        self._initialize_routes_func()
        

    
    def route(self, path):
        def _wrapper(func):
            self.register[path] = func
        return _wrapper

    
    def _initialize_routes_func(self):
        @self.route('/info')    
        async def get_cpu_info():
            await self.master_ws.send('hi form the action manager')
        
        
    
    async def dispatch(self, route):
        #given the dispatch command i shoulde be abpe to perform the action
        _func = self.register.get(route)
        if _func:
            await _func()
if __name__ == '__main__':
    s = Slave.from_cli()
    s.run()

