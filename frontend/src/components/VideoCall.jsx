import React, { useState, useEffect, useRef } from 'react';
import { FaPhone, FaPhoneSlash, FaMicrophone, FaMicrophoneSlash, FaVideo, FaVideoSlash } from 'react-icons/fa';
import api from '../api';

import ringtoneUrl from '../assets/ringtone.wav';

const ICE_SERVERS = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:global.stun.twilio.com:3478' }
    ]
};

const VideoCall = ({ socket, user, activeChat, onClose, isInitiator, callType = 'video' }) => {
    const [localStream, setLocalStream] = useState(null);
    const [remoteStream, setRemoteStream] = useState(null);
    const [isCalling, setIsCalling] = useState(false);
    const [callAccepted, setCallAccepted] = useState(false);
    const [incomingCall, setIncomingCall] = useState(null);
    const [micOn, setMicOn] = useState(true);
    const [cameraOn, setCameraOn] = useState(true);
    const [callId, setCallId] = useState(null);
    const [startTime, setStartTime] = useState(null);
    const [statusMessage, setStatusMessage] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    const localVideoRef = useRef();
    const remoteVideoRef = useRef();
    const peerConnection = useRef();

    useEffect(() => {
        if (!socket) return;

        const handleMessage = async (event) => {
            const data = JSON.parse(event.data);

            if (data.action === 'call_offer') {
                if (data.receiver_id === user.id) {
                    setIncomingCall(data);
                }
            } else if (data.action === 'call_answer') {
                if (data.receiver_id === user.id && peerConnection.current) {
                    await peerConnection.current.setRemoteDescription(new RTCSessionDescription(data.answer));
                    setCallAccepted(true);
                    setStatusMessage("");
                }
            } else if (data.action === 'ice_candidate') {
                if (data.receiver_id === user.id && peerConnection.current) {
                    try {
                        await peerConnection.current.addIceCandidate(new RTCIceCandidate(data.candidate));
                    } catch (e) {
                        console.error("Error adding received ice candidate", e);
                    }
                }
            } else if (data.action === 'call_end') {
                endCall(false); // Don't emit end call again
            }
        };

        socket.addEventListener('message', handleMessage);

        return () => {
            socket.removeEventListener('message', handleMessage);
        };
    }, [socket, user]);

    // Effect to start call if initiator
    useEffect(() => {
        if (isInitiator && !isCalling && !callAccepted && !incomingCall) {
            startCall();
        }
    }, [isInitiator]);

    // Initialize Peer Connection
    const createPeerConnection = () => {
        const pc = new RTCPeerConnection(ICE_SERVERS);

        pc.onicecandidate = (event) => {
            if (event.candidate && activeChat) {
                socket.send(JSON.stringify({
                    action: 'ice_candidate',
                    receiver_id: activeChat.contact_user.id,
                    candidate: event.candidate
                }));
            }
        };

        pc.ontrack = (event) => {
            setRemoteStream(event.streams[0]);
            if (remoteVideoRef.current) {
                remoteVideoRef.current.srcObject = event.streams[0];
            }
        };

        peerConnection.current = pc;
        return pc;
    };

    const startCall = async () => {
        setIsCalling(true);
        setStatusMessage("Initializing call...");
        setErrorMessage("");

        try {
            const pc = createPeerConnection();

            // 1. Get User Media first
            setStatusMessage("Requesting camera/microphone access...");
            const constraints = {
                video: callType === 'video',
                audio: true
            };
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            setLocalStream(stream);
            if (localVideoRef.current && callType === 'video') localVideoRef.current.srcObject = stream;

            stream.getTracks().forEach(track => pc.addTrack(track, stream));

            // 2. Create Call Log (Non-blocking)
            setStatusMessage("Connecting...");
            let callId = null;
            try {
                const res = await api.post('calls/', {
                    receiver_id: activeChat.contact_user.id,
                    status: 'missed'
                });
                callId = res.data.id;
                setCallId(callId);
            } catch (logErr) {
                console.error("Failed to create call log:", logErr);
            }

            // 3. Create Offer
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            // 4. Send Offer
            socket.send(JSON.stringify({
                action: 'call_offer',
                receiver_id: activeChat.contact_user.id,
                offer: offer,
                sender_name: user.full_name || user.username,
                call_id: callId,
                call_type: callType
            }));

            setStatusMessage("Calling...");

        } catch (err) {
            console.error("Error starting call:", err);
            setErrorMessage("Failed to start call: " + err.message);
            // endCall(); // Don't auto-close so user sees error
        }
    };

    const answerCall = async () => {
        const pc = createPeerConnection();
        setCallAccepted(true);
        setStartTime(new Date());
        setStatusMessage("Connecting...");

        try {
            // Update Call Log (if call_id was sent)
            if (incomingCall.call_id) {
                setCallId(incomingCall.call_id);
                await api.patch(`calls/${incomingCall.call_id}`, {
                    status: 'accepted'
                });
            }

            const constraints = {
                video: incomingCall.call_type === 'video',
                audio: true
            };
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            setLocalStream(stream);
            if (localVideoRef.current && incomingCall.call_type === 'video') localVideoRef.current.srcObject = stream;

            stream.getTracks().forEach(track => pc.addTrack(track, stream));

            await pc.setRemoteDescription(new RTCSessionDescription(incomingCall.offer));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);

            socket.send(JSON.stringify({
                action: 'call_answer',
                receiver_id: incomingCall.sender_id || activeChat?.contact_user?.id, // Fallback if sender_id missing
                answer: answer
            }));
            setStatusMessage("");
        } catch (err) {
            console.error("Error answering call:", err);
            setErrorMessage("Failed to answer call: " + err.message);
            // endCall();
        }
    };



    const audioRef = useRef(new Audio(ringtoneUrl));

    useEffect(() => {
        audioRef.current.loop = true;
        // Preload
        audioRef.current.load();
    }, []);

    useEffect(() => {
        const playAudio = async () => {
            try {
                if (isCalling && !callAccepted) {
                    console.log("Attempting to play ringtone...");
                    await audioRef.current.play();
                    console.log("Ringtone playing");
                } else {
                    console.log("Pausing ringtone");
                    audioRef.current.pause();
                    audioRef.current.currentTime = 0;
                }
            } catch (e) {
                console.error("Audio play failed:", e);
            }
        };
        playAudio();
    }, [isCalling, callAccepted]);

    const endCall = async (emit = true) => {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;

        if (emit && activeChat) {
            socket.send(JSON.stringify({
                action: 'call_end',
                receiver_id: activeChat.contact_user.id
            }));
        }

        // Update Call Log on End
        if (callId) {
            try {
                const status = callAccepted ? 'accepted' : 'missed';
                await api.patch(`calls/${callId}`, {
                    status: status,
                    end_time: new Date().toISOString()
                });
            } catch (e) {
                console.error("Error updating call log", e);
            }
        }

        if (peerConnection.current) {
            peerConnection.current.close();
            peerConnection.current = null;
        }

        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            setLocalStream(null);
        }

        setRemoteStream(null);
        setIsCalling(false);
        setCallAccepted(false);
        setIncomingCall(null);
        setErrorMessage("");
        setStatusMessage("");
        if (onClose) onClose();
    };

    const toggleMic = () => {
        if (localStream) {
            localStream.getAudioTracks().forEach(track => track.enabled = !micOn);
            setMicOn(!micOn);
        }
    };

    const toggleCamera = () => {
        if (localStream) {
            localStream.getVideoTracks().forEach(track => track.enabled = !cameraOn);
            setCameraOn(!cameraOn);
        }
    };

    const currentCallType = incomingCall ? incomingCall.call_type : callType;

    if (incomingCall && !callAccepted) {
        return (
            <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
                <div className="bg-gray-800 p-8 rounded-lg shadow-2xl text-center animate-bounce-in">
                    <div className="w-24 h-24 bg-gray-600 rounded-full mx-auto mb-4 overflow-hidden border-4 border-gray-700">
                        {/* Placeholder or sender image */}
                        {incomingCall.sender_picture ? (
                            <img src={incomingCall.sender_picture} className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-3xl">📞</div>
                        )}
                    </div>
                    <h3 className="text-2xl font-bold mb-2">{incomingCall.sender_name || "Unknown"}</h3>
                    <p className="text-gray-400 mb-6">Incoming {incomingCall.call_type === 'audio' ? 'Voice' : 'Video'} Call...</p>
                    <div className="flex gap-4 justify-center">
                        <button onClick={() => endCall(true)} className="bg-red-600 p-4 rounded-full hover:bg-red-700 transition-colors">
                            <FaPhoneSlash size={24} />
                        </button>
                        <button onClick={answerCall} className="bg-green-600 p-4 rounded-full hover:bg-green-700 transition-colors animate-pulse">
                            {incomingCall.call_type === 'audio' ? <FaPhone size={24} /> : <FaVideo size={24} />}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (!isCalling && !callAccepted && !errorMessage) return null;

    return (
        <div className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center">
            <div className="relative w-full max-w-4xl aspect-video bg-gray-900 rounded-lg overflow-hidden shadow-2xl flex items-center justify-center">

                {/* Main Content: Remote Video OR Avatar Layout */}
                {callAccepted && currentCallType === 'video' ? (
                    <video
                        ref={remoteVideoRef}
                        autoPlay
                        playsInline
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="flex flex-col items-center z-10">
                        <div className="w-32 h-32 bg-gray-600 rounded-full mb-4 flex items-center justify-center text-4xl overflow-hidden border-4 border-gray-700 shadow-lg">
                            {activeChat?.contact_user?.profile_picture ?
                                <img src={activeChat.contact_user.profile_picture} className="w-full h-full object-cover" /> :
                                (activeChat?.contact_user?.full_name?.[0] || activeChat?.contact_user?.username?.[0] || "U")
                            }
                        </div>

                        {/* Status Message (Calling...) - Between Avatar and Name */}
                        {!callAccepted && (
                            <div className="text-green-400 text-lg animate-pulse font-medium mb-2">
                                {statusMessage || "Calling..."}
                            </div>
                        )}

                        <h2 className="text-3xl font-bold text-white mb-2">{activeChat?.contact_user?.full_name || activeChat?.contact_user?.username}</h2>

                        {callAccepted && currentCallType === 'audio' && (
                            <p className="text-gray-400">Voice Call Connected</p>
                        )}
                    </div>
                )}

                {/* Local Video (PIP) - Only for video calls */}
                {currentCallType === 'video' && (
                    <div className="absolute bottom-4 right-4 w-48 aspect-video bg-black rounded-lg overflow-hidden border-2 border-gray-700 shadow-lg z-20">
                        <video
                            ref={localVideoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover"
                        />
                    </div>
                )}

                {/* Controls */}
                <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-4 bg-gray-800/80 backdrop-blur px-6 py-3 rounded-full z-30">
                    <button onClick={toggleMic} className={`p-4 rounded-full ${micOn ? 'bg-gray-600 hover:bg-gray-500' : 'bg-red-600 hover:bg-red-700'}`}>
                        {micOn ? <FaMicrophone /> : <FaMicrophoneSlash />}
                    </button>
                    <button onClick={() => endCall(true)} className="p-4 rounded-full bg-red-600 hover:bg-red-700">
                        <FaPhoneSlash size={24} />
                    </button>
                    {currentCallType === 'video' && (
                        <button onClick={toggleCamera} className={`p-4 rounded-full ${cameraOn ? 'bg-gray-600 hover:bg-gray-500' : 'bg-red-600 hover:bg-red-700'}`}>
                            {cameraOn ? <FaVideo /> : <FaVideoSlash />}
                        </button>
                    )}
                </div>

                {/* Error Overlay (Status removed as it's now inline) */}
                {errorMessage && (
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center z-40">
                        <div className="bg-red-600/80 p-4 rounded text-white">
                            <p className="font-bold">Error</p>
                            <p>{errorMessage}</p>
                            <button onClick={() => endCall(true)} className="mt-2 bg-white text-red-600 px-4 py-1 rounded font-bold">Close</button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default VideoCall;
