"""
utils/history.py
----------------
Optional scan history, stored in one SQLite file (data/history.db).

SQLite ships with Python, needs no server, and works offline - which is why
the README recommends it over Firebase for this app. Nothing here is required
for predictions; if the table cannot be opened the app simply runs without
history.

A thumbnail is stored inline as a small base64 JPEG so the history list still
shows the leaf after the original upload is gone. Thumbnails are capped at
160px, which keeps the database small even after a few hundred scans.
"""

import base64
import io
import json
import os
import sqlite3
import threading
from datetime import datetime

import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT    NOT NULL,
    model_slug    TEXT    NOT NULL,
    model_name    TEXT    NOT NULL,
    predicted     TEXT    NOT NULL,
    confidence    REAL    NOT NULL,
    low_conf      INTEGER NOT NULL DEFAULT 0,
    mode          TEXT    NOT NULL DEFAULT 'single',
    filename      TEXT,
    probabilities TEXT,
    thumbnail     TEXT
);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at DESC);
"""


def _connect():
    os.makedirs(os.path.dirname(config.HISTORY_DB), exist_ok=True)
    conn = sqlite3.connect(config.HISTORY_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not config.ENABLE_HISTORY:
        return
    with _lock, _connect() as conn:
        conn.executescript(SCHEMA)


def make_thumbnail(image, size: int = 160) -> str:
    """PIL image -> small base64 JPEG data URI, or '' if anything goes wrong."""
    try:
        thumb = image.copy()
        thumb.thumbnail((size, size))
        buf = io.BytesIO()
        thumb.save(buf, format="JPEG", quality=70)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def add_scan(result: dict, filename: str = None, thumbnail: str = "",
             mode: str = "single") -> None:
    """Records one prediction. Never raises - history must not break a scan."""
    if not config.ENABLE_HISTORY:
        return
    try:
        with _lock, _connect() as conn:
            conn.execute(
                """INSERT INTO scans
                   (created_at, model_slug, model_name, predicted, confidence,
                    low_conf, mode, filename, probabilities, thumbnail)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    result.get("model", "?"),
                    result.get("model_name", "?"),
                    result.get("predicted_class", "?"),
                    float(result.get("confidence", 0.0)),
                    1 if result.get("low_confidence") else 0,
                    mode,
                    filename,
                    json.dumps(result.get("probabilities", {})),
                    thumbnail,
                ),
            )
            _trim(conn)
    except Exception as exc:  # pragma: no cover - history is best-effort
        print(f"[history] could not save scan: {exc}")


def _trim(conn):
    """Keeps only the newest HISTORY_LIMIT rows."""
    conn.execute(
        """DELETE FROM scans WHERE id NOT IN
           (SELECT id FROM scans ORDER BY id DESC LIMIT ?)""",
        (config.HISTORY_LIMIT,),
    )


def list_scans(limit: int = 50, include_thumbs: bool = True):
    if not config.ENABLE_HISTORY:
        return []
    try:
        with _lock, _connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    except Exception as exc:
        print(f"[history] could not read scans: {exc}")
        return []

    out = []
    for r in rows:
        item = {
            "id": r["id"],
            "created_at": r["created_at"],
            "model": r["model_slug"],
            "model_name": r["model_name"],
            "predicted_class": r["predicted"],
            "confidence": r["confidence"],
            "low_confidence": bool(r["low_conf"]),
            "mode": r["mode"],
            "filename": r["filename"],
        }
        if include_thumbs:
            item["thumbnail"] = r["thumbnail"] or ""
        out.append(item)
    return out


def clear_scans():
    if not config.ENABLE_HISTORY:
        return
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM scans")


def stats():
    """Counts per class - used by the history panel's small summary."""
    if not config.ENABLE_HISTORY:
        return {}
    try:
        with _lock, _connect() as conn:
            rows = conn.execute(
                "SELECT predicted, COUNT(*) AS n FROM scans GROUP BY predicted"
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) AS n FROM scans").fetchone()["n"]
        return {"total": total, "by_class": {r["predicted"]: r["n"] for r in rows}}
    except Exception:
        return {}


def export_csv() -> str:
    """History as CSV text, for the thesis appendix."""
    import csv
    rows = list_scans(limit=config.HISTORY_LIMIT, include_thumbs=False)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "timestamp", "model", "predicted_class",
                     "confidence", "low_confidence", "mode", "filename"])
    for r in rows:
        writer.writerow([r["id"], r["created_at"], r["model_name"],
                         r["predicted_class"], f"{r['confidence']:.4f}",
                         r["low_confidence"], r["mode"], r["filename"] or ""])
    return buf.getvalue()
