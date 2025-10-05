# Overview

This is the Bell Music Creator - a Streamlit-based audio processing application that allows users to upload music files and combine them with bell sounds. The application supports trimming the start of audio files, cropping to custom durations, and adding fade in/out effects before appending bell files. It features a bell file library system where users can save and reuse bell files via a dropdown selector, along with the option to upload new bell files.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit for web interface with Bell Music Creator branding
- **Layout**: Wide layout configuration with two-column design for music and bell file inputs
- **User Interface**: Music file upload + bell file dropdown selector with library management
- **Bell File System**: Dropdown selector with existing bell files plus "Upload new bell file" option
- **User Experience**: Progress bars, status text, save-to-library functionality for new bell files, and dynamic processing caption showing active settings

## Backend Architecture
- **Core Processing**: Python-based audio processing using PyDub library
- **File Handling**: Temporary file management for secure audio processing
- **Validation Layer**: Multi-tier validation including file format, extension, and size checks
- **Audio Processing**: AudioSegment-based manipulation with normalization effects

## Data Storage
- **Temporary Storage**: Uses Python's tempfile module for secure temporary file handling
- **Bell File Library**: Persistent local storage in `bell_files/` directory for reusable bell files
- **Memory Management**: In-memory audio processing with BytesIO streams
- **File Constraints**: 100MB file size limit for practical performance

## Audio Processing Pipeline
- **Supported Formats**: MP3 and WAV file formats
- **Music Processing**: 
  - Trim start (optional, 0-600 seconds) - remove audio from beginning
  - Crop to custom duration (10-600 seconds) - reduce to specified length
  - Fade in effect (optional, 0-10 seconds) - gradual volume increase at start
  - Fade out effect (0.5-10 seconds) - gradual volume decrease at end
  - Combine with bell file - append bell audio seamlessly
- **Bell File Handling**: Load from library directory or temporary uploaded file
- **Processing Chain**: File validation → temporary storage → PyDub processing → MP3 export
- **Error Handling**: Comprehensive validation with user-friendly error messages

# External Dependencies

## Core Libraries
- **Streamlit**: Web application framework for the user interface
- **PyDub**: Audio processing and manipulation library
- **AudioSegment**: Audio file loading and effects processing

## System Dependencies
- **tempfile**: Python standard library for temporary file management
- **io**: Python standard library for in-memory file operations
- **os**: Operating system interface utilities
- **time**: Time-related functions for processing feedback

## Audio Processing
- **Normalization Effects**: PyDub's built-in audio normalization capabilities
- **Format Support**: Native MP3 and WAV file format handling through PyDub

# Deployment

## Docker Configuration
The application is fully containerized using Docker and Docker Compose for easy deployment:

- **Dockerfile**: Python 3.11-slim base with FFmpeg for audio processing
- **Docker Compose**: Service configuration with volume persistence for bell files
- **Health Checks**: Automated container health monitoring
- **Data Persistence**: Bell files stored in Docker volumes to persist between restarts
- **Port Mapping**: Application accessible on port 5000 (Replit) or 8765 (Docker)
- **Environment**: Streamlit configured for headless operation