import { useState, useRef, useEffect } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";
import { Send, Bot, User } from "lucide-react";

export default function Copilot() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! Ask me anything about your cloud costs — e.g. \"What's our total spend?\" or \"Which service costs the most?\"",
      sources: null,
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMessage = { role: "user", text: question, sources: null };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await api.post("/copilot/chat/", { question: userMessage.text });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: res.data.answer, sources: res.data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Sorry, I couldn't process that question. Please try again.",
          sources: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Navbar />
      <div className="copilot-container">
        <h1>AI Copilot</h1>
        <p className="subtitle">Grounded answers from your real cost data</p>

        <div className="chat-window">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message chat-${msg.role}`}>
              <div className="chat-icon">
                {msg.role === "assistant" ? <Bot size={18} /> : <User size={18} />}
              </div>
              <div className="chat-bubble">
                <p>{msg.text}</p>
                {msg.sources && Object.keys(msg.sources).length > 0 && (
                  <div className="chat-sources">
                    <strong>Sources:</strong> Total ${msg.sources.total_cost} over {msg.sources.period}
                    {msg.sources.top_services && msg.sources.top_services.length > 0 && (
                      <span> — Top: {msg.sources.top_services[0].service}</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-message chat-assistant">
              <div className="chat-icon"><Bot size={18} /></div>
              <div className="chat-bubble chat-typing">Thinking...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-form" onSubmit={handleSend}>
          <input
            type="text"
            placeholder="Ask about your cloud costs..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
