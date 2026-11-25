"""Synchronise le fichier .jsonl du webhook vers un CSV consolidé, en boucle."""

import logging
import sys
import time

from config import OUTPUT_FILE, SOURCE_FILE, get_poll_interval
from reader import JsonlReader
from store import CommentStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("comments_sync")


def run_cycle(reader: JsonlReader, store: CommentStore) -> None:
    """Un cycle : lit les nouvelles lignes, met à jour la mémoire, écrit le CSV."""
    records = reader.read_new()

    if records:
        added, updated = store.apply(records)
        if added or updated:
            logger.info("%d nouveau(x), %d modifié(s)", added, updated)

    if store.save_if_needed():
        logger.info("%s mis à jour (%d commentaires)", OUTPUT_FILE, len(store))


def main() -> None:
    try:
        interval = get_poll_interval()
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    reader = JsonlReader(SOURCE_FILE)
    store = CommentStore(OUTPUT_FILE)
    store.load()

    logger.info("Source : %s", SOURCE_FILE.resolve())
    logger.info("Sortie : %s", OUTPUT_FILE.resolve())
    logger.info("Lecture toutes les %s seconde(s). Ctrl+C pour arrêter.", interval)

    try:
        while True:
            try:
                run_cycle(reader, store)
            except Exception:
                # Une erreur ne doit jamais arrêter l'application
                logger.exception("Erreur pendant le cycle, nouvelle tentative au prochain")

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Arrêt demandé")


if __name__ == "__main__":
    main()