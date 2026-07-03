from dataclasses import dataclass


@dataclass(frozen=True)
class EmailDraft:
    to_email: str
    subject: str
    body: str
    needs_recipient_review: bool


def build_email_draft(
    issue_text: str,
    response_text: str,
    category: str,
    responsible_owner: str,
    owner_email: str = "",
) -> EmailDraft:
    short_issue = _shorten(issue_text, 32)
    subject = f"[CS 이슈 공유] {category} - {short_issue}"
    body = "\n".join(
        [
            f"안녕하세요, {responsible_owner or '담당자'}님.",
            "",
            "아래 CS 이슈 확인 요청드립니다.",
            "",
            f"- 카테고리: {category}",
            f"- 책임 주체: {responsible_owner or '확인 필요'}",
            f"- 이슈 요약: {issue_text or '확인 필요'}",
            f"- CS 대응: {response_text or '확인 필요'}",
            "",
            "확인 후 회신 부탁드립니다.",
        ]
    )
    return EmailDraft(
        to_email=owner_email.strip(),
        subject=subject,
        body=body,
        needs_recipient_review=not bool(owner_email.strip()),
    )


def _shorten(text: str, limit: int) -> str:
    value = " ".join((text or "확인 필요").split())
    return value if len(value) <= limit else value[:limit].rstrip() + "..."
