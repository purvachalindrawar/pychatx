import React, { useEffect, useState } from "react";
import { useAtom } from "jotai";
import { roomsAtom, currentRoomAtom } from "../store";
import { motion, AnimatePresence } from "framer-motion";

export default function CommandPalette(){
  const [open, setOpen] = useState(false);
  const [rooms] = useAtom(roomsAtom);
  const [, setCurrent] = useAtom(currentRoomAtom);
  const [q, setQ] = useState("");

  useEffect(()=>{
    const onKey = (e)=>{
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase()==="k"){
        e.preventDefault();
        setOpen(o=>!o);
      } else if (e.key==="Escape"){ setOpen(false); }
    };
    window.addEventListener("keydown", onKey);
    return ()=> window.removeEventListener("keydown", onKey);
  },[]);

  const filtered = rooms.filter(r => r.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="palette-backdrop"
          initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
          style={{position:"fixed", inset:0, background:"rgba(0,0,0,.5)"}}
          onClick={()=>setOpen(false)}
        >
          <motion.div
            initial={{ y:20, opacity:0 }} animate={{ y:0, opacity:1 }} exit={{ y:10, opacity:0 }}
            transition={{ duration:.15 }}
            style={{
              position:"absolute", left:"50%", top:"15%", transform:"translateX(-50%)",
              width:"min(680px, 92vw)", background:"var(--panel)", border:"1px solid rgba(255,255,255,.08)",
              borderRadius:16, padding:12, boxShadow:"0 20px 60px rgba(0,0,0,.5)"
            }}
            onClick={e=>e.stopPropagation()}
          >
            <input autoFocus className="input" placeholder="Search rooms…"
              value={q} onChange={e=>setQ(e.target.value)} />
            <div style={{maxHeight:300, overflow:"auto", marginTop:8}}>
              {filtered.map(r=>(
                <div key={r.id} className="room" onClick={()=>{ setCurrent(r); setOpen(false); }}>
                  <div>{r.name}</div>
                  <div className="small">{new Date(r.created_at).toLocaleDateString()}</div>
                </div>
              ))}
              {!filtered.length && <div className="small" style={{color:"var(--muted)", padding:8}}>No results</div>}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
