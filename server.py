import socket
import threading
import json
from db_manager import DatabaseManager

HOST = '127.0.0.1'
PORT = 5555

class ChatServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()
        self.clients = {} # {user_id: client_socket}
        self.db = DatabaseManager()
        print(f"Server running on {HOST}:{PORT}")

    def broadcast(self, message, receiver_id):
        if receiver_id in self.clients:
            client = self.clients[receiver_id]
            try:
                client.send(message.encode('utf-8'))
            except:
                client.close()
                del self.clients[receiver_id]

    def handle_client(self, client):
        user_id = None
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                if not message:
                    break
                
                data = json.loads(message)
                action = data.get('action')

                if action == 'REGISTER':
                    username = data['username']
                    password = data['password']
                    success, msg = self.db.register_user(username, password)
                    response = {'status': 'success' if success else 'error', 'message': msg}
                    client.send(json.dumps(response).encode('utf-8'))

                elif action == 'LOGIN':
                    username = data['username']
                    password = data['password']
                    success, result = self.db.login_user(username, password)
                    if success:
                        user_id = result['id']
                        self.clients[user_id] = client
                        response = {'status': 'success', 'user_id': user_id, 'username': username, 'message': 'Login successful'}
                    else:
                        response = {'status': 'error', 'message': result}
                    client.send(json.dumps(response).encode('utf-8'))

                elif action == 'GET_CONTACTS':
                    if user_id:
                        users = self.db.get_contacts(user_id)
                        response = {'action': 'CONTACT_LIST', 'users': users}
                        client.send(json.dumps(response).encode('utf-8'))

                elif action == 'SEARCH_USER':
                    if user_id:
                        target_username = data['username']
                        result = self.db.search_user(target_username)
                        if result:
                            response = {'action': 'SEARCH_RESULT', 'status': 'found', 'user': result}
                        else:
                            response = {'action': 'SEARCH_RESULT', 'status': 'not_found'}
                        client.send(json.dumps(response).encode('utf-8'))

                elif action == 'ADD_CONTACT':
                    if user_id:
                        contact_username = data['username']
                        success, msg = self.db.add_contact(user_id, contact_username)
                        response = {'action': 'ADD_RESULT', 'status': 'success' if success else 'error', 'message': msg}
                        client.send(json.dumps(response).encode('utf-8'))

                elif action == 'UPDATE_PROFILE':
                    if user_id:
                        success, msg = self.db.update_profile(
                            user_id, 
                            data.get('full_name'), 
                            data.get('mobile_number'), 
                            data.get('about'),
                            data.get('profile_picture')
                        )
                        response = {'action': 'PROFILE_UPDATE_RESULT', 'status': 'success' if success else 'error', 'message': msg}
                        client.send(json.dumps(response).encode('utf-8'))

                elif action == 'GET_PROFILE':
                    if user_id:
                        # If target_id is provided, get that user's profile, else get own
                        target_id = data.get('target_id', user_id)
                        profile = self.db.get_profile(target_id)
                        response = {'action': 'PROFILE_DATA', 'profile': profile}
                        client.send(json.dumps(response).encode('utf-8'))

                elif action == 'SEND_MSG':
                    if user_id:
                        receiver_id = data['receiver_id']
                        content = data['content']
                        self.db.save_message(user_id, receiver_id, content)
                        
                        # Send to receiver if online
                        msg_payload = {
                            'action': 'NEW_MSG',
                            'sender_id': user_id,
                            'content': content,
                            'sender_name': data.get('sender_name', 'Unknown')
                        }
                        self.broadcast(json.dumps(msg_payload), receiver_id)

                elif action == 'GET_HISTORY':
                    if user_id:
                        other_user_id = data['other_user_id']
                        history = self.db.get_chat_history(user_id, other_user_id)
                        # Convert datetime objects to string for JSON serialization
                        for msg in history:
                            msg['timestamp'] = str(msg['timestamp'])
                        
                        response = {'action': 'HISTORY_DATA', 'history': history, 'other_user_id': other_user_id}
                        client.send(json.dumps(response).encode('utf-8'))

            except Exception as e:
                print(f"Error handling client: {e}")
                break
        
        if user_id and user_id in self.clients:
            del self.clients[user_id]
        client.close()

    def start(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()




