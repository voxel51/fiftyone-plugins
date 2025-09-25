# VLM Run Plugin

A plugin that provides operators for extracting structured data from visual
sources using [VLM Run](https://vlm.run)'s vision-language model.

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/vlmrun
```

Install the required dependencies:

```shell
fiftyone plugins requirements @voxel51/vlmrun --install
```

Refer to the [main README](https://github.com/voxel51/fiftyone-plugins) for
more information about managing downloaded plugins and developing plugins
locally.

## Configuration

Set your VLM Run API key as an environment variable:

```shell
export VLMRUN_API_KEY="your-api-key-here"
```

Alternatively, you can provide the API key directly when running operators in
the FiftyOne App.

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart")
session = fo.launch_app(dataset)
```

2.  Press `` ` `` or click the `Browse operations` action to open the Operators
    list

3.  Select any of the operators listed below!

## Operators

### vlmrun_transcribe_video

Extract speech transcriptions and visual descriptions from videos with temporal
grounding.

This operator is essentially a wrapper around VLM Run's video transcription
domains:

```py
# Full transcription with temporal segments
client.run("video.transcription", video_path)

# Or 5-minute segment summaries
client.run("video.transcription-summary", video_path)
```

The operator extracts:
- Audio transcription (speech content)
- Video transcription (visual descriptions)
- Temporal segments with timestamps
- Language detection and word counts

### vlmrun_caption_images

Generate descriptive captions for images.

This operator uses VLM Run's image captioning domain:

```py
client.run("image.caption", image_path)
```

### vlmrun_object_detection

Detect and localize common objects in images.

This operator uses VLM Run's object detection capabilities with visual
grounding:

```py
client.run("image.object-detection", image_path,
           generation_config=GenerationConfig(grounding=True))
```

Features:
- Bounding boxes in normalized xywh format
- Confidence scores for each detection
- Support for common object categories

### vlmrun_person_detection

Specialized person detection with enhanced accuracy.

This operator uses VLM Run's person detection domain:

```py
client.run("image.person-detection", image_path,
           generation_config=GenerationConfig(grounding=True))
```

### vlmrun_parse_invoices

Extract structured data from invoice documents.

This operator uses VLM Run's invoice parsing domain:

```py
client.run("document.invoice", invoice_path,
           generation_config=GenerationConfig(grounding=True))
```

Extracts:
- Invoice totals and line items
- Customer and vendor information
- Payment terms and dates
- Visual grounding for each field (optional)

### vlmrun_layout_detection

Analyze document layout and structure.

This operator uses VLM Run's document structure analysis:

```py
client.run("document.structure", document_path,
           generation_config=GenerationConfig(grounding=True))
```

Identifies:
- Text regions and columns
- Headers, footers, and body text
- Tables and figures
- Bounding boxes for each layout element

## Visual Grounding

When enabled, visual grounding provides bounding box coordinates for extracted
data in normalized xywh format:
- `x`: horizontal position of top-left corner (0-1)
- `y`: vertical position of top-left corner (0-1)
- `w`: width of the box (0-1)
- `h`: height of the box (0-1)

## Supported Formats

- **Images**: JPEG, PNG, and other common formats
- **Documents**: PDF, scanned documents
- **Videos**: MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V

## Learn More

- [VLM Run Documentation](https://docs.vlm.run)
- [FiftyOne Documentation](https://docs.voxel51.com)