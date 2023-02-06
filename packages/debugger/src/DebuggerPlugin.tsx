
import {registerComponent, PluginComponentType} from '@fiftyone/plugins'
import {Debugger} from './Debugger'

registerComponent({
  name: 'Debugger',
  label: 'Debugger',
  component: Debugger,
  type: PluginComponentType.Panel,
  activator: myActivator
})

function myActivator({dataset}) {
  return true
}