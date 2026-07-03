from dataclasses import dataclass
import re


CUSTOMER_MARKERS = ("고객", "수검자", "병원", "문의자")
AGENT_MARKERS = ("상담사", "CS", "담당자", "안내")
MIN_CLEAR_LENGTH = 10


@dataclass(frozen=True)
class ExtractedIssueResponse:
    issue_text: str
    response_text: str
    needs_review: bool
    reason: str


def extract_issue_response(transcript_text: str) -> ExtractedIssueResponse:
    text = _clean(transcript_text)
    if not text:
        return ExtractedIssueResponse("", "", True, "전사문이 비어 있습니다.")

    issue_lines = []
    response_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        speaker, content = _split_speaker(line)
        if speaker and _matches_any(speaker, CUSTOMER_MARKERS):
            issue_lines.append(content)
        elif speaker and _matches_any(speaker, AGENT_MARKERS):
            response_lines.append(content)

    issue = " ".join(issue_lines).strip()
    response = " ".join(response_lines).strip()

    if not issue and not response:
        return ExtractedIssueResponse(
            text,
            "",
            True,
            "화자 구분이 없어 전체 전사문을 이슈 초안으로 넣었습니다.",
        )

    needs_review = len(issue) < MIN_CLEAR_LENGTH or not response
    reason = "이슈와 대응을 화자 라벨 기준으로 추출했습니다."
    if needs_review:
        reason = "추출 근거가 부족해 CS 담당자 확인이 필요합니다."

    return ExtractedIssueResponse(issue, response, needs_review, reason)


def _clean(text: str) -> str:
    return (text or "").strip()


def _split_speaker(line: str) -> tuple[str, str]:
    match = re.match(r"^\s*([^:：]{1,12})\s*[:：]\s*(.+)$", line)
    if not match:
        return "", line
    return match.group(1).strip(), match.group(2).strip()


def _matches_any(value: str, markers: tuple[str, ...]) -> bool:
    normalized = value.lower().replace(" ", "")
    return any(marker.lower().replace(" ", "") in normalized for marker in markers)
