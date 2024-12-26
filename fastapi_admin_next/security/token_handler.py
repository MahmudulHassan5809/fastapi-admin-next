from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt


class TokenManager:
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        default_expiry_minutes: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.default_expiry_minutes = default_expiry_minutes

    def create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """
        Creates a JWT access token.
        :param data: Payload data for the token.
        :param expires_delta: Custom expiration time for the token.
        :return: Encoded JWT token.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=self.default_expiry_minutes)
        )
        to_encode.update({"exp": expire})
        return str(jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm))

    def decode_access_token(self, token: str) -> dict[str, Any] | None:
        """
        Decodes a JWT access token.
        :param token: Encoded JWT token.
        :return: Decoded payload if valid; None if invalid.
        """
        try:
            data: dict[str, Any] = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return data
        except JWTError:
            return None
