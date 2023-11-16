from .category import (
    CategoryRequest,
    CategoryInfoRequest
)


class CMDBNamespace:

    def __init__(self, api):
        self.category = CategoryRequest(api)
        self.category_info = CategoryInfoRequest(api)
