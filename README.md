# 🧠 ChoyAI: Cost-Effective Productivity Suite

**Advanced Personal AI Assistant with 14-Module Productivity Ecosystem**

ChoyAI is a comprehensive productivity suite featuring | Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message and overview | `/start` |
| `/persona <n>` | Switch AI personality | `/persona tony` |
| `/personas` | List available personalities | `/personas` |`/persona <n>` | Switch AI personality | `/persona tony` | `/persona <n>` | Switch AI personality | `/persona tony` | `/persona <n>` | Switch AI personality | `/persona tony` |isticated AI-powered modules for personal and business automation. Built with cost-efficiency in mind, it integrates multiple free APIs and minimal paid services to deliver maximum value with minimal operational costs.

## ✨ Key Features

### 🧠 **Intelligent Core**
- **Long-term Memory**: Persistent user memories with semantic search
- **Multiple Personas**: Switch between different AI personalities (Choy, Tony, Rose, etc.)
- **Context Awareness**: Maintains conversation context across sessions
- **Strategic Thinking**: AI that remembers and builds upon previous interactions
- **Cost-Optimized**: Smart API usage with free-tier maximization

### 🤖 **Multi-Provider AI System**
- **Provider Management**: Support for multiple AI providers with automatic failover
- **Task-Specific Routing**: Different providers optimized for different task types
- **Performance Monitoring**: Real-time provider health checking and metrics
- **Flexible Configuration**: Easy switching between providers based on preferences
- **Cost Control**: DeepSeek primary (cost-effective), OpenAI/Claude fallback

### 📋 **14-Module Productivity Suite**
- **📝 Tasks & Notes**: Local management with AI scoring and summarization
- **📅 Calendar & Reminders**: Google Calendar integration with smart scheduling
- **📧 Email Assistant**: Gmail API with AI-powered drafting and management
- **📰 News Aggregator**: RSS feeds with AI summarization
- **💰 Finance Tracker**: Google Sheets integration for expense tracking
- **📊 Project Management**: ClickUp/Trello integration with AI task management
- **📈 Trading Analysis**: CoinGecko + TradingView with AI market insights
- **🌐 Social Media**: Multi-platform content management and posting
- **☎️ Voice Processing**: Whisper API for transcription and voice commands
- **🤖 Online Agent**: Service automation for bookings, orders, etc.

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
| **Tony** | Tech genius, sarcastic, innovative | Technical discussions |
| **Rose** | Warm, empathetic, supportive | Emotional support & guidance |

## 🚀 Quick Start

### Option 1: One-Command VPS Setup (Recommended)

For **complete VPS deployment** with all dependencies:

```bash
# Clone and setup everything automatically
git clone <repository-url>
cd ChoyAI
make vps-setup    # Installs Python, Docker, dependencies, and configures VPS
make setup        # Configure environment and API keys
make deploy       # Deploy ChoyAI with Docker
```

### Option 2: Local Development Setup

For **local development** or **existing systems**:

```bash
# Clone the repository
git clone <repository-url>
cd ChoyAI

# Setup environment and dependencies
make setup        # Sets up Python dependencies and creates .env

# Configure your API keys in .env
make setup-env    # Interactive environment configuration

# Start ChoyAI
make start        # Start with Docker
# OR
python main.py    # Run directly
```

### Option 3: Manual Installation

If you prefer manual setup:

