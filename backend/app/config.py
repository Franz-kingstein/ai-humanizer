from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Application
    app_name: str = "ai-humanizer"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Privacy
    store_user_text: bool = False

    # Model Provider
    model_provider: str = "transformers"
    model_device: str = "auto"

    # Humanization Model
    humanizer_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    humanizer_model_revision: str = "main"
    humanizer_max_new_tokens: int = 2048
    humanizer_temperature: float = 0.7
    humanizer_top_p: float = 0.9
    humanizer_repetition_penalty: float = 1.1
    humanizer_quantization: str = "4bit"

    # Semantic Validation
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_similarity_threshold: float = 0.85
    max_rewrite_attempts: int = 2

    # Input Limits
    max_input_characters: int = 20000
    max_input_words: int = 3000

    # NLP Analysis
    spacy_model: str = "en_core_web_sm"
    use_stopwords_in_metrics: bool = True

    # Naturalness Score Weights
    weight_sentence_variation: float = 0.20
    weight_lexical_diversity: float = 0.20
    weight_repetition: float = 0.15
    weight_template_density: float = 0.15
    weight_passive_voice: float = 0.10
    weight_readability: float = 0.10
    weight_semantic_coherence: float = 0.10

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Request ID
    request_id_header: str = "X-Request-ID"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def naturalness_weights(self) -> dict:
        return {
            "sentence_variation": self.weight_sentence_variation,
            "lexical_diversity": self.weight_lexical_diversity,
            "repetition": self.weight_repetition,
            "template_density": self.weight_template_density,
            "passive_voice": self.weight_passive_voice,
            "readability": self.weight_readability,
            "semantic_coherence": self.weight_semantic_coherence,
        }


@lru_cache()
def get_settings() -> Settings:
    return Settings()