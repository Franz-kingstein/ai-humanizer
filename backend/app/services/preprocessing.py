import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from app.models.schemas import Warning


@dataclass
class ContentPreservationResult:
    """Result of content preservation checks."""
    numbers_match: bool
    percentages_match: bool
    dates_match: bool
    urls_match: bool
    warnings: List[Warning]
    details: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "numbers_match": self.numbers_match,
            "percentages_match": self.percentages_match,
            "dates_match": self.dates_match,
            "urls_match": self.urls_match,
            "warnings": [w.model_dump() for w in self.warnings],
            "details": self.details,
        }


# Regex patterns for content extraction
NUMBER_PATTERN = re.compile(r'\b\d+(?:[.,]\d+)?\b')
PERCENTAGE_PATTERN = re.compile(r'\b\d+(?:[.,]\d+)?\s*%')
DATE_PATTERNS = [
    re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),  # MM/DD/YYYY or DD/MM/YYYY
    re.compile(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'),     # YYYY/MM/DD
    re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', re.IGNORECASE),
    re.compile(r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b', re.IGNORECASE),
]
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


def extract_numbers(text: str) -> List[str]:
    """Extract all numbers from text."""
    return NUMBER_PATTERN.findall(text)


def extract_percentages(text: str) -> List[str]:
    """Extract all percentages from text."""
    return PERCENTAGE_PATTERN.findall(text)


def extract_dates(text: str) -> List[str]:
    """Extract all dates from text."""
    dates = []
    for pattern in DATE_PATTERNS:
        dates.extend(pattern.findall(text))
    return dates


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text (trailing sentence punctuation stripped)."""
    urls = URL_PATTERN.findall(text)
    # Strip trailing punctuation that belongs to the sentence, not the URL.
    return [u.rstrip(".,;:!?)\"'") for u in urls]


def normalize_number(num: str) -> str:
    """Normalize number for comparison (remove commas, standardize decimal)."""
    return num.replace(',', '').replace(' ', '')


def normalize_percentage(pct: str) -> str:
    """Normalize percentage for comparison."""
    return pct.replace(',', '').replace(' ', '').upper()


def check_content_preservation(original: str, rewritten: str) -> ContentPreservationResult:
    """Check if important content is preserved between original and rewritten text."""
    warnings = []
    details = {}

    # Numbers
    orig_numbers = [normalize_number(n) for n in extract_numbers(original)]
    rew_numbers = [normalize_number(n) for n in extract_numbers(rewritten)]

    numbers_match = True
    missing_numbers = []
    extra_numbers = []

    orig_set = set(orig_numbers)
    rew_set = set(rew_numbers)

    if orig_set != rew_set:
        numbers_match = False
        missing_numbers = list(orig_set - rew_set)
        extra_numbers = list(rew_set - orig_set)

        if missing_numbers:
            warnings.append(Warning(
                type="missing_numbers",
                message=f"Numbers missing in rewritten text: {missing_numbers}",
                severity="warning"
            ))
        if extra_numbers:
            warnings.append(Warning(
                type="extra_numbers",
                message=f"Unexpected numbers in rewritten text: {extra_numbers}",
                severity="warning"
            ))

    details["numbers"] = {
        "original": orig_numbers,
        "rewritten": rew_numbers,
        "missing": missing_numbers,
        "extra": extra_numbers,
    }

    # Percentages
    orig_pcts = [normalize_percentage(p) for p in extract_percentages(original)]
    rew_pcts = [normalize_percentage(p) for p in extract_percentages(rewritten)]

    percentages_match = True
    missing_pcts = []
    extra_pcts = []

    orig_pct_set = set(orig_pcts)
    rew_pct_set = set(rew_pcts)

    if orig_pct_set != rew_pct_set:
        percentages_match = False
        missing_pcts = list(orig_pct_set - rew_pct_set)
        extra_pcts = list(rew_pct_set - orig_pct_set)

        if missing_pcts:
            warnings.append(Warning(
                type="missing_percentages",
                message=f"Percentages missing in rewritten text: {missing_pcts}",
                severity="warning"
            ))
        if extra_pcts:
            warnings.append(Warning(
                type="extra_percentages",
                message=f"Unexpected percentages in rewritten text: {extra_pcts}",
                severity="warning"
            ))

    details["percentages"] = {
        "original": orig_pcts,
        "rewritten": rew_pcts,
        "missing": missing_pcts,
        "extra": extra_pcts,
    }

    # Dates
    orig_dates = extract_dates(original)
    rew_dates = extract_dates(rewritten)

    dates_match = True
    missing_dates = []
    extra_dates = []

    orig_date_set = set(orig_dates)
    rew_date_set = set(rew_dates)

    if orig_date_set != rew_date_set:
        dates_match = False
        missing_dates = list(orig_date_set - rew_date_set)
        extra_dates = list(rew_date_set - orig_date_set)

        if missing_dates:
            warnings.append(Warning(
                type="missing_dates",
                message=f"Dates missing in rewritten text: {missing_dates}",
                severity="warning"
            ))
        if extra_dates:
            warnings.append(Warning(
                type="extra_dates",
                message=f"Unexpected dates in rewritten text: {extra_dates}",
                severity="warning"
            ))

    details["dates"] = {
        "original": orig_dates,
        "rewritten": rew_dates,
        "missing": missing_dates,
        "extra": extra_dates,
    }

    # URLs
    orig_urls = extract_urls(original)
    rew_urls = extract_urls(rewritten)

    urls_match = True
    missing_urls = []
    extra_urls = []

    orig_url_set = set(orig_urls)
    rew_url_set = set(rew_urls)

    if orig_url_set != rew_url_set:
        urls_match = False
        missing_urls = list(orig_url_set - rew_url_set)
        extra_urls = list(rew_url_set - orig_url_set)

        if missing_urls:
            warnings.append(Warning(
                type="missing_urls",
                message=f"URLs missing in rewritten text: {missing_urls}",
                severity="warning"
            ))
        if extra_urls:
            warnings.append(Warning(
                type="extra_urls",
                message=f"Unexpected URLs in rewritten text: {extra_urls}",
                severity="warning"
            ))

    details["urls"] = {
        "original": orig_urls,
        "rewritten": rew_urls,
        "missing": missing_urls,
        "extra": extra_urls,
    }

    return ContentPreservationResult(
        numbers_match=numbers_match,
        percentages_match=percentages_match,
        dates_match=dates_match,
        urls_match=urls_match,
        warnings=warnings,
        details=details,
    )