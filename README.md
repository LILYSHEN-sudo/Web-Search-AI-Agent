# Web Search AI Agent
This is a full-stack application with a Python FastAPI backend and React frontend that can search the web and provide intelligent answers to your questions.
The agent uses an LLM to decide when web search is needed, extracts search queries, fetches real-time results via BrightData's SERP API, and synthesizes comprehensive answers using the RAG (Retrieval-Augmented Generation) pattern.

The application includes a user-controlled "Web Search" checkbox that lets you toggle between:
- **Enabled**: Agent searches the web using BrightData and synthesizes information
- **Disabled**: Agent relies only on the LLM model's knowledge without web search

## Features
- ✅ Python async programming with FastAPI
- ✅ React frontend with TypeScript
- ✅ OpenAI-compatible API integration
- ✅ Web scraping with BrightData
- ✅ AI Agent architecture (ReAct pattern)
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ User-controlled feature toggles
- ✅ Full-stack development with AI assistance

## How to Launch this project
Step1: Configure Environment Variables
Edit `services/backend/.env` with your actual API keys:
```
BRIGHTDATA_API_TOKEN=your-actual-brightdata-token
ZEABUR_API_TOKEN=your-actual-zeabur-token
ZEABUR_MODEL=gpt-4o-mini
PORT=8000
```

Step3:  Install Dependencies
```
# Install all dependencies
make install

# Or install separately:
cd services/backend && pip3 install -r requirements.txt
cd services/frontend && npm install
```

Step3:  Start the Backend  
`cd services/backend && python3 main.py`

Step4: Start the Frontend  
`cd services/frontend && npm run dev`

Step 5: Test the Application  
[http://localhost:5173](http://localhost:5173/)
