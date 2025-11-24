import { useState } from "react";
import axios from "axios";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: "user", text: input };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/api/ask", {
        query: input
      });

      const botMessage = {
        type: "bot",
        text: res.data.answer,
        sources: res.data.sources
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: "bot",
        text: "Error: Could not get response"
      }]);
    }

    setInput("");
    setLoading(false);
  };

  return (
    <div className="container" style={{ maxWidth: "800px", margin: "0 auto" }}>
      <h2>News Chat Assistant</h2>
      
      <div style={{ 
        height: "400px", 
        border: "1px solid #ccc", 
        padding: "10px", 
        overflowY: "scroll",
        marginBottom: "10px"
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            marginBottom: "10px",
            padding: "8px",
            backgroundColor: msg.type === "user" ? "#e3f2fd" : "#f5f5f5",
            borderRadius: "5px"
          }}>
            <strong>{msg.type === "user" ? "You:" : "Assistant:"}</strong>
            <p>{msg.text}</p>
            
            {msg.sources && (
              <div style={{ fontSize: "12px", color: "#666" }}>
                <strong>Sources:</strong>
                {msg.sources.map((src, i) => (
                  <div key={i}>• {src.title}</div>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div style={{ fontStyle: "italic", color: "#666" }}>
            Assistant is typing...
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "10px" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask about the news..."
          style={{ flex: 1, padding: "8px" }}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}