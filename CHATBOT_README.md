# Healthcare Assistant Chatbot

A sophisticated, AI-powered chatbot system for healthcare management with context keeping, conversation management, and intelligent response generation.

## Features

### 🤖 Intelligent Conversation Management
- **Context Awareness**: Maintains conversation context across sessions
- **Intent Recognition**: Automatically detects user intentions
- **Entity Extraction**: Extracts relevant information from messages
- **Multi-turn Conversations**: Handles complex, multi-step interactions

### 🏥 Healthcare-Specific Capabilities
- **Patient Lookup**: Find and retrieve patient information
- **Appointment Scheduling**: Book and manage appointments
- **Medical Records**: Access and update medical records
- **Vital Signs**: Submit and monitor patient vitals
- **Triage Assessment**: Perform initial patient assessments
- **Emergency Response**: Handle urgent situations with immediate escalation

### 💬 Advanced UI Features
- **Real-time Messaging**: Instant message processing and responses
- **Typing Indicators**: Visual feedback during processing
- **Smart Suggestions**: Context-aware response suggestions
- **Session Management**: Persistent conversation sessions
- **Responsive Design**: Works on desktop and mobile devices

### 🔒 Security & Privacy
- **Session Isolation**: Secure conversation sessions
- **Data Validation**: Comprehensive input validation
- **Audit Logging**: Complete conversation and action logging
- **HIPAA Compliance**: Healthcare data protection measures

## Quick Start

### 1. Access the Chatbot UI

Navigate to the chatbot interface:
```
http://localhost:5000/chatbot
```

### 2. Start a Conversation

The chatbot will automatically create a new session and provide a welcome message with suggested actions.

### 3. Use Quick Actions

Use the sidebar quick actions for common tasks:
- **Find Patient**: Search for patient information
- **Schedule Appointment**: Book appointments
- **Medical Records**: Access patient records
- **Vital Signs**: Submit patient vitals
- **Triage Assessment**: Perform assessments

## API Endpoints

### Chat Operations

#### Send Message
```http
POST /api/chatbot/chat
Content-Type: application/json

{
  "message": "Find patient John Smith",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "patient_id": "optional-patient-id"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message processed successfully",
  "data": {
    "session_id": "session-uuid",
    "message": "I found patient John Smith...",
    "intent": "patient_lookup",
    "confidence": 0.95,
    "entities": {
      "patient_name": "John Smith"
    },
    "actions": [],
    "suggestions": [
      "View medical records",
      "Schedule appointment"
    ],
    "response_time": 1.2
  }
}
```

#### Create Session
```http
POST /api/chatbot/sessions
Content-Type: application/json

{
  "user_id": "user123",
  "patient_id": "patient456",
  "conversation_type": "general"
}
```

#### Get Conversation History
```http
GET /api/chatbot/conversations/{session_id}/messages?limit=50
```

#### Close Conversation
```http
POST /api/chatbot/conversations/{session_id}/close
```

### Context Management

#### Get Context
```http
GET /api/chatbot/context/{session_id}
```

#### Update Context
```http
PUT /api/chatbot/context/{session_id}
Content-Type: application/json

{
  "context_data": {
    "current_topic": "appointment_scheduling",
    "patient_id": "patient123"
  },
  "user_preferences": {
    "language": "en",
    "notifications": true
  }
}
```

### Analytics

#### Get Chatbot Analytics
```http
GET /api/chatbot/analytics
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_conversations": 150,
    "active_conversations": 12,
    "total_messages": 1250,
    "intent_distribution": [
      {"intent": "patient_lookup", "count": 45},
      {"intent": "appointment_scheduling", "count": 32}
    ],
    "recent_activity": [...]
  }
}
```

## Conversation Examples

### Patient Lookup
```
User: "Find patient John Smith"
Bot: "I found patient John Smith (MRN: 12345). What would you like to know about this patient?"
Suggestions: ["View medical records", "Check appointments", "View vital signs"]
```

### Appointment Scheduling
```
User: "Schedule a follow-up appointment for next week"
Bot: "I can help you schedule a follow-up appointment. What day next week works best for you?"
Suggestions: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
```

