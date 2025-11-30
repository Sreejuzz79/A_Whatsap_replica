import socketio
from app.utils.security import decode_token


sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')


connected = {} # user_id -> sid


@sio.event
async def connect(sid, environ):
    print('sio connect', sid)


@sio.event
async def authenticate(sid, data):
    token = data.get('token')
    payload = decode_token(token)
    if not payload:
      await sio.emit('auth_failed', {'msg': 'invalid token'}, to=sid)
      return
    user_id = payload['sub']
    connected[user_id] = sid
    await sio.save_session(sid, {'user_id': user_id})
    await sio.emit('auth_ok', {'user_id': user_id}, to=sid)


@sio.event
async def send_message(sid, data):
# data: {conversation_id, type, content, attachment_url}
    session = await sio.get_session(sid)
    if not session:
        await sio.emit('error', {'msg': 'not authenticated'}, to=sid)
        return
    sender = session['user_id']
# Here you would insert into DB. For brevity, we forward the message.
    payload = {**data, 'sender_id': sender}
# broadcast to conversation: in MVP we assume conversation has two users and their ids are provided
    for uid in data.get('member_ids', []):
        target_sid = connected.get(str(uid)) or connected.get(int(uid))
    if target_sid:
        await sio.emit('new_message', payload, to=target_sid)


@sio.event
async def disconnect(sid):
# clean up
    print('disconnect', sid)
# remove from connected dict
    to_delete = [k for k,v in connected.items() if v==sid]
    for k in to_delete:
        del connected[k]