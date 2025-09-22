# VLM Run Plugin for FiftyOne

Extract structured data from videos using [VLM Run](https://vlm.run)'s
vision-language model.

## Installation

```bash
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/vlmrun

# Install plugin requirements
fiftyone plugins requirements @voxel51/vlmrun --install
```

## Requirements

-   VLM Run API key (get one at [vlm.run](https://vlm.run))
-   `vlmrun` Python package (>= 0.3.4)

## Configuration

Set your VLM Run API key as an environment variable:

```bash
export VLMRUN_API_KEY="your-api-key-here"
```

Or provide it when running the operator in the FiftyOne App.

## Features

Transcribe videos with:

-   Full transcription or 5-minute summaries
-   Temporal grounding with timestamps
-   Separate audio (speech) and video (visual) content extraction

## Usage

### Via FiftyOne App

1. Load a dataset with videos:

```python
import fiftyone as fo

# Load your video dataset
dataset = fo.load_dataset("your-video-dataset")

# Launch the App
session = fo.launch_app(dataset)
```

2. Use the operator:
    - Press `` ` `` to open the command palette
    - Search for "Transcribe Video (VLM Run)"
    - Configure options:
        - Choose between full transcription or summaries
        - Enable/disable temporal grounding
        - Specify field names for results
    - Run on selected samples or entire dataset

### Programmatic Usage

```python
import fiftyone as fo
import fiftyone.operators as foo

# Load dataset
dataset = fo.load_dataset("video-dataset")

# Get the operator
transcribe = foo.get_operator("@voxel51/vlmrun/transcribe_video")

# Execute transcription
transcribe(
    dataset,
    audio_field="audio_transcription",
    video_field="video_transcription",
    include_temporal_grounding=True,
    create_temporal_detections=True,
    temporal_field="transcript_segments",
    domain="video.transcription",  # or "video.transcription-summary"
)

# View results
session = fo.launch_app(dataset)
```

## Transcription Modes

### Full Transcription (`video.transcription`)

-   Complete word-for-word transcription
-   Detailed temporal grounding
-   Best for accessibility, subtitles, or detailed analysis

### Summary Mode (`video.transcription-summary`)

-   Processes video in 5-minute segments
-   Provides concise summaries of each segment
-   Ideal for long videos or quick content overview

## Output Fields

The operator creates the following fields in your samples:

-   `audio_transcription`: Speech transcription from audio
-   `video_transcription`: Visual descriptions from video
-   `audio_transcription_language`: Detected language (if available)
-   `audio_transcription_duration`: Video duration in seconds
-   `audio_transcription_word_count`: Total word count
-   `transcript_segments`: Temporal detections with timestamps (optional)

## Temporal Detections

When enabled, creates `TemporalDetection` labels with:

-   Start and end timestamps
-   Transcribed text for each segment
-   Confidence scores

Visible as timeline annotations in FiftyOne's video player.

## Example: Processing Multiple Videos

```python
import fiftyone as fo
import fiftyone.operators as foo

# Load a dataset with videos
dataset = fo.Dataset("my-videos")
dataset.add_samples(
    [
        fo.Sample(filepath="/path/to/video1.mp4"),
        fo.Sample(filepath="/path/to/video2.mp4"),
        fo.Sample(filepath="/path/to/video3.mp4"),
    ]
)

# Transcribe all videos with temporal grounding
transcribe = foo.get_operator("@voxel51/vlmrun/transcribe_video")
results = transcribe(
    dataset,
    audio_field="audio_transcription",
    video_field="video_transcription",
    include_temporal_grounding=True,
    create_temporal_detections=True,
    temporal_field="segments",
    domain="video.transcription",
)

print(f"Processed {results['processed']} videos")
print(f"Errors: {results['errors']}")

# View results in the App
session = fo.launch_app(dataset)

# Access transcriptions programmatically
for sample in dataset:
    print(f"Video: {sample.filepath}")
    print(f"Audio: {sample.audio_transcription}")
    print(f"Video: {sample.video_transcription}")
    if sample.has_field("segments"):
        print(f"Segments: {len(sample.segments.detections)}")
```

## Performance Notes

-   Video processing uses VLM Run's batch API
-   Processing time depends on video length
-   Failed videos don't stop batch processing

## Limitations

-   Maximum video file size depends on your VLM Run plan
-   Processing timeout: 10 minutes per video (configurable via
    `VLMRUN_MAX_WAIT` environment variable)
-   Supported formats: mp4, avi, mov, mkv, webm, flv, wmv, m4v

## Troubleshooting

### API Key Issues

-   Verify your API key is set correctly: `export VLMRUN_API_KEY="your-key"`
-   Or provide it directly in the operator dialog

### Timeout Errors

-   Use summary mode for long videos
-   Adjust timeout: `export VLMRUN_MAX_WAIT=1200` (20 minutes)

### Missing vlmrun Package

-   Run: `fiftyone plugins requirements @voxel51/vlmrun --install`

## Documentation

-   [VLM Run API](https://docs.vlm.run)
-   [FiftyOne](https://docs.voxel51.com)
