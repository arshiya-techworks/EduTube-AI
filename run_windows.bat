@echo off
cd /d %~dp0backend
if not exist venv python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env copy .env.example .env
start "EduTube Backend" cmd /k "venv\Scripts\activate && uvicorn app.main:app --reload"
cd ..\frontend
call npm install
start "EduTube Frontend" cmd /k "npm run dev"
timeout /t 6 >nul
start http://localhost:5173
