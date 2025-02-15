import React, { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { useAuth } from "./AuthContext";  // Assuming you have an auth context
import { useNavigate } from "react-router-dom";

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend);

// Use environment variables instead of hardcoded URLs
const API_URL = process.env.REACT_APP_API_URL;
const WS_URL = process.env.REACT_APP_WS_URL;

// Create a CSS file named Dashboard.css
const styles = `
.dashboard-container {
    padding: 1.5rem;
    max-width: 1400px;
    margin: 0 auto;
    background-color: #111827;
    color: #ffffff;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dashboard-title {
    font-size: 1.875rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
    letter-spacing: -0.025em;
    background: linear-gradient(45deg, #60A5FA, #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.status-indicator {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.status-connected {
    background-color: rgba(16, 185, 129, 0.1);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.2);
}

.status-disconnected {
    background-color: rgba(239, 68, 68, 0.1);
    color: #F87171;
    border: 1px solid rgba(248, 113, 113, 0.2);
}

.error-message {
    background-color: rgba(239, 68, 68, 0.1);
    color: #F87171;
    padding: 1rem;
    border-radius: 0.75rem;
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
    border: 1px solid rgba(248, 113, 113, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
}

.chart-container {
    background-color: #1F2937;
    padding: 1.5rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    height: 350px;
}

.data-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background-color: #1F2937;
    border-radius: 1rem;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.data-table th {
    background-color: #374151;
    color: #fff;
    padding: 1rem;
    text-align: left;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    text-transform: uppercase;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.data-table td {
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.875rem;
    color: #D1D5DB;
    transition: all 0.2s ease;
}

.data-table tr:hover td {
    background-color: rgba(255, 255, 255, 0.05);
}

.data-input {
    width: 100%;
    padding: 0.75rem;
    background-color: #374151;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: #fff;
    font-size: 0.875rem;
    transition: all 0.2s ease;
}

.data-input:focus {
    outline: none;
    border-color: #60A5FA;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
}

.data-input:hover {
    border-color: rgba(255, 255, 255, 0.2);
}

.action-button {
    padding: 0.5rem 1rem;
    margin-left: 0.5rem;
    background-color: #374151;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.5rem;
    color: #fff;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 80px;
}

.action-button:hover:not(:disabled) {
    background-color: #4B5563;
    transform: translateY(-1px);
}

.action-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background-color: #374151;
}

.save-button {
    background-color: #059669;
    border-color: #34D399;
}

.save-button:hover:not(:disabled) {
    background-color: #047857;
}

.delete-button {
    background-color: #DC2626;
    border-color: #F87171;
}

.delete-button:hover:not(:disabled) {
    background-color: #B91C1C;
}

.add-button {
    background: linear-gradient(45deg, #60A5FA, #34D399);
    color: #fff;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 600;
    transition: all 0.2s ease;
    margin-bottom: 1.5rem;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.add-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 8px -1px rgba(0, 0, 0, 0.15), 0 3px 6px -1px rgba(0, 0, 0, 0.1);
}

.locked-row {
    background-color: rgba(239, 68, 68, 0.05);
}

.cell-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
}

.lock-indicator {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.editing-row {
    background-color: rgba(16, 185, 129, 0.05);
}

.editing-row .lock-indicator {
    background-color: rgba(16, 185, 129, 0.1);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.2);
}

.cooldown-row {
    background-color: rgba(245, 158, 11, 0.05);
}

.cooldown-row .lock-indicator {
    background-color: rgba(245, 158, 11, 0.1);
    color: #FBBF24;
    border: 1px solid rgba(251, 191, 36, 0.2);
}

.header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.logout-button {
    background: linear-gradient(45deg, #EF4444, #DC2626);
    color: #ffffff;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.logout-button:hover {
    transform: translateY(-1px);
    background: linear-gradient(45deg, #DC2626, #B91C1C);
    box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);
}

.logout-button:active {
    transform: translateY(0);
}

.username-display {
    color: #9CA3AF;
    font-size: 0.875rem;
    font-weight: 500;
}

@media (max-width: 1024px) {
    .dashboard-container {
        padding: 1rem;
    }
    
    .chart-container {
        height: 300px;
    }
    
    .data-table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }
}

@media (max-width: 768px) {
    .dashboard-header {
        flex-direction: column;
        gap: 1rem;
        text-align: center;
    }
    
    .chart-container {
        height: 250px;
        padding: 1rem;
    }
    
    .action-button {
        padding: 0.375rem 0.75rem;
        min-width: 70px;
    }
    
    .header-right {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .logout-button {
        padding: 0.375rem 0.75rem;
        font-size: 0.75rem;
    }
}

@media (max-width: 640px) {
    .dashboard-title {
        font-size: 1.5rem;
    }
    
    .data-table th,
    .data-table td {
        padding: 0.75rem 0.5rem;
        font-size: 0.75rem;
    }
    
    .action-button {
        margin-left: 0.25rem;
        font-size: 0.75rem;
        min-width: 60px;
    }
}

.loading-message {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
    font-size: 1rem;
    color: #D1D5DB;
    background-color: #1F2937;
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
`;

