from __future__ import annotations


def normalize_embedding_dim(vec: list[float], target_dim: int) -> list[float]:
    if len(vec) == target_dim:
        return vec
    if len(vec) > target_dim:
        return vec[:target_dim]
    return vec + [0.0] * (target_dim - len(vec))

