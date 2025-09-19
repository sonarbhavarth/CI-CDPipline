#!/bin/bash

# EC2 Deployment Script for FastAPI Blog
echo "🚀 Starting deployment to EC2..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv nginx -y

# Create application directory
sudo mkdir -p /var/www/blog
sudo chown $USER:$USER /var/www/blog

# Copy application files
cp -r . /var/www/blog/
cd /var/www/blog

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/blog.service > /dev/null <<EOF
[Unit]
Description=FastAPI Blog Application
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/blog
Environment="PATH=/var/www/blog/venv/bin"
ExecStart=/var/www/blog/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/blog > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /uploads/ {
        alias /var/www/blog/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create uploads directory
mkdir -p /var/www/blog/uploads
chmod 755 /var/www/blog/uploads

# Start services
sudo systemctl daemon-reload
sudo systemctl enable blog
sudo systemctl start blog
sudo systemctl restart nginx

echo "✅ Deployment completed!"
echo "🌐 Your blog is now running on http://your-ec2-ip"
echo "📊 Check status: sudo systemctl status blog"