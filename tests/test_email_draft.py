from src.email_draft import build_email_draft


def test_builds_owner_email_draft():
    draft = build_email_draft(
        issue_text="웹에서 결과지가 출력되지 않습니다.",
        response_text="브라우저 새로고침과 재로그인을 안내했습니다.",
        category="[웹] 관련 이슈",
        responsible_owner="웹 담당",
        owner_email="web@example.com",
    )

    assert draft.to_email == "web@example.com"
    assert "[CS 이슈 공유]" in draft.subject
    assert "[웹] 관련 이슈" in draft.subject
    assert "웹에서 결과지가 출력" in draft.body
    assert "브라우저 새로고침" in draft.body


def test_missing_owner_email_creates_review_draft():
    draft = build_email_draft(
        issue_text="검토가 필요한 문의입니다.",
        response_text="담당자 확인 안내",
        category="[검토 필요]",
        responsible_owner="CS 리드",
        owner_email="",
    )

    assert draft.to_email == ""
    assert draft.needs_recipient_review is True
