from bts_monitoring.services.inference.base import AIModel


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, AIModel] = {}

    def register(self, model: AIModel) -> None:
        if model.name in self._models:
            raise ValueError(
                f"Model already registered: {model.name}"
            )

        self._models[model.name] = model

    def get(self, name: str) -> AIModel:
        try:
            return self._models[name]
        except KeyError as exc:
            raise KeyError(
                f"Model not found: {name}"
            ) from exc

    def list_models(self) -> list[str]:
        return list(self._models)