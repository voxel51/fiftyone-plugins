import {PointCloud} from './PointCloud'
import {
  registerComponent,
  PluginComponentType
} from '@fiftyone/plugins'

registerComponent({
  name: 'PointCloud',
  component: PointCloud,
  type: PluginComponentType.Visualizer,
  activator: ({sample, pinned}) => typeof sample.pcd_filepath === 'string' && pinned
})