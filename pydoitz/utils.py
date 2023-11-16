from pathlib import Path
from os import environ
from collections import OrderedDict
import json
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


CONFIG_FORMATS = OrderedDict({
    "json": { "parser": json, "args": {}},
    "yml": { "parser": yaml, "args": {"Loader": Loader}},
    "yaml": { "parser": yaml, "args": {"Loader": Loader}}
})


def get_config_home():
    xdg_config_home = environ.get("XDG_CONFIG_HOME")
    if not xdg_config_home:
        return Path.home() / ".config/pydoitz"

    return Path(xdg_config_home)


def get_cache_home():
    xdg_cache_home = environ.get("XDG_CACHE_HOME")
    if not xdg_cache_home:
        return Path.home() / ".cache/pydoitz"

    return Path(xdg_cache_home)


def get_cache(host):
    if not host:
        return None
    return get_cache_home() / host


def get_config_file(path, name):
    if path:
        return Path(path)

    conf_home = get_config_home()
    for ext in CONFIG_FORMATS:
        conf_file = conf_home / f"{name}.{ext}"
        if conf_file.exists():
            break

    return conf_file
