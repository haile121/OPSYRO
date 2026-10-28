import re
from difflib import SequenceMatcher

from .models import QuestionCluster

STOP_WORDS = {"the", "and", "that", "this", "what", "when", "where", "why", "how", "does", "did", "is", "are", "was", "were", "a", "an", "to", "of", "in", "on", "it", "for", "with", "do", "can", "could", "would"}
ALIASES = {"tuning": "dial", "knob": "dial", "changes": "change", "changed": "change", "changing": "change", "frequencies": "frequency", "moving": "move", "moves": "move"}


def question_tokens(value: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", value.lower())
    return {ALIASES.get(word, word) for word in words if word not in STOP_WORDS and len(word) > 1}


def cluster_for_question(session, question: str, region_key: str):
    tokens = question_tokens(question)
    if not tokens:
        return None
    best = None
    best_score = 0.0
    for candidate in QuestionCluster.objects.filter(session=session):
        if candidate.region_key != region_key:
            continue
        previous = set(candidate.match_key.split())
        union = previous | tokens
        overlap = len(previous & tokens)
        score = overlap / len(union) if union else SequenceMatcher(None, " ".join(previous), " ".join(tokens)).ratio()
        if score >= 0.30 and score > best_score:
            best, best_score = candidate, score
    if best:
        return best
    match_key = " ".join(sorted(tokens))
    cluster, _ = QuestionCluster.objects.get_or_create(
        session=session,
        region_key=region_key,
        match_key=match_key,
        defaults={"label": question},
    )
    return cluster
