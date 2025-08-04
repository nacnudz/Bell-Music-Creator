# Bell Music Creator - Docker Setup

This document explains how to run the Bell Music Creator application using Docker and Docker Compose.

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   Open your browser and navigate to `http://localhost:8080`

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

## Docker Commands

### Build the image
```bash
docker-compose build
```

### Run in background (detached mode)
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop and remove containers
```bash
docker-compose down
```

### Remove volumes (this will delete saved bell files)
```bash
docker-compose down -v
```

## Configuration

### Port Configuration
- The application runs on port 8080 inside the container
- It's mapped to port 8080 on your host machine
- To change the host port, modify the `docker-compose.yml` file:
  ```yaml
  ports:
    - "9000:8080"  # This would map to localhost:9000
  ```

### Data Persistence
- Bell files are stored in a Docker volume named `bell_files_data`
- This ensures your uploaded bell files persist between container restarts
- To use a local directory instead, uncomment the volume mount in `docker-compose.yml`

### Environment Variables
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` disables Streamlit usage statistics

## Development

For development with live code reloading:

1. **Mount your source code:**
   ```yaml
   volumes:
     - .:/app
     - bell_files_data:/app/bell_files
   ```

2. **Run with development settings:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

## Troubleshooting

### Health Checks
The container includes health checks that verify the application is running properly. Check the health status:
```bash
docker-compose ps
```

### Container Logs
View application logs for debugging:
```bash
docker-compose logs bell-music-creator
```

### Audio Processing Issues
If you encounter audio processing problems:
- Ensure FFmpeg is properly installed (included in the Docker image)
- Check file format compatibility (MP3/WAV supported)
- Verify file size limits (100MB max)

## Production Deployment

For production deployment:

1. **Use environment-specific compose file:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **Set up reverse proxy (nginx/traefik) for HTTPS**

3. **Configure monitoring and logging**

4. **Set up automated backups for the bell_files_data volume**

## Security Considerations

- The application runs as root inside the container (consider using non-root user for production)
- File uploads are limited to 100MB
- Only MP3 and WAV files are accepted
- Consider implementing additional security measures for production use