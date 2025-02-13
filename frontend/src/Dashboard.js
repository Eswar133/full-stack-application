import React, { useState, useEffect, useCallback, useRef } from "react";
import { fetchCSV } from "./api";
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

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Legend);

const API_URL = "http://localhost:8000/api";  // Fixed API URL
const WS_URL = "ws://localhost:8000/api/ws";  // Fixed WebSocket URL

// Create a CSS file named Dashboard.css
const styles = `
.dashboard-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
    background-color: #1a1a1a;
    color: #ffffff;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 10px 0;
    border-bottom: 1px solid #333;
}

.dashboard-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0;
    color: #ffffff;
}

.status-indicator {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 14px;
    font-weight: 500;
}

.status-connected {
    background-color: #1b4332;
    color: #4ade80;
}

.status-disconnected {
    background-color: #442222;
    color: #ff4444;
}

.error-message {
    background-color: #442222;
    color: #ff4444;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    border: 1px solid #ff4444;
}

.chart-container {
    background-color: #242424;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    border: 1px solid #333;
    height: 300px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    background-color: #242424;
    border-radius: 8px;
    overflow: hidden;
}

.data-table th {
    background-color: #333;
    color: #fff;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
}

.data-table td {
    padding: 12px 16px;
    border-bottom: 1px solid #333;
    font-size: 14px;
    color: #e0e0e0;
}

.data-input {
    width: 100%;
    padding: 8px;
    background-color: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    font-size: 14px;
}

.action-button {
    padding: 6px 12px;
    margin-left: 8px;
    background-color: transparent;
    border: 1px solid #444;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    transition: all 0.2s ease;
}

.action-button:hover {
    background-color: #333;
}

.action-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.save-button {
    background-color: #1b4332;
    border-color: #4ade80;
}

.save-button:hover {
    background-color: #2d503f;
}

.delete-button {
    border-color: #dc2626;
}

.delete-button:hover {
    background-color: #502222;
}

.add-button {
    background-color: #2563eb;
    color: #fff;
    padding: 10px 20px;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    margin-bottom: 20px;
}

.add-button:hover {
    background-color: #1d4ed8;
}

.locked-row {
    background-color: rgba(220, 38, 38, 0.1);
}

.cell-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.lock-indicator {
    font-size: 12px;
    color: #dc2626;
    background-color: rgba(220, 38, 38, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 8px;
}
`;

