thonfrom __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger("product_reviews_aggregator.aggregators.merger")

def _parse_date_for_sorting(date_value: Any) -> datetime:
    from ..extractors.utils_cleaner import parse_date  # local import to avoid cycle

    iso = parse_date(date_value)
    try:
        if iso.endswith("Z"):
            iso = iso.replace("Z", "+00:00")
        return datetime.fromisoformat(iso)
    except Exception:  # noqa: BLE001
        return datetime.min

def merge_review_batches(
    batches: Iterable[Iterable[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Merge multiple collections of reviews into a unified, deduplicated list.

    Deduplication is based on the composite key:
      (productUrl, marketplace, text, date)
    """
    from ..extractors.utils_cleaner import deduplicate_reviews  # local import

    flat: List[Dict[str, Any]] = []
    for collection in batches:
        for review in collection:
            flat.append(dict(review))

    LOGGER.debug("Merging %d reviews from all batches.", len(flat))
    deduped = deduplicate_reviews(flat)
    LOGGER.info("Deduplicated reviews: %d -> %d", len(flat), len(deduped))

    # Sort by date (newest first), then by rating (highest first)
    sorted_reviews = sorted(
        deduped,
        key=lambda r: (
            _parse_date_for_sorting(r.get("date")),
            float(r.get("rating", 0.0)),
        ),
        reverse=True,
    )

    return sorted_reviews