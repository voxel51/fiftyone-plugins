"""
Simple tests for VLM Run plugin operators.
These tests verify basic operator initialization and configuration.
"""

import pytest
import sys
import os

# Add parent directory to path to import the plugin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestVideoOperators:
    """Test video transcription operator."""

    def test_transcribe_video_init(self):
        """Test VLMRunTranscribeVideo operator initialization."""
        from __init__ import VLMRunTranscribeVideo

        operator = VLMRunTranscribeVideo()
        config = operator.config

        assert config.name == "vlmrun_transcribe_video"
        assert config.label == "VLM Run: Transcribe Video"
        assert config.dynamic is True
        assert operator is not None


class TestImageOperators:
    """Test image processing operators."""

    def test_classify_images_init(self):
        """Test VLMRunClassifyImages operator initialization."""
        from __init__ import VLMRunClassifyImages

        operator = VLMRunClassifyImages()
        config = operator.config

        assert config.name == "vlmrun_classify_images"
        assert config.label == "VLM Run: Classify Images"
        assert operator is not None

    def test_caption_images_init(self):
        """Test VLMRunCaptionImages operator initialization."""
        from __init__ import VLMRunCaptionImages

        operator = VLMRunCaptionImages()
        config = operator.config

        assert config.name == "vlmrun_caption_images"
        assert config.label == "VLM Run: Caption Images"
        assert operator is not None

    def test_object_detection_init(self):
        """Test VLMRunObjectDetection operator initialization."""
        from __init__ import VLMRunObjectDetection

        operator = VLMRunObjectDetection()
        config = operator.config

        assert config.name == "vlmrun_object_detection"
        assert config.label == "VLM Run: Object Detection"
        assert operator is not None

    def test_person_detection_init(self):
        """Test VLMRunPersonDetection operator initialization."""
        from __init__ import VLMRunPersonDetection

        operator = VLMRunPersonDetection()
        config = operator.config

        assert config.name == "vlmrun_person_detection"
        assert config.label == "VLM Run: Person Detection"
        assert operator is not None


class TestDocumentOperators:
    """Test document processing operators."""

    def test_classify_documents_init(self):
        """Test VLMRunClassifyDocuments operator initialization."""
        from __init__ import VLMRunClassifyDocuments

        operator = VLMRunClassifyDocuments()
        config = operator.config

        assert config.name == "vlmrun_classify_documents"
        assert config.label == "VLM Run: Classify Documents"
        assert operator is not None

    def test_parse_invoices_init(self):
        """Test VLMRunParseInvoices operator initialization."""
        from __init__ import VLMRunParseInvoices

        operator = VLMRunParseInvoices()
        config = operator.config

        assert config.name == "vlmrun_parse_invoices"
        assert config.label == "VLM Run: Parse Invoices"
        assert operator is not None

    def test_layout_detection_init(self):
        """Test VLMRunLayoutDetection operator initialization."""
        from __init__ import VLMRunLayoutDetection

        operator = VLMRunLayoutDetection()
        config = operator.config

        assert config.name == "vlmrun_layout_detection"
        assert config.label == "VLM Run: Document Layout Detection"
        assert operator is not None


class TestOperatorRegistry:
    """Test that all operators are properly registered."""

    def test_all_operators_imported(self):
        """Test that all operators can be imported."""
        from __init__ import (
            VLMRunTranscribeVideo,
            VLMRunClassifyImages,
            VLMRunCaptionImages,
            VLMRunObjectDetection,
            VLMRunPersonDetection,
            VLMRunClassifyDocuments,
            VLMRunParseInvoices,
            VLMRunLayoutDetection
        )

        # Verify all 8 operators are importable
        operators = [
            VLMRunTranscribeVideo,
            VLMRunClassifyImages,
            VLMRunCaptionImages,
            VLMRunObjectDetection,
            VLMRunPersonDetection,
            VLMRunClassifyDocuments,
            VLMRunParseInvoices,
            VLMRunLayoutDetection
        ]

        assert len(operators) == 8

        for op_class in operators:
            operator = op_class()
            assert operator is not None
            assert hasattr(operator, 'config')
            assert hasattr(operator, 'execute')