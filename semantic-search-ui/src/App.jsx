import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    console.log('Searching for:', query);
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
    </div>
  );
}

export default App;
