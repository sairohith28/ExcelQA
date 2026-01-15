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

# Single data file that gets replaced on each upload
DATA_FILE = Path("data/current_data.csv")
DATA_FILE.parent.mkdir(exist_ok=True)  # Create data directory if it doesn't exist

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
        
        print("✅ Using local file storage (single data file)")
        
        # Try to load the data file if exists
        if DATA_FILE.exists():
            df = pd.read_csv(DATA_FILE)
            # Take the second row as header
            df.columns = df.iloc[0]
            # Drop the first row (now redundant)
            df = df.iloc[1:].reset_index(drop=True)
            
            print(f"✅ Loaded data: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"📋 Columns: {list(df.columns)}\n")
            
            # Initialize agent with default data
            await initialize_agent()
        else:
            print("ℹ️ No data file found. Waiting for admin to upload CSV...")
        
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
        "data_loaded": df is not None
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
    Upload CSV file - replaces the current data file (Admin only)
    All users will access this same data file
    """
    global df, agent
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Save/replace the data file
        with open(DATA_FILE, "wb") as f:
            f.write(contents)
        
        # Load the CSV into dataframe
        df = pd.read_csv(io.BytesIO(contents))
        # Take the second row as header
        df.columns = df.iloc[0]
        # Drop the first row (now redundant)
        df = df.iloc[1:].reset_index(drop=True)
        
        print(f"✅ Data file replaced: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"📁 Saved to: {DATA_FILE}")
        print(f"📊 Original filename: {file.filename}")
        
        # Reinitialize agent with new data
        await initialize_agent()
        
        return {
            "success": True,
            "message": "CSV uploaded successfully. Data replaced for all users.",
            "original_filename": file.filename,
            "rows": df.shape[0],
            "columns": df.shape[1]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# Load from URL endpoint - COMMENTED OUT (not needed for single file storage)
# @app.post("/load-from-url")
# async def load_from_url(request: FileURLRequest):
#     """Load CSV from HTTP/HTTPS URL"""
#     # This endpoint is no longer needed since we use a single data file
#     pass

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