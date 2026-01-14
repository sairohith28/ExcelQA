# EC2 Deployment Guide

## Overview
This guide explains how to deploy the Excel QA application on AWS EC2 with local file storage instead of S3.

## Changes Made
- ✅ S3 code commented out
- ✅ Local file storage in `uploads/` directory
- ✅ Files accessible via HTTP: `http://your-ec2-ip:8000/uploads/filename.csv`
- ✅ Upload endpoint saves files locally
- ✅ Load endpoint accepts any HTTP/HTTPS URL

## EC2 Setup Steps

### 1. Launch EC2 Instance
```bash
# Choose Ubuntu Server 22.04 LTS or Amazon Linux 2023
# Instance type: t2.micro (free tier) or t2.small recommended
# Configure Security Group to allow:
#   - SSH (port 22)
#   - HTTP (port 80)
#   - Custom TCP (port 8000) - for FastAPI
```

### 2. Connect to EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Install git
sudo apt install git -y
```

### 4. Clone/Upload Your Project
```bash
# Option 1: Using git
git clone your-repo-url
cd excelqa

# Option 2: Using scp from local machine
scp -i your-key.pem -r /path/to/excelqa ubuntu@your-ec2-ip:~/
```

### 5. Set Up Python Environment
```bash
cd excelqa

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Configure Environment Variables
```bash
# Create .env file
nano .env

# Add your configuration:
GOOGLE_API_KEY=your_gemini_api_key_here
SERVER_URL=http://your-ec2-public-ip:8000

# Save and exit (Ctrl+X, Y, Enter)
```

### 7. Create Uploads Directory
```bash
mkdir -p uploads
chmod 755 uploads
```

### 8. Run the Application

**Option A: Run directly (for testing)**
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Option B: Run with systemd (for production)**
```bash
# Create service file
sudo nano /etc/systemd/system/excelqa.service
```

Add this content:
```ini
[Unit]
Description=Excel QA FastAPI Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/excelqa
Environment="PATH=/home/ubuntu/excelqa/env/bin"
ExecStart=/home/ubuntu/excelqa/env/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable excelqa
sudo systemctl start excelqa
sudo systemctl status excelqa
```

**Option C: Run with PM2 (alternative)**
```bash
# Install PM2
sudo npm install -g pm2

# Start application
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name excelqa
pm2 save
pm2 startup
```

### 9. Configure Security Group

In AWS Console:
1. Go to EC2 → Security Groups
2. Select your instance's security group
3. Add Inbound Rules:
   - Type: Custom TCP
   - Port: 8000
   - Source: 0.0.0.0/0 (or your specific IP)

### 10. Access Your Application

Open browser to:
```
http://your-ec2-public-ip:8000
```

Login with:
- Admin: `admin` / `admin123`
- User: `user` / `user123`

## How File Storage Works

### Upload Flow:
1. Admin uploads CSV file
2. File saved to `uploads/filename.csv` on EC2
3. Accessible at: `http://your-ec2-public-ip:8000/uploads/filename.csv`
4. Data loaded into pandas dataframe for querying

### Load from URL Flow:
1. User enters URL: `http://your-ec2-public-ip:8000/uploads/file.csv`
2. Application downloads file from URL
3. Data loaded into pandas dataframe
4. Users can ask questions

## Optional: Set Up Domain & HTTPS

### Using Nginx as Reverse Proxy

1. Install Nginx:
```bash
sudo apt install nginx -y
```

2. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/excelqa
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

3. Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/excelqa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. Add SSL with Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

Then update `.env`:
```
SERVER_URL=https://your-domain.com
```

## Monitoring & Logs

### Check application logs:
```bash
# If using systemd:
sudo journalctl -u excelqa -f

# If using PM2:
pm2 logs excelqa

# Direct run:
# Logs will appear in terminal
```

### Check disk usage:
```bash
df -h
du -sh uploads/
```

### Monitor uploads directory:
```bash
ls -lh uploads/
```

## Backup Strategy

```bash
# Backup uploads directory
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/

# Copy to S3 (if you want offsite backup)
# aws s3 cp uploads-backup-*.tar.gz s3://your-backup-bucket/
```

## Troubleshooting

### Can't access from browser:
- Check security group allows port 8000
- Check EC2 public IP is correct
- Verify application is running: `sudo systemctl status excelqa`

### File upload fails:
- Check uploads directory exists and is writable
- Check disk space: `df -h`

### Application crashes:
- Check logs: `sudo journalctl -u excelqa -n 50`
- Verify .env file exists with correct API key
- Check Python dependencies: `pip list`

## Cost Estimate

**EC2 t2.micro (free tier eligible):**
- 750 hours/month free
- After: ~$8-10/month

**Storage:**
- 30GB free tier
- Additional: $0.10/GB/month

**Data Transfer:**
- First 100GB free
- Additional: $0.09/GB

## Security Recommendations

1. **Change default passwords** in main.py
2. **Use environment variables** for sensitive data
3. **Enable firewall**:
   ```bash
   sudo ufw allow 22
   sudo ufw allow 8000
   sudo ufw enable
   ```
4. **Regular updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
5. **Implement rate limiting** in production
6. **Use HTTPS** with SSL certificate
7. **Backup regularly**

## Re-enabling S3 (Optional)

If you want to use S3 again later:

1. Uncomment S3 code in `main.py`
2. Uncomment `boto3` in `requirements.txt`
3. Install boto3: `pip install boto3`
4. Add AWS credentials to `.env`
5. Update frontend to use original endpoints

---

**Need Help?** Check the main SETUP_GUIDE.md for more details.
