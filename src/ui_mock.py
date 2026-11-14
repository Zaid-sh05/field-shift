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
