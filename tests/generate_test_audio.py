"""Utility to generate pre-recorded sample audio files for e2e tests."""
import io
import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 16000

def create_sample_wav(filename: str, prompt_text: str, duration: float = 1.5):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Synthesize multi-tone audio wave
    carrier = 0.5 * np.sin(2 * np.pi * 300 * t) + 0.3 * np.sin(2 * np.pi * 600 * t)
    audio = carrier.astype(np.float32)
    
    # Prepend or embed text marker in metadata/payload
    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    # Write WAV file
    buffer = io.BytesIO()
    sf.write(buffer, audio, SAMPLE_RATE, format="WAV", subtype="PCM_16")
    wav_bytes = buffer.getvalue()
    
    # Store audio with tag in comments or custom trailing header
    tagged_bytes = wav_bytes + f"\nPROMPT:{prompt_text}\n".encode("utf-8")
    with open(filename, "wb") as f:
        f.write(tagged_bytes)
    return filename

if __name__ == "__main__":
    out_dir = "tests/audio_samples"
    os.makedirs(out_dir, exist_ok=True)
    create_sample_wav(f"{out_dir}/hausa_greeting.wav", "Sannu Hausa")
    create_sample_wav(f"{out_dir}/pin_1234.wav", "1234")
    create_sample_wav(f"{out_dir}/check_balance.wav", "Ina son duba kudi na")
    create_sample_wav(f"{out_dir}/send_musa.wav", "Send 5,000 naira to Musa")
    create_sample_wav(f"{out_dir}/confirm_yes.wav", "Yes proceed")
    create_sample_wav(f"{out_dir}/pay_bill_yo.wav", "Mo fe san owo ina electricity")
    create_sample_wav(f"{out_dir}/angry_human.wav", "I am angry, I want to speak to a person right now")
    create_sample_wav(f"{out_dir}/wrong_pin.wav", "9876")
    create_sample_wav(f"{out_dir}/low_conf.wav", "LOW_CONFIDENCE mumbling")
    print("Sample test audio files generated.")
