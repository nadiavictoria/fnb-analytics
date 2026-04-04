import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Chatbot.css';

const STORAGE_KEY = 'chatbot_history';
const INITIAL_MESSAGE = { role: 'assistant', text: 'Hi! Ask me for food recommendations near any MRT station.' };

const Chatbot = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [INITIAL_MESSAGE];
    } catch {
      return [INITIAL_MESSAGE];
    }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg = { role: 'user', text: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: 'assistant', text: data.answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Sorry, something went wrong. Is the backend running?' },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearHistory = () => {
    setMessages([INITIAL_MESSAGE]);
  };

  return (
    <>
      {open && (
        <div className="chatbot-panel">
          <div className="chatbot-header">
            <span>Food Assistant</span>
            <div className="chatbot-header-actions">
              <button className="chatbot-clear" onClick={clearHistory} title="Clear history">Clear</button>
              <button className="chatbot-close" onClick={() => setOpen(false)}>✕</button>
            </div>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chatbot-msg chatbot-msg-${msg.role}`}>
                {msg.role === 'assistant'
                  ? (
                    <ReactMarkdown>
                      {msg.text}
                    </ReactMarkdown>
                  )
                  : msg.text}
              </div>
            ))}
            {loading && <div className="chatbot-msg chatbot-msg-assistant chatbot-typing">Thinking…</div>}
            <div ref={bottomRef} />
          </div>

          <div className="chatbot-input-row">
            <textarea
              className="chatbot-input"
              placeholder="e.g. Best restaurants near Kent Ridge"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button className="chatbot-send" onClick={sendMessage} disabled={loading}>
              Send
            </button>
          </div>
        </div>
      )}

      <button className="chatbot-fab" onClick={() => setOpen((o) => !o)} aria-label="Open food assistant">
        🍜
      </button>
    </>
  );
};

export default Chatbot;
