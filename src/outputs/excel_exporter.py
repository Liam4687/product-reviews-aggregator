thonimport logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from openpyxl import Workbook

LOGGER = logging.getLogger("product_reviews_aggregator.outputs.excel")

FIELDNAMES = [
    "productUrl",
    "text",
    "rating",
    "date",
    "marketplace",
    "reviewTitle",
    "reviewUrl",
]

def export_to_excel(
    reviews: Iterable[Dict[str, Any]],
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reviews"

    # Header
    ws.append(FIELDNAMES)

    rows: List[Dict[str, Any]] = []
    for r in reviews:
        row = [r.get(field, "") for field in FIELDNAMES]
        rows.append(r)
        ws.append(row)

    try:
        wb.save(output_path)
        LOGGER.info("Excel export written to %s (%d reviews).", output_path, len(rows))
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to write Excel export to %s: %s", output_path, exc)
        raise

    return output_path