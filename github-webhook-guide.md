# GitHub Webhook Auto-Deployment Setup

## 1. Server Setup (After Initial Deployment)

```bash
# On your EC2 server, run the webhook setup
cd /var/www/blog
./webhook-setup.sh
```

## 2. GitHub Repository Webhook Configuration

### Step 1: Go to Repository Settings
1. Open your GitHub repository: `https://github.com/sonarbhavarth/CI-CDPipline`
2. Click **Settings** tab
3. Click **Webhooks** in left sidebar
4. Click **Add webhook**

### Step 2: Configure Webhook
- **Payload URL**: `http://your-ec2-public-ip/webhook`
- **Content type**: `application/json`
- **Secret**: `your-secret-key` (change this to a secure random string)
- **Which events**: Select "Just the push event"
- **Active**: ✅ Checked

### Step 3: Update Server Secret
```bash
# On EC2, update the webhook secret
sudo systemctl edit webhook
# Add:
[Service]
Environment="WEBHOOK_SECRET=your-actual-secret-key"

sudo systemctl restart webhook
```

## 3. Test Auto-Deployment

### Make a test change:
```bash
# On your local machine
echo "# Test change" >> README.md
git add README.md
git commit -m "Test auto-deployment"
git push origin main
```

### Check deployment logs:
```bash
# On EC2 server
tail -f /var/log/auto-deploy.log
```

## 4. How It Works

```
GitHub Push → Webhook → EC2 Server → Auto Deploy
     ↓            ↓         ↓           ↓
   main branch   HTTP POST  Flask App   git pull
                            (port 9000)  restart services
```

## 5. Monitoring & Troubleshooting

### Check webhook service:
```bash
sudo systemctl status webhook
```

### View webhook logs:
```bash
sudo journalctl -u webhook -f
```

### View deployment logs:
```bash
tail -f /var/log/auto-deploy.log
```

### Manual deployment:
```bash
cd /var/www/blog
./auto-deploy.sh
```

## 6. Security Notes

- Change `your-secret-key` to a strong random string
- Keep the webhook secret secure
- Monitor deployment logs regularly
- Consider IP restrictions for webhook endpoint

## 7. Webhook Payload Example

GitHub sends this when you push:
```json
{
  "ref": "refs/heads/main",
  "repository": {
    "name": "CI-CDPipline",
    "full_name": "sonarbhavarth/CI-CDPipline"
  },
  "commits": [...]
}
```

## 8. Troubleshooting Common Issues

### Webhook not triggering:
- Check GitHub webhook delivery logs
- Verify webhook URL is accessible
- Check webhook service status

### Deployment fails:
- Check git permissions: `sudo chown -R $USER:$USER /var/www/blog`
- Verify systemd service permissions
- Check deployment logs for errors

### Service restart fails:
- Add user to sudoers for systemctl commands:
```bash
sudo visudo
# Add: username ALL=(ALL) NOPASSWD: /bin/systemctl restart blog, /bin/systemctl reload nginx
```