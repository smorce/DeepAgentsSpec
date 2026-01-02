import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger("minirag")

@dataclass
class EmbeddingFunc:
    embedding_dim: int
    max_token_size: int
    func: callable

    async def __call__(self, *args, **kwargs) -> np.ndarray:
        return await self.func(*args, **kwargs)

def clean_text(text: str) -> str:
    """Clean text by removing null bytes (0x00) and whitespace"""
    return text.strip().replace("\x00", "")

def compute_mdhash_id(content: str, prefix: str = ""):
    from hashlib import md5
    return prefix + md5(content.encode()).hexdigest()