### Emergency Situation
```
User: "Patient is having chest pain and difficulty breathing"
Bot: "🚨 EMERGENCY DETECTED! I've immediately alerted the emergency response team. Please stay calm and provide any additional details about the situation. Medical staff will respond immediately."
Actions: [Emergency alert created]
```

### Medical Records
```
User: "Show me the latest medical records for patient 12345"
Bot: "I found 5 medical records for this patient. Here's a summary of the most recent records:
• Diagnosis: Hypertension (2024-01-15)
• Treatment: Medication adjustment (2024-01-10)
• Lab Results: Blood work (2024-01-05)"
```

## Database Schema

### ChatbotConversation
```sql
CREATE TABLE chatbot_conversations (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(50),
    patient_id VARCHAR(36),
    conversation_type VARCHAR(50) DEFAULT 'general',
    status VARCHAR(20) DEFAULT 'active',
    context_data JSON,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME
);
```

### ChatbotMessage
```sql
CREATE TABLE chatbot_messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(100),
    confidence FLOAT,
    entities JSON,
    context_snapshot JSON,
    response_time FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ChatbotContext
```sql
CREATE TABLE chatbot_contexts (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50),
    patient_id VARCHAR(36),
    context_data JSON NOT NULL,
    conversation_history JSON,
    user_preferences JSON,
    system_state JSON,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables
```bash
# Chatbot Configuration
CHATBOT_MAX_MESSAGE_LENGTH=1000
CHATBOT_MAX_HISTORY=50
CHATBOT_RESPONSE_TIMEOUT=30
CHATBOT_ENABLE_TYPING_INDICATORS=true
CHATBOT_ENABLE_SUGGESTIONS=true

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=llama3.2-70b-8192
```

### Chatbot Configuration Schema
```python
class ChatbotConfig:
    max_message_length: int = 1000
    max_conversation_history: int = 50
    response_timeout: float = 30.0
    enable_typing_indicators: bool = True
    enable_suggestions: bool = True
    emergency_keywords: List[str] = [
        "chest pain", "difficulty breathing", "unconscious",
        "bleeding", "seizure", "heart attack", "stroke"
    ]
```

## Security Considerations

### Input Validation
- All messages are validated for length and content
- SQL injection prevention through parameterized queries
- XSS protection through content sanitization
- Rate limiting on API endpoints

### Data Privacy
- Session data is isolated per user
- Patient data access is logged and audited
- Sensitive information is encrypted in transit
- Automatic session cleanup for inactive sessions

### Access Control
- User authentication and authorization
- Role-based access to patient data
- Audit trails for all actions
- Emergency escalation protocols

## Monitoring & Analytics

### Key Metrics
- **Response Time**: Average time to generate responses
- **Intent Accuracy**: Success rate of intent recognition
- **User Satisfaction**: Based on conversation completion
- **Emergency Detection**: Accuracy of emergency identification

### Logging
- All conversations are logged for analysis
- Intent recognition results are tracked
- Error conditions are monitored
- Performance metrics are collected

### Health Checks
```http
GET /api/chatbot/health
```

## Troubleshooting

### Common Issues

#### Session Not Found
- **Cause**: Session expired or invalid session ID
- **Solution**: Create a new session

#### Slow Response Times
- **Cause**: High system load or LLM API issues
- **Solution**: Check system resources and API status

#### Intent Recognition Errors
- **Cause**: Unclear user input or new intent patterns
- **Solution**: Improve training data and refine prompts

### Debug Mode
Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

## Development

### Adding New Intents
1. Update the `IntentType` enum in schemas
2. Add intent handler in `ChatbotAgent`
3. Update training data and prompts
4. Test with sample conversations

### Customizing Responses
1. Modify system prompts in `ChatbotAgent`
2. Update response templates
3. Add new suggestion patterns
4. Test response quality

### Extending Functionality
1. Add new tools to the tools dictionary
2. Create corresponding API endpoints
3. Update the chatbot agent to use new tools
4. Add UI components for new features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 