"""
OlistIQ - Ingestion Pipeline Module
Acquires the Olist Brazilian E-Commerce dataset via KaggleHub,
validates the existence of all 9 expected CSV files, copies them to data/raw/,
and produces a dataset inventory report with row/column counts, schemas, and timestamps.
"""

import os
import shutil
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
import kagglehub
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OlistIQ.Ingestion")

EXPECTED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
    "olist_geolocation_dataset.csv",
]

def download_and_ingest(target_dir: str = "data/raw") -> dict:
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Initiating KaggleHub dataset download for 'olistbr/brazilian-ecommerce'...")
    download_start_time = datetime.now(timezone.utc).isoformat()
    
    # 1. Download dataset automatically via KaggleHub
    source_path_str = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
    source_path = Path(source_path_str)
    logger.info(f"KaggleHub resolved dataset download path: {source_path}")
    
    # 2. Discover files in downloaded folder
    found_files = [f.name for f in source_path.iterdir() if f.is_file() and f.name.endswith(".csv")]
    logger.info(f"Discovered {len(found_files)} CSV files in KaggleHub cache: {found_files}")
    
    # 3. Validate that all 9 expected files exist
    missing_files = [f for f in EXPECTED_FILES if f not in found_files]
    if missing_files:
        error_msg = f"Validation failed! Missing expected dataset files: {missing_files}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    logger.info("Validation successful: All 9 expected CSV files are present.")
    
    # 4. Copy files to data/raw/ without destructive overwrite of existing valid raw data
    inventory = {
        "dataset_name": "olistbr/brazilian-ecommerce",
        "download_timestamp_utc": download_start_time,
        "kagglehub_cache_path": str(source_path),
        "target_raw_directory": str(target_path.resolve()),
        "total_files": len(EXPECTED_FILES),
        "files": {}
    }
    
    for filename in EXPECTED_FILES:
        src_file = source_path / filename
        dest_file = target_path / filename
        
        if not dest_file.exists():
            shutil.copy2(src_file, dest_file)
            logger.info(f"Copied {filename} to {dest_file}")
        else:
            logger.info(f"File {filename} already exists in {target_dir}. Preserving raw source file.")
            
        # 5. Read file using Pandas to record row count, column count, data types, nulls
        file_size_mb = round(dest_file.stat().st_size / (1024 * 1024), 2)
        df = pd.read_csv(dest_file)
        
        col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        null_counts = {col: int(cnt) for col, cnt in df.isnull().sum().items()}
        
        inventory["files"][filename] = {
            "file_size_mb": file_size_mb,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": list(df.columns),
            "data_types": col_types,
            "missing_values": null_counts,
            "sample_head": df.head(2).to_dict(orient="records")
        }
        logger.info(f"Profiled {filename}: {len(df):,} rows, {len(df.columns)} cols, {file_size_mb} MB")

    # 6. Save inventory metadata
    inventory_json_path = target_path / "dataset_inventory.json"
    with open(inventory_json_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)
    logger.info(f"Dataset inventory saved to {inventory_json_path}")
    
    # 7. Generate markdown documentation
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = docs_dir / "dataset_inventory.md"
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# OlistIQ Dataset Inventory & Raw Validation Report\n\n")
        f.write(f"- **Dataset Source**: `olistbr/brazilian-ecommerce` (Kaggle)\n")
        f.write(f"- **Download Timestamp (UTC)**: `{inventory['download_timestamp_utc']}`\n")
        f.write(f"- **Source Cache**: `{inventory['kagglehub_cache_path']}`\n")
        f.write(f"- **Local Raw Target**: `{inventory['target_raw_directory']}`\n")
        f.write(f"- **Validated Expected Files**: {inventory['total_files']} / {len(EXPECTED_FILES)}\n\n")
        f.write("## File Summaries\n\n")
        f.write("| File Name | Rows | Columns | Size (MB) | Total Missing Values |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for fn, meta in inventory["files"].items():
            tot_missing = sum(meta["missing_values"].values())
            f.write(f"| `{fn}` | {meta['rows']:,} | {meta['columns']} | {meta['file_size_mb']} MB | {tot_missing:,} |\n")
        
        f.write("\n## Detailed Schema & Null Profile\n\n")
        for fn, meta in inventory["files"].items():
            f.write(f"### `{fn}`\n")
            f.write(f"Rows: **{meta['rows']:,}** | Columns: **{meta['columns']}** | Size: **{meta['file_size_mb']} MB**\n\n")
            f.write("| Column | Inferred Dtype | Missing Count | Null % |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")
            for col, dtype in meta["data_types"].items():
                m_cnt = meta["missing_values"][col]
                pct = round(100.0 * m_cnt / meta["rows"], 2) if meta["rows"] > 0 else 0.0
                f.write(f"| `{col}` | `{dtype}` | {m_cnt:,} | {pct}% |\n")
            f.write("\n")

    logger.info(f"Inventory markdown report generated at {md_path}")
    return inventory

if __name__ == "__main__":
    download_and_ingest()
