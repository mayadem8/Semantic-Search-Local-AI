import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      const response = await fetch('http://127.0.0.1:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      setResults(data.slice(0, 3)); // Show only top 3 results
    } catch (error) {
      console.error("❌ Search failed:", error);
    }
  };

  return (
    <div className="app-container">
      <form onSubmit={handleSearch} className="search-box">
        <input
          type="text"
          placeholder="Type to search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <div style={{
        marginTop: '10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        maxWidth: '600px',
      }}>
        {results.map((result, index) => (
          <div
            key={index}
            style={{
              background: '#f9f9f9',
              borderRadius: '6px',
              padding: '10px 15px',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              transition: 'background 0.2s',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = '#f0f0f0'}
            onMouseLeave={(e) => e.currentTarget.style.background = '#f9f9f9'}
          >
            <h4 style={{ margin: '0 0 5px', fontSize: '1rem', color: '#333' }}>{result.name}</h4>
            <p style={{ margin: '0', fontSize: '0.9rem', color: '#666' }}>{result.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