const Dashboard = () => {
    const { user } = useAuth();
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

                const response = await axios.get(`${API_URL}/fetch_csv`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (Array.isArray(response.data)) {
                    setData(response.data);
                } else {
                    throw new Error("Invalid data format received");
                }
            } catch (error) {
                console.error("Failed to load CSV:", error);
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
        const MAX_RECONNECT_ATTEMPTS = 10; // Increased from 5 to 10
        const RECONNECT_DELAY = 2000; // Reduced from 3000 to 2000ms

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

                    // Start ping interval to keep connection alive
                    pingInterval = setInterval(() => {
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({ type: "ping" }));
                        }
                    }, 30000); // Send ping every 30 seconds
                };

                ws.onmessage = (event) => {
                    if (!isMounted) return;
                    try {
                        const message = JSON.parse(event.data);
                        
                        // Only log non-ping messages
                        if (message.type !== "ping") {
                            console.log("WebSocket message received:", message);
                        }

                        if (message.type === "lock_status") {
                            console.log("Lock status update:", message);
                            setLockedRows(prev => {
                                const newLocks = { ...prev };
                                if (message.locked_by) {
                                    newLocks[message.row_index] = message.locked_by;
                                } else {
                                    delete newLocks[message.row_index];
                                }
                                return newLocks;
                            });
                        } else if (message.type === "csv_update") {
                            console.log("CSV data update:", message.data);
                            setData(message.data);
                        } else if (message.type === "random_number") {
                            setChartData(prevData => {
                                // Create new arrays instead of spreading to avoid memory issues
                                const newLabels = prevData.labels.slice(-MAX_DATA_POINTS + 1).concat([new Date(message.timestamp).toLocaleTimeString()]);
                                const newValues = prevData.values.slice(-MAX_DATA_POINTS + 1).concat([message.value]);
                                
                                return {
                                    labels: newLabels,
                                    values: newValues
                                };
                            });
                        }
                    } catch (error) {
                        console.error("Error parsing WebSocket message:", error);
                    }
                };

                ws.onclose = (event) => {
                    if (!isMounted) return;
                    console.log("WebSocket closed:", event);
                    setWsStatus("disconnected");
                    wsRef.current = null;
                    clearInterval(pingInterval);

                    // Only attempt to reconnect if not manually closed
                    if (event.code !== 1000) {
                        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                            reconnectAttempts++;
                            console.log(`Reconnecting... Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                            reconnectTimeout = setTimeout(connect, RECONNECT_DELAY * Math.min(reconnectAttempts, 5));
                        } else {
                            setErrorMessage("Connection lost. Please refresh the page.");
                        }
                    }
                };

                ws.onerror = (error) => {
                    console.error("WebSocket error:", error);
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.close();
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
            
            if (wsRef.current) {
                wsRef.current.close(1000, "Component unmounting");
                wsRef.current = null;
            }
            if (ws) {
                ws.close(1000, "Component unmounting");
            }
        };
    }, [user?.username]);

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
            // ✅ Convert numeric fields to numbers
            const formattedRow = {
                ...newRow,
                pnl: parseFloat(newRow.pnl) || 0,
                margin: parseFloat(newRow.margin) || 0,
                max_risk: parseFloat(newRow.max_risk) || 0
            };
    
            await axios.post(`${API_URL}/add_csv`, formattedRow, {
                headers: { 
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                    'Content-Type': 'application/json'
                }
            });
            
            setNewRow(null);
            setIsAddingNew(false);
            setErrorMessage("");
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
            await axios.put(`${API_URL}/update_csv/${index}`, editRow, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            setEditIndex(null);
            setEditRow({});
            setIsAddingNew(false);
            unlockRow(index);
            setErrorMessage("");
        } catch (error) {
            setErrorMessage(error.response?.data?.detail || "Failed to update entry");
            console.error("Update Entry Error:", error);
        }
    };

    const handleDelete = async (index) => {
        try {
            await axios.delete(`${API_URL}/delete_csv/${index}`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
            });
            setErrorMessage("");
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
    
        if (lockedRows[index]) {
            setErrorMessage(`Row locked by ${lockedRows[index]}`);
            return;
        }
    
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            setErrorMessage("WebSocket connection is not ready. Please wait...");
            return;
        }
    
        try {
            // Explicit lock request
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => reject("Lock request timed out"), 2000);
                
                const handler = (event) => {
                    const msg = JSON.parse(event.data);
                    console.log("Lock response received:", msg);
                    
                    if (msg.type === "lock_status" && msg.row_index === index) {
                        clearTimeout(timeout);
                        wsRef.current.removeEventListener('message', handler);
                        if (msg.locked_by === user.username) {
                            resolve();
                        } else {
                            reject("Failed to acquire lock");
                        }
                    }
                };
    
                wsRef.current.addEventListener('message', handler);
                wsRef.current.send(JSON.stringify({
                    type: "lock_row",
                    row_index: index
                }));
            });
    
            setEditIndex(index);
            setEditRow({ ...row });
            setErrorMessage("");
        } catch (err) {
            console.error("Lock error:", err);
            setErrorMessage(typeof err === 'string' ? err : "Failed to lock row for editing");
            unlockRow(index);
        }
    };

    const cancelEditing = (index) => {
        setEditIndex(null);
        setEditRow({});
        setIsAddingNew(false);
        unlockRow(index);
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

    return (
        <div className="dashboard-container">
            <div className="dashboard-header">
                <h1 className="dashboard-title">Dashboard</h1>
                <div className={`status-indicator status-${wsStatus}`}>
                    {wsStatus === "connected" ? "Connected" : "Disconnected"}
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
                            {data.map((row, index) => (
                                <tr key={index} className={lockedRows[index] ? "locked-row" : ""}>
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
                                                    {lockedRows[index] && (
                                                        <span className="lock-indicator">
                                                            {lockedRows[index]}
                                                        </span>
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
                                                    disabled={lockedRows[index] && lockedRows[index] !== user.username}
                                                >
                                                    Edit
                                                </button>
                                                <button
                                                    className="action-button delete-button"
                                                    onClick={() => handleDelete(index)}
                                                    disabled={lockedRows[index] && lockedRows[index] !== user.username}
                                                >
                                                    Delete
                                                </button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
        </div>
    );
};

export default Dashboard;