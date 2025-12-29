# 🏆 Battlify

A web application for creating, managing, and voting on music tournaments. Users can generate brackets from Spotify playlists, vote on matchups in real-time, and view dynamic "tree-style" visualizations of the results.

## ✨ Features

* **Spotify Integration:** Automatically generate tournament brackets from Spotify playlists or albums.
* **Dynamic Visualizations:** Interactive "Split Tree" bracket view that scales with tournament size.
* **Real-time Voting:** Users can vote on active rounds with instant updates.
* **Admin Management:** Secure admin dashboard to create, delete, and manage tournaments.
* **Responsive Design:** Optimized for both desktop and mobile viewing.
* **Dockerized:** Fully containerized for easy deployment.

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI
* **Database:** MongoDB
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Integration:** Spotify Web API (Spotipy)
* **Testing:** Pytest, HTTPX
* **Infrastructure:** Docker, Docker Compose, GitHub Actions

## 📂 Project Structure

```bash
tournament_app/
├── app/                  # Backend Logic
│   ├── routes/           # API Endpoints (admin.py, voting.py)
│   ├── services/         # Business Logic (bracket_service.py, spotify_service.py)
│   ├── database.py       # MongoDB Connection
│   └── main.py           # FastAPI Entry Point
├── frontend/             # Static Frontend Files
│   ├── styles.css        # Visual Styles (Bracket logic)
│   ├── script.js         # Frontend Logic (Auth, Timers, Fetch)
│   └── *.html            # Pages (Vote, Manage, Index, Create)
├── tests/                # Automated Tests
├── docker-compose.yml    # Container Orchestration
└── requirements.txt      # Python Dependencies
``` 

## 🚀 Quick Start

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop) installed.
* A [Spotify Developer Account](https://developer.spotify.com/dashboard/) (for Client ID/Secret).

### 1. Clone the Repository
```bash
git clone https://github.com/anightatheopera/tournament_website
cd tournament_website
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory with the following variables:
```env
MONGO_URI=mongodb://mongo:27017
DB_NAME=tournament_db
SITE_ADMIN_PASSWORD=your_secure_password
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

### 3. Build and Run with Docker
The app will be available at `http://localhost:8000`.
```bash
docker-compose up --build
```     

## 🧪 Running Tests
You can run the full test suite inside the container or locally.

### Using Docker
```bash
docker-compose exec app pytest
```

### Locally (requires venv)
Ensure you have the dependencies installed:
```bash
pip install -r requirements.txt
pytest
```

## 📄 License
GNU General Public License v3.0 (GPL-3.0). See `LICENSE` file for details.
