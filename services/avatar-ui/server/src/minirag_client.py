import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp


logger = logging.getLogger(__name__)


class MiniRagError(RuntimeError):
    pass


@dataclass(frozen=True)
class MiniRagConfig:
    base_url: str
    workspace: str
    timeout_seconds: int = 30


class MiniRagClient:
    def __init__(self, config: MiniRagConfig) -> None:
        self._config = config
        self._base_url = config.base_url.rstrip("/")

    async def bulk_insert(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "workspace": self._config.workspace,
            "documents": documents,
        }
        return await self._post("/minirag/documents/bulk", payload)

    async def search(self, query: str, top_k: int) -> dict[str, Any]:
        payload = {
            "workspace": self._config.workspace,
            "query": query,
            "top_k": top_k,
        }
        return await self._post("/minirag/search", payload)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise MiniRagError(f"MiniRAG error {response.status}: {text}")
                    return await response.json()
        except asyncio.TimeoutError as exc:
            logger.exception("MiniRAG request timed out after %s seconds: %s", self._config.timeout_seconds, url)
            raise MiniRagError(f"MiniRAG request timed out after {self._config.timeout_seconds} seconds") from exc
        except aiohttp.ClientError as exc:
            logger.exception("MiniRAG request failed: %s", exc)
            raise MiniRagError(f"MiniRAG request failed: {exc}") from exc
        except ValueError as exc:
            logger.exception("MiniRAG response JSON parse failed: %s", exc)
            raise MiniRagError(f"MiniRAG response JSON parse failed: {exc}") from exc
