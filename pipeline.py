"""
Batch pipeline for ETF candidate evaluation.

Usage:
    python main_grader.py --batch --csv input.csv
    python main_grader.py --batch --csv input.csv --output-dir output

The pipeline:
  1. Optionally syncs CVs from Google Drive (if GOOGLE_DRIVE_FOLDER_ID is set in .env).
  2. Filters candidates to Europe-only (OR logic: current location / university / employer).
  3. Grades eligible candidates with Grader.grade_applicant().
  4. Writes status + grades back to the CSV after every candidate (crash-safe).
  5. Logs per-candidate output to output/logs/<name>.log.

Status values written to the 'status' column:
  pending          — not yet processed (initial state)
  processing       — currently being processed (set before starting)
  done             — grading complete
  failed           — an exception occurred (see error_message column)
  rejected_europe  — did not pass the Europe eligibility filter
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_REJECTED = "rejected_europe"

# Columns added/managed by the pipeline
PIPELINE_COLUMNS = {
    "status": STATUS_PENDING,
    "grade_Education": None,
    "grade_Community": None,
    "grade_HackProject": None,
    "grade_Research": None,
    "grade_Startup": None,
    "trust_score": None,
    "europe_reason": None,
    "chart_path": None,
    "error_message": None,
    "processed_at": None,
}


class BatchPipeline:
    def __init__(self, csv_path: str, output_dir: str = "output"):
        self.csv_path = csv_path
        self.output_dir = output_dir
        self.logs_dir = os.path.join(output_dir, "logs")
        self.cvs_dir = "cvs"

    def _load_or_initialize_csv(self) -> pd.DataFrame:
        """Load CSV and add missing pipeline columns with default values."""
        df = pd.read_csv(self.csv_path)
        for col, default in PIPELINE_COLUMNS.items():
            if col not in df.columns:
                df[col] = default
        # Rows with no status yet → mark as pending
        df["status"] = df["status"].fillna(STATUS_PENDING)
        return df

    def _save_progress(self, df: pd.DataFrame) -> None:
        """Write the full DataFrame back to CSV immediately."""
        df.to_csv(self.csv_path, index=False)

    def _setup_logger(self, name: str) -> logging.Logger:
        """Create a per-candidate logger writing to output/logs/<name>.log and stdout."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        log_path = os.path.join(self.logs_dir, f"{safe_name}.log")

        logger = logging.getLogger(f"candidate.{safe_name}")
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)

        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        fh.setFormatter(fmt)
        sh.setFormatter(fmt)

        logger.addHandler(fh)
        logger.addHandler(sh)
        return logger

    def _match_cv_to_row(self, df: pd.DataFrame, downloaded_paths: list) -> pd.DataFrame:
        """
        For newly downloaded CVs, try to update the uploadResume column in df
        by matching filename substrings against candidate first/last names.
        Best-effort: skips rows where no confident match is found.
        """
        for local_path in downloaded_paths:
            filename = os.path.basename(local_path).lower()
            for idx, row in df.iterrows():
                first = str(row.get("firstName", "")).lower()
                last = str(row.get("lastName", "")).lower()
                if first and last and first in filename and last in filename:
                    df.at[idx, "uploadResume"] = local_path
                    break
                # Fallback: just last name
                elif last and len(last) > 3 and last in filename:
                    if pd.isna(df.at[idx, "uploadResume"]) or str(df.at[idx, "uploadResume"]).startswith("http"):
                        df.at[idx, "uploadResume"] = local_path
        return df

    def run(self) -> None:
        """Main entry point. Process all pending candidates sequentially."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.cvs_dir, exist_ok=True)

        root_logger = self._setup_logger("pipeline")
        root_logger.info(f"BatchPipeline started. CSV: {self.csv_path}")

        df = self._load_or_initialize_csv()

        # Step 1: Sync CVs from Google Drive if configured
        drive_folder = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
        if drive_folder:
            root_logger.info("Google Drive folder detected — syncing CVs...")
            try:
                from drive_downloader import get_downloader_from_env
                downloader = get_downloader_from_env()
                if downloader:
                    downloader.authenticate()
                    downloaded = downloader.sync_folder(self.cvs_dir)
                    if downloaded:
                        df = self._match_cv_to_row(df, downloaded)
                        self._save_progress(df)
            except Exception as e:
                root_logger.warning(f"Drive sync failed: {e}. Continuing with local files.")

        # Step 2: Load shared resources
        root_logger.info("Loading world rankings for Europe filter...")
        world_df = pd.read_csv("average_ranking_with_region.csv")

        from europe_filter import EuropeFilter
        europe_filter = EuropeFilter(world_df)

        root_logger.info("Initializing Grader (Selenium + Ollama)...")
        from grader import Grader
        from visualizer import plot_pentagram
        grader = Grader()

        # Step 3: Process pending rows
        pending_mask = df["status"] == STATUS_PENDING
        pending_count = pending_mask.sum()
        root_logger.info(f"{pending_count} candidate(s) pending.")

        for idx in df[pending_mask].index:
            row = df.loc[idx]
            first = str(row.get("firstName", "")).strip()
            last = str(row.get("lastName", "")).strip()
            name = f"{first} {last}".strip() or f"candidate_{idx}"

            logger = self._setup_logger(name)
            logger.info(f"--- Processing: {name} (row {idx}) ---")

            # Mark as processing immediately
            df.at[idx, "status"] = STATUS_PROCESSING
            self._save_progress(df)

            try:
                # Step 3a: Pre-scrape LinkedIn to populate cache for Europe filter
                linkedin_url = row.get("linkedinUrl", "")
                linkedin_data = {}
                if isinstance(linkedin_url, str) and "linkedin.com" in linkedin_url:
                    logger.info("Pre-scraping LinkedIn for Europe filter...")
                    linkedin_data = grader._scrape_linkedin(linkedin_url)

                # Step 3b: Europe filter
                eligible, reason = europe_filter.is_eligible(row, linkedin_data)
                df.at[idx, "europe_reason"] = reason

                if not eligible:
                    logger.info(f"REJECTED (Europe filter): {reason}")
                    df.at[idx, "status"] = STATUS_REJECTED
                    df.at[idx, "processed_at"] = datetime.utcnow().isoformat()
                    self._save_progress(df)
                    continue

                logger.info(f"Europe filter: {reason}")

                # Step 3c: Grade
                logger.info("Grading candidate...")
                grades = grader.grade_applicant(row)

                # Step 3d: Write results
                df.at[idx, "grade_Education"] = grades.get("Education")
                df.at[idx, "grade_Community"] = round(grades.get("Community", 0), 1)
                df.at[idx, "grade_HackProject"] = round(grades.get("Hack/Project", 0), 1)
                df.at[idx, "grade_Research"] = round(grades.get("Research", 0), 1)
                df.at[idx, "grade_Startup"] = round(grades.get("Startup", 0), 1)

                verification = grades.get("Verification", {})
                df.at[idx, "trust_score"] = verification.get("trust_score")

                # Step 3e: Generate chart
                safe_name = name.replace(" ", "_")
                chart_path = os.path.join(self.output_dir, f"grade_{safe_name}.png")
                plot_pentagram(grades, chart_path)
                df.at[idx, "chart_path"] = chart_path

                df.at[idx, "status"] = STATUS_DONE
                df.at[idx, "processed_at"] = datetime.utcnow().isoformat()
                logger.info(
                    f"Done. Education={grades.get('Education')} "
                    f"Community={round(grades.get('Community', 0), 1)} "
                    f"Hack={round(grades.get('Hack/Project', 0), 1)} "
                    f"Research={round(grades.get('Research', 0), 1)} "
                    f"Startup={round(grades.get('Startup', 0), 1)} "
                    f"Trust={verification.get('trust_score')}"
                )

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                logger.error(f"FAILED: {error_msg}")
                logger.debug(traceback.format_exc())
                df.at[idx, "status"] = STATUS_FAILED
                df.at[idx, "error_message"] = error_msg
                df.at[idx, "processed_at"] = datetime.utcnow().isoformat()

            finally:
                self._save_progress(df)

        done_count = (df["status"] == STATUS_DONE).sum()
        rejected_count = (df["status"] == STATUS_REJECTED).sum()
        failed_count = (df["status"] == STATUS_FAILED).sum()
        root_logger.info(
            f"Pipeline finished. Done: {done_count}, Rejected (Europe): {rejected_count}, Failed: {failed_count}"
        )
