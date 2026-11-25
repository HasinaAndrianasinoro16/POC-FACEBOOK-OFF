# Comments Sync

Application hors ligne qui lit le fichier `facebook_comments.jsonl` produit par le webhook
et tient à jour un **fichier JSON** : une liste avec un objet par commentaire.

Elle n'utilise ni Internet ni l'API Facebook : elle ne lit qu'un fichier local.

## Fonctionnement

- Toutes les `POLL_INTERVAL_SECONDS` secondes (15 par défaut), elle lit les **nouvelles lignes** du `.jsonl`.
- Seuls les événements `add` et `edited` sont conservés (`remove` et les autres sont ignorés).
- Un événement `edited` **remplace l'objet d'origine** du même `comment_id`, à la même position dans la liste.
- Un `add` tardif ou rejoué n'écrase jamais une version déjà modifiée.
- Une valeur vide dans une version modifiée n'efface pas la valeur existante (par exemple un message non récupéré).
- Le fichier JSON n'est réécrit que lorsqu'il y a un changement, de façon atomique.
- Au redémarrage, le fichier existant est repris : rien n'est perdu ni dupliqué.
- Si le fichier JSON devient illisible, il est conservé sous `comments.json.corrupt` et reconstruit depuis le `.jsonl`.

## Format de sortie

```json
[
  {
    "comment_id": "122102974203554894_1185649797315773",
    "post_id": "1424319170767941_122102974203554894",
    "parent_id": "1424319170767941_122102974203554894",
    "sender_id": "29092067733807895",
    "sender_name": "Mitia Celo",
    "message": "Bonjour",
    "attachment": null,
    "event_verb": "add",
    "created_time": "2026-11-24T08:21:17+00:00",
    "received_at": "2026-11-24T08:21:20+00:00"
  }
]
```

## Installation (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Copie `.env.example` en `.env` :

| Variable | Description | Défaut |
|---|---|---|
| `SOURCE_FILE` | Chemin du `.jsonl` du webhook | `../facebook_webhook/data/facebook_comments.jsonl` |
| `OUTPUT_FILE` | Chemin du JSON consolidé | `data/comments.json` |
| `POLL_INTERVAL_SECONDS` | Intervalle de lecture, en secondes | `15` |

## Lancement

```powershell
python main.py
```

`Ctrl+C` pour arrêter. L'application continue de tourner même si un cycle échoue.

## À savoir

- Si un autre programme verrouille le fichier JSON, l'application le signale dans le terminal
  et réessaie au cycle suivant.
- Les champs conservés se modifient dans `config.py` (`FIELDS`).