import { useState } from "react";
import { processArticle } from "../services/api";
import Loader from "../components/Loader";

function Home() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!text.trim()) return alert("Please paste an article first.");
    setLoading(true);
    try {
      const res = await processArticle(text);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <h2>Paste an article to summarize and generate a quiz</h2>
      <textarea
        rows="10"
        placeholder="Paste article text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      ></textarea>
      <button onClick={handleSubmit}>Summarize</button>

      {loading && <Loader />}

      {result && (
        <div className="output">
          <h3>Summary</h3>
          <p>{result.summary_raw}</p>
          <h3>Quiz</h3>
          <pre>{result.quiz_raw}</pre>
        </div>
      )}
    </div>
  );
}

export default Home;
