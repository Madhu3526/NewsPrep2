import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/api";

export default function RecommendationPanel({ seedType = "topic", seedId, limit = 6 }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

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

  if (!seedId) return null;

  return (
    <div className="recommend-panel">
      <h3>Recommended for you</h3>
      {loading ? (
        <div className="loading">Loading recommendations...</div>
      ) : (
        <div className="rec-grid">
          {items.map((it) => (
            <div
              className="rec-card"
              key={it.id}
              onClick={async () => {
                // fire-and-forget: log click event
                try {
                  await apiPost(`/events/`, {
                    user_id: null,
                    event: "click_recommendation",
                    item_id: it.id,
                    context: { seedType, seedId }
                  });
                } catch (e) {
                  console.error("Failed to log event", e);
                }
              }}
              style={{ cursor: "pointer" }}
            >
              <h4>{it.title || "Untitled"}</h4>
              <p className="excerpt">{it.excerpt ? it.excerpt.slice(0, 200) + "..." : ""}</p>
              <div className="meta">Score: {it.score?.toFixed(3)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
