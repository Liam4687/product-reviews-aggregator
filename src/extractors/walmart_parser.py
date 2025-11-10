thonimport logging
from typing import Any, Dict, List

from .utils_cleaner import generate_fake_reviews

LOGGER = logging.getLogger("product_reviews_aggregator.extractors.walmart")

def extract_reviews(
product_url: str,
max_reviews: int,
marketplace: str = "walmart",
) -> List[Dict[str, Any]]:
"""
Extract reviews for a Walmart product.

This implementation generates deterministic synthetic reviews suitable
for testing the aggregation and export pipeline.
"""
LOGGER.info("Starting Walmart extraction for %s (max=%d)", product_url, max_reviews)
reviews = generate_fake_reviews(
product_url=product_url,
marketplace=marketplace,
max_reviews=max_reviews,
)
LOGGER.info("Walmart extractor produced %d reviews", len(reviews))
return reviews