# Healthcare Management System

A comprehensive AI-powered healthcare management system built with Python, LangChain, and PostgreSQL. This system provides intelligent agents for various healthcare workflows including triage, emergency response, patient monitoring, and treatment management.

## Features

- **AI-Powered Agents**: Multiple specialized agents for different healthcare tasks
- **Real-time Monitoring**: Continuous patient vital signs monitoring with alert system
- **Emergency Response**: Automated emergency detection and response workflows
- **Patient Management**: Complete patient admission, treatment, and discharge workflows
- **Medical Records**: Intelligent medical records management and retrieval
- **Scheduling**: Automated appointment scheduling and resource management
- **API Integration**: RESTful API for external system integration

## Architecture

The system is built with a modular architecture:

```
src/
├── agents/           # AI agents for different healthcare tasks
├── api/             # REST API endpoints
├── config/          # Configuration management
├── database/        # Database models and connection
├── tools/           # LangChain tools for agent operations
├── utils/           # Utility functions and helpers
└── workflows/       # Complex healthcare workflows
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd healthcare_management_system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
python -m database.connection
```

5. Run the application:
```bash
python src/main.py
```

## Configuration

### Environment Variables

- `DATABASE_HOST`: PostgreSQL host (default: localhost)
- `DATABASE_PORT`: PostgreSQL port (default: 5432)
- `DATABASE_NAME`: Database name (default: healthcare_db)
- `DATABASE_USER`: Database user (default: postgres)
- `DATABASE_PASSWORD`: Database password
- `GROQ_API_KEY`: Groq API key for LLM operations
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 5000)
- `SECRET_KEY`: Application secret key

### Docker Deployment

```bash
docker-compose up -d
```

## API Documentation

### Endpoints

- `GET /api/health`: Health check
- `POST /api/triage`: Patient triage
- `POST /api/emergency`: Emergency response
- `GET /api/patients`: List patients
- `POST /api/patients`: Create patient
- `GET /api/patients/{id}`: Get patient details
- `PUT /api/patients/{id}`: Update patient
- `POST /api/monitoring`: Submit vital signs
- `GET /api/appointments`: List appointments
- `POST /api/appointments`: Create appointment

## Agents

### Triage Agent
Handles initial patient assessment and triage level assignment.

### Emergency Agent
Manages emergency situations and coordinates emergency response.

### Monitoring Agent
Monitors patient vital signs and generates alerts for abnormal values.

### Treatment Agent
Manages patient treatment plans and medication administration.

### Medical Records Agent
Handles medical records creation, retrieval, and updates.

### Scheduling Agent
Manages appointments, resource allocation, and scheduling conflicts.

## Workflows

### Emergency Response Workflow
1. Emergency detection
2. Alert generation
3. Resource allocation
4. Response coordination
5. Follow-up actions

### Patient Admission Workflow
1. Patient registration
2. Initial assessment
3. Room assignment
4. Care plan creation
5. Monitoring setup

### Treatment Workflow
1. Diagnosis review
2. Treatment planning
3. Medication management
4. Progress monitoring
5. Discharge planning

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

```bash
black src/
flake8 src/
```

### Database Migrations

```bash
python -m database.migrations
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.
# MESSAGE
