"""
Plugin management utilities.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import functools
import requests

import fiftyone.plugins.utils as fopu


@functools.lru_cache
def find_plugins(gh_repo):
    try:
        return fopu.find_plugins(gh_repo, info=True)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None

        raise e


@functools.lru_cache
def get_zoo_plugins():
    plugins = fopu.list_zoo_plugins()

    voxel51_plugins = []
    community_plugins = []
    for plugin in plugins:
        if plugin["name"].startswith("@voxel51/"):
            voxel51_plugins.append(plugin)
        else:
            community_plugins.append(plugin)

    return voxel51_plugins, community_plugins


@functools.lru_cache
def get_plugin_info(gh_repo, path=None):
    return fopu.get_plugin_info(gh_repo, path=path)
