# Logistics Tracking Dashboard

A modern, full-stack logistics tracking application. Built with React (Vite), FastAPI, and PostgreSQL (with local SQLite fallback for out-of-the-box local development).

## Project Structure
- `frontend/` - React application representing the Premium UI Dashboard and Live Activity Map.
- `backend/` - FastAPI service representing the API endpoints and Database models.

## Prerequisites
- **Node.js** & **npm** (for the frontend)
- **Python 3.8+** (for the backend)

---

## 🚀 Quick Start Guide

### 1. Setting up the Backend

1. Open a new terminal and navigate to the backend folder:
   ```powershell
   cd backend
   ```
2. (Optional but recommended) Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install the required Python dependencies:
   ```powershell
   pip install fastapi uvicorn sqlalchemy psycopg2-binary asyncpg python-dotenv greenlet mangum pydantic
   ```
4. **Seed the database:** Populate your empty database with mock active shipment data to test out tracking:
   ```powershell
   python seed.py
   ```
5. **Start the API Server:**
   ```powershell
   uvicorn main:app --reload
   ```
   *The backend routes will now broadcast on `http://localhost:8000`.*

---

### 2. Setting up the Frontend

1. Open a second detached terminal window and navigate to the frontend folder:
   ```powershell
   cd frontend
   ```
2. Install necessary React packages:
   ```powershell
   npm install
   ```
3. **Start the Development Server:**
   ```powershell
   npm run dev
   ```
   *Load up the application at `http://localhost:5173`.*

---

## Deployments 

### Frontend (Netlify)
1. Within Netlify's web console, link your Git repository.
2. The `netlify.toml` file at the root automatically dictates how Netlify operates:
   - **Base directory:** `frontend/`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist/`
   - *It will also correctly intercept routing commands to safeguard React Single Page App logic!*

### Backend (Render / API)
The Python framework logic includes `mangum`, ensuring it is 100% compliant with standard Serverless deployment architecture. It is highly recommended to bridge the API structure using something simple like **Render.com** or **Railway**. Use start command `uvicorn main:app --host 0.0.0.0 --port 10000`.

## Switching to PostgreSQL safely
By standard default, `database.py` generates a lightweight local SQLite Database (`logistics.db`). To permanently upgrade to your Postgres production database:
1. Ensure your PostgreSQL server is active.
2. In your deployment console (or local `.env`), store the absolute connection path explicitly:
   `DATABASE_URL="postgresql://user:password@localhost:5432/dbname"`