1. **Install dependencies**
   ```bash
   make install-python    # Install Python 3.11
   make install-deps      # Install Python packages  
   make install-docker    # Install Docker (optional)
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run ChoyAI**
   ```bash
   make start      # With Docker
   # OR  
   python main.py  # Direct execution
   ```

### 📋 Quick Commands Reference

| Command | Purpose | Description |
|---------|---------|-------------|
| `make help` | 📖 Show all commands | Complete command reference |
| `make vps-setup` | 🖥️ Full VPS setup | Complete server setup |
| `make setup` | ⚙️ Configure environment | Setup dependencies and .env |
| `make deploy` | 🚀 Deploy ChoyAI | Deploy with Docker |
| `make status` | 📊 Check services | View running status |
| `make logs` | 📋 View logs | Monitor application logs |
| `make backup` | 💾 Create backup | Backup data and config |
| `make health` | 🏥 Health check | Verify system health |
| `make update` | 🔄 Update system | Pull code and restart |

### Prerequisites

**Required:**
- Telegram Bot Token (from @BotFather)
- At least one AI API Key:
  - **DeepSeek API Key** (Primary, recommended - cost-effective)
  - **OpenAI API Key** (Optional, for ChatGPT)
  - **Anthropic API Key** (Optional, for Claude)
  - **xAI API Key** (Optional, for Grok)
  - **Google AI API Key** (Optional, for Gemini)

**System Requirements:**
- Ubuntu/Debian/CentOS server (for VPS)
- 2GB+ RAM, 10GB+ storage
- Python 3.11+ (auto-installed with `make vps-setup`)
- Docker (auto-installed with `make vps-setup`)

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
│   ├── modules/                  # 14 Productivity modules
│   │   ├── memory/              # Memory management system
│   │   ├── personas/            # Multi-personality system
│   │   ├── chat/                # Chat and conversation processing
│   │   ├── productivity/        # Productivity suite modules
│   │   │   ├── tasks/           # Task and to-do management
│   │   │   ├── calendar/        # Calendar and scheduling
│   │   │   ├── notes/           # Notes and knowledge management
│   │   │   ├── finance/         # Finance and expense tracking
│   │   │   ├── email/           # Email management and drafting
│   │   │   ├── news/            # News aggregation and summarization
│   │   │   ├── social/          # Social media management
│   │   │   ├── projects/        # Project management integration
│   │   │   ├── trading/         # Trading and market analysis
│   │   │   ├── voice/           # Voice processing and STT
│   │   │   ├── messaging/       # Multi-platform messaging
│   │   │   ├── drive/           # Cloud storage management
│   │   │   ├── calls/           # Voice call processing
│   │   │   └── agent/           # Online service automation
│   │   └── users/               # User management
│   ├── integrations/            # External API integrations
│   │   ├── telegram/            # Telegram bot
│   │   ├── google/              # Google APIs (Calendar, Gmail, Sheets)
│   │   ├── openai/              # OpenAI APIs (GPT, Whisper)
│   │   ├── social_media/        # Social media APIs
│   │   └── trading/             # Trading and crypto APIs
│   ├── config/                  # Configuration
│   └── utils/                   # Utilities
├── data/                        # Data storage
│   ├── personas/               # Persona definitions
│   ├── databases/              # SQLite databases
│   ├── core_memory/            # Core memory storage
│   └── logs/                   # Log files
└── docs/                       # Documentation
```

### Core Components

- **AI Engine**: Multi-provider orchestration with cost optimization
- **Memory Managers**: 3-layer memory system (Core, User, Conversation)
- **Persona Manager**: Dynamic personality switching system
- **Productivity Modules**: 14 specialized modules for different tasks
- **Integration Layer**: Unified API management with fallback mechanisms
- **Cost Controller**: Smart usage tracking and optimization

## 🔮 ChoyAI: Cost-Effective Productivity Suite

### 💡 14 Planned Modules – Cost-Efficient Design

| Module # | Feature | API / Tool Used | Cost |
|----------|---------|-----------------|------|
| 1 | **Chat / Voice** | GPT-4o / Claude / DeepSeek | Already owned |
| 2 | **Reminders / Calendar** | Google Calendar API + GPT-4o logic | Free (low use) |
| 3 | **Tasks / To-Do** (Google Tasks) | Local DB + GPT-4o (for scoring/intent) | Free (local) |
| 4 | **Notes** (Google Keep) | Local DB + GPT-4o summarization | Free |
| 5 | **Cloud Drive** (Google Drive) | Supabase / Firebase + Vector embeddings | Free tier |
| 6 | **News** | RSS feeds + GPT-4o summarizer | Free |
| 7 | **Mail** | Gmail API + GPT-4o drafting engine | Free (limited) |
| 8 | **Messaging Hub** | Telegram Bot API / WhatsApp API | Telegram free, WhatsApp paid |
| 9 | **Call** | OpenAI Whisper API for STT | ~$0.006/min |
| 10 | **Social Media** | X, FB, IG APIs + GPT-4o content generator | Free/basic use |
| 11 | **Accounts / Finance** | Google Sheets API + GPT-4o summarizer | Free |
| 12 | **Project Management** | Trello or ClickUp API + GPT-4o task manager | Free |
| 13 | **Trading Analysis** | CoinGecko API + TradingView API + GPT-4o summarization | Free |
| 14 | **Online Agent** | Uber, Booking, etc. APIs + GPT-4o logic | Free/dev accounts |

