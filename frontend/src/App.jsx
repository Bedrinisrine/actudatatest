import { useState } from 'react'

/**
 * Simple React frontend for multi-tenant document search.
 * 
 * Key security principle: The tenant is identified ONLY via the X-API-KEY header.
 * The tenant selection NEVER appears in the request body - this ensures
 * server-side control over tenant resolution and prevents client manipulation.
 */

function App() {
  // Client selection state - maps to API keys
  const [client, setClient] = useState('A')
  
  // Question/query input
  const [question, setQuestion] = useState('')
  
  // Response state
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // API key mapping - client selection determines which key to use
  // This is the ONLY place where client affects the API call
  const API_KEYS = {
    'A': 'tenantA_key',
    'B': 'tenantB_key'
  }

  // Backend API URL
  const API_URL = 'http://localhost:8000/search'

  /**
   * Handle form submission.
   * 
   * Critical: The tenant is sent ONLY in the X-API-KEY header.
   * The request body contains ONLY the query string.
   * This ensures the server has full control over tenant resolution.
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Reset previous results
    setAnswer('')
    setSources([])
    setError('')
    setLoading(true)

    try {
      // Get the API key for the selected client
      const apiKey = API_KEYS[client]
      
      // Make the API call
      // IMPORTANT: Tenant is ONLY in the header, NEVER in the body
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': apiKey  // Tenant identification via header only
        },
        body: JSON.stringify({
          query: question  // Body contains ONLY the query, no tenant info
        })
      })

      // Handle HTTP errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      
      // Display the response
      setAnswer(data.answer || '')
      setSources(data.sources || [])
      
      // Clear error if request succeeded
      setError('')
      
    } catch (err) {
      // Display error message clearly
      setError(err.message || 'An error occurred')
      setAnswer('')
      setSources([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '50px auto', 
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>
        Document Search
      </h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: '30px' }}>
        {/* Client selector - affects ONLY the X-API-KEY header */}
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="client" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Client:
          </label>
          <select
            id="client"
            value={client}
            onChange={(e) => setClient(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              fontSize: '16px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          >
            <option value="A">Client A</option>
            <option value="B">Client B</option>
          </select>
          <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
            This selection determines the API key sent in the X-API-KEY header
          </small>
        </div>

        {/* Question input */}
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="question" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Question:
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your question here..."
            rows="4"
            required
            style={{
              width: '100%',
              padding: '8px',
              fontSize: '16px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontFamily: 'inherit',
              resize: 'vertical'
            }}
          />
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading || !question.trim()}
          style={{
            width: '100%',
            padding: '12px',
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* Error display */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results display */}
      {(answer || sources.length > 0) && (
        <div style={{
          padding: '20px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '4px'
        }}>
          <h2 style={{ marginTop: '0', marginBottom: '15px' }}>Answer:</h2>
          <p style={{ 
            marginBottom: '20px', 
            lineHeight: '1.6',
            whiteSpace: 'pre-wrap'
          }}>
            {answer}
          </p>

          {sources.length > 0 && (
            <div>
              <h3 style={{ marginBottom: '10px' }}>Sources:</h3>
              <ul style={{ margin: '0', paddingLeft: '20px' }}>
                {sources.map((source, index) => (
                  <li key={index} style={{ marginBottom: '5px' }}>{source}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* No answer case - explicit handling */}
      {answer === 'Aucune information disponible pour ce client' && sources.length === 0 && !error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#fff3cd',
          color: '#856404',
          border: '1px solid #ffeaa7',
          borderRadius: '4px',
          textAlign: 'center'
        }}>
          <strong>No answer available</strong>
          <p style={{ margin: '10px 0 0 0' }}>
            Aucune information disponible pour ce client
          </p>
        </div>
      )}
    </div>
  )
}

export default App

