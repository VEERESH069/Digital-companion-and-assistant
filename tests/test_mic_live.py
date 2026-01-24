import numpy as np
import sounddevice as sd
from pre_visit_agent.services.stt_service import RealTimeSTT
import queue
import sys

def main():
    print("Initializing STT Service (English)...")
    # Increased min_duration to 2.5s for better accuracy (prevents cutting words)
    stt = RealTimeSTT(model_size="base", language="en", min_duration=2.5) 
    
    print("\n" + "="*50)
    print("  LIVE MICROPHONE TEST (English)")
    print("  Speak in English. Wait ~3s for transcript.")
    print("  DEBUG: Check the Volume indicator below.")
    print("="*50 + "\n")

    # Callback to print text
    def on_transcription(text):
        print(f"\n>> TRANSCRIPT: {text}")
        print("-" * 20)

    stt.start(on_transcription)
    
    # Audio callback configuration
    q = queue.Queue()
    
    def audio_callback(indata, frames, time, status):
        """This is called by sounddevice in a separate thread for every audio block."""
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    try:
        with sd.InputStream(samplerate=16000, 
                          channels=1, 
                          dtype='float32',
                          callback=audio_callback,
                          blocksize=8000): # 0.5s chunks
            
            print("Microphone active... Start speaking!")
            
            while True:
                indata = q.get()
                audio_chunk = indata.flatten()
                
                # --- Volume Check Debug ---
                vol = np.max(np.abs(audio_chunk))
                if vol < 0.01:
                    print(f"\r[Volume: {vol:.4f} (Too Quiet/Silence)]", end="", flush=True)
                elif vol > 0.01:
                    print(f"\r[Volume: {vol:.4f} (Good)]             ", end="", flush=True)
                # --------------------------

                stt.add_audio_chunk(audio_chunk)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        stt.stop()
        print("Test finished.")

if __name__ == "__main__":
    main()
