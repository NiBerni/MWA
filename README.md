# MVP_MovieWebApp

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/yourusername/MVP_MovieWebApp/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/MVP_MovieWebApp/actions/workflows/ci.yml)

**MVP_MovieWebApp** is a lightweight movie database web application built to help you keep track of your favorite films.
It's designed with simplicity and functionality in mind, adhering to modern Python standards and best practices.

## Project Structure

```text
MVP_MovieWebApp
├── .cadence             # Cadence configuration for development workflow
├── src                  # Source code directory
│   ├── templates        # HTML templates for the web application
│   └── app.py           # Main application file
├── tests                # Test cases for the application
├── .env.example         # Example environment variables file
├── pyproject.toml       # Project configuration file for poetry
├── README.md            # This documentation file
└── requirements.txt     # List of project dependencies
```

## Tech Stack & Standards

- **Python 3.14**: The application is built using Python 3.14, ensuring compatibility and performance.
- **Flask**: A micro web framework for building the backend.
- **SQLAlchemy 2.1**: ORM to interact with the database efficiently.
- **Jinja2**: For templating HTML files.
- **PEP 8 & PEP 20**: Adherence to Python's style guide and Zen of Python for clean and maintainable code.

## Getting Started

### Prerequisites

- Ensure you have Python 3.14 installed on your system.
- It’s recommended to use a virtual environment for this project.

### Installation

1. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment:**
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On macOS and Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**
   ```bash
   python src/app.py
   ```

## Usage

To see the application in action, simply open your browser and navigate to `http://127.0.0.1:5000/`.

Here's a simple example of how you can interact with the application:

```python
from src.app import app, db
from src.models import Movie

# Add a new movie to the database
with app.app_context():
	new_movie = Movie(title="Inception", year=2010)
	db.session.add(new_movie)
	db.session.commit()
```

## Outlook (Known Issues & Future Features)

### Known Issues

- **Database Migration:** Currently, there's no built-in migration system for handling schema changes.
- **User Authentication:** Basic user authentication is not implemented.

### Future Features

- **Advanced Search:** Implement a more sophisticated search functionality to find movies by title, genre, etc.
- **User Profiles:** Allow users to create profiles and save their favorite movies.
- **Integration with IMDb API:** Fetch movie data from the IMDb database for up-to-date information.

We believe that "code is never truly finished" and welcome contributions from the community. Feel free to open issues,
submit pull requests, or share your ideas!

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make changes and commit them (`git add . && git commit -m 'Add some feature'`).
4. Push the changes to your forked repository (`git push origin feature/your-feature`).
5. Open a pull request.

We look forward to your contributions!

---

**Maintainer:** [Your Name]

**License:** MIT License

**Project Home:** [GitHub Repository URL]