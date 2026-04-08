import { FormEvent, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

import { buildChatSocket, type ReadyStateResponse } from "../api/client";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ConnectionState = "connecting" | "ready" | "streaming" | "disconnected" | "error" | "interrupted";

const CONNECTION_COPY: Record<ConnectionState, string> = {
  connecting: "Connecting to Stella...",
  ready: "Connected. Ask Stella about the current data set.",
  streaming: "Stella is streaming a response.",
  disconnected: "Chat disconnected. Reconnect to continue.",
  error: "Chat error. Reconnect to continue.",
  interrupted: "Stella restarted while the session was open. Reconnect to continue.",
};

export function ChatPage({
  runtime,
  runtimeError,
}: {
  runtime?: ReadyStateResponse;
  runtimeError?: Error | null;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const [statusMessage, setStatusMessage] = useState(CONNECTION_COPY.connecting);
  const [socketVersion, setSocketVersion] = useState(0);
  const socketRef = useRef<WebSocket | null>(null);
  const awaitingReplyRef = useRef(false);
  const terminalReasonRef = useRef<"none" | "error">("none");

  const chatBlockedReason = runtimeError
    ? "The backend runtime is offline. Restart Stella before opening chat."
    : !runtime
      ? "Checking workspace readiness..."
      : !runtime.has_data
        ? "Import health data first. Stella chat only becomes useful after the workspace has data to analyze."
        : !runtime.llm_reachable
          ? `Chat is unavailable in metrics-only mode. Reports and analytics still work while ${runtime.llm_provider} recovers.`
          : null;
  const chatAvailable = !chatBlockedReason;
  const introMessage = chatBlockedReason ?? "Ask about your trends, anomalies, or strongest correlations.";

  useEffect(() => {
    setMessages([{ role: "assistant", content: introMessage }]);
  }, [introMessage]);

  useEffect(() => {
    terminalReasonRef.current = "none";
    awaitingReplyRef.current = false;
    setStreaming(false);

    if (!chatAvailable) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setConnectionState(runtimeError ? "error" : "disconnected");
      setStatusMessage(chatBlockedReason ?? CONNECTION_COPY.disconnected);
      return;
    }

    setConnectionState("connecting");
    setStatusMessage(CONNECTION_COPY.connecting);

    const socket = buildChatSocket();
    socketRef.current = socket;

    socket.addEventListener("open", () => {
      setConnectionState("ready");
      setStatusMessage(CONNECTION_COPY.ready);
    });

    socket.addEventListener("message", (event) => {
      const payload = JSON.parse(event.data) as { type: string; content?: string; message?: string };
      if (payload.type === "chunk") {
        awaitingReplyRef.current = true;
        setStreaming(true);
        setConnectionState("streaming");
        setStatusMessage(CONNECTION_COPY.streaming);
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
        awaitingReplyRef.current = false;
        setStreaming(false);
        setConnectionState("ready");
        setStatusMessage(CONNECTION_COPY.ready);
      }
      if (payload.type === "error") {
        terminalReasonRef.current = "error";
        awaitingReplyRef.current = false;
        setStreaming(false);
        setConnectionState("error");
        setStatusMessage(payload.message ?? CONNECTION_COPY.error);
        setMessages((current) => {
          const last = current[current.length - 1];
          if (last?.role === "assistant" && !last.content.trim()) {
            return [
              ...current.slice(0, -1),
              { role: "assistant", content: payload.message ?? "Streaming error." },
            ];
          }
          return [...current, { role: "assistant", content: payload.message ?? "Streaming error." }];
        });
      }
    });

    socket.addEventListener("error", () => {
      terminalReasonRef.current = "error";
      setStreaming(false);
      setConnectionState("error");
      setStatusMessage("The chat connection hit a network error.");
    });

    socket.addEventListener("close", (event) => {
      socketRef.current = null;
      setStreaming(false);

      if (terminalReasonRef.current === "error") {
        awaitingReplyRef.current = false;
        return;
      }

      if (event.code === 1012) {
        awaitingReplyRef.current = false;
        setConnectionState("interrupted");
        setStatusMessage(CONNECTION_COPY.interrupted);
        return;
      }

      if (awaitingReplyRef.current) {
        awaitingReplyRef.current = false;
        setConnectionState("error");
        setStatusMessage("The connection closed before Stella finished responding.");
        setMessages((current) => [...current, { role: "assistant", content: "The session closed before the answer completed." }]);
        return;
      }

      setConnectionState("disconnected");
      setStatusMessage(CONNECTION_COPY.disconnected);
    });

    return () => {
      socketRef.current = null;
      socket.close();
    };
  }, [chatAvailable, chatBlockedReason, runtimeError, socketVersion]);

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || !socketRef.current || connectionState !== "ready") {
      return;
    }

    awaitingReplyRef.current = true;
    terminalReasonRef.current = "none";
    setMessages((current) => [...current, { role: "user", content: trimmed }, { role: "assistant", content: "" }]);
    setDraft("");
    socketRef.current.send(JSON.stringify({ message: trimmed }));
  }

  const allowReconnect =
    chatAvailable && (connectionState === "disconnected" || connectionState === "error" || connectionState === "interrupted");

  return (
    <section className="chat-layout">
      <div className="panel chat-transcript">
        <div className="panel-heading">
          <p className="eyebrow">Streaming chat</p>
          <h3>Ask Stella about the current data set</h3>
        </div>
        <div className="status-row">
          <p className={`status-pill ${chatAvailable ? connectionState : "blocked"}`}>{chatAvailable ? connectionState : "blocked"}</p>
          <p className="status">{statusMessage}</p>
          {allowReconnect ? (
            <button type="button" className="inline-button" onClick={() => setSocketVersion((current) => current + 1)}>
              Reconnect chat
            </button>
          ) : null}
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
          disabled={!chatAvailable}
        />
        <button type="submit" disabled={!draft.trim() || streaming || connectionState !== "ready" || !chatAvailable}>
          {streaming ? "Streaming..." : "Send question"}
        </button>
      </form>
    </section>
  );
}
