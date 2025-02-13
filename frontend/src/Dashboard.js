import React, { useState, useEffect } from "react";
import { fetchCSV } from "./api";
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

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend
);

const styles = {
  container: {
    padding: "20px",
    maxWidth: "1200px",
    margin: "0 auto",
    fontFamily: "Arial, sans-serif",
    backgroundColor: "#f4f7fc",
    borderRadius: "10px",
  },
  header: {
    fontSize: "26px",
    color: "#222",
    marginBottom: "20px",
    fontWeight: "bold",
    textAlign: "center",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: "12px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.15)",
    padding: "20px",
    marginBottom: "20px",
    transition: "transform 0.2s ease-in-out",
  },
  chartContainer: {
    width: "100%",
    height: "400px",
    position: "relative",
    borderRadius: "10px",
    overflow: "hidden",
  },
  tableContainer: {
    overflowX: "auto",
    borderRadius: "10px",
    boxShadow: "0 2px 6px rgba(0, 0, 0, 0.1)",
    backgroundColor: "#fff",
    padding: "10px",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: "10px",
  },
  th: {
    backgroundColor: "#007BFF",
    color: "#fff",
    padding: "14px",
    textAlign: "left",
    borderBottom: "3px solid #0056b3",
    fontWeight: "bold",
  },
  td: {
    padding: "12px",
    borderBottom: "1px solid #ddd",
    color: "#333",
  },
  tr: {
    transition: "background-color 0.2s ease",
  },
  trHover: {
    backgroundColor: "#f5faff",
  },
  statusIndicatorContainer: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "15px",
    color: "#555",
    marginBottom: "20px",
  },
  statusIndicator: {
    display: "inline-block",
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    transition: "background-color 0.3s ease-in-out",
  },
  connected: {
    backgroundColor: "#4CAF50",
  },
  disconnected: {
    backgroundColor: "#f44336",
  },
  connecting: {
    backgroundColor: "#FFC107",
  },
};

const Dashboard = () => {
  const [data, setData] = useState([]);
  const [headers, setHeaders] = useState([]);
  const [chartData, setChartData] = useState({ labels: [], values: [] });
  const [wsStatus, setWsStatus] = useState("connecting");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetchCSV();
        if (response.length > 0) {
          setHeaders(Object.keys(response[0]));
        }
        setData(response);
      } catch (error) {
        console.error("Failed to load CSV data:", error);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    let ws;
    let reconnectInterval = null;

    const connectWebSocket = () => {
      ws = new WebSocket("ws://localhost:8000/ws");

      ws.onopen = () => {
        setWsStatus("connected");
        if (reconnectInterval) clearInterval(reconnectInterval);
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setChartData((prev) => ({
          labels: [...prev.labels, message.timestamp].slice(-10),
          values: [...prev.values, message.value].slice(-10),
        }));
      };

      ws.onclose = () => {
        setWsStatus("disconnected");
        reconnectInterval = setInterval(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setWsStatus("error");
        ws.close();
      };
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectInterval) clearInterval(reconnectInterval);
    };
  }, []);

  const getStatusIndicatorStyle = (status) => {
    switch (status) {
      case "connected":
        return { ...styles.statusIndicator, ...styles.connected };
      case "disconnected":
        return { ...styles.statusIndicator, ...styles.disconnected };
      default:
        return { ...styles.statusIndicator, ...styles.connecting };
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Dashboard</h1>

      <div style={styles.card}>
        <div style={styles.statusIndicatorContainer}>
          <span style={getStatusIndicatorStyle(wsStatus)}></span>
           Status: {wsStatus}
        </div>

        <div style={styles.chartContainer}>
          <Line
            data={{
              labels: chartData.labels,
              datasets: [
                {
                  label: "Live Data Stream",
                  data: chartData.values,
                  borderColor: "#007BFF",
                  borderWidth: 2,
                  fill: false,
                  tension: 0.3,
                  pointRadius: 3,
                  pointBackgroundColor: "#007BFF",
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: { title: { display: true, text: "Timestamp" } },
                y: { title: { display: true, text: "Value" } },
              },
            }}
          />
        </div>
      </div>

      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr>
              {headers.map((header, index) => (
                <th key={index} style={styles.th}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={index}
                style={{
                  ...styles.tr,
                  ":hover": styles.trHover,
                }}
              >
                {headers.map((header, i) => (
                  <td key={i} style={styles.td}>
                    {row[header]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
