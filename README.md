# Universal File Converter API

A powerful, feature-rich REST API for converting files between various formats including documents, images, audio, video, and more. Built with FastAPI and Python, this API provides real-time file conversion with automatic deduplication and storage management.

## 🚀 Features

- **Document Conversion**: PDF ↔ DOCX, DOC, TXT, HTML, RTF, ODT, XML, EPUB, MOBI
- **Spreadsheet Conversion**: XLSX ↔ XLS, CSV, PDF, HTML, XML, JSON
- **Image Conversion**: JPG ↔ PNG, BMP, GIF, TIFF, WEBP, SVG, ICO, PDF
- **Presentation Conversion**: PPTX ↔ PPT, PDF, JPG, PNG, HTML, ODP
- **Audio Conversion**: MP3 ↔ WAV, AAC, FLAC, OGG, M4A
- **Video Conversion**: MP4 ↔ AVI, MOV, WMV, MKV, WEBM + audio extraction
- **Data Format Conversion**: JSON ↔ XML, CSV, HTML, XLSX
- **Text Processing**: TXT to various formats including PDF, DOCX, HTML
- **File Deduplication**: Automatic detection and reuse of identical files to save storage space
- **Storage Management**: Built-in cleanup and storage statistics
- **Real-time Progress Tracking**: Monitor conversion progress with job status updates
- **Swagger UI**: Interactive API documentation and testing interface

## 📋 Prerequisites

Before installing the Universal File Converter API, ensure you have:

- **Python 3.11+** (recommended) or Python 3.8+
- **Git** (for cloning the repository)
- **pip** (Python package installer)

### System Dependencies

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install cairo pango gdk-pixbuf libffi pkg-config poppler ffmpeg
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
sudo apt install -y poppler-utils ffmpeg wkhtmltopdf
```

#### Windows
```bash
# Install Python from https://python.org
# Install FFmpeg from https://ffmpeg.org/download.html
# Install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
```

## 🛠️ Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Universal-converter-python
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Check if all dependencies are installed
pip list

# Test the installation
python -c "import fastapi, uvicorn; print('✅ Installation successful!')"
```

## 🚀 Quick Start

### Method 1: Using the Start Script

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server
python start_server.py
```

### Method 2: Using Uvicorn Directly

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Production Mode

```bash
# For production deployment
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🌐 Access the API

Once the server is running, you can access:

- **API Base URL**: `http://localhost:8000`
- **Interactive Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc)**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 📚 API Endpoints

### Core Endpoints

#### `POST /convert`
Convert a file from one format to another.

**Request**:
- `file`: The file to convert (multipart/form-data)
- `sourceFormat`: Source file format (e.g., "PDF")
- `destinationFormat`: Target file format (e.g., "DOCX")

**Response**:
```json
{
  "jobId": "uuid-string"
}
```

#### `GET /status/{jobId}`
Check the status of a conversion job.

**Response**:
```json
{
  "status": "pending|converting|completed|error",
  "progress": 75,
  "downloadUrl": "/download/uuid-string",
  "error": null
}
```

#### `GET /download/{jobId}`
Download the converted file.

**Response**: File download

#### `GET /formats`
Get all supported conversion formats.

**Response**:
```json
[
  {
    "source": "PDF",
    "destination": ["DOCX", "DOC", "TXT", "HTML", ...]
  },
  ...
]
```

### Additional Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /jobs` - List all jobs (admin)
- `DELETE /jobs/{jobId}` - Delete a job and cleanup files
- `GET /cleanup` - Manually trigger cleanup of unused files
- `GET /storage/stats` - Get storage statistics (files, jobs, etc.)

## 🔧 Usage Examples

### Using cURL

```bash
# Convert PDF to DOCX
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "sourceFormat=PDF" \
  -F "destinationFormat=DOCX"

# Check status
curl "http://localhost:8000/status/your-job-id"

# Download converted file
curl -O "http://localhost:8000/download/your-job-id"
```

### Using Python requests

```python
import requests
import time

# Upload and convert
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/convert',
        files={'file': f},
        data={
            'sourceFormat': 'PDF',
            'destinationFormat': 'DOCX'
        }
    )

job_id = response.json()['jobId']

# Poll for completion
while True:
    status_response = requests.get(f'http://localhost:8000/status/{job_id}')
    status = status_response.json()
    
    if status['status'] == 'completed':
        # Download the file
        download_response = requests.get(f'http://localhost:8000/download/{job_id}')
        with open('converted_document.docx', 'wb') as f:
            f.write(download_response.content)
        break
    elif status['status'] == 'error':
        print(f"Conversion failed: {status['error']}")
        break
    
    time.sleep(1)
```

