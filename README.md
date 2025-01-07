# Aptitude Platform

Aptitude Platform is a Django web application designed to help users practice and improve their aptitude skills by solving daily problems. Features include user registration, login, solving daily problems, viewing leaderboards, and reviewing past problems.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- **User Authentication**: Registration, Login, Profile management, Logout.
- **Daily Problems**: Solve problems within a specific time window (17:00 to 22:00).
- **Leaderboards**: Daily and Monthly leaderboards.
- **Past Problems Review**: Access past problems with correct answers.

## Installation

### Prerequisites

- Python 3.6+
- Django 3.0+
- SQLite (default database)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aptitude-platform.git
   cd aptitude-platform
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. Run the development server:
   ```bash
   python manage.py runserver
   ```
7. Open the app in your browser: `http://127.0.0.1:8000/`.

## Usage

- **User Authentication**: Register, log in, and manage your profile.
- **Daily Problems**: Solve problems during the specified window (17:00 to 22:00).
- **Leaderboards**: View daily and monthly leaderboards.
- **Past Problems**: Review previous problems and answers.

## Project Structure

```
aptitude_platform/
├── aptitude/
│   ├── models.py
│   ├── views.py
│   ├── templates/
│   └── ...
├── aptitude_platform/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── README.md
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
