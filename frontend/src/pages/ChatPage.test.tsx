import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

type Listener = (event?: Event | { data?: string; code?: number }) => void;

class MockSocket {
  static readonly OPEN = 1;
  static readonly CLOSED = 3;

  readyState = 0;
  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockSocket.CLOSED;
  });

  private listeners = new Map<string, Listener[]>();

  addEventListener(type: string, listener: Listener) {
    const current = this.listeners.get(type) ?? [];
    current.push(listener);
    this.listeners.set(type, current);
  }

  emit(type: string, event?: Event | { data?: string; code?: number }) {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }

  open() {
    this.readyState = MockSocket.OPEN;
    this.emit("open", new Event("open"));
  }

  message(payload: object) {
    this.emit("message", { data: JSON.stringify(payload) });
  }

  closeWith(code: number) {
    this.readyState = MockSocket.CLOSED;
    this.emit("close", { code });
  }
}

const sockets: MockSocket[] = [];

vi.mock("../api/client", () => ({
  buildChatSocket: () => {
    const socket = new MockSocket();
    sockets.push(socket);
    return socket as unknown as WebSocket;
  },
}));

import { ChatPage } from "./ChatPage";

describe("ChatPage", () => {
  beforeEach(() => {
    cleanup();
    sockets.length = 0;
  });

  it("surfaces server interruption and offers reconnect", async () => {
    render(
      <ChatPage
        runtime={{
          status: "ready",
          has_data: true,
          llm_provider: "stub",
          llm_model: "test-model",
          llm_reachable: true,
          llm_error: null,
        }}
      />,
    );

    expect(screen.getByText(/connecting to stella/i)).toBeTruthy();

    act(() => {
      sockets[0].open();
    });

    fireEvent.change(screen.getByPlaceholderText(/why was my sleep score weak this week/i), {
      target: { value: "What changed this week?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send question/i }));

    expect(sockets[0].send).toHaveBeenCalledWith(JSON.stringify({ message: "What changed this week?" }));

    act(() => {
      sockets[0].message({ type: "chunk", content: "Your sleep dipped." });
      sockets[0].closeWith(1012);
    });

    expect(await screen.findByText(/stella restarted while the session was open/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /reconnect chat/i })).toBeTruthy();
  });

  it("explains metrics-only mode when chat is unavailable", async () => {
    render(
      <ChatPage
        runtime={{
          status: "ready",
          has_data: true,
          llm_provider: "ollama",
          llm_model: "mistral",
          llm_reachable: false,
          llm_error: "provider unavailable",
        }}
      />,
    );

    expect((await screen.findAllByText(/chat is unavailable in metrics-only mode/i)).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /send question/i }).hasAttribute("disabled")).toBe(true);
  });
});
