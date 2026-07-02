import json

from openpyxl import Workbook

from src.sample_data import load_sample_cases, load_synthetic_excel_cases


def test_load_sample_cases_reads_json_fallback(tmp_path):
    sample_path = tmp_path / "sample_cases.json"
    sample_path.write_text(
        json.dumps(
            [
                {
                    "title": "가상 샘플",
                    "issue_text": "웹 화면 버튼 문의",
                    "response_text": "브라우저 새로고침 안내",
                    "expected_category": "[웹] 관련 이슈",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    cases = load_sample_cases(sample_json_path=sample_path, synthetic_excel_path=tmp_path / "missing.xlsx")

    assert cases[0]["title"] == "가상 샘플"
    assert cases[0]["expected_category"] == "[웹] 관련 이슈"


def test_load_synthetic_excel_cases_reads_issue_response_category(tmp_path):
    workbook_path = tmp_path / "synthetic.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "2026"
    sheet.append(["날짜", "병원명", "이슈", "대응", "_x0008_카테고리2026"])
    sheet.append(["2026-01-01", "가상병원 001", "앱 업로드 멈춤", "앱 재실행 안내", "[앱] 관련 이슈"])
    workbook.save(workbook_path)

    cases = load_synthetic_excel_cases(workbook_path, max_cases=1)

    assert cases == [
        {
            "title": "[앱] 관련 이슈 샘플 1",
            "issue_text": "앱 업로드 멈춤",
            "response_text": "앱 재실행 안내",
            "expected_category": "[앱] 관련 이슈",
        }
    ]
