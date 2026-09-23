from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_api_host: str = "https://dashscope.aliyuncs.com"
    # Image generation is not served by every OpenAI-compatible MaaS gateway.
    # Keep it on DashScope's official multimodal-generation endpoint even when
    # chat uses a workspace-specific compatible-mode URL.
    dashscope_image_api_host: str = "https://dashscope.aliyuncs.com"
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
    # Windows hosts upload completed ERP JPEGs to this Linux service. Keep the
    # endpoint disabled until a distinct, high-entropy bearer token is set.
    camera_ingest_token: str = ""
    camera_ingest_max_upload_mb: int = 256
    # Canonical public HTTPS origin used in returned camera asset URLs when
    # FastAPI is behind a reverse proxy. Leave blank for direct/local serving.
    public_base_url: str = ""
    windows_camera_gateway_url: str = ""
    windows_camera_gateway_token: str = ""
    windows_camera_gateway_timeout: float = 720.0
    # Live inference is intentionally separate from the checked-in fixtures.
    # "auto" chooses the CUDA device with sufficient free VRAM, or CPU.
    yolo_weights: str = ""
    yolo_device: str = "auto"
    # In auto mode choose the CUDA device with at least this much currently
    # free VRAM; otherwise use CPU instead of repeatedly OOMing GPU 0.
    yolo_auto_min_free_mb: int = 1024
    yolo_confidence: float = 0.12
    yolo_view_size: int = 768
    yolo_fov_deg: float = 90.0
    lux3d_region: str = "cn"
    lux3d_base_url: str = "https://api.aholo3d.cn"
    use_llm: bool = False
    use_external_tools: bool = False
    evidence_confidence_threshold: float = 0.78
    research_web_enabled: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
