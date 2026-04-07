from rouge_score import rouge_scorer as _rouge_scorer


def rouge_l_score(prediction: str, reference: str) -> float:
    """Return the ROUGE-L F1 score between prediction and reference."""
    scorer = _rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    scores = scorer.score(reference, prediction)
    return float(scores["rougeL"].fmeasure)
