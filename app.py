import streamlit as st
import os
import tempfile
import io
from pydub import AudioSegment
from pydub.effects import normalize
import time

# Configure page
st.set_page_config(
    page_title="Audio Processor",
    page_icon="🎵",
    layout="wide"
)

def validate_audio_file(uploaded_file):
    """Validate if the uploaded file is a supported audio format"""
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file extension
    file_extension = uploaded_file.name.lower().split('.')[-1]
    supported_formats = ['mp3', 'wav']
    
    if file_extension not in supported_formats:
        return False, f"Unsupported file format. Please upload MP3 or WAV files only."
    
    # Check file size (limit to 100MB for practical purposes)
    if uploaded_file.size > 100 * 1024 * 1024:
        return False, "File size too large. Please upload files smaller than 100MB."
    
    return True, "Valid file"

def process_audio_files(file1_data, file2_data, file1_name, file2_name, progress_bar, status_text):
    """Process the two audio files according to requirements"""
    try:
        # Update progress
        progress_bar.progress(10)
        status_text.text("Loading first audio file...")
        
        # Load first audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file1_name.split('.')[-1]}") as tmp1:
            tmp1.write(file1_data)
            tmp1.flush()
            audio1 = AudioSegment.from_file(tmp1.name)
        
        progress_bar.progress(25)
        status_text.text("Loading second audio file...")
        
        # Load second audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file2_name.split('.')[-1]}") as tmp2:
            tmp2.write(file2_data)
            tmp2.flush()
            audio2 = AudioSegment.from_file(tmp2.name)
        
        progress_bar.progress(40)
        status_text.text("Cropping first file to 3 minutes...")
        
        # Crop first audio to exactly 3 minutes (180 seconds)
        three_minutes_ms = 3 * 60 * 1000  # 3 minutes in milliseconds
        if len(audio1) > three_minutes_ms:
            audio1_cropped = audio1[:three_minutes_ms]
        else:
            audio1_cropped = audio1
        
        progress_bar.progress(55)
        status_text.text("Applying fade out effect...")
        
        # Apply fade out effect (2 seconds fade out)
        fade_duration_ms = 2000  # 2 seconds
        audio1_with_fade = audio1_cropped.fade_out(fade_duration_ms)
        
        progress_bar.progress(70)
        status_text.text("Combining audio files...")
        
        # Append second audio to the processed first audio
        combined_audio = audio1_with_fade + audio2
        
        progress_bar.progress(85)
        status_text.text("Converting to MP3 format...")
        
        # Export as MP3
        output_buffer = io.BytesIO()
        combined_audio.export(output_buffer, format="mp3", bitrate="192k")
        output_buffer.seek(0)
        
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Clean up temporary files
        try:
            os.unlink(tmp1.name)
            os.unlink(tmp2.name)
        except:
            pass  # Ignore cleanup errors
        
        return output_buffer.getvalue(), None
        
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            if 'tmp1' in locals() and tmp1:
                os.unlink(tmp1.name)
            if 'tmp2' in locals() and tmp2:
                os.unlink(tmp2.name)
        except:
            pass
        
        return None, f"Error processing audio files: {str(e)}"

def main():
    st.title("🎵 Audio File Processor")
    st.markdown("Upload two audio files to automatically process and combine them.")
    
    # Instructions
    with st.expander("📋 How it works", expanded=True):
        st.markdown("""
        1. **Upload first audio file** (MP3 or WAV) - will be cropped to exactly 3 minutes
        2. **Upload second audio file** (MP3 or WAV) - will be appended to the first
        3. The app will:
           - Crop the first file to 3 minutes
           - Add a 2-second fade out effect to the first file
           - Append the second file to the processed first file
           - Convert the result to MP3 format
        4. **Download** your processed audio file
        """)
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("First Audio File")
        st.caption("Will be cropped to 3 minutes with fade out")
        uploaded_file1 = st.file_uploader(
            "Choose first audio file",
            type=['mp3', 'wav'],
            key="file1",
            help="Upload MP3 or WAV file (max 100MB)"
        )
        
        if uploaded_file1:
            is_valid1, message1 = validate_audio_file(uploaded_file1)
            if is_valid1:
                st.success(f"✅ {uploaded_file1.name} loaded successfully")
                st.info(f"File size: {uploaded_file1.size / (1024*1024):.1f} MB")
            else:
                st.error(f"❌ {message1}")
    
    with col2:
        st.subheader("Second Audio File")
        st.caption("Will be appended to the processed first file")
        uploaded_file2 = st.file_uploader(
            "Choose second audio file",
            type=['mp3', 'wav'],
            key="file2",
            help="Upload MP3 or WAV file (max 100MB)"
        )
        
        if uploaded_file2:
            is_valid2, message2 = validate_audio_file(uploaded_file2)
            if is_valid2:
                st.success(f"✅ {uploaded_file2.name} loaded successfully")
                st.info(f"File size: {uploaded_file2.size / (1024*1024):.1f} MB")
            else:
                st.error(f"❌ {message2}")
    
    # Process button
    st.markdown("---")
    
    if uploaded_file1 and uploaded_file2:
        # Validate both files
        is_valid1, message1 = validate_audio_file(uploaded_file1)
        is_valid2, message2 = validate_audio_file(uploaded_file2)
        
        if is_valid1 and is_valid2:
            if st.button("🎵 Process Audio Files", type="primary", use_container_width=True):
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process the files
                processed_data, error = process_audio_files(
                    uploaded_file1.getvalue(),
                    uploaded_file2.getvalue(),
                    uploaded_file1.name,
                    uploaded_file2.name,
                    progress_bar,
                    status_text
                )
                
                if error:
                    st.error(f"❌ Processing failed: {error}")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.success("✅ Audio processing completed successfully!")
                    
                    # Generate download filename
                    timestamp = int(time.time())
                    download_filename = f"processed_audio_{timestamp}.mp3"
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download Processed Audio (MP3)",
                        data=processed_data,
                        file_name=download_filename,
                        mime="audio/mpeg",
                        type="secondary",
                        use_container_width=True
                    )
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
        else:
            st.warning("⚠️ Please upload valid audio files before processing.")
    else:
        st.info("👆 Please upload both audio files to begin processing.")
    
    # Footer with technical information
    st.markdown("---")
    with st.expander("ℹ️ Technical Details"):
        st.markdown("""
        **Supported Formats:** MP3, WAV  
        **Processing Steps:**
        - First file: Cropped to exactly 180 seconds (3 minutes)
        - Fade out: 2-second fade applied to end of first file
        - Combination: Second file appended seamlessly
        - Output: MP3 format at 192kbps bitrate
        
        **Requirements:** This application uses FFmpeg for audio processing.
        """)

if __name__ == "__main__":
    main()
