from app.daily_content.models import TalkItem


def dedup_news_across_categories(category_lists: list[list[TalkItem]]) -> list[list[TalkItem]]:
    """Keep each article in only the first category it appears in, so a headline never shows up in two sections.

    NewsAPI tags the same story under several categories (a market story lands in both politics and business); we dedup by URL (falling back to title) across categories, preserving the input order.
    """
    seen: set[str] = set()
    result: list[list[TalkItem]] = []
    for items in category_lists:
        kept: list[TalkItem] = []
        for item in items:
            key = item.url or item.title
            if key in seen:
                continue
            seen.add(key)
            kept.append(item)
        result.append(kept)
    return result
