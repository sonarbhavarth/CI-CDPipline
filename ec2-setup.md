# EC2 Deployment Guide

## 1. Launch EC2 Instance

### Instance Configuration:
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t2.micro (free tier)
- **Security Group**: Allow HTTP (80), HTTPS (443), SSH (22)

### Security Group Rules:
```
Type        Protocol    Port Range    Source
SSH         TCP         22           0.0.0.0/0
HTTP        TCP         80           0.0.0.0/0
HTTPS       TCP         443          0.0.0.0/0
```

## 2. Connect to EC2

```bash
# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## 3. Deploy Application

### Option A: Direct Upload
```bash
# Upload files to EC2
scp -i your-key.pem -r . ubuntu@your-ec2-ip:~/blog/

# Connect and run deployment
ssh -i your-key.pem ubuntu@your-ec2-ip
cd ~/blog
chmod +x deploy.sh
./deploy.sh
```

### Option B: Git Clone
```bash
# On EC2 instance
git clone https://github.com/sonarbhavarth/CI-CDPipline.git blog
cd blog
chmod +x deploy.sh
./deploy.sh
```

## 4. Verify Deployment

```bash
# Check application status
sudo systemctl status blog

# Check nginx status
sudo systemctl status nginx

# View logs
sudo journalctl -u blog -f
```

## 5. Access Your Blog

- **URL**: http://your-ec2-public-ip
- **Admin**: admin / admin123
- **User**: user / 123

## 6. Optional: Domain Setup

### Add Custom Domain:
1. Point your domain to EC2 public IP
2. Update nginx config:
```bash
sudo nano /etc/nginx/sites-available/blog
# Change server_name _ to server_name yourdomain.com;
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt):
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

## 7. Maintenance Commands

```bash
# Restart application
sudo systemctl restart blog

# Update application
cd /var/www/blog
git pull
sudo systemctl restart blog

# View logs
sudo tail -f /var/log/nginx/access.log
sudo journalctl -u blog -f
```