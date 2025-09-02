import React, { useEffect, useState } from "react";
import { verify } from "../api";
import { useSearchParams, Link } from "react-router-dom";

export default function Verify(){
  const [sp] = useSearchParams();
  const token = sp.get("token");
  const [msg, setMsg] = useState("Verifying...");

  useEffect(()=>{
    if (!token) { setMsg("Missing token"); return; }
    verify(token).then(()=>{
      setMsg("Email verified. You can sign in now.");
    }).catch(e=>{
      setMsg(e?.response?.data?.detail || "Verification failed");
    });
  },[token]);

  return (
    <div className="auth"><div className="card">
      <h2>Email verification</h2>
      <div className="row">{msg}</div>
      <div className="actions"><Link className="btn" to="/login">Go to Login</Link></div>
    </div></div>
  );
}
