import pytest
import spacy
from app.nlp import (
    TextTokenizer, simple_sentence_split, simple_word_tokenize,
    calculate_basic_stats, calculate_sentence_stats,
    calculate_lexical_metrics, calculate_readability,
    analyze_ngram_repetition, analyze_template_phrases,
    analyze_passive_voice, analyze_pos, analyze_punctuation,
    analyze_conjunctions, get_syntax_features,
    BasicStatistics, SentenceStatistics, LexicalMetrics,
    ReadabilityMetrics, NGramRepetition, TemplatePhraseMetrics,
    PassiveVoiceMetrics, POSDistribution, PunctuationDistribution,
    ConjunctionIndicators,
)


# Test fixtures
@pytest.fixture
def nlp():
    """Load spaCy model for tests."""
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        pytest.skip("spaCy model en_core_web_sm not installed")


@pytest.fixture
def tokenizer(nlp):
    return TextTokenizer(nlp)


# Test texts
EMPTY_TEXT = ""
ONE_SENTENCE = "This is a simple sentence."
MULTIPLE_SENTENCES = "This is the first sentence. This is the second sentence. And this is the third one."
PARAGRAPHS = "This is paragraph one.\n\nThis is paragraph two with more content.\n\nThird paragraph here."
REPEATED_WORDS = "The the the quick quick brown fox fox jumps jumps over over the the lazy lazy dog dog."
REPEATED_NGRAMS = "The cat sat on the mat. The cat sat on the mat. The cat sat on the mat."
TEMPLATE_PHRASES = "Moreover, furthermore, additionally, in conclusion, it is important to note that this is a test."
NUMBERS_TEXT = "The price is $19.99 and the quantity is 42. The rate is 3.14%."
PERCENTAGES_TEXT = "The increase was 25% and the decrease was 10.5%."
URLS_TEXT = "Visit https://example.com and http://test.org for more info."
PUNCTUATION_TEXT = "Hello! How are you? I'm fine... Really? Yes, absolutely!"
LONG_TEXT = """Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language. 
The goal is to program computers to process and analyze large amounts of natural language data. 
Challenges in natural language processing frequently involve speech recognition, natural language understanding, and natural language generation. 
Moreover, it is important to note that these challenges require sophisticated algorithms. 
Furthermore, researchers continue to develop new approaches. 
In conclusion, NLP remains a vibrant field of study."""


class TestTokenizer:
    """Test tokenization functions."""

    def test_simple_sentence_split(self):
        sentences = simple_sentence_split(ONE_SENTENCE)
        assert len(sentences) == 1
        assert sentences[0] == ONE_SENTENCE

        sentences = simple_sentence_split(MULTIPLE_SENTENCES)
        assert len(sentences) == 3

    def test_simple_word_tokenize(self):
        words = simple_word_tokenize(ONE_SENTENCE)
        assert "this" in words
        assert "is" in words
        assert "a" in words
        assert "simple" in words
        assert "sentence" in words

    def test_spacy_tokenizer(self, tokenizer):
        doc = tokenizer.tokenize(ONE_SENTENCE)
        assert len(doc) > 0

        words = tokenizer.get_words(doc)
        assert len(words) > 0

        sentences = tokenizer.get_sentences(doc)
        assert len(sentences) == 1

    def test_paragraphs(self, tokenizer):
        paragraphs = tokenizer.get_paragraphs(PARAGRAPHS)
        assert len(paragraphs) == 3


class TestBasicStatistics:
    """Test basic statistics calculation."""

    def test_empty_text(self):
        stats = calculate_basic_stats("", [], [], [], 0)
        assert stats.character_count == 0
        assert stats.word_count == 0
        assert stats.sentence_count == 0

    def test_one_sentence(self, nlp):
        doc = nlp(ONE_SENTENCE)
        words = [t.text.lower() for t in doc if t.is_alpha]
        sentences = [s.text.strip() for s in doc.sents]
        paragraphs = [ONE_SENTENCE]
        stats = calculate_basic_stats(ONE_SENTENCE, words, sentences, paragraphs, len(set(words)))
        assert stats.word_count == 5
        assert stats.sentence_count == 1
        assert stats.paragraph_count == 1

    def test_multiple_sentences(self, nlp):
        doc = nlp(MULTIPLE_SENTENCES)
        words = [t.text.lower() for t in doc if t.is_alpha]
        sentences = [s.text.strip() for s in doc.sents]
        paragraphs = [MULTIPLE_SENTENCES]
        stats = calculate_basic_stats(MULTIPLE_SENTENCES, words, sentences, paragraphs, len(set(words)))
        assert stats.sentence_count == 3
        assert stats.word_count > 0

    def test_paragraphs(self, nlp):
        doc = nlp(PARAGRAPHS)
        words = [t.text.lower() for t in doc if t.is_alpha]
        sentences = [s.text.strip() for s in doc.sents]
        paragraphs = [p.strip() for p in PARAGRAPHS.split("\n\n") if p.strip()]
        stats = calculate_basic_stats(PARAGRAPHS, words, sentences, paragraphs, len(set(words)))
        assert stats.paragraph_count == 3


