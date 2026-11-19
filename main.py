"""
OlistIQ — E-Commerce Intelligence & Business Analytics Platform
Single Master Entry Point

Supported commands:
  python main.py --stage ingestion
  python main.py --stage cleaning
  python main.py --stage database
  python main.py --stage analytics
  python main.py --stage exports
  python main.py --stage all
"""

import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from src.ingestion.download import download_and_ingest
from src.processing.transform import clean_and_transform
from src.database.loader import get_database_engine, run_migrations, load_star_schema
from src.analytics.engine import run_all_analytics
from src.analytics.sql_runner import run_sql_analytics
from src.analytics.generate_powerbi_pbip import generate_powerbi_project
from src.analytics.generate_tableau_workbook import generate_tableau_workbook
from bi.looker.generate_looker_specs import generate_looker_specifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OlistIQ.Main")

def stage_ingestion():
    logger.info("=== STAGE 1: INGESTION (KaggleHub Automated Pull) ===")
    res = download_and_ingest()
    logger.info(f"Ingestion verified: {res['total_files']} files acquired.")
    return res

def stage_cleaning():
    logger.info("=== STAGE 2: CLEANING & DIMENSIONAL TRANSFORMATION ===")
    res = clean_and_transform()
    logger.info(f"Transformation complete: {len(res)} star schema tables generated.")
    return res

def stage_database():
    logger.info("=== STAGE 3: DATABASE MIGRATION & BULK LOADING ===")
    engine, dialect = get_database_engine()
    run_migrations(engine, dialect)
    res = load_star_schema(engine, dialect)
    logger.info(f"Database loading verified: {len(res)} tables loaded ({dialect}).")
    return res

def stage_analytics():
    logger.info("=== STAGE 4: ADVANCED SQL & PYTHON ANALYTICS ===")
    sql_res = run_sql_analytics()
    py_res = run_all_analytics()
    logger.info("Analytics complete: SQL analytical views and Python statistical modules executed.")
    return {"sql": sql_res, "python": py_res}

def stage_exports():
    logger.info("=== STAGE 5: BI ASSET GENERATION & EXPORTS ===")
    pb_res = generate_powerbi_project()
    tw_res = generate_tableau_workbook()
    lk_res = generate_looker_specifications()
    logger.info("BI asset generation complete (Power BI PBIP, Tableau TWB, Looker Studio JSON).")
    return {"powerbi": pb_res, "tableau": str(tw_res), "looker": str(lk_res)}

def run_all():
    start_time = datetime.now(timezone.utc)
    logger.info("=== STARTING COMPLETE OLISTIQ REPRODUCIBLE END-TO-END PIPELINE ===")
    
    stage_ingestion()
    stage_cleaning()
    stage_database()
    stage_analytics()
    stage_exports()
    
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(f"=== OLISTIQ PIPELINE COMPLETED SUCCESSFULLY IN {duration:.2f} SECONDS ===")

def main():
    parser = argparse.ArgumentParser(description="OlistIQ Master Pipeline CLI")
    parser.add_argument(
        "--stage",
        choices=["ingestion", "cleaning", "database", "analytics", "exports", "all"],
        default="all",
        help="Specify the pipeline stage to execute."
    )
    args = parser.parse_args()
    
    try:
        if args.stage == "ingestion":
            stage_ingestion()
        elif args.stage == "cleaning":
            stage_cleaning()
        elif args.stage == "database":
            stage_database()
        elif args.stage == "analytics":
            stage_analytics()
        elif args.stage == "exports":
            stage_exports()
        elif args.stage == "all":
            run_all()
    except Exception as e:
        logger.error(f"Pipeline execution failed at stage '{args.stage}': {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
