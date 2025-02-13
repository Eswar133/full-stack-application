import React, { useState } from "react";
import { loginUser } from "../api";
import { useNavigate } from "react-router-dom";

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f4f7fc",
  },
  card: {
    backgroundColor: "#fff",
    padding: "30px",
    borderRadius: "10px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.15)",
    width: "350px",
    textAlign: "center",
  },
  header: {
    fontSize: "24px",
    fontWeight: "bold",
    marginBottom: "20px",
    color: "#333",
  },
  input: {
    width: "100%",
    padding: "12px",
    marginBottom: "15px",
    border: "1px solid #ccc",
    borderRadius: "6px",
    fontSize: "16px",
    outline: "none",
    transition: "border 0.3s ease",
  },
  inputFocus: {
    border: "1px solid #007BFF",
  },
  button: {
    width: "100%",
    padding: "12px",
    backgroundColor: "#007BFF",
    color: "#fff",
    border: "none",
    borderRadius: "6px",
    fontSize: "16px",
    cursor: "pointer",
    transition: "background 0.3s",
  },
  buttonDisabled: {
    backgroundColor: "#999",
    cursor: "not-allowed",
  },
  error: {
    color: "#ff3333",
    fontSize: "14px",
    marginTop: "10px",
  },
};

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await loginUser(username, password);
      localStorage.setItem("token", response.token);  // ✅ Store token
      navigate("/dashboard");
    } catch (error) {
      setError("Invalid username or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.header}>Login</h2>
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ ...styles.input }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ ...styles.input }}
          />
          <button
            type="submit"
            style={{ ...styles.button, ...(loading ? styles.buttonDisabled : {}) }}
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
        {error && <p style={styles.error}>{error}</p>}
      </div>
    </div>
  );
};

export default Login;
