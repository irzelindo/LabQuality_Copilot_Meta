"""Regressions for line wrapping observed in real Meta responses."""
import pytest

from app.ai import validate_grounding
from app.schemas import RecommendationResult


def proposal(quote):
    return RecommendationResult.model_validate({
        "summary": "Fictional software test only.", "insufficient_evidence": False,
        "recommendations": [{"title": "Review the record", "justification": "Review the fictional document history.",
            "priority": "medium", "steps": ["Inspect the record."],
            "completion_criterion": "A different person reviews the record.", "finding_ids": ["f1"],
            "citations": [{"source_id": "d1", "quote": quote}]}]})


def context(content, allowed=None):
    return {"findings": [{"id": "f1", "criterion_code": "TEST-DOC",
                          "allowed_source_ids": ["d1"] if allowed is None else allowed}],
            "sources": [{"id": "d1", "criterion_codes": ["TEST-DOC"], "content": content}]}


def test_flattened_line_breaks_are_restored_to_the_exact_source_span():
    original = "A new revision must\n  be approved\tbefore use."
    result = proposal("A new revision must be approved before use.")
    validate_grounding(result, context("Fictional procedure. " + original + " Keep a record."))
    assert result.recommendations[0].citations[0].quote == original


@pytest.mark.parametrize("quote", [
    "A new revision must not be approved before use.",
    "A new revision MUST be approved before use.",
    "A new revision must be approved; before use.",
])
def test_changes_to_words_case_or_punctuation_remain_rejected(quote):
    with pytest.raises(ValueError, match="citação"):
        validate_grounding(proposal(quote), context("A new revision must\nbe approved before use."))


def test_matching_quote_does_not_override_the_allowed_sources():
    quote = "A new revision must be approved before use."
    with pytest.raises(ValueError, match="não se aplica"):
        validate_grounding(proposal(quote), context(quote, allowed=[]))
