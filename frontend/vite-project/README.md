# VibeCheck — Frontend

React (Vite) frontend for VibeCheck — record practice sessions and
view AI-generated performance feedback.

---

## Tech Stack

- **Framework:** React + Vite
- **Routing:** React Router
- **Styling:** Plain CSS (per-page stylesheets)
- **Node:** Requires Node.js 18+

---

## Project Structure

```
frontend/
└── vite-project/
    ├── public/
    │
    ├── src/
    │   ├── assets/
    │   │   ├── hero.png
    │   │   ├── logo.svg
    │   │   └── vite.svg
    │   │
    │   ├── activity.css
    │   ├── activity.jsx
    │   ├── analysis.css
    │   ├── analysis.jsx
    │   ├── api.js
    │   ├── App.css
    │   ├── App.jsx
    │   ├── dashboard.css
    │   ├── dashboard.jsx
    │   ├── index.css
    │   ├── login.jsx
    │   ├── main.jsx
    │   ├── progress.css
    │   ├── progress.jsx
    │   ├── record.css
    │   └── record.jsx
    │
    ├── .env
    ├── .gitignore
    ├── eslint.config.js
    ├── index.html
    ├── package-lock.json
    ├── package.json
    ├── README.md
    └── vite.config.js
```

---

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

Create a `.env` file in the project root (same folder as `package.json`)
by copying `.env.example`:

```bash
VITE_API_BASE=http://127.0.0.1:8000
```

This tells the frontend where to find the backend API. It's read in
`src/api.js` via `import.meta.env.VITE_API_BASE`, with a fallback to
`http://127.0.0.1:8000` if not set.

> `.env` is gitignored and won't be included when cloning the repo —
> you need to create it yourself using the value above (or your own
> backend URL if different).

### 3. Run the dev server

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

### 4. Backend must be running

This frontend expects a backend API running at the URL set in `.env`
(default `http://127.0.0.1:8000`). Start it separately — see
`backend/README.md`.

**Both servers need to run at the same time, in separate terminals:**

| Terminal | Command | Runs at |
|----------|---------|---------|
| 1 (frontend) | `npm run dev` | `http://localhost:5173` |
| 2 (backend) | see `backend/README.md` | `http://127.0.0.1:8000` |

If you log in and see "Failed to fetch," it usually means the backend
isn't running yet.

---

## Pages / Routes

| Route         | Component     | Description                              |
|---------------|---------------|-------------------------------------------|
| `/`           | `Login`       | Signup / login                            |
| `/dashboard`  | `Dashboard`   | Landing page after login                  |
| `/record`     | `Record`      | Camera capture + recording session        |
| `/analysis`   | `Analysis`    | Scores + AI feedback for a session        |
| `/activity`   | `Activity`    | List of past sessions                     |
| `/progress`   | `Progress`    | Improvement trends across sessions        |

---

## Auth

On successful login/signup, the JWT token is stored in
`localStorage` under `vibecheckToken` and sent as an
`Authorization: Bearer <token>` header on authenticated requests
(e.g. video upload).