### Using JavaScript/Fetch

```javascript
// Convert file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('sourceFormat', 'PDF');
formData.append('destinationFormat', 'DOCX');

const response = await fetch('http://localhost:8000/convert', {
    method: 'POST',
    body: formData
});

const { jobId } = await response.json();

// Poll for completion
const pollStatus = async () => {
    const statusResponse = await fetch(`http://localhost:8000/status/${jobId}`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        // Download file
        window.open(`http://localhost:8000/download/${jobId}`);
    } else if (status.status === 'error') {
        console.error('Conversion failed:', status.error);
    } else {
        setTimeout(pollStatus, 1000);
    }
};

pollStatus();
```

## 🎯 Supported Conversions

### Document Formats
- **PDF**: ↔ DOCX, DOC, TXT, HTML, JPG, PNG, XLSX, CSV, XML
- **DOCX/DOC**: ↔ PDF, TXT, HTML, RTF, ODT, XML, EPUB, MOBI, JPG, PNG
- **RTF**: ↔ DOCX, DOC, PDF, HTML, TXT, ODT
- **ODT**: ↔ DOCX, DOC, PDF, HTML, TXT, RTF, EPUB, MOBI

### Spreadsheet Formats
- **XLSX/XLS**: ↔ CSV, PDF, HTML, XML, ODS, TXT, JSON
- **CSV**: ↔ XLSX, XLS, PDF, HTML, XML, JSON, TXT
- **ODS**: ↔ XLSX, XLS, CSV, PDF, HTML, XML, JSON

### Image Formats
- **JPG/JPEG**: ↔ PNG, BMP, GIF, TIFF, WEBP, SVG, ICO, PDF, DOCX, DOC, PPTX, TXT
- **PNG**: ↔ JPG, BMP, GIF, TIFF, WEBP, SVG, ICO, PDF, DOCX, DOC, XLSX, PPTX, TXT
- **BMP/GIF/TIFF/WEBP**: ↔ Various image formats + PDF, DOCX, DOC, TXT
- **SVG**: ↔ PNG, JPG, PDF, WEBP, BMP, GIF, TIFF

### Presentation Formats
- **PPTX/PPT**: ↔ PDF, JPG, PNG, HTML, ODP
- **ODP**: ↔ PPTX, PPT, PDF, JPG, PNG, HTML

### Audio Formats
- **MP3**: ↔ WAV, AAC, FLAC, OGG, M4A
- **WAV**: ↔ MP3, AAC, FLAC, OGG, M4A

### Video Formats
- **MP4**: ↔ AVI, MOV, WMV, FLV, MKV, WEBM, MP3, WAV, GIF
- **AVI/MOV**: ↔ MP4, other video formats, audio extraction

### Data Formats
- **JSON**: ↔ XML, CSV, TXT, HTML, XLSX, XLS
- **XML**: ↔ JSON, CSV, HTML, TXT, XLSX, XLS, DOCX, PDF
- **HTML**: ↔ PDF, DOCX, DOC, TXT, EPUB, MOBI, JPG, PNG

### E-book Formats
- **EPUB/MOBI/AZW3**: ↔ PDF, TXT, HTML, DOCX, DOC (mutual conversion)

## ⚙️ Configuration

### Environment Variables
- `UPLOAD_DIR`: Directory for uploaded files (default: "uploads")
- `CONVERTED_DIR`: Directory for converted files (default: "converted")
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 100MB)

### File Deduplication

The API automatically detects and reuses identical files to save storage space:

- **Hash-based Detection**: Files are identified by SHA-256 hash
- **Automatic Reuse**: When the same file is uploaded multiple times, only one copy is stored
- **Smart Cleanup**: Files are automatically removed when no longer referenced by any jobs
- **Storage Statistics**: Monitor file usage with `/storage/stats` endpoint

### Storage Management

- **Automatic Cleanup**: Unused files are cleaned up when jobs are deleted
- **Manual Cleanup**: Trigger cleanup with `GET /cleanup` endpoint
- **Storage Monitoring**: Check storage usage with `GET /storage/stats`
- **Job Tracking**: Each job tracks which file it uses, enabling proper cleanup

## 🧪 Testing

### Test File Deduplication

```bash
# Run the test script
python test_deduplication.py

