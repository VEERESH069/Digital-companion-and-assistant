"""
Interactive Audio Player - Test Cartesia Voice Samples
"""
import pygame
import os
from pathlib import Path
import time

# Initialize pygame mixer
pygame.mixer.init()

# Audio files
samples = {
    "1": ("Arabic Greeting", "output/arabic_sample.wav"),
    "2": ("English Greeting", "output/english_sample.wav"),
    "3": ("Arabic Medical Question", "output/arabic_medical.wav"),
    "4": ("English Medical Question", "output/english_medical.wav"),
}

def play_audio(filepath):
    """Play an audio file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        print(f"\n🔊 Playing: {filepath}")
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        
        # Wait for playback to complete
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("✅ Playback complete")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  🎤 CARTESIA VOICE SAMPLE PLAYER")
    print("=" * 70)
    
    while True:
        print("\n📋 Available Samples:")
        print("-" * 70)
        for key, (name, _) in samples.items():
            print(f"  {key}. {name}")
        print("  5. Play All Samples")
        print("  Q. Quit")
        print("-" * 70)
        
        choice = input("\n🔊 Select a sample to play: ").strip().lower()
        
        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        elif choice == '5':
            # Play all samples
            print("\n🎵 Playing all samples...\n")
            for key in sorted(samples.keys()):
                name, filepath = samples[key]
                print(f"\n{'='*70}")
                print(f"  {name}")
                print('='*70)
                play_audio(filepath)
                time.sleep(0.5)  # Brief pause between samples
        elif choice in samples:
            name, filepath = samples[choice]
            print(f"\n{'='*70}")
            print(f"  {name}")
            print('='*70)
            play_audio(filepath)
        else:
            print("❌ Invalid choice. Please try again.")
    
    pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        pygame.quit()
