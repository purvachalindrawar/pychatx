// frontend/src/pages/Rooms.jsx
import React, { useEffect, useState } from "react";
import { useAtom } from "jotai";
import { roomsAtom, currentRoomAtom } from "../store";
import { myRooms, createRoom, joinByInvite, inviteLink } from "../api";

export default function Rooms(){
  const [rooms, setRooms] = useAtom(roomsAtom);
  const [current, setCurrent] = useAtom(currentRoomAtom);
  const [invite, setInvite] = useState("");
  const [creating, setCreating] = useState(false);
  const [joining, setJoining] = useState(false);

  async function refresh(){
    const rs = await myRooms();
    setRooms(rs);
    if (!current && rs.length) setCurrent(rs[0]);
  }
  useEffect(()=>{ refresh(); /* eslint-disable-next-line */ },[]);

  // NEW: quick join that works well on phones (prompt)
  async function quickJoin(){
    const raw = (prompt("Enter invite code or link:") || "").trim();
    if (!raw) return;

    // allow full links like https://pychatx.vercel.app/invite/AbCdEf123
    let code = raw;
    const m = raw.match(/\/invite\/([A-Za-z0-9_-]+)/);
    if (m) code = m[1];

    setJoining(true);
    try{
      await joinByInvite(code);
      await refresh();
      alert("Joined!");
    }catch(e){
      console.error(e);
      alert("Couldn't join with that code. Please check and try again.");
    }finally{
      setJoining(false);
    }
  }

  return (
    <div className="sidebar">
      <div className="section">
        <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
          <h3 style={{margin:"8px 0"}}>Rooms</h3>

          <div style={{display:"flex", gap:8}}>
            {/* NEW: small Join button that opens the prompt (great on mobile) */}
            <button className="btn" title="Join by invite" onClick={quickJoin}>
              {joining ? "…" : "Join"}
            </button>

            <button className="btn" title="Create room" onClick={async ()=>{
              const name = prompt("Room name?");
              if (!name) return;
              setCreating(true);
              try{
                await createRoom(name);
                await refresh();
              } finally { setCreating(false); }
            }}>
              {creating ? "…" : "＋"}
            </button>
          </div>
        </div>

        <div className="small" style={{marginBottom:8, color:"var(--muted)"}}>Click to open</div>
        <div>
          {rooms.map(r=>(
            <div key={r.id}
              className={"room " + (current?.id===r.id?"active":"")}
              onClick={()=>setCurrent(r)}
              title={r.is_private ? "Private" : "Public"}
            >
              <div>{r.name}</div>
              <div className="small">{new Date(r.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Keep your existing inline join box for desktop users */}
      <div className="section">
        <h4 style={{margin:"8px 0"}}>Join by invite</h4>
        <div style={{display:"flex", gap:8}}>
          <input className="input" placeholder="Invite code" value={invite} onChange={e=>setInvite(e.target.value)} />
          <button className="btn" onClick={async ()=>{
            if (!invite.trim()) return;
            try{
              await joinByInvite(invite.trim());
              setInvite("");
              await refresh();
            }catch(e){
              console.error(e);
              alert("Couldn't join with that code.");
            }
          }}>Join</button>
        </div>
      </div>

      {/* Share section when a room with invite_code is selected */}
      {current && current.invite_code && (
        <div className="section">
          <h4 style={{margin:"8px 0"}}>Share</h4>
          <div className="small" style={{color:"var(--muted)", marginBottom:6}}>
            Anyone with this link can request to join:
          </div>
          <div style={{display:"grid", gap:8}}>
            <input className="input" readOnly value={inviteLink(current.invite_code)} />
            <button className="btn" onClick={async ()=>{
              await navigator.clipboard.writeText(inviteLink(current.invite_code));
              alert("Invite link copied!");
            }}>Copy link</button>
          </div>
        </div>
      )}

      <div className="section small" style={{color:"var(--muted)"}}>
        Tip: Press <span className="kbd">Ctrl</span>+<span className="kbd">K</span> for command palette.
      </div>
    </div>
  );
}
