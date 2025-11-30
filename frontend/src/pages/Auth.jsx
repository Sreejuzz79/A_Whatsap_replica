import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const { login } = useContext(AuthContext);
    const navigate = useNavigate();
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await login(username, password);
            navigate('/');
        } catch (err) {
            setError('Invalid credentials');
        }
    };

    return (
        <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
            <div className="bg-gray-800 p-8 rounded shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
                {error && <p className="text-red-500 mb-4">{error}</p>}
                <form onSubmit={handleSubmit}>
                    <input className="w-full p-2 mb-4 bg-gray-700 rounded" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
                    <input className="w-full p-2 mb-6 bg-gray-700 rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
                    <button className="w-full bg-green-600 p-2 rounded hover:bg-green-500">Login</button>
                </form>
                <p className="mt-4 text-center text-gray-400">
                    Don't have an account? <Link to="/register" className="text-green-500">Register</Link>
                </p>
            </div>
        </div>
    );
};

export const Register = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const { register } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await register(username, password, fullName);
            alert('Registration successful! Please login.');
            navigate('/login');
        } catch (err) {
            console.error("Registration Error:", err);
            if (err.response) {
                console.error("Server Response:", err.response.data);
                alert(`Registration failed: ${JSON.stringify(err.response.data)}`);
            } else {
                alert('Registration failed: Network Error or Server Unreachable');
            }
        }
    };

    return (
        <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
            <div className="bg-gray-800 p-8 rounded shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center">Register</h2>
                <form onSubmit={handleSubmit}>
                    <input className="w-full p-2 mb-4 bg-gray-700 rounded" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
                    <input className="w-full p-2 mb-4 bg-gray-700 rounded" placeholder="Full Name" value={fullName} onChange={e => setFullName(e.target.value)} />
                    <input className="w-full p-2 mb-6 bg-gray-700 rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
                    <button className="w-full bg-green-600 p-2 rounded hover:bg-green-500">Register</button>
                </form>
                <p className="mt-4 text-center text-gray-400">
                    Already have an account? <Link to="/login" className="text-green-500">Login</Link>
                </p>
            </div>
        </div>
    );
};
