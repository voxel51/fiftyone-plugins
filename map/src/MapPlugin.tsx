
import {registerComponent, PluginComponentType} from '@fiftyone/plugins'
import Map from './Map'

registerComponent({
  name: 'Map',
  label: 'Map',
  component: Map,
  type: PluginComponentType.Plot,
  // TODO custom activator
  activator: () => true
})
