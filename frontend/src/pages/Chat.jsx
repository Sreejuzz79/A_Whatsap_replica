import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../api';
import { FaUser, FaSignOutAlt, FaPlus, FaSmile, FaPaperPlane, FaBars, FaEllipsisV, FaTimes, FaSearch, FaArrowLeft, FaCamera, FaCog, FaVideo, FaPhone, FaCheck, FaCheckDouble } from 'react-icons/fa';
import VideoCall from '../components/VideoCall';
// import EmojiPicker from 'emoji-picker-react';

export const Chat = () => {
    const { user, logout, checkUser } = useContext(AuthContext);
    const [contacts, setContacts] = useState([]);
    const [activeChat, setActiveChat] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [socket, setSocket] = useState(null);
    const messagesEndRef = useRef(null);
    const menuRef = useRef(null);
    const emojiPickerRef = useRef(null);

    // UI States
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [showMenu, setShowMenu] = useState(false);
    const [showGlobalSearch, setShowGlobalSearch] = useState(false);
    const [showContactList, setShowContactList] = useState(false);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [showContactProfileModal, setShowContactProfileModal] = useState(false);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [isVideoCallInitiator, setIsVideoCallInitiator] = useState(false);
    const [callType, setCallType] = useState('video'); // 'video' or 'audio'
    const [showCalls, setShowCalls] = useState(false);
    const [callHistory, setCallHistory] = useState([]);

    // Profile Data State
    const [profileData, setProfileData] = useState({
        full_name: '',
        about: '',
        profile_picture: ''
    });

    // Search States
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [contactFilter, setContactFilter] = useState('');

    useEffect(() => {
        fetchContacts();
        fetchCalls();
        connectWebSocket();

        // Click outside listener for menu and emoji picker
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setShowMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            if (socket) socket.close();
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const onEmojiClick = (emojiObject) => {
        setInput(prevInput => prevInput + emojiObject.emoji);
    };

    useEffect(() => {
        if (activeChat) {
            fetchHistory(activeChat.contact_user.id);
            markMessagesRead(activeChat.contact_user.id);
            if (window.innerWidth < 768) setSidebarOpen(false);
        }
    }, [activeChat]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (showProfileModal && user) {
            setProfileData({
                full_name: user.full_name || '',
                about: user.about || '',
                profile_picture: user.profile_picture || ''
            });
        }
    }, [showProfileModal, user]);

    const connectWebSocket = () => {
        const token = localStorage.getItem('token');
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';
        const ws = new WebSocket(`${wsUrl}/ws/chat/?token=${token}`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'new_message' || data.type === 'message_sent') {
                setMessages(prev => [...prev, {
                    id: data.id,
                    sender_username: data.sender_username || user.username,
                    content: data.message,
                    timestamp: data.timestamp,
                    sender: data.sender_id || user.id,
                    read: false // Default to unread
                }]);
                fetchContacts();
            } else if (data.type === 'messages_read') {
                // Update local messages to read
                if (activeChat && activeChat.contact_user.id === data.reader_id) {
                    setMessages(prev => prev.map(msg =>
                        data.message_ids.includes(msg.id) ? { ...msg, read: true } : msg
                    ));
                }
            } else if (data.type === 'user_status') {
                // Update active chat user status if it matches
                if (activeChat && activeChat.contact_user.id === data.user_id) {
                    setActiveChat(prev => ({
                        ...prev,
                        contact_user: {
                            ...prev.contact_user,
                            is_online: data.status === 'online',
                            last_seen: data.last_seen
                        }
                    }));
                }
            }
        };
        setSocket(ws);
    };

    const fetchContacts = async () => {
        const res = await api.get('contacts/');
        setContacts(res.data);
    };

    const fetchCalls = async () => {
        try {
            const res = await api.get('calls/');
            setCallHistory(res.data);
        } catch (err) {
            console.error("Failed to fetch calls", err);
        }
    };

    const markMessagesRead = async (contactId) => {
        try {
            await api.post(`messages/${contactId}/read/`);
            fetchContacts(); // Refresh to clear unread count
        } catch (err) {
            console.error("Failed to mark read", err);
        }
    };

    const fetchHistory = async (userId) => {
        const res = await api.get(`messages/${userId}/`);
        setMessages(res.data);
    };

    const sendMessage = () => {
        if (!input.trim() || !activeChat || !socket) return;

        socket.send(JSON.stringify({
            action: 'send_message',
            receiver_id: activeChat.contact_user.id,
            content: input
        }));
        setInput('');
    };

    const handleGlobalSearch = async (e) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        try {
            console.log("Searching for:", searchQuery);
            const res = await api.get(`search/?q=${searchQuery}`);
            console.log("Search results:", res.data);
            setSearchResults(res.data);
        } catch (err) {
            console.error("Search failed", err.response || err);
        }
    };

    const startChat = (selectedUser) => {
        const existing = contacts.find(c => c.contact_user.id === selectedUser.id);
        if (existing) {
            setActiveChat(existing);
        } else {
            setActiveChat({
                id: 'temp_' + selectedUser.id,
                contact_user: selectedUser
            });
        }
        setShowGlobalSearch(false);
        setShowContactList(false);
        setSearchQuery('');
        setSearchResults([]);
        setContactFilter('');
    };

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;
                    const MAX_WIDTH = 800;
                    const MAX_HEIGHT = 800;

                    if (width > height) {
                        if (width > MAX_WIDTH) {
                            height *= MAX_WIDTH / width;
                            width = MAX_WIDTH;
                        }
                    } else {
                        if (height > MAX_HEIGHT) {
                            width *= MAX_HEIGHT / height;
                            height = MAX_HEIGHT;
                        }
                    }

                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    const dataUrl = canvas.toDataURL('image/jpeg', 0.7); // Compress to 70% quality
                    setProfileData({ ...profileData, profile_picture: dataUrl });
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    };

    const saveProfile = async () => {
        try {
            await api.patch('auth/profile', profileData);
            await checkUser();
            setShowProfileModal(false);
            alert("Profile updated successfully!");
        } catch (err) {
            console.error("Profile update failed", err);
            alert("Failed to update profile.");
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const filteredContacts = contacts.filter(c =>
        (c.contact_user.full_name || '').toLowerCase().includes(contactFilter.toLowerCase()) ||
        (c.contact_user.username || '').toLowerCase().includes(contactFilter.toLowerCase())
    );

    return (
        <div className="flex h-screen bg-gray-900 text-white overflow-hidden relative">

            {/* Sidebar (Left) */}
            <div className={`bg-gray-800 flex flex-col border-r border-gray-700 transition-all duration-300 absolute md:relative z-20 h-full overflow-hidden
                ${sidebarOpen ? 'w-80 translate-x-0' : 'w-0 -translate-x-full md:w-0 md:translate-x-0'}
            `}>
                {/* Sidebar Header (User Info) */}
                <div className="p-4 bg-gray-800 border-b border-gray-700 flex items-center justify-between h-16 shrink-0">
                    <div className="flex items-center cursor-pointer" onClick={() => setShowProfileModal(true)}>
                        <div className="w-10 h-10 bg-gray-600 rounded-full mr-3 overflow-hidden shrink-0">
                            {user?.profile_picture ? <img src={user.profile_picture} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><FaUser /></div>}
                        </div>
                        <span className="font-bold truncate w-32">{user?.full_name || user?.username}</span>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => setShowCalls(false)} className={`p-2 rounded-full ${!showCalls ? 'bg-gray-700 text-green-500' : 'text-gray-400 hover:text-white'}`} title="Chats">
                            <FaPaperPlane size={16} />
                        </button>
                        <button onClick={() => { setShowCalls(true); fetchCalls(); }} className={`p-2 rounded-full ${showCalls ? 'bg-gray-700 text-green-500' : 'text-gray-400 hover:text-white'}`} title="Calls">
                            <FaPhone size={16} />
                        </button>
                    </div>
                </div>

                {/* Contact List */}
                {/* Contact List or Call History */}
                <div className="flex-1 overflow-y-auto w-80">
                    {!showCalls ? (
                        contacts.map(contact => (
                            <div
                                key={contact.id}
                                onClick={() => setActiveChat(contact)}
                                className={`p-4 flex items-center cursor-pointer hover:bg-gray-700 border-b border-gray-700/50 ${activeChat?.id === contact.id ? 'bg-gray-700' : ''}`}
                            >
                                <div className="w-12 h-12 bg-gray-600 rounded-full mr-3 overflow-hidden flex-shrink-0 relative">
                                    {contact.contact_user.profile_picture ?
                                        <img src={contact.contact_user.profile_picture} className="w-full h-full object-cover" /> :
                                        <div className="w-full h-full flex items-center justify-center"><FaUser /></div>
                                    }
                                </div>
                                <div className="overflow-hidden flex-1 ml-3">
                                    <div className="flex justify-between items-center">
                                        <h4 className="font-bold truncate">{contact.contact_user.full_name || contact.contact_user.username}</h4>
                                        {contact.unread_count > 0 && (
                                            <span className="bg-green-500 text-black text-xs font-bold px-2 py-0.5 rounded-full">{contact.unread_count}</span>
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-400 truncate">{contact.contact_user.about || "Hey there! I am using WhatsApp."}</p>
                                </div>
                            </div>
                        ))
                    ) : (
                        callHistory.map(call => (
                            <div key={call.id} className="p-4 flex items-center border-b border-gray-700/50 hover:bg-gray-700">
                                <div className="w-12 h-12 bg-gray-600 rounded-full mr-3 overflow-hidden flex-shrink-0">
                                    {call.other_user?.profile_picture ?
                                        <img src={call.other_user.profile_picture} className="w-full h-full object-cover" /> :
                                        <div className="w-full h-full flex items-center justify-center"><FaUser /></div>
                                    }
                                </div>
                                <div className="flex-1">
                                    <h4 className="font-bold">{call.other_user?.full_name || call.other_user?.username || "Unknown"}</h4>
                                    <div className="flex items-center text-sm text-gray-400">
                                        {call.type === 'incoming' ?
                                            (call.status === 'missed' ? <FaArrowLeft className="text-red-500 mr-1" /> : <FaArrowLeft className="text-green-500 mr-1" />) :
                                            <FaArrowLeft className="text-green-500 mr-1 rotate-180" />
                                        }
                                        <span>{call.status === 'missed' ? 'Missed' : 'Accepted'}</span>
                                        <span className="mx-1">•</span>
                                        <span>{new Date(call.start_time).toLocaleDateString()}</span>
                                    </div>
                                </div>
                                <button onClick={() => startChat(call.other_user)} className="text-green-500 p-2 hover:bg-gray-600 rounded-full">
                                    <FaVideo />
                                </button>
                            </div>
                        ))
                    )}
                    {showCalls && callHistory.length === 0 && (
                        <div className="p-8 text-center text-gray-500">No call history</div>
                    )}
                </div>

                {/* FAB (Existing Contacts) */}
                <button
                    onClick={() => setShowContactList(true)}
                    className="absolute bottom-20 right-6 bg-green-600 w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:bg-green-500 transition-transform hover:scale-110 z-30"
                >
                    <FaPlus size={24} />
                </button>
            </div>

            {/* Chat Area (Right) */}
            <div className="flex-1 flex flex-col bg-black/90 w-full relative">

                {/* Global Chat Header */}
                <div className="p-4 bg-gray-800 border-b border-gray-700 flex items-center justify-between h-16 shrink-0 z-10">
                    <div className="flex items-center">
                        {/* Hamburger Menu (Visible only on Home Page) */}
                        {!activeChat && (
                            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="mr-4 text-gray-400 hover:text-white">
                                <FaBars size={20} />
                            </button>
                        )}

                        {/* Back Button (Only in Active Chat) */}
                        {activeChat && (
                            <button onClick={() => setActiveChat(null)} className="mr-4 text-gray-400 hover:text-white">
                                <FaArrowLeft size={20} />
                            </button>
                        )}

                        {/* Active Chat Info */}
                        {activeChat && (
                            <div className="flex items-center cursor-pointer" onClick={() => setShowContactProfileModal(true)}>
                                <div className="w-10 h-10 bg-gray-600 rounded-full mr-3 overflow-hidden">
                                    {activeChat.contact_user.profile_picture ?
                                        <img src={activeChat.contact_user.profile_picture} className="w-full h-full object-cover" /> :
                                        <div className="w-full h-full flex items-center justify-center"><FaUser /></div>
                                    }
                                </div>
                                <div className="ml-4">
                                    <h2 className="text-xl font-bold">{activeChat.contact_user.full_name || activeChat.contact_user.username}</h2>
                                    <p className="text-sm text-gray-400">
                                        {activeChat.contact_user.is_online ? (
                                            <span className="text-green-400">Online</span>
                                        ) : (
                                            activeChat.contact_user.last_seen ?
                                                `Last seen ${new Date(activeChat.contact_user.last_seen).toLocaleString()}` :
                                                'Offline'
                                        )}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Header Icons & Menu */}
                    <div className="relative flex items-center" ref={menuRef}>
                        {/* Search Icon (Only on Home Page / No Active Chat) */}
                        {!activeChat && (
                            <button onClick={() => setShowGlobalSearch(true)} className="text-gray-400 hover:text-white p-2 mr-2">
                                <FaSearch />
                            </button>
                        )}

                        {/* Voice Call Icon (Only in Active Chat) */}
                        {activeChat && (
                            <button onClick={() => { setCallType('audio'); setIsVideoCallInitiator(true); }} className="text-gray-400 hover:text-white p-2 mr-2">
                                <FaPhone size={16} />
                            </button>
                        )}

                        {/* Video Call Icon (Only in Active Chat) */}
                        {activeChat && (
                            <button onClick={() => { setCallType('video'); setIsVideoCallInitiator(true); }} className="text-gray-400 hover:text-white p-2 mr-2">
                                <FaVideo size={18} />
                            </button>
                        )}

                        <button onClick={() => setShowMenu(!showMenu)} className="text-gray-400 hover:text-white p-2">
                            <FaEllipsisV />
                        </button>

                        {showMenu && (
                            <div className="absolute right-0 top-10 w-48 bg-gray-700 rounded shadow-xl z-50 py-2 border border-gray-600">
                                {activeChat ? (
                                    // Chat Window Menu Options
                                    <>
                                        <button onClick={() => { setShowContactProfileModal(true); setShowMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-600 flex items-center">
                                            <FaUser className="mr-2" /> Profile
                                        </button>
                                        <button onClick={() => { alert("Chat settings coming soon!"); setShowMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-600 flex items-center">
                                            <FaCog className="mr-2" /> Settings
                                        </button>
                                    </>
                                ) : (
                                    // Home Page Menu Options
                                    <>
                                        <button onClick={() => { setShowProfileModal(true); setShowMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-600 flex items-center">
                                            <FaUser className="mr-2" /> Profile
                                        </button>
                                        <button onClick={() => { alert("App settings coming soon!"); setShowMenu(false); }} className="w-full text-left px-4 py-2 hover:bg-gray-600 flex items-center">
                                            <FaCog className="mr-2" /> Settings
                                        </button>
                                        <div className="border-t border-gray-600 my-1"></div>
                                        <button onClick={logout} className="w-full text-left px-4 py-2 hover:bg-gray-600 flex items-center text-red-400">
                                            <FaSignOutAlt className="mr-2" /> Logout
                                        </button>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {activeChat ? (
                    <>
                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 pb-36 space-y-2 bg-[url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png')] bg-fixed">
                            {messages.map((msg, idx) => {
                                const isMe = msg.sender_username === user.username;
                                return (
                                    <div key={idx} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[70%] p-2 px-3 rounded-lg shadow ${isMe ? 'bg-green-700 rounded-tr-none' : 'bg-gray-700 rounded-tl-none'}`}>
                                            <p className="text-sm md:text-base">{msg.content}</p>
                                            <div className="flex items-center justify-end mt-1 space-x-1">
                                                <span className="text-[10px] text-gray-300">
                                                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                                {isMe && (
                                                    <span className={msg.read ? "text-blue-400" : "text-gray-400"}>
                                                        {msg.read ? <FaCheckDouble size={12} /> : <FaCheck size={12} />}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="absolute bottom-10 left-10 right-10 p-2 bg-gray-600/50 backdrop-blur-md flex items-center rounded-full shadow-2xl border border-gray-500/30 z-20">
                            <div className="relative">
                                <button
                                    className="text-gray-300 ml-2 mr-3 hover:text-white transition-colors emoji-trigger"
                                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                                >
                                    <FaSmile size={24} />
                                </button>
                                {showEmojiPicker && (
                                    <div className="absolute bottom-14 left-0 z-50 shadow-2xl rounded-xl overflow-hidden" ref={emojiPickerRef}>
                                        {/* <EmojiPicker onEmojiClick={onEmojiClick} theme="dark" width={300} height={400} /> */}
                                        <div className="bg-gray-800 p-4 text-white">Emoji Picker Loading...</div>
                                    </div>
                                )}
                            </div>
                            <input
                                className="flex-1 bg-transparent p-3 outline-none text-white placeholder-gray-300 font-medium"
                                placeholder="Type a message..."
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyPress={e => e.key === 'Enter' && sendMessage()}
                            />
                            <button onClick={sendMessage} className="mr-2 ml-3 bg-green-600 p-3 rounded-full text-white hover:bg-green-500 shadow-lg transition-transform transform hover:scale-110">
                                <FaPaperPlane size={18} />
                            </button>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500 bg-gray-900 border-b-8 border-green-500">
                        <h1 className="text-3xl font-light mb-4 text-gray-300">WhatsApp Web</h1>
                        <p>Send and receive messages without keeping your phone online.</p>
                    </div>
                )}
            </div>

            {/* Global Search Modal */}
            {showGlobalSearch && (
                <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 w-full max-w-md rounded-lg shadow-2xl overflow-hidden">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-green-700">
                            <h3 className="font-bold text-lg">Global Search</h3>
                            <button onClick={() => setShowGlobalSearch(false)}><FaTimes /></button>
                        </div>
                        <div className="p-4">
                            <form onSubmit={handleGlobalSearch} className="flex mb-4">
                                <input
                                    className="flex-1 bg-gray-700 p-2 rounded-l outline-none"
                                    placeholder="Search database..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    autoFocus
                                />
                                <button className="bg-green-600 px-4 rounded-r hover:bg-green-500"><FaSearch /></button>
                            </form>

                            <div className="max-h-60 overflow-y-auto">
                                {searchResults.length === 0 && searchQuery && <p className="text-center text-gray-500">No users found</p>}
                                {searchResults.map(u => (
                                    <div key={u.id} onClick={() => startChat(u)} className="flex items-center p-3 hover:bg-gray-700 cursor-pointer rounded">
                                        <div className="w-10 h-10 bg-gray-600 rounded-full mr-3 overflow-hidden">
                                            {u.profile_picture ? <img src={u.profile_picture} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><FaUser /></div>}
                                        </div>
                                        <div>
                                            <p className="font-bold">{u.full_name || u.username}</p>
                                            <p className="text-xs text-gray-400">@{u.username}</p>
                                            <p className="text-xs text-gray-500 italic">{u.about || "Hey there! I am using WhatsApp."}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Contact List Modal (Existing Contacts) */}
            {showContactList && (
                <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 w-full max-w-md rounded-lg shadow-2xl overflow-hidden">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-green-700">
                            <h3 className="font-bold text-lg">Select Contact</h3>
                            <button onClick={() => setShowContactList(false)}><FaTimes /></button>
                        </div>
                        <div className="p-4">
                            <input
                                className="w-full bg-gray-700 p-2 rounded outline-none mb-4"
                                placeholder="Filter contacts..."
                                value={contactFilter}
                                onChange={e => setContactFilter(e.target.value)}
                                autoFocus
                            />

                            <div className="max-h-60 overflow-y-auto">
                                {filteredContacts.length === 0 && <p className="text-center text-gray-500">No contacts found</p>}
                                {filteredContacts.map(c => (
                                    <div key={c.id} onClick={() => startChat(c.contact_user)} className="flex items-center p-3 hover:bg-gray-700 cursor-pointer rounded">
                                        <div className="w-10 h-10 bg-gray-600 rounded-full mr-3 overflow-hidden">
                                            {c.contact_user.profile_picture ? <img src={c.contact_user.profile_picture} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><FaUser /></div>}
                                        </div>
                                        <div>
                                            <p className="font-bold">{c.contact_user.full_name || c.contact_user.username}</p>
                                            <p className="text-xs text-gray-400">@{c.contact_user.username}</p>
                                            <p className="text-xs text-gray-500 italic truncate w-48">{c.contact_user.about || "Hey there! I am using WhatsApp."}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* User Profile Modal (Edit My Profile) */}
            {showProfileModal && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 w-full max-w-md rounded-lg shadow-2xl overflow-hidden animate-fade-in-up">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-green-700">
                            <h3 className="font-bold text-lg">My Profile</h3>
                            <button onClick={() => setShowProfileModal(false)}><FaTimes /></button>
                        </div>
                        <div className="p-6 flex flex-col items-center">
                            <div className="relative w-32 h-32 mb-6 group">
                                <div className="w-full h-full rounded-full overflow-hidden border-4 border-gray-700">
                                    {profileData.profile_picture ?
                                        <img src={profileData.profile_picture} className="w-full h-full object-cover" /> :
                                        <div className="w-full h-full bg-gray-600 flex items-center justify-center"><FaUser size={40} /></div>
                                    }
                                </div>
                                <label className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer rounded-full">
                                    <FaCamera size={24} />
                                    <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
                                </label>
                            </div>

                            <div className="w-full space-y-4">
                                <div>
                                    <label className="text-green-500 text-sm font-bold">Your Name</label>
                                    <input
                                        className="w-full bg-gray-700 p-2 rounded mt-1 outline-none focus:border-green-500 border border-transparent"
                                        value={profileData.full_name}
                                        onChange={e => setProfileData({ ...profileData, full_name: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="text-green-500 text-sm font-bold">About</label>
                                    <input
                                        className="w-full bg-gray-700 p-2 rounded mt-1 outline-none focus:border-green-500 border border-transparent"
                                        value={profileData.about}
                                        onChange={e => setProfileData({ ...profileData, about: e.target.value })}
                                    />
                                </div>
                                <button onClick={saveProfile} className="w-full bg-green-600 py-2 rounded font-bold hover:bg-green-500 mt-4">
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Contact Profile Modal (View Contact Info) */}
            {showContactProfileModal && activeChat && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 w-full max-w-md rounded-lg shadow-2xl overflow-hidden animate-fade-in-up">
                        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-green-700">
                            <h3 className="font-bold text-lg">Contact Info</h3>
                            <button onClick={() => setShowContactProfileModal(false)}><FaTimes /></button>
                        </div>
                        <div className="p-6 flex flex-col items-center">
                            <div className="w-32 h-32 mb-6 rounded-full overflow-hidden border-4 border-gray-700">
                                {activeChat.contact_user.profile_picture ?
                                    <img src={activeChat.contact_user.profile_picture} className="w-full h-full object-cover" /> :
                                    <div className="w-full h-full bg-gray-600 flex items-center justify-center"><FaUser size={40} /></div>
                                }
                            </div>

                            <div className="w-full space-y-4 text-center">
                                <div>
                                    <h2 className="text-2xl font-bold">{activeChat.contact_user.full_name || activeChat.contact_user.username}</h2>
                                    <p className="text-gray-400">@{activeChat.contact_user.username}</p>
                                </div>
                                <div className="bg-gray-700 p-4 rounded-lg text-left">
                                    <label className="text-green-500 text-sm font-bold block mb-1">About</label>
                                    <p className="text-gray-200">{activeChat.contact_user.about || "Hey there! I am using WhatsApp."}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Video Call Component */}
            {socket && (
                <VideoCall
                    socket={socket}
                    user={user}
                    activeChat={activeChat}
                    isInitiator={isVideoCallInitiator}
                    callType={callType}
                    onClose={() => setIsVideoCallInitiator(false)}
                />
            )}
        </div>
    );
};
