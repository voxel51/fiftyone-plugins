"""
VLM Run FiftyOne Plugin.

Integration plugin for VLM Run (vlm.run) with FiftyOne.
"""
# pylint: disable=no-member,no-name-in-module

import os
import os.path
import time
from pathlib import Path

import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone.core.utils as fou
import fiftyone.core.labels as fol
from vlmrun.client.types import GenerationConfig

# Configuration constants
DEFAULT_API_URL = "https://api.vlm.run/v1"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 5
DEFAULT_MAX_WAIT = 600  # 10 minutes
DEFAULT_POLL_INTERVAL = 5  # seconds
MAX_ERROR_DETAILS = 5

# Supported file extensions
VIDEO_EXTENSIONS = (
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".m4v",
)

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
    ".webp",
)

DOCUMENT_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
)

class VLMRunTranscribeVideo(foo.Operator):
    """Transcribe video content with temporal grounding using VLM Run."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_transcribe_video",
            label="VLM Run: Transcribe Video",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )


        inputs.str(
            "audio_field",
            label="Audio Field",
            description="Field name to store audio content (speech transcription)",
            default="audio_transcription",
            required=True,
        )

        inputs.str(
            "video_field",
            label="Video Field",
            description="Field name to store video content (visual descriptions)",
            default="video_transcription",
            required=True,
        )

        return types.Property(
            inputs, view=types.View(label="Transcribe Video")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}
        target = ctx.params.get("target", "DATASET")
        audio_field = ctx.params["audio_field"]
        video_field = ctx.params["video_field"]
        domain = "video.transcription"  # Fixed domain for this operator

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset

        # Use all samples (we'll check for video during processing)
        video_samples = sample_collection
        total_videos = len(video_samples)

        if total_videos == 0:
            return {
                "error": "No video samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
        except ImportError as e:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration from environment or use defaults
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        with fou.ProgressBar(total=total_videos) as pb:
            for sample in video_samples:
                try:
                    # Skip non-video files
                    if not sample.filepath.lower().endswith(VIDEO_EXTENSIONS):
                        pb.update()
                        continue

                    # Process video with VLM Run
                    file_path = Path(sample.filepath)
                    response = client.video.generate(
                        file=file_path,
                        domain=domain,
                        batch=True,
                    )

                    # Poll for batch completion
                    if hasattr(response, "id") and hasattr(response, "status"):
                        prediction_id = response.id
                        max_wait = int(
                            os.getenv("VLMRUN_MAX_WAIT", str(DEFAULT_MAX_WAIT))
                        )
                        poll_interval = int(
                            os.getenv(
                                "VLMRUN_POLL_INTERVAL",
                                str(DEFAULT_POLL_INTERVAL),
                            )
                        )
                        elapsed = 0

                        while elapsed < max_wait:
                            pred_response = client.predictions.get(
                                id=prediction_id
                            )

                            if pred_response.status == "completed":
                                result = (
                                    pred_response.result
                                    if hasattr(pred_response, "result")
                                    else pred_response
                                )
                                break
                            elif pred_response.status == "failed":
                                raise RuntimeError(
                                    f"Video prediction failed: {pred_response.error if hasattr(pred_response, 'error') else 'Unknown error'}"
                                )

                            time.sleep(poll_interval)
                            elapsed += poll_interval
                        else:
                            raise TimeoutError(
                                f"Video prediction timed out after {max_wait} seconds"
                            )

                    else:
                        result = response

                    # Parse the result
                    self._process_transcription_result(
                        sample,
                        result,
                        audio_field,
                        video_field,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_videos,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_transcription_result(
        self,
        sample,
        result,
        audio_field,
        video_field,
    ):
        """Process VLM Run transcription result and update sample."""

        # Extract transcription text
        if hasattr(result, "response"):
            response_data = result.response
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        # Store audio and video transcriptions separately
        if isinstance(response_data, dict):
            # VLM Run video.transcription returns segments with audio.content and video.content
            if "segments" in response_data:
                # Store full segments with timestamps for detailed analysis
                segments_data = []

                # Also combine text for quick access
                audio_transcripts = []
                video_descriptions = []

                for segment in response_data["segments"]:
                    if isinstance(segment, dict):
                        segment_info = {}

                        # Capture timestamps
                        if "start_time" in segment:
                            segment_info["start_time"] = segment["start_time"]
                        if "end_time" in segment:
                            segment_info["end_time"] = segment["end_time"]

                        # Get audio content
                        if "audio" in segment and isinstance(segment["audio"], dict):
                            audio_content = segment["audio"].get("content", "")
                            segment_info["audio"] = audio_content
                            if audio_content:
                                audio_transcripts.append(audio_content)

                        # Get video content
                        if "video" in segment and isinstance(segment["video"], dict):
                            video_content = segment["video"].get("content", "")
                            segment_info["video"] = video_content
                            if video_content:
                                video_descriptions.append(video_content)

                        if segment_info:
                            segments_data.append(segment_info)

                # Save combined text fields
                audio_text = " ".join(audio_transcripts)
                video_text = " ".join(video_descriptions)

                if audio_text:
                    sample[audio_field] = audio_text
                if video_text:
                    sample[video_field] = video_text

                # Save full segments data with timestamps
                if segments_data:
                    sample[f"{video_field}_segments"] = segments_data

            # Store metadata if present
            if "metadata" in response_data and isinstance(response_data["metadata"], dict):
                metadata = response_data["metadata"]
                if "duration" in metadata and metadata["duration"] is not None:
                    sample[f"{video_field}_duration"] = metadata["duration"]
                if "topics" in metadata and metadata["topics"] is not None:
                    sample[f"{video_field}_topics"] = metadata["topics"]
                if "content" in metadata and metadata["content"] is not None:
                    sample[f"{video_field}_summary"] = metadata["content"]

        elif isinstance(response_data, str):
            sample[audio_field] = response_data
        else:
            sample[audio_field] = str(response_data)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Videos Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Videos")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully transcribed {ctx.results.get('processed')} video(s). Check the '{ctx.params.get('audio_field', 'audio_transcription')}' and '{ctx.params.get('video_field', 'video_transcription')}' fields in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Transcription Results")
        )

class VLMRunClassifyImages(foo.Operator):
    """Classify images using VLM Run to generate tags with confidence scores."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_classify_images",
            label="VLM Run: Classify Images",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for classification
        default_field = "image_classification"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store classification results",
            default=default_field,
            required=True,
        )

        inputs.bool(
            "populate_builtin_tags",
            label="Populate Built-in Tags",
            description="Also add classification results to the sample's built-in 'tags' field for easier filtering",
            default=False,
            required=False,
        )

        return types.Property(
            inputs, view=types.View(label="Classify Images")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        populate_builtin_tags = ctx.params.get("populate_builtin_tags", False)
        domain = "image.classification"  # Fixed domain for this operator

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset

        # Filter for image samples
        image_samples = sample_collection
        total_images = len(image_samples)

        if total_images == 0:
            return {
                "error": "No image samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration from environment or use defaults
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        with fou.ProgressBar(total=total_images) as pb:
            for sample in image_samples:
                try:
                    # Skip non-image files
                    if not sample.filepath.lower().endswith(IMAGE_EXTENSIONS):
                        pb.update()
                        continue

                    # Process image with VLM Run
                    file_path = Path(sample.filepath)

                    response = client.image.generate(
                        images=[file_path],
                        domain=domain,
                    )

                    # Parse and store the result
                    self._process_image_result(
                        sample,
                        response,
                        result_field,
                        domain,
                        populate_builtin_tags=populate_builtin_tags,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_images,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_image_result(self, sample, result, result_field, domain, populate_builtin_tags=False):
        """Process VLM Run image result and update sample."""

        # Extract response data - handle nested response structure
        if hasattr(result, "response"):
            response_data = result.response
            # If response is a Pydantic model, convert to dict
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        # Store results based on domain
        if domain == "image.classification":
            if isinstance(response_data, dict):
                # Store classification results based on actual VLM Run response structure
                if "tags" in response_data:
                    # Store tags as the main classification result
                    sample[result_field] = response_data["tags"]

                    # Optionally populate the built-in tags field
                    if populate_builtin_tags:
                        if hasattr(sample, 'tags'):
                            # Append to existing tags
                            existing_tags = sample.tags if sample.tags else []
                            sample.tags = list(set(existing_tags + response_data["tags"]))
                        else:
                            sample.tags = response_data["tags"]

                if "confidence" in response_data:
                    sample[f"{result_field}_confidence"] = response_data["confidence"]

                if "rationale" in response_data:
                    sample[f"{result_field}_rationale"] = response_data["rationale"]
            else:
                sample[result_field] = str(response_data)

        elif domain == "image.caption":
            if isinstance(response_data, dict):
                # Store caption as main result
                if "caption" in response_data:
                    sample[result_field] = response_data["caption"]
                elif "description" in response_data:
                    sample[result_field] = response_data["description"]

                # Store tags if present
                if "tags" in response_data:
                    sample[f"{result_field}_tags"] = response_data["tags"]
            else:
                sample[result_field] = str(response_data)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Images Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Images")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully processed {ctx.results.get('processed')} image(s). Check the '{ctx.params.get('result_field', 'vlmrun_image')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Classification Results")
        )

class VLMRunCaptionImages(foo.Operator):
    """Generate descriptive captions for images using VLM Run."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_caption_images",
            label="VLM Run: Caption Images",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for captions
        default_field = "image_caption"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store image captions",
            default=default_field,
            required=True,
        )

        inputs.bool(
            "populate_builtin_tags",
            label="Populate Built-in Tags",
            description="If the caption includes tags, also add them to the sample's built-in 'tags' field for easier filtering",
            default=False,
            required=False,
        )

        return types.Property(
            inputs, view=types.View(label="Caption Images")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        populate_builtin_tags = ctx.params.get("populate_builtin_tags", False)
        domain = "image.caption"  # Fixed domain for this operator

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset

        # Filter for image samples
        image_samples = sample_collection
        total_images = len(image_samples)

        if total_images == 0:
            return {
                "error": "No image samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration from environment or use defaults
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        with fou.ProgressBar(total=total_images) as pb:
            for sample in image_samples:
                try:
                    # Skip non-image files
                    if not sample.filepath.lower().endswith(IMAGE_EXTENSIONS):
                        pb.update()
                        continue

                    # Process image with VLM Run
                    file_path = Path(sample.filepath)

                    response = client.image.generate(
                        images=[file_path],
                        domain=domain,
                    )

                    # Parse and store the result
                    self._process_image_result(
                        sample,
                        response,
                        result_field,
                        domain,
                        populate_builtin_tags=populate_builtin_tags,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_images,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_image_result(self, sample, result, result_field, domain, populate_builtin_tags=False):
        """Process VLM Run image result and update sample."""

        # Extract response data - handle nested response structure
        if hasattr(result, "response"):
            response_data = result.response
            # If response is a Pydantic model, convert to dict
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        # Store caption results
        if isinstance(response_data, dict):
            # Store caption as main result
            if "caption" in response_data:
                sample[result_field] = response_data["caption"]
            elif "description" in response_data:
                sample[result_field] = response_data["description"]

            # Store tags if present
            if "tags" in response_data:
                sample[f"{result_field}_tags"] = response_data["tags"]

                # Optionally populate the built-in tags field
                if populate_builtin_tags:
                    if hasattr(sample, 'tags'):
                        # Append to existing tags
                        existing_tags = sample.tags if sample.tags else []
                        sample.tags = list(set(existing_tags + response_data["tags"]))
                    else:
                        sample.tags = response_data["tags"]
        else:
            sample[result_field] = str(response_data)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Images Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Images")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully captioned {ctx.results.get('processed')} image(s). Check the '{ctx.params.get('result_field', 'image_caption')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Captioning Results")
        )

class VLMRunClassifyDocuments(foo.Operator):
    """Classify documents using VLM Run to determine document type."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_classify_documents",
            label="VLM Run: Classify Documents",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for classification
        default_field = "document_classification"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store extraction results",
            default=default_field,
            required=True,
        )

        inputs.bool(
            "populate_builtin_tags",
            label="Populate Built-in Tags",
            description="Also add classification results to the sample's built-in 'tags' field for easier filtering",
            default=False,
            required=False,
        )

        return types.Property(
            inputs, view=types.View(label="Classify Documents")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        populate_builtin_tags = ctx.params.get("populate_builtin_tags", False)
        domain = "document.classification"  # Fixed domain for this operator
        enable_grounding = False  # Classification doesn't need grounding
        detections_field = None

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset

        # Filter for document samples
        document_samples = sample_collection
        total_documents = len(document_samples)

        if total_documents == 0:
            return {
                "error": "No document samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration from environment or use defaults
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Create config for grounding if enabled
        config = None
        if enable_grounding:
            config = GenerationConfig(grounding=True)

        processed = 0
        errors = []
        grounding_info = []  # Collect grounding information

        with fou.ProgressBar(total=total_documents) as pb:
            for sample in document_samples:
                try:
                    # Skip non-document files
                    if not sample.filepath.lower().endswith(DOCUMENT_EXTENSIONS):
                        pb.update()
                        continue

                    # Process document with VLM Run
                    file_path = Path(sample.filepath)

                    # Use batch mode for documents as they may take longer
                    generate_kwargs = {
                        "file": file_path,
                        "domain": domain,
                        "batch": True,
                    }
                    if enable_grounding and config:
                        generate_kwargs["config"] = config

                    response = client.document.generate(**generate_kwargs)

                    # Poll for batch completion
                    if hasattr(response, "id") and hasattr(response, "status"):
                        prediction_id = response.id
                        max_wait = int(
                            os.getenv("VLMRUN_MAX_WAIT", str(DEFAULT_MAX_WAIT))
                        )
                        poll_interval = int(
                            os.getenv(
                                "VLMRUN_POLL_INTERVAL",
                                str(DEFAULT_POLL_INTERVAL),
                            )
                        )
                        elapsed = 0

                        while elapsed < max_wait:
                            pred_response = client.predictions.get(
                                id=prediction_id
                            )

                            if pred_response.status == "completed":
                                result = (
                                    pred_response.result
                                    if hasattr(pred_response, "result")
                                    else pred_response
                                )
                                break
                            elif pred_response.status == "failed":
                                raise RuntimeError(
                                    f"Document prediction failed: {pred_response.error if hasattr(pred_response, 'error') else 'Unknown error'}"
                                )

                            time.sleep(poll_interval)
                            elapsed += poll_interval
                        else:
                            raise TimeoutError(
                                f"Document prediction timed out after {max_wait} seconds"
                            )

                    else:
                        result = response

                    # Parse and store the result
                    sample_grounding_info = self._process_document_result(
                        sample,
                        result,
                        result_field,
                        domain,
                        enable_grounding,
                        detections_field,
                        populate_builtin_tags=populate_builtin_tags,
                    )

                    if sample_grounding_info and enable_grounding:
                        grounding_info.append({
                            "file": os.path.basename(sample.filepath),
                            **sample_grounding_info
                        })

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_documents,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        if enable_grounding and grounding_info:
            # Format the raw responses for display
            raw_responses = []
            for item in grounding_info[:20]:  # Limit to 20
                if "raw_response" in item:
                    raw_responses.append(f"File: {item.get('file', 'unknown')}\n{item['raw_response']}")

            if raw_responses:
                result["grounding_raw_data"] = raw_responses
            result["total_grounding_items"] = len(grounding_info)

        return result

    def _process_document_result(self, sample, result, result_field, domain, enable_grounding=False, detections_field=None, populate_builtin_tags=False):
        """Process VLM Run document result and update sample. Returns grounding info if enabled."""
        grounding_info = {}

        # Extract response data - handle nested response structure
        if hasattr(result, "response"):
            response_data = result.response
            # If response is a Pydantic model, convert to dict
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        # Store results based on domain
        if domain == "document.classification":
            if isinstance(response_data, dict):
                # Document classification returns tags, confidence, and rationale (like image classification)
                if "tags" in response_data:
                    sample[result_field] = response_data["tags"]

                    # Optionally populate the built-in tags field
                    if populate_builtin_tags:
                        if hasattr(sample, 'tags'):
                            # Append to existing tags
                            existing_tags = sample.tags if sample.tags else []
                            sample.tags = list(set(existing_tags + response_data["tags"]))
                        else:
                            sample.tags = response_data["tags"]

                if "confidence" in response_data:
                    sample[f"{result_field}_confidence"] = response_data["confidence"]
                if "rationale" in response_data:
                    sample[f"{result_field}_rationale"] = response_data["rationale"]

                # Handle grounding if enabled
                if enable_grounding and detections_field:
                    detections_list = []

                    # Store raw response for grounding display
                    grounding_info["raw_response"] = str(response_data)

                    # Check for any field ending with _metadata (VLM Run convention)
                    for field_name, field_value in response_data.items():
                        if field_name.endswith("_metadata") and isinstance(field_value, dict):
                            # Extract the base field name (remove _metadata suffix)
                            label = field_name.replace("_metadata", "")
                            self._add_detection_from_metadata(detections_list, label, field_value)

                    if detections_list:
                        sample[detections_field] = fol.Detections(detections=detections_list)
            else:
                sample[result_field] = str(response_data)

        elif domain == "document.invoice":
            if isinstance(response_data, dict):
                # Store key invoice fields based on actual response
                if "invoice_id" in response_data:
                    sample[f"{result_field}_id"] = response_data["invoice_id"]
                if "issuer" in response_data:
                    sample[f"{result_field}_issuer"] = response_data["issuer"]
                if "customer" in response_data:
                    sample[f"{result_field}_customer"] = response_data["customer"]
                if "invoice_issue_date" in response_data:
                    sample[f"{result_field}_date"] = response_data["invoice_issue_date"]
                if "total" in response_data:
                    sample[f"{result_field}_total"] = response_data["total"]
                if "currency" in response_data:
                    sample[f"{result_field}_currency"] = response_data["currency"]
                if "items" in response_data:
                    sample[f"{result_field}_items"] = response_data["items"]

                # Store full response for reference
                sample[result_field] = response_data
            else:
                sample[result_field] = str(response_data)

        return grounding_info if enable_grounding else None

    def _add_detection_from_metadata(self, detections_list, label, metadata):
        """Convert VLM Run grounding metadata to FiftyOne Detection."""
        if not metadata or not isinstance(metadata, dict):
            return

        if "bboxes" in metadata:
            # Convert confidence string to numeric
            confidence_str = metadata.get("confidence", "med")
            if confidence_str == "hi":
                confidence = 0.9
            elif confidence_str == "med":
                confidence = 0.7
            else:  # "low"
                confidence = 0.5

            # Process each bounding box
            for bbox_info in metadata["bboxes"]:
                # Check for bbox in nested structure
                bbox_data = None
                if "bbox" in bbox_info and "xywh" in bbox_info["bbox"]:
                    bbox_data = bbox_info["bbox"]["xywh"]
                elif "xywh" in bbox_info:
                    bbox_data = bbox_info["xywh"]

                if bbox_data:
                    # VLM Run format is already [x, y, w, h] normalized
                    detection = fol.Detection(
                        label=label,
                        bounding_box=bbox_data,
                        confidence=confidence,
                    )
                    # Add page info if available
                    if "page" in bbox_info:
                        detection["page"] = bbox_info["page"]

                    detections_list.append(detection)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Documents Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Documents")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Show grounding information if available
        if "grounding_raw_data" in ctx.results:
            outputs.list(
                "grounding_raw_data",
                types.String(),
                label="Raw Grounding Responses",
                description="Raw response data from VLM Run API"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully processed {ctx.results.get('processed')} document(s). Check the '{ctx.params.get('result_field', 'document_data')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Classification Results")
        )

class VLMRunParseInvoices(foo.Operator):
    """Extract structured data from invoices using VLM Run."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_parse_invoices",
            label="VLM Run: Parse Invoices",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for invoice parsing
        default_field = "invoice_data"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store invoice data",
            default=default_field,
            required=True,
        )

        # Grounding option
        inputs.bool(
            "enable_grounding",
            label="Enable Visual Grounding",
            description="Extract bounding boxes for detected invoice fields",
            default=True,
            required=False,
        )

        inputs.str(
            "detections_field",
            label="Detections Field",
            description="Field name to store bounding box detections (if grounding enabled)",
            default="invoice_detections",
            required=False,
        )

        return types.Property(
            inputs, view=types.View(label="Parse Invoices")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        enable_grounding = ctx.params.get("enable_grounding", True)
        detections_field = ctx.params.get("detections_field", "invoice_detections")
        domain = "document.invoice"  # Fixed domain for this operator

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset

        # Filter for document samples
        document_samples = sample_collection
        total_documents = len(document_samples)

        if total_documents == 0:
            return {
                "error": "No document samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration from environment or use defaults
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Create config for grounding if enabled
        config = None
        if enable_grounding:
            config = GenerationConfig(grounding=True)

        processed = 0
        errors = []
        grounding_info = []  # Collect grounding information

        with fou.ProgressBar(total=total_documents) as pb:
            for sample in document_samples:
                try:
                    # Skip non-document files
                    if not sample.filepath.lower().endswith(DOCUMENT_EXTENSIONS):
                        pb.update()
                        continue

                    # Process document with VLM Run
                    file_path = Path(sample.filepath)

                    # Use batch mode for documents as they may take longer
                    generate_kwargs = {
                        "file": file_path,
                        "domain": domain,
                        "batch": True,
                    }
                    if enable_grounding and config:
                        generate_kwargs["config"] = config

                    response = client.document.generate(**generate_kwargs)

                    # Poll for batch completion
                    if hasattr(response, "id") and hasattr(response, "status"):
                        prediction_id = response.id
                        max_wait = int(
                            os.getenv("VLMRUN_MAX_WAIT", str(DEFAULT_MAX_WAIT))
                        )
                        poll_interval = int(
                            os.getenv(
                                "VLMRUN_POLL_INTERVAL",
                                str(DEFAULT_POLL_INTERVAL),
                            )
                        )
                        elapsed = 0

                        while elapsed < max_wait:
                            pred_response = client.predictions.get(
                                id=prediction_id
                            )

                            if pred_response.status == "completed":
                                result = (
                                    pred_response.result
                                    if hasattr(pred_response, "result")
                                    else pred_response
                                )
                                break
                            elif pred_response.status == "failed":
                                raise RuntimeError(
                                    f"Document prediction failed: {pred_response.error if hasattr(pred_response, 'error') else 'Unknown error'}"
                                )

                            time.sleep(poll_interval)
                            elapsed += poll_interval
                        else:
                            raise TimeoutError(
                                f"Document prediction timed out after {max_wait} seconds"
                            )

                    else:
                        result = response

                    # Parse and store the result
                    sample_grounding_info = self._process_invoice_result(
                        sample,
                        result,
                        result_field,
                        enable_grounding,
                        detections_field,
                    )

                    if sample_grounding_info and enable_grounding:
                        grounding_info.append({
                            "file": os.path.basename(sample.filepath),
                            **sample_grounding_info
                        })

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_documents,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        if enable_grounding and grounding_info:
            # Format the raw responses for display
            raw_responses = []
            for item in grounding_info[:20]:  # Limit to 20
                if "raw_response" in item:
                    raw_responses.append(f"File: {item.get('file', 'unknown')}\n{item['raw_response']}")

            if raw_responses:
                result["grounding_raw_data"] = raw_responses
            result["total_grounding_items"] = len(grounding_info)

        return result

    def _process_invoice_result(self, sample, result, result_field, enable_grounding=False, detections_field=None):
        """Process VLM Run invoice result and update sample. Returns grounding info if enabled."""
        grounding_info = {}

        # Extract response data - handle nested response structure
        if hasattr(result, "response"):
            response_data = result.response
            # If response is a Pydantic model, convert to dict
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        # Store invoice results
        if isinstance(response_data, dict):
            # Store raw response for grounding display
            if enable_grounding:
                grounding_info["raw_response"] = str(response_data)

            # Collect detections if grounding is enabled
            detections = []

            # Store key invoice fields based on actual response
            if "invoice_id" in response_data:
                sample[f"{result_field}_id"] = response_data["invoice_id"]
                # Check for grounding metadata
                if enable_grounding and "invoice_id_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "invoice_id", response_data["invoice_id_metadata"]
                    )

            if "issuer" in response_data:
                sample[f"{result_field}_issuer"] = response_data["issuer"]
                if enable_grounding and "issuer_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "issuer", response_data["issuer_metadata"]
                    )

            if "customer" in response_data:
                sample[f"{result_field}_customer"] = response_data["customer"]
                if enable_grounding and "customer_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "customer", response_data["customer_metadata"]
                    )

            if "invoice_issue_date" in response_data:
                sample[f"{result_field}_date"] = response_data["invoice_issue_date"]
                if enable_grounding and "invoice_issue_date_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "invoice_date", response_data["invoice_issue_date_metadata"]
                    )

            if "total" in response_data:
                sample[f"{result_field}_total"] = response_data["total"]
                if enable_grounding and "total_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "total", response_data["total_metadata"]
                    )

            if "currency" in response_data:
                sample[f"{result_field}_currency"] = response_data["currency"]
                if enable_grounding and "currency_metadata" in response_data:
                    self._add_detection_from_metadata(
                        detections, "currency", response_data["currency_metadata"]
                    )

            if "items" in response_data:
                sample[f"{result_field}_items"] = response_data["items"]
                # Items might have their own metadata

            # Store detections if grounding is enabled and we have detections
            if enable_grounding and detections and detections_field:
                sample[detections_field] = fol.Detections(detections=detections)

            # Store full response for reference
            sample[result_field] = response_data
        else:
            sample[result_field] = str(response_data)

        return grounding_info if enable_grounding else None

    def _add_detection_from_metadata(self, detections_list, label, metadata):
        """Convert VLM Run grounding metadata to FiftyOne Detection."""
        if not metadata or not isinstance(metadata, dict):
            return

        if "bboxes" in metadata:
            # Convert confidence string to numeric
            confidence_str = metadata.get("confidence", "med")
            if confidence_str == "hi":
                confidence = 0.9
            elif confidence_str == "med":
                confidence = 0.7
            else:  # "low"
                confidence = 0.5

            # Process each bounding box
            for bbox_info in metadata["bboxes"]:
                # Check for bbox in nested structure
                bbox_data = None
                if "bbox" in bbox_info and "xywh" in bbox_info["bbox"]:
                    bbox_data = bbox_info["bbox"]["xywh"]
                elif "xywh" in bbox_info:
                    bbox_data = bbox_info["xywh"]

                if bbox_data:
                    # VLM Run format is already [x, y, w, h] normalized
                    detection = fol.Detection(
                        label=label,
                        bounding_box=bbox_data,
                        confidence=confidence,
                    )
                    # Add page info if available
                    if "page" in bbox_info:
                        detection["page"] = bbox_info["page"]

                    detections_list.append(detection)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Invoices Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Documents")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Show grounding information if available
        if "grounding_raw_data" in ctx.results:
            outputs.list(
                "grounding_raw_data",
                types.String(),
                label="Raw Grounding Responses",
                description="Raw response data from VLM Run API"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully parsed {ctx.results.get('processed')} invoice(s). Check the '{ctx.params.get('result_field', 'invoice_data')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Invoice Parsing Results")
        )

class VLMRunObjectDetection(foo.Operator):
    """Detect objects in images using VLM Run's object detection."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_object_detection",
            label="VLM Run: Object Detection",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for object detection
        default_field = "object_detections"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store detected objects",
            default=default_field,
            required=True,
        )

        return types.Property(
            inputs, view=types.View(label="Object Detection")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        domain = "image.object-detection"  # Fixed domain

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset
        image_samples = sample_collection
        total_images = len(image_samples)

        if total_images == 0:
            return {
                "error": "No image samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
            from vlmrun.client.types import GenerationConfig
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        # Create config with grounding enabled
        config = GenerationConfig(grounding=True)

        with fou.ProgressBar(total=total_images) as pb:
            for sample in image_samples:
                try:
                    # Skip non-image files
                    if not sample.filepath.lower().endswith(IMAGE_EXTENSIONS):
                        pb.update()
                        continue

                    # Process image with VLM Run
                    file_path = Path(sample.filepath)

                    response = client.image.generate(
                        images=[file_path],
                        domain=domain,
                        config=config,
                    )

                    # Parse and store the result
                    self._process_detection_result(
                        sample,
                        response,
                        result_field,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_images,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_detection_result(self, sample, result, result_field):
        """Process VLM Run object detection result and update sample."""

        # Extract response data
        if hasattr(result, "response"):
            response_data = result.response
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        if isinstance(response_data, dict):
            detections = []

            # Store the content description
            if "content" in response_data:
                sample[f"{result_field}_description"] = response_data["content"]

            # Process detected objects - they come as metadata fields
            for key, value in response_data.items():
                if key.endswith("_metadata") and isinstance(value, dict):
                    # Extract object label from the key
                    label = key.replace("_metadata", "").replace("_page0", "")

                    if "bboxes" in value:
                        for bbox_info in value["bboxes"]:
                            if "bbox" in bbox_info and "xywh" in bbox_info["bbox"]:
                                bbox_data = bbox_info["bbox"]["xywh"]

                                # Convert confidence to numeric
                                confidence_str = value.get("confidence", "med")
                                if confidence_str == "hi":
                                    confidence = 0.9
                                elif confidence_str == "med":
                                    confidence = 0.7
                                else:
                                    confidence = 0.5

                                detection = fol.Detection(
                                    label=label,
                                    bounding_box=bbox_data,
                                    confidence=confidence,
                                )
                                detections.append(detection)

            if detections:
                sample[result_field] = fol.Detections(detections=detections)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Images Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Images")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully detected objects in {ctx.results.get('processed')} image(s). Check the '{ctx.params.get('result_field', 'object_detections')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Object Detection Results")
        )

class VLMRunPersonDetection(foo.Operator):
    """Detect persons in images using VLM Run's person detection."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_person_detection",
            label="VLM Run: Person Detection",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for person detection
        default_field = "person_detections"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store detected persons",
            default=default_field,
            required=True,
        )

        return types.Property(
            inputs, view=types.View(label="Person Detection")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        domain = "image.person-detection"  # Fixed domain

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset
        image_samples = sample_collection
        total_images = len(image_samples)

        if total_images == 0:
            return {
                "error": "No image samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
            from vlmrun.client.types import GenerationConfig
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        # Create config with grounding enabled
        config = GenerationConfig(grounding=True)

        with fou.ProgressBar(total=total_images) as pb:
            for sample in image_samples:
                try:
                    # Skip non-image files
                    if not sample.filepath.lower().endswith(IMAGE_EXTENSIONS):
                        pb.update()
                        continue

                    # Process image with VLM Run
                    file_path = Path(sample.filepath)

                    response = client.image.generate(
                        images=[file_path],
                        domain=domain,
                        config=config,
                    )

                    # Parse and store the result
                    self._process_person_result(
                        sample,
                        response,
                        result_field,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_images,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_person_result(self, sample, result, result_field):
        """Process VLM Run person detection result and update sample."""

        # Extract response data
        if hasattr(result, "response"):
            response_data = result.response
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        if isinstance(response_data, dict):
            # Store the content description
            if "content" in response_data:
                sample[f"{result_field}_description"] = response_data["content"]

            detections = []

            # Person detection returns fields like "person-1_page0_metadata" with bboxes
            for key, value in response_data.items():
                if key.endswith("_metadata") and "person" in key:
                    if isinstance(value, dict) and "bboxes" in value:
                        # Extract confidence from metadata
                        confidence_str = value.get("confidence", "med")
                        if confidence_str == "hi":
                            confidence = 0.9
                        elif confidence_str == "med":
                            confidence = 0.7
                        else:
                            confidence = 0.5

                        for bbox_info in value["bboxes"]:
                            if isinstance(bbox_info, dict):
                                # Extract bbox coordinates
                                bbox_data = None
                                if "bbox" in bbox_info and "xywh" in bbox_info["bbox"]:
                                    bbox_data = bbox_info["bbox"]["xywh"]
                                elif "xywh" in bbox_info:
                                    bbox_data = bbox_info["xywh"]

                                if bbox_data:
                                    detection = fol.Detection(
                                        label=bbox_info.get("content", "person"),
                                        bounding_box=bbox_data,
                                        confidence=confidence,
                                    )
                                    detections.append(detection)

            if detections:
                sample[result_field] = fol.Detections(detections=detections)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Images Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Images")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully detected persons in {ctx.results.get('processed')} image(s). Check the '{ctx.params.get('result_field', 'person_detections')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Person Detection Results")
        )

class VLMRunLayoutDetection(foo.Operator):
    """Detect document layout elements using VLM Run."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="vlmrun_layout_detection",
            label="VLM Run: Document Layout Detection",
            dynamic=True,
            allow_immediate_execution=True,
            allow_delegated_execution=False,
        )

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Check for API key
        api_key = ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )
        if not api_key:
            inputs.str(
                "api_key",
                label="VLM Run API Key",
                description="Your VLM Run API key",
                required=True,
            )

        # Target selection
        has_view = ctx.dataset is not None and ctx.view != ctx.dataset.view()
        if has_view:
            target_choices = types.RadioGroup()
            target_choices.add_choice("DATASET", label="Entire dataset")
            target_choices.add_choice("VIEW", label="Current view")
            inputs.enum(
                "target",
                target_choices.values(),
                default="VIEW",
                label="Process",
                view=target_choices,
            )

        # Fixed field name for layout detection
        default_field = "layout_detections"

        inputs.str(
            "result_field",
            label="Result Field",
            description="Field name to store detected layout elements",
            default=default_field,
            required=True,
        )

        return types.Property(
            inputs, view=types.View(label="Layout Detection")
        )

    def execute(self, ctx):
        # Get parameters
        api_key = ctx.params.get("api_key") or ctx.secrets.get(
            "VLMRUN_API_KEY", os.getenv("VLMRUN_API_KEY")
        )

        if not api_key:
            return {"error": "VLM Run API key is required"}

        target = ctx.params.get("target", "DATASET")
        result_field = ctx.params["result_field"]
        domain = "document.layout-detection"  # Fixed domain

        # Get samples
        sample_collection = ctx.view if target == "VIEW" else ctx.dataset
        document_samples = sample_collection
        total_documents = len(document_samples)

        if total_documents == 0:
            return {
                "error": "No document samples found in the selected collection"
            }

        # Initialize VLM Run client
        try:
            from vlmrun.client import VLMRun
            from vlmrun.client.types import GenerationConfig
        except ImportError:
            return {
                "error": "VLMRun package not installed. Run: fiftyone plugins requirements @voxel51/vlmrun --install"
            }

        # Get configuration
        api_url = os.getenv("VLMRUN_API_URL", DEFAULT_API_URL)
        timeout = float(os.getenv("VLMRUN_TIMEOUT", str(DEFAULT_TIMEOUT)))
        max_retries = int(
            os.getenv("VLMRUN_MAX_RETRIES", str(DEFAULT_MAX_RETRIES))
        )

        client = VLMRun(
            api_key=api_key,
            base_url=api_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        processed = 0
        errors = []

        # Create config with grounding enabled
        config = GenerationConfig(grounding=True)

        with fou.ProgressBar(total=total_documents) as pb:
            for sample in document_samples:
                try:
                    # Process document with VLM Run
                    file_path = Path(sample.filepath)

                    # Use batch mode for documents
                    response = client.document.generate(
                        file=file_path,
                        domain=domain,
                        config=config,
                        batch=True,
                    )

                    # Poll for batch completion if needed
                    if hasattr(response, "id") and hasattr(response, "status"):
                        prediction_id = response.id
                        max_wait = int(
                            os.getenv("VLMRUN_MAX_WAIT", str(DEFAULT_MAX_WAIT))
                        )
                        poll_interval = int(
                            os.getenv(
                                "VLMRUN_POLL_INTERVAL",
                                str(DEFAULT_POLL_INTERVAL),
                            )
                        )
                        elapsed = 0

                        while elapsed < max_wait:
                            pred_response = client.predictions.get(
                                id=prediction_id
                            )

                            if pred_response.status == "completed":
                                result = (
                                    pred_response.result
                                    if hasattr(pred_response, "result")
                                    else pred_response
                                )
                                break
                            elif pred_response.status == "failed":
                                raise RuntimeError(
                                    f"Layout detection failed: {pred_response.error if hasattr(pred_response, 'error') else 'Unknown error'}"
                                )

                            time.sleep(poll_interval)
                            elapsed += poll_interval
                        else:
                            raise TimeoutError(
                                f"Layout detection timed out after {max_wait} seconds"
                            )
                    else:
                        result = response

                    # Parse and store the result
                    self._process_layout_result(
                        sample,
                        result,
                        result_field,
                    )

                    sample.save()
                    processed += 1

                except Exception as e:
                    error_msg = f"Failed to process {os.path.basename(sample.filepath)}: {str(e)}"
                    errors.append(error_msg)

                pb.update()

        # Refresh the app
        if not ctx.delegated:
            ctx.trigger("reload_dataset")

        # Return summary
        result = {
            "processed": processed,
            "total": total_documents,
            "errors": len(errors),
        }

        if errors:
            result["error_details"] = errors[:MAX_ERROR_DETAILS]

        return result

    def _process_layout_result(self, sample, result, result_field):
        """Process VLM Run layout detection result and update sample."""

        # Extract response data
        if hasattr(result, "response"):
            response_data = result.response
            if hasattr(response_data, "model_dump"):
                response_data = response_data.model_dump()
        elif hasattr(result, "data"):
            response_data = result.data
        else:
            response_data = result

        if isinstance(response_data, dict):
            detections = []
            layout_elements = {}

            # Process layout elements - they come as key-value pairs with metadata
            for key, value in response_data.items():
                if not key.endswith("_metadata"):
                    # Store the layout element text
                    element_name = key.replace("_page0", "")
                    layout_elements[element_name] = value

                    # Check for corresponding metadata
                    metadata_key = f"{key}_metadata"
                    if metadata_key in response_data:
                        metadata = response_data[metadata_key]
                        if isinstance(metadata, dict) and "bboxes" in metadata:
                            for bbox_info in metadata["bboxes"]:
                                if "bbox" in bbox_info and "xywh" in bbox_info["bbox"]:
                                    bbox_data = bbox_info["bbox"]["xywh"]

                                    # Convert confidence to numeric
                                    confidence_str = metadata.get("confidence", "med")
                                    if confidence_str == "hi":
                                        confidence = 0.9
                                    elif confidence_str == "med":
                                        confidence = 0.7
                                    else:
                                        confidence = 0.5

                                    detection = fol.Detection(
                                        label=element_name,
                                        bounding_box=bbox_data,
                                        confidence=confidence,
                                    )

                                    # Add page info if available
                                    if "page" in bbox_info:
                                        detection["page"] = bbox_info["page"]

                                    detections.append(detection)

            # Store layout elements as structured data
            if layout_elements:
                sample[f"{result_field}_elements"] = layout_elements

            # Store detections
            if detections:
                sample[result_field] = fol.Detections(detections=detections)

    def resolve_output(self, ctx):
        """Display output to the user."""
        outputs = types.Object()

        # Show actual results
        if "processed" in ctx.results:
            outputs.int("processed", label="Documents Processed")
        if "total" in ctx.results:
            outputs.int("total", label="Total Documents")
        if "errors" in ctx.results:
            outputs.int("errors", label="Errors")
        if "error" in ctx.results:
            outputs.str("error", label="Error", view=types.Warning())
        if "error_details" in ctx.results:
            outputs.list(
                "error_details", types.String(), label="Error Details"
            )

        # Success message
        if ctx.results.get("processed", 0) > 0:
            outputs.str(
                "success_msg",
                label="Success",
                default=f"Successfully detected layout in {ctx.results.get('processed')} document(s). Check the '{ctx.params.get('result_field', 'layout_detections')}' field in your samples.",
                view=types.Notice(variant="success"),
            )

        return types.Property(
            outputs, view=types.View(label="Layout Detection Results")
        )

def register(plugin):
    """Register all VLM Run operators."""
    plugin.register(VLMRunTranscribeVideo)
    plugin.register(VLMRunClassifyImages)
    plugin.register(VLMRunCaptionImages)
    plugin.register(VLMRunClassifyDocuments)
    plugin.register(VLMRunParseInvoices)
    plugin.register(VLMRunObjectDetection)
    plugin.register(VLMRunPersonDetection)
    plugin.register(VLMRunLayoutDetection)
