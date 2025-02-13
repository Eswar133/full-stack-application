import axios from "axios";

const API_URL = "http://localhost:8000";

// ✅ Use Basic Auth for login, Bearer for other requests
export const loginUser = async (username, password) => {
    try {
        const response = await axios.post(`${API_URL}/login`, {}, {
            auth: { username, password }  // ✅ Basic Auth
        });
        localStorage.setItem("token", response.data.token);
        return response.data;
    } catch (error) {
        throw error;
    }
};



// ✅ Fetch CSV API - Ensure token is included in Authorization header
export const fetchCSV = async () => {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No token found!");

    try {
        const response = await axios.get(`${API_URL}/fetch_csv`, {
            headers: { 
                Authorization: `Bearer ${token}`  // ✅ Use Bearer token
            }
        });
        return response.data;
    } catch (error) {
        console.error("Fetch CSV error:", error);
        throw error;
    }
};
