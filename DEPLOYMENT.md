# 🚀 Quick Deployment Guide

## **Option 1: Docker (Easiest)**

```bash
# 1. Clone your repository
git clone <your-repo-url>
cd Universal-converter-python

# 2. Deploy with one command
./deploy.sh

# 3. Your API is now running at:
# http://your-server-ip:8000
# http://your-server-ip:8000/docs (Swagger UI)
```

## **Option 2: Traditional Server**

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx
sudo apt install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev poppler-utils ffmpeg

# 2. Setup application
git clone <your-repo-url>
cd Universal-converter-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 3. Start the server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## **Option 3: Cloud Platforms**

### **Heroku**
```bash
heroku create your-universal-converter
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-apt
echo "libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev poppler-utils ffmpeg" > Aptfile
git push heroku main
```

### **AWS EC2**
```bash
# Follow Option 2 steps on your EC2 instance
# Then add Nginx reverse proxy for domain access
```

### **Google Cloud Run**
```bash
gcloud run deploy universal-converter --source . --platform managed --region us-central1 --allow-unauthenticated
```

## **Environment Variables**

Create a `.env` file:
```env
UPLOAD_DIR=/app/uploads
CONVERTED_DIR=/app/converted
MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
```

## **Production Checklist**

- [ ] **Security**: HTTPS/SSL configured
- [ ] **Monitoring**: Health checks working
- [ ] **Backup**: File backup strategy
- [ ] **Performance**: Load balancing (if needed)
- [ ] **Logging**: Application logs configured

## **Quick Commands**

```bash
# Docker
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose logs -f        # View logs

# Traditional
gunicorn main:app -w 4 --bind 0.0.0.0:8000  # Start
sudo systemctl restart universal-converter     # Restart

# Health check
curl http://localhost:8000/health

# Storage stats
curl http://localhost:8000/storage/stats
```

## **Troubleshooting**

1. **Port in use**: `sudo lsof -i :8000` then `sudo kill -9 <PID>`
2. **Permission denied**: `chmod 755 uploads converted`
3. **Memory issues**: Add swap space
4. **Docker issues**: `docker system prune -a`

## **Next Steps**

1. **Domain Setup**: Point your domain to your server
2. **SSL Certificate**: Use Let's Encrypt
3. **Monitoring**: Set up application monitoring
4. **Backup**: Configure automated backups
5. **Scaling**: Add load balancer if needed

---

**Need help?** Check the full README.md for detailed instructions! 