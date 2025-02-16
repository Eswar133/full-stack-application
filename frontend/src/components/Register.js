import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL;

const styles = `
.register-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d3748 100%);
    padding: 20px;
}

.register-form {
    background: rgba(36, 36, 36, 0.95);
    padding: 2.5rem;
    border-radius: 16px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.register-title {
    color: #ffffff;
    text-align: center;
    margin-bottom: 2rem;
    font-size: 2rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.form-group {
    margin-bottom: 1.5rem;
    text-align: center;
}

.form-label {
    display: block;
    color: #e2e8f0;
    margin-bottom: 0.75rem;
    font-size: 0.95rem;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.form-input {
    width: 100%;
    padding: 0.875rem 1rem;
    background-color: rgba(51, 51, 51, 0.8);
    border: 2px solid rgba(99, 99, 99, 0.2);
    border-radius: 8px;
    color: #ffffff;
    font-size: 1rem;
    transition: all 0.3s ease;
    text-align: center;
}

.form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    background-color: rgba(51, 51, 51, 0.95);
}

.form-input::placeholder {
    color: #9ca3af;
}

.register-button {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    margin-top: 1rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.register-button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.register-button:active {
    transform: translateY(0);
}

.error-message {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #ef4444;
    margin-top: 1rem;
    text-align: center;
    font-size: 0.875rem;
    padding: 0.75rem;
    border-radius: 8px;
    font-weight: 500;
}

.success-message {
    background-color: rgba(20, 184, 166, 0.1);
    border: 1px solid rgba(20, 184, 166, 0.2);
    color: #14b8a6;
    margin-top: 1rem;
    text-align: center;
    font-size: 0.875rem;
    padding: 0.75rem;
    border-radius: 8px;
    font-weight: 500;
}

.login-link {
    display: block;
    text-align: center;
    margin-top: 1.5rem;
    color: #60a5fa;
    text-decoration: none;
    font-size: 0.9rem;
    transition: color 0.3s ease;
}

.login-link:hover {
    color: #3b82f6;
}
`;

const Register = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        const styleElement = document.createElement("style");
        styleElement.innerHTML = styles;
        document.head.appendChild(styleElement);
        return () => {
            document.head.removeChild(styleElement);
        };
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        try {
            await axios.post(`${API_URL}/register`, {
                username,
                password
            });
            
            setSuccess("Registration successful! Redirecting to login...");
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (error) {
            setError(error.response?.data?.detail || "Registration failed");
        }
    };

    return (
        <div className="register-container">
            <form className="register-form" onSubmit={handleSubmit}>
                <h1 className="register-title">Sign Up</h1>
                
                <div className="form-group">
                    <label className="form-label" htmlFor="username">
                        Username
                    </label>
                    <input
                        id="username"
                        type="text"
                        className="form-input"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter username"
                        required
                    />
                </div>

                <div className="form-group">
                    <label className="form-label" htmlFor="password">
                        Password
                    </label>
                    <input
                        id="password"
                        type="password"
                        className="form-input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password"
                        required
                    />
                </div>

                <div className="form-group">
                    <label className="form-label" htmlFor="confirm-password">
                        Confirm Password
                    </label>
                    <input
                        id="confirm-password"
                        type="password"
                        className="form-input"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm password"
                        required
                    />
                </div>

                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">{success}</div>}

                <button type="submit" className="register-button">
                    Sign Up
                </button>

                <a href="/login" className="login-link">
                    Already have an account? Login
                </a>
            </form>
        </div>
    );
};

export default Register; 