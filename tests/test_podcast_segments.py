import os
import tempfile
import unittest.mock as mock

import pytest

from bible_reading_plan.utils.podcast_segments import (
    BufferSegment,
    ESVReadingSegment,
    GeneratedSpeechSegment,
    PodcastSegment,
)


class TestPodcastSegment:
    def test_base_class_raises_not_implemented(self):
        segment = PodcastSegment()

        with pytest.raises(NotImplementedError):
            segment.duration()

        with pytest.raises(NotImplementedError):
            segment.file_path()

        with pytest.raises(NotImplementedError):
            segment._build()


class TestBufferSegment:
    def test_init_validates_duration_type(self):
        BufferSegment(1000)  # Should not raise

        with pytest.raises(ValueError, match="duration_ms must be an integer"):
            BufferSegment(1000.5)

        with pytest.raises(ValueError, match="duration_ms must be an integer"):
            BufferSegment("1000")

    def test_duration_conversion(self):
        segment = BufferSegment(1000)
        assert segment.duration() == 1.0

        segment = BufferSegment(500)
        assert segment.duration() == 0.5

    def test_file_path(self):
        segment = BufferSegment(1000)
        assert segment.file_path() == "build/silence-1000.mp3"

        segment = BufferSegment(2500)
        assert segment.file_path() == "build/silence-2500.mp3"

    def test_is_built(self):
        segment = BufferSegment(999999)  # Use unlikely duration to avoid existing file
        assert not segment.is_built()


class TestGeneratedSpeechSegment:
    def test_file_path_uses_text_hash(self):
        segment = GeneratedSpeechSegment("Hello, world!")
        expected_hash = (
            "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        )
        assert segment.file_path() == f"build/gtts/{expected_hash}.mp3"

    def test_different_text_different_paths(self):
        segment1 = GeneratedSpeechSegment("Hello")
        segment2 = GeneratedSpeechSegment("World")
        assert segment1.file_path() != segment2.file_path()

    def test_is_built(self):
        segment = GeneratedSpeechSegment("Test text")
        assert not segment.is_built()

    @mock.patch.object(GeneratedSpeechSegment, '_duration_from_file', return_value=2.5)
    @mock.patch.object(GeneratedSpeechSegment, 'build')
    def test_duration_returns_value(self, mock_build, mock_duration_from_file):
        segment = GeneratedSpeechSegment("Test text")
        result = segment.duration()
        assert result == 2.5
        mock_build.assert_called_once()
        mock_duration_from_file.assert_called_once()


class TestESVReadingSegment:
    def test_file_path_replaces_spaces(self):
        segment = ESVReadingSegment("Genesis 1")
        assert segment.file_path() == "build/esv_chapters/Genesis_1.mp3"

        segment = ESVReadingSegment("1 Corinthians 13")
        assert segment.file_path() == "build/esv_chapters/1_Corinthians_13.mp3"

    def test_is_built(self):
        segment = ESVReadingSegment("NonExistent 999")  # Use unlikely chapter name
        assert not segment.is_built()

    def test_build_missing_api_key(self):
        segment = ESVReadingSegment("Genesis 1")

        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="ESV_API_KEY environment variable is not set"
            ):
                segment._build()

    @mock.patch("requests.get")
    @mock.patch("os.getenv")
    @mock.patch("os.makedirs")
    def test_build_success(self, mock_makedirs, mock_getenv, mock_get):
        mock_getenv.return_value = "test-api-key"
        mock_response = mock.Mock()
        mock_response.content = b"fake audio data"
        mock_get.return_value = mock_response

        segment = ESVReadingSegment("Genesis 1")

        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            segment._build()

        mock_get.assert_called_once_with(
            "https://api.esv.org/v3/passage/audio/?q=Genesis+1",
            headers={"Authorization": "Token test-api-key"},
        )
        mock_file.assert_called_once_with(segment.file_path(), "wb")

    @mock.patch("requests.get")
    @mock.patch("os.getenv")
    @mock.patch("os.makedirs")
    def test_build_request_error(self, mock_makedirs, mock_getenv, mock_get):
        import requests

        mock_getenv.return_value = "test-api-key"
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        segment = ESVReadingSegment("Genesis 1")

        with pytest.raises(
            ESVReadingSegment.DownloadError,
            match="Failed to download audio for Genesis 1",
        ):
            segment._build()
