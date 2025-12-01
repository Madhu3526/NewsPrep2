import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/api";
import axios from "axios";

export default function RecommendationPanel({ seedType = "topic", seedId, limit = 6 }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summaries, setSummaries] = useState({});
  const [summarizing, setSummarizing] = useState({});

  useEffect(() => {
    if (!seedId) return;
    async function load() {
      setLoading(true);
        try {
        let path;
        if (seedType === "article") {
          path = `/recommend/hybrid/article/${seedId}?n=${limit}`;
        } else {
          path = `/recommend/topic/${seedId}?n=${limit}`;
        }
        const data = await apiGet(path);
        setItems(data || []);
      } catch (e) {
        console.error("Error loading recommendations", e);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [seedType, seedId, limit]);

  async function handleSummarize(text, itemId, type) {
    if (!text) return;
    
    setSummarizing(prev => ({ ...prev, [itemId]: type }));
    
    try {
      const response = await apiGet(`/summarize?text=${encodeURIComponent(text)}&type=${type}`);
      setSummaries(prev => ({ 
        ...prev, 
        [itemId]: {
          ...prev[itemId],
          [type]: response.summary
        }
      }));
    } catch (err) {
      console.error("Error summarizing:", err);
      setSummaries(prev => ({ 
        ...prev, 
        [itemId]: {
          ...prev[itemId],
          [type]: "Error generating summary"
        }
      }));
    }
    
    setSummarizing(prev => ({ ...prev, [itemId]: false }));
  }

  function generateQuiz(articleId) {
    axios
      .post(`http://localhost:8000/api/quiz/${articleId}`)
      .then(res => {
        const qid = res.data.quiz_id;
        window.location.href = `/quiz/${qid}`;
      })
      .catch(() => alert("Quiz generation failed"));
  }

  async function handleCardClick(item) {
    // fire-and-forget: log click event
    try {
      await apiPost(`/events/`, {
        user_id: null,
        event: "click_recommendation",
        item_id: item.id,
        context: { seedType, seedId }
      });
    } catch (e) {
      console.error("Failed to log event", e);
    }
  }

  if (!seedId) return null;

  return (
    <div className="recommend-panel">
      <div className="recommend-header">
        <h3>✨ Recommended for you</h3>
        <p className="recommend-subtitle">Discover articles tailored to your interests</p>
      </div>
      {loading ? (
        <div className="loading">Loading recommendations...</div>
      ) : (
        <div className="rec-grid">
          {items.map((it) => (
            <div className="rec-card" key={it.id}>
              <div 
                className="rec-card-content"
                onClick={() => handleCardClick(it)}
                style={{ cursor: "pointer" }}
              >
                <h4>{it.title || "Untitled"}</h4>
                <p className="excerpt">{it.excerpt ? it.excerpt.slice(0, 150) + "..." : ""}</p>
                <div className="meta">📊 Score: {it.score?.toFixed(3)}</div>
              </div>
              
              <div className="rec-actions">
                <button 
                  className="rec-btn summarize-btn extractive"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSummarize(it.excerpt || it.title, it.id, 'extractive');
                  }}
                  disabled={summarizing[it.id]}
                  title="Generate extractive summary"
                >
                  {summarizing[it.id] === 'extractive' ? '⏳' : '📄'}
                </button>
                <button 
                  className="rec-btn summarize-btn abstractive"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSummarize(it.excerpt || it.title, it.id, 'abstractive');
                  }}
                  disabled={summarizing[it.id]}
                  title="Generate abstractive summary"
                >
                  {summarizing[it.id] === 'abstractive' ? '⏳' : '🤖'}
                </button>
                <button 
                  className="rec-btn quiz-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    generateQuiz(it.id);
                  }}
                  title="Generate quiz"
                >
                  🧠
                </button>
              </div>
              
              {summaries[it.id]?.extractive && (
                <div className="summary-box extractive">
                  <h5>📄 Extractive Summary:</h5>
                  <p>{summaries[it.id].extractive}</p>
                </div>
              )}
              
              {summaries[it.id]?.abstractive && (
                <div className="summary-box abstractive">
                  <h5>🤖 Abstractive Summary:</h5>
                  <p>{summaries[it.id].abstractive}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
