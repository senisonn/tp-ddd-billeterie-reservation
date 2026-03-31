"""
Adaptateur REST — ContexteRéservation
Couche Adapters (hexagonale) : expose le domaine via HTTP.
Dépendances : stdlib uniquement (http.server, json, logging).
"""
from __future__ import annotations

import json
import logging
import sys
import threading
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Logging structuré (JSON)
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for attr in ("correlation_id", "reservation_id", "spectateur_id", "duration_ms"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        return json.dumps(entry, ensure_ascii=False)


def _setup_logger() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    logger = logging.getLogger("billetterie.rest")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


logger = _setup_logger()

# ---------------------------------------------------------------------------
# Métriques simples (compteurs en mémoire)
# ---------------------------------------------------------------------------

_metrics: dict[str, Any] = {
    "reservations_creees_total":    0,   # métier
    "reservations_confirmees_total": 0,  # métier
    "http_requests_total":          0,   # technique
    "http_errors_total":            0,   # technique
    "jauge_disponible":             {},  # libre (par événement)
}


def _inc(name: str) -> None:
    _metrics[name] += 1


def get_metrics() -> dict[str, Any]:
    return dict(_metrics)

# ---------------------------------------------------------------------------
# Handler HTTP
# ---------------------------------------------------------------------------

class ReservationHandler(BaseHTTPRequestHandler):
    """
    Routes :
      POST /api/reservations          → creer_reservation
      GET  /api/reservations/{id}     → get_reservation
      POST /api/reservations/{id}/confirmer → confirmer_paiement
      GET  /metrics                   → exposition des métriques
    """

    # Référence vers le ServiceReservation injecté au démarrage du serveur
    service = None
    repo_reservations = None

    def log_message(self, fmt: str, *args: Any) -> None:
        # On redirige les logs vers notre logger structuré
        logger.info(fmt % args)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _correlation_id(self) -> str:
        return self.headers.get("X-Correlation-ID") or f"COR-{uuid.uuid4().hex[:12].upper()}"

    def _send_json(self, status: int, body: dict, correlation_id: str) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Correlation-ID", correlation_id)
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _reservation_to_dict(self, res) -> dict:
        return {
            "reservation_id": res.reservation_id,
            "statut":         res.statut.name,
            "evenement_id":   res.evenement_id,
            "spectateur_id":  res.spectateur_id,
            "montant_total":  res.montant.total,
            "nb_places":      len(res.places),
            "billets": [
                {"billet_id": b.billet_id, "qr_code": b.qr_code}
                for b in res.billets
            ],
        }

    # ------------------------------------------------------------------ #
    #  Routing                                                             #
    # ------------------------------------------------------------------ #

    def do_GET(self) -> None:
        _inc("http_requests_total")
        cid = self._correlation_id()
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        # GET /metrics
        if parts == ["metrics"]:
            self._send_json(200, get_metrics(), cid)
            return

        # GET /api/reservations/{id}
        if len(parts) == 3 and parts[:2] == ["api", "reservations"]:
            reservation_id = parts[2]
            try:
                res = self.repo_reservations.trouver_par_id(reservation_id)
                logger.info(
                    "GET reservation",
                    extra={"correlation_id": cid, "reservation_id": reservation_id},
                )
                self._send_json(200, self._reservation_to_dict(res), cid)
            except KeyError:
                _inc("http_errors_total")
                self._send_json(404, {"code": "NOT_FOUND", "message": f"{reservation_id} introuvable"}, cid)
            return

        _inc("http_errors_total")
        self._send_json(404, {"code": "NOT_FOUND", "message": "Route inconnue"}, cid)

    def do_POST(self) -> None:
        _inc("http_requests_total")
        cid = self._correlation_id()
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        # POST /api/reservations
        if parts == ["api", "reservations"]:
            self._handle_creer_reservation(cid)
            return

        # POST /api/reservations/{id}/confirmer
        if len(parts) == 4 and parts[:2] == ["api", "reservations"] and parts[3] == "confirmer":
            self._handle_confirmer_paiement(parts[2], cid)
            return

        _inc("http_errors_total")
        self._send_json(404, {"code": "NOT_FOUND", "message": "Route inconnue"}, cid)

    # ------------------------------------------------------------------ #
    #  Handlers métier                                                     #
    # ------------------------------------------------------------------ #

    def _handle_creer_reservation(self, cid: str) -> None:
        from tests.integration.test_scenario import (
            MontantTarife, PlaceAssignee, ErreurDomaine
        )
        body = self._read_body()
        try:
            places = [
                PlaceAssignee(
                    zone=p["zone"], rangee=p["rangee"],
                    numero=p["numero"], categorie=p.get("categorie", "Orchestre")
                )
                for p in body.get("places", [])
            ]
            m = body["montant"]
            montant = MontantTarife(
                tarif_base=m["tarif_base"],
                reduction=m["reduction"],
                frais_service=m["frais_service"],
            )
            res = self.service.creer_reservation(
                spectateur_id=body["spectateur_id"],
                evenement_id=body["evenement_id"],
                places=places,
                montant=montant,
                aujourd_hui=date.today(),
            )
            _inc("reservations_creees_total")
            logger.info(
                "Réservation créée",
                extra={
                    "correlation_id": cid,
                    "reservation_id": res.reservation_id,
                    "spectateur_id":  res.spectateur_id,
                },
            )
            self._send_json(201, self._reservation_to_dict(res), cid)
        except ErreurDomaine as e:
            _inc("http_errors_total")
            self._send_json(400, {"code": "ERREUR_METIER", "message": str(e), "correlation_id": cid}, cid)

    def _handle_confirmer_paiement(self, reservation_id: str, cid: str) -> None:
        from tests.integration.test_scenario import ErreurDomaine
        body = self._read_body()
        try:
            res = self.service.confirmer_paiement(
                reservation_id=reservation_id,
                montant_paye=float(body.get("montant_paye", 0)),
            )
            _inc("reservations_confirmees_total")
            logger.info(
                "Réservation confirmée",
                extra={"correlation_id": cid, "reservation_id": reservation_id},
            )
            self._send_json(200, self._reservation_to_dict(res), cid)
        except ErreurDomaine as e:
            _inc("http_errors_total")
            self._send_json(400, {"code": "ERREUR_METIER", "message": str(e), "correlation_id": cid}, cid)


# ---------------------------------------------------------------------------
# Lancement du serveur
# ---------------------------------------------------------------------------

def demarrer_serveur(service, repo_reservations, host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    ReservationHandler.service = service
    ReservationHandler.repo_reservations = repo_reservations

    server = HTTPServer((host, port), ReservationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Serveur démarré sur http://{host}:{port}")
    return server
