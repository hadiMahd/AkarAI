from typing import Protocol, runtime_checkable


@runtime_checkable
class ChatProvider(Protocol):
    async def chat(self, messages: list[dict], **kwargs) -> dict: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str], **kwargs) -> list[list[float]]: ...


@runtime_checkable
class RerankingProvider(Protocol):
    async def rerank(self, query: str, documents: list[str], **kwargs) -> list[dict]: ...


@runtime_checkable
class OCRProvider(Protocol):
    async def extract_text(self, file_bytes: bytes, **kwargs) -> str: ...


@runtime_checkable
class STTProvider(Protocol):
    async def transcribe(self, audio_bytes: bytes, **kwargs) -> str: ...


@runtime_checkable
class TTSProvider(Protocol):
    async def synthesize(self, text: str, **kwargs) -> bytes: ...


@runtime_checkable
class ImageModerationProvider(Protocol):
    async def moderate(self, image_bytes: bytes, **kwargs) -> dict: ...


@runtime_checkable
class ImageQualityProvider(Protocol):
    async def assess(self, image_bytes: bytes, **kwargs) -> dict: ...


@runtime_checkable
class SpamClassifierProvider(Protocol):
    async def classify(self, text: str, **kwargs) -> dict: ...


@runtime_checkable
class LeadClassifierProvider(Protocol):
    async def classify(self, lead_data: dict, **kwargs) -> dict: ...
