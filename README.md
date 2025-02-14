# Full Stack Application

A real-time data management application with React frontend and FastAPI backend.

## Project Structure
```
full-stack-application/
├── frontend/           # React frontend application
│   ├── src/           # Source files
│   ├── public/        # Public assets
│   └── package.json   # Frontend dependencies
│
├── backend/           # FastAPI backend application
│   ├── app/          # Application files
│   └── requirements.txt # Backend dependencies
│
└── README.md         # This file
```

## Prerequisites

Before you begin, ensure you have the following installed:
- Node.js (v14 or higher)
- Python (v3.7 or higher)
- pip (Python package manager)
- npm (Node package manager)

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a Python virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

### Backend Dependencies
- fastapi==0.68.0
- uvicorn==0.15.0
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- aiofiles
- pandas
- python-dotenv
- websockets
- filelock
- sqlite3

### Running the Backend
Development mode:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The backend API will be available at: http://localhost:8000
API documentation will be available at: http://localhost:8000/docs

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install frontend dependencies:
```bash
npm install
```

### Frontend Dependencies
- react (v18)
- react-dom
- react-router-dom
- axios
- chart.js
- react-chartjs-2
- @emotion/styled
- @emotion/react

### Running the Frontend
Development mode:
```bash
npm start
```

Production build:
```bash
npm run build
```

The frontend application will be available at: http://localhost:3000

## Development Features

### Backend Features
- FastAPI REST API
- WebSocket real-time updates
- JWT authentication
- SQLite database
- File operations with CSV
- Row-level locking mechanism
- Automatic data backup

### Frontend Features
- React components
- Real-time data updates
- Chart visualization
- Responsive design
- Protected routes
- Authentication state management
- WebSocket connection management

## Environment Variables

### Backend (.env)
```env
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./backend.db
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/api/ws
```

## Default Credentials
```
Username: admin
Password: admin123
```

## Common Issues and Solutions

1. **Backend Connection Refused**
   - Ensure the backend server is running
   - Check if the port 8000 is available
   - Verify Python virtual environment is activated

2. **Frontend Network Error**
   - Verify backend URL in environment variables
   - Check if backend server is running
   - Clear browser cache and reload

3. **WebSocket Connection Failed**
   - Ensure backend WebSocket server is running
   - Check network connectivity
   - Verify WebSocket URL in environment variables

## Additional Commands

### Backend
```bash
# Generate requirements.txt
pip freeze > requirements.txt

# Run tests
pytest

# Format code
black .
```

### Frontend
```bash
# Run tests
npm test

# Run linter
npm run lint

# Format code
npm run format
```

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details 