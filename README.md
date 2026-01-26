# DQ Agent 🤖

AI-powered Data Quality validation agent with intelligent rule generation and multi-turn conversations.

## ✨ Features

- **🤖 AI Rule Generation** - LLM automatically suggests DQ rules based on your dataset
- **💬 Multi-turn Conversations** - Thread-based state management for interactive validation
- **✏️ Rule Management** - Edit and delete rules with inline editing
- **🎨 Modern UI** - Clean chat interface with light theme
- **⚡ Real-time Streaming** - Server-sent events for live progress updates
- **🏷️ Source Tracking** - Distinguish between user-provided and AI-generated rules

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

### Installation

1. **Clone the repository**

```bash
git clone git@github.com:aroy1856/DQ_agent.git
cd DQ_agent
```

2. **Backend Setup**

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

3. **Frontend Setup**

```bash
cd ../frontend
npm install
```

### Running the Application

**Terminal 1 - Backend:**

```bash
cd backend
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## 📖 How It Works

### 1. Upload Your Data

Upload a CSV file with optional DQ rules. If you don't provide rules, the AI will generate suggestions automatically.

### 2. Review AI Suggestions

The system analyzes your dataset and suggests relevant rules based on:

- Column names (e.g., "email" → email format validation)
- Data types (numeric → range checks)
- Sample data patterns

### 3. Edit & Customize

- ✏️ Edit any rule with inline editing
- 🗑️ Delete rules you don't need
- 👤 User rules vs 🤖 AI suggestions are clearly tagged

### 4. Validate

Click "Proceed" to generate validation code and execute checks. Results are streamed in real-time.

## 🏗️ Architecture

```
DQ_agent/
├── backend/                    # FastAPI + LangGraph
│   ├── src/dq_agent/
│   │   ├── nodes/             # LangGraph nodes
│   │   │   ├── load_data.py
│   │   │   ├── rule_generator.py    # AI rule generation
│   │   │   ├── code_generator.py    # LLM code generation
│   │   │   ├── code_executor.py
│   │   │   └── result_formatter.py
│   │   ├── state.py           # State schema
│   │   └── thread_manager.py  # Multi-turn state management
│   └── api.py                 # FastAPI endpoints
└── frontend/                   # React + TypeScript
    └── src/
        ├── components/        # UI components
        ├── hooks/            # Custom hooks
        └── types.ts          # TypeScript types
```

## 🔌 API Endpoints

| Endpoint                  | Method | Description                      |
| ------------------------- | ------ | -------------------------------- |
| `/thread/create`          | POST   | Create a new conversation thread |
| `/thread/{id}/load-rules` | POST   | Load CSV and generate AI rules   |
| `/thread/{id}/rules`      | PUT    | Update rules (edit/delete)       |
| `/thread/{id}/confirm`    | POST   | Execute validation (streaming)   |
| `/thread/{id}`            | GET    | Get thread status                |
| `/thread/{id}`            | DELETE | Delete thread                    |

## 🛠️ Tech Stack

**Backend:**

- FastAPI - Web framework
- LangGraph - Agent orchestration
- LangChain - LLM integration
- OpenAI GPT-4 - Code & rule generation
- Pandas - Data processing

**Frontend:**

- React 18 - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Tailwind CSS - Styling

## 📝 Example Rules

**User-provided:**

- Check that the 'email' column contains valid email formats
- Ensure 'age' column values are between 0 and 120

**AI-generated:**

- Verify 'amount' column has no negative values
- Check for null or empty values in 'id' column
- Ensure 'name' column has no leading or trailing spaces

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with [LangGraph](https://github.com/langchain-ai/langgraph) and [FastAPI](https://fastapi.tiangolo.com/)
