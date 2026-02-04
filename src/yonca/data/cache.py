from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


class _CachedRepository:
    def __init__(self, repo: Any, cache: dict[Any, Any] | None = None) -> None:
        self._repo = repo
        self._cache: dict[Any, Any] = cache or {}

    def _call_repo(self, method_names: Sequence[str], *args: Any, **kwargs: Any) -> Any:
        for name in method_names:
            if hasattr(self._repo, name):
                return getattr(self._repo, name)(*args, **kwargs)
        raise AttributeError(
            f"Underlying repository does not implement any of: {', '.join(method_names)}"
        )

    def _cache_key(self, *args: Any, **kwargs: Any) -> Any:
        if args:
            return args[0]
        if "id" in kwargs:
            return kwargs["id"]
        if "uid" in kwargs:
            return kwargs["uid"]
        return tuple(kwargs.items())

    def get_by_id(self, id: Any) -> Any:
        if id in self._cache:
            return self._cache[id]
        item = self._call_repo(["get_by_id", "get", "get_one", "fetch_by_id"], id)
        self._cache[id] = item
        return item

    def get(self, id: Any) -> Any:
        return self.get_by_id(id)

    def get_or_none(self, id: Any) -> Any | None:
        try:
            return self.get_by_id(id)
        except Exception:
            return None

    def get_by_ids(self, ids: Iterable[Any]) -> dict[Any, Any]:
        results: dict[Any, Any] = {}
        missing: list[Any] = []
        for _id in ids:
            if _id in self._cache:
                results[_id] = self._cache[_id]
            else:
                missing.append(_id)

        if missing:
            fetched = self._call_repo(
                ["get_by_ids", "get_many", "list_by_ids", "fetch_by_ids"], missing
            )
            if isinstance(fetched, dict):
                for k, v in fetched.items():
                    self._cache[k] = v
                    results[k] = v
            else:
                for item in fetched:
                    key = getattr(item, "id", None)
                    if key is None:
                        continue
                    self._cache[key] = item
                    results[key] = item

        return results

    def __getattr__(self, name: str) -> Any:
        return getattr(self._repo, name)


class CachedFarmRepository(_CachedRepository):
    def __init__(self, repo: Any, cache: dict[Any, Any] | None = None) -> None:
        super().__init__(repo, cache)


class CachedUserRepository(_CachedRepository):
    def __init__(self, repo: Any, cache: dict[Any, Any] | None = None) -> None:
        super().__init__(repo, cache)
