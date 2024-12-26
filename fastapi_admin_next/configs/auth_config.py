from dataclasses import dataclass


@dataclass
class AuthConfig:
    auth_model: type
    auth_username_field: str
    password_field: str
    secret_key: str
    algorithm: str
    token_expiry_minutes: int
    cookie_name: str


class AuthConfigManager:
    _instance: AuthConfig | None = None

    @classmethod
    def set_auth_config(cls, auth_config: AuthConfig) -> None:
        """Sets the AuthConfig instance."""
        cls._instance = auth_config

    @classmethod
    def get_auth_config(cls) -> AuthConfig:
        """Retrieves the AuthConfig instance."""
        if cls._instance is None:
            raise ValueError("AuthConfig has not been initialized.")
        return cls._instance
