thonimport hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger("product_reviews_aggregator.extractors.utils")

def clean_review_text(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def normalize_rating(raw: Any, scale: int = 5) -> float:
    try:
        rating = float(raw)
    except (TypeError, ValueError):
        return 0.0

    if rating < 0:
        rating = 0.0
    if rating > scale:
        rating = float(scale)
    return round(rating, 2)

def parse_date(date_value: Any) -> str:
    """
    Convert various date representations to ISO 8601 string (UTC).
    Accepts datetime, date, or ISO-like strings.
    """
    if isinstance(date_value, datetime):
        dt = date_value
    else:
        if not isinstance(date_value, str):
            return ""
        txt = date_value.strip()
        if not txt:
            return ""
        # Try parse ISO formats
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(txt, fmt)
                break
            except ValueError:
                dt = None  # type: ignore[assignment]
        else:
            # Fallback: try fromisoformat
            try:
                dt = datetime.fromisoformat(txt)
            except ValueError:
                LOGGER.debug("Could not parse date '%s', returning as-is.", date_value)
                return txt

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")

def marketplace_slug(marketplace: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", marketplace.lower()).strip("-")

def deterministic_random(seed: str, min_val: int = 1, max_val: int = 5) -> int:
    if min_val > max_val:
        raise ValueError("min_val must not be greater than max_val")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    num = int(digest[:8], 16)
    span = max_val - min_val + 1
    return min_val + (num % span)

def generate_fake_reviews(
    product_url: str,
    marketplace: str,
    max_reviews: int,
) -> List[Dict[str, Any]]:
    """
    Generate deterministic, synthetic reviews for a given product URL.

    This makes the project runnable offline while still having realistic,
    structured review data.
    """
    reviews: List[Dict[str, Any]] = []
    marketplace_slugged = marketplace_slug(marketplace)

    base_seed = hashlib.sha256(product_url.encode("utf-8")).hexdigest()
    max_reviews = max(1, max_reviews)
    now = datetime.now(timezone.utc)

    for idx in range(1, max_reviews + 1):
        seed = f"{base_seed}-{idx}"
        rating = normalize_rating(deterministic_random(seed, 1, 5))
        days_ago = deterministic_random(seed + "-days", 1, 365)
        created_at = now - timedelta(days=days_ago, hours=idx)
        title = f"Review #{idx} for {marketplace_slugged.upper()}"
        text = (
            f"This is an auto-generated synthetic review #{idx} for "
            f"product {product_url} on {marketplace_slugged}."
        )
        review_url = f"{product_url}#review-{idx}"

        reviews.append(
            {
                "productUrl": product_url,
                "text": clean_review_text(text),
                "rating": rating,
                "date": parse_date(created_at),
                "marketplace": marketplace_slugged,
                "reviewTitle": title,
                "reviewUrl": review_url,
            },
        )

    return reviews

def deduplicate_reviews(reviews: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate reviews by a composite key.
    """
    seen: set[str] = set()
    result: List[Dict[str, Any]] = []

    for review in reviews:
        key_parts = [
            str(review.get("productUrl", "")).strip().lower(),
            str(review.get("marketplace", "")).strip().lower(),
            str(review.get("text", "")).strip().lower(),
            str(review.get("date", "")).strip(),
        ]
        key = "|".join(key_parts)

        if key in seen:
            continue
        seen.add(key)
        result.append(review)

    return result