import re
from typing import List


def clean_text(text: str) -> str:
    """Clean text for processing."""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    return text.strip()


def truncate_text(text: str, max_chars: int, suffix: str = "...") -> str:
    """Truncate text to maximum characters."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)].rstrip() + suffix


def count_words(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r'\b\w+\b', text))


def count_sentences(text: str) -> int:
    """Count sentences in text (simple heuristic)."""
    return len(re.findall(r'[.!?]+(?:\s+|$)', text))


def count_paragraphs(text: str) -> int:
    """Count paragraphs in text."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    return len(paragraphs)


def split_into_chunks(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    if len(words) <= max_chunk_size:
        return [text]

    chunks = []
    for i in range(0, len(words), max_chunk_size - overlap):
        chunk = ' '.join(words[i:i + max_chunk_size])
        chunks.append(chunk)
        if i + max_chunk_size >= len(words):
            break

    return chunks


def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
    """Extract key phrases using simple frequency analysis."""
    # Simple noun phrase extraction pattern
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    # Filter common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her',
        'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how',
        'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did',
        'man', 'oil', 'sit', 'use', 'way', 'been', 'call', 'come', 'could',
        'find', 'first', 'give', 'good', 'have', 'into', 'just', 'know', 'like',
        'look', 'made', 'make', 'more', 'most', 'much', 'must', 'over', 'part',
        'people', 'said', 'should', 'some', 'take', 'than', 'that', 'their',
        'them', 'then', 'there', 'these', 'they', 'think', 'this', 'time',
        'very', 'what', 'when', 'where', 'which', 'will', 'with', 'work',
        'would', 'year', 'your'
    }
    words = [w for w in words if w not in stop_words]

    from collections import Counter
    word_counts = Counter(words)

    return [word for word, _ in word_counts.most_common(max_phrases)]