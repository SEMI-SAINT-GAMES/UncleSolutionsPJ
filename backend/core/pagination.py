from fastapi import Query


class Pagination:
    def __init__(self, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)):
        self.page = page
        self.limit = limit
        self.skip = self.limit * (page - 1)

    def create_pagination_response(self, total_count: int, items: list):
        return {
            "total_count": total_count,
            "total_pages": total_count // self.limit
            + (1 if total_count % self.limit > 0 else 0),
            "current_page": self.page,
            "limit": self.limit,
            "items": items,
        }

    def create_user_profile_pagination_response(self, total_count: int):
        paginated_with_info = {
            "total_count": total_count,
            "total_pages": total_count // self.limit
            + (1 if total_count % self.limit > 0 else 0),
            "current_page": self.page,
            "limit": self.limit,
        }
        return paginated_with_info
