import React, { useEffect, useState } from "react";
import { useAtom } from "jotai";
import { roomsAtom, currentRoomAtom } from "../store";
import { myRooms, createRoom, joinByInvite, inviteLink } from "../api";

export default function Rooms() {
  const [rooms, setRooms] = useAtom(roomsAtom);
  const [current, setCurrent] = useAtom(currentRoomAtom);
  const [invite, setInvite] = useState("");
  const [creating, setCreating] = useState(false);

  async function refresh() {
    const rs = await myRooms();
    setRooms(rs);
    if (!current && rs.length) setCurrent(rs[0]);
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="sidebar">
      {/* Rooms list */}
      <div className="section">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: "8px 0" }}>Rooms</h3>
          <button
            className="btn"
            onClick={async () => {
              const name = (prompt("Room name?") || "").trim();
              if (!name) return;
              setCreating(true);
              try {
                await createRoom(name);
                await refresh();
              } finally {
                setCreating(false);
              }
            }}
            title="Create room"
          >
            {creating ? "..." : "＋"}
          </button>
        </div>
        <div className="small" style={{ marginBottom: 8, color: "var(--muted)" }}>
          Click to open
        </div>
        <div>
          {rooms.map((r) => (
            <div
              key={r.id}
              className={"room " + (current?.id === r.id ? "active" : "")}
              onClick={() => setCurrent(r)}
              title={r.is_private ? "Private" : "Public"}
            >
              <div>{r.name}</div>
              <div className="small">{new Date(r.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Join by invite */}
      <div className="section">
        <h4 style={{ margin: "8px 0" }}>Join by invite</h4>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            className="input"
            placeholder="Invite code"
            value={invite}
            onChange={(e) => setInvite(e.target.value)}
          />
          <button
            className="btn"
            onClick={async () => {
              const code = invite.trim();
              if (!code) return;
              await joinByInvite(code);
              setInvite("");
              await refresh();
            }}
          >
            Join
          </button>
        </div>
      </div>

      {/* Shareable invite link for the selected room */}
      {current && current.invite_code && (
        <div className="section">
          <h4 style={{ margin: "8px 0" }}>Share</h4>
          <div className="small" style={{ color: "var(--muted)", marginBottom: 6 }}>
            Anyone with this link can request to join:
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <input className="input" readOnly value={inviteLink(current.invite_code)} />
            <button
              className="btn"
              onClick={async () => {
                await navigator.clipboard.writeText(inviteLink(current.invite_code));
                alert("Invite link copied!");
              }}
            >
              Copy link
            </button>
          </div>
        </div>
      )}

      <div className="section small" style={{ color: "var(--muted)" }}>
        Tip: Press <span className="kbd">Ctrl</span>+<span className="kbd">K</span> for command palette.
      </div>
    </div>
  );
}
