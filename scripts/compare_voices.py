#!/usr/bin/env python3
"""
Generate voice samples with announcement + ESV audio.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ffmpeg
from bible_reading_plan.utils.podcast_segments import BufferSegment, ESVReadingSegment, GeneratedSpeechSegment
from bible_reading_plan.utils.podcast_episode import _create_chapter_announcement_text

VOICES_TO_TEST = [
    ("chirp3-charon", "en-US-Chirp3-HD-Charon"),
    ("neural2-d", "en-US-Neural2-D"),
    ("studio-q", "en-US-Studio-Q"),
]

CHAPTER = "Genesis 1"

def build_sample_with_voice(voice_label, voice_name):
    output_file = f"build/voice_samples/{voice_label}_with_esv.mp3"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    announcement_text = _create_chapter_announcement_text(CHAPTER)

    announcement_segment = GeneratedSpeechSegment(announcement_text)
    announcement_segment.voice_name = voice_name

    buffer_segment = BufferSegment(duration_ms=1000)
    esv_segment = ESVReadingSegment(CHAPTER)

    segments = [buffer_segment, announcement_segment, buffer_segment, esv_segment]

    for segment in segments:
        if isinstance(segment, GeneratedSpeechSegment) and hasattr(segment, 'voice_name'):
            original_build = segment._build
            def custom_build(voice=voice_name):
                from google.cloud import texttospeech
                client = texttospeech.TextToSpeechClient()

                if segment.text.strip().startswith('<speak>'):
                    synthesis_input = texttospeech.SynthesisInput(ssml=segment.text)
                else:
                    synthesis_input = texttospeech.SynthesisInput(text=segment.text)

                voice_params = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name=voice
                )

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )

                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )

                with open(segment.file_path(), "wb") as out:
                    out.write(response.audio_content)

            segment._build = custom_build
            segment.build(force=True)
        else:
            segment.build(force=False)

    temp_dir = os.path.dirname(output_file)
    concat_file = output_file + ".concat.txt"
    wav_files = []

    try:
        for i, segment in enumerate(segments):
            wav_file = os.path.join(temp_dir, f".temp_voice_{voice_label}_{i:03d}.wav")
            wav_files.append(wav_file)

            ffmpeg.input(segment.file_path()).output(
                wav_file, acodec="pcm_s16le", ar="44100", ac=1
            ).run(overwrite_output=True, quiet=True)

        with open(concat_file, "w") as f:
            for wav_file in wav_files:
                f.write(f"file '{os.path.abspath(wav_file)}'\n")

        ffmpeg.input(concat_file, format="concat", safe=0).output(
            output_file, acodec="libmp3lame", audio_bitrate="128k", ar="44100"
        ).run(overwrite_output=True, quiet=True)

    finally:
        for wav_file in wav_files:
            if os.path.exists(wav_file):
                os.remove(wav_file)
        if os.path.exists(concat_file):
            os.remove(concat_file)

    print(f"Generated: {output_file}")

if __name__ == "__main__":
    print(f"Generating samples: announcement + {CHAPTER} ESV audio")
    print()

    for voice_label, voice_name in VOICES_TO_TEST:
        print(f"{voice_label:15s} ({voice_name})")
        try:
            build_sample_with_voice(voice_label, voice_name)
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print()
    print("All samples generated in build/voice_samples/")
    print("Each sample includes: buffer -> announcement -> buffer -> ESV audio")