class TestSentenceStatistics:
    """Test sentence statistics."""

    def test_empty(self):
        stats = calculate_sentence_stats([], [])
        assert stats.sentence_count == 0
        assert stats.mean_length == 0.0

    def test_single_sentence(self):
        stats = calculate_sentence_stats(["One sentence."], [3])
        assert stats.sentence_count == 1
        assert stats.min_length == 3
        assert stats.max_length == 3
        assert stats.mean_length == 3.0
        assert stats.median_length == 3.0

    def test_multiple_sentences(self):
        lengths = [5, 10, 15]
        stats = calculate_sentence_stats(["a b c d e.", "a b c d e f g h i j.", "a b c d e f g h i j k l m n o."], lengths)
        assert stats.sentence_count == 3
        assert stats.min_length == 5
        assert stats.max_length == 15
        assert stats.mean_length == 10.0
        assert stats.median_length == 10.0
        assert stats.std_dev > 0


class TestLexicalMetrics:
    """Test lexical diversity metrics."""

    def test_empty(self):
        metrics = calculate_lexical_metrics([], [], [])
        assert metrics.total_word_count == 0
        assert metrics.unique_word_count == 0
        assert metrics.type_token_ratio is None

    def test_repeated_words(self):
        words = ["the", "the", "the", "quick", "quick", "brown", "fox"]
        content = ["quick", "brown", "fox"]
        function = ["the", "the", "the"]
        metrics = calculate_lexical_metrics(words, content, function)
        assert metrics.total_word_count == 7
        assert metrics.unique_word_count == 4
        # TTR is rounded to 4 decimal places
        assert round(metrics.type_token_ratio, 4) == round(4/7, 4)
        assert len(metrics.most_repeated_words) > 0

    def test_diverse_text(self):
        words = ["unique", "words", "every", "single", "time"]
        content = words
        function = []
        metrics = calculate_lexical_metrics(words, content, function)
        assert metrics.type_token_ratio == 1.0
        assert metrics.hapax_legomena_ratio == 1.0


class TestReadability:
    """Test readability metrics."""

    def test_empty(self):
        metrics = calculate_readability("")
        assert metrics.flesch_reading_ease is None

    def test_simple_text(self):
        metrics = calculate_readability("This is a simple sentence.")
        assert metrics.flesch_reading_ease is not None
        assert metrics.flesch_kincaid_grade is not None

    def test_complex_text(self):
        metrics = calculate_readability(LONG_TEXT)
        # textstat may return None for some metrics on certain inputs
        # Just verify the function runs without error
        assert isinstance(metrics, ReadabilityMetrics)


class TestNGramRepetition:
    """Test n-gram repetition analysis."""

    def test_empty(self):
        result = analyze_ngram_repetition([])
        assert result.total_bigrams == 0
        assert result.total_trigrams == 0

    def test_repeated_bigrams(self):
        words = ["the", "cat", "sat", "the", "cat", "sat"]
        result = analyze_ngram_repetition(words)
        assert result.total_bigrams == 5
        # 3 unique bigrams: "the cat", "cat sat", "sat the"
        assert result.unique_bigrams == 3
        assert result.bigram_repetition_ratio > 0
        assert len(result.repeated_bigrams) == 2

    def test_repeated_trigrams(self):
        words = ["the", "cat", "sat", "the", "cat", "sat"]
        result = analyze_ngram_repetition(words)
        assert result.total_trigrams == 4
        # 3 unique trigrams: "the cat sat", "cat sat the", "sat the cat"
        assert result.unique_trigrams == 3
        assert result.trigram_repetition_ratio > 0


class TestTemplatePhrases:
    """Test template phrase detection."""

    def test_no_templates(self):
        result = analyze_template_phrases("This is a normal sentence without templates.")
        assert result.total_template_occurrences == 0
        assert result.template_phrase_density == 0.0

    def test_with_templates(self):
        result = analyze_template_phrases(TEMPLATE_PHRASES)
        assert result.total_template_occurrences > 0
        assert result.template_phrase_density > 0
        assert result.unique_templates_used > 0

    def test_custom_templates(self):
        custom = ["custom phrase", "another one"]
        result = analyze_template_phrases("This has a custom phrase and another one.", custom)
        assert result.total_template_occurrences == 2


class TestPassiveVoice:
    """Test passive voice detection."""

    def test_empty(self, nlp):
        doc = nlp("")
        result = analyze_passive_voice(doc)
        assert result.passive_sentences == 0
        assert result.total_sentences == 0

    def test_active_voice(self, nlp):
        doc = nlp("The cat chased the mouse.")
        result = analyze_passive_voice(doc)
        # May or may not detect passive depending on parser
        assert result.total_sentences == 1

    def test_passive_voice(self, nlp):
        doc = nlp("The mouse was chased by the cat.")
        result = analyze_passive_voice(doc)
        # Should detect passive
        assert result.total_sentences == 1


