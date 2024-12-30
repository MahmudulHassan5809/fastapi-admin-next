from typing import Any

from jose import ExpiredSignatureError, jwt
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    SimpleUser,
    UnauthenticatedUser,
)
from starlette.requests import Request

from fastapi_admin_next.configs import AuthConfigManager
from fastapi_admin_next.logger import logger


class JWTCookieBackend(AuthenticationBackend):
    def verify_user_id(self, token: str) -> dict[str, Any] | None:

        auth_config = AuthConfigManager.get_auth_config()

        data: dict[str, Any] = {}
        try:
            data = jwt.decode(
                token, auth_config.secret_key, algorithms=[auth_config.algorithm]
            )
        except ExpiredSignatureError as e:
            logger.info("log out user %s", e)
        except Exception:  # pylint: disable=broad-except
            pass

        if "id" not in data:
            return None
        return data

    async def authenticate(  # pylint: disable=arguments-renamed
        self, request: Request
    ) -> tuple[AuthCredentials, SimpleUser | UnauthenticatedUser]:

        auth_token: str = request.cookies.get("auth_token", "")
        user_data: dict[str, Any] | None = self.verify_user_id(auth_token)
        if user_data is None:
            roles = ["anon"]
            return AuthCredentials(roles), UnauthenticatedUser()

        request.state.user = user_data
        user_id: str = user_data.get("id", "")
        roles = ["authenticated"]
        return AuthCredentials(roles), SimpleUser(user_id)
