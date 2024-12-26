from fastapi import Request

from fastapi_admin_next.schemas import QueryParams


class CommonQueryParam:
    def __init__(self, filter_fields: list[str] | None = None):
        self.filter_fields = filter_fields

    def __call__(self, request: Request) -> QueryParams:
        # Extract query parameters from the request
        query_params = dict(request.query_params)
        search = query_params.get("search")
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", 10))

        # Filter and clean additional query parameters
        filter_params = {
            k: v
            for k, v in query_params.items()
            if k in (self.filter_fields or []) and v
        }

        return QueryParams(
            search=search,
            page=page,
            page_size=page_size,
            filter_params=filter_params,
        )
