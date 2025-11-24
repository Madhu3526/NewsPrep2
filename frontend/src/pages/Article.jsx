// frontend/src/pages/Article.jsx
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { getArticle, summarizeArticle } from "../api/api";
import axios from "axios";

export default function ArticlePage() {
  const { id } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summarizing, setSummarizing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await getArticle(id);
        setArticle(res.data);
      } catch (e) {
        console.error(e);
        alert("Failed to load article");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleSummarize = async (useAbstractive = true) => {
    setSummarizing(true);
    try {
      const res = await summarizeArticle(Number(id), useAbstractive);
      // After summarization, fetch article again to show saved summary
      const fresh = await getArticle(id);
      setArticle(fresh.data);
    } catch (e) {
      console.error(e);
      alert("Summarization failed");
    } finally {
      setSummarizing(false);
    }
  };

  if (loading) return <div className="container"><p>Loading...</p></div>;
  if (!article) return <div className="container"><p>Article not found</p></div>;

  return (
    <div className="container">
      <h2>{article.title || `Article ${article.id}`}</h2>
      <div style={{whiteSpace:"pre-wrap", marginTop: "1rem"}}>{article.text}</div>

      <div style={{marginTop: "2rem"}}>
        <button onClick={() => handleSummarize(true)} disabled={summarizing}>
          {summarizing ? "Summarizing..." : "Generate abstractive summary (Llama3.1)"}
        </button>
        <button onClick={() => handleSummarize(false)} disabled={summarizing} style={{marginLeft: "0.5rem"}}>
          {summarizing ? "..." : "Quick extractive summary"}
        </button>
      </div>

      {article.summary && (
        <div className="output" style={{marginTop:"2rem"}}>
          <h3>Summary</h3>
          <p>{article.summary}</p>

          {article.key_points && article.key_points.length > 0 && (
            <>
              <h4>Key points</h4>
              <ul>
                {article.key_points.map((kp, idx) => <li key={idx}>{kp}</li>)}
              </ul>
            </>
          )}
        </div>
      )}
      <div style={{marginTop: "1rem"}}>
        <button
          onClick={() =>
            axios
              .post(`http://localhost:8000/api/quiz/${id}`)
              .then(res => {
                const qid = res.data.quiz_id;
                window.location.href = `/quiz/${qid}`;
              })
              .catch(() => alert("Quiz generation failed"))
          }
          style={{background: "#6f42c1", color: "white", padding: "0.5rem 1rem", border: "none", borderRadius: "4px", cursor: "pointer"}}
        >
          🧠 Generate Quiz
        </button>
      </div>

    </div>
  );
}
