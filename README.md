# Orders MyCPA FastAPI Application

## Production Deployment Guide

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3-venv python3-pip nginx certbot python3-certbot-nginx -y
```

### 2. Project Setup
```bash
# Create project directory
sudo mkdir -p /var/www/orders.mycpa.uz
sudo chown -R www-data:www-data /var/www/orders.mycpa.uz

# Clone the repository
sudo -u www-data git clone https://github.com/your-repo/orders.mycpa.uz.git /var/www/orders.mycpa.uz

# Create and activate virtual environment
cd /var/www/orders.mycpa.uz
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. SSL Certificate
```bash
# Obtain SSL certificate
sudo certbot --nginx -d orders.mycpa.uz
```

### 4. Configure Nginx
```bash
# Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/orders.mycpa.uz
sudo ln -s /etc/nginx/sites-available/orders.mycpa.uz /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Setup SystemD Service
```bash
# Copy and start service
sudo cp orders-mycpa.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start orders-mycpa
sudo systemctl enable orders-mycpa
```

### 6. Logs
- Application logs: `/var/log/gunicorn/`
- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`

### 7. Maintenance
```bash
# Restart application
sudo systemctl restart orders-mycpa

# Check status
sudo systemctl status orders-mycpa

# View logs
sudo journalctl -u orders-mycpa