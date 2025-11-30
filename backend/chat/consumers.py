import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            # Join user's personal group
            self.room_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'send_message':
            receiver_id = data['receiver_id']
            content = data['content']
            
            # Save to DB
            await self.save_message(self.user.id, receiver_id, content)

            # Send to receiver
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    'type': 'chat_message',
                    'message': content,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username
                }
            )
            
            # Send back to sender (confirmation/echo)
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message': content,
                'receiver_id': receiver_id,
                'timestamp': str(data.get('timestamp', '')) # Should use server time
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        Message.objects.create(sender=sender, receiver=receiver, content=content)
        
        # Auto-create contacts if they don't exist
        from .models import Contact
        if not Contact.objects.filter(user=sender, contact=receiver).exists():
            Contact.objects.create(user=sender, contact=receiver)
        if not Contact.objects.filter(user=receiver, contact=sender).exists():
            Contact.objects.create(user=receiver, contact=sender)



