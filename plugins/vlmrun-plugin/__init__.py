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

# Configuration constants
DEFAULT_API_URL = "https://api.vlm.run/v1"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 5
DEFAULT_MAX_WAIT = 600  # 10 minutes
DEFAULT_POLL_INTERVAL = 5  # seconds
MAX_ERROR_DETAILS = 5

# Supported video extensions
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


class TranscribeVideo(foo.Operator):
    """Transcribe video content with temporal grounding using VLM Run."""

    @property
    def config(self):
        return foo.OperatorConfig(
            name="transcribe_video",
            label="Transcribe Video (VLM Run)",
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
        has_view = ctx.view != ctx.dataset.view()
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

        inputs.enum(
            "domain",
            [
                "video.transcription",
            ],
            label="Transcription Mode",
            description="Full video transcription with audio and visual content",
            default="video.transcription",
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
        domain = ctx.params.get("domain", "video.transcription")

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
                # Combine all audio transcripts from segments
                audio_transcripts = []
                video_descriptions = []

                for segment in response_data["segments"]:
                    if isinstance(segment, dict):
                        # Get audio content
                        if "audio" in segment and isinstance(
                            segment["audio"], dict
                        ):
                            audio_content = segment["audio"].get("content", "")
                            if audio_content:
                                audio_transcripts.append(audio_content)

                        # Get video content
                        if "video" in segment and isinstance(
                            segment["video"], dict
                        ):
                            video_content = segment["video"].get("content", "")
                            if video_content:
                                video_descriptions.append(video_content)

                # Save both fields only if they have content
                audio_text = " ".join(audio_transcripts)
                video_text = " ".join(video_descriptions)

                if audio_text:
                    sample[audio_field] = audio_text
                if video_text:
                    sample[video_field] = video_text

            # Store metadata if present
            if "metadata" in response_data and isinstance(response_data["metadata"], dict):
                metadata = response_data["metadata"]
                if "duration" in metadata and metadata["duration"] is not None:
                    sample[f"{audio_field}_duration"] = metadata["duration"]
                if "topics" in metadata and metadata["topics"] is not None:
                    sample[f"{audio_field}_topics"] = metadata["topics"]


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


def register(plugin):
    """Register all VLM Run operators."""
    plugin.register(TranscribeVideo)
