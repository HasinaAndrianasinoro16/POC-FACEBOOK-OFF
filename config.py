"""Configuration de l'application (lue depuis les variables d'environnement)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Fichier produit par le webhook (une ligne JSON par événement)
SOURCE_FILE = Path(
    os.getenv("SOURCE_FILE", "../facebook_webhook/data/facebook_comments.jsonl")
)

# Fichier JSON consolidé (une liste : un commentaire = un objet)
OUTPUT_FILE = Path(os.getenv("OUTPUT_FILE", "data/comments.json"))

# Seuls ces événements sont conservés
ALLOWED_VERBS = {"add", "edited"}

# Champs conservés pour chaque commentaire (modifiables ici)
FIELDS = [
    "comment_id",
    "post_id",
    "parent_id",
    "sender_id",
    "sender_name",
    "message",
    "attachment",
    "event_verb",
    "created_time",
    "received_at",
]


def get_poll_interval() -> float:
    """Intervalle de lecture en secondes (POLL_INTERVAL_SECONDS, 15 par défaut)."""
    raw = os.getenv("POLL_INTERVAL_SECONDS", "15")

    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"POLL_INTERVAL_SECONDS invalide : {raw!r}") from None

    if value <= 0:
        raise ValueError("POLL_INTERVAL_SECONDS doit être supérieur à 0")

    return value