const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const wsRef = useRef(null);
    const [data, setData] = useState([]);
    const [headers] = useState([
        "user", "broker", "API key", "API secret", "pnl", "margin", "max_risk"
    ]);
    const [chartData, setChartData] = useState({
        labels: [],
        values: []
    });
    const [wsStatus, setWsStatus] = useState("connecting");
    const [editIndex, setEditIndex] = useState(null);
    const [editRow, setEditRow] = useState({});
    const [lockedRows, setLockedRows] = useState({});
    const lockedRowsRef = useRef(lockedRows);
    const [errorMessage, setErrorMessage] = useState("");
    const [isAddingNew, setIsAddingNew] = useState(false);
    const [newRow, setNewRow] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const MAX_DATA_POINTS = 50; // Maximum number of points to show on chart

    // Create style element
    useEffect(() => {
        const styleElement = document.createElement('style');
        styleElement.innerHTML = styles;
        document.head.appendChild(styleElement);
        return () => {
            document.head.removeChild(styleElement);
        };
    }, []);

    // Fetch initial CSV data
    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                setErrorMessage("");
                const token = localStorage.getItem('token');
                
                if (!token) {
                    throw new Error("No authentication token found");
                }

                console.log("Fetching CSV data from:", `${API_URL}/fetch_csv`);
                console.log("Using token:", token);
                
                const response = await axios.get(`${API_URL}/fetch_csv`, {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log("CSV Response:", response.data);
                
                if (Array.isArray(response.data)) {
                    setData(response.data);
                    console.log("CSV data loaded successfully:", response.data.length, "rows");
                } else {
                    throw new Error("Invalid data format received");
                }
            } catch (error) {
                console.error("Failed to load CSV:", error);
                console.error("Error details:", {
                    message: error.message,
                    response: error.response?.data,
                    status: error.response?.status
                });
                setErrorMessage(
                    error.response?.data?.detail || 
                    error.message || 
                    "Failed to load data from server"
                );
            } finally {
                setIsLoading(false);
            }
        };

        if (user) {
            console.log("User authenticated, fetching CSV data...");
            fetchData();
        }
    }, [user]);

    // WebSocket connection
    useEffect(() => {
        if (!user?.username) return;

        let isMounted = true;
        let reconnectTimeout;
        let reconnectAttempts = 0;
        let pingInterval;
        const MAX_RECONNECT_ATTEMPTS = 10;
        const RECONNECT_DELAY = 2000;
        const PING_INTERVAL = 30000;
        let lastPingTime = Date.now();
        let pingTimeoutId;

        const checkConnection = () => {
            const now = Date.now();
            if (now - lastPingTime > PING_INTERVAL * 2) {
                console.log("No ping received, reconnecting...");
                if (wsRef.current) {
                    wsRef.current.close();
                }
            }
        };

        const connect = () => {
            try {
                console.log("Attempting WebSocket connection...");
                const ws = new WebSocket(`${WS_URL}?username=${encodeURIComponent(user.username)}`);
                wsRef.current = ws;

            ws.onopen = () => {
                    if (!isMounted) return;
                    console.log("WebSocket connected successfully");
                setWsStatus("connected");
                    setErrorMessage("");
                    reconnectAttempts = 0;
                    lastPingTime = Date.now();

                    // Start ping interval
                    pingInterval = setInterval(() => {
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({ type: "ping" }));
                            pingTimeoutId = setTimeout(checkConnection, PING_INTERVAL);
                        }
                    }, PING_INTERVAL);

                    // Request lock state verification after reconnection
                    if (editIndex !== null) {
                        console.log("Requesting lock verification after reconnection");
                        ws.send(JSON.stringify({
                            type: "verify_lock",
                            row_index: editIndex
                        }));
                    }
                };

                ws.onclose = (event) => {
                    if (!isMounted) return;
                    console.log("WebSocket closed:", event);
                    setWsStatus("disconnected");
                    wsRef.current = null;
                    clearInterval(pingInterval);
                    clearTimeout(pingTimeoutId);

                    // Don't clear edit state immediately on disconnect
                    // It will be restored if we reconnect within the grace period

                    if (event.code !== 1000) {
                        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                            reconnectAttempts++;
                            const delay = RECONNECT_DELAY * Math.min(reconnectAttempts, 5);
                            console.log(`Reconnecting in ${delay}ms... Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                            reconnectTimeout = setTimeout(connect, delay);
                        } else {
                            setErrorMessage("Connection lost. Please refresh the page to continue editing.");
                            // Clear edit state after max reconnection attempts
                            setEditIndex(null);
                            setEditRow({});
                        }
                    }
            };

            ws.onmessage = (event) => {
                    if (!isMounted) return;
                    try {
                const message = JSON.parse(event.data);
                        lastPingTime = Date.now();
                        
                        if (message.type === "ping") {
                            clearTimeout(pingTimeoutId);
                            return;
                        }

                        if (message.type === "lock_status") {
                            setLockedRows(prev => {
                                const newLocks = { ...prev };
                                if (message.locked_by) {
                                    newLocks[message.row_index] = {
                                        username: message.locked_by,
                                        status: message.status,
                                        expiresAt: new Date(message.expires_at),
                                        message: message.message || ''
                                    };
                                    
                                    // If this is our lock being restored after reconnection
                                    if (message.locked_by === user?.username && 
                                        message.status === 'editing' && 
                                        message.row_index === editIndex) {
                                        console.log("Lock restored after reconnection");
                                    }
                                    // If our lock was taken by someone else
                                    else if (message.row_index === editIndex && 
                                             message.locked_by !== user?.username) {
                                        setEditIndex(null);
                                        setEditRow({});
                                        setErrorMessage("Your lock was lost due to connection issues.");
                                    }
                                } else {
                                    delete newLocks[message.row_index];
                                    if (message.row_index === editIndex) {
                                        setEditIndex(null);
                                        setEditRow({});
                                    }
                                }
                                return newLocks;
                            });
                } else if (message.type === "csv_update") {
                            console.log("Received CSV update:", {
                                source: message.source,
                                currentUser: user?.username,
                                timestamp: message.timestamp,
                                rowCount: message.data?.length
                            });

                            // Skip if we're the source of the update
                            if (message.source === user?.username) {
                                console.log("Skipping update from self");
                                return;
                            }

                            // Handle updates from other users while preserving local edits
                            setData(prevData => {
                                const newData = [...message.data];
                                
                                // If we're currently editing, preserve our edits
                                if (editIndex !== null && editIndex < newData.length) {
                                    console.log("Preserving local edits for row", editIndex);
                                    newData[editIndex] = { ...editRow };
                                }
                                
                                return newData;
                            });

                            // Show notification about the update
                            if (message.source) {
                                setErrorMessage(`Data updated by ${message.source}`);
                                setTimeout(() => setErrorMessage(""), 3000);
                            }
                        } else if (message.type === "random_number") {
                            setChartData(prevData => {
                                const newLabels = prevData.labels.slice(-MAX_DATA_POINTS + 1)
                                    .concat([message.timestamp]);  // Now using IST formatted timestamp
                                const newValues = prevData.values.slice(-MAX_DATA_POINTS + 1)
                                    .concat([message.value]);
                                return { labels: newLabels, values: newValues };
                            });
                        }
                    } catch (error) {
                        console.error("Error processing WebSocket message:", error);
                    }
                };

                return ws;
            } catch (error) {
                console.error("Error creating WebSocket:", error);
                setErrorMessage("Failed to create WebSocket connection");
                return null;
            }
        };

        const ws = connect();

        return () => {
            console.log("Cleaning up WebSocket connection...");
            isMounted = false;
            clearTimeout(reconnectTimeout);
            clearInterval(pingInterval);
            clearTimeout(pingTimeoutId);
            
            if (wsRef.current) {
                wsRef.current.close(1000, "Component unmounting");
                wsRef.current = null;
            }
            if (ws) {
                ws.close(1000, "Component unmounting");
            }
        };
    }, [user?.username, editIndex]);

    useEffect(() => {
        lockedRowsRef.current = lockedRows;
    }, [lockedRows, editRow]);

    const unlockRow = useCallback((index) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            try {
                wsRef.current.send(JSON.stringify({
                    type: "unlock_row",
                    row_index: index
                }));
            } catch (error) {
                console.error('Error sending unlock message:', error);
                setErrorMessage('Failed to unlock row. Please try again.');
            }
        } else {
            setErrorMessage('WebSocket connection is not open. Please wait for reconnection.');
        }
    }, []);

    const handleAdd = () => {
        // Create empty row with default values
        const emptyRow = {
            user: "",
            broker: "",
            "API key": "",
            "API secret": "",
            pnl: 0,
            margin: 0,
            max_risk: 0
        };
        
        setNewRow(emptyRow);
        setIsAddingNew(true);
    };

    const handleSaveNew = async () => {
        try {
            setErrorMessage("");
            const formattedRow = {
                ...newRow,
                pnl: parseFloat(newRow.pnl) || 0,
                margin: parseFloat(newRow.margin) || 0,
                max_risk: parseFloat(newRow.max_risk) || 0
            };

            const response = await axios.post(`${API_URL}/add_csv`, formattedRow, {
                headers: { 
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                    'Content-Type': 'application/json'
                }
            });
            
            // Update the local data state with the new data
            if (response.data && response.data.data) {
                setData(response.data.data);
            }
            
            setNewRow(null);
            setIsAddingNew(false);
            setErrorMessage("");
            
            // Show success message
            setErrorMessage("Entry added successfully!");
            setTimeout(() => setErrorMessage(""), 3000);
            
        } catch (error) {
            const errorMsg = error.response?.data?.detail || "Failed to add new entry";
            setErrorMessage(errorMsg);
            console.error("Add Entry Error:", error);
        }
    };

    const handleCancelNew = () => {
        setNewRow(null);
        setIsAddingNew(false);
        setErrorMessage("");
    };

    const handleNewRowInputChange = (e, key) => {
        let value = e.target.value;
        
        // Validate numeric fields
        if (['pnl', 'margin', 'max_risk'].includes(key)) {
            if (isNaN(value) || value === "") {
                value = 0;
            }
            value = parseFloat(value);
        }
        
        setNewRow(prev => ({ 
            ...prev, 
            [key]: value 
        }));
    };

    const handleUpdate = async (index) => {
        try {
            setErrorMessage("");
            const response = await axios.put(`${API_URL}/update_csv/${index}`, editRow, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            
            // Update local state immediately
            setData(prevData => {
                const newData = [...prevData];
                newData[index] = { ...editRow };
                return newData;
            });
            
            setEditIndex(null);
            setEditRow({});
            setIsAddingNew(false);
            unlockRow(index);
            
            // The WebSocket will handle broadcasting the update to all clients
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || "Failed to update entry");
            console.error("Update Entry Error:", error);
        }
    };

    const handleDelete = async (index) => {
        try {
            setErrorMessage("");
            await axios.delete(`${API_URL}/delete_csv/${index}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            
            // Update local state immediately
            setData(prevData => prevData.filter((_, i) => i !== index));
            
            // The WebSocket will handle broadcasting the update to all clients
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || "Failed to delete entry");
            console.error("Delete Entry Error:", error);
        }
    };

    const startEditing = async (index, row) => {
        if (!user?.username) {
            setErrorMessage("Authentication required");
            return;
        }
    
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setErrorMessage("WebSocket connection is not ready. Please wait...");
            return;
        }
    
        try {
            console.log(`Requesting lock for row ${index}`);
            wsRef.current.send(JSON.stringify({
                type: "lock_row",
                row_index: index
            }));

            // Wait for lock confirmation with retries
            let attempts = 0;
            const maxAttempts = 3;
            const attemptLock = () => new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    cleanup();
                    reject(new Error("Lock request timed out"));
                }, 10000); // Increased timeout to 10 seconds

                const handler = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        if (message.type === "lock_confirmation" && message.row_index === index) {
                            cleanup();
                            resolve(true);
                        } else if (message.type === "lock_denied" && message.row_index === index) {
                            cleanup();
                            reject(new Error(message.message));
                        }
                    } catch (error) {
                        console.error("Error parsing message:", error);
                    }
                };

                const cleanup = () => {
                    clearTimeout(timeout);
                    wsRef.current?.removeEventListener('message', handler);
                };

                wsRef.current.addEventListener('message', handler);
            });

            while (attempts < maxAttempts) {
                try {
                    await attemptLock();
                    // Lock acquired successfully
                    setEditIndex(index);
                    setEditRow({ ...row });
                    setErrorMessage("");
                    return;
                } catch (error) {
                    attempts++;
                    if (attempts === maxAttempts) {
                        throw error;
                    }
                    console.log(`Lock attempt ${attempts} failed, retrying...`);
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second between retries
                }
            }
        } catch (error) {
            console.error("Failed to acquire lock:", error);
            setErrorMessage(error.message || "Failed to start editing. Please try again.");
            setEditIndex(null);
            setEditRow({});
        }
    };

    // Add WebSocket message handler
    useEffect(() => {
        const handleWebSocketMessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                
                if (message.type === "lock_status") {
                    setLockedRows(prev => {
                        const newLocks = { ...prev };
                        if (message.locked_by) {
                            const serverTime = new Date(message.expires_at);
                            newLocks[message.row_index] = {
                                username: message.locked_by,
                                status: message.status,
                                expiresAt: serverTime,
                                message: message.message || ''
                            };
                        } else {
                            delete newLocks[message.row_index];
                            if (message.row_index === editIndex) {
                                setEditIndex(null);
                                setEditRow({});
                            }
                        }
                        return newLocks;
                    });
                } else if (message.type === "lock_restored") {
                    // Handle lock restoration after reconnection
                    const serverTime = new Date(message.expires_at);
                    setLockedRows(prev => ({
                        ...prev,
                        [message.row_index]: {
                            username: user?.username,
                            status: 'editing',
                            expiresAt: serverTime,
                            message: message.message
                        }
                    }));
                    setErrorMessage("Your lock has been restored");
                    setTimeout(() => setErrorMessage(""), 3000);
                }
                
            } catch (error) {
                console.error("Error processing WebSocket message:", error);
            }
        };

        if (wsRef.current) {
            wsRef.current.addEventListener('message', handleWebSocketMessage);
        }

        return () => {
            if (wsRef.current) {
                wsRef.current.removeEventListener('message', handleWebSocketMessage);
            }
        };
    }, [wsRef.current, user?.username, editIndex]);

    const cancelEditing = (index) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: "unlock_row",
                row_index: index
            }));
        }
        setEditIndex(null);
        setEditRow({});
        setErrorMessage("");
    };

    const handleInputChange = (e, key) => {
        let value = e.target.value;
        // Auto-convert numeric fields
        if (['pnl', 'margin', 'max_risk'].includes(key)) {
            value = value === "" ? 0 : Number(value);
        }
        setEditRow(prev => ({ ...prev, [key]: value }));
    };

    // Monitor chart data updates
    useEffect(() => {
        console.log("Chart data updated:", {
            labels: chartData.labels.length,
            values: chartData.values.length,
            lastValue: chartData.values[chartData.values.length - 1]
        });
    }, [chartData]);

    // Add cooldown timer effect
    useEffect(() => {
        const interval = setInterval(() => {
            setLockedRows(prev => {
                const now = new Date();
                const updated = { ...prev };
                Object.keys(updated).forEach(index => {
                    if (now > new Date(updated[index].expiresAt)) {
                        delete updated[index];
                    }
                });
                return updated;
            });
        }, 1000);
        return () => clearInterval(interval);
    }, []);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <h1 className="dashboard-title">Dashboard</h1>
                <div className="header-right">
                    <span className="username-display">Welcome, {user?.username}</span>
                    <div className={`status-indicator status-${wsStatus}`}>
                        {wsStatus === "connected" ? "Connected" : "Disconnected"}
                    </div>
                    <button className="logout-button" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            </div>

            {errorMessage && (
                <div className="error-message">
                    {errorMessage}
                </div>
            )}

            {isLoading ? (
                <div className="loading-message">Loading data...</div>
            ) : (
                <>
            <div className="chart-container">
                <Line
                    data={{
                        labels: chartData.labels,
                        datasets: [{
                                    label: "Random Numbers",
                            data: chartData.values,
                                    borderColor: "#4ade80",
                                    backgroundColor: "rgba(74, 222, 128, 0.1)",
                            tension: 0.4,
                            fill: true,
                                    pointRadius: 0 // Hide points for smoother appearance
                                }]
                    }}
                    options={{
                        responsive: true,
                        maintainAspectRatio: false,
                                animation: false, // Disable animations completely
                                elements: {
                                    line: {
                                        borderWidth: 2,
                                        tension: 0.4
                                    }
                                },
                        plugins: {
                            legend: {
                                        display: true,
                                labels: {
                                            color: "#ffffff",
                                            font: {
                                                size: 14
                                            }
                                        }
                                    },
                                    title: {
                                        display: true,
                                        text: 'Real-time Random Numbers',
                                        color: "#ffffff",
                                        font: {
                                            size: 16,
                                            weight: 'bold'
                                        },
                                        padding: {
                                            bottom: 15
                                        }
                                    },
                                    tooltip: {
                                        mode: 'index',
                                        intersect: false,
                            }
                        },
                        scales: {
                            y: {
                                        beginAtZero: true,
                                        max: 100,
                                grid: {
                                            color: "#333",
                                            drawBorder: false
                                },
                                ticks: {
                                            color: "#ffffff",
                                            stepSize: 20,
                                            font: {
                                                size: 12
                                            }
                                }
                            },
                            x: {
                                grid: {
                                            display: false
                                        },
                                        ticks: {
                                            color: "#ffffff",
                                            maxRotation: 0,
                                            autoSkip: true,
                                            maxTicksLimit: 6,
                                            font: {
                                                size: 12
                                            }
                                        }
                                    }
                                },
                                interaction: {
                                    intersect: false,
                                    mode: 'nearest',
                                    axis: 'x'
                                },
                                transitions: {
                                    active: {
                                        animation: {
                                            duration: 0
                                }
                            }
                        }
                    }}
                />
            </div>

                    <button 
                        className="add-button" 
                        onClick={handleAdd}
                        disabled={isAddingNew || editIndex !== null}
                    >
                        Add New Entry
                    </button>

            <table className="data-table">
                <thead>
                    <tr>
                                {headers.map(header => (
                                    <th key={header}>{header}</th>
                        ))}
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                            {/* New Row Input Fields */}
                            {isAddingNew && (
                                <tr>
                                    {headers.map(header => (
                                        <td key={header}>
                                            <input
                                                type={['pnl', 'margin', 'max_risk'].includes(header) ? "number" : "text"}
                                                className="data-input"
                                                value={newRow[header] || ""}
                                                onChange={(e) => handleNewRowInputChange(e, header)}
                                                placeholder={['pnl', 'margin', 'max_risk'].includes(header) ? "0" : `Enter ${header}`}
                                            />
                                        </td>
                                    ))}
                                    <td>
                                        <button
                                            className="action-button save-button"
                                            onClick={handleSaveNew}
                                        >
                                            Save
                                        </button>
                                        <button
                                            className="action-button"
                                            onClick={handleCancelNew}
                                        >
                                            Cancel
                                        </button>
                                    </td>
                                </tr>
                            )}

                            {/* Existing Rows */}
                            {data.map((row, index) => {
                                const lockInfo = lockedRows[index];
                                const isLocked = lockInfo && new Date() < new Date(lockInfo.expiresAt);
                                const isCooldown = lockInfo?.status === 'cooldown';
                                const remainingTime = lockInfo 
                                    ? Math.ceil((new Date(lockInfo.expiresAt) - new Date()) / 1000)
                                    : 0;

                                return (
                                    <tr key={index} 
                                        className={isLocked ? (isCooldown ? "cooldown-row" : "editing-row") : ""}>
                                        {headers.map(header => (
                                <td key={header}>
                                    {editIndex === index ? (
                                        <input
                                                        type={['pnl', 'margin', 'max_risk'].includes(header) ? "number" : "text"}
                                            className="data-input"
                                                        value={editRow[header] || ""}
                                            onChange={(e) => handleInputChange(e, header)}
                                                        placeholder={['pnl', 'margin', 'max_risk'].includes(header) ? "0" : `Enter ${header}`}
                                        />
                                    ) : (
                                                    <div className="cell-content">
                                                        <span>{row[header]}</span>
                                                        {lockInfo && isLocked && (
                                                            <div className="lock-indicator">
                                                                {isCooldown 
                                                                    ? `Available in ${remainingTime}s`
                                                                    : `Being modified by ${lockInfo.username}`}
                                                            </div>
                                                        )}
                                                    </div>
                                    )}
                                </td>
                            ))}
                            <td>
                                {editIndex === index ? (
                                                <>
                                    <button 
                                        className="action-button save-button"
                                                        onClick={() => handleUpdate(index)}
                                    >
                                        Save
                                    </button>
                                                    <button
                                                        className="action-button"
                                                        onClick={() => cancelEditing(index)}
                                                    >
                                                        Cancel
                                                    </button>
                                                </>
                                ) : (
                                    <>
                                        <button 
                                            className="action-button"
                                            onClick={() => startEditing(index, row)}
                                                        disabled={isLocked}
                                        >
                                            Edit
                                        </button>
                                        <button 
                                            className="action-button delete-button"
                                            onClick={() => handleDelete(index)}
                                                        disabled={isLocked}
                                        >
                                            Delete
                                        </button>
                                    </>
                                )}
                            </td>
                        </tr>
                                );
                            })}
                </tbody>
            </table>
                </>
            )}
        </div>
    );
};

export default Dashboard;