from unittest.mock import AsyncMock, patch

from bot.services.user_service import UserService


async def test_register_activity_delegates_to_repository():
    with patch("bot.services.user_service.UserRepository") as repo_cls:
        repo_cls.return_value.upsert_on_activity = AsyncMock(return_value="user-obj")

        service = UserService(session=object())
        result = await service.register_activity(42, "alice")

    repo_cls.return_value.upsert_on_activity.assert_awaited_once_with(42, "alice")
    assert result == "user-obj"