# Or use the curl test
chmod +x test_deduplication_curl.sh
./test_deduplication_curl.sh
```

### Manual Testing

1. **Start the server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Open Swagger UI**: `http://localhost:8000/docs`

3. **Test a conversion**:
   - Upload a file using the `/convert` endpoint
   - Check status with `/status/{jobId}`
   - Download the converted file

## 🐛 Troubleshooting

### Common Issues

1. **Missing system dependencies**:
   ```bash
   # macOS
   brew install cairo pango gdk-pixbuf libffi pkg-config poppler ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev poppler-utils ffmpeg
   ```

2. **Python version issues**:
   - Ensure you're using Python 3.11+ for best compatibility
   - Use virtual environment to avoid conflicts

3. **Port already in use**:
   ```bash
   # Use a different port
   uvicorn main:app --reload --port 8001
   ```

4. **Memory issues with large files**:
   - Increase system memory
   - Process files in chunks
   - Implement file size limits

### Logs

Server logs are available in the console output. For production, configure proper logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🚀 Production Deployment

### Option 1: Docker Deployment (Recommended)

#### Quick Start with Docker
```bash
# Clone your repository
git clone <your-repo-url>
cd Universal-converter-python

# Deploy with one command
./deploy.sh

# Or manually:
docker-compose up -d
```

#### Docker Commands
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Update and redeploy
git pull
docker-compose down
docker-compose up -d --build
```

### Option 2: Traditional Server Deployment

#### Ubuntu/Debian Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx
sudo apt install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
sudo apt install -y poppler-utils ffmpeg wkhtmltopdf

# Clone repository
git clone <your-repo-url>
cd Universal-converter-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create directories
mkdir -p uploads converted logs

# Start with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Systemd Service (for auto-start)
```bash
# Create service file
sudo nano /etc/systemd/system/universal-converter.service
```

```ini
[Unit]
Description=Universal File Converter API
After=network.target

[Service]
Type=exec
User=ubuntu
WorkingDirectory=/path/to/Universal-converter-python
Environment=PATH=/path/to/Universal-converter-python/venv/bin
ExecStart=/path/to/Universal-converter-python/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable universal-converter
sudo systemctl start universal-converter
sudo systemctl status universal-converter
```

### Option 3: Cloud Platform Deployment

#### Heroku Deployment
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login to Heroku
heroku login

# Create Heroku app
heroku create your-universal-converter

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-apt

# Create Aptfile for system dependencies
echo "libcairo2
libpango-1.0-0
libgdk-pixbuf2.0-0
libffi-dev
poppler-utils
ffmpeg" > Aptfile

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Open app
heroku open
```

#### AWS EC2 Deployment
```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Follow traditional server deployment steps above
# Then set up Nginx reverse proxy:

sudo nano /etc/nginx/sites-available/universal-converter
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/universal-converter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Google Cloud Run
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login and set project
gcloud auth login
gcloud config set project your-project-id

# Deploy to Cloud Run
gcloud run deploy universal-converter \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### Option 4: Kubernetes Deployment

#### Docker Hub Push
```bash
# Build and tag image
docker build -t your-username/universal-converter:latest .

# Push to Docker Hub
docker push your-username/universal-converter:latest
```

#### Kubernetes YAML
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: universal-converter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: universal-converter
  template:
    metadata:
      labels:
        app: universal-converter
    spec:
      containers:
      - name: universal-converter
        image: your-username/universal-converter:latest
        ports:
        - containerPort: 8000
        env:
        - name: UPLOAD_DIR
          value: "/app/uploads"
        - name: CONVERTED_DIR
          value: "/app/converted"
        volumeMounts:
        - name: uploads-volume
          mountPath: /app/uploads
        - name: converted-volume
          mountPath: /app/converted
      volumes:
      - name: uploads-volume
        persistentVolumeClaim:
          claimName: uploads-pvc
      - name: converted-volume
        persistentVolumeClaim:
          claimName: converted-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: universal-converter-service
spec:
  selector:
    app: universal-converter
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Apply Kubernetes configuration
kubectl apply -f k8s-deployment.yaml
```

### Environment Configuration

