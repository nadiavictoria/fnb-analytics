import { useEffect, useRef, useState } from 'react';
import './Chatbot.css';

const STORAGE_KEY = 'chatbot_history';
const INITIAL_MESSAGE = { role: 'assistant', text: 'Hi! Ask me for food recommendations near any MRT station.' };

const HELP_TEXT = `How to use the Food Assistant:

1. Ask by MRT station:
Type the name of any MRT station and get restaurant recommendations nearby.
e.g. "Best hawker stalls near Tampines"

2. Filter by food type:
Mention a cuisine or food type to narrow results.
e.g. "Japanese restaurants near Orchard"

3. Tips:
- Partial station names work: "jurong" finds Jurong East & Jurong West.
- Results are ranked by rating.
- Up to 20 results are shown if not specified.`;

const Chatbot = () => {
  const [open, setOpen] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
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
            <div className="chatbot-header-title">
              <span>Food Assistant</span>
              <button className="chatbot-clear" onClick={clearHistory} title="Clear history">Clear</button>
            </div>
            <div className="chatbot-header-actions">
              <button className="chatbot-help" onClick={() => setShowHelp((h) => !h)} title="Help">?</button>
              <button className="chatbot-close" onClick={() => setOpen(false)}>✕</button>
            </div>
          </div>

          {showHelp ? (
            <div className="chatbot-help-panel">
              <span style={{ whiteSpace: 'pre-wrap' }}>{HELP_TEXT}</span>
            </div>
          ) : (
          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chatbot-msg chatbot-msg-${msg.role}`}>
                {msg.role === 'assistant'
                  ? <span style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</span>
                  : msg.text}
              </div>
            ))}
            {loading && <div className="chatbot-msg chatbot-msg-assistant chatbot-typing">Thinking…</div>}
            <div ref={bottomRef} />
          </div>
          )}

          <div className="chatbot-input-row">
            <textarea
              className="chatbot-input"
              placeholder="e.g. Best restaurants near Kent Ridge MRT"
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
