import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

export default function QuizPage() {
  const { quiz_id } = useParams();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    axios.get(`http://localhost:8000/api/quiz/${quiz_id}`)
      .then(res => setQuiz(res.data))
      .catch(() => alert("Error loading quiz"));
  }, [quiz_id]);

  const submitQuiz = () => {
    setSubmitted(true);
  };

  if (!quiz) return <div>Loading quiz...</div>;

  return (
    <div className="container">
      <h2>{quiz.title}</h2>

      {quiz.questions.map((q, idx) => (
        <div key={q.id} className="question-card">
          <p><strong>{idx + 1}. {q.question}</strong></p>

          {q.options.map((opt, i) => (
            <label key={i} style={{ display: "block" }}>
              <input
                type="radio"
                name={`q-${q.id}`}
                disabled={submitted}
                onChange={() =>
                  setAnswers({ ...answers, [q.id]: i })
                }
              />
              {opt}
            </label>
          ))}

          {submitted && (
            <p style={{ 
              color: answers[q.id] === q.correct ? "green" : "red" 
            }}>
              {answers[q.id] === q.correct ? "✅ Correct!" : "❌ Wrong!"} 
              Correct answer: {q.options[q.correct]}
            </p>
          )}
        </div>
      ))}

      {!submitted && (
        <button onClick={submitQuiz}>Submit</button>
      )}
    </div>
  );
}
