import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useAtom } from "jotai";
import { authAtom, roomsAtom, currentRoomAtom } from "./store";
import { storage, myRooms, logout } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Verify from "./pages/Verify";
import Rooms from "./pages/Rooms";
import Chat from "./pages/Chat";
import CommandPalette from "./components/CommandPalette";
import Invite from "./pages/Invite";

function Header(){
  const [auth, setAuth] = useAtom(authAtom);
  const nav = useNavigate();
  return (
    <div className="header">
      <div className="brand" onClick={()=>nav("/app")} style={{cursor:"pointer"}}>
        <div className="brand-badge"></div>
        PyChatX
        <span className="small" style={{marginLeft:8, opacity:.7}}>beta</span>
      </div>
      <div className="actions">
        {auth?.user && <span className="small" style={{marginRight:8, color:"var(--muted)"}}>
          {auth.user.display_name}
        </span>}
        {auth?.user ? (
          <button className="btn" onClick={async ()=>{ await logout(); setAuth({user:null,ready:true}); nav("/login");}}>Log out</button>
        ) : (
          <>
            <button className="btn" onClick={()=>nav("/login")}>Login</button>
            <button className="btn primary" onClick={()=>nav("/signup")}>Sign up</button>
          </>
        )}
      </div>
    </div>
  );
}

function AppShell(){
  const [, setRooms] = useAtom(roomsAtom);
  const [current, setCurrent] = useAtom(currentRoomAtom);

  useEffect(()=>{
    myRooms().then(rs=>{
      setRooms(rs);
      if (!current && rs.length) setCurrent(rs[0]);
    }).catch(()=>{});
  },[]);

  return (
    <div className="shell">
      <Rooms />
      <Chat />
      <CommandPalette />
    </div>
  );
}
<Route path="/invite/:code" element={<Page><Invite /></Page>} />

function Gate({ children }) {
  const [auth] = useAtom(authAtom);
  // If there is no token or no user, send to login
  if (!localStorage.getItem("access") || !auth.user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}


export default function App(){
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/login" element={<Page><Login /></Page>} />
            <Route path="/signup" element={<Page><Signup /></Page>} />
            <Route path="/verify" element={<Page><Verify /></Page>} />
            <Route path="/app" element={<Gate><Page><AppShell /></Page></Gate>} />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Routes>
        </AnimatePresence>
      </div>
    </BrowserRouter>
  );
}

function Page({children}){
  return (
    <motion.div
      key={location.pathname}
      initial={{ opacity:0, y:8 }}
      animate={{ opacity:1, y:0 }}
      exit={{ opacity:0, y:-8 }}
      transition={{ duration:.2, ease:"easeOut" }}
      style={{height:"100%"}}
    >
      {children}
    </motion.div>
  );
}
