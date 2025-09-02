import axios from "axios";

const BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
export const FRONT = import.meta.env.VITE_FRONTEND_URL || window.location.origin;
export function inviteLink(code){ return `${FRONT}/invite/${encodeURIComponent(code)}`; }

export const storage = {
  get access() { return localStorage.getItem("access") || ""; },
  set access(t){ localStorage.setItem("access", t); },
  get refresh(){ return localStorage.getItem("refresh") || ""; },
  set refresh(t){ localStorage.setItem("refresh", t); },
  get user(){ try{return JSON.parse(localStorage.getItem("user")||"null")}catch{ return null } },
  set user(u){ localStorage.setItem("user", JSON.stringify(u)); },
  clear(){ localStorage.removeItem("access"); localStorage.removeItem("refresh"); localStorage.removeItem("user"); }
};

const api = axios.create({ baseURL: BASE, timeout: 15000 });

api.interceptors.request.use(cfg => {
  const t = storage.access;
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

let refreshing = null;
api.interceptors.response.use(
  r => r,
  async err => {
    const { config, response } = err;
    if (response?.status === 401 && storage.refresh && !config.__retry) {
      config.__retry = true;
      refreshing = refreshing ?? api.post("/auth/refresh", { refresh_token: storage.refresh })
        .then(r => r.data)
        .finally(()=> refreshing = null);
      const data = await refreshing;
      storage.access = data.access_token;
      storage.refresh = data.refresh_token;
      config.headers.Authorization = `Bearer ${storage.access}`;
      return api(config);
    }
    return Promise.reject(err);
  }
);

// ---- API ----
export async function signup(email, password, display_name){
  return api.post("/auth/signup", { email, password, display_name }).then(r=>r.data);
}
export async function verify(token){
  return api.get("/auth/verify", { params: { token }}).then(r=>r.data);
}
export async function login(email, password){
  const d = await api.post("/auth/login", { email, password }).then(r=>r.data);
  storage.access = d.access_token; storage.refresh = d.refresh_token;
  const me = await api.get("/users/me").then(r=>r.data);
  storage.user = me;
  return me;
}
export async function logout(){
  try{ await api.post("/auth/logout"); }catch{}
  storage.clear();
}
export async function myRooms(){
  return api.get("/rooms").then(r=>r.data);
}
export async function createRoom(name, is_private=false){
  return api.post("/rooms", { name, is_private }).then(r=>r.data);
}
export async function joinByInvite(invite_code){
  return api.post("/rooms/join", null, { params: { invite_code }}).then(r=>r.data);
}
export async function listMessages(room_id){
  return api.get("/messages", { params: { room_id }}).then(r=>r.data);
}
export async function postMessage(room_id, content, parent_id=null, mentions=[]){
  return api.post("/messages", { room_id, content, parent_id, mentions }).then(r=>r.data);
}
export async function searchMessages(room_id, q){
  return api.get("/search/messages", { params: { room_id, q }}).then(r=>r.data);
}
export async function addReaction(message_id, emoji){
  return api.post("/reactions/add", { message_id, emoji }).then(r=>r.data);
}
export async function removeReaction(message_id, emoji){
  return api.post("/reactions/remove", { message_id, emoji }).then(r=>r.data);
}
export async function markDelivered(message_ids){
  return api.post("/receipts/delivered", { message_ids }).then(r=>r.data);
}
export async function markRead(message_ids){
  return api.post("/receipts/read", { message_ids }).then(r=>r.data);
}

export function wsUrl(room_id, user_id){
  const u = new URL(BASE);
  const proto = u.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${u.host}/ws?room_id=${encodeURIComponent(room_id)}&user_id=${encodeURIComponent(user_id)}`;
}