#### Environment Variables
```bash
# Production environment variables
export UPLOAD_DIR=/app/uploads
export CONVERTED_DIR=/app/converted
export MAX_FILE_SIZE=104857600
export LOG_LEVEL=INFO
export CORS_ORIGINS=https://your-frontend-domain.com
```

#### .env File
```env
# .env.production
UPLOAD_DIR=/app/uploads
CONVERTED_DIR=/app/converted
MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend-domain.com
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

### Production Considerations

#### 1. **Database Integration**
```python
# Add to main.py for persistent job storage
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobs.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

#### 2. **Redis for Job Queue**
```python
# Add to main.py for distributed job processing
import redis

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
```

#### 3. **File Storage (S3/Cloud Storage)**
```python
# Add to main.py for cloud file storage
import boto3

s3_client = boto3.client('s3')
BUCKET_NAME = os.getenv("S3_BUCKET", "your-bucket-name")
```

#### 4. **Monitoring and Logging**
```python
# Add structured logging
import structlog

logger = structlog.get_logger()
```

#### 5. **Security Headers**
```python
# Add to main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

### SSL/HTTPS Setup

#### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Load Balancing

#### Nginx Configuration
```nginx
upstream universal_converter {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://universal_converter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # File upload settings
        client_max_body_size 100M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### Backup and Recovery

#### Automated Backups
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/universal-converter"

mkdir -p $BACKUP_DIR

# Backup uploads and converted files
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/
tar -czf $BACKUP_DIR/converted_$DATE.tar.gz converted/

# Backup database (if using one)
# pg_dump your_database > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

```bash
# Add to crontab for daily backups
0 2 * * * /path/to/backup.sh
```

### Performance Optimization

#### 1. **Worker Processes**
```bash
# Use multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 2. **Caching**
```python
# Add Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            result = redis_client.get(cache_key)
            if result:
                return json.loads(result)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 3. **File Cleanup**
```python
# Add scheduled cleanup
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)
async def cleanup_old_files():
    # Clean up files older than 24 hours
    pass

scheduler.start()
```

### Deployment Checklist

- [ ] **Environment Setup**
  - [ ] System dependencies installed
  - [ ] Python virtual environment created
  - [ ] Dependencies installed from requirements.txt

- [ ] **Configuration**
  - [ ] Environment variables set
  - [ ] File paths configured
  - [ ] CORS settings updated for production

- [ ] **Security**
  - [ ] HTTPS/SSL configured
  - [ ] Firewall rules set
  - [ ] Rate limiting implemented

- [ ] **Monitoring**
  - [ ] Health checks configured
  - [ ] Logging set up
  - [ ] Error tracking implemented

- [ ] **Backup**
  - [ ] Backup strategy implemented
  - [ ] Recovery procedures documented

- [ ] **Performance**
  - [ ] Load balancing configured
  - [ ] Caching implemented
  - [ ] File cleanup scheduled

### Troubleshooting Deployment

#### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   sudo lsof -i :8000
   
   # Kill the process
   sudo kill -9 <PID>
   ```

2. **Permission denied**
   ```bash
   # Fix directory permissions
   sudo chown -R $USER:$USER uploads converted
   chmod 755 uploads converted
   ```

3. **Memory issues**
   ```bash
   # Increase swap space
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

4. **Docker issues**
   ```bash
   # Clean up Docker
   docker system prune -a
   docker volume prune
   ```

#### Log Analysis
```bash
# View application logs
docker-compose logs -f universal-converter

# View system logs
sudo journalctl -u universal-converter -f

# Check disk space
df -h

# Check memory usage
free -h
```

## 📊 Monitoring

### Storage Statistics

```bash
# Check storage usage
curl http://localhost:8000/storage/stats

# Manual cleanup
curl http://localhost:8000/cleanup
```

### Health Monitoring

```bash
# Health check
curl http://localhost:8000/health

# List all jobs
curl http://localhost:8000/jobs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Various Python libraries for file conversion capabilities
- Contributors and users of this project

## 📞 Support

For support, please:

1. Check the troubleshooting section above
2. Review the API documentation at `http://localhost:8000/docs`
3. Open an issue on GitHub
4. Contact the development team

## 🔄 Changelog

### Version 1.0.0
- Initial release with comprehensive file conversion support
- File deduplication system
- Storage management and cleanup
- Interactive API documentation
- Real-time progress tracking

---

**Happy Converting! 🎉**

*Built with ❤️ using FastAPI and Python*
