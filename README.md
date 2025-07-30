# 🏥 Healthcare Management System - Multi-Agent AI Platform

A comprehensive, production-ready healthcare management system powered by multiple AI agents working together to provide intelligent healthcare services.

## 🚀 Features

### 🤖 Multi-Agent AI System
- **Chatbot Agent**: Natural language processing with Groq LLaMA models
- **Emergency Agent**: Real-time emergency detection and response
- **Triage Agent**: Intelligent patient triage and prioritization
- **Monitoring Agent**: Continuous vital signs monitoring and alerts
- **Treatment Agent**: Evidence-based treatment recommendations
- **Medical Records Agent**: HIPAA-compliant record management
- **Scheduling Agent**: AI-optimized appointment scheduling

### 🏥 Healthcare Capabilities
- Patient registration and management
- Medical record creation and retrieval
- Vital signs monitoring and analysis
- Emergency response coordination
- Appointment scheduling and optimization
- Drug interaction checking
- Medical coding assistance (ICD-10, CPT)
- HIPAA-compliant data handling

### 🔧 Technical Features
- Flask-based REST API
- MySQL/PostgreSQL database support
- Real-time WebSocket communication
- JWT authentication and authorization
- Comprehensive logging and monitoring
- Docker containerization
- Production-ready security features

## 📁 Project Structure

```
healthcareagents/
├── 📁 data/                          # Medical data and configurations
│   ├── medical_codes.json            # ICD-10, CPT codes
│   ├── medications.json              # Drug database with interactions
│   └── synthetic_patients.json      # Sample patient data
├── 📁 src/
│   ├── 📁 agents/                   # AI Agent implementations
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── chatbot_agent.py        # Conversational AI agent
│   │   ├── emergency_agent.py      # Emergency response agent
│   │   ├── triage_agent.py         # Patient triage agent
│   │   ├── monitoring_agent.py     # Vital signs monitoring
│   │   ├── treatment_agent.py      # Treatment planning agent
│   │   ├── medical_records_agent.py # Medical records management
│   │   └── scheduling_agent.py     # Appointment scheduling
│   ├── 📁 api/                      # REST API endpoints
│   │   ├── routes.py               # Main API routes
│   │   ├── chatbot_routes.py       # Chatbot API endpoints
│   │   ├── patient_entry_form.py   # Patient registration
│   │   └── middleware.py           # Authentication & security
│   ├── 📁 database/                # Database models and connection
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── connection.py          # Database connection management
│   │   ├── schema.sql             # Database schema
│   │   └── sample_data.sql        # Sample data
│   ├── 📁 tools/                   # Agent tools and utilities
│   │   ├── database_tools.py      # Database operations
│   │   ├── medical_tools.py       # Medical calculations
│   │   ├── notification_tools.py  # Alert and notification system
│   │   └── validation_tools.py    # Input validation
│   ├── 📁 workflows/               # Business process workflows
│   │   ├── emergency_response_workflow.py
│   │   ├── patient_admission_workflow.py
│   │   ├── treatment_workflow.py
│   │   └── monitoring_workflow.py
│   ├── 📁 static/                  # Frontend interfaces
│   │   ├── chatbot.html           # Chatbot UI
│   │   └── new-patient.html       # Patient registration form
│   └── main.py                     # Application entry point
├── 📁 tests/                       # Comprehensive test suite
├── 📁 logs/                        # Application logs
├── docker-compose.yml              # Multi-container setup
├── Dockerfile                      # Application container
└── requirements.txt                # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL or PostgreSQL
- Docker (optional)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd healthcareagents
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database and API credentials
```

4. **Initialize database**
```bash
python -c "from src.database.connection import init_database; init_database()"
```

5. **Run the application**
```bash
python src/main.py
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual container
docker build -t healthcare-agents .
docker run -p 5000:5000 healthcare-agents
```

## 🏥 API Endpoints

### Authentication
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - Session termination
- `GET /api/auth/profile` - User profile

### Patient Management
- `GET /api/patients` - List patients with search/filter
- `POST /api/patients` - Register new patient
- `GET /api/patients/{id}` - Get patient details
- `PUT /api/patients/{id}` - Update patient information

### Medical Records
- `GET /api/medical-records/{patient_id}` - Get patient records
- `POST /api/medical-records` - Create medical record
- `GET /api/vital-signs/{patient_id}` - Get vital signs history
- `POST /api/vital-signs` - Submit vital signs

### Chatbot & AI Agents
- `POST /api/chatbot/chat` - Process chat message
- `GET /api/chatbot/conversations` - Get conversation history
- `POST /api/agents/triage` - Process patient triage
- `POST /api/agents/emergency` - Emergency response

