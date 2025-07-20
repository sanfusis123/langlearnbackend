# Language Learning Platform - Backend

A comprehensive FastAPI backend for an AI-powered language learning platform, featuring real-time conversations, meeting analysis, and adaptive learning experiences.

## 🌟 Features

### Core Features
- **AI-Powered Conversations**: Real-time chat with intelligent language tutors
- **Meeting Analysis**: Analyze meeting transcriptions for language improvement
- **Adaptive Learning**: Personalized lessons based on user proficiency
- **Multi-Language Support**: Support for English, Hindi, French, Russian, and more
- **Voice Support**: WebSocket-based real-time communication
- **Progress Tracking**: Detailed analytics and learning streaks

### Technical Features
- **User Management**: JWT authentication, role-based access control
- **MongoDB Integration**: Using Beanie ODM for async database operations
- **LangChain Integration**: Advanced AI language processing
- **Token Usage Tracking**: Monitor and manage AI API usage
- **WebSocket Support**: Real-time bidirectional communication
- **Admin Dashboard**: User and content management

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- OpenAI API key (or other LLM provider)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi-chat-app
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
DATABASE_URL=mongodb://localhost:27017/language_learning
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# CORS Configuration
FRONTEND_URL=http://localhost:3000
```

5. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
fastapi-chat-app/
├── app/
│   ├── api/
│   │   ├── api_v1/
│   │   │   └── api.py          # API router configuration
│   │   ├── deps.py             # Dependencies (auth, etc.)
│   │   └── endpoints/          # API endpoints
│   │       ├── admin.py        # Admin endpoints
│   │       ├── auth.py         # Authentication
│   │       ├── chat.py         # Chat functionality
│   │       ├── learning.py     # Language learning endpoints
│   │       ├── tokens.py       # Token usage tracking
│   │       └── users.py        # User management
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   └── security.py         # Security utilities
│   ├── db/
│   │   └── database.py         # Database initialization
│   ├── llm/
│   │   ├── agents/
│   │   │   └── chat_agent.py   # LangChain chat agent
│   │   └── providers/
│   │       └── openai_provider.py
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── chat.py             # Chat models
│   │   ├── language_learning.py # Learning models
│   │   └── token_usage.py      # Token tracking models
│   ├── schemas/
│   │   ├── user.py             # User schemas
│   │   ├── chat.py             # Chat schemas
│   │   └── language_learning.py # Learning schemas
│   ├── services/
│   │   ├── language_learning.py # Learning service
│   │   └── token_usage.py      # Token tracking service
│   └── main.py                 # FastAPI application
├── requirements.txt
├── .env.example
└── README.md
```

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login (returns JWT token)

