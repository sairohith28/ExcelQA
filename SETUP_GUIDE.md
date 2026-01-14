# Excel QA Application - Setup Guide

A minimalistic chat interface to ask questions about CSV data using AI, with S3 integration for data storage.

## Features

- 🔐 Simple login system (Admin/User roles)
- 📤 CSV upload to S3 (Admin only)
- 🔗 Load CSV from S3 URL (All users)
- 💬 Chat interface to ask questions about data
- 🤖 AI-powered answers using Google Gemini

## Prerequisites

- Python 3.8+
- AWS Account with S3 bucket
- Google Gemini API key

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-bucket-name
   ```

3. **Configure S3 Bucket:**
   - Create an S3 bucket in your AWS account
   - Ensure your AWS credentials have permissions to:
     - Upload files (PutObject)
     - Download files (GetObject)
   - Update `S3_BUCKET_NAME` in `.env`

## Running the Application

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at: **http://localhost:8000**

## Usage

### 1. Login

Open http://localhost:8000 and login with:

**Admin Account:**
- Username: `admin`
- Password: `admin123`

**User Account:**
- Username: `user`
- Password: `user123`

### 2. Load Data

**For Admin:**
- Upload CSV file directly → Automatically uploads to S3
- Or enter S3 URL to load existing data

**For Users:**
- Enter S3 URL to load data

### 3. Ask Questions

Once data is loaded, ask questions in the chat interface:
- "How many rows are there?"
- "What are the column names?"
- "What is the average of column X?"
- "Show me the top 5 values"

## API Endpoints

- `GET /` - Login page
- `POST /login` - Authentication
- `GET /chat` - Chat interface
- `POST /upload-csv` - Upload CSV to S3 (Admin)
- `POST /load-from-s3` - Load CSV from S3 URL
- `POST /ask` - Ask questions about data
- `GET /health` - Health check
- `GET /data/info` - Get dataset information

## Project Structure

```
excelqa/
├── main.py              # FastAPI backend
├── finalapp.py          # Original standalone script
├── static/              # Frontend files
│   ├── login.html       # Login page
│   ├── index.html       # Chat interface
│   ├── styles.css       # Styling
│   └── script.js        # Frontend logic
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
└── .env.example         # Example environment file
```

## Security Notes

⚠️ **Important for Production:**

1. Replace the simple in-memory user store with a proper database
2. Use proper password hashing (bcrypt, argon2)
3. Implement JWT tokens for authentication
4. Add HTTPS/SSL
5. Restrict CORS origins
6. Use IAM roles instead of hardcoded AWS credentials
7. Add rate limiting
8. Implement proper session management

## Troubleshooting

**Data not loading:**
- Check if CSV format is correct (first row should be headers)
- Verify S3 bucket permissions
- Check AWS credentials in `.env`

**API errors:**
- Ensure Google API key is valid
- Check if all dependencies are installed
- Verify `.env` file is in the project root

**S3 upload fails:**
- Verify bucket name and region
- Check AWS credentials have write permissions
- Ensure bucket exists and is accessible

## Sample CSV Format

Your CSV should have headers in the second row (first row gets promoted to headers):

```csv
Name,Age,City
John,30,New York
Jane,25,Los Angeles
```

## License

MIT License
