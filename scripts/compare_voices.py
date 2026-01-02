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
    ("chirp3-gacrux", "en-US-Chirp3-HD-Gacrux"),
    ("chirp3-schedar", "en-US-Chirp3-HD-Schedar"),
    ("chirp3-alnilam", "en-US-Chirp3-HD-Alnilam"),
    ("neural2-a", "en-US-Neural2-A"),
    ("neural2-d", "en-US-Neural2-D"),
    ("neural2-j", "en-US-Neural2-J"),
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

    concat_file = output_file + ".concat.txt"
    wav_files = []

    try:
        import hashlib
        wav_cache_dir = "build/wav_cache"
        os.makedirs(wav_cache_dir, exist_ok=True)

        for segment in segments:
            mp3_path = segment.file_path()

            with open(mp3_path, "rb") as f:
                mp3_hash = hashlib.md5(f.read()).hexdigest()

            cached_wav = os.path.join(wav_cache_dir, f"{mp3_hash}.wav")

            if not os.path.exists(cached_wav):
                ffmpeg.input(mp3_path).output(
                    cached_wav, acodec="pcm_s16le", ar="44100", ac=1
                ).run(overwrite_output=True, quiet=True)

            wav_files.append(cached_wav)

        with open(concat_file, "w") as f:
            for wav_file in wav_files:
                f.write(f"file '{os.path.abspath(wav_file)}'\n")

        ffmpeg.input(concat_file, format="concat", safe=0).output(
            output_file, acodec="libmp3lame", audio_bitrate="128k", ar="44100"
        ).run(overwrite_output=True, quiet=True)

    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)

    print(f"Generated: {output_file}")

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"Generating samples: announcement + {CHAPTER} ESV audio")
    print(f"Processing {len(VOICES_TO_TEST)} voices in parallel...")
    print()

    def build_with_status(voice_tuple):
        voice_label, voice_name = voice_tuple
        try:
            build_sample_with_voice(voice_label, voice_name)
            return voice_label, voice_name, None
        except Exception as e:
            import traceback
            return voice_label, voice_name, traceback.format_exc()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(build_with_status, voice): voice for voice in VOICES_TO_TEST}

        for future in as_completed(futures):
            voice_label, voice_name, error = future.result()
            if error:
                print(f"{voice_label:15s} ({voice_name}) - ERROR")
                print(error)
            else:
                print(f"{voice_label:15s} ({voice_name}) - DONE")

    print()
    print("All samples generated in build/voice_samples/")
    print("Each sample includes: buffer -> announcement -> buffer -> ESV audio")
