import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "../api/api";

import { TopicCard } from "../components/TopicCard";

export default function TopicList() {
  const [topics, setTopics] = useState([]);
  const [filtered, setFiltered] = useState(null);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await apiGet("/topics");
        setTopics(data);
      } catch (e) {
        console.error("Error fetching topics", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // CHANGE THIS → send to Explore page
  const openTopic = (id) => navigate(`/explore/${id}`);

  function handleSearch(q) {
    if (!q.trim()) return setFiltered(null);
    const ql = q.toLowerCase();
    setFiltered(
      topics.filter(
        (t) => {
          const name = (t.name || t.Name || "").toLowerCase();
          const repr = (t.keywords || t.Representation || []).join(" ").toLowerCase();
          return name.includes(ql) || repr.includes(ql);
        }
      )
    );
  }

  const show = filtered || topics;

  return (
    <div className="page">
      <h1>Topics</h1>

      {loading ? (
        <div className="loading">Loading topics...</div>
      ) : (
        <div className="topic-grid">
          {show.map((topic) => (
            <TopicCard key={topic.topic_id ?? topic.Topic} topic={topic} onOpen={openTopic} />
          ))}
        </div>
      )}
    </div>
  );
}
