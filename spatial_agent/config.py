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
    # qwen-image-3.0-pro is account-dependent: this workspace accepts the
    # synchronous request from the official example but rejects the async
    # header with AccessDenied. Keep async opt-in rather than defaulting it on.
    dashscope_image_async: bool = False
    dashscope_image_timeout: float = 240.0
    dashscope_chat_timeout: float = 120.0
    lux3d_api_key: str = ""
    aholo_api_key: str = ""
    tripo_api_key: str = ""
    tripo_base_url: str = "https://openapi.tripo3d.com/v3"
    # Aliyun OSS is the shared hand-off between the Windows camera gateway,
    # this Linux service, and providers that require an HTTP(S) asset URL.
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket: str = ""
    oss_endpoint: str = ""
    oss_region: str = ""
    oss_prefix: str = "second-life-view"
    oss_signed_url_ttl: int = 3600
    oss_max_upload_mb: int = 1024
    lux3d_region: str = "cn"
    lux3d_base_url: str = "https://api.aholo3d.cn"
    use_llm: bool = False
    use_external_tools: bool = False
    evidence_confidence_threshold: float = 0.78
    research_web_enabled: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
