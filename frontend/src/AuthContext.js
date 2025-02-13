import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        if (token && username) {
            setUser({ username, token });
            // Set default authorization header
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            setError(null);
            const response = await axios.post(`${API_URL}/login`, {
                username,
                password
            });

            const { access_token, username: user_name } = response.data;
            
            // Set the token in localStorage and axios defaults
            localStorage.setItem('token', access_token);
            localStorage.setItem('username', user_name);
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
            
            setUser({ username: user_name, token: access_token });
            return true;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 
                               error.response?.data?.message || 
                               'Login failed';
            setError(errorMessage);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        delete axios.defaults.headers.common['Authorization'];
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ 
            user, 
            login, 
            logout, 
            loading,
            error,
            setError 
        }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);