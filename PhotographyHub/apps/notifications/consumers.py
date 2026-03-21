from channels.generic.websocket import AsyncJsonWebsocketConsumer


class PhotographerPingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        self.group_name = f"photographer_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def booking_ping(self, event):
        await self.send_json(
            {
                "event": "ping",
                "booking_id": event["booking_id"],
                "service_category": event.get("service_category", "General Photography"),
                "distance_km": event["distance_km"],
                "ping_radius_km": event["ping_radius_km"],
            }
        )
