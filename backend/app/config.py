"""
Configuration Management - Environment Variables and Settings

Loads all configuration from environment variables with validation.
Uses pydantic-settings for type-safe configuration.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class LLMConfig(BaseSettings):
    """LLM Configuration (FR-001, FR-002)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    provider: str = Field(default="groq", env="LLM_PROVIDER")
    model: str = Field(default="mixtral-8x7b-32768", env="LLM_MODEL")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")


class DatabaseConfig(BaseSettings):
    """Database Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""  # Explicitly set no prefix for root-level env vars
    )
    
    url: str = Field(..., env="DATABASE_URL", validation_alias="DATABASE_URL")
    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    user: str = Field(default="walletmind", env="POSTGRES_USER")
    password: str = Field(default="", env="POSTGRES_PASSWORD")
    database: str = Field(default="walletmind", env="POSTGRES_DB")


class ChromaDBConfig(BaseSettings):
    """ChromaDB Configuration (FR-003)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    persist_dir: str = Field(default="./data/chromadb", env="CHROMADB_PERSIST_DIR")
    host: str = Field(default="localhost", env="CHROMADB_HOST")
    port: int = Field(default=8000, env="CHROMADB_PORT")


class BlockchainConfig(BaseSettings):
    """Blockchain Configuration (FR-004, FR-005, FR-006)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    # Private keys (SENSITIVE - never log these)
    deployer_private_key: Optional[str] = Field(default=None, env="DEPLOYER_PRIVATE_KEY")
    agent_private_key: Optional[str] = Field(default=None, env="AGENT_PRIVATE_KEY")
    
    # Network RPCs
    sepolia_rpc_url: str = Field(..., env="SEPOLIA_RPC_URL", validation_alias="SEPOLIA_RPC_URL")
    polygon_amoy_rpc_url: Optional[str] = Field(default=None, env="POLYGON_AMOY_RPC_URL")
    base_goerli_rpc_url: Optional[str] = Field(default=None, env="BASE_GOERLI_RPC_URL")
    
    # Contract addresses
    agent_wallet_contract: Optional[str] = Field(default=None, env="AGENT_WALLET_CONTRACT_ADDRESS")
    agent_registry_contract: Optional[str] = Field(default=None, env="AGENT_REGISTRY_CONTRACT_ADDRESS")
    
    # Gas configuration
    default_gas_limit: int = Field(default=100000, env="DEFAULT_GAS_LIMIT")
    max_gas_price_gwei: int = Field(default=50, env="MAX_GAS_PRICE_GWEI")
    gas_price_multiplier: float = Field(default=1.1, env="GAS_PRICE_MULTIPLIER")


class IPFSConfig(BaseSettings):
    """IPFS Configuration (FR-007)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    api_url: str = Field(default="http://localhost:5001", env="IPFS_API_URL")
    pinata_api_key: Optional[str] = Field(default=None, env="PINATA_API_KEY")
    pinata_secret_key: Optional[str] = Field(default=None, env="PINATA_SECRET_API_KEY")
    pinata_jwt: Optional[str] = Field(default=None, env="PINATA_JWT")


class RedisConfig(BaseSettings):
    """Redis Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")


class BackgroundTasksConfig(BaseSettings):
    """Background Tasks Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    transaction_monitor_interval: int = Field(default=10, env="TRANSACTION_MONITOR_INTERVAL")
    reputation_update_interval: int = Field(default=300, env="REPUTATION_UPDATE_INTERVAL")
    agent_loop_check_interval: int = Field(default=30, env="AGENT_LOOP_CHECK_INTERVAL")
    enable_background_tasks: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")


