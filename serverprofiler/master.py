import collections
import itertools
import json
import asyncio
import argparse
import logging

import websockets
from sanic import Sanic
from sanic_cors import CORS
from sanic.response import json as jsonify, text

logging.getLogger('asyncio').setLevel(logging.DEBUG)


def get_header_val(headers):
    '''returns header dict'''
    return dict(headers)

class Master:
    '''Master Node in the profiling cluster'''

    DEFAULT_MASTER_HOST = '0.0.0.0'
    DEFAULT_MASTER_PORT = 5000
    DEFAULT_HTTP_PORT = 8000

    @classmethod
    def from_cli(cls, config=None):
        self = cls(config=config)
        return self

    def __init__(self, config=None):
        self.slave_registry = {}
        self.config = config or self._load_config_from_cli()

        
        self.master_host = self.config['MASTER_HOST'] or self.DEFAULT_MASTER_HOST
        self.master_port = self.config['MASTER_PORT'] or self.DEFAULT_MASTER_PORT
        self.http_port = self.config['MASTER_HTTP_PORT'] or self.DEFAULT_HTTP_PORT

        self.http_server = Sanic(__name__)
        CORS(self.http_server)
        self.create_http_app()
    
    @classmethod
    def _load_config_from_cli(cls):
        config = {}
        for key, val in vars(cls._from_args()).items():
            key = 'MASTER_' + key.upper() 
            config[key] = val
        return config
        
    
    @classmethod
    def _from_args(cls):

        parser = argparse.ArgumentParser(
            description='Master Node for server profiler'
        )
        parser.add_argument(
            '-host',
            action='store',
            type=str,
            default=None,
            dest='host',
            help='Master Host address'
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
            '-hp', '--httpport',
            action='store',
            type=int,
            dest='http_port',
            help='HTTP port number',
            required=False
        )
        
        return parser.parse_args()

    
    def create_http_app(self):
        
        
        async def snapshot(_):
            return jsonify({'nodes': [{'cpu': self.slave_registry[key]['cpu'], 'name': key} for key in self.slave_registry
                                        if self.slave_registry[key]['ws'].state == 1]})
        self.http_server.route('/nodes')(snapshot)
        
        async def get_info(_):
            print(self.slave_registry)
            current_slave_ws = self.slave_registry['robus']['ws']
            #send the json patload to the current selected slave
            await current_slave_ws.send('{"destination" : "robus", "route" : "/info"}')
            #get the response from the slave
            response_from_current_slave = await current_slave_ws.recv()
            #send back the response to the client
            
            return text(response_from_current_slave)
        self.http_server.route('/graph')(get_info)
        
        

    
    async def handler(self, websocket: websockets.WebSocketClientProtocol, _: str):

       
        #check to see if it is the slave or client
        mode = get_header_val(websocket.request_headers._headers)
        
        _type_of_client = mode.get('mode')
        _id = mode.get('id')
        if _type_of_client == 'slave' and _id:
            print('Got connection from the slave node', _id)

            #register as the slave server
            
            self.slave_registry[_id] = {}
            self.slave_registry[_id]['ws'] = websocket
            self.slave_registry[_id]['cpu'] = mode.get('cpu')
            
            while True:
                #await websocket.send('hi there to the slave')
                #await websocket.ping()
                await asyncio.sleep(3)
        #since this is the client that i coming,
        #we create a new instance of the of the connection that involves three major parameter
        print('got connection from fli')
        client_cluster = ClientCluster(
            client_ws=websocket, 
            slave_registry=self.slave_registry,
        )

        websocket.loop.create_task(client_cluster.manage_production())
        websocket.loop.create_task(client_cluster.manage_consumption())
        
        while True:
            await asyncio.sleep(3)

    def run(self):
        _master_server = websockets.serve(
            self.handler,
            self.master_host,
            self.master_port
        )

        sanic_server = self.http_server.create_server(
            '0.0.0.0',
            port=self.http_port
        )
        sanic_task = asyncio.ensure_future(sanic_server)

        loop = asyncio.get_event_loop()
        #loop.set_debug(True)
        loop.run_until_complete(asyncio.gather(_master_server, sanic_task))
        loop.run_forever()


class ClientCluster:
    '''Client cluster that represents the connected client and the registered slaves.'''

    def __init__(self, client_ws, slave_registry):
        self.client_ws = client_ws
        self.slave_registry = slave_registry
        self.current_slave_ws = None
        
    
    
    async def manage_consumption(self):
        count = 0
        while True:
            try:
                count += 1
                print('manager consumerionlooping', count)
                msg = await self.client_ws.recv()
                try:
                    request = json.loads(msg)
                except json.JSONDecodeError:
                    print('failed to decode')
                    continue
                if not request.get('destination'):
                    continue
                if not self.slave_registry.get(request['destination']):
                    continue
                #get the desitnation slave socket
                self.current_slave_ws = self.slave_registry[request['destination']]['ws']
                #send the json patload to the current selected slave
                await self.current_slave_ws.send(msg)
                #get the response from the slave
                response_from_current_slave = await self.current_slave_ws.recv()
                #send back the response to the client
                await self.client_ws.send(response_from_current_slave)

            except websockets.exceptions.ConnectionClosed:
                print('Connection closed by the client')
                
                #self.slave_registry.pop(request['destination'])
                
                break

    
    async def manage_production(self):
        while True:
            try:
                
                #await self.client_ws.send('hi there')
                await asyncio.sleep(3)
            except websockets.exceptions.ConnectionClosed:
                print('Connection closed by the client')
                break


if __name__ == '__main__':
    m = Master()
    m.run()
    

