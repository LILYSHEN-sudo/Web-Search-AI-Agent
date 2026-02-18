import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

interface QueryResult {
  question: string
  answer: string
  usedSearch: boolean
  timestamp: Date
}

const API_URL = import.meta.env.VITE_API_URL || ''

function App() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [usedSearch, setUsedSearch] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<QueryResult[]>([])
  const [useWebSearch, setUseWebSearch] = useState(true)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedQuery = query.trim()
    if (!trimmedQuery) return

    setLoading(true)
    setError('')
    setAnswer('')

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: trimmedQuery,
          use_web_search: useWebSearch,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Request failed with status ${response.status}`)
      }

      const data = await response.json()
      setAnswer(data.answer)
      setUsedSearch(data.used_search)

      // Add to history (keep last 5)
      setHistory((prev) => [
        {
          question: trimmedQuery,
          answer: data.answer,
          usedSearch: data.used_search,
          timestamp: new Date(),
        },
        ...prev.slice(0, 4),
      ])

      setQuery('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleHistoryClick = (item: QueryResult) => {
    setAnswer(item.answer)
    setUsedSearch(item.usedSearch)
    setError('')
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Deep Research Agent</h1>
        <p className="subtitle">Ask questions and get AI-powered answers with web search</p>
      </header>

      <div className="options-container">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={useWebSearch}
            onChange={(e) => setUseWebSearch(e.target.checked)}
            disabled={loading}
          />
          <span className="checkbox-custom"></span>
          <span className="checkbox-text">
            <strong>Web Search</strong>
            <span className="checkbox-description">
              Search the web for current information (uses BrightData)
            </span>
          </span>
        </label>
      </div>

      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="search-input"
          disabled={loading}
        />
        <button type="submit" className="search-button" disabled={loading || !query.trim()}>
          {loading ? 'Searching...' : 'Ask'}
        </button>
      </form>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>{useWebSearch ? 'Researching your question...' : 'Generating answer...'}</p>
        </div>
      )}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {answer && !loading && (
        <div className="answer-container">
          <div className="answer-header">
            <h2>Answer</h2>
            {usedSearch && <span className="search-badge">Web Search Used</span>}
          </div>
          <div className="answer-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="history-container">
          <h3>Recent Questions</h3>
          <ul className="history-list">
            {history.map((item, index) => (
              <li key={index} className="history-item" onClick={() => handleHistoryClick(item)}>
                <span className="history-question">{item.question}</span>
                <span className="history-time">
                  {item.timestamp.toLocaleTimeString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default App
