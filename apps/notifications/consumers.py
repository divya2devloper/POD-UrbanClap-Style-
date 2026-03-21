import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        self.user_id = self.scope['user'].id
        self.group_name = f"photographer_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to PhotographyHub notifications'
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        pass  # Clients don't send messages; server pushes pings

    async def new_booking_ping(self, event):
        """Send new booking ping to WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'new_booking_ping',
            'booking_id': event['booking_id'],
            'service_name': event['service_name'],
            'customer_address': event['customer_address'],
            'scheduled_at': event['scheduled_at'],
            'budget': event['budget'],
            'distance_km': event['distance_km'],
        }))
