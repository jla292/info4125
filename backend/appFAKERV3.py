from __future__ import annotations
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
import pandas as pd
import nltk
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from nltk.sentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# ---------------------------------------------------------------------
# 1. Setup + Hyperparameters
# ---------------------------------------------------------------------
nltk.download("vader_lexicon")

'''
TOP_K = 8
MIN_SIM = 0.25
ENTAIL_T = 0.80
CONTRA_T = 0.80
NLI_MODEL = "roberta-large-mnli"
EPS = 1e-9
'''
'''
TOP_K = 12
MIN_SIM = 0.20
ENTAIL_T = 0.70
CONTRA_T = 0.85
#NLI_MODEL = "microsoft/deberta-v3-base-mnli"
NLI_MODEL = "roberta-large-mnli"
EPS = 1e-9
'''

TOP_K = 8
MIN_SIM = 0.25
NLI_MODEL = "roberta-large-mnli"  # or "microsoft/deberta-v3-base-mnli" for smaller/faster
EPS = 1e-9
ENTAIL_T = 0.60  # or even 0.55
CONTRA_T = 0.75  # keep contradiction stricter
MARGIN   = 0.10

app = Flask(__name__)
CORS(app)  # allow Chrome extension calls

# ---------------------------------------------------------------------
# 2. Data + Model Building
# ---------------------------------------------------------------------
def load_json_df(path: str) -> pd.DataFrame:
    """Load JSON or JSONL of verified true facts."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read().strip()
    if "\n" in raw and raw[0] != "[":
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(json.loads(raw))

    needed = {"text", "label", "source", "date", "topic"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    df = df.dropna(subset=["text"]).copy()
    df["label"] = df["label"].astype(str).str.lower().str.strip()
    df["label"] = df["label"].replace({
        "1": "true", "t": "true", "true": "true",
        "0": "false", "f": "false", "false": "false"
    })
    return df


@dataclass
class VerificationSystem:
    tone: SentimentIntensityAnalyzer
    retriever: SentenceTransformer
    nli: Any
    corpus_texts: List[str]
    corpus_meta: List[Dict[str, Any]]
    corpus_embeddings: np.ndarray


def build_system(df: pd.DataFrame) -> VerificationSystem:
    """Initialize tone, retriever, and NLI model."""
    print("🔧 Building verification system ... this may take 1–2 minutes.")
    tone = SentimentIntensityAnalyzer()
    retriever = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    corpus_texts = df["text"].tolist()
    corpus_meta = [
        {
            "source": row.get("source"),
            "date": row.get("date"),
            "topic": row.get("topic"),
            "text": row.get("text"),
        }
        for _, row in df.iterrows()
    ]

    corpus_embeddings = retriever.encode(
        corpus_texts, convert_to_numpy=True, normalize_embeddings=True
    )

    nli_pipe = pipeline(
        "text-classification",
        model=AutoModelForSequenceClassification.from_pretrained(NLI_MODEL),
        tokenizer=AutoTokenizer.from_pretrained(NLI_MODEL),
        return_all_scores=True,
        truncation=True,
    )

    print("✅ System built successfully.")
    return VerificationSystem(
        tone=tone,
        retriever=retriever,
        nli=nli_pipe,
        corpus_texts=corpus_texts,
        corpus_meta=corpus_meta,
        corpus_embeddings=corpus_embeddings,
    )

# ---------------------------------------------------------------------
# 3. Functions
# ---------------------------------------------------------------------
def tone_summary(scores: Dict[str, float]) -> str:
    c = scores["compound"]
    if c >= 0.3:
        base = "positive"
    elif c <= -0.3:
        base = "negative"
    else:
        base = "neutral"
    mag = abs(c)
    if base == "neutral":
        return "neutral"
    if mag >= 0.7:
        return f"very {base}"
    elif mag >= 0.45:
        return f"fairly {base}"
    else:
        return f"slightly {base}"


def nearest_hits(sys: VerificationSystem, query: str, top_k: int = TOP_K) -> List[Tuple[int, float]]:
    if len(sys.corpus_texts) == 0:
        return []
    q_emb = sys.retriever.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    sims = util.cos_sim(q_emb, sys.corpus_embeddings).cpu().numpy().ravel()
    order = np.argsort(-sims)[:top_k]
    return [(i, float(sims[i])) for i in order if sims[i] >= MIN_SIM]


def nli_scores(sys: VerificationSystem, premise: str, hypothesis: str) -> Dict[str, float]:
    out = sys.nli({"text": premise, "text_pair": hypothesis})
    if isinstance(out, dict):
        scores_list = [out]
    elif isinstance(out, list):
        scores_list = out[0] if isinstance(out[0], list) else out
    else:
        scores_list = []
    label2score = {}
    for item in scores_list:
        if not isinstance(item, dict):
            continue
        lab = str(item.get("label", "")).lower()
        sc = float(item.get("score", 0.0))
        label2score[lab] = sc
    ent = label2score.get("entailment", 0.0) or label2score.get("label_2", 0.0)
    neu = label2score.get("neutral", 0.0) or label2score.get("label_1", 0.0)
    con = label2score.get("contradiction", 0.0) or label2score.get("label_0", 0.0)
    total = ent + neu + con + EPS
    ent /= total
    neu /= total
    con /= total
    return {"entailment": ent, "neutral": neu, "contradiction": con}


def aggregate_true_false(nli_list: List[Dict[str, float]]) -> Tuple[float, float]:
    if not nli_list:
        return 0.5, 0.5
    ents = np.array([d["entailment"] for d in nli_list])
    cons = np.array([d["contradiction"] for d in nli_list])
    neuts = np.array([d["neutral"] for d in nli_list])
    p_true = float(np.clip(ents.mean(), 0.0, 1.0))
    alt_false = 1.0 - float(ents.mean() + neuts.mean())
    p_false = float(np.clip(max(cons.mean(), alt_false), 0.0, 1.0))
    s = p_true + p_false + EPS
    return p_true / s, p_false / s


def classify_text(sys: VerificationSystem, claim: str) -> Dict[str, Any]:
    ts = sys.tone.polarity_scores(claim)
    tone = tone_summary(ts)
    hits = nearest_hits(sys, claim, TOP_K)

    nli_list, support_sources, contra_sources = [], [], []
    for i, sim in hits:
        premise = sys.corpus_texts[i]
        scores = nli_scores(sys, premise=premise, hypothesis=claim)
        nli_list.append(scores)
        meta = sys.corpus_meta[i] | {
            "similarity": round(sim, 3),
            "short_text": premise[:180] + ("…" if len(premise) > 200 else ""),
        }
        if scores["entailment"] >= ENTAIL_T:
            support_sources.append(meta | {"entailment": round(scores["entailment"], 3)})
        if scores["contradiction"] >= CONTRA_T:
            contra_sources.append(meta | {"contradiction": round(scores["contradiction"], 3)})

    p_true, p_false = aggregate_true_false(nli_list)

    if support_sources:
        verdict = "likely_true"
        msg = "This appears likely true based on entailment with trusted facts from your dataset."
    elif contra_sources:
        verdict = "likely_false"
        msg = "This appears likely false because it contradicts trusted facts from your dataset."
    else:
        verdict = "cannot_verify"
        msg = "I can't verify this with enough confidence. Review the closest sources below."

    return {
        "input": claim,
        "verdict": verdict,
        "message": msg,
        "probabilities": {"true": round(p_true, 4), "false": round(p_false, 4)},
        "tone": {"summary": tone, "raw": ts},
        "supporting_sources_true": support_sources[:5],
        "supporting_sources_false": contra_sources[:5],
        "nearest_sources_considered": [
            sys.corpus_meta[i] | {"similarity": round(sim, 3)} for i, sim in hits
        ],
        "notes": {
            "nli_model": NLI_MODEL,
            "thresholds": {
                "entailment": ENTAIL_T,
                "contradiction": CONTRA_T,
                "min_similarity": MIN_SIM,
            },
        },
    }

# ---------------------------------------------------------------------
# 4. Load Data + Initialize System
# ---------------------------------------------------------------------
Data_paths = [
    "financial_aid_facts.json",
    "cornell_mealplans_2025.json",
    "cornell_classes_2025.json"
]

# df = load_json_df(DATA_PATH)
dfs= []
for path in Data_paths:
    df_part = load_json_df(path)
    dfs.append(df_part)

df = pd.concat(dfs, ignore_index=True)
sys_model = build_system(df)

# ---------------------------------------------------------------------
# 5. API Routes
# ---------------------------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        result = classify_text(sys_model, text)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Processing failed: {e}"}), 500


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "running", "model": "VerificationSystem"})

# ---------------------------------------------------------------------
# 6. Run Flask App
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
