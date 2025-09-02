import React, { useEffect, useMemo, useRef, useState } from "react";
import { useAtom } from "jotai";
import { authAtom, currentRoomAtom, messagesAtom, typingAtom } from "../store";
import {
  listMessages,
  postMessage,
  addReaction,
  removeReaction,
  markDelivered,
  markRead,
  wsUrl,
} from "../api";
import { motion } from "framer-motion";

export default function Chat() {
  const [auth] = useAtom(authAtom);
  const [room] = useAtom(currentRoomAtom);
  const [messages, setMessages] = useAtom(messagesAtom);
  const [typing, setTyping] = useAtom(typingAtom);
  const [q, setQ] = useState("");

  // Reactions state: { [messageId]: { [emoji]: count } }
  const [rx, setRx] = useState({});

  const wsRef = useRef(null);
  const endRef = useRef(null);

  function scrollBottom() {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    if (!room || !auth.user) return;
    let ws;

    (async () => {
      // reset reactions for the new room
      setRx({});
      // load messages
      const data = await listMessages(room.id);
      setMessages(data);
      scrollBottom();
      // mark delivered (best-effort)
      try {
        await markDelivered(data.map((m) => m.id));
      } catch {}

      // open WebSocket
      ws = new WebSocket(wsUrl(room.id, auth.user.id));
      wsRef.current = ws;

      ws.onopen = () => console.log("WS open");
      ws.onclose = (e) => console.log("WS closed", e.code, e.reason);
      ws.onerror = (e) => console.log("WS error", e);

      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === "message") {
          setMessages((prev) => [
            ...prev,
            {
              id: msg.id,
              user_id: msg.user_id,
              content: msg.content,
              edited: false,
              deleted: false,
              created_at: msg.created_at,
              updated_at: null,
              parent_id: null,
              attachment: null,
            },
          ]);
          scrollBottom();
        } else if (msg.type === "typing") {
          setTyping((prev) => {
            const s = new Set([...prev]);
            if (msg.state) s.add(msg.user_id);
            else s.delete(msg.user_id);
            return s;
          });
        } else if (msg.type === "reaction") {
          // {type:"reaction", message_id, emoji, action:"add"|"remove"}
          setRx((prev) => {
            const byMsg = { ...(prev[msg.message_id] || {}) };
            const delta = msg.action === "remove" ? -1 : 1;
            byMsg[msg.emoji] = Math.max(0, (byMsg[msg.emoji] || 0) + delta);
            if (byMsg[msg.emoji] === 0) delete byMsg[msg.emoji];
            return { ...prev, [msg.message_id]: byMsg };
          });
        } else if (msg.type === "presence") {
          // reserved
        }
      };
    })();

    return () => {
      try {
        ws?.close();
      } catch {}
      setTyping(new Set());
    };
  }, [room?.id, auth?.user?.id, setMessages, setTyping]);

  // Send message (WS if ready, else REST + optimistic append)
  async function send(content) {
    if (!content.trim()) return;

    if (wsRef.current?.readyState === 1) {
      wsRef.current.send(JSON.stringify({ type: "message", content }));
      return;
    }

    const r = await postMessage(room.id, content);
    setMessages((prev) => [
      ...prev,
      {
        id: r.id,
        user_id: auth.user.id,
        content,
        edited: false,
        deleted: false,
        created_at: r.created_at,
        updated_at: null,
        parent_id: null,
        attachment: null,
      },
    ]);
    try {
      await markRead([r.id]);
    } catch {}
  }

  const me = auth.user?.id;
  const filtered = useMemo(() => {
    if (!q) return messages;
    const s = q.toLowerCase();
    return messages.filter((m) => m.content.toLowerCase().includes(s));
  }, [messages, q]);

  return (
    <div className="content">
      <div className="toolbar">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <strong>{room?.name || "—"}</strong>
          <span className="small" style={{ color: "var(--muted)" }}>
            {typing.size ? "typing…" : ""}
          </span>
        </div>
        <input
          className="input"
          placeholder="Search in room…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ maxWidth: 360 }}
        />
      </div>

      <div className="messages">
        {filtered.map((m) => (
          <motion.div
            key={m.id}
            className={"message " + (m.user_id === me ? "me" : "")}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15 }}
          >
            <div className="bubble">
              <div>{m.content}</div>
              <div className="meta">
                {new Date(m.created_at).toLocaleString()}
              </div>

              {/* Quick reaction buttons (optimistic add) */}
              <div className="reaction-bar">
                {["👍", "🔥", "🎉", "😂", "❤️"].map((e) => (
                  <button
                    key={e}
                    className="reaction"
                    onClick={async () => {
                      // optimistic add
                      setRx((prev) => {
                        const byMsg = { ...(prev[m.id] || {}) };
                        byMsg[e] = (byMsg[e] || 0) + 1;
                        return { ...prev, [m.id]: byMsg };
                      });
                      try {
                        if (wsRef.current?.readyState === 1) {
                          wsRef.current.send(
                            JSON.stringify({
                              type: "reaction",
                              message_id: m.id,
                              emoji: e,
                              action: "add",
                            })
                          );
                        } else {
                          await addReaction(m.id, e);
                        }
                      } catch {
                        // rollback
                        setRx((prev) => {
                          const byMsg = { ...(prev[m.id] || {}) };
                          byMsg[e] = Math.max(0, (byMsg[e] || 1) - 1);
                          if (byMsg[e] === 0) delete byMsg[e];
                          return { ...prev, [m.id]: byMsg };
                        });
                      }
                    }}
                  >
                    {e}
                  </button>
                ))}
              </div>

              {/* Current reaction counts (click to remove) */}
              {Object.entries(rx[m.id] || {}).length > 0 && (
                <div className="reaction-bar">
                  {Object.entries(rx[m.id] || {}).map(([emoji, count]) => (
                    <span
                      key={emoji}
                      className="reaction"
                      title="Click to remove"
                      onClick={async () => {
                        // optimistic remove
                        setRx((prev) => {
                          const byMsg = { ...(prev[m.id] || {}) };
                          byMsg[emoji] = Math.max(
                            0,
                            (byMsg[emoji] || 1) - 1
                          );
                          if (byMsg[emoji] === 0) delete byMsg[emoji];
                          return { ...prev, [m.id]: byMsg };
                        });
                        try {
                          if (wsRef.current?.readyState === 1) {
                            wsRef.current.send(
                              JSON.stringify({
                                type: "reaction",
                                message_id: m.id,
                                emoji,
                                action: "remove",
                              })
                            );
                          } else {
                            await removeReaction(m.id, emoji);
                          }
                        } catch {
                          // rollback
                          setRx((prev) => {
                            const byMsg = { ...(prev[m.id] || {}) };
                            byMsg[emoji] = (byMsg[emoji] || 0) + 1;
                            return { ...prev, [m.id]: byMsg };
                          });
                        }
                      }}
                    >
                      {emoji} {count}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        <div ref={endRef} />
      </div>

      <Composer
        onTyping={(state) => {
          try {
            wsRef.current?.send(JSON.stringify({ type: "typing", state }));
          } catch {}
        }}
        onSend={async (text) => {
          await send(text);
          // mark read (best-effort)
          try {
            await markRead([...messages.slice(-5).map((m) => m.id)]);
          } catch {}
        }}
      />
    </div>
  );
}

function Composer({ onSend, onTyping }) {
  const [value, setValue] = useState("");
  const typingTimeout = useRef(null);

  function setTyping(state) {
    onTyping?.(state);
    clearTimeout(typingTimeout.current);
    if (state) {
      typingTimeout.current = setTimeout(() => onTyping?.(false), 1500);
    }
  }

  return (
    <div className="composer">
      <div className="row">
        <textarea
          className="input"
          placeholder="Message…"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setTyping(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              const text = value.trim();
              if (text) {
                onSend?.(text);
                setValue("");
                setTyping(false);
              }
            }
          }}
        />
        <button
          className="btn primary"
          onClick={() => {
            const text = value.trim();
            if (text) {
              onSend?.(text);
              setValue("");
              setTyping(false);
            }
          }}
        >
          Send
        </button>
      </div>
      <div className="help">
        Press <span className="kbd">Enter</span> to send •{" "}
        <span className="kbd">Shift</span>+<span className="kbd">Enter</span> for newline
      </div>
    </div>
  );
}
