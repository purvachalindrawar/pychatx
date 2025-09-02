import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { useAtom } from "jotai";
import { authAtom, roomsAtom, currentRoomAtom } from "./store";
import { myRooms, logout } from "./api";
import { motion, AnimatePresence } from "framer-motion";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Verify from "./pages/Verify";
import Rooms from "./pages/Rooms";
import Chat from "./pages/Chat";
import CommandPalette from "./components/CommandPalette";
import Invite from "./pages/Invite";

/* ------------------------- small theme helper (add-only) ------------------------- */
function useTheme() {
  const initial =
    (typeof window !== "undefined" &&
      (localStorage.getItem("theme") ||
        (window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"))) ||
    "dark";
  const [theme, setTheme] = useState(initial);

  useEffect(() => {
    // toggle a dataset attribute so CSS can react with [data-theme="light"]
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {}
  }, [theme]);

  return [theme, setTheme];
}
/* ------------------------------------------------------------------------------- */

function Header() {
  const [auth, setAuth] = useAtom(authAtom);
  const nav = useNavigate();
  const [theme, setTheme] = useTheme();

  return (
    <motion.div
      className="header"
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      <div
        className="brand"
        onClick={() => nav("/app")}
        style={{ cursor: "pointer" }}
      >
        {/* subtle animated glow on the badge */}
        <motion.div
          className="brand-badge"
          animate={{
            boxShadow: [
              "0 0 0px rgba(120, 80, 255, .0)",
              "0 0 12px rgba(120, 80, 255, .35)",
              "0 0 0px rgba(120, 80, 255, .0)",
            ],
            scale: [1, 1.025, 1],
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
        PyChatX
        <span className="small" style={{ marginLeft: 8, opacity: 0.7 }}>
          beta
        </span>
      </div>

      <div className="actions">
        {/* theme toggle — no other files required; CSS patch can enhance later */}
        <button
          className="btn"
          title="Toggle theme"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          style={{ marginRight: 8 }}
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>

        {auth?.user && (
          <span className="small" style={{ marginRight: 8, color: "var(--muted)" }}>
            {auth.user.display_name}
          </span>
        )}

        {auth?.user ? (
          <button
            className="btn"
            onClick={async () => {
              await logout();
              setAuth({ user: null, ready: true });
              nav("/login");
            }}
          >
            Log out
          </button>
        ) : (
          <>
            <button className="btn" onClick={() => nav("/login")}>
              Login
            </button>
            <button className="btn primary" onClick={() => nav("/signup")}>
              Sign up
            </button>
          </>
        )}
      </div>
    </motion.div>
  );
}

function AppShell() {
  const [, setRooms] = useAtom(roomsAtom);
  const [current, setCurrent] = useAtom(currentRoomAtom);

  useEffect(() => {
    myRooms()
      .then((rs) => {
        setRooms(rs);
        if (!current && rs.length) setCurrent(rs[0]);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="shell">
      <Rooms />
      <Chat />
      <CommandPalette />
    </div>
  );
}

function Gate({ children }) {
  const [auth] = useAtom(authAtom);
  // if no token or no known user, send to login
  if (!localStorage.getItem("access") || !auth.user) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/* page wrapper with safe key (uses router location, not global) */
function Page({ children }) {
  const location = useLocation();
  return (
    <motion.div
      key={location.pathname}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      style={{ height: "100%" }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  // AnimatePresence needs the location/key from the Router context
  return (
    <BrowserRouter>
      <div className="app">
        <Header />
        <AnimatePresence mode="wait" initial={false}>
          <Routes location={location} key={location.pathname}>
            <Route path="/login" element={<Page><Login /></Page>} />
            <Route path="/signup" element={<Page><Signup /></Page>} />
            <Route path="/verify" element={<Page><Verify /></Page>} />
            {/* NEW: deep-link route to accept invite codes */}
            <Route path="/invite/:code" element={<Page><Invite /></Page>} />
            <Route
              path="/app"
              element={
                <Gate>
                  <Page>
                    <AppShell />
                  </Page>
                </Gate>
              }
            />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Routes>
        </AnimatePresence>
      </div>
    </BrowserRouter>
  );
}
