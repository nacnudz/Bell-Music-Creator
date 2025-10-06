import streamlit as st
import os
import tempfile
import io
from pydub import AudioSegment
from pydub.effects import normalize
import time
import requests
from requests.auth import HTTPBasicAuth

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

def load_algo_config():
    """Load Algo 8301 configuration from file"""
    import json
    config_file = "algo_config.json"
    default_config = {
        "enabled": False,
        "device_ip": "",
        "username": "admin",
        "password": ""
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"DEBUG: Loaded config: enabled={config.get('enabled')}, ip={config.get('device_ip')}, has_password={bool(config.get('password'))}")
                return config
        except Exception as e:
            print(f"DEBUG: Error loading config: {e}")
            return default_config
    else:
        print(f"DEBUG: Config file not found at {os.path.abspath(config_file)}")
    return default_config

def convert_to_algo_mp3(audio_segment, filename):
    """Convert AudioSegment to MP3 format for Algo 8301"""
    # Convert to mono for compatibility
    audio_mono = audio_segment.set_channels(1)
    # Export as MP3
    mp3_buffer = io.BytesIO()
    audio_mono.export(mp3_buffer, format="mp3", bitrate="192k")
    mp3_buffer.seek(0)
    return mp3_buffer.getvalue()

def upload_to_algo8301(audio_data, filename, device_ip, username, password):
    """Upload audio file to Algo 8301 IP Paging Adapter"""
    try:
        # Ensure filename has .mp3 extension
        if not filename.lower().endswith('.mp3'):
            filename = filename.rsplit('.', 1)[0] + '.mp3'
        
        # Clean filename: max 32 chars, no spaces
        filename = filename.replace(' ', '_')[:32]
        
        # Prepare the upload
        url = f"http://{device_ip}/api/files/upload"
        files = {'file': (filename, audio_data, 'audio/mpeg')}
        auth = HTTPBasicAuth(username, password)
        
        # Upload with timeout
        response = requests.post(url, files=files, auth=auth, timeout=30)
        
        if response.status_code == 200:
            return True, f"Successfully uploaded {filename} to Algo 8301"
        else:
            return False, f"Upload failed: {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "Upload failed: Connection timeout. Check device IP address."
    except requests.exceptions.ConnectionError:
        return False, "Upload failed: Cannot connect to device. Check IP address and network."
    except Exception as e:
        return False, f"Upload failed: {str(e)}"

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

def process_audio_files(file1_data, file2_data, file1_name, file2_name, progress_bar, status_text, is_file2_from_library=False, crop_duration=180, fade_out_duration=2.0, trim_start=0, fade_in_duration=0.0):
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
        
        # Trim start if specified
        if trim_start > 0:
            status_text.text(f"Trimming first {trim_start} seconds from start...")
            trim_start_ms = int(trim_start * 1000)
            audio1 = audio1[trim_start_ms:]
        
        status_text.text(f"Cropping music file to {crop_duration} seconds...")
        
        # Crop first audio to specified duration
        crop_duration_ms = int(crop_duration * 1000)  # Convert to milliseconds as integer
        if len(audio1) > crop_duration_ms:
            audio1_cropped = audio1[:crop_duration_ms]
        else:
            audio1_cropped = audio1
        
        progress_bar.progress(55)
        
        # Apply fade in effect if specified
        if fade_in_duration > 0:
            status_text.text(f"Applying {fade_in_duration} second fade in effect...")
            fade_in_duration_ms = int(fade_in_duration * 1000)
            audio1_cropped = audio1_cropped.fade_in(fade_in_duration_ms)
        
        status_text.text(f"Applying {fade_out_duration} second fade out effect...")
        
        # Apply fade out effect with specified duration
        fade_out_duration_ms = int(fade_out_duration * 1000)  # Convert to milliseconds as integer
        audio1_with_fade = audio1_cropped.fade_out(fade_out_duration_ms)
        
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
        
        return output_buffer.getvalue(), combined_audio, None
        
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            if 'tmp1' in locals() and tmp1:
                os.unlink(tmp1.name)
            if 'tmp2' in locals() and tmp2 is not None:
                os.unlink(tmp2.name)
        except:
            pass
        
        return None, None, f"Error processing audio files: {str(e)}"

