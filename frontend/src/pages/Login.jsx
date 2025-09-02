import React, { useState } from "react";
import { login } from "../api";
import { useNavigate, Link } from "react-router-dom";
import { useAtom } from "jotai";
import { authAtom } from "../store";

export default function Login(){
  const nav = useNavigate();
  const [, setAuth] = useAtom(authAtom);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function onSubmit(e){
    e.preventDefault();
    try{
      setLoading(true); setErr("");
      const me = await login(email, password);
      setAuth({ user: me, ready: true });
      nav("/app");
    }catch(e){
      setErr(e?.response?.data?.detail || "Login failed");
    }finally{ setLoading(false); }
  }

  return (
    <div className="auth">
      <div className="card">
        <h2>Welcome back</h2>
        <form onSubmit={onSubmit}>
          <div className="row">
            <label>Email</label>
            <input className="input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/>
          </div>
          <div className="row">
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} required/>
          </div>
          {err && <div className="small" style={{color:"var(--danger)"}}>{err}</div>}
          <div className="actions">
            <button className="btn primary" disabled={loading}>{loading?"Signing in...":"Sign in"}</button>
          </div>
        </form>
        <div className="small">No account? <Link to="/signup">Create one</Link></div>
      </div>
    </div>
  );
}
