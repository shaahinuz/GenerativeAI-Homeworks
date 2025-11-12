import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
from PIL import Image
from io import BytesIO

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def transcribe_audio(audio_file):
    try:
        if not audio_file:
            raise Exception("No audio data provided")

        audio_file.seek(0)
        audio_bytes = audio_file.read()
        audio_buffer = BytesIO(audio_bytes)
        audio_buffer.name = "audio.wav"

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer,
            language="en",
            prompt="Description of an image containing objects, scenes, animals, people, or artistic concepts."
        )

        return transcript.text

    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")


def enhance_prompt(user_text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Convert user requests into detailed image generation prompts. Be descriptive but concise."},
            {"role": "user", "content": f"Create an image prompt for: {user_text}"}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


def generate_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )

        image_url = response.data[0].url
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()

        return Image.open(BytesIO(img_response.content))

    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


def main():
    st.set_page_config(
        page_title="Voice to Image Generator",
        layout="centered"
    )

    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
        }
        .stTextArea textarea {
            border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Voice to Image Generator")

    if not OPENAI_API_KEY:
        st.error("Please set OPENAI_API_KEY in .env file")
        return

    with st.sidebar:
        st.markdown("## Models Used")
        st.markdown("### 1. Speech-to-Text")
        st.code("OpenAI Whisper-1")
        st.caption("Converts voice to text")

        st.markdown("### 2. Prompt Enhancement")
        st.code("OpenAI GPT-4o-mini")
        st.caption("Enhances user text into detailed prompts")

        st.markdown("### 3. Image Generation")
        st.code("OpenAI DALL-E 2")
        st.caption("Generates 1024x1024 images")

        st.markdown("---")
        st.markdown("## Pipeline Overview")
        st.markdown("""
        1. Record voice
        2. Transcribe with Whisper
        3. Enhance with GPT-4o-mini
        4. Generate with DALL-E 2
        """)

    if 'audio_input_key' not in st.session_state:
        st.session_state['audio_input_key'] = 0

    st.markdown("### Step 1: Record Audio")
    st.info("Your browser will ask for microphone permission.")
    audio_bytes = st.audio_input("Record your image description", key=f"audio_input_{st.session_state['audio_input_key']}")

    if audio_bytes:
        st.markdown("**Your Recording:**")
        st.audio(audio_bytes, format='audio/wav')

        st.markdown("### Step 2: Transcribe Audio")
        st.info("Model: OpenAI Whisper-1")

        with st.status("Processing audio...", expanded=True) as status:
            try:
                st.write("Transcribing audio using Whisper-1...")
                transcript = transcribe_audio(audio_bytes)

                if not transcript or transcript.strip() == "":
                    st.error("No text detected. Speak clearly and record for at least 3 seconds.")
                    status.update(label="Transcription failed", state="error")
                else:
                    status.update(label="Transcription complete", state="complete")

                    st.markdown("### Step 3: Review Transcription")

                    edited_transcript = st.text_area(
                        "Review and edit:",
                        value=transcript,
                        height=100
                    )

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        enhance_button = st.button("Enhance prompt and Generate Image", type="primary", use_container_width=True)

                    with col2:
                        if st.button("Record New Voice", use_container_width=True):
                            st.session_state['audio_input_key'] += 1
                            st.session_state['prompt_ready'] = False
                            if 'pending_transcript' in st.session_state:
                                del st.session_state['pending_transcript']
                            if 'pending_prompt' in st.session_state:
                                del st.session_state['pending_prompt']
                            st.rerun()

                    if enhance_button:
                        st.markdown("### Step 4: Enhance Prompt")
                        st.info("Model: OpenAI GPT-4o-mini")

                        with st.status("Enhancing prompt...", expanded=True) as enhance_status:
                            try:
                                st.write("Using GPT-4o-mini to enhance prompt...")
                                enhanced = enhance_prompt(edited_transcript)
                                enhance_status.update(label="Prompt enhanced", state="complete")

                                st.session_state['pending_transcript'] = edited_transcript
                                st.session_state['pending_prompt'] = enhanced
                                st.session_state['prompt_ready'] = True

                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                                enhance_status.update(label="Error occurred", state="error")
                                st.session_state['prompt_ready'] = False

                    if st.session_state.get('prompt_ready', False):
                        st.markdown("---")
                        st.markdown("### Step 5: Review Enhanced Prompt")

                        with st.expander("View Data", expanded=True):
                            st.markdown("**Original Transcript:**")
                            st.text(st.session_state['pending_transcript'])
                            st.markdown("**Enhanced Prompt for DALL-E 2:**")
                            st.success(st.session_state['pending_prompt'])

                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            if st.button("Accept", type="primary", use_container_width=True):
                                st.markdown("### Step 6: Generate Image")
                                st.info("Model: OpenAI DALL-E 2 (1024x1024)")

                                with st.status("Generating image...", expanded=True) as img_status:
                                    try:
                                        st.write("Using DALL-E 2 to generate image...")
                                        st.write("This may take 30-60 seconds.")

                                        with st.spinner("Generating..."):
                                            image = generate_image(st.session_state['pending_prompt'])

                                        st.success("Image generated")
                                        img_status.update(label="Complete", state="complete")

                                        st.session_state['last_transcript'] = st.session_state['pending_transcript']
                                        st.session_state['last_enhanced'] = st.session_state['pending_prompt']
                                        st.session_state['last_image'] = image
                                        st.session_state['prompt_ready'] = False
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                        img_status.update(label="Error occurred", state="error")

                        with col2:
                            if st.button("Try New", use_container_width=True):
                                with st.status("Regenerating prompt...", expanded=True) as regen_status:
                                    try:
                                        enhanced = enhance_prompt(st.session_state['pending_transcript'])
                                        st.session_state['pending_prompt'] = enhanced
                                        regen_status.update(label="New prompt generated", state="complete")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                        regen_status.update(label="Error occurred", state="error")

                        with col3:
                            if st.button("Record New Voice", use_container_width=True, key="record_new_2"):
                                st.session_state['audio_input_key'] += 1
                                st.session_state['prompt_ready'] = False
                                if 'pending_transcript' in st.session_state:
                                    del st.session_state['pending_transcript']
                                if 'pending_prompt' in st.session_state:
                                    del st.session_state['pending_prompt']
                                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")
                status.update(label="Error occurred", state="error")

    if 'last_image' in st.session_state:
        st.markdown("---")
        st.markdown("## Final Result")

        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            st.image(st.session_state['last_image'], use_container_width=True)

        with st.expander("View Complete Pipeline Data", expanded=False):
            st.markdown("### Pipeline Steps")

            st.markdown("#### Step 1: Audio Recording")
            st.caption("Input: Voice recording")

            st.markdown("#### Step 2: Speech-to-Text")
            st.caption("Model: OpenAI Whisper-1")
            st.markdown("**Transcript:**")
            st.text(st.session_state['last_transcript'])

            st.markdown("---")

            st.markdown("#### Step 3: Prompt Enhancement")
            st.caption("Model: OpenAI GPT-4o-mini")
            st.markdown("**Original Input:**")
            st.text(st.session_state['last_transcript'])
            st.markdown("**Enhanced Prompt:**")
            st.success(st.session_state['last_enhanced'])

            st.markdown("---")

            st.markdown("#### Step 4: Image Generation")
            st.caption("Model: OpenAI DALL-E 2")
            st.markdown("**Input Prompt:**")
            st.text(st.session_state['last_enhanced'])
            st.markdown("**Output:** 1024x1024 image (displayed above)")


if __name__ == "__main__":
    main()
