import { useState } from "react";
import { Send, Bot, User, MessageCircle, X } from "lucide-react";
import { mockChatMessages } from "@/lib/mock-data";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  role: "system" | "user" | "assistant";
  content: string;
}

const FloatingChat = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(mockChatMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input };
    const botMsg: Message = { role: "assistant", content: `Processing: "${input}" — [Mock mode — connect to backend agents for live responses]` };
    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput("");
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
              <span className="text-[9px] text-muted-foreground">Agent-powered</span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : ""}`}>
                  {msg.role !== "user" && (
                    <div className="shrink-0 h-5 w-5 rounded bg-accent/10 flex items-center justify-center">
                      <Bot className="h-3 w-3 text-accent" />
                    </div>
                  )}
                  <div className={`max-w-[80%] px-3 py-1.5 rounded text-xs ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-foreground"
                  }`}>
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="shrink-0 h-5 w-5 rounded bg-primary/10 flex items-center justify-center">
                      <User className="h-3 w-3 text-primary" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="p-2.5 border-t border-border">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Query shipment or agent..."
                  className="flex-1 px-3 py-1.5 text-xs rounded border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  aria-label="Console input"
                />
                <button
                  onClick={handleSend}
                  className="px-2.5 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
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
