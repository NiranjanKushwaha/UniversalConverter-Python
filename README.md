# Universal File Converter API

A comprehensive REST API for converting files between various formats including documents, images, audio, video, and more.

## 🚀 Features

- **Document Conversion**: PDF ↔ DOCX, DOC, TXT, HTML, RTF, ODT, XML, EPUB, MOBI
- **Spreadsheet Conversion**: XLSX ↔ XLS, CSV, PDF, HTML, XML, JSON
- **Image Conversion**: JPG ↔ PNG, BMP, GIF, TIFF, WEBP, SVG, ICO, PDF
- **Presentation Conversion**: PPTX ↔ PPT, PDF, JPG, PNG, HTML, ODP
- **Audio Conversion**: MP3 ↔ WAV, AAC, FLAC, OGG, M4A
- **Video Conversion**: MP4 ↔ AVI, MOV, WMV, MKV, WEBM + audio extraction
- **Data Format Conversion**: JSON ↔ XML, CSV, HTML, XLSX
- **Text Processing**: TXT to various formats including PDF, DOCX, HTML

## 📋 Requirements

- Python 3.8+
- FastAPI
- Various conversion libraries (see requirements.txt)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Universal-converter-python
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install system dependencies** (if needed):
   
   **For PDF processing**:
   ```bash
   # macOS
   brew install poppler
   
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   
   # Windows
   # Download poppler binaries and add to PATH
   ```
   
   **For video/audio processing**:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # Windows
   # Download FFmpeg and add to PATH
   ```

## 🚀 Quick Start

1. **Start the server**:
   ```bash
   python start_server.py
   ```
   
   Or manually:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive Documentation: `http://localhost:8000/docs`
   - Alternative Documentation: `http://localhost:8000/redoc`

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

### Production Deployment

For production deployment, consider:

1. **Use a production ASGI server**:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Set up a reverse proxy** (nginx, Apache)

3. **Use a persistent job store** (Redis, database)

4. **Implement file cleanup** (scheduled tasks)

5. **Add authentication and rate limiting**

## 🐛 Troubleshooting

### Common Issues

1. **Missing system dependencies**:
   - Install poppler for PDF processing
   - Install FFmpeg for audio/video processing
   - Install wkhtmltopdf for HTML to PDF conversion

2. **Memory issues with large files**:
   - Increase system memory
   - Process files in chunks
   - Implement file size limits

3. **Conversion failures**:
   - Check file format and integrity
   - Verify source format matches actual file type
   - Check server logs for detailed error messages

### Logs

Server logs are available in the console output. For production, configure proper logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Various Python libraries for file conversion capabilities
- Contributors and users of this project

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
4. Contact the development team

---

**Happy Converting! 🎉**
