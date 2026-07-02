import csv
from pathlib import Path
from typing import Dict, List


RESULT_COLUMNS = [
    "created_at",
    "issue",
    "response",
    "recommended_category",
    "final_category",
    "confidence",
    "needs_human_review",
    "matched_keywords",
]


def append_classification_result(csv_path, row: Dict[str, object]) -> None:
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()

    with path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow({column: row.get(column, "") for column in RESULT_COLUMNS})


def load_classification_results(csv_path) -> List[Dict[str, str]]:
    path = Path(csv_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def update_latest_final_category(csv_path, final_category: str) -> None:
    path = Path(csv_path)
    rows = load_classification_results(path)
    if not rows:
        return

    rows[-1]["final_category"] = final_category
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
