from src.result_store import (
    append_classification_result,
    load_classification_results,
    update_latest_final_category,
)


def test_append_classification_result_creates_csv_with_expected_columns(tmp_path):
    csv_path = tmp_path / "classification_results.csv"

    append_classification_result(
        csv_path,
        {
            "created_at": "2026-07-02 16:30:00",
            "issue": "웹 결과지 출력이 안 됩니다",
            "response": "브라우저 새로고침 안내",
            "recommended_category": "[웹] 관련 이슈",
            "final_category": "[웹] 관련 이슈",
            "confidence": 0.82,
            "needs_human_review": False,
            "matched_keywords": "웹, 결과지, 브라우저",
        },
    )

    rows = load_classification_results(csv_path)

    assert len(rows) == 1
    assert rows[0]["issue"] == "웹 결과지 출력이 안 됩니다"
    assert rows[0]["final_category"] == "[웹] 관련 이슈"
    assert rows[0]["matched_keywords"] == "웹, 결과지, 브라우저"


def test_append_classification_result_appends_rows(tmp_path):
    csv_path = tmp_path / "classification_results.csv"

    append_classification_result(csv_path, {"issue": "앱 멈춤", "final_category": "[앱] 관련 이슈"})
    append_classification_result(csv_path, {"issue": "노이즈 발생", "final_category": "[사용자] 부착 불량 노이즈"})

    rows = load_classification_results(csv_path)

    assert [row["issue"] for row in rows] == ["앱 멈춤", "노이즈 발생"]


def test_update_latest_final_category_changes_most_recent_row(tmp_path):
    csv_path = tmp_path / "classification_results.csv"
    append_classification_result(csv_path, {"issue": "첫 번째", "final_category": "[앱] 관련 이슈"})
    append_classification_result(csv_path, {"issue": "두 번째", "final_category": "[검토 필요]"})

    update_latest_final_category(csv_path, "[웹] 관련 이슈")

    rows = load_classification_results(csv_path)
    assert rows[0]["final_category"] == "[앱] 관련 이슈"
    assert rows[1]["final_category"] == "[웹] 관련 이슈"
