thonimport csv
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger("product_reviews_aggregator.outputs.csv")

FIELDNAMES = [
    "productUrl",
    "text",
    "rating",
    "date",
    "marketplace",
    "reviewTitle",
    "reviewUrl",
]

def export_to_csv(
    reviews: Iterable[Dict[str, Any]],
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for r in reviews:
        row = {field: r.get(field, "") for field in FIELDNAMES}
        rows.append(row)

    try:
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        LOGGER.info("CSV export written to %s (%d reviews).", output_path, len(rows))
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to write CSV export to %s: %s", output_path, exc)
        raise

    return output_path