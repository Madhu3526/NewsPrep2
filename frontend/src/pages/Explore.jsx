import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet } from "../api/api";
import RecommendationPanel from "../components/RecommendationPanel";
import axios from "axios";
import "./Explore.css";

export default function Explore() {
  const { id } = useParams();
  const [topicInfo, setTopicInfo] = useState(null);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summaries, setSummaries] = useState({});
  const [summarizing, setSummarizing] = useState({});

  function safeHTML(text) {
    if (!text) return "No content";
    return text.replace(/<[^>]+>/g, ""); // remove HTML tags
  }

  async function handleSummarize(text, articleIdx, type) {
    if (!text) return;
    
    setSummarizing(prev => ({ ...prev, [articleIdx]: type }));
    
    try {
      const response = await apiGet(`/summarize?text=${encodeURIComponent(text)}&type=${type}`);
      setSummaries(prev => ({ 
        ...prev, 
        [articleIdx]: {
          ...prev[articleIdx],
          [type]: response.summary
        }
      }));
    } catch (err) {
      console.error("Error summarizing:", err);
      setSummaries(prev => ({ 
        ...prev, 
        [articleIdx]: {
          ...prev[articleIdx],
          [type]: "Error generating summary"
        }
      }));
    }
    
    setSummarizing(prev => ({ ...prev, [articleIdx]: false }));
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

  useEffect(() => {
    async function loadData() {
      try {
        const topicRes = await apiGet(`/topics/${id}`);
        // backend provides representative docs at /api/topics/{id}/example
        const docsRes = await apiGet(`/topics/${id}/example?n=15`);

        setTopicInfo(topicRes);
        // docsRes is either a list (example_articles route) or an object with docs
        setArticles(Array.isArray(docsRes) ? docsRes : docsRes.docs || []);
      } catch (err) {
        console.error("Error loading topic:", err);
      }
      setLoading(false);
    }

    loadData();
  }, [id]);

  if (loading) return <p className="loading">Loading topic…</p>;
  if (!topicInfo) return <p className="error">Topic not found or server error.</p>;

  return (
    <div className="explore-container">
      <h1>Topic #{id}</h1>
      <h2 className="topic-name">{topicInfo.name || topicInfo.Name}</h2>

      <div className="keywords-box">
        {(topicInfo.keywords || topicInfo.Representation || []).slice(0, 8).map((k, idx) => (
          <span className="keyword" key={idx}>
            {k}
          </span>
        ))}
      </div>

      <h3 className="subheading">Representative Articles</h3>

      <div className="articles-list">
        {articles.map((a, idx) => (
          <div className="article-card" key={idx}>
            <h4>{a.title || "Untitled Article"}</h4>

            <div className="article-content">
              <div className="full-text">
                <h5>📰 Full Article:</h5>
                <p>{safeHTML(a.text)}</p>
              </div>
            </div>

            <div className="meta">
              <span>Source: {a.source || "unknown"}</span>
            </div>

            <div className="article-actions">
              {a.url && (
                <a className="readmore" href={a.url} target="_blank">
                  Read Full Article →
                </a>
              )}
              <button 
                className="summarize-btn extractive"
                onClick={() => handleSummarize(a.text, idx, 'extractive')}
                disabled={summarizing[idx]}
              >
                {summarizing[idx] === 'extractive' ? '⏳ Extracting...' : '📄 Extractive'}
              </button>
              <button 
                className="summarize-btn abstractive"
                onClick={() => handleSummarize(a.text, idx, 'abstractive')}
                disabled={summarizing[idx]}
              >
                {summarizing[idx] === 'abstractive' ? '⏳ Abstracting...' : '🤖 Abstractive'}
              </button>
              <button 
                className="quiz-btn"
                onClick={() => generateQuiz(a.id || idx)}
              >
                🧠 Quiz
              </button>
            </div>
            
            {summaries[idx]?.extractive && (
              <div className="summary-box extractive">
                <h5>📄 Extractive Summary:</h5>
                <p>{summaries[idx].extractive}</p>
              </div>
            )}
            
            {summaries[idx]?.abstractive && (
              <div className="summary-box abstractive">
                <h5>🤖 Abstractive Summary:</h5>
                <p>{summaries[idx].abstractive}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      <RecommendationPanel seedType="topic" seedId={id} limit={6} />
    </div>
  );
}
