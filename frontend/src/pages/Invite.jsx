import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { storage, joinByInvite } from "../api";

export default function Invite(){
  const { code } = useParams();
  const nav = useNavigate();
  const [status, setStatus] = useState("Ready to join");

  async function tryJoin(){
    if (!code) { setStatus("Invalid invite code"); return; }
    if (!storage.access){
      localStorage.setItem("pendingInvite", code);
      nav("/login");
      return;
    }
    try{
      setStatus("Joining…");
      await joinByInvite(code);
      setStatus("Joined! Redirecting…");
      setTimeout(()=> nav("/app"), 500);
    }catch(e){
      setStatus(e?.response?.data?.detail || "Failed to join. Are you already a member?");
    }
  }

  useEffect(()=>{
    // auto-join if user is already signed in
    if (storage.access) tryJoin();
  },[]);

  return (
    <div className="auth">
      <div className="card">
        <h2>Room invitation</h2>
        <div className="row">Invite code: <b>{code}</b></div>
        <div className="row small" style={{color:"var(--muted)"}}>{status}</div>
        <div className="actions">
          <button className="btn primary" onClick={tryJoin}>Join room</button>
          {!storage.access && <Link className="btn" to="/login">Sign in</Link>}
        </div>
      </div>
    </div>
  );
}
