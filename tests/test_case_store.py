from src.case_store import init_case_store, list_reviewed_cases, save_reviewed_case


def test_save_and_list_reviewed_cases(tmp_path):
    db_path = tmp_path / "cases.db"
    init_case_store(db_path)

    case_id = save_reviewed_case(
        db_path,
        {
            "transcript_text": "고객: 앱 업로드가 멈춰요.",
            "issue_text": "앱 업로드가 멈춤",
            "response_text": "앱 재실행 안내",
            "recommended_category": "[앱] 관련 이슈",
            "final_category": "[앱] 관련 이슈",
            "responsible_owner": "앱 담당",
            "review_status": "reviewed",
            "reviewer": "CS",
            "internal_note": "시험 저장",
        },
    )

    rows = list_reviewed_cases(db_path)

    assert case_id == 1
    assert len(rows) == 1
    assert rows[0]["issue_text"] == "앱 업로드가 멈춤"
    assert rows[0]["final_category"] == "[앱] 관련 이슈"
