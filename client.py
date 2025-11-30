import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import threading
import json
from ui_components import *

HOST = '127.0.0.1'
PORT = 5555

class WhatsAppClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Clone")
        self.root.geometry("900x600")
        self.root.configure(bg=BG_COLOR)
        
        self.client = None
        self.user_id = None
        self.username = None
        self.current_chat_id = None
        
        self.connect_to_server()
        self.show_login_screen()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def connect_to_server(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server: {e}")

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message:
                    break
                
                data = json.loads(message)
                self.root.after(0, self.handle_server_response, data)
            except:
                break

    def handle_server_response(self, data):
        action = data.get('action')
        
        if 'status' in data: # Login/Register response
            if data['status'] == 'success':
                if 'user_id' in data: # Login success
                    self.user_id = data['user_id']
                    self.username = data['username']
                    self.show_main_ui()
                    self.request_contact_list()
                else: # Register success
                    messagebox.showinfo("Success", data['message'])
                    self.show_login_screen()
            else:
                messagebox.showerror("Error", data['message'])
                
        elif action == 'CONTACT_LIST':
            self.update_contact_list(data['users'])
            
        elif action == 'ADD_RESULT':
            if data['status'] == 'success':
                messagebox.showinfo("Success", data['message'])
                self.request_contact_list()
            else:
                messagebox.showerror("Error", data['message'])

        elif action == 'PROFILE_UPDATE_RESULT':
            messagebox.showinfo("Profile", data['message'])
            if data['status'] == 'success':
                # Refresh profile if needed
                pass

        elif action == 'PROFILE_DATA':
            self.show_profile_popup(data['profile'])

        elif action == 'NEW_MSG':
            sender_id = data['sender_id']
            content = data['content']
            if self.current_chat_id == sender_id:
                self.display_message(content, is_sender=False)
            else:
                # Optional: Show notification or highlight contact
                pass
                
        elif action == 'HISTORY_DATA':
            if self.current_chat_id == data['other_user_id']:
                self.chat_area_frame.destroy()
                self.create_chat_area() # Clear and recreate
                for msg in data['history']:
                    is_sender = (msg['sender_id'] == self.user_id)
                    self.display_message(msg['content'], is_sender, str(msg['timestamp']))

    def request_contact_list(self):
        req = {'action': 'GET_CONTACTS'}
        self.client.send(json.dumps(req).encode('utf-8'))

    def add_contact_dialog(self):
        username = simpledialog.askstring("Add Contact", "Enter username to add:")
        if username:
            req = {'action': 'ADD_CONTACT', 'username': username}
            self.client.send(json.dumps(req).encode('utf-8'))

    def request_my_profile(self):
        req = {'action': 'GET_PROFILE'}
        self.client.send(json.dumps(req).encode('utf-8'))

    def show_profile_popup(self, profile_data):
        popup = tk.Toplevel(self.root)
        popup.title("My Profile")
        popup.geometry("400x500")
        popup.configure(bg=BG_COLOR)

        tk.Label(popup, text="Profile", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=10)

        # Fields
        fields = {
            "Full Name": profile_data.get('full_name', ''),
            "Mobile Number": profile_data.get('mobile_number', ''),
            "About": profile_data.get('about', ''),
            "Profile Picture (URL/Base64)": profile_data.get('profile_picture', '')
        }
        entries = {}

        for label, value in fields.items():
            tk.Label(popup, text=label, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", padx=20)
            entry = tk.Entry(popup, font=("Segoe UI", 11))
            entry.insert(0, value if value else "")
            entry.pack(fill="x", padx=20, pady=5)
            entries[label] = entry

        def save_profile():
            req = {
                'action': 'UPDATE_PROFILE',
                'full_name': entries["Full Name"].get(),
                'mobile_number': entries["Mobile Number"].get(),
                'about': entries["About"].get(),
                'profile_picture': entries["Profile Picture (URL/Base64)"].get()
            }
            self.client.send(json.dumps(req).encode('utf-8'))
            popup.destroy()

        tk.Button(popup, text="Save", command=save_profile, bg=BUTTON_COLOR, fg="white").pack(pady=20)

    def logout(self):
        self.user_id = None
        self.username = None
        self.current_chat_id = None
        self.show_login_screen()

    def open_emoji_picker(self):
        EmojiPicker(self.root, self.insert_emoji)

    def insert_emoji(self, emoji):
        self.msg_entry.insert(tk.INSERT, emoji)

    def send_message(self):
        content = self.msg_entry.get()
        if content and self.current_chat_id:
            req = {
                'action': 'SEND_MSG',
                'receiver_id': self.current_chat_id,
                'content': content,
                'sender_name': self.username
            }
            self.client.send(json.dumps(req).encode('utf-8'))
            self.display_message(content, is_sender=True)
            self.msg_entry.delete(0, tk.END)

    def load_chat(self, user_id, username):
        self.current_chat_id = user_id
        self.chat_header_lbl.config(text=username)
        
        # Request history
        req = {'action': 'GET_HISTORY', 'other_user_id': user_id}
        self.client.send(json.dumps(req).encode('utf-8'))

    # --- UI Methods ---
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="WhatsApp Clone", font=("Segoe UI", 20, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=20)
        
        tk.Label(frame, text="Username", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        self.username_entry = tk.Entry(frame, font=("Segoe UI", 12))
        self.username_entry.pack(pady=5, fill="x")
        
        tk.Label(frame, text="Password", bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        self.password_entry = tk.Entry(frame, show="*", font=("Segoe UI", 12))
        self.password_entry.pack(pady=5, fill="x")
        
        tk.Button(frame, text="Login", command=self.login, bg=BUTTON_COLOR, fg="white", font=("Segoe UI", 12)).pack(pady=10, fill="x")
        tk.Button(frame, text="Register", command=self.register, bg=SIDEBAR_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 12)).pack(pady=5, fill="x")

    def show_main_ui(self):
        self.clear_window()
        
        # Sidebar (Moved to Right)
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR_COLOR, width=250)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Sidebar Header
        sidebar_header = tk.Frame(self.sidebar, bg=SIDEBAR_COLOR)
        sidebar_header.pack(fill="x", pady=10, padx=10)
        
        tk.Button(sidebar_header, text="👤", command=self.request_my_profile, bg=SIDEBAR_COLOR, fg=TEXT_COLOR, relief="flat", font=("Segoe UI", 12)).pack(side="left")
        tk.Label(sidebar_header, text="Chats", bg=SIDEBAR_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 16, "bold")).pack(side="left", padx=5)
        
        tk.Button(sidebar_header, text="🚪", command=self.logout, bg=SIDEBAR_COLOR, fg="#ff4444", relief="flat", font=("Segoe UI", 12)).pack(side="right")
        tk.Button(sidebar_header, text="+", command=self.add_contact_dialog, bg=BUTTON_COLOR, fg="white", font=("Segoe UI", 12, "bold"), width=3).pack(side="right", padx=5)
        
        self.contact_list_frame = tk.Frame(self.sidebar, bg=SIDEBAR_COLOR)
        self.contact_list_frame.pack(fill="both", expand=True)

        # Chat Area (Moved to Left)
        self.chat_main = tk.Frame(self.root, bg=CHAT_BG_COLOR)
        self.chat_main.pack(side="left", fill="both", expand=True)
        
        # Header
        self.chat_header = tk.Frame(self.chat_main, bg=SIDEBAR_COLOR, height=50)
        self.chat_header.pack(fill="x")
        self.chat_header_lbl = tk.Label(self.chat_header, text="Select a contact", bg=SIDEBAR_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 12, "bold"))
        self.chat_header_lbl.pack(side="left", padx=20, pady=10)
        
        # Messages Area
        self.create_chat_area()
        
        # Input Area
        self.input_area = tk.Frame(self.chat_main, bg=SIDEBAR_COLOR, height=60)
        self.input_area.pack(fill="x", side="bottom")
        
        tk.Button(self.input_area, text="😀", command=self.open_emoji_picker, bg=SIDEBAR_COLOR, fg=TEXT_COLOR, relief="flat", font=("Segoe UI Emoji", 12)).pack(side="left", padx=5)
        
        self.msg_entry = tk.Entry(self.input_area, bg=INPUT_BG_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 12), relief="flat")
        self.msg_entry.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=10)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        send_btn = tk.Button(self.input_area, text="➤", command=self.send_message, bg=BUTTON_COLOR, fg="white", font=("Segoe UI", 12))
        send_btn.pack(side="right", padx=10)

    def create_chat_area(self):
        self.chat_area_canvas = tk.Canvas(self.chat_main, bg=CHAT_BG_COLOR, highlightthickness=0)
        self.chat_scrollbar = ttk.Scrollbar(self.chat_main, orient="vertical", command=self.chat_area_canvas.yview)
        self.chat_area_frame = tk.Frame(self.chat_area_canvas, bg=CHAT_BG_COLOR)
        
        self.chat_area_frame.bind(
            "<Configure>",
            lambda e: self.chat_area_canvas.configure(
                scrollregion=self.chat_area_canvas.bbox("all")
            )
        )
        
        self.chat_area_canvas.create_window((0, 0), window=self.chat_area_frame, anchor="nw", width=self.root.winfo_width()-250) # Approx width
        self.chat_area_canvas.configure(yscrollcommand=self.chat_scrollbar.set)
        
        self.chat_area_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")

    def update_contact_list(self, users):
        for widget in self.contact_list_frame.winfo_children():
            widget.destroy()
            
        for user in users:
            item = ContactItem(self.contact_list_frame, user['username'], user['id'], self.load_chat)
            item.pack(fill="x", pady=1)

    def display_message(self, text, is_sender, timestamp=""):
        ChatBubble(self.chat_area_frame, text, is_sender, timestamp).pack(fill="x", pady=2)
        self.root.update_idletasks() # Force update to get correct scroll region
        self.chat_area_canvas.yview_moveto(1.0)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            req = {'action': 'LOGIN', 'username': username, 'password': password}
            self.client.send(json.dumps(req).encode('utf-8'))

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            req = {'action': 'REGISTER', 'username': username, 'password': password}
            self.client.send(json.dumps(req).encode('utf-8'))

    def on_closing(self):
        if self.client:
            self.client.close()
        self.root.destroy()

if __name__ == "__main__":
    WhatsAppClient()
