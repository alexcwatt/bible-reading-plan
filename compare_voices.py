#!/usr/bin/env python3
"""
Generate sample intro with different voices for comparison.
"""

from google.cloud import texttospeech
import os

SAMPLE_TEXT = "Week 1, Day 1. Today's reading is Genesis 1-2; Psalm 19; and Mark 1."

VOICES_TO_TEST = [
    ("chirp3-achernar", "en-US-Chirp3-HD-Achernar"),
    ("chirp3-alnilam", "en-US-Chirp3-HD-Alnilam"),
    ("chirp3-charon", "en-US-Chirp3-HD-Charon"),
    ("chirp3-gacrux", "en-US-Chirp3-HD-Gacrux"),
    ("chirp3-rasalgethi", "en-US-Chirp3-HD-Rasalgethi"),
    ("chirp3-schedar", "en-US-Chirp3-HD-Schedar"),
    ("chirp3-vindemiatrix", "en-US-Chirp3-HD-Vindemiatrix"),
]

def generate_sample(voice_label, voice_name):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=SAMPLE_TEXT)

    if voice_name:
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    output_file = f"build/voice_samples/{voice_label}.mp3"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "wb") as out:
        out.write(response.audio_content)

    print(f"Generated: {output_file}")
    return output_file

if __name__ == "__main__":
    print(f"Generating samples with text: '{SAMPLE_TEXT}'")
    print()

    for voice_label, voice_name in VOICES_TO_TEST:
        display_name = voice_name if voice_name else "Auto (NEUTRAL)"
        print(f"{voice_label:15s} ({display_name})")
        try:
            generate_sample(voice_label, voice_name)
        except Exception as e:
            print(f"  ERROR: {e}")

    print()
    print("All samples generated in build/voice_samples/")
    print("Listen and compare to choose your favorite!")
