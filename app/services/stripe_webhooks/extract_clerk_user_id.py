from typing import Any


def extract_clerk_user_id(data: dict[str, Any]) -> str | None:
    # iOS / subscription-create flow sets metadata.clerk_user_id on either the subscription or the customer. Check the subscription first, fall back to the customer.
    metadata = data.get("metadata") or {}
    clerk_user_id = metadata.get("clerk_user_id")
    if clerk_user_id:
        return str(clerk_user_id)
    customer = data.get("customer")
    if isinstance(customer, dict):
        cust_meta = customer.get("metadata") or {}
        if cust_meta.get("clerk_user_id"):
            return str(cust_meta["clerk_user_id"])
    return None
