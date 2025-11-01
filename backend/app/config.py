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
    
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    google_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    provider: str = Field(default="groq", validation_alias="LLM_PROVIDER")
    model: str = Field(default="mixtral-8x7b-32768", validation_alias="LLM_MODEL")
    temperature: float = Field(default=0.7, validation_alias="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")


class DatabaseConfig(BaseSettings):
    """Database Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""  # Explicitly set no prefix for root-level env vars
    )
    
    url: str = Field(default="postgresql://walletmind:password@localhost:5432/walletmind", validation_alias="DATABASE_URL")
    host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    user: str = Field(default="walletmind", validation_alias="POSTGRES_USER")
    password: str = Field(default="", validation_alias="POSTGRES_PASSWORD")
    database: str = Field(default="walletmind", validation_alias="POSTGRES_DB")


class ChromaDBConfig(BaseSettings):
    """ChromaDB Configuration (FR-003)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    persist_dir: str = Field(default="./data/chromadb", validation_alias="CHROMADB_PERSIST_DIR")
    host: str = Field(default="localhost", validation_alias="CHROMADB_HOST")
    port: int = Field(default=8000, validation_alias="CHROMADB_PORT")


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
    deployer_private_key: Optional[str] = Field(default=None, validation_alias="DEPLOYER_PRIVATE_KEY")
    agent_private_key: Optional[str] = Field(default=None, validation_alias="AGENT_PRIVATE_KEY")
    
    # Network RPCs
    sepolia_rpc_url: str = Field(default="https://rpc.sepolia.org", validation_alias="SEPOLIA_RPC_URL")
    polygon_amoy_rpc_url: Optional[str] = Field(default=None, validation_alias="POLYGON_AMOY_RPC_URL")
    base_goerli_rpc_url: Optional[str] = Field(default=None, validation_alias="BASE_GOERLI_RPC_URL")
    
    # Contract addresses
    agent_wallet_contract: Optional[str] = Field(default=None, validation_alias="AGENT_WALLET_CONTRACT_ADDRESS")
    agent_registry_contract: Optional[str] = Field(default=None, validation_alias="AGENT_REGISTRY_CONTRACT_ADDRESS")
    
    # Gas configuration
    default_gas_limit: int = Field(default=100000, validation_alias="DEFAULT_GAS_LIMIT")
    max_gas_price_gwei: int = Field(default=50, validation_alias="MAX_GAS_PRICE_GWEI")
    gas_price_multiplier: float = Field(default=1.1, validation_alias="GAS_PRICE_MULTIPLIER")


class IPFSConfig(BaseSettings):
    """IPFS Configuration (FR-007)"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    api_url: str = Field(default="http://localhost:5001", validation_alias="IPFS_API_URL")
    pinata_api_key: Optional[str] = Field(default=None, validation_alias="PINATA_API_KEY")
    pinata_secret_key: Optional[str] = Field(default=None, validation_alias="PINATA_SECRET_API_KEY")
    pinata_jwt: Optional[str] = Field(default=None, validation_alias="PINATA_JWT")


class RedisConfig(BaseSettings):
    """Redis Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    port: int = Field(default=6379, validation_alias="REDIS_PORT")
    db: int = Field(default=0, validation_alias="REDIS_DB")
    password: Optional[str] = Field(default=None, validation_alias="REDIS_PASSWORD")


