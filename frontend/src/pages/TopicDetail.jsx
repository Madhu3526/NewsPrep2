import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

export default function TopicDetail() {
  const { id } = useParams();
  const [topic, setTopic] = useState(null);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  function safeHTML(text) {
    if (!text) return "No content";
    return text.replace(/<[^>]+>/g, "");
  }

  useEffect(() => {
    async function loadData() {
      try {
        const topicRes = await axios.get(`http://localhost:8000/api/topics/${id}`);
        const docsRes = await axios.get(`http://localhost:8000/api/topics/${id}/docs`);

        setTopic(topicRes.data);
        setDocs(docsRes.data.docs || []);
      } catch (err) {
        console.error("Topic load error:", err);
      }
      setLoading(false);
    }

    loadData();
  }, [id]);

  if (loading) return <p className="loading">Loading...</p>;
  if (!topic) return <p className="error">Topic not found.</p>;

  return (
    <div className="page">
      <h1>Topic #{topic.Topic}</h1>
      <h2>{topic.Name}</h2>

      <div className="topic-words">
        {topic.Representation.slice(0, 10).map((k, idx) => (
          <span className="kw" key={idx}>
            {k}
          </span>
        ))}
      </div>

      <h3>Articles</h3>

      {docs.map((d, idx) => (
        <div className="doc-item" key={idx}>
          <h3>{d.title || "Untitled Article"}</h3>

          <div
            className="excerpt"
            dangerouslySetInnerHTML={{
              __html: safeHTML(d.text).slice(0, 400) + "..."
            }}
          />

          <small>Source: {d.source}</small>
          {d.url && (
            <div>
              <a href={d.url} target="_blank">
                Read more →
              </a>
            </div>
          )}
        </div>
      ))}

      <Link to="/">← Back to Topics</Link>
    </div>
  );
}
