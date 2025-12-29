"""
🧠 MODUŁ PRZETWARZANIA JĘZYKA NATURALNEGO (NLP)
==============================================

Zaawansowany procesor NLP oparty na spaCy dla analizy tekstu,
ekstrakcji encji, analizy sentymentu i innych zadań językowych.

Autor: Zaawansowany System Kognitywny ahui69
Data: 19 października 2025
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import time

import spacy
from spacy.lang.pl import Polish
from spacy.lang.en import English

from .config import *
from .helpers import log_info, log_error, log_warning

@dataclass
class NLPAnalysisResult:
    """Wynik analizy NLP tekstu"""
    text: str
    language: str
    tokens: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]
    key_phrases: List[str]
    pos_tags: List[Dict[str, str]]
    dependencies: List[Dict[str, Any]]
    readability_score: float
    processing_time: float

@dataclass
class Entity:
    """Encja nazwana"""
    text: str
    label: str
    start: int
    end: int
    confidence: float

@dataclass
class SentimentAnalysis:
    """Analiza sentymentu"""
    polarity: float  # -1 do 1
    subjectivity: float  # 0 do 1
    emotions: Dict[str, float]
    intensity: float

class NLPProcessor:
    """
    🧠 Zaawansowany Procesor NLP oparty na spaCy

    Funkcjonalności:
    - Tokenizacja i lematyzacja
    - Ekstrakcja encji nazwanych (NER)
    - Analiza części mowy (POS tagging)
    - Analiza zależności składniowych
    - Ekstrakcja fraz kluczowych
    - Analiza sentymentu
    - Wykrywanie języka
    - Ocena czytelności tekstu
    """

    def __init__(self):
        self.models = {}
        self._load_models()

        # Cache dla wyników analizy
        self.analysis_cache = {}
        self.cache_max_size = 1000

        # Statystyki przetwarzania
        self.stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "processing_times": [],
            "language_distribution": defaultdict(int)
        }

        log_info("[NLP_PROCESSOR] Procesor NLP zainicjalizowany")

    def _load_models(self):
        """Ładuje modele językowe spaCy"""
        try:
            # Model polski
            self.models['pl'] = spacy.load('pl_core_news_sm')
            log_info("[NLP_PROCESSOR] Załadowano model polski: pl_core_news_sm")

            # Model angielski jako fallback
            self.models['en'] = spacy.load('en_core_web_sm')
            log_info("[NLP_PROCESSOR] Załadowano model angielski: en_core_web_sm")

        except OSError as e:
            log_error(f"[NLP_PROCESSOR] Błąd ładowania modeli spaCy: {e}")
            # Fallback do podstawowych modeli
            self.models['pl'] = Polish()
            self.models['en'] = English()
            log_warning("[NLP_PROCESSOR] Używam podstawowych modeli językowych")

    def _detect_language(self, text: str) -> str:
        """Wykrywa język tekstu"""
        # Prosta heurystyka językowa
        polish_chars = set('ąćęłńóśźż')
        english_chars = set('abcdefghijklmnopqrstuvwxyz')

        text_lower = text.lower()
        polish_count = sum(1 for char in text_lower if char in polish_chars)
        english_count = sum(1 for char in text_lower if char in english_chars)

        # Jeśli więcej polskich znaków - polski
        if polish_count > english_count * 0.1:
            return 'pl'

        # Domyślnie angielski
        return 'en'

    async def analyze_text(self, text: str, use_cache: bool = True) -> NLPAnalysisResult:
        """
        Przeprowadza kompleksową analizę NLP tekstu

        Args:
            text: Tekst do analizy
            use_cache: Czy używać cache'a

        Returns:
            NLPAnalysisResult: Kompletny wynik analizy
        """
        start_time = time.time()

        # Sprawdź cache
        cache_key = hash(text)
        if use_cache and cache_key in self.analysis_cache:
            self.stats["cache_hits"] += 1
            cached_result = self.analysis_cache[cache_key]
            cached_result.processing_time = time.time() - start_time
            return cached_result

        try:
            # Wykryj język
            language = self._detect_language(text)
            self.stats["language_distribution"][language] += 1

            # Pobierz odpowiedni model
            nlp_model = self.models.get(language, self.models.get('en'))

            # Przetwórz tekst
            doc = nlp_model(text)

            # Przeprowadź analizy
            tokens = self._extract_tokens(doc)
            entities = self._extract_entities(doc)
            sentiment = self._analyze_sentiment(text, language)
            key_phrases = self._extract_key_phrases(doc)
            pos_tags = self._extract_pos_tags(doc)
            dependencies = self._extract_dependencies(doc)
            readability = self._calculate_readability(text, language)

            # Utwórz wynik
            result = NLPAnalysisResult(
                text=text,
                language=language,
                tokens=tokens,
                entities=entities,
                sentiment=sentiment,
                key_phrases=key_phrases,
                pos_tags=pos_tags,
                dependencies=dependencies,
                readability_score=readability,
                processing_time=time.time() - start_time
            )

            # Zapisz w cache
            if use_cache:
                if len(self.analysis_cache) >= self.cache_max_size:
                    # Usuń najstarszy wpis
                    oldest_key = next(iter(self.analysis_cache))
                    del self.analysis_cache[oldest_key]
                self.analysis_cache[cache_key] = result

            self.stats["total_analyses"] += 1
            processing_time = time.time() - start_time
            self.stats["processing_times"].append(processing_time)

            log_info(f"[NLP_PROCESSOR] Przeanalizowano tekst ({language}): {len(text)} znaków w {processing_time:.3f}s")
            return result

        except Exception as e:
            log_error(f"[NLP_PROCESSOR] Błąd analizy tekstu: {e}")
            # Zwróć minimalny wynik błędu
            return NLPAnalysisResult(
                text=text,
                language="unknown",
                tokens=[],
                entities=[],
                sentiment={"polarity": 0.0, "subjectivity": 0.0, "emotions": {}, "intensity": 0.0},
                key_phrases=[],
                pos_tags=[],
                dependencies=[],
                readability_score=0.0,
                processing_time=time.time() - start_time
            )

    def _extract_tokens(self, doc) -> List[Dict[str, Any]]:
        """Ekstrahuje tokeny z dokumentu spaCy"""
        tokens = []
        for token in doc:
            token_info = {
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "is_alpha": token.is_alpha,
                "is_stop": token.is_stop,
                "is_punct": token.is_punct,
                "like_num": token.like_num,
                "like_email": token.like_email,
                "like_url": token.like_url
            }
            tokens.append(token_info)
        return tokens

    def _extract_entities(self, doc) -> List[Dict[str, Any]]:
        """Ekstrahuje encje nazwane"""
        entities = []
        for ent in doc.ents:
            entity_info = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": getattr(ent, '_.confidence', 1.0)  # Jeśli dostępne
            }
            entities.append(entity_info)
        return entities

    def _analyze_sentiment(self, text: str, language: str) -> Dict[str, float]:
        """Analizuje sentyment tekstu"""
        # Prosta analiza sentymentu oparta na słowach kluczowych
        # W produkcji można użyć dedykowanych modeli sentymentu

        positive_words = {
            'pl': ['dobry', 'świetny', 'fantastyczny', 'wspaniały', 'doskonale', 'świetnie', 'super', 'genialny', 'znakomity', 'świetny'],
            'en': ['good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'awesome', 'brilliant', 'outstanding', 'superb']
        }

        negative_words = {
            'pl': ['zły', 'okropny', 'straszny', 'fatalny', 'beznadziejny', 'przerażający', 'okropnie', 'fatalnie', 'źle', 'gorszy'],
            'en': ['bad', 'terrible', 'awful', 'horrible', 'dreadful', 'atrocious', 'abominable', 'appalling', 'dire', 'execrable']
        }

        emotion_words = {
            'radość': ['radość', 'szczęście', 'wesołość', 'euforia', 'zachwyt'],
            'smutek': ['smutek', 'żal', 'przygnębienie', 'depresja', 'rozpacz'],
            'gniew': ['gniew', 'złość', 'wściekłość', 'furia', 'irytacja'],
            'strach': ['strach', 'lęk', 'przerażenie', 'panika', 'obawa'],
            'zaskoczenie': ['zaskoczenie', 'zdziwienie', 'zdumienie', 'osłupienie'],
            'wstręt': ['wstręt', 'obrzydzenie', 'odraza', 'niesmak']
        }

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Policz słowa pozytywne i negatywne
        pos_count = sum(1 for word in words if word in positive_words.get(language, positive_words['en']))
        neg_count = sum(1 for word in words if word in negative_words.get(language, negative_words['en']))

        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words == 0:
            polarity = 0.0
        else:
            polarity = (pos_count - neg_count) / total_sentiment_words

        # Analiza emocji
        emotions = {}
        for emotion, keywords in emotion_words.items():
            count = sum(1 for word in words if word in keywords)
            emotions[emotion] = count / len(words) if words else 0.0

        # Intensywność (proporcja słów sentymentu)
        intensity = total_sentiment_words / len(words) if words else 0.0

        # Subiektywność (heurystyka)
        subjectivity = min(1.0, intensity * 2)

        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "emotions": emotions,
            "intensity": intensity
        }

    def _extract_key_phrases(self, doc) -> List[str]:
        """Ekstrahuje frazy kluczowe"""
        # Prosta ekstrakcja oparta na rzeczownikach i przymiotnikach
        key_phrases = []

        # Znajdź rzeczowniki
        nouns = [token.lemma_ for token in doc if token.pos_ in ['NOUN', 'PROPN']]

        # Znajdź przymiotniki
        adjectives = [token.lemma_ for token in doc if token.pos_ == 'ADJ']

        # Połącz w frazy (rzeczownik + przymiotnik)
        for noun in nouns[:10]:  # Max 10 fraz
            # Znajdź przymiotniki blisko rzeczownika
            nearby_adjectives = []
            for token in doc:
                if token.lemma_ == noun and token.pos_ in ['NOUN', 'PROPN']:
                    # Sprawdź tokeny w okolicy
                    start = max(0, token.i - 3)
                    end = min(len(doc), token.i + 4)
                    for nearby_token in doc[start:end]:
                        if nearby_token.pos_ == 'ADJ' and nearby_token.lemma_ not in nearby_adjectives:
                            nearby_adjectives.append(nearby_token.lemma_)

            if nearby_adjectives:
                phrase = f"{nearby_adjectives[0]} {noun}"
                key_phrases.append(phrase)
            else:
                key_phrases.append(noun)

        return list(set(key_phrases))  # Usuń duplikaty

    def _extract_pos_tags(self, doc) -> List[Dict[str, str]]:
        """Ekstrahuje tagi części mowy"""
        pos_tags = []
        for token in doc:
            pos_tags.append({
                "token": token.text,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_
            })
        return pos_tags

    def _extract_dependencies(self, doc) -> List[Dict[str, Any]]:
        """Ekstrahuje relacje zależności składniowych"""
        dependencies = []
        for token in doc:
            dep_info = {
                "token": token.text,
                "head": token.head.text if token.head != token else "ROOT",
                "dep": token.dep_,
                "children": [child.text for child in token.children]
            }
            dependencies.append(dep_info)
        return dependencies

    def _calculate_readability(self, text: str, language: str) -> float:
        """Oblicza ocenę czytelności tekstu"""
        # Implementacja uproszczonej formuły czytelności (np. Flesch-Kincaid)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        words = re.findall(r'\b\w+\b', text)
        syllables = sum(self._count_syllables(word, language) for word in words)

        if not sentences or not words:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllables / len(words)

        # Polskojęzyczna adaptacja Flesch-Kincaid
        if language == 'pl':
            readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        else:
            # Standardowa formuła dla angielskiego
            readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

        # Normalizuj do 0-1 (wyższe = bardziej czytelne)
        return max(0.0, min(1.0, readability / 100.0))

    def _count_syllables(self, word: str, language: str) -> int:
        """Liczy sylaby w słowie"""
        word = word.lower()

        if language == 'pl':
            # Prosta heurystyka dla polskiego
            vowels = 'aeiouyąęó'
            syllables = 0
            prev_vowel = False

            for char in word:
                if char in vowels:
                    if not prev_vowel:
                        syllables += 1
                    prev_vowel = True
                else:
                    prev_vowel = False

            return max(1, syllables)
        else:
            # Dla angielskiego - uproszczona wersja
            vowels = 'aeiouy'
            syllables = 0
            prev_vowel = False

            for char in word:
                if char in vowels:
                    if not prev_vowel:
                        syllables += 1
                    prev_vowel = True
                else:
                    prev_vowel = False

            # Korekty
            if word.endswith('e'):
                syllables -= 1
            if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
                syllables += 1

            return max(1, syllables)

    async def extract_topics(self, texts: List[str], num_topics: int = 5) -> List[str]:
        """
        Ekstrahuje tematy z kolekcji tekstów (prosta implementacja)

        Args:
            texts: Lista tekstów do analizy
            num_topics: Liczba tematów do ekstrakcji

        Returns:
            List[str]: Lista głównych tematów
        """
        try:
            all_tokens = []

            for text in texts:
                analysis = await self.analyze_text(text, use_cache=True)
                # Zbierz rzeczowniki i przymiotniki
                content_words = [
                    token['lemma'] for token in analysis.tokens
                    if not token['is_stop'] and token['pos'] in ['NOUN', 'PROPN', 'ADJ']
                ]
                all_tokens.extend(content_words)

            # Policz najczęściej występujące słowa
            word_counts = Counter(all_tokens)
            top_words = [word for word, count in word_counts.most_common(num_topics * 2)]

            # Grupuj podobne słowa (prosta heurystyka)
            topics = []
            used_words = set()

            for word in top_words:
                if word not in used_words:
                    # Znajdź podobne słowa
                    similar = [w for w in top_words if self._words_similar(word, w) and w not in used_words]
                    if similar:
                        topics.append(" ".join(similar[:3]))  # Max 3 słowa w temacie
                        used_words.update(similar)
                    else:
                        topics.append(word)
                        used_words.add(word)

                if len(topics) >= num_topics:
                    break

            return topics[:num_topics]

        except Exception as e:
            log_error(f"[NLP_PROCESSOR] Błąd ekstrakcji tematów: {e}")
            return []

    def _words_similar(self, word1: str, word2: str) -> bool:
        """Sprawdza czy słowa są podobne (prosta heurystyka)"""
        if word1 == word2:
            return True

        # Sprawdź wspólną długość
        if abs(len(word1) - len(word2)) > 2:
            return False

        # Sprawdź wspólną część
        common_chars = set(word1) & set(word2)
        return len(common_chars) / max(len(set(word1)), len(set(word2))) > 0.6

    def get_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki procesora NLP"""
        avg_processing_time = sum(self.stats["processing_times"]) / len(self.stats["processing_times"]) if self.stats["processing_times"] else 0.0

        return {
            "total_analyses": self.stats["total_analyses"],
            "cache_hits": self.stats["cache_hits"],
            "cache_size": len(self.analysis_cache),
            "avg_processing_time": avg_processing_time,
            "language_distribution": dict(self.stats["language_distribution"]),
            "models_loaded": list(self.models.keys())
        }

    async def batch_analyze(self, texts: List[str], batch_size: int = 10) -> List[NLPAnalysisResult]:
        """
        Przeprowadza analizę NLP dla wielu tekstów wsadowo

        Args:
            texts: Lista tekstów do analizy
            batch_size: Rozmiar wsadu

        Returns:
            List[NLPAnalysisResult]: Wyniki analizy dla wszystkich tekstów
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Przetwórz wsad równolegle
            tasks = [self.analyze_text(text) for text in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    log_error(f"[NLP_PROCESSOR] Błąd w analizie wsadowej: {result}")
                    # Dodaj pusty wynik dla błędnego tekstu
                    results.append(NLPAnalysisResult(
                        text="",
                        language="error",
                        tokens=[],
                        entities=[],
                        sentiment={"polarity": 0.0, "subjectivity": 0.0, "emotions": {}, "intensity": 0.0},
                        key_phrases=[],
                        pos_tags=[],
                        dependencies=[],
                        readability_score=0.0,
                        processing_time=0.0
                    ))
                else:
                    results.append(result)

        return results

# Globalna instancja procesora NLP
_nlp_processor = None

def get_nlp_processor() -> NLPProcessor:
    """Pobierz globalną instancję procesora NLP"""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor

# Test funkcji
if __name__ == "__main__":
    async def test_nlp():
        """Test procesora NLP"""
        processor = get_nlp_processor()

        test_texts = [
            "To jest przykładowy tekst w języku polskim. Zawiera różne części mowy i encje.",
            "Python to wspaniały język programowania. Używam go do tworzenia aplikacji webowych.",
            "Sztuczna inteligencja rewolucjonizuje sposób, w jaki rozwiązujemy problemy."
        ]

        print("🧠 TEST PROCESORA NLP")
        print("=" * 50)

        for i, text in enumerate(test_texts):
            print(f"\n📝 Tekst {i+1}: {text[:60]}...")
            analysis = await processor.analyze_text(text)

            print(f"🌍 Język: {analysis.language}")
            print(f"🏷️ Encje: {len(analysis.entities)}")
            print(f"🔑 Frazy kluczowe: {analysis.key_phrases[:3]}")
            print(f"😊 Sentyment: {analysis.sentiment['polarity']:.2f}")
            print(f"📖 Czytelność: {analysis.readability_score:.2f}")
            print(f"⚡ Czas: {analysis.processing_time:.3f}s")

        # Test ekstrakcji tematów
        topics = await processor.extract_topics(test_texts)
        print(f"\n📊 Tematy: {topics}")

        # Statystyki
        stats = processor.get_stats()
        print(f"\n📈 Statystyki: {stats}")

    # Uruchom test
    asyncio.run(test_nlp())