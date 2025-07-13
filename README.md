# 🧠 Choy AI Brain

**Advanced Personal AI Assistant with Long-Term Memory & Multiple Personalities**

Choy AI Brain is the central intelligence hub designed to be the core AI system that integrates with all other modules in the Choy AI ecosystem. It features sophisticated long-term memory, multiple AI personalities, and a scalable architecture ready for integration with various platforms and services.

## ✨ Key Features

### 🧠 **Intelligent Core**
- **Long-term Memory**: Persistent user memories with semantic search
- **Multiple Personas**: Switch between different AI personalities (Choy, Stark, Rose, etc.)
- **Context Awareness**: Maintains conversation context across sessions
- **Strategic Thinking**: AI that remembers and builds upon previous interactions

### 🤖 **Multi-Provider AI System**
- **Provider Management**: Support for multiple AI providers with automatic failover
- **Task-Specific Routing**: Different providers optimized for different task types
- **Performance Monitoring**: Real-time provider health checking and metrics
- **Flexible Configuration**: Easy switching between providers based on preferences

### 💬 **Communication**
- **Telegram Bot**: Full-featured Telegram integration
- **Natural Conversations**: Context-aware responses that reference past interactions
- **Memory Commands**: Save, recall, and manage personal information
- **Persona Switching**: Real-time personality changes for different interaction styles

### 🏗️ **Architecture**
- **Modular Design**: Clean separation of concerns with pluggable components
- **Scalable**: Designed to handle multiple users and high conversation volume
- **Integration Ready**: Prepared for Google Workspace, Meta, Notion, ClickUp, and more
- **Production Ready**: Includes logging, monitoring, and deployment configurations

### 🎭 **Available Personas**

