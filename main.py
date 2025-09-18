from fastapi import FastAPI, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional
import os
import uuid
from database import db

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# In-memory sessions only
sessions = {}  # session_id: username

def get_current_user(request: Request) -> Optional[str]:
    session_id = request.cookies.get("session_id")
    return sessions.get(session_id) if session_id else None

def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

def require_admin(request: Request):
    user = get_current_user(request)
    if user != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    posts = db.get_all_posts()
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "user": user})

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def view_post(request: Request, post_id: int):
    post = db.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    user = get_current_user(request)
    return templates.TemplateResponse("post.html", {"request": request, "post": post, "user": user})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    require_admin(request)
    posts = db.get_all_posts()
    users = db.get_all_users()
    return templates.TemplateResponse("admin.html", {"request": request, "posts": posts, "users": users, "user": "admin"})

@app.post("/admin/delete-post/{post_id}")
async def delete_post(request: Request, post_id: int):
    require_admin(request)
    db.delete_post(post_id)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/create-user")
async def create_user(request: Request, username: str = Form(...), password: str = Form(...)):
    require_admin(request)
    success = db.create_user(username, password)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/delete-user/{username}")
async def delete_user(request: Request, username: str):
    require_admin(request)
    db.delete_user(username)
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if db.verify_user(username, password):
        session_id = f"{username}_{datetime.now().timestamp()}"
        sessions[session_id] = username
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("session_id", session_id)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response

@app.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    require_auth(request)
    user = get_current_user(request)
    return templates.TemplateResponse("create.html", {"request": request, "user": user})

@app.post("/create")
async def create_post(request: Request, title: str = Form(...), content: str = Form(...), image: UploadFile = File(None)):
    require_auth(request)
    user = get_current_user(request)
    
    image_path = None
    if image and image.filename:
        # Save uploaded image
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        image_path = f"uploads/{unique_filename}"
        
        with open(image_path, "wb") as buffer:
            content_bytes = await image.read()
            buffer.write(content_bytes)
    
    db.create_post(title, content, user, image_path)
    return RedirectResponse(url="/", status_code=303)