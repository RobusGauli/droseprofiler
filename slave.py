import websockets
import asyncio


class Slave:
    '''This represents the slave node in the monitoring cluster
        Main purpose -> register itself to the master server as the slave node
        -> recv the command from client, connect directly to the client socket
        -> master acts as the bridge between the client and this node
    '''
    MASTER_HOST = 'localhost'
    MASTER_PORT = 5000

    def __init__(self, config=None):
        self.config = config
        self.ws = None

    async def run(self):
        async with websockets.connect('ws://%s:%s/' % (self.MASTER_HOST, self.MASTER_PORT)) as ws:
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


    async def _manage_client_production(self):
        while True:
            await self.ws.send('hi from the client')
            await asyncio.sleep(3)
        
    


if __name__ == '__main__':
    slave = Slave()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(slave.run())
