thonimport logging
from typing import Any, Dict, List

from .utils_cleaner import generate_fake_reviews

LOGGER = logging.getLogger("product_reviews_aggregator.extractors.ebay")

def extract_reviews(
product_url: str,
max_reviews: int,
marketplace: str = "ebay",
) -> List[Dict[str, Any]]:
"""
Extract reviews for an eBay product.

This demonstration implementation generates deterministic synthetic reviews.
It mirrors the interface of a real parser that would scrape live data.
"""
LOGGER.info("Starting eBay extraction for %s (max=%d)", product_url, max_reviews)
reviews = generate_fake_reviews(
product_url=product_url,
marketplace=marketplace,
max_reviews=max_reviews,
)
LOGGER.info("eBay extractor produced %d reviews", len(reviews))
return reviews