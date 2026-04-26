from tinydb import TinyDB, Query
from functools import reduce


class ApathyRepo:
    def __init__(self, table_name: str):
        self._db = TinyDB("database.json")
        self._table = self._db.table(table_name)

    def insert(self, data: dict) -> int:
        return self._table.insert(data)

    def find(self, **kwargs) -> list[dict]:
        if not kwargs:
            return self._table.all()
        q = Query()
        conditions = [getattr(q, k) == v for k, v in kwargs.items()]
        return self._table.search(reduce(lambda a, b: a & b, conditions))

    def find_one(self, **kwargs) -> dict | None:
        results = self.find(**kwargs)
        return results[0] if results else None

    def update(self, data: dict, doc_id: int) -> None:
        self._table.update(data, doc_ids=doc_id)

    def delete(self, doc_id: int) -> None:
        self._table.remove(doc_ids=doc_id)