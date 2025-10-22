# 🧠 Flask String Analyzer

A lightweight Flask application that analyzes strings and returning details such as word count, unique characters, palindrome check, SHA-256 hash, and more.  
Initially built with **SQLite** for local development, then migrated to **PostgreSQL** for deployment.

---

## 🚀 Features

- Routes that allows:
    - Add strings
    - Search strings
    - Accepts natural language as search queries
    - Search strings with filters
- Errors are dynamically handled with their corresponding status code
- Analyzes text and stores results in a relational database.
- Computes:
  - String length
  - Word count
  - Unique characters
  - Character frequency map
  - Palindrome detection
  - SHA-256 hash
- Displays analysis results as JSON.

---

## 🧩 Tech Stack

- **Flask** (Python backend)
- **SQLAlchemy** ORM
- **SQLite** (local)
- **PostgreSQL** (production)
- **Gunicorn** (for deployment)
- **Railway** 

---

## 🧠 Project Structure
│
├── app.py # Main Flask app
├── requirements.txt
├── Procfile # For deployment
└── README.md

---

## 🧰 Local Development Setup

### 1 Clone the repository
"git clone https://github.com/yourusername/flask-string-analyzer.git"
cd flask-string-analyzer
### 2 Create and activate a virtual environment
  - python -m venv venv
  - source venv/bin/activate   # macOS/Linux
  - venv\Scripts\activate      # Windows
### 3 Install dependencies
  - pip install -r requirements.txt
### 4 Setup environment variables

### 5 Initialize the database
from app import db
db.create_all()
exit()

### 5 Run the application
python app run
- app should run on  "http://127.0.0.1:5000/strings"

## 🧪 Testing Locally
To test the endpoints directly, make sure the app is running.
Use curl to send requests in "Windows powershell" 

- curl -X POST http://127.0.0.1:5000/strings \ -H "Content-Type: application/json" \ -d '{"text": "madam"}'

- replace madam with any strings you like to analyze
---

🧑‍💻 Author

Abdulhafeez Agunloye
Python Developer | Flask Enthusiast | Backend Engineer

---

🪶 License

This project is open-source under the MIT License.