### 🔧 Minimal External APIs (Must-Have Only)

| API | Purpose | Cost |
|-----|---------|------|
| **OpenAI Whisper** | Voice transcription | ~$0.006/min |
| **Google Calendar API** | Reminder scheduling | Free |
| **Google Sheets API** | Expense/Budget tracking | Free |
| **Supabase / Firebase** | File, task, note storage | Free tier |
| **Telegram Bot API** | Interface layer | Free |
| **CoinGecko API** | Crypto prices and updates | Free |
| **Gmail API** | Email access and automation | Free |

### 🚀 Final API Stack for ChoyAI: v1 Power Boost

| Purpose | API / Tool | Status |
|---------|------------|--------|
| **Web Search** | ✅ Serper / Perplexity | Ready |
| **Voice → Text** | ✅ Whisper API | Ready |
| **Text → Voice** | ✅ ElevenLabs or Google TTS | Ready |
| **YouTube Search** | ✅ YouTube API | Ready |
| **News** | ✅ RSS Feeds | Ready |
| **Crypto/Finance** | ✅ CoinGecko | Ready |
| **Map & Location** | ✅ Google Maps | Ready |
| **Memory** | ✅ ChromaDB + SQLite | Implemented |
| **Assistant Brain** | ✅ ChatGPT + DeepSeek | Implemented |

### 📋 Current Implementation Status

| Module | Status | Features | API Integration |
|--------|--------|----------|-----------------|
| **🧠 Core AI** | ✅ **Complete** | Multi-provider, memory, personas | DeepSeek/OpenAI/Claude |
| **� Chat/Voice** | ✅ **Complete** | Telegram bot, personality switching | Telegram Bot API |
| **🧠 Memory System** | ✅ **Complete** | 3-layer memory, semantic search | ChromaDB + SQLite |
| **🎭 Personas** | ✅ **Complete** | Multiple personalities, YAML configs | Local implementation |
| **📝 Tasks/Notes** | 🚧 **In Progress** | Local task management, AI scoring | Local DB + GPT logic |
| **� Calendar** | 📋 **Planned** | Smart scheduling, reminders | Google Calendar API |
| **📧 Email** | 📋 **Planned** | AI-powered drafting, management | Gmail API |
| **📰 News** | 📋 **Planned** | RSS aggregation, AI summarization | RSS + GPT |
| **💰 Finance** | 📋 **Planned** | Expense tracking, budget insights | Google Sheets API |
| **📊 Projects** | 📋 **Planned** | Task management, progress tracking | ClickUp/Trello API |
| **📈 Trading** | 📋 **Planned** | Market analysis, crypto tracking | CoinGecko + TradingView |
| **🌐 Social** | � **Planned** | Content management, posting | Social Media APIs |
| **☎️ Voice Calls** | 📋 **Planned** | Voice transcription, responses | Whisper API |
| **🤖 Online Agent** | 📋 **Planned** | Service automation, bookings | Various APIs |

### 🎯 Module Integration Framework

Each module follows a standardized integration pattern:

```python
class ModuleInterface:
    - OAuth/API authentication
    - Webhook support for real-time updates  
    - Unified command interface
    - Memory integration for context sharing
    - Cost-optimized API usage
    - Fallback mechanisms
```

### 💰 Cost Optimization Strategy

