# AI-Powered Personal Planning & Scheduling Agent

An intelligent task scheduling application that uses AI to analyze tasks, understand natural language descriptions, and automatically create optimal schedules in Google Calendar.

## 🌟 Features

- **AI-Powered Task Analysis**: Uses Mistral AI to extract task metadata from natural language descriptions
- **Intelligent Scheduling**: Automatically schedules tasks considering deadlines, priorities, working hours, and breaks
- **Google Calendar Integration**: Syncs schedules directly to your Google Calendar
- **Natural Language Input**: Describe tasks naturally (e.g., "Finish project report by Friday, high priority, 2 hours")
- **Smart Clarifications**: AI asks targeted questions when task details are unclear
- **Flexible Scheduling**: Respects user preferences for working hours, lunch breaks, and buffer time
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLite**: Lightweight database
- **Mistral AI**: AI-powered task analysis
- **Google OAuth 2.0**: Secure authentication
- **Google Calendar API**: Calendar integration

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Fast build tool
- **Axios**: HTTP client

### Deployment
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-container orchestration

## 📋 Prerequisites

Before you begin, ensure you have:

1. **Google Cloud Console Account**
   - Create OAuth 2.0 credentials
   - Enable Google Calendar API
   - Set authorized redirect URIs

2. **Mistral AI API Key**
   - Sign up at [Mistral AI](https://mistral.ai/)
   - Get your API key (free tier available)

3. **Development Tools**
   - Python 3.11+
   - Node.js 20+
   - Docker & Docker Compose (for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Sanjay24-05/ai-scheduler.git
cd ai-scheduler
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Application
SECRET_KEY=your-secret-key-here
CSRF_SECRET=your-csrf-secret-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Mistral AI
MISTRAL_API_KEY=your-mistral-api-key-here
```

### 3. Local Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
python app.py
```

Backend will be available at `http://localhost:8000`

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 4. Docker Deployment

For production deployment using Docker:

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Run in detached mode
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop containers
docker-compose -f docker/docker-compose.yml down
```

Application will be available at `http://localhost:8000`

## 📖 Usage Guide

### 1. Sign In

- Click "Sign in with Google" on the login page
- Authorize the application to access your Google Calendar

### 2. Create Tasks

- Click "+ Add Task" on the dashboard
- Enter task description (e.g., "Finish project report by Friday, 2 hours")
- Click "🤖 AI Analyze" to extract task metadata automatically
- Review and adjust the extracted information
- Click "Create Task"

### 3. Generate Schedule

- Once you have multiple tasks, click "Generate Schedule"
- The AI will create an optimal schedule considering:
  - Task priorities and deadlines
  - Your working hours
  - Break requirements
  - Lunch periods
  - Task dependencies

### 4. View Schedule

- Switch to the "Schedule" tab to see your generated schedule
- Tasks are grouped by day with time slots
- Each task shows AI reasoning for its scheduling

### 5. Sync to Google Calendar

- Navigate to the Calendar section
- Click "Sync to Calendar"
- Your scheduled tasks will appear in Google Calendar

## 🔧 Configuration

### User Preferences

Customize your scheduling preferences in the Settings page:

- **Working Hours**: Set your start and end times (default: 9 AM - 5 PM)
- **Lunch Time**: Configure lunch break time and duration
- **Break Frequency**: Set how often you want breaks (default: every 2 hours)
- **Break Duration**: Set break length (default: 15 minutes)
- **Buffer Time**: Time between tasks (default: 5 minutes)
- **Timezone**: Your local timezone

### API Rate Limits

Default rate limits (configurable in `.env`):
- AI API: 50 requests per hour per user
- General API: 1000 requests per hour per user

## 🏗️ Project Structure

```
scheduling-agent/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── database.py            # Database setup
│   ├── models/                # SQLAlchemy models
│   ├── services/              # Business logic
│   │   ├── ai_service.py      # Mistral AI integration
│   │   ├── auth_service.py    # Google OAuth
│   │   ├── calendar_service.py # Google Calendar API
│   │   └── scheduler.py       # Scheduling algorithm
│   ├── routes/                # API endpoints
│   └── utils/                 # Utilities
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   ├── hooks/             # Custom hooks
│   │   └── types/             # TypeScript types
│   └── package.json
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── README.md
```

## 🔒 Security Features

- **Google OAuth 2.0**: Secure authentication
- **CSRF Protection**: Token-based CSRF prevention
- **HTTP-Only Cookies**: Secure session management
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: Prevents API abuse
- **Security Headers**: HSTS, X-Frame-Options, etc.

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 📝 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Mistral AI](https://mistral.ai/) for AI capabilities
- [Google Calendar API](https://developers.google.com/calendar) for calendar integration
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [React](https://react.dev/) for the UI framework

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Built with ❤️ using AI and modern web technologies
