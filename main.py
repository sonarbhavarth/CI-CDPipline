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

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")

# In-memory sessions only
sessions = {}  # session_id: username

def get_current_user(request: Request) -> Optional[str]:
    session_id = request.cookies.get("session_id")
    if session_id:
        # Clean up expired sessions periodically
        db.cleanup_expired_sessions()
        return db.get_session(session_id)
    return None

def require_auth(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

def require_admin(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
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
    
    # Track view
    db.add_view(post_id)
    
    user = get_current_user(request)
    return templates.TemplateResponse("post.html", {"request": request, "post": post, "user": user})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    posts = db.get_all_posts()
    users = db.get_all_users()
    return templates.TemplateResponse("admin.html", {"request": request, "posts": posts, "users": users, "user": user})

@app.post("/admin/delete-post/{post_id}")
async def delete_post(request: Request, post_id: int):
    require_admin(request)
    db.delete_post(post_id)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/create-user")
async def create_user(request: Request, username: str = Form(None), password: str = Form(None)):
    require_admin(request)
    if username and password:
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
async def login(request: Request, username: str = Form(None), password: str = Form(None), remember_me: str = Form(None)):
    if username and password and db.verify_user(username, password):
        import uuid
        session_id = str(uuid.uuid4())
        
        # Set expiration for persistent sessions
        expires_at = None
        if remember_me:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
        
        # Store session in database
        db.create_session(session_id, username, expires_at)
        
        response = RedirectResponse(url="/", status_code=303)
        
        # Set persistent cookie if remember me is checked
        if remember_me:
            response.set_cookie(
                "session_id", 
                session_id, 
                max_age=30*24*60*60,  # 30 days in seconds
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
        else:
            # Session cookie (expires when browser closes)
            response.set_cookie(
                "session_id", 
                session_id,
                httponly=True,
                secure=False,
                samesite="lax"
            )
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        db.delete_session(session_id)
    response = RedirectResponse(url="/", status_code=303)
    # Delete cookie with same settings as when it was set
    response.delete_cookie(
        "session_id",
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return response

@app.get("/create", response_class=HTMLResponse)
async def create_form(request: Request):
    require_auth(request)
    user = get_current_user(request)
    return templates.TemplateResponse("create.html", {"request": request, "user": user})

@app.post("/create")
async def create_post(request: Request, title: str = Form(None), content: str = Form(None), image: UploadFile = File(None)):
    require_auth(request)
    user = get_current_user(request)
    
    if not title or not content:
        return RedirectResponse(url="/create", status_code=303)
    
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

@app.post("/like/{post_id}")
async def toggle_like(request: Request, post_id: int):
    user = get_current_user(request)
    if user:
        db.toggle_like(post_id, user)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.post("/comment/{post_id}")
async def add_comment(request: Request, post_id: int, content: str = Form(None)):
    user = get_current_user(request)
    if user and content:
        db.add_comment(post_id, user, content)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.get("/analytics", response_class=HTMLResponse)
async def user_analytics(request: Request):
    require_auth(request)
    user = get_current_user(request)
    posts = db.get_user_posts_analytics(user)
    return templates.TemplateResponse("analytics.html", {"request": request, "posts": posts, "user": user})

@app.get("/analytics/{post_id}", response_class=HTMLResponse)
async def post_analytics(request: Request, post_id: int):
    require_auth(request)
    user = get_current_user(request)
    post = db.get_post(post_id)
    
    if not post or post['author'] != user:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = db.get_post_analytics(post_id)
    return templates.TemplateResponse("post_analytics.html", {"request": request, "post": post, "analytics": analytics, "user": user})