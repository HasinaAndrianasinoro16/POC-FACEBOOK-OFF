"""Stockage consolidé des commentaires dans un fichier JSON."""

import json
import logging
import os
import tempfile
from pathlib import Path

from config import ALLOWED_VERBS, FIELDS

logger = logging.getLogger("comments_sync")

# La date de réception change à chaque événement : elle ne compte pas comme une modification
_IGNORED_FOR_COMPARISON = {"received_at"}


def normalize(record: dict) -> dict:
    """Ne garde que les champs utiles, avec leurs types d'origine."""
    row = {field: record.get(field) for field in FIELDS}

    if row["comment_id"] is not None:
        row["comment_id"] = str(row["comment_id"])

    return row


def _is_empty(value) -> bool:
    return value is None or value == ""


def _is_same(first: dict, second: dict) -> bool:
    return all(
        first[field] == second[field]
        for field in FIELDS
        if field not in _IGNORED_FOR_COMPARISON
    )


class CommentStore:
    """Un commentaire = un objet JSON. Une modification remplace l'objet d'origine."""

    def __init__(self, path: Path):
        self.path = path
        self._comments: dict[str, dict] = {}
        self._dirty = False

    def __len__(self) -> int:
        return len(self._comments)

    def load(self) -> None:
        """Reprend le fichier JSON existant, ou prépare sa création."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists() or self.path.stat().st_size == 0:
            self._dirty = True
            return

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise ValueError("une liste était attendue")

        except ValueError:
            # Fichier illisible : on le met de côté, il sera reconstruit depuis le .jsonl
            backup = self.path.with_name(self.path.name + ".corrupt")
            os.replace(self.path, backup)
            logger.warning("%s est illisible, copie conservée dans %s", self.path, backup)
            self._dirty = True
            return

        for item in data:
            if isinstance(item, dict) and item.get("comment_id"):
                row = normalize(item)
                self._comments[row["comment_id"]] = row

        logger.info("%d commentaire(s) chargé(s) depuis %s", len(self), self.path)

    def apply(self, records: list[dict]) -> tuple[int, int]:
        """Applique les événements. Renvoie (ajoutés, modifiés)."""
        added = updated = 0

        for record in records:
            verb = record.get("event_verb")
            if verb not in ALLOWED_VERBS:
                continue

            row = normalize(record)
            comment_id = row["comment_id"]
            if not comment_id:
                continue

            existing = self._comments.get(comment_id)

            if existing is None:
                self._comments[comment_id] = row
                added += 1
                continue

            # Un "add" tardif ou rejoué ne doit pas écraser une version modifiée
            if verb == "add" and existing["event_verb"] == "edited":
                continue

            # La nouvelle version remplace l'ancienne, sans effacer une valeur par du vide
            merged = {
                field: existing[field] if _is_empty(row[field]) else row[field]
                for field in FIELDS
            }

            if not _is_same(merged, existing):
                self._comments[comment_id] = merged  # même position dans le fichier
                updated += 1

        if added or updated:
            self._dirty = True

        return added, updated

    def save_if_needed(self) -> bool:
        """Réécrit le fichier JSON s'il a changé. Renvoie True si le fichier a été écrit."""
        if not self._dirty:
            return False

        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(list(self._comments.values()), file, ensure_ascii=False, indent=2)

            os.replace(tmp_name, self.path)

        except OSError as exc:
            # Sous Windows, le remplacement échoue si un autre programme verrouille le fichier
            Path(tmp_name).unlink(missing_ok=True)
            logger.warning(
                "Écriture impossible (%s). Le fichier est-il ouvert dans un autre programme ? "
                "Nouvelle tentative au prochain cycle.",
                type(exc).__name__,
            )
            return False

        self._dirty = False
        return True