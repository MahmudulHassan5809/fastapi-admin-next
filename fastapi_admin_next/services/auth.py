from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_admin_next.configs import AuthConfigManager
from fastapi_admin_next.crud import CRUDGenerator
from fastapi_admin_next.db_connect import Base
from fastapi_admin_next.security import PasswordHandler, TokenManager

from .base import BaseService


class AuthService(BaseService):

    async def login(
        self,
        data_dict: dict[str, Any],
        db: AsyncSession,
    ) -> tuple[dict[str, Any], bool]:
        auth_config = AuthConfigManager.get_auth_config()

        model = self.registry.get_model(auth_config.auth_model)
        crud: CRUDGenerator[Base] = CRUDGenerator(model=model, session=db)

        user = await crud.get_by_field(
            filters={
                auth_config.auth_username_field: data_dict[
                    auth_config.auth_username_field
                ]
            }
        )
        if not user or not PasswordHandler.verify_password(
            data_dict[auth_config.password_field], user.password  # type: ignore
        ):
            errors = {"credentials": "Invalid credentials"}
            return errors, False

        access_token = TokenManager(
            secret_key=auth_config.secret_key,
            algorithm=auth_config.algorithm,
            default_expiry_minutes=auth_config.token_expiry_minutes,
        ).create_access_token(
            {
                "id": user.id,  # type: ignore
                "username": data_dict[auth_config.auth_username_field],
            }
        )

        return {
            "value": access_token,
            "key": auth_config.cookie_name,
            "max_age": auth_config.token_expiry_minutes * 60,
            "httponly": True,
            "secure": False,
        }, True
