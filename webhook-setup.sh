#!/bin/bash

# Setup GitHub webhook for automatic deployment
echo "🔄 Setting up automatic deployment webhook..."

# Create webhook script
sudo tee /var/www/blog/webhook.py > /dev/null <<'EOF'
from flask import Flask, request, jsonify
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)

# GitHub webhook secret (set this in GitHub webhook settings)
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key')

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify GitHub signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature:
        expected_signature = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 401
    
    # Get payload
    payload = request.json
    
    # Check if it's a push to main branch
    if payload.get('ref') == 'refs/heads/main':
        try:
            # Run deployment script
            result = subprocess.run(['/var/www/blog/auto-deploy.sh'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return jsonify({'status': 'success', 'message': 'Deployment completed'})
            else:
                return jsonify({'status': 'error', 'message': result.stderr}), 500
                
        except subprocess.TimeoutExpired:
            return jsonify({'status': 'error', 'message': 'Deployment timeout'}), 500
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return jsonify({'status': 'ignored', 'message': 'Not a main branch push'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
EOF

# Create auto-deploy script
sudo tee /var/www/blog/auto-deploy.sh > /dev/null <<'EOF'
#!/bin/bash

cd /var/www/blog

# Log deployment
echo "$(date): Starting auto-deployment" >> /var/log/auto-deploy.log

# Pull latest changes
git pull origin main >> /var/log/auto-deploy.log 2>&1

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt >> /var/log/auto-deploy.log 2>&1

# Restart application
sudo systemctl restart blog >> /var/log/auto-deploy.log 2>&1

# Reload nginx
sudo systemctl reload nginx >> /var/log/auto-deploy.log 2>&1

echo "$(date): Auto-deployment completed" >> /var/log/auto-deploy.log
EOF

# Make scripts executable
sudo chmod +x /var/www/blog/auto-deploy.sh
sudo chmod +x /var/www/blog/webhook.py

# Install Flask for webhook
cd /var/www/blog
source venv/bin/activate
pip install flask

# Create webhook service
sudo tee /etc/systemd/system/webhook.service > /dev/null <<EOF
[Unit]
Description=GitHub Webhook Service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/blog
Environment="PATH=/var/www/blog/venv/bin"
Environment="WEBHOOK_SECRET=your-secret-key"
ExecStart=/var/www/blog/venv/bin/python webhook.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Update nginx to proxy webhook
sudo tee -a /etc/nginx/sites-available/blog > /dev/null <<'EOF'

    location /webhook {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
EOF

# Create log file
sudo touch /var/log/auto-deploy.log
sudo chown $USER:$USER /var/log/auto-deploy.log

# Start webhook service
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook
sudo systemctl reload nginx

echo "✅ Webhook setup completed!"
echo "🔗 Webhook URL: http://your-ec2-ip/webhook"
echo "🔑 Set webhook secret in GitHub: your-secret-key"
echo "📝 View logs: tail -f /var/log/auto-deploy.log"