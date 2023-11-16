import pydoitz
from typing import List, Dict, Union, Optional
from collections import UserDict
from pydoitz.settings import CategoryConfig
from pydoitz.request import IDoitRequest
from pydoitz.exceptions import SystemError


class CategoryRequest(IDoitRequest):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_config = CategoryConfig(host=self._client.host)

    # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/methods.html#cmdbcategorycreate
    def create(self, object_ids: List[int], category: str, attributes: List[dict]):
        # "create" Function is deprecated
        return self.save(object_ids, category, attributes)

    # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/methods.html#cmdbcategorysave
    def save(self, object_ids: List[int], category: str,
             attributes: List[dict], entry_id: Optional[int] = None) -> List[int]:
        reqs = self._build_requests(
            method="save",
            attributes=attributes,
            object_ids=object_ids,
            categories=[category],
            entry_ids=[entry_id] if entry_id is not None else [],
        )
        res = self._client.batch_request(reqs)
        res.check_error()
        # TODO: Group created categories by object id
        return [result["entry"] for result in res.results()]

    # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/methods.html#cmdbcategorydelete
    def delete(self, object_ids: List[int], categories: List[str],
               entry_ids: Union[str, List[int]]) -> None:
        reqs = self._build_requests(
            method="delete",
            object_key="objID",
            entry_key="cateID",
            object_ids=object_ids,
            categories=categories,
            entry_ids=entry_ids,
        )
        self._client.batch_request(reqs).check_error()

    # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/methods.html#cmdbcategoryread
    def read(self, object_ids: List[int], categories: List[str]) -> None:
        """Read Category Entries of one or more Objects"""
        reqs = self._build_requests(
            method="read",
            object_key="objID",
            object_ids=object_ids,
            categories=categories,
        )
        res = self._client.batch_request(reqs)
        res.check_error()
        # TODO: Proper formatting
        return res

    # https://kb.i-doit.com/en/i-doit-pro-add-ons/api/methods.html#cmdbcategoryupdate
    def update(self, object_ids: List[int], category: str,
             attributes: List[dict], entry_id: Optional[int] = None):
        # "update" Function is deprecated
        return self.save(object_ids, category, attributes, entry_id)

    def quickpurge(self, object_ids: List[int], categories: List[str],
               entry_ids: Union[str, List[int]]) -> None:
        reqs = self._build_requests(
            method="quickpurge",
            object_key="objID",
            entry_key="cateID",
            object_ids=object_ids,
            categories=categories,
            entry_ids=entry_ids,
        )
        self._client.batch_request(reqs).check_error()

    def purge(self, object_ids: List[int], categories: List[str],
               entry_ids: Union[str, List[int]]) -> None:
        reqs = self._build_requests(
            method="purge",
            object_ids=object_ids,
            categories=categories,
            entry_ids=entry_ids,
        )
        self._client.batch_request(reqs).check_error()

    def recycle(self, object_ids: List[int], categories: List[str],
               entry_ids: Union[str, List[int]]) -> None:
        reqs = self._build_requests(
            method="recycle",
            object_ids=object_ids,
            categories=categories,
            entry_ids=entry_ids,
        )
        self._client.batch_request(reqs).check_error()

    def archive(self, object_ids: List[int], categories: List[str],
               entry_ids: Union[str, List[int]]) -> None:
        reqs = self._build_requests(
            method="archive",
            object_ids=object_ids,
            categories=categories,
            entry_ids=entry_ids,
        )
        self._client.batch_request(reqs).check_error()

    def _make_extra_params(self, entries, entry_key, attrs):
        out = []

        if not entries:
            return [{"data": attrs}]

        for entry in entries:
            params = {f"{entry_key}": entry}
            if attrs:
                params["data"] = attrs
            out.append(params)

        return out

    def _build_requests(self, method, object_ids, categories, object_key="object",
                        entry_key="entry", entry_ids=[], attributes=[]):
        reqs = []
        for obj in object_ids:
            for category in categories:
                params_list = [{}]

                if isinstance(entry_ids, str) and entry_ids == "all":
                    # TODO: Get all Entry IDs for that category
                    entry_ids = []

                if attributes:
                    params_list = []
                    for attrs in attributes:
                        params_list.extend(self._make_extra_params(
                            entry_ids, entry_key, attrs
                        ))
                elif entry_ids:
                    params_list = self._make_extra_params(entry_ids, entry_key, {})

                for params in params_list:
                    if "data" in params:
                        params["data"] = self.category_config.remap_keys(
                                category, params["data"]
                        )
                    reqs.append({
                        "method": f"cmdb.category.{method}",
                        "params": {
                            f"{object_key}": obj,
                            "category": category,
                            **params
                        }
                    })
        return reqs


class CategoryInfoRequest(IDoitRequest):

    def _build_requests(self, categories: List[str] = None):
        reqs = []
        req_id_map = {}

        for cat in categories:
            req_id = self._client.next_request_id()
            reqs.append({
                "method": "cmdb.category_info",
                "params": { "category": cat },
                "id": req_id
            })
            req_id_map[req_id] = cat

        return reqs, req_id_map

    def _read(self, categories, verify):
        reqs, req_id_map = self._build_requests(categories)
        resp = self._client.batch_request(reqs)
        out = {}

        for req in resp:
            category = req_id_map[req.request_id]

            if not verify and req.error:
                # If we read all categories, ignore those that the API will
                # complain about
                continue
            else:
                req.check_error()

            out[category] = req.result

        return out

    def read(self, categories: List[str]):
        return self._read(categories, True)

    def read_all(self):
        category_const = self._client.idoit.constants().get("categories", {})
        categories = []
        for data in category_const.values():
            categories.extend(list(data.keys()))

        return self._read(categories, False)