def main():
    st.title("🔔 Bell Music Creator")
    st.markdown("Upload your music file and select the required bell to automatically create the required bell audio file for the bell system.")
    
    # Instructions
    with st.expander("📋 How it works", expanded=True):
        st.markdown("""
        1. **Upload music file** (MP3 or WAV) - will be cropped to your specified length
        2. **Choose bell file** - select from existing bell files or upload a new one
        3. **Customize settings** - adjust crop length and fade out duration
        4. The app will:
           - Trim the start of the music file (optional)
           - Crop the music file to your specified duration
           - Add fade in effect (optional)
           - Add fade out effect with your chosen duration
           - Append the selected bell file to the processed music file
           - Convert the result to MP3 format
        5. **Download** your processed audio file with automatic naming
        
        **Bell Files:** You can build a library of bell files by uploading new ones, which will be saved for future use.
        """)
    
    # Audio Files section
    st.subheader("🎵 Audio Files")
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Music File**")
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
            else:
                st.error(f"❌ {message1}")
    
    # Processing settings section - moved after music file
    st.markdown("---")
    st.subheader("⚙️ Processing Settings")
    settings_col1, settings_col2 = st.columns(2)
    
    with settings_col1:
        st.write("**Trim start of audio**")
        trim_col1, trim_col2 = st.columns(2)
        with trim_col1:
            trim_minutes = st.number_input(
                "Minutes",
                min_value=0,
                max_value=10,
                value=0,
                step=1,
                help="Minutes to skip from the start (0-10)",
                key="trim_minutes"
            )
        with trim_col2:
            trim_seconds = st.number_input(
                "Seconds",
                min_value=0,
                max_value=59,
                value=0,
                step=1,
                help="Seconds to skip from the start (0-59)",
                key="trim_seconds"
            )
        trim_start = trim_minutes * 60 + trim_seconds
        
        st.write("**Music file length**")
        duration_col1, duration_col2 = st.columns(2)
        with duration_col1:
            minutes = st.number_input(
                "Minutes",
                min_value=0,
                max_value=10,
                value=3,
                step=1,
                help="Minutes (0-10)"
            )
        with duration_col2:
            seconds = st.number_input(
                "Seconds",
                min_value=0,
                max_value=59,
                value=0,
                step=1,
                help="Seconds (0-59)"
            )
        crop_duration = minutes * 60 + seconds
        # Ensure minimum 10 seconds
        if crop_duration < 10:
            crop_duration = 10
            st.warning("Minimum duration is 10 seconds")
    
    with settings_col2:
        st.write("**Fade in duration**")
        fade_in_duration = st.number_input(
            "Seconds",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
            help="Length of fade in effect at the start of the music file",
            key="fade_in_seconds"
        )
        
        st.write("**Fade out duration**")
        fade_out_duration = st.number_input(
            "Seconds",
            min_value=0.5,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="Length of fade out effect at the end of the music file",
            key="fade_out_seconds"
        )
    
    # Update music file caption with current settings
    if uploaded_file1:
        caption_parts = []
        if trim_start > 0:
            caption_parts.append(f"skip first {trim_start}s")
        caption_parts.append(f"crop to {crop_duration}s")
        if fade_in_duration > 0:
            caption_parts.append(f"{fade_in_duration}s fade in")
        caption_parts.append(f"{fade_out_duration}s fade out")
        st.caption(f"Processing: {', '.join(caption_parts)}")
    
    st.markdown("---")
    with col2:
        st.write("**Choose Bell File**")
        
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
                bell_file_path = os.path.join(BELL_FILES_DIR, selected_bell)
                if os.path.exists(bell_file_path):
                    bell_file_name = selected_bell
                    is_from_library = True
    
    # Check if we have both music file and bell file ready
    has_music_file = uploaded_file1 is not None
    has_bell_file = (bell_file_name is not None and 
                     (is_from_library or bell_file_data is not None))
    
    if has_music_file and has_bell_file:
        # Validate music file
        is_valid1, message1 = validate_audio_file(uploaded_file1)
        
        if is_valid1:
            # Filename customization
            st.subheader("📝 Output File Name")
            
            # Create week options
            week_options = [f"Week {i} Bell" for i in range(1, 12)] + ["Custom"]
            
            selected_option = st.selectbox(
                "Select output file name",
                options=week_options,
                help="Choose a week bell name or select Custom to enter your own"
            )
            
            # Determine filename based on selection
            if selected_option == "Custom":
                # Generate automatic filename for custom
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
            else:
                # Extract week number from selection (e.g., "Week 1 Bell" -> 1)
                week_num = selected_option.split()[1]
                final_filename = f"week_{week_num}_bell_music.mp3"
                
            st.info(f"Output file name: **{final_filename}**")
            
            if st.button("🎵 Process Audio Files", type="primary", use_container_width=True):
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process the files
                processed_data, audio_segment, error = process_audio_files(
                    uploaded_file1.getvalue(),
                    bell_file_data,
                    uploaded_file1.name,
                    bell_file_name,
                    progress_bar,
                    status_text,
                    is_from_library,
                    crop_duration,
                    fade_out_duration,
                    trim_start,
                    fade_in_duration
                )
                
                if error:
                    st.error(f"❌ Processing failed: {error}")
                    progress_bar.empty()
                    status_text.empty()
                else:
                    st.success("✅ Audio processing completed successfully!")
                    
                    # Store audio segment in session state for buttons
                    st.session_state['processed_audio_segment'] = audio_segment
                    st.session_state['processed_filename'] = final_filename
                    st.session_state['processed_data'] = processed_data
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Load Algo 8301 configuration from file (reload after processing)
                    algo_config = load_algo_config()
                    
                    # Create two columns for download and upload buttons
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        # Download button
                        st.download_button(
                            label="📥 Download to Computer",
                            data=processed_data,
                            file_name=final_filename,
                            mime="audio/mpeg",
                            type="primary",
                            use_container_width=True
                        )
                    
                    with btn_col2:
                        # Upload to Bell System button (if configured in config file)
                        is_enabled = algo_config.get('enabled', False)
                        has_ip = bool(algo_config.get('device_ip', ''))
                        has_password = bool(algo_config.get('password', ''))
                        
                        st.write(f"Debug: enabled={is_enabled}, has_ip={has_ip}, has_password={has_password}")
                        
                        if is_enabled and has_ip and has_password:
                            if st.button("📡 Upload to Bell System", type="primary", use_container_width=True):
                                with st.spinner("Converting and uploading to Bell System..."):
                                    # Convert to MP3 format
                                    mp3_data = convert_to_algo_mp3(audio_segment, final_filename)
                                    
                                    # Upload to device
                                    success, message = upload_to_algo8301(
                                        mp3_data,
                                        final_filename,
                                        algo_config['device_ip'],
                                        algo_config.get('username', 'admin'),
                                        algo_config['password']
                                    )
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                    else:
                                        st.error(f"❌ {message}")
                        else:
                            st.info("Bell System upload not configured")
        else:
            st.error("❌ Please upload a valid music file before processing.")
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
        - Trim start: Optional trimming from the beginning (0-600 seconds)
        - Music file: Cropped to your specified duration (10-600 seconds)
        - Fade in: Optional fade in effect (0-10 seconds) applied at the start
        - Fade out: Customizable fade out duration (0.5-10 seconds) applied to end of music file
        - Combination: Bell file appended seamlessly after fade
        - Output: MP3 format at 192kbps bitrate
        - Naming: Automatic naming as "MusicFileName_Bell.mp3" with option to customize
        
        **Requirements:** This application uses FFmpeg for audio processing.
        """)

if __name__ == "__main__":
    main()
