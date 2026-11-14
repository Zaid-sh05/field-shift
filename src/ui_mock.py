"""Opt-in layout fixtures only. No field identities or scientific results."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MockPreview:
    is_mock: bool = True
    label: str = "MOCK — layout preview only / نموذج عرض تجريبي"
    card_slots: tuple = (None, None, None)
    months: tuple = (None,) * 12


def mock_preview() -> MockPreview:
    return MockPreview()


DEMO_LABEL = "DEMO DATA — NOT SCIENTIFIC RESULTS"


def demo_rotations():
    """Synthetic UI fixtures, unrelated to any selected real field or preferences.

    The January start is a DEMO layout convention, not an agricultural calendar.
    Scores and confidence are hand-written test values, never engine outputs.
    """
    sequences = (("Demo wheat", "Demo lentil"), ("Demo barley", "Demo chickpea"),
                 ("Demo oat", "Demo bean"))
    arabic = (("قمح تجريبي", "عدس تجريبي"), ("شعير تجريبي", "حمص تجريبي"),
              ("شوفان تجريبي", "فاصولياء تجريبية"))
    result = []
    for index, (sequence, sequence_ar) in enumerate(zip(sequences, arabic), 1):
        result.append({"id": f"demo_rotation_{index}", "name_ar": f"مثال تجريبي {index}",
                       "name_en": f"Synthetic example {index}", "sequence": list(sequence),
                       "sequence_ar": list(sequence_ar), "is_demo": True,
                       "score": (42, 65, 28)[index - 1],
                       "confidence": ("high", "medium", "low")[index - 1],
                       "calendar_start": 1,
                       "calendar": [sequence[0]] * 4 + [None] * 2 + [sequence[1]] * 4 + [None] * 2,
                       "calendar_ar": [sequence_ar[0]] * 4 + [None] * 2 + [sequence_ar[1]] * 4 + [None] * 2})
    return result
