import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import './Quiz.css';

export default function QuizPage() {
  const { quiz_id } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    axios.get(`http://localhost:8001/api/quiz/${quiz_id}`)
      .then(res => setQuiz(res.data))
      .catch(() => alert("Error loading quiz"));
  }, [quiz_id]);

  const handleAnswer = (questionId, answerIndex) => {
    setAnswers({ ...answers, [questionId]: answerIndex });
  };

  const nextQuestion = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const submitQuiz = () => {
    let correctAnswers = 0;
    quiz.questions.forEach(q => {
      if (answers[q.id] === q.correct) {
        correctAnswers++;
      }
    });
    setScore(correctAnswers);
    setSubmitted(true);
    setShowResults(true);
  };

  const resetQuiz = () => {
    setAnswers({});
    setSubmitted(false);
    setCurrentQuestion(0);
    setScore(0);
    setShowResults(false);
  };

  if (!quiz) {
    return (
      <div className="quiz-container">
        <div className="loading-quiz">
          <div className="quiz-spinner"></div>
          <p>Loading your quiz...</p>
        </div>
      </div>
    );
  }

  if (showResults) {
    const percentage = Math.round((score / quiz.questions.length) * 100);
    return (
      <div className="quiz-container">
        <div className="quiz-results">
          <div className="results-header">
            <div className="score-circle">
              <span className="score-number">{percentage}%</span>
            </div>
            <h2>Quiz Complete!</h2>
            <p className="score-text">
              You scored {score} out of {quiz.questions.length} questions correctly
            </p>
          </div>
          
          <div className="results-breakdown">
            {quiz.questions.map((q, idx) => (
              <div key={q.id} className={`result-item ${
                answers[q.id] === q.correct ? 'correct' : 'incorrect'
              }`}>
                <div className="result-icon">
                  {answers[q.id] === q.correct ? '✅' : '❌'}
                </div>
                <div className="result-content">
                  <h4>Question {idx + 1}</h4>
                  <p className="question-text">{q.question}</p>
                  <p className="correct-answer">
                    <strong>Correct:</strong> {q.options[q.correct]}
                  </p>
                  {answers[q.id] !== q.correct && (
                    <p className="your-answer">
                      <strong>Your answer:</strong> {q.options[answers[q.id]] || 'Not answered'}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="results-actions">
            <button className="btn-primary" onClick={resetQuiz}>
              Retake Quiz
            </button>
            <button className="btn-secondary" onClick={() => navigate(-1)}>
              Back to Article
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQ = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;
  const allAnswered = quiz.questions.every(q => answers[q.id] !== undefined);

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <h1>{quiz.title}</h1>
        <div className="quiz-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <span className="progress-text">
            Question {currentQuestion + 1} of {quiz.questions.length}
          </span>
        </div>
      </div>

      <div className="quiz-content">
        <div className="question-card">
          <div className="question-header">
            <span className="question-number">Q{currentQuestion + 1}</span>
            <h3 className="question-text">{currentQ.question}</h3>
          </div>

          <div className="options-container">
            {currentQ.options.map((option, index) => (
              <label 
                key={index} 
                className={`option-label ${
                  answers[currentQ.id] === index ? 'selected' : ''
                }`}
              >
                <input
                  type="radio"
                  name={`q-${currentQ.id}`}
                  checked={answers[currentQ.id] === index}
                  onChange={() => handleAnswer(currentQ.id, index)}
                  className="option-input"
                />
                <div className="option-content">
                  <span className="option-letter">{String.fromCharCode(65 + index)}</span>
                  <span className="option-text">{option}</span>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="quiz-navigation">
          <button 
            className="btn-nav" 
            onClick={prevQuestion}
            disabled={currentQuestion === 0}
          >
            ← Previous
          </button>
          
          <div className="nav-center">
            {currentQuestion === quiz.questions.length - 1 ? (
              <button 
                className="btn-submit" 
                onClick={submitQuiz}
                disabled={!allAnswered}
              >
                Submit Quiz
              </button>
            ) : (
              <button 
                className="btn-nav" 
                onClick={nextQuestion}
                disabled={answers[currentQ.id] === undefined}
              >
                Next →
              </button>
            )}
          </div>
          
          <div className="answered-count">
            {Object.keys(answers).length}/{quiz.questions.length} answered
          </div>
        </div>
      </div>
    </div>
  );
}
