# Excel QA - Simple Deployment Guide

## Overview
A minimalistic chat interface to ask questions about CSV data using AI. Simple single-file storage system.

## How It Works

### Single Data File System
- Admin uploads a CSV file
- File is saved as `data/current_data.csv`
- **Each new upload replaces the previous file**
- All users (admin and regular) access the same data
- No need for S3 or complex storage

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
cp .env.example .env
nano .env
```

Add your Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Run the Server
```bash
python main.py
```

Or:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Access the Application
Open browser to: `http://localhost:8000`

**Login Credentials:**
- Admin: `admin` / `admin123`
- User: `user` / `user123`

## User Roles

### Admin
- Can upload CSV files
- Upload replaces the current data for all users
- Can chat and ask questions

### Regular User
- Can only chat and ask questions
- Uses the data uploaded by admin

## File Structure
```
excelqa/
├── main.py              # FastAPI backend
├── data/                # Data directory (auto-created)
│   └── current_data.csv # Current data file (replaced on upload)
├── static/              # Frontend files
│   ├── login.html
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── requirements.txt
├── .env                 # Your config (create from .env.example)
└── README.md
```

## Usage Flow

### Admin Workflow:
1. Login as admin
2. Upload a CSV file using the "Upload File" button
3. File is saved and data is immediately available
4. Upload a new file to replace the old one
5. Ask questions in the chat

### User Workflow:
1. Login as user
2. Ask questions about the data in the chat
3. Wait for admin to upload data if none is available

## Sample Questions
- "How many rows are there?"
- "What are the column names?"
- "Show me the first 5 rows"
- "What is the average salary?"
- "How many employees in Engineering department?"

## Deployment on Server

### Option 1: Using systemd (Recommended)
```bash
sudo nano /etc/systemd/system/excelqa.service
```

Add:
```ini
[Unit]
Description=Excel QA Application
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/excelqa
Environment="PATH=/path/to/excelqa/env/bin"
ExecStart=/path/to/excelqa/env/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable excelqa
sudo systemctl start excelqa
sudo systemctl status excelqa
```

### Option 2: Using screen (Quick & Simple)
```bash
screen -S excelqa
python main.py
# Press Ctrl+A then D to detach
```

To reattach:
```bash
screen -r excelqa
```

## Backup the Data
```bash
# Backup the current data file
cp data/current_data.csv backup_$(date +%Y%m%d).csv
```

## Troubleshooting

### No data loaded
- Admin needs to upload a CSV file first
- Check if `data/` directory exists and has write permissions

### Can't upload file
- Check disk space: `df -h`
- Verify user is logged in as admin
- Check file permissions on `data/` directory

### Application won't start
- Verify `.env` file exists with valid API key
- Check if port 8000 is available: `lsof -i :8000`
- Review logs for errors

## Security Notes

⚠️ **For Production:**
1. Change default passwords in `main.py`
2. Use environment variables for credentials
3. Enable HTTPS
4. Add authentication middleware
5. Implement rate limiting
6. Regular backups of data file

## API Endpoints

- `GET /` - Login page
- `POST /login` - Authentication
- `GET /chat` - Chat interface  
- `POST /upload-csv` - Upload CSV (Admin only)
- `POST /ask` - Ask questions about data
- `GET /health` - Health check
- `GET /data/info` - Dataset information

## Tech Stack
- **Backend:** FastAPI, Python
- **AI:** Google Gemini 2.5 Flash
- **Data Processing:** Pandas, LangChain
- **Frontend:** Vanilla HTML/CSS/JavaScript

## Requirements
- Python 3.8+
- Google Gemini API key
- ~10MB disk space for data storage

---

**That's it!** Simple, lightweight, and easy to deploy. 🚀
