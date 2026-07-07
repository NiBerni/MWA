# 🎬 MovieWebApp

A lightweight, secure Flask web application that allows users to search for their favorite movies via the OMDb API and
curate a personal movie dashboard.

Built with an emphasis on defensive programming, data security, and a clean, responsive dark-mode UI.

## ✨ Features

* **Secure Authentication:** User registration and login flow with Werkzeug password hashing.
* **Encrypted API Key Storage:** Users provide their own personal OMDb API keys during registration. Keys are
  transparently encrypted in the SQLite database using symmetric encryption (Fernet) to prevent plaintext exposure.
* **Dynamic Movie Search:** Live integration with the OMDb API to fetch movie posters, directors, release years, and
  IMDB ratings.
* **Personalized Dashboard:** Users can save movies to their favorites list. Database cascades ensure that if an account
  is deleted, all associated user data is safely wiped.
* **Profile Management:** Users can seamlessly update their passwords, swap out their OMDb API keys, or permanently
  delete their accounts.
* **Responsive Dark UI:** Frontend built with Bootstrap 5, featuring a sleek, responsive dark theme and interactive SVG
  UI elements.

## 🛠️ Tech Stack

* **Backend:** Python 3, Flask
* **Database:** SQLite, SQLAlchemy (ORM)
* **Security:** Cryptography (Fernet), Werkzeug Security
* **Frontend:** HTML5, Jinja2, Bootstrap 5 (CDN), Vanilla JavaScript
* **Testing:** Pytest, Flask-Testing

## 🚀 Getting Started

### Prerequisites

1. **Python 3.10+** installed on your machine.
2. An **OMDb API Key**. (Users will need to get a free key from [omdbapi.com](http://www.omdbapi.com/apikey.aspx) to
   register).

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/MVP_MovieWebApp.git
cd MVP_MovieWebApp
```

2. **Set up your virtual environment:**
   *(Note: This project includes a uv.lock file, meaning you can use the blazing-fast uv package manager, or standard
   venv/pip)*

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure Environment Variables:**
   Create a .env file in the root directory. You must generate a valid 32-url-safe-base64-encoded string for the Fernet
   encryption key.
   To generate an encryption key, run this in your python terminal:
   from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
   Add the following to your .env file:

```env
SECRET_KEY=your-super-secret-flask-session-key
ENCRYPTION_KEY=your-generated-fernet-key-here
```

4. **Initialize the Database & Run the App:**

   First, initialize the local SQLite database. This command will create `instance/moviewebapp.db` and provision all
   necessary tables:

```bash
flask init-db
```

Next, start the Flask development server:

```bash
flask run
```

The application will be available at [http://127.0.0.1:5000](https://www.google.com/search?q=http://127.0.0.1:5000).

## 🧪 Running Tests

This project employs Defensive TDD (Test-Driven Development). The test suite covers database cascades, session
invalidation, security injections, and OMDB client fetching.

To run the test suite:

```bash
pytest tests/ -v
```

## 📁 Project Structure

```text
MVP_MovieWebApp/
├── src/
│   ├── app.py             # Flask application factory
│   ├── auth.py            # Authentication & profile routing
│   ├── database.py        # SQLAlchemy db instance
│   ├── decorators.py      # Security & session guard clauses
│   ├── models.py          # SQLAlchemy ORM Models (User, Movie, Director)
│   ├── omdb_client.py     # External API integration layer
│   ├── routes.py          # API Endpoints
│   └── views.py           # Frontend HTML rendering routes
├── templates/             # Jinja2 HTML Templates
├── tests/                 # Pytest suite
├── instance/              # Local SQLite Database (auto-generated)
├── requirements.txt       # Dependencies
└── pyproject.toml         # Project metadata

```

## 🛡️ Security Considerations

* **Session Poisoning Prevention:** The application actively clears orphaned session cookies if database lookups fail or
  UUIDs are malformed.
* **Write-Only Passwords:** The User model enforces write-only access to password fields, preventing accidental logging
  or exposure of plaintext passwords.
* **Sanitized Deletion:** Deleting a user profile triggers SQLAlchemy cascades to wipe all associated foreign-key data,
  leaving no orphaned records in the database.

---

*Created as a Minimum Viable Product (MVP).*
'''