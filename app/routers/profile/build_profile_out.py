from pydantic import BaseModel

from app.services.neon.rows import UserRow


class ProfileOut(BaseModel):
    email: str | None
    display_name: str | None
    name_pronunciation: str | None
    native_language: str | None
    target_accent: str | None
    goals: str | None
    location_city: str | None
    timezone: str | None


def build_profile_out(user: UserRow) -> ProfileOut:
    return ProfileOut(
        email=user["email"],
        display_name=user["display_name"],
        name_pronunciation=user["name_pronunciation"],
        native_language=user["native_language"],
        target_accent=user["target_accent"],
        goals=user["goals"],
        location_city=user["location_city"],
        timezone=user["timezone"],
    )
