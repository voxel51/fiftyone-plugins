# Label Count Plugin

Includes a modal panel that renders an a plot displaying the given field count
for a corresponding frame

https://github.com/user-attachments/assets/33ddd658-502f-4f86-bdbe-19e39086bfa4

## Installation

```shell
fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/label_count
```

## Usage

1.  Launch the App:

```py
import fiftyone as fo
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset("quickstart-video")
session = fo.launch_app(dataset)
```

2.  Select a sample in the grid

3.  Press the `+` button next to "Sample" in the top left and choose "Label
    Count"

4.  Choose the "detections.detections" field in the dropdown.

5.  Playing the video will show the corresponding frame in the plot.
