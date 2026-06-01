# Instagram Clone — Frontend

React + Vite + Tailwind SPA for the Instagram-clone backend.

## Requirements

- Node.js 18+ and npm

If Node is not installed (no sudo needed):

```bash
# install nvm, then the latest LTS Node
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
# restart your shell, then:
nvm install --lts
```

## Setup

```bash
cd frontend
npm install
```

Configure the API base URL (defaults to `http://localhost:8000`):

```bash
cp .env.example .env   # edit if your backend runs elsewhere
```

## Run

Start the backend first (`docker compose up`, or `python manage.py runserver`),
then:

```bash
npm run dev
```

The app runs at http://localhost:5173 (already whitelisted in the backend's
`CORS_ALLOWED_ORIGINS`).

## Auth flow

- Login with email or phone. The backend sends a 6-digit OTP.
- In `DEBUG` mode the backend returns a `dev_code` in the response, shown on the
  verify screen with an autofill button (no real email/SMS needed for testing).
- New email/phone values are signed up automatically on first verify.
- Access + refresh JWTs are stored in `localStorage`; the axios client refreshes
  the access token automatically on 401.

## Structure

```
src/
  api/client.js        axios instance + JWT refresh interceptor
  auth/tokenStore.js   localStorage token helpers
  auth/AuthContext.jsx auth state, login/logout, /me bootstrap
  components/          ProtectedRoute, Layout (sidebar shell), Spinner
  pages/              LoginPage, HomePage, PlaceholderPage
  App.jsx             routes
```
