# Frontend Documentation

## Overview
The frontend is built using React, providing a modern, responsive interface for data management and real-time updates. It features authentication, real-time data synchronization, and a dynamic dashboard.

## Core Components

### 1. App Component (`App.js`)
- Root component of the application
- Implements routing logic
- Manages authentication context
- Protected route handling

Features:
- Route protection
- Authentication state management
- Navigation management

### 2. Authentication Context (`AuthContext.js`)
- Manages authentication state
- Handles JWT token management
- Provides authentication methods

Key Features:
- JWT token storage
- Login/logout functionality
- Authentication state persistence
- Axios interceptor configuration

Methods:
- login(username, password)
- logout()
- useAuth() hook

### 3. Dashboard Component (`Dashboard.js`)
The main interface for data management and visualization.

#### State Management
```javascript
const [data, setData] = useState([]);
const [chartData, setChartData] = useState({ labels: [], values: [] });
const [wsStatus, setWsStatus] = useState("connecting");
const [editIndex, setEditIndex] = useState(null);
const [editRow, setEditRow] = useState({});
const [lockedRows, setLockedRows] = useState({});
```

#### Features

1. **Real-time Data Visualization**
   - Line chart for random numbers
   - Real-time updates
   - Configurable data points limit
   - Responsive chart sizing

2. **WebSocket Connection**
   - Automatic connection management
   - Reconnection logic
   - Connection status indication
   - Ping/Pong mechanism

3. **Data Management**
   - CRUD operations for entries
   - Real-time updates
   - Optimistic updates
   - Error handling

4. **Row Locking System**
   - Visual lock indicators
   - Cooldown period display
   - Lock acquisition
   - Lock release

5. **Responsive Design**
   - Mobile-friendly layout
   - Adaptive table display
   - Responsive controls
   - Dynamic sizing

### 4. Login Component (`Login.js`)
- User authentication interface
- Form validation
- Error handling
- Responsive design

Features:
- Username/password validation
- Error message display
- Responsive layout
- Authentication state management

## Styling System

### Dashboard Styles
```css
/* Container Styles */
.dashboard-container {
    max-width: 1400px;
    background-color: #111827;
    color: #ffffff;
}

/* Component-specific styles */
.chart-container {
    height: 350px;
    background-color: #1F2937;
}

/* Responsive Design */
@media (max-width: 1024px) {
    /* Tablet layout */
}

@media (max-width: 768px) {
    /* Mobile layout */
}
```

### Theme Colors
- Primary: #60A5FA (Blue)
- Success: #34D399 (Green)
- Error: #F87171 (Red)
- Background: #111827 (Dark)
- Surface: #1F2937 (Dark Gray)

## API Integration

### Endpoints
- GET `/api/fetch_csv`: Fetch data
- POST `/api/add_csv`: Add entry
- PUT `/api/update_csv/{index}`: Update entry
- DELETE `/api/delete_csv/{index}`: Delete entry
- WebSocket: `ws://localhost:8000/api/ws`

### WebSocket Messages
1. **Incoming Messages**
   - lock_status: Row lock updates
   - csv_update: Data changes
   - random_number: Chart updates
   - ping: Connection health

2. **Outgoing Messages**
   - lock_row: Request row lock
   - unlock_row: Release lock
   - verify_lock: Verify lock state

## Error Handling
- API error handling
- WebSocket connection errors
- Data validation errors
- Authentication errors
- Lock acquisition failures

## State Management
- Local state for UI
- WebSocket state
- Authentication state
- Row lock state
- Edit state

## Performance Optimizations
- Debounced updates
- Optimistic UI updates
- Efficient re-rendering
- Connection management
- Chart optimization

## Security Features
- JWT token management
- Secure WebSocket connection
- Protected routes
- Input validation
- Error handling

## Setup and Configuration

### Prerequisites
- Node.js 14+
- npm or yarn
- Modern web browser

### Installation
1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   ```
4. Start development server:
   ```bash
   npm start
   ```

### Building for Production
```bash
npm run build
```

## Best Practices
- Component composition
- State management
- Error handling
- Performance optimization
- Responsive design
- Code organization

## Testing
- Component testing
- Integration testing
- WebSocket testing
- Error scenario testing
- Responsive design testing
