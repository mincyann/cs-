import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .schema import CategoryDefinition, CategoryScore, ClassificationResult


DEFAULT_CATEGORIES_PATH = Path(__file__).resolve().parents[1] / "data" / "categories.json"
REVIEW_CATEGORY = "[검토 필요]"
ISSUE_WEIGHT = 2.0
RESPONSE_WEIGHT = 1.0
MIN_SCORE = 2.0
AMBIGUOUS_MARGIN = 1.5
REVIEW_SIGNALS = ["검토", "확인 필요", "담당자 확인", "복합", "동시에"]


def load_categories(categories_path=DEFAULT_CATEGORIES_PATH) -> List[CategoryDefinition]:
    path = Path(categories_path)
    with path.open("r", encoding="utf-8") as file:
        raw_categories = json.load(file)

    return [
        CategoryDefinition(
            name=item["name"],
            description=item.get("description", ""),
            keywords=list(item.get("keywords", [])),
        )
        for item in raw_categories
    ]


def classify_issue_response(
    issue_text: str,
    response_text: str,
    categories_path=DEFAULT_CATEGORIES_PATH,
) -> ClassificationResult:
    categories = load_categories(categories_path)
    scores = _score_categories(issue_text, response_text, categories)
    ranked = sorted(scores, key=lambda item: item.score, reverse=True)

    review_signal_matches = _find_review_signals(issue_text, response_text)
    if not ranked or ranked[0].score < MIN_SCORE:
        return _review_result(ranked, review_signal_matches)

    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    margin = best.score - (second.score if second else 0.0)
    ambiguous = second is not None and second.score > 0 and margin <= AMBIGUOUS_MARGIN
    needs_review = ambiguous or bool(review_signal_matches)

    confidence = _confidence(best.score, margin, needs_review)
    reason = _reason(best, second, margin, review_signal_matches, ambiguous)

    return ClassificationResult(
        recommended_category=best.category,
        confidence=confidence,
        reason=reason,
        needs_human_review=needs_review,
        matched_keywords=best.matched_keywords,
        scores={score.category: score.score for score in ranked},
    )


def _score_categories(
    issue_text: str,
    response_text: str,
    categories: Sequence[CategoryDefinition],
) -> List[CategoryScore]:
    issue_normalized = _normalize(issue_text)
    response_normalized = _normalize(response_text)
    category_scores = []

    for category in categories:
        if category.name == REVIEW_CATEGORY:
            continue

        issue_matches = _matched_keywords(issue_normalized, category.keywords)
        response_matches = _matched_keywords(response_normalized, category.keywords)
        score = len(issue_matches) * ISSUE_WEIGHT + len(response_matches) * RESPONSE_WEIGHT
        matched = _unique(issue_matches + response_matches)

        category_scores.append(
            CategoryScore(
                category=category.name,
                score=score,
                matched_keywords=matched,
                issue_matches=issue_matches,
                response_matches=response_matches,
            )
        )

    return category_scores


def _matched_keywords(text: str, keywords: Iterable[str]) -> List[str]:
    matches = []
    for keyword in keywords:
        normalized_keyword = _normalize(keyword)
        if normalized_keyword and normalized_keyword in text:
            matches.append(keyword)
    return matches


def _find_review_signals(issue_text: str, response_text: str) -> List[str]:
    text = _normalize(issue_text + " " + response_text)
    return [signal for signal in REVIEW_SIGNALS if _normalize(signal) in text]


def _review_result(
    ranked: Sequence[CategoryScore],
    review_signal_matches: Sequence[str],
) -> ClassificationResult:
    scores = {score.category: score.score for score in ranked}
    reason = "분류 근거가 부족해 사람이 최종 검토해야 합니다."
    matched_keywords = []

    if ranked and ranked[0].matched_keywords:
        matched_keywords = ranked[0].matched_keywords
        reason = (
            f"가장 높은 후보는 {ranked[0].category}이지만 "
            f"점수 {ranked[0].score:.1f}로 기준보다 낮습니다."
        )

    if review_signal_matches:
        reason += f" 검토 신호({', '.join(review_signal_matches)})가 포함되어 있습니다."

    return ClassificationResult(
        recommended_category=REVIEW_CATEGORY,
        confidence=0.2 if not matched_keywords else 0.35,
        reason=reason,
        needs_human_review=True,
        matched_keywords=matched_keywords,
        scores=scores,
    )


def _reason(
    best: CategoryScore,
    second: CategoryScore,
    margin: float,
    review_signal_matches: Sequence[str],
    ambiguous: bool,
) -> str:
    issue_part = _format_matches(best.issue_matches)
    response_part = _format_matches(best.response_matches)
    pieces = [
        f"{best.category} 키워드가 가장 많이 매칭되었습니다.",
        f"이슈 매칭: {issue_part}.",
        f"대응 매칭: {response_part}.",
    ]

    if second and second.score > 0:
        pieces.append(f"2순위는 {second.category}이며 점수 차이는 {margin:.1f}입니다.")
    if ambiguous:
        pieces.append("1순위와 2순위 점수 차이가 작아 사람 검토를 권장합니다.")
    if review_signal_matches:
        pieces.append(f"검토 신호({', '.join(review_signal_matches)})가 포함되어 있습니다.")

    return " ".join(pieces)


def _confidence(score: float, margin: float, needs_review: bool) -> float:
    evidence = min(score / 8.0, 1.0) * 0.75
    separation = min(max(margin, 0.0) / 4.0, 1.0) * 0.25
    confidence = evidence + separation
    if needs_review:
        confidence = min(confidence, 0.72)
    return round(max(0.0, min(confidence, 1.0)), 2)


def _format_matches(matches: Sequence[str]) -> str:
    return ", ".join(matches) if matches else "없음"


def _normalize(text: str) -> str:
    return (text or "").lower().replace(" ", "")


def _unique(items: Sequence[str]) -> List[str]:
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
