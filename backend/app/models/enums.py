from enum import Enum


class HumanizationStyle(str, Enum):
    NATURAL = "natural"
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"


class HumanizationStrength(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelProvider(str, Enum):
    TRANSFORMERS = "transformers"
    OLLAMA = "ollama"
    VLLM = "vllm"
    TRITON = "triton"


class Device(str, Enum):
    AUTO = "auto"
    CUDA = "cuda"
    CPU = "cpu"
    MPS = "mps"