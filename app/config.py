from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis configuration
    # redis_host: str
    # redis_port: int
    redis_db: int = 0
    redis_password: str
    redis_host_node_1: str
    redis_port_node_1: int
    redis_host_node_2: str
    redis_port_node_2: int
    redis_host_node_3: str
    redis_port_node_3: int
    redis_host_node_4: str
    redis_port_node_4: int
    redis_host_node_5: str
    redis_port_node_5: int
    redis_host_node_6: str
    redis_port_node_6: int

    # Application settings
    app_name: str = "100k Rate Limiter"
    app_version: str = "1.0.0"
    debug: bool = False

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
