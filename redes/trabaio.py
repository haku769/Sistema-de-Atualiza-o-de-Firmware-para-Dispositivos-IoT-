import asyncio
import websockets
import random
import logging

logging.basicConfig(level=logging.INFO)

# ==================== SERVIDOR ====================

class FirmwareServer:
    def __init__(self):
        self.connected_clients = set()
        self.update_number = 1
        self.last_update = None

    async def register(self, websocket):
        self.connected_clients.add(websocket)
        logging.info(f"Cliente conectado. Total: {len(self.connected_clients)}")
        # Envia a última atualização ao novo cliente, se houver
        if self.last_update:
            await websocket.send(self.last_update)

    async def unregister(self, websocket):
        self.connected_clients.remove(websocket)
        logging.info(f"Cliente desconectado. Total: {len(self.connected_clients)}")

    async def handler(self, websocket, path):
        await self.register(websocket)
        try:
            async for _ in websocket:
                pass  # Ignora mensagens dos clientes
        finally:
            await self.unregister(websocket)

    async def send_updates(self):
        while True:
            if self.connected_clients:
                message = f"ATUALIZAÇÃO {self.update_number}"
                self.last_update = message
                logging.info(f"[SERVIDOR] Enviando: {message}")
                await asyncio.gather(*(client.send(message) for client in self.connected_clients))
                self.update_number += 1
            await asyncio.sleep(5)


# ==================== CLIENTES COM ATRASO ALEATÓRIO ====================

class SimulatedClient:
    def __init__(self, client_id, initial_delay):
        self.client_id = client_id
        self.initial_delay = initial_delay
        self.uri = "ws://localhost:8765"

    async def run(self):
        await asyncio.sleep(self.initial_delay)  # Simula entrada em tempos diferentes
        try:
            async with websockets.connect(self.uri) as websocket:
                logging.info(f"[CLIENTE {self.client_id}] Conectado após {self.initial_delay}s")
                while True:
                    msg = await websocket.recv()
                    # Simula variação de tempo de rede/processamento (exibição atrasada)
                    delay = random.uniform(0.5, 3.0)
                    await asyncio.sleep(delay)
                    print(f"[CLIENTE {self.client_id}] Recebeu (após {delay:.1f}s): {msg}")
        except Exception as e:
            logging.error(f"[CLIENTE {self.client_id}] Erro: {e}")


# ==================== EXECUÇÃO ====================

async def main():
    server = FirmwareServer()

    # Inicia o servidor
    server_task = websockets.serve(server.handler, "localhost", 8765)
    asyncio.create_task(server.send_updates())
    await server_task

    # Simula clientes conectando em tempos diferentes
    delays = [0, 2, 5, 7, 10]  # Clientes entram em tempos diferentes
    client_tasks = [SimulatedClient(i + 1, delay).run() for i, delay in enumerate(delays)]
    await asyncio.gather(*client_tasks)


# ==================== INÍCIO ====================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Simulação encerrada.")