| Persona | Style | Purpose |
|---------|-------|---------|
| **Choy** | Confident, strategic, direct | Primary assistant persona |
| **Stark** | Tech genius, sarcastic, innovative | Technical discussions |
| **Rose** | Warm, empathetic, supportive | Emotional support & guidance |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- At least one AI API Key:
  - **DeepSeek API Key** (Primary, recommended)
  - **OpenAI API Key** (Optional, for ChatGPT)
  - **Anthropic API Key** (Optional, for Claude)
  - **xAI API Key** (Optional, for Grok)
  - **Google AI API Key** (Optional, for Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ChoyAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the AI Brain**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following required variables:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional
DEFAULT_PERSONA=choy
LOG_LEVEL=INFO
MAX_CONVERSATION_HISTORY=50
```

See `.env.example` for all available configuration options.

### Personas Configuration

Personas are defined in YAML files in the `data/personas/` directory. Each persona has:

- **System Prompt**: Core personality instructions
- **Style**: Communication style description
- **Traits**: Personality characteristics
- **Response Style**: Technical response parameters

## 🎯 Usage

### Telegram Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and overview | `/start` |
| `/persona <name>` | Switch AI personality | `/persona stark` |
| `/personas` | List available personalities | `/personas` |
| `/remember <key> <value>` | Save a memory | `/remember favorite_color blue` |
| `/recall <key>` | Retrieve a memory | `/recall favorite_color` |
| `/memories` | List all memories | `/memories` |
| `/bio <text>` | Set biography | `/bio Software engineer` |
| `/history` | View conversation history | `/history` |
| `/stats` | View AI statistics | `/stats` |

### AI Provider Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/providers` | Show available AI providers and status | `/providers` |
| `/switchai <task> <provider>` | Switch AI provider for tasks | `/switchai creative openai` |
| `/aitask <task> <message>` | Force specific task type | `/aitask technical Explain async Python` |

### Available Task Types & Optimal Providers

| Task Type | Best For | Optimal Provider | Fallback |
|-----------|----------|------------------|----------|
| `conversation` | General chat | DeepSeek | OpenAI, Claude |
| `technical` | Programming questions | DeepSeek | OpenAI, xAI |
| `creative` | Writing, storytelling | OpenAI | Claude, DeepSeek |
| `analysis` | Deep analysis, research | Claude | OpenAI, DeepSeek |
| `research` | Information gathering | Gemini | Claude, OpenAI |
| `coding` | Code generation | DeepSeek | OpenAI, Claude |
| `problem` | Problem solving | OpenAI | Claude, DeepSeek |
| `emotional` | Emotional support | Claude | OpenAI, DeepSeek |
| `summary` | Summarization | Claude | Gemini, OpenAI |
| `translate` | Translation | Gemini | OpenAI, Claude |

### Natural Conversation

Just chat naturally! The AI will:
- Remember important details automatically
- Reference past conversations
- Adapt responses based on the active persona
- Provide personalized assistance

## 🏗️ Architecture

```
ChoyAI/
├── app/                          # Main application
│   ├── core/                     # Core AI engine
│   ├── modules/                  # Functional modules
│   │   ├── memory/              # Memory management
│   │   ├── personas/            # Personality system
│   │   └── chat/                # Chat processing
│   ├── integrations/            # External integrations
│   │   └── telegram/            # Telegram bot
│   ├── config/                  # Configuration
│   └── utils/                   # Utilities
├── data/                        # Data storage
│   ├── personas/               # Persona definitions
│   ├── databases/              # SQLite databases
│   └── logs/                   # Log files
└── docs/                       # Documentation
```

### Core Components

- **AI Engine**: Central processing unit that orchestrates all functionality
- **Memory Managers**: Core, User, and Conversation memory systems
- **Persona Manager**: Multi-personality system with YAML-based configs
- **Chat Engine**: Natural language processing and response generation
- **Integration Handlers**: Platform-specific integrations (Telegram, future: Web, Mobile)

## 🔮 Future Integrations

The architecture is designed to support the full Choy AI ecosystem:

### Planned Modules
- **📧 Email** - Gmail integration with AI-powered management
- **📅 Calendar** - Google Calendar with intelligent scheduling
- **📝 Notes** - Notion integration for knowledge management
- **📊 Project Management** - ClickUp integration for task management
- **💰 Finance** - Personal finance tracking and insights
- **📱 Social Media** - Multi-platform content management
- **📈 Trading** - TradingView integration for market analysis
- **🌐 Web Interface** - Full web application
- **📱 Mobile Apps** - Flutter-based mobile applications

### Integration Framework
Each module follows a standardized integration pattern:
- OAuth/API authentication
- Webhook support for real-time updates
- Unified command interface
- Memory integration for context sharing

## 📊 Memory System

### Three-Layer Memory Architecture

1. **Core Memory**: System facts, capabilities, and permanent knowledge
2. **User Memory**: Personal information, preferences, and custom memories
3. **Conversation Memory**: Chat history and session context

### Memory Features
- **Automatic Extraction**: Important information is automatically saved
- **Manual Commands**: Users can explicitly save/recall memories
- **Semantic Search**: Find relevant memories using natural language
- **Context Integration**: Memories are automatically included in AI responses

## 🔒 Security & Privacy

- **Rate Limiting**: Prevents abuse with configurable limits
- **User Validation**: Optional user allowlists for private deployment
- **Data Encryption**: Sensitive data is properly secured
- **Local Storage**: All data stored locally in SQLite databases
- **No Cloud Dependencies**: Complete control over your data

## 🚀 Deployment

### Development
```bash
python main.py
```

### Production with Docker
```bash
docker build -t choy-ai-brain .
docker run -d --env-file .env choy-ai-brain
```

### Docker Compose
```bash
docker-compose up -d
```

## 📈 Monitoring

The system includes comprehensive monitoring:

- **Performance Metrics**: Response times, message counts, memory usage
- **Health Checks**: Automatic system health monitoring
- **Structured Logging**: JSON logs for analysis
- **Error Tracking**: Detailed error logging and reporting

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs and request features via GitHub issues
- **Discussions**: Join community discussions for help and ideas

## 🎯 Vision

Choy AI Brain serves as the foundation for a complete AI-powered personal assistant ecosystem. Our goal is to create an intelligent system that:

- **Learns and Remembers**: Builds a comprehensive understanding of each user
- **Integrates Everything**: Connects all your digital tools and services
- **Stays Personal**: Maintains privacy while providing personalized assistance
- **Scales Intelligently**: Grows more capable and useful over time

---

**Built with ❤️ for the future of personal AI assistance**
