from pathlib import Path

from src.classify import classify_issue_response, load_categories


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ROOT / "data" / "categories.json"


def classify(issue, response):
    return classify_issue_response(issue, response, categories_path=CATEGORIES)


def test_noise_attachment_issue_is_classified():
    result = classify(
        "검사 중 노이즈가 많이 발생했고 전극 부착 상태가 불안정합니다",
        "패치 부착 상태 확인 및 재측정 안내",
    )

    assert result.recommended_category == "[사용자] 부착 불량 노이즈"
    assert "노이즈" in result.matched_keywords
    assert result.confidence > 0.45


def test_web_output_issue_is_classified():
    result = classify(
        "웹에서 결과지가 출력되지 않고 화면 버튼이 동작하지 않습니다",
        "브라우저 새로고침과 재로그인 안내",
    )

    assert result.recommended_category == "[웹] 관련 이슈"
    assert not result.needs_human_review


def test_eb_review_issue_is_classified():
    result = classify(
        "판독 결과 코멘트 확인 요청이고 EB팀 검토가 필요합니다",
        "분석 결과 확인 후 회신 안내",
    )

    assert result.recommended_category == "[EB팀] 판독 관련 요청"
    assert result.needs_human_review


def test_app_issue_is_classified():
    result = classify(
        "앱 업로드가 검사 도중 멈춤 상태이고 재실행해도 오류가 납니다",
        "앱 초기화와 네트워크 확인 후 다시 업로드 안내",
    )

    assert result.recommended_category == "[앱] 관련 이슈"
    assert "앱" in result.matched_keywords


def test_user_mistake_issue_is_classified():
    result = classify(
        "수검자가 장비를 임의로 탈착하고 검사를 일찍 종료했습니다",
        "잘못 사용한 가능성이 있어 재검 기준 안내",
    )

    assert result.recommended_category == "[사용자] 과실"


def test_low_evidence_returns_review_needed():
    result = classify("통화했습니다", "내용을 남겼습니다")

    assert result.recommended_category == "[검토 필요]"
    assert result.needs_human_review
    assert result.confidence <= 0.35


def test_categories_load_from_json():
    categories = load_categories(CATEGORIES)

    assert categories
    assert categories[0].name == "[CS] 사용 문의"
