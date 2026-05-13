# Voice-Based Examination System

A secure AI-powered voice-based examination platform built using Flask and MongoDB.

The system supports:

* Voice-based answering
* AI-assisted grading
* Examiner & invigilator workflows
* Encrypted answer storage
* Anti-cheat monitoring
* Real-time exam sessions
* Student result management

---

# Features

## Authentication & Roles

* Multi-role login system
* Admin
* Invigilator
* Examiner
* Candidate(Student)

## Candidate Features

* Voice-based answering
* Autosave answers
* Text-to-Speech (TTS)
* Speech recognition
* Live exam timer
* Exam submission
* Result dashboard

## Invigilator Features

* Create exams
* Add/edit/delete questions
* Assign students to exams
* Start exams
* Monitor sessions

## Examiner Features

* View submitted answers
* Manual grading
* AI grading
* Result calculation
* Tamper detection

## Admin Features

* User management
* Examiner assignment
* Invigilator assignment
* Student management

## Security Features

* AES-256-GCM encrypted answers
* HMAC integrity verification
* Session validation
* Anti-tampering checks

---

# Tech Stack

## Backend

* Python
* Flask
* MongoDB
* PyMongo

## Frontend

* HTML
* CSS
* JavaScript

## Voice Features

* Speech Recognition API
* Text-to-Speech API

## Security

* Cryptography
* AES-256-GCM Encryption
* HMAC-SHA256 Integrity Checks

---

# Project Structure

```text
app/
├── routes/
├── services/
├── database/
├── utils/
├── middleware/
├── validators/
├── constants/
├── templates/
└── static/
```

---

# Installation

## Clone Repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

## Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Requirements

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create `.env` file:

```env
EXAM_MASTER_KEY=your-generated-master-key
FLASK_SECRET_KEY=your-secret-key
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=exam_db
```

Generate encryption key:

```bash
python -c "from app.services.crypto_service import generate_master_key; print(generate_master_key())"
```

---

# Run Application

```bash
python run.py
```

Default URL:

```text
http://127.0.0.1:5005
```

---

# Seed Database

```bash
python app/database/seed.py
```

---

# Demo Accounts

| Role        | Username    | Password       |
| ----------- | ----------- | -------------- |
| Admin       | admin       | admin123       |
| Invigilator | invigilator | invigilator123 |
| Examiner    | examiner    | examiner123    |
| Student     | student     | student123     |

---

# Logs & Uploads

## logs/

Stores:

* error logs
* voice logs
* anti-cheat logs
* session logs

## uploads/

Stores:

* exported PDFs
* temporary files
* audio files
* generated reports

---

# Future Improvements

* WebSocket real-time monitoring
* Advanced AI grading
* Semester-wise result system
* Voice command navigation
* Cross-platform TTS support
* Analytics dashboard
* PDF result generation
* Plagiarism detection

---

# License

This project is developed for educational and research purposes.
