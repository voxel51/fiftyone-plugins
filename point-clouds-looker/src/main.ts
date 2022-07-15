import { PluginComponentType, registerComponent } from "@fiftyone/plugins";
import {Looker,BaseElement, BaseConfig, BaseState} from '@fiftyone/looker'
import { Optional, BaseOptions, DEFAULT_BASE_OPTIONS } from "@fiftyone/looker/src/state";
import * as common from "@fiftyone/looker/src/elements/common/index";
import { GetElements } from "@fiftyone/looker/src/elements";
import { createElementsTree } from "@fiftyone/looker/src/elements/util";

class PointCloudLooker extends Looker {
  protected getDefaultOptions(): BaseOptions {
    return {...DEFAULT_BASE_OPTIONS}
  }
  protected getInitialState(config: BaseConfig, options: Optional<BaseOptions>): BaseState {
    options = {
      ...this.getDefaultOptions(),
      ...options,
    };

    return {
      ...super.getInitialBaseState(),
      config: { ...config },
      options,
      SHORTCUTS: common.COMMON_SHORTCUTS,
    };
  }
  protected getElements(config: Readonly<BaseConfig>): common.LookerElement<BaseState> {
    return getPointCloudElements(config, super.updater, super.getDispatchEvent())
  }
  protected hasDefaultZoom(state: BaseState, overlays: any): boolean {
    return false
  }

  updateOptions(options: Optional<BaseState["options"]>) {
    
  }
}

class CanvasElement<State extends BaseState> extends BaseElement<
  State,
  HTMLCanvasElement
> {

  getEvents(): any {
    return {}
  }

  createHTMLElement() {
    const element = document.createElement("canvas");
    return element;
  }

  renderSelf(state: Readonly<State>) {
    return null
  }
}



const getPointCloudElements: GetElements<BaseState> = (
  config,
  update,
  dispatchEvent
) => {
  const elements = {
    node: common.LookerElement,
    children: [
      {
        node: CanvasElement,
      },
      {
        node: common.ErrorElement,
      },
      { node: common.TagsElement },
      {
        node: common.ThumbnailSelectorElement,
      },
      {
        node: common.JSONPanelElement,
      },
      {
        node: common.HelpPanelElement,
      },
      {
        node: common.ControlsElement,
        children: [
          { node: common.FullscreenButtonElement },
          { node: common.ToggleOverlaysButtonElement },
          { node: common.JSONButtonElement },
          { node: common.OptionsButtonElement },
          { node: common.HelpButtonElement },
        ],
      },
      {
        node: common.PreviousElement,
      },
      {
        node: common.NextElement,
      },
      {
        node: common.OptionsPanelElement,
        children: [
          { node: common.OnlyShowHoveredOnLabelOptionElement },
          { node: common.ShowConfidenceOptionElement },
          { node: common.ShowIndexOptionElement },
          { node: common.ShowLabelOptionElement },
          { node: common.ShowTooltipOptionElement },
        ],
      },
    ],
  };

  return createElementsTree<BaseState, common.LookerElement<BaseState>>(
    config,
    elements,
    update,
    dispatchEvent
  );
};

registerComponent({
  name: 'PointCloudLooker',
  type: PluginComponentType.Looker,
  constructor: PointCloudLooker,
  activator: () => true
})