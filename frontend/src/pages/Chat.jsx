import { useState, useRef, useEffect } from "react";
import axios from "axios";
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      type: "bot",
      text: "Hello! I'm your News Assistant. I can help you find information about current events, analyze news topics, and answer questions about articles. What would you like to know?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { 
      type: "user", 
      text: input.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input.trim();
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8001/api/ask", {
        query: currentInput
      });

      const botMessage = {
        type: "bot",
        text: res.data.answer || "I couldn't find a specific answer to your question.",
        sources: res.data.sources || [],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: "bot",
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        type: "bot",
        text: "Chat cleared! How can I help you with the news today?",
        timestamp: new Date()
      }
    ]);
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const suggestedQuestions = [
    "What are the latest news topics?",
    "Tell me about recent political developments",
    "What's happening in technology news?",
    "Show me sports updates"
  ];

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">
          <div className="chat-avatar">
            <span className="avatar-icon">🤖</span>
          </div>
          <div className="title-content">
            <h1>News Assistant</h1>
            <p>Ask me anything about current events and news</p>
          </div>
        </div>
        <button className="clear-chat-btn" onClick={clearChat} title="Clear chat">
          🗑️
        </button>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}-message ${msg.isError ? 'error-message' : ''}`}>
            <div className="message-avatar">
              {msg.type === "user" ? (
                <span className="user-avatar">👤</span>
              ) : (
                <span className="bot-avatar">🤖</span>
              )}
            </div>
            <div className="message-content">
              <div className="message-bubble">
                <p className="message-text">{msg.text}</p>
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <span className="sources-icon">📰</span>
                      <strong>Sources:</strong>
                    </div>
                    <div className="sources-list">
                      {msg.sources.map((src, i) => (
                        <div key={i} className="source-item">
                          <span className="source-bullet">•</span>
                          <span className="source-title">{src.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="message-time">
                {formatTime(msg.timestamp)}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message bot-message typing-message">
            <div className="message-avatar">
              <span className="bot-avatar">🤖</span>
            </div>
            <div className="message-content">
              <div className="message-bubble typing-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p className="typing-text">Assistant is thinking...</p>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {messages.length === 1 && (
        <div className="suggested-questions">
          <p className="suggestions-title">Try asking:</p>
          <div className="suggestions-grid">
            {suggestedQuestions.map((question, idx) => (
              <button
                key={idx}
                className="suggestion-btn"
                onClick={() => setInput(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about the news..."
            className="chat-input"
            disabled={loading}
            rows={1}
            style={{
              height: 'auto',
              minHeight: '24px',
              maxHeight: '120px',
              resize: 'none'
            }}
            onInput={(e) => {
              e.target.style.height = 'auto';
              e.target.style.height = e.target.scrollHeight + 'px';
            }}
          />
          <button 
            className={`send-btn ${input.trim() && !loading ? 'active' : ''}`}
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            title="Send message"
          >
            {loading ? (
              <div className="send-spinner"></div>
            ) : (
              <span className="send-icon">➤</span>
            )}
          </button>
        </div>
        <div className="input-hint">
          Press Enter to send • Shift + Enter for new line
        </div>
      </div>
    </div>
  );
}