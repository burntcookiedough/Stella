import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";

import { buildChatSocket } from "../api/client";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Ask about your trends, anomalies, or strongest correlations.",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = buildChatSocket();
    socketRef.current = socket;

    socket.addEventListener("message", (event) => {
      const payload = JSON.parse(event.data) as { type: string; content?: string; message?: string };
      if (payload.type === "chunk") {
        setStreaming(true);
        setMessages((current) => {
          const last = current[current.length - 1];
          if (last?.role === "assistant") {
            return [
              ...current.slice(0, -1),
              { ...last, content: `${last.content}${payload.content ?? ""}` },
            ];
          }
          return [...current, { role: "assistant", content: payload.content ?? "" }];
        });
      }
      if (payload.type === "done") {
        setStreaming(false);
      }
      if (payload.type === "error") {
        setStreaming(false);
        setMessages((current) => [...current, { role: "assistant", content: payload.message ?? "Streaming error." }]);
      }
    });

    return () => socket.close();
  }, []);

  const lastRole = useMemo(() => messages[messages.length - 1]?.role, [messages]);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || !socketRef.current) {
      return;
    }

    setMessages((current) => {
      const assistantPlaceholder: Message[] =
        lastRole === "assistant" ? [] : [{ role: "assistant", content: "" }];
      const nextMessages: Message[] = [
        ...current,
        { role: "user", content: trimmed },
        ...assistantPlaceholder,
      ];
      return nextMessages;
    });
    setDraft("");
    socketRef.current.send(JSON.stringify({ message: trimmed }));
  }

  return (
    <section className="chat-layout">
      <div className="panel chat-transcript">
        <div className="panel-heading">
          <p className="eyebrow">Streaming chat</p>
          <h3>Ask Stella about the current data set</h3>
        </div>
        <div className="transcript-list">
          {messages.map((message, index) => (
            <motion.article
              key={`${message.role}-${index}`}
              className={`bubble ${message.role}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.24 }}
            >
              <span>{message.role === "assistant" ? "Stella" : "You"}</span>
              <p>{message.content}</p>
            </motion.article>
          ))}
          {streaming ? <div className="stream-pulse" aria-label="Streaming response" /> : null}
        </div>
      </div>

      <form className="panel chat-composer" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">Prompt</p>
          <h3>Send a focused question</h3>
        </div>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Why was my sleep score weak this week?"
        />
        <button type="submit" disabled={!draft.trim() || streaming}>
          {streaming ? "Streaming..." : "Send question"}
        </button>
      </form>
    </section>
  );
}
