# Automate Accounts PDF processing

## Prerequisites
Ensure the following are installed:
- **Docker & Docker Compose**
- **Python 3.13+** (If running locally)


## Run the Project

### Using Docker Compose (Recommended)
For Prod/Test
```bash
docker-compose up --build
```
For Dev/Debug
```bash
DOCKERFILE=Dockerfile.dev ENV=dev docker-compose up --build
```


### Using Docker File Directly
```bash
docker build -t fastapi-ocr -f Dockerfile.prod .
docker run -p 8000:8000 fastapi-ocr
```
If running in windows without docker you will need to setup/install *tesseract*,  *poppler* and *en_core_web_sm* for spacy. 

