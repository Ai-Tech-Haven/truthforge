import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, MessageCircle, X, Radio } from "lucide-react";
import { mockChatMessages } from "@/lib/mock-data";
import { motion, AnimatePresence } from "framer-motion";
import { useMockMode } from "@/contexts/MockModeContext";

const RAILWAY = "https://web-production-dcd43.up.railway.app";

interface Message {
  role: "system" | "user" | "assistant";
  content: string;
  agent?: string;
  timestamp?: string;
}

const FloatingChat = () => {
  const { isMockMode } = useMockMode();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(mockChatMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Reset messages when mode changes
  useEffect(() => {
    if (isMockMode) {
      setMessages(mockChatMessages);
    } else {
      setMessages([
        {
          role: "system",
          content: "TruthForge Live Agent Console ready. Ask about shipments, agents, or verification status.",
        },
      ]);
    }
  }, [isMockMode]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput("");

    const userMsg: Message = { role: "user", content: userText };
    setMessages((prev) => [...prev, userMsg]);

    if (isMockMode) {
      const botMsg: Message = {
        role: "assistant",
        content: `Processing: "${userText}" — [Mock mode — switch to Live for real agent responses]`,
      };
      setMessages((prev) => [...prev, botMsg]);
      return;
    }

    // Live mode — call backend
    setLoading(true);
    try {
      const res = await fetch(`${RAILWAY}/api/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
        signal: AbortSignal.timeout(15000),
      });

      if (res.ok) {
        const data = await res.json();
        const botMsg: Message = {
          role: "assistant",
          content: data.response ?? data.message ?? JSON.stringify(data),
          agent: data.agent ?? data.agent_id ?? undefined,
          timestamp: data.timestamp ?? new Date().toISOString(),
        };
        setMessages((prev) => [...prev, botMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Backend error ${res.status}. Please try again.` },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Could not reach backend agents. Check your connection." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setOpen((p) => !p)}
        aria-label={open ? "Close verification console" : "Open verification console"}
        className="fixed bottom-6 right-6 z-50 h-12 w-12 rounded-full bg-primary text-primary-foreground shadow-elevated hover:shadow-glow transition-all flex items-center justify-center"
      >
        {open ? <X className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
      </button>

      {/* Chat Panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-20 right-6 z-50 w-[360px] max-w-[calc(100vw-2rem)] rounded-lg border border-border bg-card shadow-elevated flex flex-col h-[420px]"
          >
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <h3 className="font-heading font-bold text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Bot className="h-3.5 w-3.5 text-accent" />
                Verification Console
              </h3>
              <span className={`flex items-center gap-1 text-[9px] font-medium ${isMockMode ? "text-warning" : "text-success"}`}>
                {!isMockMode && <Radio className="h-2.5 w-2.5 animate-pulse" />}
                {isMockMode ? "Mock" : "Live Agents"}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role !== "user" && (
                    <div className="shrink-0 h-5 w-5 rounded bg-accent/10 flex items-center justify-center">
                      <Bot className="h-3 w-3 text-accent" />
                    </div>
                  )}
                  <div className={`max-w-[80%] space-y-0.5`}>
                    <div className={`px-3 py-1.5 rounded text-xs ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-foreground"
                    }`}>
                      {msg.content}
                    </div>
                    {msg.agent && (
                      <div className="text-[9px] text-muted-foreground px-1">via {msg.agent}</div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="shrink-0 h-5 w-5 rounded bg-primary/10 flex items-center justify-center">
                      <User className="h-3 w-3 text-primary" />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-2">
                  <div className="shrink-0 h-5 w-5 rounded bg-accent/10 flex items-center justify-center">
                    <Bot className="h-3 w-3 text-accent" />
                  </div>
                  <div className="px-3 py-1.5 rounded bg-secondary text-xs text-muted-foreground animate-pulse">
                    Agents processing...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="p-2.5 border-t border-border">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder={isMockMode ? "Query shipment or agent..." : "Ask live agents..."}
                  className="flex-1 px-3 py-1.5 text-xs rounded border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  aria-label="Console input"
                  disabled={loading}
                />
                <button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  className="px-2.5 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40"
                  aria-label="Send"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingChat;
