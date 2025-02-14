import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const styles = `
.not-found-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #1a1a1a 0%, #2d3748 100%);
    padding: 2rem;
    text-align: center;
    color: #ffffff;
}

.not-found-title {
    font-size: 8rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(45deg, #60A5FA, #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.not-found-subtitle {
    font-size: 2rem;
    margin: 1rem 0 2rem;
    color: #e2e8f0;
}

.not-found-text {
    font-size: 1.1rem;
    color: #a0aec0;
    margin-bottom: 2rem;
    max-width: 600px;
}

.back-button {
    padding: 0.75rem 1.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
    background: linear-gradient(45deg, #60A5FA, #34D399);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
}

.back-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(52, 211, 153, 0.2);
}

.back-button:active {
    transform: translateY(0);
}

@media (max-width: 768px) {
    .not-found-title {
        font-size: 6rem;
    }
    
    .not-found-subtitle {
        font-size: 1.5rem;
    }
    
    .not-found-text {
        font-size: 1rem;
    }
}

@media (max-width: 480px) {
    .not-found-title {
        font-size: 4rem;
    }
    
    .not-found-subtitle {
        font-size: 1.25rem;
    }
}
`;

const NotFound = () => {
    const navigate = useNavigate();

    useEffect(() => {
        const styleElement = document.createElement('style');
        styleElement.innerHTML = styles;
        document.head.appendChild(styleElement);
        return () => {
            document.head.removeChild(styleElement);
        };
    }, []);

    return (
        <div className="not-found-container">
            <h1 className="not-found-title">404</h1>
            <h2 className="not-found-subtitle">Page Not Found</h2>
            <p className="not-found-text">
                Oops! The page you're looking for doesn't exist. You might have mistyped the address or the page may have moved.
            </p>
            <button onClick={() => navigate('/dashboard')} className="back-button">
                Back to Dashboard
            </button>
        </div>
    );
};

export default NotFound; 