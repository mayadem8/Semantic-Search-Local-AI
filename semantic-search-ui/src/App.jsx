import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [maxDistance, setMaxDistance] = useState(1.0); // default to 1.0


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
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="distance" style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#007BFF' }}>
          Max Distance: {maxDistance}
        </label>
        <input
          type="range"
          id="distance"
          min="0"
          max="2"
          step="0.01"
          value={maxDistance}
          onChange={(e) => setMaxDistance(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: '#007BFF', backgroundColor: '#333' }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#666' }}>
          {[0.0, 0.5, 1.0, 1.5, 2.0].map((tick) => (
            <span key={tick}>{tick.toFixed(1)}</span>
          ))}
        </div>
      </div>

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
        {results.filter(result => result.distance <= maxDistance).map((result, index) => (

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
            
             {result.step_name && (
      <div style={{ marginTop: '20px', fontSize: '0.8rem', color: '#888' }}>
           <strong>{result.step_name}</strong>
        <div style={{ marginTop: '2px' }}>{result.step_description}</div>
      </div>
    )}
            <p style={{ color: '#000' }}>
  🔎 Distance: {result.distance.toFixed(3)}
</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
