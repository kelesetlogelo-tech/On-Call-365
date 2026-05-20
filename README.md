# MedPractice - Medical Practice Management System

A modern web application for managing a medical practice — patients, doctors, and appointments — all in one place.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-green) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)

---

## Features

- **Dashboard** with real-time stats, weekly charts, and upcoming appointments
- **Patient Management** — add, view, edit, search, and delete patients
- **Doctor Management** — manage doctors with specializations and active/inactive status
- **Appointment Scheduling** — schedule, reschedule, and track appointment status
- **User Authentication** — secure login and registration
- **Responsive Design** — works on desktop and mobile

---

## Quick Start (3 Steps)

### Prerequisites

You only need **Python 3.9 or newer** installed on your computer.

- **Check if Python is installed**: Open a terminal/command prompt and type:
  ```
  python --version
  ```
  If you see something like `Python 3.x.x`, you're good to go!

- **Don't have Python?** Download it free from [python.org](https://www.python.org/downloads/). During installation on Windows, check the box that says **"Add Python to PATH"**.

---

### Step 1 — Install Dependencies

Open a terminal/command prompt, navigate to this project folder, and run:

```bash
pip install -r requirements.txt
```

### Step 2 — Set Up the Database with Sample Data

```bash
python seed_data.py
```

This creates the database and adds sample patients, doctors, and appointments so you can explore right away.

### Step 3 — Start the Application

```bash
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
```

**Open your web browser and go to:** [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Login Credentials

After running the seed script, use these credentials to log in:

| Username | Password    |
|----------|-------------|
| `admin`  | `admin123`  |

You can also create a new account using the **Register** page.

---

## Project Structure

```
medical-practice-mgmt/
├── app.py                  # Main application (routes & logic)
├── config.py               # Configuration settings
├── models.py               # Database models
├── forms.py                # Form definitions
├── seed_data.py            # Sample data script
├── requirements.txt        # Python dependencies
├── instance/
│   └── medical_practice.db # SQLite database (created automatically)
├── static/
│   ├── css/style.css       # Custom styles
│   └── js/main.js          # Custom JavaScript
└── templates/              # HTML templates
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── patients/
    ├── appointments/
    └── doctors/
```

---

## How It Works

- **Database**: All data is stored in a single SQLite file (`instance/medical_practice.db`). No separate database server needed.
- **Web Server**: Flask runs a local web server on your computer. Only you can access it (it's not on the internet).
- **Security**: Passwords are hashed (not stored as plain text). All pages require login.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` command not found | Try `python3` instead of `python` |
| `pip` command not found | Try `pip3` instead of `pip` |
| Port 5000 already in use | Change the port in `app.py` (last line) to e.g. `port=8080` |
| Database errors | Delete the `instance/` folder and re-run `python seed_data.py` |

---

## Tech Stack

| Component   | Technology  | Why?                                |
|-------------|-------------|-------------------------------------|
| Backend     | Flask       | Simplest Python web framework       |
| Database    | SQLite      | Zero configuration, just a file     |
| Frontend    | Bootstrap 5 | Modern, responsive UI out of the box|
| Icons       | Bootstrap Icons | Clean, professional icons       |
| Auth        | Flask-Login | Simple session-based authentication |
