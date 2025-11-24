import { useState } from "react";
import axios from "axios";

export default function AskPage() {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/ask", { query });
      setAnswer(res.data.answer);
      setSources(res.data.sources);
    } catch {
      alert("Error processing question");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2>Ask the News</h2>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask something about the news..."
        style={{ width: "80%", padding: "0.5rem" }}
      />

      <button onClick={ask} disabled={loading}>
        {loading ? "Thinking..." : "Ask"}
      </button>

      {answer && (
        <>
          <h3>Answer</h3>
          <p>{answer}</p>

          <h4>Sources</h4>
          <ul>
            {sources.map((s, i) => (
              <li key={i}>
                <strong>{s.title}</strong><br />
                {s.snippet}<br />
                <em>{s.published}</em>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