class TestPOSAnalysis:
    """Test POS analysis."""

    def test_pos_distribution(self, nlp):
        doc = nlp("The quick brown fox jumps.")
        result = analyze_pos(doc)
        assert result.total_tokens > 0
        assert "NOUN" in result.counts or "VERB" in result.counts

    def test_punctuation(self, nlp):
        doc = nlp(PUNCTUATION_TEXT)
        result = analyze_punctuation(doc)
        assert result.total_punctuation > 0

    def test_conjunctions(self, nlp):
        doc = nlp("And but or however therefore.")
        result = analyze_conjunctions(doc)
        assert result.total > 0

    def test_syntax_features(self, nlp):
        doc = nlp("The cat sat on the mat.")
        result = get_syntax_features(doc)
        assert "dependency_distribution" in result


class TestFullAnalysis:
    """Integration tests with full analyzer."""

    def test_analyze_short_text(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze("This is a test sentence.")
        assert result.basic_stats.word_count > 0
        assert result.sentence_stats.sentence_count == 1

    def test_analyze_long_text(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze(LONG_TEXT)
        assert result.basic_stats.word_count > 50
        assert result.sentence_stats.sentence_count > 5
        assert result.lexical_metrics.type_token_ratio is not None

    def test_analyze_with_numbers(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze(NUMBERS_TEXT)
        assert result.basic_stats.word_count > 0

    def test_analyze_with_percentages(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze(PERCENTAGES_TEXT)
        assert result.basic_stats.word_count > 0

    def test_analyze_with_urls(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze(URLS_TEXT)
        assert result.basic_stats.word_count > 0

    def test_analyze_punctuation(self, nlp):
        from app.services.analyzer import TextAnalyzer
        analyzer = TextAnalyzer(nlp)
        result = analyzer.analyze(PUNCTUATION_TEXT)
        assert result.punctuation_distribution.total_punctuation > 0


class TestSemanticCoherence:
    """Tests for the intra-text semantic coherence metric."""

    def test_coherent_text_scores_higher(self):
        from app.services.metrics import compute_semantic_coherence
        coherent = (
            "The research team studied the effects of sleep on memory. "
            "The memory study involved forty participants. "
            "These participants completed memory tasks each morning. "
            "The morning tasks measured recall accuracy."
        )
        score = compute_semantic_coherence(coherent)
        assert 0.0 <= score <= 100.0
        assert score > 50.0

    def test_disjoint_text_scores_lower(self):
        from app.services.metrics import compute_semantic_coherence
        coherent = (
            "The research team studied the effects of sleep on memory. "
            "The memory study involved forty participants. "
            "These participants completed memory tasks each morning."
        )
        disjoint = (
            "The research team studied the effects of sleep on memory. "
            "Bananas grow in tropical climates. "
            "Quantum entanglement defies classical intuition."
        )
        assert compute_semantic_coherence(coherent) > compute_semantic_coherence(disjoint)

    def test_short_text_neutral(self):
        from app.services.metrics import compute_semantic_coherence
        assert compute_semantic_coherence("One single sentence.") == 50.0

    def test_empty_text_neutral(self):
        from app.services.metrics import compute_semantic_coherence
        assert compute_semantic_coherence("") == 50.0

    def test_naturalness_score_is_deterministic(self):
        from app.services.analyzer import TextAnalyzer
        from app.services.metrics import calculate_naturalness_score
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            pytest.skip("spaCy model not installed")
        analyzer = TextAnalyzer(nlp)
        analysis = analyzer.analyze(LONG_TEXT)
        first = calculate_naturalness_score(analysis, LONG_TEXT)
        second = calculate_naturalness_score(analysis, LONG_TEXT)
        assert first.score == second.score
        assert 0.0 <= first.score <= 100.0
        # No component may be a bare constant placeholder
        assert len(set(first.components.values())) > 1


class TestReadabilityRobustness:
    """Readability must survive numbers, URLs and hyphenated words."""

    def test_plain_text(self):
        from app.nlp.readability import calculate_readability
        m = calculate_readability(
            "The cat sat on the mat. The dog ran to the park. Birds sang in the tree."
        )
        assert m.flesch_reading_ease is not None
        assert m.flesch_kincaid_grade is not None

    def test_text_with_numbers_and_percentages(self):
        from app.nlp.readability import calculate_readability
        m = calculate_readability(
            "The accuracy reached 94.7% in 2023 and the total was 1,250 units."
        )
        assert m.flesch_reading_ease is not None, "numbers must not nullify Flesch"

    def test_text_with_url(self):
        from app.nlp.readability import calculate_readability
        m = calculate_readability(
            "See https://example.com for details about the methodology."
        )
        assert m.flesch_reading_ease is not None, "URLs must not nullify Flesch"

    def test_text_with_hyphenated_words(self):
        from app.nlp.readability import calculate_readability
        m = calculate_readability(
            "This fast-changing environment requires a data-driven approach."
        )
        assert m.flesch_reading_ease is not None, "hyphens must not nullify Flesch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])