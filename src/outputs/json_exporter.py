thonimport json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

LOGGER = logging.getLogger("product_reviews_aggregator.outputs.json")

def export_to_json(
    reviews: Iterable[Dict[str, Any]],
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data: List[Dict[str, Any]] = [dict(r) for r in reviews]

    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        LOGGER.info("JSON export written to %s (%d reviews).", output_path, len(data))
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to write JSON export to %s: %s", output_path, exc)
        raise

    return output_path