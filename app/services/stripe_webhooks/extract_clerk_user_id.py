from pydantic import BaseModel, ValidationError


class _Metadata(BaseModel):
    clerk_user_id: str | None = None


class _Customer(BaseModel):
    metadata: _Metadata | None = None


class _SubscriptionData(BaseModel):
    """Subset of a Stripe `data.object` we read for clerk_user_id resolution.

    Strict-typed alternative to `Mapping[str, object]` — pyright narrows isinstance(dict) to `Mapping[Unknown, Unknown]` which loses element type info, so we validate into this BaseModel instead.
    """

    metadata: _Metadata | None = None
    customer: _Customer | None = None


def extract_clerk_user_id(data: dict[str, object]) -> str | None:
    # iOS / subscription-create flow sets metadata.clerk_user_id on either the subscription or the customer. Check the subscription first, fall back to the customer.
    try:
        parsed = _SubscriptionData.model_validate(data)
    except ValidationError:
        return None
    if parsed.metadata and parsed.metadata.clerk_user_id:
        return parsed.metadata.clerk_user_id
    if parsed.customer and parsed.customer.metadata and parsed.customer.metadata.clerk_user_id:
        return parsed.customer.metadata.clerk_user_id
    return None
