# Nova Law AI Backend

**Multi-agent AI system backend with comprehensive API versioning and security features.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- Poetry (for dependency management)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nova-law/backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   # or
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database**
   ```bash
   # Start PostgreSQL (or use Docker)
   docker-compose up postgres -d

   # Run migrations
   alembic upgrade head
   ```

5. **Start the server**
   ```bash
   # Development
   uvicorn app.main:app --reload

   # Production
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 📚 Documentation

### **📁 [Complete Documentation](/docs/)**

- **[Getting Started](/docs/getting-started/)** - Installation, configuration, and deployment
- **[API Documentation](/docs/api/)** - API overview, authentication, and endpoints
- **[Development Guide](/docs/development/)** - Setup, testing, and contributing
- **[Architecture](/docs/architecture/)** - System design and security
- **[Guides](/docs/guides/)** - Versioning, encryption, and troubleshooting

### **🔗 Quick Links**
- [API Reference](http://localhost:8000/api/docs)
- [Health Check](http://localhost:8000/health)
- [Version Info](http://localhost:8000/api/versions)

## 🏗️ Architecture

### **Core Features**
- ✅ **Multi-agent AI system** with LangChain and LangGraph
- ✅ **Comprehensive API versioning** with backward compatibility
- ✅ **JWT-based authentication** with role-based permissions
- ✅ **PostgreSQL database** with Alembic migrations
- ✅ **Rate limiting** and security headers
- ✅ **Monitoring** and health checks
- ✅ **Docker support** for easy deployment

### **Technology Stack**
- **Backend Framework:** FastAPI
- **Database:** PostgreSQL with SQLAlchemy
- **AI/ML:** LangChain, LangGraph, OpenAI, Anthropic
- **Authentication:** JWT with role-based permissions
- **Testing:** pytest with comprehensive test coverage
- **Code Quality:** mypy, ruff, pre-commit hooks

## 🔧 Configuration

### **Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nova_law_db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# AWS SES SMTP (for email sending)
AWS_SES_SMTP_USERNAME=your-smtp-username
AWS_SES_SMTP_PASSWORD=your-smtp-password
AWS_SES_SMTP_HOST=email-smtp.eu-west-2.amazonaws.com
AWS_SES_SMTP_PORT=587
DEFAULT_EMAIL_SENDER=your-verified-email@domain.com
```

### **Docker Deployment**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 🧪 Testing

### **Run Tests**
```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_api.py
```

### **Code Quality**
```bash
# Type checking
mypy app/

# Linting
ruff check app/

# Formatting
ruff format app/
```

## 📊 API Endpoints

### **Authentication**
- `POST /api/v1/register` - User registration
- `POST /api/v1/login` - User login
- `POST /api/v1/refresh` - Token refresh

### **Users**
- `GET /api/v1/users` - List users
- `GET /api/v1/users/me` - Current user profile
- `PUT /api/v1/users/{user_id}` - Update user

### **Agents**
- `GET /api/v1/agents` - List AI agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `PUT /api/v1/agents/{agent_id}/config` - Update agent config

### **System**
- `GET /health` - Health check
- `GET /api/v1/status/detailed` - Detailed system status
- `GET /api/versions` - API version information

## 🔒 Security

### **Features**
- ✅ **JWT authentication** with secure token handling
- ✅ **Role-based permissions** with fine-grained access control
- ✅ **Rate limiting** to prevent abuse
- ✅ **Security headers** (CORS, XSS protection, etc.)
- ✅ **Input validation** with Pydantic models
- ✅ **SQL injection protection** with SQLAlchemy
- ✅ **ID encryption** for sensitive data

### **Best Practices**
- All endpoints require authentication (except public endpoints)
- Sensitive data is encrypted at rest
- Rate limiting prevents abuse
- Comprehensive logging for security events
- Regular security updates and dependency scanning

## 🚀 Deployment

### **Production Checklist**
- [ ] Set `DEBUG=false` in environment
- [ ] Configure production database
- [ ] Set secure `SECRET_KEY`
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline

### **Docker Production**
```bash
# Build production image
docker build -t nova-law-backend .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e DEBUG=false \
  -e DATABASE_URL=postgresql://... \
  nova-law-backend
```

## 🤝 Contributing

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Run the test suite
6. Submit a pull request

### **Code Standards**
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Getting Help**
- 📖 **[Documentation](/docs/)** - Comprehensive guides and references
- 🐛 **[Issues](https://github.com/your-repo/issues)** - Report bugs or request features
- 💬 **[Discussions](https://github.com/your-repo/discussions)** - Ask questions and share ideas

### **Quick Troubleshooting**
- **Database connection issues:** Check `DATABASE_URL` in `.env`
- **Authentication problems:** Verify `SECRET_KEY` and JWT settings
- **AI service errors:** Check API keys for OpenAI/Anthropic
- **Docker issues:** Ensure Docker and Docker Compose are installed

---

**Built with ❤️ by the Nova Law Team**

Updated: 13-Nov-2025 08:05 PM