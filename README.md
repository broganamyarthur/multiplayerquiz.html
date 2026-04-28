# Quiz Web App

A multiplayer quiz application built with Flask and SocketIO.

## Features
- Single-player and multiplayer quiz modes
- Real-time multiplayer gameplay
- Multiple choice questions with images
- Leaderboards and scoring

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

3. Open http://localhost:5000

## Deployment to Railway

1. Go to [Railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account and select this repository
4. Railway will automatically detect the Python app and deploy it
5. Your app will be live at `https://your-project-name.railway.app`

## Tech Stack
- **Backend**: Flask + SocketIO
- **Frontend**: HTML, CSS, JavaScript
- **Real-time**: WebSockets
- **Hosting**: Railway (Python support)