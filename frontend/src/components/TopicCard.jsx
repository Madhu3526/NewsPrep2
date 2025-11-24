
export function TopicCard({ topic, onOpen }) {
  if (!topic) return null;

  // Accept backend shape: { topic_id, name, count, keywords }
  const id = topic.topic_id ?? topic.Topic;
  const name = topic.name ?? topic.Name;
  const count = topic.count ?? topic.Count;
  const keywords = topic.keywords ?? topic.Representation ?? [];

  return (
    <div className="topic-card" onClick={() => onOpen(id)}>
      <div className="topic-id">#{id}</div>

      <h3>{name || `Topic ${id}`}</h3>

      <div className="topic-count">{count ?? 0} articles</div>

      <div className="topic-words">
        {keywords?.slice(0, 5).map((word, idx) => (
          <span className="kw" key={`${id}-${idx}`}>
            {word}
          </span>
        ))}
      </div>
    </div>
  );
}
