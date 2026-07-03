from src.transcript_extract import extract_issue_response


def test_extracts_issue_and_response_from_labeled_transcript():
    transcript = """
    고객: 앱에서 업로드가 계속 멈춰요.
    상담사: 네트워크 상태 확인 후 앱을 재실행해 보시도록 안내했습니다.
    """

    result = extract_issue_response(transcript)

    assert "업로드" in result.issue_text
    assert "멈" in result.issue_text
    assert "네트워크" in result.response_text
    assert "재실행" in result.response_text
    assert result.needs_review is False


def test_short_unclear_transcript_needs_review():
    result = extract_issue_response("통화했습니다. 확인했습니다.")

    assert result.issue_text == "통화했습니다. 확인했습니다."
    assert result.response_text == ""
    assert result.needs_review is True