1. **Primary Free APIs**: Google Calendar, Sheets, Gmail, Telegram
2. **Minimal Paid APIs**: Only Whisper for voice (~$0.006/min)
3. **Local Processing**: Tasks, notes, and memory stored locally
4. **Smart Caching**: Reduce API calls with intelligent caching
5. **Batch Operations**: Group API requests to minimize costs
6. **Free Tiers**: Maximize usage of free API tiers

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

### One-Command VPS Setup (Recommended)
```bash
make vps-setup    # Complete server setup with all dependencies
make setup        # Configure environment and API keys  
make deploy       # Deploy ChoyAI with Docker
```

### Development
```bash
make setup        # Setup local environment
python main.py    # Direct execution
```

### Production with Docker
```bash
make build        # Build Docker image
make start        # Start with Docker Compose
make status       # Check deployment status
```

### Production with Enhanced Makefile
```bash
make deploy-production    # Full production deployment with backup
make health              # Comprehensive health check
make backup              # Create system backup
make update-production   # Safe production updates
```

### 📋 Post-Deployment Module Setup

After deployment, modules can be individually configured:

```bash
# Setup individual modules (when APIs are ready)
make productivity-setup   # Initialize all 14 modules
make test-modules        # Test module functionality

# Configure specific APIs in .env:
GOOGLE_CALENDAR_API_KEY=your_key    # For calendar module
GMAIL_API_KEY=your_key              # For email module  
OPENAI_API_KEY=your_key             # For voice module (Whisper)
COINGECKO_API_KEY=your_key          # For trading module (optional)
```

### 🔧 Module Activation Status

Modules activate automatically when their required APIs are configured:

| Module | Auto-Activate When | Status |
|--------|-------------------|--------|
| **Core AI** | DeepSeek/OpenAI API set | ✅ Active |
| **Memory** | Always (local storage) | ✅ Active |
| **Telegram** | TELEGRAM_BOT_TOKEN set | ✅ Active |
| **Tasks/Notes** | Always (local storage) | ✅ Active |
| **Calendar** | GOOGLE_CALENDAR_API_KEY set | 📋 Ready |
| **Email** | GMAIL_API_KEY set | 📋 Ready |
| **Voice** | OPENAI_API_KEY set | 📋 Ready |
| **Finance** | GOOGLE_SHEETS_API_KEY set | 📋 Ready |
| **News** | Always (RSS feeds) | 📋 Ready |
| **Trading** | COINGECKO_API_KEY set | 📋 Ready |
| **Social** | Social API keys set | 📋 Ready |
| **Projects** | CLICKUP/TRELLO_API_KEY set | 📋 Ready |

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

ChoyAI serves as the foundation for a **cost-effective productivity ecosystem** that maximizes value while minimizing operational costs. Our goal is to create an intelligent system that:

- **🧠 Learns and Remembers**: Builds a comprehensive understanding of each user through advanced memory systems
- **🔗 Integrates Everything**: Connects 14+ digital tools and services with unified AI intelligence
- **💰 Stays Cost-Effective**: Delivers enterprise-level functionality using free APIs and minimal paid services
- **🔒 Maintains Privacy**: All data stored locally with complete user control
- **📈 Scales Intelligently**: Grows more capable and useful over time without proportional cost increases
- **🚀 Maximizes Productivity**: Automates routine tasks across all major productivity domains

### 💡 **Cost-Effectiveness Philosophy**

ChoyAI is designed around the principle that **maximum productivity shouldn't require maximum spending**:

- ✅ **14 productivity modules** for the cost of basic AI API usage
- ✅ **90% free APIs** (Google Calendar, Sheets, Gmail, Telegram, CoinGecko, RSS)
- ✅ **10% minimal paid** (only Whisper API at ~$0.006/min)
- ✅ **Local-first storage** eliminates cloud storage costs
- ✅ **Smart caching** minimizes API calls and costs
- ✅ **Free-tier optimization** maximizes value from free API limits

---

**Built with ❤️ for cost-effective personal and business productivity**
