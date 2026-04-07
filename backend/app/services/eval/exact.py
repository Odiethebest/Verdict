import string


def exact_match(prediction: str, reference: str) -> bool:
    """Return True if prediction exactly equals reference."""
    return prediction == reference


def normalized_match(prediction: str, reference: str) -> bool:
    """Return True after lowercasing and stripping punctuation from both strings."""

    def normalize(text: str) -> str:
        text = text.lower().strip()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return " ".join(text.split())

    return normalize(prediction) == normalize(reference)
