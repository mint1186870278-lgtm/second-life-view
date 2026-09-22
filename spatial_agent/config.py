from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_api_host: str = "https://dashscope.aliyuncs.com"
    dashscope_text_model: str = "deepseek-v4-pro"
    dashscope_vision_model: str = "qwen3.8-max"
    dashscope_image_model: str = "qwen-image-3.0-pro"
    lux3d_api_key: str = ""
    lux3d_region: str = "cn"
    lux3d_base_url: str = "https://api.aholo3d.cn"
    use_llm: bool = False
    use_external_tools: bool = False
    evidence_confidence_threshold: float = 0.78

@lru_cache
def get_settings() -> Settings:
    return Settings()
