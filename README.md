# Excel QA - AI-Powered CSV Query System

A lightweight, minimalistic chat interface to ask questions about your CSV data using Google Gemini AI.

## Features

✅ **Simple Chat Interface** - Clean, modern UI for asking questions  
✅ **AI-Powered Answers** - Uses Google Gemini for intelligent responses  
✅ **Role-Based Access** - Admin can upload, all users can query  
✅ **Single File Storage** - Simple file management, no database needed  
✅ **Real-time Updates** - Upload new data instantly replaces old data  
✅ **No Setup Complexity** - Just upload CSV and start asking questions  

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Run the Application

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Access the App

Open browser: `http://localhost:8000`

**Login Credentials:**
- Admin: `admin` / `admin123`
- User: `user` / `user123`

## How It Works

1. **Admin uploads CSV** → File saved to `data/current_data.csv`
2. **Data loaded** → Pandas DataFrame created
3. **LangChain Agent** → Created with Gemini AI model
4. **Users ask questions** → Agent analyzes data and responds
5. **New upload** → Replaces old file, all users get new data

### Data Flow
```
Admin Upload → data/current_data.csv → Pandas DataFrame → LangChain Agent → AI Response
```

## User Roles

### Admin
- **Upload CSV files** - Replace current data
- **Ask questions** - Query the data via chat

### Regular User  
- **Ask questions** - Query the data via chat
- Uses data uploaded by admin

## Project Structure

```
excelqa/
├── main.py                 # FastAPI backend
├── data/                   # Data storage (auto-created)
│   └── current_data.csv   # Current data file (replaced on upload)
├── static/                 # Frontend files
│   ├── login.html         # Login page
│   ├── index.html         # Chat interface
│   ├── styles.css         # Styling
│   └── script.js          # Frontend logic
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── .env.example           # Example environment file
├── README.md              # This file
├── SIMPLE_SETUP.md        # Quick setup guide
└── EC2_DEPLOYMENT.md      # Deployment guide

```

## Sample Questions

- "How many rows are there?"
- "What are the column names?"
- "Show me the first 5 rows"
- "What is the average of column X?"
- "How many unique values in column Y?"
- "Show me records where column Z > 100"
- "What's the total sum of column A?"

## API Endpoints

### Public Endpoints
- `GET /` - Login page
- `POST /login` - Authentication
- `GET /health` - Health check

### Authenticated Endpoints
- `GET /chat` - Chat interface
- `POST /ask` - Ask questions (all users)
- `POST /upload-csv` - Upload CSV (admin only)
- `GET /data/info` - Dataset information

## Deployment

### Local Development
```bash
python main.py
# Access at http://localhost:8000
```

### Production (systemd)
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

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable excelqa
sudo systemctl start excelqa
```

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t excelqa .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --env-file .env excelqa
```

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **AI/ML**: Google Gemini 2.5 Flash, LangChain, LangChain Experimental
- **Data Processing**: Pandas
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: Session-based (in-memory)

## Requirements

- Python 3.8 or higher
- Google Gemini API key (free tier available)
- ~10MB disk space for application
- Additional space for CSV data files

## Security Considerations

⚠️ **For Production Deployment:**

1. **Change default passwords** in `main.py`
2. **Use proper authentication** - JWT tokens, OAuth, etc.
3. **Enable HTTPS** - Use reverse proxy (nginx) with SSL
4. **Database for users** - Replace in-memory USERS dict
5. **Rate limiting** - Prevent API abuse
6. **Input validation** - Sanitize file uploads
7. **Environment variables** - Never commit .env file
8. **Regular backups** - Backup data/ directory
9. **Access control** - Implement proper authorization
10. **Update dependencies** - Keep packages up to date

## Troubleshooting

### Application won't start
```bash
# Check if port 8000 is available
lsof -i :8000

# Check logs
journalctl -u excelqa -f

# Verify environment
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('API Key:', 'Set' if os.getenv('GOOGLE_API_KEY') else 'Missing')"
```

### No data loaded
- Admin must upload a CSV file first
- Check `data/` directory exists and is writable
- Verify CSV format is correct

### Upload fails
- Check file size limits
- Verify CSV format (headers in first row after processing)
- Check disk space: `df -h`

### Questions not working
- Ensure data is loaded (check status in UI)
- Verify Gemini API key is valid
- Check API quota/limits

## CSV Format

Your CSV should have headers. The code processes it as:
```python
df = pd.read_csv(file)
df.columns = df.iloc[0]  # Second row becomes headers
df = df.iloc[1:]          # Drop first row
```

Example:
```csv
Name,Age,City
John,30,New York
Jane,25,Los Angeles
Bob,35,Chicago
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - feel free to use for personal or commercial projects.

## Support

- **Issues**: GitHub Issues
- **Documentation**: See SIMPLE_SETUP.md and EC2_DEPLOYMENT.md
- **API Docs**: http://localhost:8000/docs (when running)

## Acknowledgments

- Google Gemini AI for powerful language models
- LangChain for agent framework
- FastAPI for excellent web framework
- Pandas for data processing

---

**Made with ❤️ for simple, effective data querying**