class SecurityConfig(BaseSettings):
    """Security Configuration (NFR-004, FR-007, NFR-006)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    # Key Management (NFR-004)
    master_password: str = Field(..., env="MASTER_PASSWORD", validation_alias="MASTER_PASSWORD")
    key_salt: str = Field(default="walletmind_security_salt", env="KEY_SALT")
    key_rotation_days: int = Field(default=90, env="KEY_ROTATION_DAYS")
    enable_key_rotation: bool = Field(default=True, env="ENABLE_KEY_ROTATION")
    
    # Cryptographic Operations (FR-007, NFR-006)
    nonce_validity_seconds: int = Field(default=300, env="NONCE_VALIDITY_SECONDS")
    signature_max_age_seconds: int = Field(default=3600, env="SIGNATURE_MAX_AGE_SECONDS")
    
    # Authentication
    jwt_secret: str = Field(..., env="JWT_SECRET", validation_alias="JWT_SECRET")
    access_token_expiry_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRY_MINUTES")
    refresh_token_expiry_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRY_DAYS")
    
    # Rate Limiting
    default_rate_limit: int = Field(default=60, env="DEFAULT_RATE_LIMIT")
    rate_limit_window_seconds: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")


class InfrastructureServicesConfig(BaseSettings):
    """Infrastructure Services Configuration (FR-010, FR-011)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    # Oracle Service
    oracle_cache_ttl: int = Field(default=300, env="ORACLE_CACHE_TTL")
    coingecko_api_key: Optional[str] = Field(default=None, env="COINGECKO_API_KEY")
    chainlink_provider_url: Optional[str] = Field(default=None, env="CHAINLINK_PROVIDER_URL")
    etherscan_api_key: Optional[str] = Field(default=None, env="ETHERSCAN_API_KEY")
    
    # Payment Service
    payment_confirmation_blocks: int = Field(default=3, env="PAYMENT_CONFIRMATION_BLOCKS")
    default_payment_gas_limit: int = Field(default=100000, env="DEFAULT_PAYMENT_GAS_LIMIT")
    
    # Verification Service
    blockchain_logging_enabled: bool = Field(default=True, env="BLOCKCHAIN_LOGGING_ENABLED")
    ipfs_storage_enabled: bool = Field(default=True, env="IPFS_STORAGE_ENABLED")


class APIConfig(BaseSettings):
    """API Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = Field(default=4, env="API_WORKERS")
    reload: bool = Field(default=False, env="API_RELOAD")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class MonitoringConfig(BaseSettings):
    """Monitoring & Logging Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")


class FeatureFlagsConfig(BaseSettings):
    """Feature Flags"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    enable_swagger_docs: bool = Field(default=True, env="ENABLE_SWAGGER_DOCS")
    enable_websockets: bool = Field(default=True, env="ENABLE_WEBSOCKETS")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")


class Settings(BaseSettings):
    """
    Main Settings class that aggregates all configuration.
    
    Loads from:
    1. Environment variables
    2. .env file
    3. Default values
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__"
    )
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Sub-configurations - Use default_factory lambda to delay instantiation
    llm: LLMConfig = Field(default_factory=lambda: LLMConfig())
    database: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig())
    chromadb: ChromaDBConfig = Field(default_factory=lambda: ChromaDBConfig())
    blockchain: BlockchainConfig = Field(default_factory=lambda: BlockchainConfig())
    ipfs: IPFSConfig = Field(default_factory=lambda: IPFSConfig())
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    background_tasks: BackgroundTasksConfig = Field(default_factory=lambda: BackgroundTasksConfig())
    security: SecurityConfig = Field(default_factory=lambda: SecurityConfig())
    infrastructure: InfrastructureServicesConfig = Field(default_factory=lambda: InfrastructureServicesConfig())
    api: APIConfig = Field(default_factory=lambda: APIConfig())
    monitoring: MonitoringConfig = Field(default_factory=lambda: MonitoringConfig())
    features: FeatureFlagsConfig = Field(default_factory=lambda: FeatureFlagsConfig())


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create singleton Settings instance.
    
    Returns:
        Settings instance with all configuration loaded
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings


# Network configurations for blockchain
NETWORK_CONFIGS = {
    "sepolia": {
        "chain_id": 11155111,
        "name": "Sepolia Testnet",
        "currency": "ETH",
        "explorer": "https://sepolia.etherscan.io"
    },
    "polygon_amoy": {
        "chain_id": 80002,
        "name": "Polygon Amoy Testnet",
        "currency": "MATIC",
        "explorer": "https://amoy.polygonscan.com"
    },
    "base_goerli": {
        "chain_id": 84531,
        "name": "Base Goerli Testnet",
        "currency": "ETH",
        "explorer": "https://goerli.basescan.org"
    }
}


def get_network_config(network: str) -> dict:
    """Get configuration for a specific blockchain network"""
    return NETWORK_CONFIGS.get(network.lower(), NETWORK_CONFIGS["sepolia"])