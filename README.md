# FastAPI Blog

A modern blog application built with FastAPI, featuring user authentication, image uploads, and admin controls.

## Features

- 📝 Create and view blog posts
- 🖼️ Image upload support
- 🔐 User authentication system
- 🛠️ Admin control panel
- 📱 Responsive design
- 🗄️ SQLite database

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Testing

```bash
# Run tests
pytest tests/ -v
```

## Default Accounts

- **Admin**: `admin` / `password`
- **User**: `user` / `123`

## API Endpoints

- `/` - Home page
- `/login` - User login
- `/create` - Create new post (authenticated)
- `/admin` - Admin control panel (admin only)
- `/post/{id}` - View individual post

## CI/CD

This project uses GitHub Actions for automated testing and deployment. The pipeline runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` branch