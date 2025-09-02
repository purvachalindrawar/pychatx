import React, { useState } from "react";
import { signup } from "../api";
import { Link } from "react-router-dom";

export default function Signup(){
  const [email, setEmail] = useState("");
  const [display, setDisplay] = useState("");
  const [password, setPassword] = useState("");
  const [ok, setOk] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e){
    e.preventDefault();
    try{
      setLoading(true); setErr("");
      const r = await signup(email, password, display);
      setOk(r.message || "Please check your email.");
    }catch(e){
      setErr(e?.response?.data?.detail || "Signup failed");
    }finally{ setLoading(false); }
  }

  return (
    <div className="auth">
      <div className="card">
        <h2>Create your account</h2>
        <form onSubmit={onSubmit}>
          <div className="row">
            <label>Display name</label>
            <input className="input" value={display} onChange={e=>setDisplay(e.target.value)} required/>
          </div>
          <div className="row">
            <label>Email</label>
            <input className="input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required/>
          </div>
          <div className="row">
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} required/>
          </div>
          {ok && <div className="small" style={{color:"var(--ok)"}}>{ok}</div>}
          {err && <div className="small" style={{color:"var(--danger)"}}>{err}</div>}
          <div className="actions"><button className="btn primary" disabled={loading}>{loading?"Creating...":"Create account"}</button></div>
        </form>
        <div className="small">Already have an account? <Link to="/login">Sign in</Link></div>
      </div>
    </div>
  );
}
