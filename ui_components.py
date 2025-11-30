import tkinter as tk
from tkinter import ttk

# Colors
BG_COLOR = "#1e1e1e"
SIDEBAR_COLOR = "#252526"
CHAT_BG_COLOR = "#1e1e1e"
MSG_SENT_COLOR = "#005c4b"
MSG_RECEIVED_COLOR = "#202c33"
TEXT_COLOR = "#e9edef"
INPUT_BG_COLOR = "#2a3942"
BUTTON_COLOR = "#00a884"

class ChatBubble(tk.Frame):
    def __init__(self, master, text, is_sender=True, timestamp=""):
        bg = MSG_SENT_COLOR if is_sender else MSG_RECEIVED_COLOR
        align = "e" if is_sender else "w"
        
        super().__init__(master, bg=CHAT_BG_COLOR)
        
        self.bubble = tk.Label(
            self, 
            text=text, 
            bg=bg, 
            fg=TEXT_COLOR, 
            font=("Segoe UI", 11), 
            wraplength=250, 
            justify="left",
            padx=10, 
            pady=5,
            relief="flat",
            bd=0
        )
        self.bubble.pack(anchor=align, padx=10, pady=2)
        
        if timestamp:
            self.time_lbl = tk.Label(
                self, 
                text=timestamp, 
                bg=CHAT_BG_COLOR, 
                fg="#8696a0", 
                font=("Segoe UI", 8)
            )
            self.time_lbl.pack(anchor=align, padx=10)

class ContactItem(tk.Frame):
    def __init__(self, master, username, user_id, callback):
        super().__init__(master, bg=SIDEBAR_COLOR, pady=5, padx=5)
        self.user_id = user_id
        self.callback = callback
        
        self.lbl = tk.Label(
            self, 
            text=username, 
            bg=SIDEBAR_COLOR, 
            fg=TEXT_COLOR, 
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        self.lbl.pack(fill="x", expand=True)
        
        self.bind("<Button-1>", self.on_click)
        self.lbl.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        self.callback(self.user_id, self.lbl.cget("text"))

class EmojiPicker(tk.Toplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title("Emojis")
        self.geometry("300x300")
        self.configure(bg=BG_COLOR)
        
        # Simple grid of emojis
        emojis = [
            "😀", "😂", "😍", "😎", "😭", "😡", "👍", "👎",
            "🎉", "❤️", "🔥", "✨", "🤔", "🙄", "😴", "🤢",
            "👋", "🙏", "🤝", "✌️", "💀", "👻", "👽", "🤖"
        ]
        
        row = 0
        col = 0
        for emoji in emojis:
            btn = tk.Button(
                self, 
                text=emoji, 
                font=("Segoe UI Emoji", 14), 
                bg=SIDEBAR_COLOR, 
                fg="white", 
                relief="flat",
                command=lambda e=emoji: self.on_emoji_click(e)
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            col += 1
            if col > 5:
                col = 0
                row += 1

    def on_emoji_click(self, emoji):
        self.callback(emoji)
        # self.destroy() # Keep open or close? User might want multiple. Let's keep open.
