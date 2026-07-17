from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ModelDetection:
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float] | None = None
    polygon: list[tuple[float, float]] | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


class AIModel(ABC):
    name: str
    version: str

    @abstractmethod
    def predict(
        self,
        frame: np.ndarray,
    ) -> list[ModelDetection]:
        raise NotImplementedError