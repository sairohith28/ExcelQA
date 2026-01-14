from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import os
# import boto3  # S3 support - commented out for EC2 local storage
from dotenv import load_dotenv
import io
from typing import Optional
import shutil
from pathlib import Path
import requests

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Excel QA API", description="Ask questions about your CSV data")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving HTML/CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount uploads directory to serve uploaded CSV files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Request models
class Question(BaseModel):
    question: str

class LoginRequest(BaseModel):
    username: str
    password: str

class FileURLRequest(BaseModel):
    file_url: str  # HTTP/HTTPS URL to CSV file (e.g., http://ec2-ip/uploads/file.csv)

# Response models
class Answer(BaseModel):
    question: str
    answer: str

class LoginResponse(BaseModel):
    success: bool
    role: Optional[str] = None
    message: str

# Simple in-memory user store (replace with database in production)
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

# Global variables for agent
agent = None
df = None
# s3_client = None  # S3 support - commented out
current_file_url = None

# Local file storage settings (for EC2 deployment)
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)  # Create uploads directory if it doesn't exist

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent, df  # , s3_client
    
    try:
        # S3 initialization - commented out for EC2 local storage
        # s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        #     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        #     region_name=os.getenv('AWS_REGION', 'us-east-1')
        # )
        # print("✅ S3 client initialized")
        
        print("✅ Using local file storage in uploads/ directory")
        
        # Try to load default CSV if exists
        if os.path.exists('sample.csv'):
            df = pd.read_csv('sample.csv')
            # Take the second row as header
            df.columns = df.iloc[0]
            # Drop the first row (now redundant)
            df = df.iloc[1:].reset_index(drop=True)
            
            print(f"✅ Loaded data: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"📋 Columns: {list(df.columns)}\n")
            
            # Initialize agent with default data
            await initialize_agent()
        else:
            print("ℹ️ No default CSV found. Waiting for data upload...")
        
    except Exception as e:
        print(f"❌ Error during startup: {str(e)}")

async def initialize_agent():
    """Initialize or reinitialize the agent with current dataframe"""
    global agent, df
    
    if df is None:
        raise ValueError("No dataframe loaded")
    
    # Create Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        convert_system_message_to_human=True
    )
    
    # Create pandas dataframe agent
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True,
    )
    
    print("✅ Agent initialized successfully!")

@app.get("/")
async def root():
    """Serve the login page"""
    return FileResponse("static/login.html")

@app.get("/chat")
async def chat_page():
    """Serve the chat interface"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Excel QA API is running",
        "data_shape": f"{df.shape[0]} rows × {df.shape[1]} columns" if df is not None else "No data loaded",
        "file_url": current_file_url
    }

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Simple login endpoint"""
    user = USERS.get(credentials.username)
    
    if not user:
        return LoginResponse(success=False, message="User not found")
    
    if user["password"] != credentials.password:
        return LoginResponse(success=False, message="Invalid password")
    
    return LoginResponse(
        success=True,
        role=user["role"],
        message="Login successful"
    )

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file to local storage (Admin only)
    File will be accessible via: http://your-ec2-ip:8000/uploads/filename.csv
    """
    global df, agent, current_file_url
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Save file locally to uploads directory
        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Generate file URL (use your EC2 public IP or domain)
        # Format: http://your-ec2-ip:8000/uploads/filename.csv
        server_url = os.getenv('SERVER_URL', 'http://localhost:8000')
        file_url = f"{server_url}/uploads/{file.filename}"
        current_file_url = file_url
        
        # S3 Upload - COMMENTED OUT
        # bucket_name = os.getenv('S3_BUCKET_NAME', 'your-bucket-name')
        # s3_key = f"uploads/{file.filename}"
        # s3_client.put_object(
        #     Bucket=bucket_name,
        #     Key=s3_key,
        #     Body=contents,
        #     ContentType='text/csv'
        # )
        # s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        
        # Load the CSV into dataframe
        df = pd.read_csv(io.BytesIO(contents))
        # Take the second row as header
        df.columns = df.iloc[0]
        # Drop the first row (now redundant)
        df = df.iloc[1:].reset_index(drop=True)
        
        print(f"✅ Uploaded and loaded data: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"📁 File saved to: {file_path}")
        print(f"🔗 Accessible at: {file_url}")
        
        # Reinitialize agent with new data
        await initialize_agent()
        
        return {
            "success": True,
            "message": "CSV uploaded successfully",
            "file_url": file_url,
            "local_path": str(file_path),
            "rows": df.shape[0],
            "columns": df.shape[1]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/load-from-url")
async def load_from_url(request: FileURLRequest):
    """
    Load CSV from HTTP/HTTPS URL (including EC2 instance URLs)
    Example: http://your-ec2-ip:8000/uploads/file.csv
    """
    global df, agent, current_file_url
    
    try:
        file_url = request.file_url
        
        # Download file from URL
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        contents = response.content
        
        # S3 LOADING - COMMENTED OUT
        # if s3_url.startswith('s3://'):
        #     parts = s3_url.replace('s3://', '').split('/', 1)
        #     bucket_name = parts[0]
        #     s3_key = parts[1] if len(parts) > 1 else ''
        # else:
        #     parts = s3_url.replace('https://', '').split('.s3.amazonaws.com/', 1)
        #     bucket_name = parts[0]
        #     s3_key = parts[1] if len(parts) > 1 else ''
        # response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        # contents = response['Body'].read()
        
        # Load the CSV into dataframe
        df = pd.read_csv(io.BytesIO(contents))
        # Take the second row as header
        df.columns = df.iloc[0]
        # Drop the first row (now redundant)
        df = df.iloc[1:].reset_index(drop=True)
        
        current_file_url = file_url
        
        print(f"✅ Loaded data from URL: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"🔗 Source: {file_url}")
        
        # Reinitialize agent with new data
        await initialize_agent()
        
        return {
            "success": True,
            "message": "Data loaded from URL successfully",
            "rows": df.shape[0],
            "columns": df.shape[1]
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/ask", response_model=Answer)
async def ask_question(question: Question):
    """
    Ask a question about the CSV data
    
    Args:
        question: Question object containing the user's question
        
    Returns:
        Answer object with the question and answer
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        # Invoke the agent with the question
        response = agent.invoke(question.question)
        
        return Answer(
            question=question.question,
            answer=response.get('output', 'No answer generated')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/data/info")
async def get_data_info():
    """Get information about the loaded dataset"""
    if df is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": list(df.columns)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)