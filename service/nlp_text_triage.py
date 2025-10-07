import os
from functools import lru_cache
from typing import Dict, List

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ml.text.labels import LABELS

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_store", "text_triage.pkl")


def _default_model() -> Dict[str, object]:
    """Train an in-memory fallback model when the serialized artifact is absent."""

    data_path = (
        Path(__file__).resolve().parents[1]
        / "ml"
        / "text"
        / "data"
        / "delivery_notes.sample.csv"
    )
    if not data_path.exists():
        raise FileNotFoundError(
            "Missing training data for fallback model. Expected delivery_notes.sample.csv."
        )

    df = pd.read_csv(data_path)
    df["note"] = df["note"].fillna("").astype(str)
    df["label"] = df["label"].where(df["label"].isin(LABELS), "OTHER")

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=50000),
            ),
            ("clf", LogisticRegression(max_iter=200)),
        ]
    )
    pipeline.fit(df["note"], df["label"])

    return {
        "pipeline": pipeline,
        "labels": LABELS,
        "version": "text-triage-fallback-0.1.0",
    }


@lru_cache(maxsize=1)
def _load_model() -> Dict[str, object]:
    if os.path.exists(_MODEL_PATH):
        return joblib.load(_MODEL_PATH)

    model = _default_model()

    model_dir = os.path.dirname(_MODEL_PATH)
    os.makedirs(model_dir, exist_ok=True)
    try:
        joblib.dump(model, _MODEL_PATH)
    except Exception:
        # Best-effort cache; failures shouldn't block predictions.
        pass

    return model


def _top_indices(probs: List[float], limit: int = 3) -> List[int]:
    return sorted(range(len(probs)), key=lambda idx: probs[idx], reverse=True)[:limit]


def predict_note(note: str) -> Dict[str, object]:
    model = _load_model()
    pipeline = model["pipeline"]
    version = model.get("version", "unknown")
    probabilities = pipeline.predict_proba([note])[0]
    classes = pipeline.classes_
    best_idx = int(probabilities.argmax())

    top_items = []
    for idx in _top_indices(probabilities):
        top_items.append({"label": str(classes[idx]), "p": float(probabilities[idx])})

    return {
        "label": str(classes[best_idx]),
        "confidence": float(probabilities[best_idx]),
        "version": version,
        "top3": top_items,
    }
