import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        message = data.get('message')
        receiver_id = data.get('receiver_id')
        order_info = data.get('order_info')

        if not all([message_type, message, receiver_id]):
            return
        # 更新消息未读状态
        if message_type == 'mark_read':
            message_id = data.get('message_id')
            if not message_id:
                return
            await self.get_message_and_update(message_id)
            return

        receiver = await self.get_user(receiver_id)
        if not receiver:
            return

        chat_message = await self.save_message(message, receiver, order_info)
        if not chat_message:
            return

        message_data = {
            'type': 'chat_message',
            'message': message,
            'sender_id': self.user.id,
            'sender_name': self.user.username,
            'order_info': order_info,
            'is_read': False,
            "message_id": chat_message.id,
        }

        # Send message to sender's room group
        await self.channel_layer.group_send(
            self.room_name,
            message_data
        )

        # Send message to receiver's room group
        await self.channel_layer.group_send(
            f"user_{receiver.id}",
            message_data
        )
    

    @database_sync_to_async
    def get_message_and_update(self, message_id):
        message = ChatMessage.objects.get(id=message_id)
        if message.send_to.id == self.user.id:
            message.is_read = True
            message.save()
        return message

    async def chat_message(self, event):
        # 更新消息未读状态
        if 'message_id' in event:
            await self.get_message_and_update(event['message_id'])
        
        # 检查消息是否是发送者自己的消息
        if event.get('sender_id') == self.user.id and not event.get('is_history'):
            # 如果是发送者自己的消息且不是历史消息，则不重复显示
            return
        
        # 发送消息到WebSocket
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, message, receiver, order_info):
        try:
            return ChatMessage.objects.create(
                send_from=self.user,
                send_to=receiver,
                message=message,
                order_info=order_info
            )
        except Exception:
            return None