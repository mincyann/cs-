from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class CategoryDefinition:
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CategoryScore:
    category: str
    score: float
    matched_keywords: List[str]
    issue_matches: List[str]
    response_matches: List[str]


@dataclass(frozen=True)
class ClassificationResult:
    recommended_category: str
    confidence: float
    reason: str
    needs_human_review: bool
    matched_keywords: List[str]
    scores: Dict[str, float] = field(default_factory=dict)