class BackgroundTasksConfig(BaseSettings):
    """Background Tasks Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    transaction_monitor_interval: int = Field(default=10, validation_alias="TRANSACTION_MONITOR_INTERVAL")
    reputation_update_interval: int = Field(default=300, validation_alias="REPUTATION_UPDATE_INTERVAL")
    agent_loop_check_interval: int = Field(default=30, validation_alias="AGENT_LOOP_CHECK_INTERVAL")
    enable_background_tasks: bool = Field(default=True, validation_alias="ENABLE_BACKGROUND_TASKS")


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
    master_password: str = Field(default="change_this_in_production", validation_alias="MASTER_PASSWORD")
    key_salt: str = Field(default="walletmind_security_salt", validation_alias="KEY_SALT")
    key_rotation_days: int = Field(default=90, validation_alias="KEY_ROTATION_DAYS")
    enable_key_rotation: bool = Field(default=True, validation_alias="ENABLE_KEY_ROTATION")
    
    # Cryptographic Operations (FR-007, NFR-006)
    nonce_validity_seconds: int = Field(default=300, validation_alias="NONCE_VALIDITY_SECONDS")
    signature_max_age_seconds: int = Field(default=3600, validation_alias="SIGNATURE_MAX_AGE_SECONDS")
    
    # Authentication
    jwt_secret: str = Field(default="change_this_jwt_secret_in_production", validation_alias="JWT_SECRET")
    access_token_expiry_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRY_MINUTES")
    refresh_token_expiry_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRY_DAYS")
    
    # Rate Limiting
    default_rate_limit: int = Field(default=60, validation_alias="DEFAULT_RATE_LIMIT")
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS")


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
    oracle_cache_ttl: int = Field(default=300, validation_alias="ORACLE_CACHE_TTL")
    coingecko_api_key: Optional[str] = Field(default=None, validation_alias="COINGECKO_API_KEY")
    chainlink_provider_url: Optional[str] = Field(default=None, validation_alias="CHAINLINK_PROVIDER_URL")
    etherscan_api_key: Optional[str] = Field(default=None, validation_alias="ETHERSCAN_API_KEY")
    
    # Payment Service
    payment_confirmation_blocks: int = Field(default=3, validation_alias="PAYMENT_CONFIRMATION_BLOCKS")
    default_payment_gas_limit: int = Field(default=100000, validation_alias="DEFAULT_PAYMENT_GAS_LIMIT")
    
    # Verification Service
    blockchain_logging_enabled: bool = Field(default=True, validation_alias="BLOCKCHAIN_LOGGING_ENABLED")
    ipfs_storage_enabled: bool = Field(default=True, validation_alias="IPFS_STORAGE_ENABLED")


class APIConfig(BaseSettings):
    """API Configuration"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    port: int = Field(default=8000, validation_alias="API_PORT")
    workers: int = Field(default=4, validation_alias="API_WORKERS")
    reload: bool = Field(default=False, validation_alias="API_RELOAD")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        validation_alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, validation_alias="CORS_ALLOW_CREDENTIALS")
    
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
    
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(default="json", validation_alias="LOG_FORMAT")
    sentry_dsn: Optional[str] = Field(default=None, validation_alias="SENTRY_DSN")


class FeatureFlagsConfig(BaseSettings):
    """Feature Flags"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    enable_swagger_docs: bool = Field(default=True, validation_alias="ENABLE_SWAGGER_DOCS")
    enable_websockets: bool = Field(default=True, validation_alias="ENABLE_WEBSOCKETS")
    enable_metrics: bool = Field(default=True, validation_alias="ENABLE_METRICS")
    enable_rate_limiting: bool = Field(default=True, validation_alias="ENABLE_RATE_LIMITING")


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
    debug: bool = Field(default=False, validation_alias="DEBUG")
    testing: bool = Field(default=False, validation_alias="TESTING")
    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    
    # Sub-configurations - Create instances with defaults using Field
    llm: LLMConfig = LLMConfig()
    database: DatabaseConfig = DatabaseConfig()
    chromadb: ChromaDBConfig = ChromaDBConfig()
    blockchain: BlockchainConfig = BlockchainConfig()
    ipfs: IPFSConfig = IPFSConfig()
    redis: RedisConfig = RedisConfig()
    background_tasks: BackgroundTasksConfig = BackgroundTasksConfig()
    security: SecurityConfig = SecurityConfig()
    infrastructure: InfrastructureServicesConfig = InfrastructureServicesConfig()
    api: APIConfig = APIConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    features: FeatureFlagsConfig = FeatureFlagsConfig()


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