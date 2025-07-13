# Choy AI Brain - Professional Project Structure

## Project Architecture Overview

```
ChoyAI/                                    # Root directory (AI Brain)
├── README.md                              # Project documentation
├── requirements.txt                       # Python dependencies
├── docker-compose.yml                     # Multi-service deployment
├── Dockerfile                            # Main app container
├── .env.example                          # Environment variables template
├── .gitignore                            # Git ignore rules
├── pyproject.toml                        # Modern Python project config
├── alembic.ini                           # Database migrations config
├── 
├── app/                                  # Main application code
│   ├── __init__.py
│   ├── main.py                           # Application entry point
│   ├── core/                             # Core AI brain functionality
│   │   ├── __init__.py
│   │   ├── ai_engine.py                  # Main AI processing engine
│   │   ├── memory_manager.py             # Long-term memory orchestrator
│   │   ├── persona_engine.py             # Personality system
│   │   ├── context_manager.py            # Conversation context handling
│   │   └── command_router.py             # Command routing & processing
│   │
│   ├── integrations/                     # External service integrations
│   │   ├── __init__.py
│   │   ├── base/                         # Base integration classes
│   │   │   ├── __init__.py
│   │   │   ├── base_integration.py       # Abstract base for all integrations
│   │   │   ├── auth_manager.py           # Authentication handling
│   │   │   └── webhook_handler.py        # Webhook processing
│   │   │
│   │   ├── telegram/                     # Telegram bot integration
│   │   │   ├── __init__.py
│   │   │   ├── bot_handler.py            # Main telegram bot
│   │   │   ├── commands.py               # Command handlers
│   │   │   ├── callbacks.py              # Callback handlers
│   │   │   └── middleware.py             # Custom middleware
│   │   │
│   │   ├── google/                       # Google Workspace integrations
│   │   │   ├── __init__.py
│   │   │   ├── gmail_client.py           # Gmail API integration
│   │   │   ├── calendar_client.py        # Google Calendar
│   │   │   ├── drive_client.py           # Google Drive
│   │   │   └── tasks_client.py           # Google Tasks
│   │   │
│   │   ├── meta/                         # Meta platform integrations
│   │   │   ├── __init__.py
│   │   │   ├── messenger_client.py       # Facebook Messenger
│   │   │   ├── instagram_client.py       # Instagram API
│   │   │   └── whatsapp_client.py        # WhatsApp Business API
│   │   │
│   │   ├── notion/                       # Notion integration
│   │   │   ├── __init__.py
│   │   │   └── notion_client.py          # Notion API client
│   │   │
│   │   ├── clickup/                      # ClickUp integration
│   │   │   ├── __init__.py
│   │   │   └── clickup_client.py         # ClickUp API client
│   │   │
│   │   └── tradingview/                  # TradingView integration
│   │       ├── __init__.py
│   │       └── trading_client.py         # Trading data integration
│   │
│   ├── modules/                          # Core functional modules
│   │   ├── __init__.py
│   │   ├── chat/                         # Chat & conversation module
│   │   │   ├── __init__.py
│   │   │   ├── chat_engine.py            # Main chat processing
│   │   │   ├── conversation_manager.py   # Conversation state
│   │   │   └── response_generator.py     # Response generation
│   │   │
│   │   ├── memory/                       # Memory management module
│   │   │   ├── __init__.py
│   │   │   ├── core_memory.py            # Core facts & knowledge
│   │   │   ├── user_memory.py            # User-specific memories
│   │   │   ├── conversation_memory.py    # Conversation history
│   │   │   └── vector_store.py           # Vector database for semantic search
│   │   │
│   │   ├── personas/                     # Personality system
│   │   │   ├── __init__.py
│   │   │   ├── persona_manager.py        # Persona switching logic
│   │   │   ├── personality_traits.py     # Personality definitions
│   │   │   └── response_styles.py        # Response style adapters
│   │   │
│   │   ├── reminders/                    # Reminder system
│   │   │   ├── __init__.py
│   │   │   ├── reminder_engine.py        # Core reminder logic
│   │   │   ├── scheduler.py              # Task scheduling
│   │   │   └── notifications.py          # Notification delivery
│   │   │
│   │   ├── tasks/                        # Task management
│   │   │   ├── __init__.py
│   │   │   ├── task_manager.py           # Task CRUD operations
│   │   │   ├── priority_engine.py        # Task prioritization
│   │   │   └── automation.py             # Task automation logic
│   │   │
│   │   ├── finance/                      # Finance tracking
│   │   │   ├── __init__.py
│   │   │   ├── finance_manager.py        # Financial data management
│   │   │   ├── analytics.py              # Financial analytics
│   │   │   └── reporting.py              # Financial reporting
│   │   │
│   │   └── intelligence/                 # AI intelligence modules
│   │       ├── __init__.py
│   │       ├── nlp_processor.py          # Natural language processing
│   │       ├── intent_classifier.py      # Intent recognition
│   │       ├── entity_extractor.py       # Entity extraction
│   │       └── sentiment_analyzer.py     # Sentiment analysis
│   │
│   ├── api/                              # API layer (future web interface)
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI application
│   │   ├── routes/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                   # Authentication routes
│   │   │   ├── chat.py                   # Chat API endpoints
│   │   │   ├── memory.py                 # Memory API endpoints
│   │   │   ├── integrations.py           # Integration management
│   │   │   └── webhooks.py               # Webhook endpoints
│   │   │
│   │   ├── middleware/                   # API middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py        # Authentication middleware
│   │   │   ├── rate_limiting.py          # Rate limiting
│   │   │   └── logging_middleware.py     # Request logging
│   │   │
│   │   └── schemas/                      # Pydantic schemas
│   │       ├── __init__.py
│   │       ├── auth.py                   # Authentication schemas
│   │       ├── chat.py                   # Chat schemas
│   │       ├── memory.py                 # Memory schemas
│   │       └── integrations.py           # Integration schemas
│   │
│   ├── database/                         # Database layer
│   │   ├── __init__.py
│   │   ├── models/                       # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # Base model class
│   │   │   ├── user.py                   # User model
│   │   │   ├── conversation.py           # Conversation model
│   │   │   ├── memory.py                 # Memory models
│   │   │   ├── persona.py                # Persona model
│   │   │   ├── integration.py            # Integration model
│   │   │   └── task.py                   # Task model
│   │   │
│   │   ├── repositories/                 # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py        # Base repository
│   │   │   ├── user_repository.py        # User data access
│   │   │   ├── memory_repository.py      # Memory data access
│   │   │   ├── conversation_repository.py # Conversation data access
│   │   │   └── task_repository.py        # Task data access
│   │   │
│   │   ├── migrations/                   # Alembic migrations
│   │   │   └── versions/                 # Migration files
│   │   │
│   │   └── connection.py                 # Database connection management
│   │
│   ├── services/                         # Business logic services
│   │   ├── __init__.py
│   │   ├── user_service.py               # User management service
│   │   ├── chat_service.py               # Chat processing service
│   │   ├── memory_service.py             # Memory management service
│   │   ├── persona_service.py            # Persona management service
│   │   ├── integration_service.py        # Integration management service
│   │   ├── task_service.py               # Task management service
│   │   └── notification_service.py       # Notification service
│   │
│   ├── utils/                            # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py                     # Logging configuration
│   │   ├── security.py                   # Security utilities
│   │   ├── validators.py                 # Data validation utilities
│   │   ├── date_utils.py                 # Date/time utilities
│   │   ├── text_processing.py            # Text processing utilities
│   │   └── cache.py                      # Caching utilities
│   │
│   └── config/                           # Configuration management
│       ├── __init__.py
│       ├── settings.py                   # Main settings
│       ├── database.py                   # Database configuration
│       ├── integrations.py               # Integration configurations
│       └── personas.py                   # Persona configurations
│
├── data/                                 # Data storage
│   ├── personas/                         # Persona prompt files
│   │   ├── choy.yaml                     # Choy persona definition
│   │   ├── stark.yaml                    # Stark persona definition
│   │   ├── rose.yaml                     # Rose persona definition
│   │   ├── sherlock.yaml                 # Sherlock persona definition
│   │   ├── joker.yaml                    # Joker persona definition
│   │   ├── hermione.yaml                 # Hermione persona definition
│   │   └── harley.yaml                   # Harley persona definition
│   │
│   ├── prompts/                          # System prompts
│   │   ├── system_prompts.yaml           # Base system prompts
│   │   ├── integration_prompts.yaml      # Integration-specific prompts
│   │   └── task_prompts.yaml             # Task-specific prompts
│   │
│   ├── databases/                        # Database files
│   │   ├── core_memory.db                # Core memory database
│   │   ├── user_memories.db              # User memory database
│   │   └── conversations.db              # Conversation history
│   │
│   └── logs/                             # Log files
│       ├── app.log                       # Application logs
│       ├── error.log                     # Error logs
│       └── integration.log               # Integration logs
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── conftest.py                       # Pytest configuration
│   ├── unit/                             # Unit tests
│   │   ├── __init__.py
│   │   ├── test_core/                    # Core functionality tests
│   │   ├── test_modules/                 # Module tests
│   │   ├── test_integrations/            # Integration tests
│   │   └── test_services/                # Service tests
│   │
│   ├── integration/                      # Integration tests
│   │   ├── __init__.py
│   │   ├── test_telegram_bot.py          # Telegram bot tests
│   │   ├── test_memory_system.py         # Memory system tests
│   │   └── test_personas.py              # Persona system tests
│   │
│   └── fixtures/                         # Test fixtures
│       ├── __init__.py
│       ├── sample_conversations.json     # Sample conversation data
│       ├── sample_memories.json          # Sample memory data
│       └── sample_personas.yaml          # Sample persona data
│
├── scripts/                              # Utility scripts
│   ├── setup_environment.py              # Environment setup
│   ├── migrate_database.py               # Database migration
│   ├── backup_data.py                    # Data backup
│   ├── deploy.py                         # Deployment script
│   └── health_check.py                   # Health monitoring
│
├── docs/                                 # Documentation
│   ├── README.md                         # Main documentation
│   ├── INSTALLATION.md                   # Installation guide
│   ├── API.md                            # API documentation
│   ├── INTEGRATIONS.md                   # Integration guide
│   ├── DEPLOYMENT.md                     # Deployment guide
│   └── ARCHITECTURE.md                   # Architecture documentation
│
└── deploy/                               # Deployment configurations
    ├── docker/                           # Docker configurations
    │   ├── Dockerfile.prod               # Production Dockerfile
    │   ├── Dockerfile.dev                # Development Dockerfile
    │   └── docker-compose.prod.yml       # Production compose
    │
    ├── kubernetes/                       # Kubernetes manifests
    │   ├── namespace.yaml
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── ingress.yaml
    │
    └── terraform/                        # Infrastructure as Code
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Key Architectural Principles

1. **Modular Design**: Each functionality is isolated in its own module
2. **Integration Ready**: Prepared for all planned integrations (Google, Meta, Notion, etc.)
3. **Scalable**: Can handle multiple users and high conversation volume
4. **Memory-Centric**: Long-term memory is a first-class citizen
5. **Persona-Aware**: Multiple personalities with consistent behavior
6. **API-First**: Ready for web and mobile interfaces
7. **Production-Ready**: Includes monitoring, logging, and deployment configs

## Next Steps

1. Restructure existing code into this architecture
2. Implement the core AI engine with memory management
3. Enhance persona system with YAML-based configurations
4. Add integration framework for future modules
5. Set up proper testing and deployment pipelines
