from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from openai import OpenAI

# ✅ Load .env variables
load_dotenv()

# ✅ Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# ✅ Initialize FastAPI app
app = FastAPI(
    title="GitHub Issue Analyzer",
    description="Analyze GitHub issues using GPT",
    version="1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify your frontend URL instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Request model
class IssueRequest(BaseModel):
    owner: str
    repo: str
    issue_number: int

# ✅ Fetch issue from GitHub
def fetch_issue(owner, repo, issue_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
    return response.json()

# ✅ Analyze issue using GPT
def analyze_with_gpt(issue_data):
    try:
        content = f"Issue Title: {issue_data.get('title')}\n\nDescription:\n{issue_data.get('body', '')}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a valid model name for OpenRouter
            messages=[
                {"role": "system", "content": "You are an assistant that analyzes GitHub issues and provides summaries and suggestions."},
                {"role": "user", "content": content}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI Error: {str(e)}")

# ✅ POST endpoint to analyze issue
@app.post("/analyze_issue/")
def analyze_issue(issue: IssueRequest):
    try:
        issue_data = fetch_issue(issue.owner, issue.repo, issue.issue_number)
        analysis = analyze_with_gpt(issue_data)
        return {"analysis": analysis}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
