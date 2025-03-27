from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user: User | None = result.scalar_one_or_none()
        return user

    async def create_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str | None,
        is_bot: bool = False,
    ) -> User:
        """Create new user."""
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_bot=is_bot,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_or_create_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str | None,
        is_bot: bool = False,
    ) -> User:
        """Get existing user or create new one."""
        user = await self.get_user(user_id)
        if user is None:
            user = await self.create_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                is_bot=is_bot,
            )
        return user
