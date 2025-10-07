import argparse
import os
from typing import Optional

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .labels import LABELS


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["note"] = df["note"].fillna("").astype(str)
    df["label"] = df["label"].where(df["label"].isin(LABELS), "OTHER")
    return df


def _pick_stratify(labels: pd.Series) -> Optional[pd.Series]:
    value_counts = labels.value_counts()
    if value_counts.empty or value_counts.min() < 2:
        return None
    return labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(__file__), "data", "delivery_notes.sample.csv"),
    )
    parser.add_argument(
        "--out",
        default=os.path.join("service", "model_store", "text_triage.pkl"),
    )
    args = parser.parse_args()

    df = load_data(args.csv)
    stratify = _pick_stratify(df["label"])
    X_train, X_test, y_train, y_test = train_test_split(
        df["note"],
        df["label"],
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=50_000),
            ),
            ("clf", LogisticRegression(max_iter=200, n_jobs=None)),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    report = classification_report(y_test, y_pred, labels=LABELS, zero_division=0)
    print(report)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "labels": LABELS,
            "version": "text-triage-0.1.0",
        },
        args.out,
    )
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
