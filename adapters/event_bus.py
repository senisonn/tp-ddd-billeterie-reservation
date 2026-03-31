"""
Event Bus en mémoire — intégration événementielle inter-contextes.
Couche Adapters (hexagonale) : implémente le port de publication d'événements.

Pattern : Publish / Subscribe avec Correlation ID propagé.
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Logger structuré (réutilisé par les handlers de contextes)
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        for attr in ("correlation_id", "event_type", "event_id", "context"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        return json.dumps(entry, ensure_ascii=False)


def _get_logger(name: str) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    log = logging.getLogger(name)
    if not log.handlers:
        log.setLevel(logging.INFO)
        log.addHandler(handler)
    return log


# ---------------------------------------------------------------------------
# Enveloppe d'événement (structure commune à tous les événements)
# ---------------------------------------------------------------------------

class DomainEvent:
    def __init__(self, event_type: str, payload: dict, correlation_id: str | None = None) -> None:
        self.event_id       = f"EVE-{uuid.uuid4().hex[:8].upper()}"
        self.event_type     = event_type
        self.correlation_id = correlation_id or f"COR-{uuid.uuid4().hex[:12].upper()}"
        self.timestamp      = datetime.now(timezone.utc).isoformat()
        self.payload        = payload

    def to_dict(self) -> dict:
        return {
            "event_type":     self.event_type,
            "event_id":       self.event_id,
            "correlation_id": self.correlation_id,
            "timestamp":      self.timestamp,
            "payload":        self.payload,
        }

    def __repr__(self) -> str:
        return f"DomainEvent({self.event_type}, id={self.event_id})"


# ---------------------------------------------------------------------------
# Event Bus
# ---------------------------------------------------------------------------

Handler = Callable[[DomainEvent], None]


class EventBus:
    """
    Bus d'événements synchrone en mémoire.
    En production, il serait remplacé par un adaptateur RabbitMQ / Kafka.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._history: list[DomainEvent] = []
        self._logger = _get_logger("billetterie.eventbus")

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        self._history.append(event)
        self._logger.info(
            f"Événement publié : {event.event_type}",
            extra={
                "correlation_id": event.correlation_id,
                "event_type":     event.event_type,
                "event_id":       event.event_id,
            },
        )
        for handler in self._subscribers.get(event.event_type, []):
            handler(event)

    def published_events(self, event_type: str | None = None) -> list[DomainEvent]:
        if event_type:
            return [e for e in self._history if e.event_type == event_type]
        return list(self._history)


# ---------------------------------------------------------------------------
# ContexteNotification — consommateur d'événements
# ---------------------------------------------------------------------------

class ContexteNotification:
    """
    Contexte générique (Notification) :
    - S'abonne à RéservationConfirmée → simule l'envoi d'un email de confirmation
    - S'abonne à RéservationAnnulée  → simule l'envoi d'un email d'annulation
    """

    def __init__(self, bus: EventBus) -> None:
        self._logger = _get_logger("billetterie.notification")
        self.notifications_envoyees: list[dict] = []

        bus.subscribe("RéservationConfirmée", self._on_reservation_confirmee)
        bus.subscribe("RéservationAnnulée",   self._on_reservation_annulee)

    def _on_reservation_confirmee(self, event: DomainEvent) -> None:
        p = event.payload
        notif = {
            "type":           "email_confirmation",
            "spectateur_id":  p["spectateur_id"],
            "reservation_id": p["reservation_id"],
            "nb_billets":     len(p.get("billets", [])),
            "correlation_id": event.correlation_id,
        }
        self.notifications_envoyees.append(notif)
        self._logger.info(
            f"Email de confirmation envoyé à {p['spectateur_id']}",
            extra={
                "correlation_id": event.correlation_id,
                "event_type":     event.event_type,
                "context":        "ContexteNotification",
            },
        )

    def _on_reservation_annulee(self, event: DomainEvent) -> None:
        p = event.payload
        notif = {
            "type":           "email_annulation",
            "spectateur_id":  p["spectateur_id"],
            "reservation_id": p["reservation_id"],
            "correlation_id": event.correlation_id,
        }
        self.notifications_envoyees.append(notif)
        self._logger.info(
            f"Email d'annulation envoyé à {p['spectateur_id']}",
            extra={
                "correlation_id": event.correlation_id,
                "event_type":     event.event_type,
                "context":        "ContexteNotification",
            },
        )


# ---------------------------------------------------------------------------
# ContexteContrôleAccès — consommateur d'événements
# ---------------------------------------------------------------------------

class ContexteControleAcces:
    """
    Contexte de support (ContrôleAccès) :
    - S'abonne à RéservationConfirmée → active les QR codes
    - S'abonne à RéservationAnnulée   → invalide les QR codes
    """

    def __init__(self, bus: EventBus) -> None:
        self._logger = _get_logger("billetterie.controle_acces")
        self.qr_codes_actifs: set[str] = set()

        bus.subscribe("RéservationConfirmée", self._on_reservation_confirmee)
        bus.subscribe("RéservationAnnulée",   self._on_reservation_annulee)

    def _on_reservation_confirmee(self, event: DomainEvent) -> None:
        for billet in event.payload.get("billets", []):
            self.qr_codes_actifs.add(billet["qr_code"])
        self._logger.info(
            f"{len(event.payload.get('billets', []))} QR code(s) activé(s)",
            extra={
                "correlation_id": event.correlation_id,
                "event_type":     event.event_type,
                "context":        "ContexteContrôleAccès",
            },
        )

    def _on_reservation_annulee(self, event: DomainEvent) -> None:
        reservation_id = event.payload["reservation_id"]
        avant = len(self.qr_codes_actifs)
        self.qr_codes_actifs = {
            qr for qr in self.qr_codes_actifs if reservation_id not in qr
        }
        invalides = avant - len(self.qr_codes_actifs)
        self._logger.info(
            f"{invalides} QR code(s) invalidé(s)",
            extra={
                "correlation_id": event.correlation_id,
                "event_type":     event.event_type,
                "context":        "ContexteContrôleAccès",
            },
        )
