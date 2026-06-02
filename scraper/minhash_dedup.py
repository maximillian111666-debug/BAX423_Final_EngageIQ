"""
BAX-423 Technique: Sketching (MinHash for near-duplicate detection).
Uses min-wise independent hash functions to estimate Jaccard similarity
between documents without comparing full content.
"""
import hashlib
import re
import json
from typing import Optional


NUM_HASHES = 128
SHINGLE_SIZE = 3
SIMILARITY_THRESHOLD = 0.8


def _shingles(text: str, k: int = SHINGLE_SIZE) -> set[str]:
    tokens = re.sub(r"\W+", " ", text.lower()).split()
    return {" ".join(tokens[i: i + k]) for i in range(max(1, len(tokens) - k + 1))}


def _hash_fn(shingle: str, seed: int) -> int:
    h = hashlib.md5(f"{seed}:{shingle}".encode()).hexdigest()
    return int(h, 16)


def compute_minhash(text: str, num_hashes: int = NUM_HASHES) -> list[int]:
    shingles = _shingles(text)
    if not shingles:
        return [0] * num_hashes
    signature = []
    for seed in range(num_hashes):
        min_hash = min(_hash_fn(s, seed) for s in shingles)
        signature.append(min_hash)
    return signature


def jaccard_from_signatures(sig1: list[int], sig2: list[int]) -> float:
    if len(sig1) != len(sig2) or not sig1:
        return 0.0
    matches = sum(a == b for a, b in zip(sig1, sig2))
    return matches / len(sig1)


class MinHashDeduplicator:
    """
    Maintains an in-memory set of seen MinHash signatures for deduplication.
    Uses LSH banding to achieve sub-linear candidate lookup.
    """

    def __init__(self, num_hashes: int = NUM_HASHES, threshold: float = SIMILARITY_THRESHOLD):
        self.num_hashes = num_hashes
        self.threshold = threshold
        self.num_bands = 32
        self.rows_per_band = num_hashes // self.num_bands
        self._buckets: dict[tuple, list[list[int]]] = {}

    def _band_keys(self, signature: list[int]) -> list[tuple]:
        keys = []
        for b in range(self.num_bands):
            start = b * self.rows_per_band
            band = tuple(signature[start: start + self.rows_per_band])
            keys.append((b, band))
        return keys

    def is_duplicate(self, text: str) -> tuple[bool, list[int]]:
        sig = compute_minhash(text, self.num_hashes)
        candidates: set[int] = set()
        for key in self._band_keys(sig):
            for stored in self._buckets.get(key, []):
                sim = jaccard_from_signatures(sig, stored)
                if sim >= self.threshold:
                    return True, sig
        return False, sig

    def add(self, signature: list[int]):
        for key in self._band_keys(signature):
            self._buckets.setdefault(key, []).append(signature)

    def check_and_add(self, text: str) -> tuple[bool, list[int]]:
        is_dup, sig = self.is_duplicate(text)
        if not is_dup:
            self.add(sig)
        return is_dup, sig
