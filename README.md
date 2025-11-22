# ConnectPU (Upload-only avatars)

A minimal Tinder-style dating web app built with Flask and **direct profile photo uploads** (no image URLs).

## Features

- User registration and login
- Editable profiles (name, age, gender, bio, interests, location)
- Profile photo upload (stored in `static/uploads/`)
- Swipe-style discover screen with like / pass and basic filters
- Mutual matches list
- Simple one-to-one chat between matched users
- Clean, responsive UI

## Quick start

```bash
# create and activate virtual environment (example for Windows PowerShell)
python -m venv venv
venv\Scripts\activate

# or on macOS / Linux
# python3 -m venv venv
# source venv/bin/activate

pip install -r requirements.txt

# run the app
python app.py
```

The app will create an SQLite database `connect_pu.db` on first run.

> IMPORTANT: open `app.py` and change `SECRET_KEY` before deploying anywhere public.
