"""Lecture incrémentale du fichier .jsonl : seules les nouvelles lignes sont lues."""

import json
import logging
from pathlib import Path

logger = logging.getLogger("comments_sync")


class JsonlReader:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self._missing_logged = False

    def read_new(self) -> list[dict]:
        """Renvoie les nouvelles lignes complètes depuis la dernière lecture."""
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            if not self._missing_logged:
                logger.warning("Fichier source introuvable : %s", self.path.resolve())
                self._missing_logged = True
            return []

        self._missing_logged = False

        # Fichier vidé ou remplacé : on repart du début
        if size < self.offset:
            logger.info("Fichier source réinitialisé : relecture depuis le début")
            self.offset = 0

        if size == self.offset:
            return []

        with self.path.open("rb") as file:
            file.seek(self.offset)
            chunk = file.read()

        # Une ligne en cours d'écriture n'a pas encore son saut de ligne : on l'attend
        last_newline = chunk.rfind(b"\n")
        if last_newline == -1:
            return []

        complete = chunk[: last_newline + 1]
        self.offset += len(complete)

        records = []
        for raw_line in complete.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                data = json.loads(raw_line)
            except ValueError:
                logger.warning("Ligne JSON invalide ignorée")
                continue

            if isinstance(data, dict):
                records.append(data)

        return records