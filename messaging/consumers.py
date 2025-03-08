import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection attempt from:", self.scope['client'])
        await self.channel_layer.group_add("messages", self.channel_name)
        await self.accept()
        print("WebSocket connection accepted for:", self.scope['client'])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("messages", self.channel_name)

    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event.get("id"),
            "request": event.get("message"),
        }))