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

class CityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the city from query parameters (passed when the frontend connects)
        self.city = self.scope["query_string"].decode("utf-8").split("=")[-1]  # Extract city from query string
        
        if self.city:
            await self.channel_layer.group_add(self.city, self.channel_name)
        
        await self.accept()

    async def disconnect(self, close_code):
        if self.city:
            await self.channel_layer.group_discard(self.city, self.channel_name)

    async def new_group(self, event):
        """Send the new group data to all users in the city."""
        await self.send(text_data=json.dumps({
            "type": "New Group",
            "data": event["data"]  # Contains group info
        }))

class VolunteerRequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Expect the admin id as a URL parameter (e.g., /ws/volunteer_requests/<admin_id>/)
        self.admin_id = self.scope['url_route']['kwargs'].get('admin_id')
        if not self.admin_id:
            await self.close()
            return
        self.group_name = f"volunteer_requests_admin_{self.admin_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_volunteer_request(self, event):
        await self.send(text_data=json.dumps({
            "type": "New Volunteer Request",
            "data": event["data"]
        }))

class PhoneConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the phone number from the URL.
        self.phone_number = self.scope['url_route']['kwargs'].get('phone_number')
        if not self.phone_number:
            await self.close()
            return

        # Sanitize the phone number for use in a group name.
        # Replace '+' with 'plus' so that the group name contains only allowed characters.
        sanitized_phone = self.phone_number.replace("+", "plus")
        self.group_name = f"phone_updates_{sanitized_phone}"

        # Add the channel to the group.
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.phone_number:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_phone_update(self, event):
        """Send updates related to the phone number to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "Phone Update",
            "data": event["data"]
        }))
        
    async def send_chat_update(self, event):
        """Send chat messages to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "data": event["data"]
        }))

    async def send_task_update(self, event):
        """Send task updates to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "task_update",
            "data": event["data"]
        }))    