import React, { createContext, useState, useEffect } from 'react';
import api from '../api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkUser();
    }, []);

    const checkUser = async () => {
        console.log("AuthContext: Checking user...");
        // For session-based auth, we don't check for token. We just try to fetch the profile.
        try {
            // Add timeout to prevent infinite loading
            const res = await api.get('auth/profile', { timeout: 5000 });
            console.log("AuthContext: User found", res.data);
            setUser(res.data);
        } catch (err) {
            console.error("AuthContext: Check user failed", err.response || err);
            if (err.response && err.response.status === 401) {
                console.log("AuthContext: User not authenticated");
                localStorage.removeItem('token');
            }
            setUser(null);
        } finally {
            console.log("AuthContext: Loading set to false");
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        const res = await api.post('auth/login', { username, password });
        console.log("Login response:", res.data);
        // Session auth doesn't use tokens, but if we add JWT later, this is fine.
        if (res.data.access_token) {
            localStorage.setItem('token', res.data.access_token);
        }
        // Set user data
        setUser(res.data.user || res.data);
    };

    const register = async (username, password, full_name) => {
        await api.post('auth/register', { username, password, full_name });
    };

    const logout = async () => {
        try {
            await api.post('logout/');
        } catch (err) {
            console.error("Logout failed", err);
        }
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading, checkUser }}>
            {children}
        </AuthContext.Provider>
    );
};
