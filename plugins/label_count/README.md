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

## Creating Animations with `FrameLoaderView` and `TimelineView`

### What is FrameLoaderView?

`FrameLoaderView` is a `types.View` that facilitates the incremental loading of
animation data, buffering frame-level data that corresponds to associated
`TimelineView`.

### How FrameLoaderView Works in a Panel

When used in a panel, `FrameLoaderView` loads and buffers animation data based
on the current playback state of a video or other temporal sample, or an
associated `types.TimelineView`. Here’s how it functions:

1. **Create a FrameLoaderView:**

    - The component is embedded in a panel’s rendering logic, similar to other
      Views like `GridView`.
    - Rendering an object with a `FrameLoaderView` tells the panel to buffer
      animation data for the default timeline.
    - You can create your own `TimelineView` and link it to your
      `FrameLoaderView` by passing the same `timeline_name`.

2. **Buffering Animation Data:**

    - As the video sample plays or the user scrubs through the timeline,
      `FrameLoaderView` loads frame-specific animation data into a buffer.
    - Whatever data is loaded will be set as the animation plays at the given
      `target` path (e.g., `"plot.selectedpoints"`).

3. **Dynamic Frame Loading:**
    - It fetches frame data dynamically, keeping only the required frames in
      memory.
    - When the video timeline changes (e.g., jumping to a new timestamp or
      playing continuously), the buffer is updated accordingly, fetching the
      necessary animation data for that frame range.

### What is TimelineView?

`TimelineView` is a `types.View` that enables timeline-based navigation in a
panel. It allows users to scrub, jump, or play through the timeline, triggering
dynamic loading of animation data from the `FrameLoaderView`.

### How TimelineView Works in a Panel

When used in a panel, `TimelineView` provides the timeline control,
synchronizing with the `FrameLoaderView` to load animation data in real-time.
Here’s how it functions:

1. **Create a TimelineView:**

    - The component is embedded in a panel’s rendering logic, similar to other
      Views like buttons or dropdowns.
    - You can define the total number of frames and link it to a
      `FrameLoaderView` by using the same `timeline_name`.

2. **Navigating the Timeline:**

    - Users can interact with the timeline by scrubbing, seeking, or playing,
      which triggers the loading of the relevant frame range.
    - It sends updates to the linked `FrameLoaderView`, which buffers animation
      data in sync with the current playback position.

3. **Real-Time Synchronization:**
    - The `TimelineView` updates the current frame dynamically, enabling
      real-time loading and display of frame-specific data or animations.
    - It supports both continuous playback and manual scrubbing, ensuring that
      users have full control over frame navigation.

### Example Implementation

Here’s an example of how `FrameLoaderView` is used with a custom
`TimelineView`:

```python
import fiftyone.operators.types as types
import fiftyone.operators as foo

# Example data for demonstration purposes
EXAMPLE_DATA = [1, 2, 3, 4, 5, 6, 7, 8]


class AnimationPanel(foo.Panel):
    @property
    def config(self):
        return foo.PanelConfig(
            name="animation_panel",
            label="Animation",
            surfaces="main",
            allow_multiple=True,
            reload_on_navigation=True,
        )

    def on_load(self, ctx):
        # Initialize the plot with example data
        ctx.panel.data.plot = {
            "type": "scatter",
            "x": EXAMPLE_DATA,
            "y": EXAMPLE_DATA,
            "selectedpoints": [0],
        }

    def render(self, ctx):
        # Define the timeline name and total frames for animation
        timeline_name = "my_timeline"
        total_frames = len(EXAMPLE_DATA)

        # Create the panel container object
        panel = types.Object()

        # Add the scatter plot to the panel
        panel.plot("plot")

        # Add the TimelineView for navigating through frames
        panel.view(
            "timeline",
            view=types.TimelineView(
                timeline_name=timeline_name, total_frames=total_frames
            ),
        )

        # Add the FrameLoaderView to handle buffering of animation data
        panel.obj(
            "animation_data",
            view=types.FrameLoaderView(
                timeline_name=timeline_name,  # Link to the same timeline
                on_load_range=self.on_load_range,
                target="plot.selectedpoints",  # Set the target for animation
            ),
        )

        # Return the complete panel with all components
        return types.Property(panel)

    def on_load_range(self, ctx):
        # Retrieve the range of frames to buffer from the context
        range_to_load = ctx.params.get("range")
        self.buffer_frames(ctx, range_to_load)

    def buffer_frames(self, ctx, range_to_load):
        start, end = range_to_load
        buffer = {}

        # Load animation data for the specified frame range
        for i in range(start, end):
            buffer[f"animation_data.frames[{i}]"] = self.render_frame(i)

        # Update the panel's buffer with the loaded frame data
        ctx.panel.set_data(buffer)

    def render_frame(self, frame):
        # Generate animation data for the given frame
        return [frame]
```
