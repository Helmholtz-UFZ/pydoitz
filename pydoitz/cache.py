import yaml
import json
import pydoitz
from pydoitz import utils
from pathlib import Path


def init(client):
    cache_dir = utils.get_cache_home() / client.host

    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)

    _setup_categories(client, cache_dir)


def _setup_categories(client, path):
    categories = client.cmdb.category_info.read_all()
    file_data = []

    for cat, cat_data in categories.items():
        data = {"name": cat, "params": {}}

        if not cat_data:
            continue

        for key, values in cat_data.items():
            key_type = values["data"].get("type")
            key_title = values["title"]
            key_desc = values["info"].get("description")

            to_add = {
                key: {
                    "param": key,
                    "help": key_desc if key_desc else key_title,
                    "type": key_type
                }
            }
            data["params"].update(to_add)

        # C "" CATG "" <NAME>
        # oder
        # C "" CATG "" CUSTOM "" FIELDS "" <NAME>
        # TODO: fix this mess...
        catg_name_components = cat.rsplit("_")
        real_name_idx = sum([-1 for i in catg_name_components if not i])
        real_name = "-".join(catg_name_components[real_name_idx:])

        if "CUSTOM" in catg_name_components:
            cli_name = f"c.{real_name}"
        elif "C__CATS" in catg_name_components:
            cli_name = f"s.{real_name}"
        else:
            cli_name = f"g.{real_name}"

        data["cli_name"] = cli_name.casefold()
        file_data.append(data)

    path = path / "categories.json"
    with path.open("w") as f:
        json.dump(file_data, f, indent=4)
