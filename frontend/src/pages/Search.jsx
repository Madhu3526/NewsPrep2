import React, { useState } from "react";
import { apiGet } from "../api/api";
import "./Search.css";

export default function Search() {
  const [query, setQuery] = useState("");
  const [keywordResults, setKeywordResults] = useState([]);
  const [semanticResults, setSemanticResults] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);

    try {
      // single endpoint call — returns BOTH keyword + semantic
      const res = await apiGet(`/search?q=${query}`);

      setKeywordResults(res.keyword || []);
      setSemanticResults(res.semantic || []);
    } catch (err) {
      console.error("Search error:", err);
    }

    setLoading(false);
  }

  return (
    <div className="search-page">
      <h1>Search News</h1>

      <form className="searchbox" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search anything (AI powered)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button>Search</button>
      </form>

      {loading && <p className="loading">Searching...</p>}

      {!loading && (
        <div className="results-container">

          <div className="column">
            <h2>Keyword Matches</h2>
            {keywordResults.map((item, idx) => (
              <div className="result-card" key={idx}>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <small>Source: {item.source}</small>
              </div>
            ))}
          </div>

          <div className="column">
            <h2>AI Semantic Matches</h2>
            {semanticResults.map((item, idx) => (
              <div className="result-card" key={idx}>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <small>Score: {item.score}</small>
              </div>
            ))}
          </div>

        </div>
      )}
    </div>
  );
}
