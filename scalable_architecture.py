"""
Scalable Architecture for Universal File Converter
Supports 10K+ simultaneous users
"""

import os
import asyncio
import redis
import psycopg2
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from celery import Celery
from fastapi import FastAPI, BackgroundTasks
import boto3
from typing import Dict, Optional
import logging

# ============================================================================
# 1. DATABASE SETUP (PostgreSQL for persistent storage)
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/universal_converter")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    status = Column(String, default="pending")  # pending, converting, completed, error
    progress = Column(Integer, default=0)
    source_format = Column(String)
    destination_format = Column(String)
    input_file_path = Column(String)
    output_file_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user_id = Column(String, nullable=True)  # For multi-tenant support

class FileHash(Base):
    __tablename__ = "file_hashes"
    
    hash = Column(String, primary_key=True)
    file_path = Column(String)
    file_size = Column(Integer)
    created_at = Column(DateTime)
    usage_count = Column(Integer, default=1)

# ============================================================================
# 2. REDIS SETUP (For caching and job queue)
# ============================================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.Redis.from_url(REDIS_URL)

# ============================================================================
# 3. CELERY SETUP (Background job processing)
# ============================================================================

celery_app = Celery(
    "universal_converter",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery_app.task(bind=True)
def convert_file_task(self, job_id: str, input_path: str, output_path: str, 
                     source_format: str, destination_format: str):
    """Background task for file conversion"""
    try:
        # Update job status to converting
        update_job_status(job_id, "converting", 10)
        
        # Perform conversion (your existing conversion logic)
        success = perform_conversion(input_path, output_path, source_format, destination_format)
        
        if success:
            update_job_status(job_id, "completed", 100, output_path=output_path)
        else:
            update_job_status(job_id, "error", 0, error_message="Conversion failed")
            
    except Exception as e:
        update_job_status(job_id, "error", 0, error_message=str(e))

# ============================================================================
# 4. CLOUD STORAGE (S3 for distributed file storage)
# ============================================================================

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

S3_BUCKET = os.getenv("S3_BUCKET", "universal-converter-files")

def upload_to_s3(file_path: str, s3_key: str) -> str:
    """Upload file to S3"""
    s3_client.upload_file(file_path, S3_BUCKET, s3_key)
    return f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"

def download_from_s3(s3_key: str, local_path: str):
    """Download file from S3"""
    s3_client.download_file(S3_BUCKET, s3_key, local_path)

# ============================================================================
# 5. SCALABLE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="Scalable Universal File Converter")

@app.post("/convert")
async def convert_file(
    file: UploadFile,
    source_format: str,
    destination_format: str,
    background_tasks: BackgroundTasks
):
    """Scalable file conversion endpoint"""
    
    # 1. Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # 2. Save file to S3
    s3_key = f"uploads/{job_id}/{file.filename}"
    temp_path = f"/tmp/{job_id}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Upload to S3
    s3_url = upload_to_s3(temp_path, s3_key)
    
    # 3. Create job record in database
    job = Job(
        id=job_id,
        status="pending",
        source_format=source_format,
        destination_format=destination_format,
        input_file_path=s3_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db = SessionLocal()
    db.add(job)
    db.commit()
    db.close()
    
    # 4. Queue background task
    convert_file_task.delay(job_id, s3_url, f"converted/{job_id}", 
                           source_format, destination_format)
    
    return {"jobId": job_id}

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status from database"""
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    db.close()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "status": job.status,
        "progress": job.progress,
        "error": job.error_message
    }
    
    if job.status == "completed":
        response["downloadUrl"] = f"/download/{job_id}"
    
    return response

@app.get("/download/{job_id}")
async def download_file(job_id: str):
    """Download converted file from S3"""
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    db.close()
    
    if not job or job.status != "completed":
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate presigned URL for S3 download
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': job.output_file_path},
        ExpiresIn=3600
    )
    
    return {"downloadUrl": presigned_url}

# ============================================================================
# 6. LOAD BALANCER CONFIGURATION (Nginx)
# ============================================================================

"""
# nginx.conf
upstream universal_converter {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
    server 127.0.0.1:8005;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://universal_converter;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # File upload settings
        client_max_body_size 100M;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
"""

# ============================================================================
# 7. KUBERNETES DEPLOYMENT
# ============================================================================

"""
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: universal-converter
spec:
  replicas: 10  # Scale to 10 instances
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
        image: your-registry/universal-converter:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

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

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: universal-converter-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: universal-converter
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""

# ============================================================================
# 8. MONITORING AND METRICS
# ============================================================================

from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_JOBS = Gauge('active_jobs', 'Number of active conversion jobs')
QUEUE_SIZE = Gauge('queue_size', 'Number of jobs in queue')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

# ============================================================================
# 9. RATE LIMITING
# ============================================================================

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/convert")
@limiter.limit("10/minute")  # 10 conversions per minute per IP
async def convert_file_with_rate_limit(request: Request, file: UploadFile, source_format: str, destination_format: str):
    # Your conversion logic here
    pass

# ============================================================================
# 10. CACHING STRATEGY
# ============================================================================

def get_cached_formats():
    """Cache supported formats in Redis"""
    cached = redis_client.get("supported_formats")
    if cached:
        return json.loads(cached)
    
    # Generate formats list
    formats = generate_supported_formats()
    
    # Cache for 1 hour
    redis_client.setex("supported_formats", 3600, json.dumps(formats))
    return formats

@app.get("/formats")
async def get_formats():
    """Get cached supported formats"""
    return get_cached_formats()

# ============================================================================
# 11. DATABASE CONNECTION POOLING
# ============================================================================

from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=30,  # Additional connections that can be created
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600  # Recycle connections after 1 hour
)

# ============================================================================
# 12. BACKGROUND WORKERS (Celery)
# ============================================================================

# Start Celery workers
# celery -A scalable_architecture worker --loglevel=info --concurrency=4

# Start Celery beat for scheduled tasks
# celery -A scalable_architecture beat --loglevel=info

@celery_app.task
def cleanup_old_files():
    """Scheduled task to cleanup old files"""
    # Cleanup logic here
    pass

# ============================================================================
# 13. HEALTH CHECKS
# ============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        # Check Redis
        redis_client.ping()
        
        # Check S3
        s3_client.head_bucket(Bucket=S3_BUCKET)
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected", 
            "s3": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# 14. PERFORMANCE OPTIMIZATIONS
# ============================================================================

# 1. Use connection pooling
# 2. Implement caching
# 3. Use async/await for I/O operations
# 4. Implement proper error handling
# 5. Use background tasks for heavy operations
# 6. Implement proper logging
# 7. Use CDN for static files
# 8. Implement proper security headers

# ============================================================================
# 15. SECURITY CONSIDERATIONS
# ============================================================================

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
app.add_middleware(HTTPSRedirectMiddleware)

# Rate limiting
# Input validation
# File type validation
# Virus scanning
# Authentication/Authorization
# API key management 