### Appointments & Scheduling
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Schedule appointment
- `PUT /api/appointments/{id}` - Update appointment

### Monitoring & Alerts
- `GET /api/alerts` - Get system alerts
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert

## 🤖 AI Agents Overview

### Chatbot Agent
- Natural language processing with Groq LLaMA models
- Multi-turn conversation management
- Intent recognition and entity extraction
- Integration with all healthcare agents
- Multilingual support

### Emergency Agent
- Real-time emergency detection
- Automated emergency protocol activation
- Staff notification and coordination
- Resource allocation optimization
- Post-incident analysis

### Triage Agent
- Intelligent patient triage and prioritization
- Symptom assessment and severity scoring
- Resource allocation optimization
- Queue management and wait time prediction
- Emergency vs. routine classification

### Monitoring Agent
- Real-time vital signs monitoring
- Automated alert generation
- Trend analysis and predictive analytics
- Integration with medical devices (IoT)
- Patient deterioration detection

### Treatment Agent
- Evidence-based treatment recommendations
- Drug interaction and allergy checking
- Dosage calculation and optimization
- Treatment protocol adherence monitoring
- Clinical decision support

### Medical Records Agent
- Secure medical record management
- HIPAA-compliant data encryption
- Medical history analysis and summarization
- Document processing and OCR integration
- Medical coding assistance

### Scheduling Agent
- AI-optimized appointment scheduling
- Doctor availability and workload balancing
- Patient preference consideration
- Automated reminder system
- Resource scheduling optimization

## 🔒 Security & Compliance

### HIPAA Compliance
- Data encryption at rest and in transit
- Access control and audit logging
- Secure authentication and authorization
- Data backup and disaster recovery
- Privacy protection measures

### Security Features
- JWT token-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting and abuse prevention

## 📊 Database Schema

### Core Entities
- **Patients**: Demographics, contact info, insurance
- **MedicalRecords**: Encrypted clinical data with versioning
- **Appointments**: Scheduling with status tracking
- **VitalSigns**: Patient vital signs with timestamps
- **Alerts**: System alerts and notifications
- **Users**: Staff authentication and permissions
- **ChatHistory**: Conversation logs with agent interactions

### Relationships
- Patients have multiple MedicalRecords
- Patients have multiple VitalSigns
- Patients have multiple Appointments
- Users can access multiple Patients
- Agents interact through ChatHistory

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_agents.py
pytest tests/test_database.py
pytest tests/test_api.py

# Run with coverage
pytest --cov=src tests/
```

### Test Categories
- **Unit Tests**: Individual agent and tool testing
- **Integration Tests**: Database and API testing
- **Workflow Tests**: End-to-end process testing
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

## 📈 Monitoring & Logging

### Logging
- Structured logging with log rotation
- Request/response logging
- Error tracking and alerting
- Performance metrics collection
- Audit trail for compliance

### Health Checks
- Database connectivity monitoring
- Agent availability checks
- API endpoint health monitoring
- System resource monitoring
- External service dependencies

## 🚀 Deployment

### Production Deployment
1. **Environment Setup**
   - Configure production database
   - Set up SSL certificates
   - Configure load balancer
   - Set up monitoring and alerting

2. **Docker Deployment**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Database Migration**
   ```bash
   alembic upgrade head
   ```

4. **Health Monitoring**
   - Monitor application health at `/health`
   - Set up automated backups
   - Configure log aggregation

### Scaling
- Horizontal scaling with load balancers
- Database read replicas
- Caching with Redis
- Message queues for async processing
- Microservices architecture support

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- API Documentation: `/docs` (when running)
- Code Documentation: Inline docstrings
- Architecture Overview: This README

### Issues & Questions
- Create an issue for bugs or feature requests
- Check existing issues for solutions
- Contact the development team for support

## 🔮 Roadmap

### Planned Features
- [ ] Voice recognition and synthesis
- [ ] Advanced analytics and reporting
- [ ] Mobile application
- [ ] Integration with external EHR systems
- [ ] Machine learning model training pipeline
- [ ] Advanced security features
- [ ] Multi-tenant architecture
- [ ] Real-time collaboration features

### Performance Optimizations
- [ ] Database query optimization
- [ ] Caching layer implementation
- [ ] Async processing improvements
- [ ] Memory usage optimization
- [ ] Response time improvements

---

**🏥 Healthcare Management System** - Empowering healthcare with intelligent AI agents for better patient care and operational efficiency.  