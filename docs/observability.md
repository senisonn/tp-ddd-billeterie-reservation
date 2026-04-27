# Observabilité — Billetterie & Réservation

## 5.3 Stratégie d'observabilité

Trois piliers sont implémentés : **Correlation ID**, **logging structuré** et **métriques**.

---

## Correlation ID

Chaque requête entrante génère (ou hérite) un identifiant unique propagé à travers
tous les contextes. Il permet de relier les logs et événements d'un même flux métier.

### Cycle de vie

```
Client HTTP
  │  Header: X-Correlation-ID: COR-20250210-XYZ789
  ▼
adapters/rest_api.py      ← génère si absent
  │  correlation_id = "COR-20250210-XYZ789"
  ▼
ServiceReservation        ← passe le cid au domaine
  │
  ▼
EventBus.publish(event)   ← event.correlation_id = cid
  │
  ├──▶ ContexteNotification   (email avec cid dans les logs)
  └──▶ ContexteContrôleAccès  (QR activation avec cid dans les logs)
```

### Implémentation (`adapters/rest_api.py`)

```python
def _correlation_id(self) -> str:
    return self.headers.get("X-Correlation-ID") \
        or f"COR-{uuid.uuid4().hex[:12].upper()}"
```

---

## Logging structuré (JSON)

Tous les logs sont émis en JSON (un objet par ligne), exploitables par ELK / Loki.

### Format

```json
{
  "timestamp": "2025-02-10 14:32:05,123",
  "level":     "INFO",
  "logger":    "billetterie.rest",
  "message":   "Réservation créée",
  "correlation_id": "COR-20250210-XYZ789",
  "reservation_id": "RES-ABC12345",
  "spectateur_id":  "CLI-2025-00042"
}
```

### Captures de logs 

Sortie produite par lors du scénario bout-en-bout :

```json
{"timestamp": "2025-02-10 14:32:05,101", "level": "INFO", "logger": "billetterie.eventbus",
 "message": "Événement publié : ReservationCréée",
 "correlation_id": "COR-TEST-PROPAGATION", "event_type": "ReservationCréée", "event_id": "EVE-A1B2C3D4"}

{"timestamp": "2025-02-10 14:32:05,203", "level": "INFO", "logger": "billetterie.eventbus",
 "message": "Événement publié : RéservationConfirmée",
 "correlation_id": "COR-TEST-PROPAGATION", "event_type": "RéservationConfirmée", "event_id": "EVE-E5F6G7H8"}

{"timestamp": "2025-02-10 14:32:05,204", "level": "INFO", "logger": "billetterie.notification",
 "message": "Email de confirmation envoyé à CLI-MARIE",
 "correlation_id": "COR-TEST-PROPAGATION", "event_type": "RéservationConfirmée",
 "context": "ContexteNotification"}

{"timestamp": "2025-02-10 14:32:05,205", "level": "INFO", "logger": "billetterie.controle_acces",
 "message": "2 QR code(s) activé(s)",
 "correlation_id": "COR-TEST-PROPAGATION", "event_type": "RéservationConfirmée",
 "context": "ContexteContrôleAccès"}
```

---

## Métriques

Trois métriques exposées sur `GET /metrics` (format JSON, production → Prometheus `Counter`/`Gauge`).

| Métrique | Type | Nature | Description |
|----------|------|--------|-------------|
| `reservations_creees_total` | Counter | **Métier** | Nombre de réservations créées depuis le démarrage |
| `http_requests_total` | Counter | **Technique** | Nombre total de requêtes HTTP traitées |
| `jauge_disponible` | Gauge | **Libre** | Places restantes par événement (dict `{evenement_id: int}`) |

### Endpoint `/metrics` — réponse exemple

```json
{
  "reservations_creees_total":     42,
  "reservations_confirmees_total": 38,
  "http_requests_total":          127,
  "http_errors_total":              5,
  "jauge_disponible": {
    "EVT-2025-00010": 21,
    "EVT-2025-00011": 0
  }
}
```

### Implémentation

```python
_metrics = {
    "reservations_creees_total":    0,   # métier
    "http_requests_total":          0,   # technique
    "jauge_disponible":             {},  # libre
}

def _inc(name):
    _metrics[name] += 1
```

---

## Capture d'exécution des tests bout-en-bout (Partie 5.4)

```
============================= test session starts ==============================
platform linux -- Python 3.13.12, pytest-8.3.5, pluggy-1.5.0 -- /usr/bin/python3
rootdir: /home/soheil/Bureau/DDD/tp-ddd-billeterie-reservation
collected 25 items

tests/integration/test_scenario.py::TestScenarioBoutEnBout::test_reservation_confirmee_declenche_notification_et_qr PASSED [ 92%]
tests/integration/test_scenario.py::TestScenarioBoutEnBout::test_annulation_declenche_notification_et_invalide_qr  PASSED [ 96%]
tests/integration/test_scenario.py::TestScenarioBoutEnBout::test_correlation_id_propage_sur_tous_les_contextes     PASSED [100%]

============================== 25 passed in 0.25s ==============================
```

---

## Architecture de l'observabilité (production)

```
                    ┌──────────────────────────────────┐
                    │         Billetterie API           │
                    │  adapters/rest_api.py             │
                    │  • Correlation ID (header)        │
                    │  • JSON logs → stdout             │
                    │  • /metrics → JSON                │
                    └──────────┬───────────────────────┘
                               │ stdout (JSON logs)
                    ┌──────────▼───────────┐
                    │    Log Aggregator     │
                    │  (Loki / ELK Stack)   │
                    │  filtre: correlation_id│
                    └──────────────────────┘

                    ┌──────────────────────┐
                    │   /metrics endpoint   │
                    │        ▼             │
                    │   Prometheus scrape   │
                    │        ▼             │
                    │   Grafana Dashboard  │
                    │  • reservations/min  │
                    │  • jauge par event   │
                    │  • erreurs HTTP      │
                    └──────────────────────┘
```
