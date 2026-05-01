from src.models import Keyword, Trend, ContentBrief


def select_todays_content(
    keywords: list[Keyword],
    trends: list[Trend],
    daily_pin_limit: int,
    seo_percent: int = 70
) -> list[ContentBrief]:
    """
    Decide what content to create today.
    
    Logic:
    1. Calculate seo_count = round(daily_pin_limit * seo_percent / 100)
    2. Calculate trend_count = daily_pin_limit - seo_count
    3. Sort keywords by performance_score (desc), then suggestion_rank (asc)
    4. Take top seo_count keywords → create ContentBrief(content_type="seo")
    5. Filter trends to velocity > 1.0
    6. Take top trend_count trends → create ContentBrief(content_type="trend")
    7. Return combined list sorted by priority
    """
    seo_count = round(daily_pin_limit * seo_percent / 100)
    trend_count = daily_pin_limit - seo_count

    sorted_keywords = sorted(
        keywords,
        key=lambda k: (-k.performance_score, k.suggestion_rank)
    )

    seo_briefs = [
        ContentBrief(
            target_keyword=kw.term,
            content_type="seo",
            priority=i + 1,
            related_terms=kw.related_terms,
            board_name=""
        )
        for i, kw in enumerate(sorted_keywords[:seo_count])
    ]

    rising_trends = [t for t in trends if t.velocity > 1.0]
    sorted_trends = sorted(rising_trends, key=lambda t: -t.velocity)

    trend_briefs = [
        ContentBrief(
            target_keyword=t.name,
            content_type="trend",
            priority=seo_count + i + 1,
            related_terms=t.keywords,
            board_name=""
        )
        for i, t in enumerate(sorted_trends[:trend_count])
    ]

    all_briefs = seo_briefs + trend_briefs
    all_briefs.sort(key=lambda b: b.priority)

    return all_briefs