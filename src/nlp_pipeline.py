"""Lightweight, explainable NLP pipeline for semiconductor documents."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TOPICS = {
    "AI & Data Center": ["ai", "gpu", "accelerator", "data center", "hyperscaler", "generative"],
    "Memory & Packaging": ["memory", "hbm", "dram", "nand", "packaging", "storage"],
    "Manufacturing & Equipment": ["foundry", "lithography", "euv", "capacity", "process", "wafer"],
    "Supply Chain": ["supply", "supplier", "component", "inventory", "energy", "water"],
    "Competition & Demand": ["competition", "demand", "pricing", "customer", "bookings", "cyclical"],
    "Geopolitics & Regulation": ["export", "regulation", "geopolitical", "restriction", "uncertain"],
}
POSITIVE = {"strong", "growth", "healthy", "increasing", "accelerate", "robust", "benefit", "investment", "leading"}
NEGATIVE = {"risk", "uncertain", "uncertainty", "constrained", "volatility", "pressure", "cyclical", "restriction", "dependency", "mixed"}

def load_documents(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"company", "document_type", "period", "text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    return df[list(required)].dropna().reset_index(drop=True)

def classify_topic(text: str) -> str:
    lower = text.lower()
    scores = {topic: sum(lower.count(term) for term in terms) for topic, terms in TOPICS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "Other"

def sentiment(text: str) -> tuple[str, float]:
    words = set(re.findall(r"[a-z]+", text.lower()))
    pos, neg = len(words & POSITIVE), len(words & NEGATIVE)
    score = (pos - neg) / max(pos + neg, 1)
    label = "Positive" if score > 0.15 else "Negative" if score < -0.15 else "Neutral"
    return label, round(float(score), 3)

def analyze(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["topic"] = result["text"].map(classify_topic)
    sentiment_values = result["text"].map(sentiment).apply(pd.Series)
    sentiment_values.columns = ["sentiment", "sentiment_score"]
    result[["sentiment", "sentiment_score"]] = sentiment_values
    result["word_count"] = result["text"].str.split().str.len()
    return result

def keywords(texts: list[str], n: int = 12) -> list[tuple[str, float]]:
    if not texts:
        return []
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=500)
    matrix = vectorizer.fit_transform(texts)
    scores = np.asarray(matrix.mean(axis=0)).ravel()
    terms = vectorizer.get_feature_names_out()
    return sorted(zip(terms, scores), key=lambda item: item[1], reverse=True)[:n]

def similar_documents(df: pd.DataFrame, query: str, n: int = 5) -> pd.DataFrame:
    corpus = list(df["text"]) + [query]
    matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    result = df.copy()
    result["similarity"] = scores
    return result.sort_values("similarity", ascending=False).head(n)

