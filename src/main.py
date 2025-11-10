thonimport argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .extractors import amazon_parser, ebay_parser, walmart_parser
from .aggregators.review_merger import merge_review_batches
from .outputs.json_exporter import export_to_json
from .outputs.csv_exporter import export_to_csv
from .outputs.excel_exporter import export_to_excel

LOGGER = logging.getLogger("product_reviews_aggregator")

def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        LOGGER.warning("Config file %s not found, using default settings.", config_path)
        return {
            "max_reviews_per_product": 25,
            "export": {
                "formats": ["json", "csv", "excel"],
                "output_dir": "data",
            },
        }

    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Failed to load config %s: %s", config_path, exc)
        raise

def load_input_tasks(input_path: Path) -> List[Dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input file must contain a JSON array of tasks.")

    return data

def _get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def resolve_paths(
    input_file: str | None,
    config_file: str | None,
    output_dir_override: str | None,
) -> Dict[str, Path]:
    root = _get_project_root()

    src_dir = root / "src"
    data_dir = root / "data"
    config_dir = src_dir / "config"

    input_path = Path(input_file) if input_file else data_dir / "inputs.sample.json"
    config_path = Path(config_file) if config_file else config_dir / "settings.example.json"

    config = load_config(config_path)

    default_output_dir = root / config.get("export", {}).get("output_dir", "data")
    output_dir = Path(output_dir_override) if output_dir_override else default_output_dir

    return {
        "root": root,
        "input": input_path,
        "config": config_path,
        "output_dir": output_dir,
    }

def run(
    input_file: str | None = None,
    config_file: str | None = None,
    output_dir: str | None = None,
    verbose: bool = False,
) -> None:
    _setup_logging(verbose)
    paths = resolve_paths(input_file, config_file, output_dir)
    root = paths["root"]
    input_path = paths["input"]
    config_path = paths["config"]
    output_dir_path = paths["output_dir"]

    LOGGER.info("Project root: %s", root)
    LOGGER.info("Using config: %s", config_path)
    LOGGER.info("Using input: %s", input_path)
    LOGGER.info("Output directory: %s", output_dir_path)

    config = load_config(config_path)
    tasks = load_input_tasks(input_path)
    max_reviews_default = int(config.get("max_reviews_per_product", 25))

    output_dir_path.mkdir(parents=True, exist_ok=True)

    all_batches: List[List[Dict[str, Any]]] = []

    for idx, task in enumerate(tasks, start=1):
        marketplace = str(task.get("marketplace", "")).lower().strip()
        product_url = task.get("productUrl") or task.get("product_url")
        max_reviews = int(task.get("maxReviews", max_reviews_default))

        if not marketplace or not product_url:
            LOGGER.warning(
                "Skipping task #%d because marketplace or productUrl is missing: %s",
                idx,
                task,
            )
            continue

        LOGGER.info(
            "Processing task #%d: marketplace=%s, url=%s, max_reviews=%d",
            idx,
            marketplace,
            product_url,
            max_reviews,
        )

        try:
            if marketplace == "amazon":
                reviews = amazon_parser.extract_reviews(
                    product_url=product_url,
                    max_reviews=max_reviews,
                    marketplace=marketplace,
                )
            elif marketplace == "ebay":
                reviews = ebay_parser.extract_reviews(
                    product_url=product_url,
                    max_reviews=max_reviews,
                    marketplace=marketplace,
                )
            elif marketplace == "walmart":
                reviews = walmart_parser.extract_reviews(
                    product_url=product_url,
                    max_reviews=max_reviews,
                    marketplace=marketplace,
                )
            else:
                LOGGER.warning("Unknown marketplace '%s', skipping task.", marketplace)
                continue

            LOGGER.info(
                "Task #%d produced %d reviews before aggregation.",
                idx,
                len(reviews),
            )
            all_batches.append(reviews)

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Error while processing task #%d: %s", idx, exc)

    aggregated = merge_review_batches(all_batches)
    LOGGER.info("Aggregated total of %d reviews.", len(aggregated))

    export_formats = config.get("export", {}).get("formats", ["json", "csv", "excel"])
    export_formats = [f.lower() for f in export_formats]

    base_output = output_dir_path / "output.sample"

    if "json" in export_formats:
        json_path = base_output.with_suffix(".json")
        export_to_json(aggregated, json_path)

    if "csv" in export_formats:
        csv_path = base_output.with_suffix(".csv")
        export_to_csv(aggregated, csv_path)

    if "excel" in export_formats or "xlsx" in export_formats:
        excel_path = base_output.with_suffix(".xlsx")
        export_to_excel(aggregated, excel_path)

    LOGGER.info("Processing complete.")

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Product Reviews Aggregator - collect and merge product reviews.",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        help="Path to input JSON file with tasks (default: data/inputs.sample.json)",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        help="Path to settings JSON file (default: src/config/settings.example.json)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        help="Directory where export files will be written (default from config).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args(argv)

if __name__ == "__main__":
    args = parse_args()
    run(
        input_file=args.input,
        config_file=args.config,
        output_dir=args.output_dir,
        verbose=args.verbose,
    )