import streamlit as st
import os
import tempfile
import io
from pydub import AudioSegment
from pydub.effects import normalize
import time

# Configure page
st.set_page_config(
    page_title="Bell Music Creator",
    page_icon="🔔",
    layout="wide"
)

# Create bell files directory if it doesn't exist
BELL_FILES_DIR = "bell_files"
if not os.path.exists(BELL_FILES_DIR):
    os.makedirs(BELL_FILES_DIR)

def get_available_bell_files():
    """Get list of available bell files"""
    bell_files = []
    if os.path.exists(BELL_FILES_DIR):
        for file in os.listdir(BELL_FILES_DIR):
            if file.lower().endswith(('.mp3', '.wav')):
                bell_files.append(file)
    return sorted(bell_files)

def save_bell_file(uploaded_file):
    """Save uploaded bell file to bell files directory"""
    file_path = os.path.join(BELL_FILES_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

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

def process_audio_files(file1_data, file2_data, file1_name, file2_name, progress_bar, status_text, is_file2_from_library=False, crop_duration=180, fade_duration=2):
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
        status_text.text("Loading bell audio file...")
        
        # Load second audio file (bell file)
        if is_file2_from_library:
            # Load directly from bell files directory
            bell_file_path = os.path.join(BELL_FILES_DIR, file2_name)
            audio2 = AudioSegment.from_file(bell_file_path)
            tmp2 = None  # No temp file needed
        else:
            # Load from uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file2_name.split('.')[-1]}") as tmp2:
                tmp2.write(file2_data)
                tmp2.flush()
                audio2 = AudioSegment.from_file(tmp2.name)
        
        progress_bar.progress(40)
        status_text.text(f"Cropping music file to {crop_duration} seconds...")
        
        # Crop first audio to specified duration
        crop_duration_ms = crop_duration * 1000  # Convert to milliseconds
        if len(audio1) > crop_duration_ms:
            audio1_cropped = audio1[:crop_duration_ms]
        else:
            audio1_cropped = audio1
        
        progress_bar.progress(55)
        status_text.text(f"Applying {fade_duration} second fade out effect...")
        
        # Apply fade out effect with specified duration
        fade_duration_ms = fade_duration * 1000  # Convert to milliseconds
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
            if tmp2 is not None:
                os.unlink(tmp2.name)
        except:
            pass  # Ignore cleanup errors
        
        return output_buffer.getvalue(), None
        
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            if 'tmp1' in locals() and tmp1:
                os.unlink(tmp1.name)
            if 'tmp2' in locals() and tmp2 is not None:
                os.unlink(tmp2.name)
        except:
            pass
        
        return None, f"Error processing audio files: {str(e)}"

def main():
    st.title("🔔 Bell Music Creator")
    st.markdown("Upload two audio files to automatically process and combine them.")
    
    # Instructions
    with st.expander("📋 How it works", expanded=True):
        st.markdown("""
        1. **Upload music file** (MP3 or WAV) - will be cropped to your specified length
        2. **Choose bell file** - select from existing bell files or upload a new one
        3. **Customize settings** - adjust crop length and fade out duration
        4. The app will:
           - Crop the music file to your specified duration
           - Add a fade out effect with your chosen duration
           - Append the selected bell file to the processed music file
           - Convert the result to MP3 format
        5. **Download** your processed audio file with automatic naming
        
        **Bell Files:** You can build a library of bell files by uploading new ones, which will be saved for future use.
        """)
    
    # Processing settings section
    st.subheader("⚙️ Processing Settings")
    settings_col1, settings_col2 = st.columns(2)
    
    with settings_col1:
        crop_duration = st.number_input(
            "Music file length (seconds)",
            min_value=10,
            max_value=600,
            value=180,
            step=10,
            help="How long to crop the music file (10 seconds to 10 minutes)"
        )
    
    with settings_col2:
        fade_duration = st.number_input(
            "Fade out duration (seconds)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Length of fade out effect at the end of the music file"
        )
    
    st.markdown("---")
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Music File")
        st.caption(f"Will be cropped to {crop_duration} seconds with {fade_duration}s fade out")
        uploaded_file1 = st.file_uploader(
            "Choose music file",
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
        st.subheader("Choose Bell File")
        st.caption("Will be appended to the processed music file")
        
        # Get available bell files
        available_bells = get_available_bell_files()
        bell_options = available_bells + ["Upload new bell file..."]
        
        selected_bell = st.selectbox(
            "Select a bell file",
            options=bell_options,
            key="bell_selector",
            help="Choose from existing bell files or upload a new one"
        )
        
        uploaded_file2 = None
        bell_file_name = None
        bell_file_data = None
        is_from_library = False
        
        if selected_bell == "Upload new bell file...":
            uploaded_file2 = st.file_uploader(
                "Upload new bell file",
                type=['mp3', 'wav'],
                key="file2",
                help="Upload MP3 or WAV file (max 100MB)"
            )
            
            if uploaded_file2:
                is_valid2, message2 = validate_audio_file(uploaded_file2)
                if is_valid2:
                    st.success(f"✅ {uploaded_file2.name} loaded successfully")
                    st.info(f"File size: {uploaded_file2.size / (1024*1024):.1f} MB")
                    
                    # Ask if user wants to save this bell file
                    if st.button("💾 Save this bell file for future use", key="save_bell"):
                        save_bell_file(uploaded_file2)
                        st.success(f"Bell file saved! It will be available in the dropdown next time.")
                        st.rerun()
                    
                    bell_file_name = uploaded_file2.name
                    bell_file_data = uploaded_file2.getvalue()
                else:
                    st.error(f"❌ {message2}")
        else:
            # Using existing bell file
            if selected_bell:
                st.success(f"✅ {selected_bell} selected")
                bell_file_path = os.path.join(BELL_FILES_DIR, selected_bell)
                if os.path.exists(bell_file_path):
                    file_size = os.path.getsize(bell_file_path) / (1024*1024)
                    st.info(f"File size: {file_size:.1f} MB")
                    bell_file_name = selected_bell
                    is_from_library = True
    
    # Process button
    st.markdown("---")
    
    # Check if we have both music file and bell file ready
    has_music_file = uploaded_file1 is not None
    has_bell_file = (bell_file_name is not None and 
                     (is_from_library or bell_file_data is not None))
    
    if has_music_file and has_bell_file:
        # Validate music file
        is_valid1, message1 = validate_audio_file(uploaded_file1)
        
        if is_valid1:
            # Filename customization
            st.markdown("---")
            st.subheader("📝 Output File Name")
            
            # Generate automatic filename
            music_basename = os.path.splitext(uploaded_file1.name)[0]
            auto_filename = f"{music_basename}_Bell.mp3"
            
            custom_filename = st.text_input(
                "File name (without extension)",
                value=os.path.splitext(auto_filename)[0],
                help="The file will be saved as MP3 format"
            )
            
            # Ensure .mp3 extension
            if not custom_filename.endswith('.mp3'):
                final_filename = f"{custom_filename}.mp3"
            else:
                final_filename = custom_filename
                
            st.info(f"Download file name: **{final_filename}**")
            
            if st.button("🎵 Process Audio Files", type="primary", use_container_width=True):
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process the files
                processed_data, error = process_audio_files(
                    uploaded_file1.getvalue(),
                    bell_file_data,
                    uploaded_file1.name,
                    bell_file_name,
                    progress_bar,
                    status_text,
                    is_from_library,
                    crop_duration,
                    fade_duration
                )
                
                if error:
                    st.error(f"❌ Processing failed: {error}")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.success("✅ Audio processing completed successfully!")
                    
                    # Provide download button with custom filename
                    st.download_button(
                        label="📥 Download Processed Audio (MP3)",
                        data=processed_data,
                        file_name=final_filename,
                        mime="audio/mpeg",
                        type="secondary",
                        use_container_width=True
                    )
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
        else:
            st.warning("⚠️ Please upload a valid music file before processing.")
    else:
        if not has_music_file:
            st.info("👆 Please upload a music file to begin processing.")
        elif not has_bell_file:
            st.info("👆 Please select or upload a bell file to begin processing.")
    
    # Footer with technical information
    st.markdown("---")
    with st.expander("ℹ️ Technical Details"):
        st.markdown("""
        **Supported Formats:** MP3, WAV  
        **Processing Steps:**
        - Music file: Cropped to your specified duration (10-600 seconds)
        - Fade out: Customizable fade duration (0.5-10 seconds) applied to end of music file
        - Combination: Bell file appended seamlessly after fade
        - Output: MP3 format at 192kbps bitrate
        - Naming: Automatic naming as "MusicFileName_Bell.mp3" with option to customize
        
        **Requirements:** This application uses FFmpeg for audio processing.
        """)

if __name__ == "__main__":
    main()
