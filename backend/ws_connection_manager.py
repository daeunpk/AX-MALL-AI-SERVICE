# connection_manager.py

from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict, exclude=None):
        for conn in self.active_connections:
            if conn == exclude:
                continue
            await conn.send_json(message)


    async def send_to(self, websocket: WebSocket, message: dict):
        """특정 클라이언트에게 메시지 전송"""
        await websocket.send_json(message)
