import collections
import itertools
import json
import asyncio

import websockets
from sanic import Sanic
from sanic_cors import CORS
from sanic.response import json as jsonify 




def get_header_val(headers):
    '''returns header dict'''
    return dict(headers)

class Master:

    DEFAULT_MASTER_HOST = '0.0.0.0'
    DEFAULT_MASTER_PORT = 5000
    DEFAULT_HTTP_PORT = 8000

    def __init__(self):
        self.slave_registry = {}

        self.http_server = Sanic(__name__)
        CORS(self.http_server)
        self.create_http_app()

    def create_http_app(self):
        
        async def snapshot(_):
            return jsonify({'nodes': [{'cpu': self.slave_registry[key]['cpu'], 'name': key} for key in self.slave_registry
                                        if self.slave_registry[key]['ws'].state == 1]})

        self.http_server.route('/nodes')(snapshot)

    
    async def handler(self, websocket: websockets.WebSocketClientProtocol, _: str):

        print('Got connection from the client', websocket)

        #check to see if it is the slave or client
        mode = get_header_val(websocket.request_headers._headers)
        _type_of_client = mode.get('mode')
        _id = mode.get('id')
        if _type_of_client == 'slave' and _id:
            #register as the slave server
            
            self.slave_registry[_id] = {}
            self.slave_registry[_id]['ws'] = websocket
            self.slave_registry[_id]['cpu'] = mode.get('cpu') 
            print(self.slave_registry)
            while True:
                await asyncio.sleep(0)
        #since this is the client that i coming,
        #we create a new instance of the of the connection that involves three major parameter
        client_cluster = ClientCluster(
            client_ws=websocket, 
            slave_registry=self.slave_registry,
        
        )

        websocket.loop.create_task(client_cluster.manage_production())
        websocket.loop.create_task(client_cluster.manage_consumption())
        while True:
            await asyncio.sleep(0)
            #it simply persist the connecrion and yield the control back to the event loop

    def run(self):
        _master_server = websockets.serve(
            self.handler,
            'localhost',
            5000
        )

        sanic_server = self.http_server.create_server(
            '0.0.0.0',
            port=8000
        )
        sanic_task = asyncio.ensure_future(sanic_server)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(_master_server, sanic_task))
        loop.run_forever()


class ClientCluster:
    '''Client cluster that represents the connected client and the registered slaves.'''

    def __init__(self, client_ws, slave_registry):
        self.client_ws = client_ws
        self.slave_registry = slave_registry
        self.current_slave_ws = None
        
    
    async def manage_consumption(self):
        while True:
            try:
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
                
                self.slave_registry.pop(request['destination'])
                
                break

    
    async def manage_production(self):
        while True:
            try:
                
                await asyncio.sleep(2)
            except websockets.exceptions.ConnectionClosed:
                print('Connection closed by the client')
                break


if __name__ == '__main__':
    m = Master()
    m.run()
    
