import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api/api";

export default function ArticleList() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
  // request the collection with a trailing slash to avoid server redirect
  const data = await apiGet("/articles/");
        setArticles(data);
      } catch (e) {
        console.error(e);
        alert("Failed to load articles");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="container"><p>Loading...</p></div>;
  if (!articles.length) return <div className="container"><p>No articles found</p></div>;

  return (
    <div className="container">
      <h2>Articles</h2>
      <ul>
        {articles.map(a => (
          <li key={a.id}>
            <Link to={`/articles/${a.id}`}>{a.title || `Article ${a.id}`}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}