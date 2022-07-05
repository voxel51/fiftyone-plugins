import {PointCloud} from './PointCloud'
import {
  registerComponent,
  PluginComponentType
} from '@fiftyone/plugins'


registerComponent({
  name: 'PointCloud',
  component: PointCloud,
  type: PluginComponentType.SampleModalContent,
  activator: ({sample}) => typeof sample.pcd_filepath === 'string'
})