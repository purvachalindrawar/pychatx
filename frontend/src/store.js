import { atom } from "jotai";

function getSavedUser() {
  try { return JSON.parse(localStorage.getItem("user") || "null"); }
  catch { return null; }
}

// Initialize from localStorage so there’s no “blank” frame
export const authAtom = atom({
  user: getSavedUser(),
  ready: true
});

export const roomsAtom = atom([]);
export const currentRoomAtom = atom(null);
export const messagesAtom = atom([]);
export const typingAtom = atom(new Set());
