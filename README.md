# PyChatX — Real-time Team Chat (FastAPI + React)

A production-style chat app with secure signup/login & email verification, WebSocket messaging, emoji reactions, read/delivered receipts, room invites (code & deep-link), search, and a responsive dark UI.

**Frontend (Vercel):** https://pychatx.vercel.app  
**Backend (Render / API docs):** https://pychatx-backend.onrender.com/docs  
**Database:** Neon Postgres

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Monorepo Layout](#monorepo-layout)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Invites & Deep-Linking](#invites--deep-linking)
- [Deploy](#deploy)
  - [Backend → Render](#backend--render)
  - [Frontend → Vercel](#frontend--vercel)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [License](#license)

---

## Features

- **Auth & Email Verification**
  - JWT (access/refresh), email verification via Gmail SMTP (app password)
- **Rooms**
  - Public/private, invite by **code** or **shareable link**
- **Real-time Chat**
  - WebSockets for new messages and typing indicators
  - Delivered / read receipts
  - Emoji reactions
- **Search**
  - Client-side message search within a room
- **Responsive UI**
  - Works on desktop & mobile, dark theme by default
- **Ops**
  - Prometheus metrics (`/metrics`)
  - Optional Sentry integration
  - Strict CORS & security headers

---

## Tech Stack

**Backend:** FastAPI · Psycopg 3 · Postgres (Neon) · python-jose (JWT) · Passlib (bcrypt) · aiosmtplib · Uvicorn  
**Frontend:** React + Vite · Jotai · Framer Motion  
**Infra:** Render (backend) · Vercel (frontend)  
**Optional:** S3-compatible storage (presigned uploads), Web Push, Sentry

---



---

## Environment Variables

Create **`backend/.env`** (example):

```env
# ---- Database (Neon) ----
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require

# ---- JWT ----
JWT_SECRET=change-this-to-a-long-random-string
JWT_ALGO=HS256
ACCESS_MIN=120
REFRESH_DAYS=14
ISSUER=pychatx

# ---- SMTP (Gmail app password) ----
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourgmail@gmail.com
SMTP_PASS=your-google-app-password
SMTP_FROM="PyChatX <yourgmail@gmail.com>"

# ---- CORS / Frontend origin ----
APP_ORIGIN=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# ---- Optional: S3 / R2 (uploads) ----
S3_ENDPOINT=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_PRESIGN_EXPIRE=3600
S3_PUBLIC_BASE_URL=

# ---- Optional: Sentry / Web Push ----
SENTRY_DSN=
SENTRY_ENV=dev
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_EMAIL=

```


## Monorepo Layout

