import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a group for new admin notifications.
        await self.channel_layer.group_add("new_admin_users", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("new_admin_users", self.channel_name)

    async def new_admin(self, event):
        # Broadcast new admin data to connected clients.
        await self.send(text_data=json.dumps({
            "admin": event["admin"]
        }))
        
class ProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join the progress_updates group.
        await self.channel_layer.group_add("progress_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("progress_updates", self.channel_name)

    async def progress_update(self, event):
        # Send the event data (which should contain "admin") to the client.
        await self.send(text_data=json.dumps(event))