### Users
- `POST /api/v1/users/` - Register new user
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/{user_id}` - Update user profile
- `GET /api/v1/users/` - List all users (admin only)
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

### Language Learning
- `GET /api/v1/learning/languages` - Get available languages
- `GET /api/v1/learning/lessons` - Get lessons (with filters)
- `GET /api/v1/learning/lessons/{lesson_id}` - Get specific lesson
- `POST /api/v1/learning/lessons` - Create lesson
- `PUT /api/v1/learning/lessons/{lesson_id}` - Update lesson
- `DELETE /api/v1/learning/lessons/{lesson_id}` - Delete lesson
- `GET /api/v1/learning/progress/{language_code}` - Get user progress
- `GET /api/v1/learning/stats/dashboard` - Get dashboard statistics

### Conversations
- `POST /api/v1/chat/sessions` - Create chat session
- `GET /api/v1/chat/sessions` - Get user's sessions
- `GET /api/v1/chat/sessions/{session_id}` - Get session details
- `PUT /api/v1/chat/sessions/{session_id}` - Update session
- `DELETE /api/v1/chat/sessions/{session_id}` - Delete session
- `GET /api/v1/chat/sessions/{session_id}/messages` - Get messages
- `POST /api/v1/chat/chat` - Send message (streaming/non-streaming)
- `POST /api/v1/learning/conversation/analyze` - Analyze conversation

### Meeting Analysis
- `POST /api/v1/learning/meeting/analyze` - Analyze meeting transcription
- `GET /api/v1/learning/meeting/analyses` - Get past analyses
- `GET /api/v1/learning/meeting/analyses/{analysis_id}` - Get analysis details
- `DELETE /api/v1/learning/meeting/analyses/{analysis_id}` - Delete analysis
- `POST /api/v1/learning/meeting/analyses/{analysis_id}/response-suggestions` - Generate suggestions
- `GET /api/v1/learning/meeting/analyses/{analysis_id}/response-suggestions` - Get suggestions

### Admin
- `GET /api/v1/admin/users` - List all users with search
- `GET /api/v1/admin/users/{user_id}` - Get user details
- `PUT /api/v1/admin/users/{user_id}` - Update user (admin)
- `POST /api/v1/admin/users/{user_id}/toggle-active` - Toggle user active status
- `POST /api/v1/admin/users/{user_id}/toggle-admin` - Toggle admin status
- `GET /api/v1/admin/stats/overview` - Get platform statistics
- `GET /api/v1/admin/languages` - Get all languages
- `POST /api/v1/admin/languages` - Create language
- `PUT /api/v1/admin/languages/{language_id}` - Update language
- `DELETE /api/v1/admin/languages/{language_id}` - Delete language

### Token Usage
- `GET /api/v1/tokens/usage` - Get usage history
- `GET /api/v1/tokens/usage/summary` - Get usage summary

### WebSocket
- `ws://localhost:8000/ws/{session_id}` - Real-time chat connection

## 🗄️ Database Models

### User
- Authentication and profile information
- Learning preferences and languages
- Admin/regular user roles

### Language
- Supported languages for learning
- Language codes and native names

### Lesson
- Language-specific lessons
- Multiple difficulty levels
- Rich content with exercises

### Chat Session
- User conversations with AI
- Practice scenarios
- Session metadata

### Meeting Analysis
- Transcription analysis results
- Grammar and fluency scores
- Improvement suggestions

### Token Usage
- Track API usage per user
- Cost calculation
- Model-specific breakdowns

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MongoDB connection string | `mongodb://localhost:27017/language_learning` |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Default AI model | `gpt-4` |
| `OPENAI_TEMPERATURE` | AI response creativity | `0.7` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |

### Adding New Languages

1. Use the admin API to add languages:
```python
POST /api/v1/admin/languages
{
    "code": "es",
    "name": "Spanish",
    "native_name": "Español"
}
```

### Customizing AI Behavior

Modify prompts in `app/services/language_learning.py`:
- Conversation analysis prompts
- Meeting analysis prompts
- Response generation prompts

## 🚀 Deployment

### Docker

1. Build the Docker image:
```bash
docker build -t language-learning-backend .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

### Production Considerations

1. **Security**:
   - Use strong SECRET_KEY
   - Enable HTTPS
   - Configure proper CORS origins
   - Rate limiting

2. **Performance**:
   - Use Redis for caching
   - Implement connection pooling
   - Consider horizontal scaling

3. **Monitoring**:
   - Set up logging
   - Monitor API usage
   - Track error rates

## 🛠 Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

The application uses Beanie ODM which handles schema changes automatically. For manual migrations:

```python
# Initialize collections
python -m app.db.init_db
```

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check DATABASE_URL in .env
   - Verify network connectivity

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check rate limits
   - Monitor token usage

3. **CORS Issues**
   - Update FRONTEND_URL in .env
   - Check allowed origins in config

4. **WebSocket Connection Failed**
   - Ensure WebSocket support in deployment
   - Check firewall rules
   - Verify session ID format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- MongoDB for the flexible database
- OpenAI for GPT models
- LangChain for AI orchestration
- All contributors and testers
