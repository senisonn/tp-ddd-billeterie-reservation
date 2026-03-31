# Contrats d'intégration — Billetterie & Réservation

## 5.1 Contrats d'échange inter-contextes

Trois formats sont utilisés selon le type d'intégration :
- **OpenAPI 3.0** pour les échanges REST synchrones
- **JSON Schema** pour les événements asynchrones publiés sur l'event bus

---

## REST — OpenAPI 3.0

### POST `/api/reservations` — Créer une réservation

```yaml
openapi: "3.0.3"
info:
  title: Billetterie & Réservation API
  version: "1.0.0"

paths:
  /api/reservations:
    post:
      summary: Créer une réservation
      operationId: creerReservation
      parameters:
        - in: header
          name: X-Correlation-ID
          schema:
            type: string
          required: false
          description: Identifiant de corrélation pour le traçage inter-services
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreerReservationRequest'
            example:
              spectateur_id: "CLI-2025-00042"
              evenement_id:  "EVT-2025-00010"
              places:
                - zone: "A"
                  rangee: "1"
                  numero: 1
                  categorie: "Orchestre"
                - zone: "A"
                  rangee: "1"
                  numero: 2
                  categorie: "Orchestre"
              montant:
                tarif_base: 90.0
                reduction: 18.0
                frais_service: 4.0
      responses:
        "201":
          description: Réservation créée (statut EnAttente)
          headers:
            X-Correlation-ID:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'
        "400":
          description: Données invalides (INV-R1, INV-R2)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurMetier'
        "409":
          description: Place déjà réservée (INV-R2) ou événement complet (INV-E2)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurMetier'

  /api/reservations/{reservation_id}:
    get:
      summary: Récupérer l'état d'une réservation
      operationId: getReservation
      parameters:
        - in: path
          name: reservation_id
          required: true
          schema:
            type: string
            pattern: "^RES-[A-Z0-9]{8}$"
        - in: header
          name: X-Correlation-ID
          schema:
            type: string
      responses:
        "200":
          description: Réservation trouvée
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'
        "404":
          description: Réservation introuvable

  /api/reservations/{reservation_id}/confirmer:
    post:
      summary: Confirmer le paiement d'une réservation
      operationId: confirmerPaiement
      parameters:
        - in: path
          name: reservation_id
          required: true
          schema:
            type: string
        - in: header
          name: X-Correlation-ID
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [montant_paye]
              properties:
                montant_paye:
                  type: number
                  example: 76.0
      responses:
        "200":
          description: Réservation confirmée, billets générés
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReservationResponse'
        "400":
          description: Montant incorrect ou paiement invalide (INV-R3)

components:
  schemas:
    CreerReservationRequest:
      type: object
      required: [spectateur_id, evenement_id, places, montant]
      properties:
        spectateur_id:
          type: string
          pattern: "^CLI-[0-9]{4}-[0-9]{5}$"
        evenement_id:
          type: string
          pattern: "^EVT-[0-9]{4}-[0-9]{5}$"
        places:
          type: array
          minItems: 1
          maxItems: 10
          items:
            $ref: '#/components/schemas/PlaceAssignee'
        montant:
          $ref: '#/components/schemas/MontantTarife'

    PlaceAssignee:
      type: object
      required: [zone, rangee, numero]
      properties:
        zone:      { type: string }
        rangee:    { type: string }
        numero:    { type: integer, minimum: 1 }
        categorie: { type: string, enum: [Orchestre, Mezzanine, Balcon] }

    MontantTarife:
      type: object
      required: [tarif_base, reduction, frais_service]
      properties:
        tarif_base:    { type: number, minimum: 0 }
        reduction:     { type: number, minimum: 0 }
        frais_service: { type: number, minimum: 0 }
        devise:        { type: string, default: EUR }

    ReservationResponse:
      type: object
      properties:
        reservation_id: { type: string }
        statut:
          type: string
          enum: [EnAttente, Confirmee, Annulee, Remboursee]
        evenement_id:   { type: string }
        spectateur_id:  { type: string }
        montant_total:  { type: number }
        places_choisies:
          description: >
            Présent uniquement au statut EnAttente. Représente les places
            sélectionnées avant confirmation. Absent une fois les billets générés.
          type: array
          items:
            $ref: '#/components/schemas/PlaceAssignee'
        billets:
          description: >
            Présent uniquement aux statuts Confirmee / Annulee / Remboursee.
            Chaque billet porte sa PlaceAssignée, son QR code et son statut.
          type: array
          items:
            $ref: '#/components/schemas/Billet'

    Billet:
      type: object
      properties:
        billet_id: { type: string, example: "BIL-2025-00283" }
        qr_code:   { type: string, example: "QR-X7K9M-2025-00283" }
        statut:
          type: string
          enum: [Valide, Utilise, Annule]
        place:
          $ref: '#/components/schemas/PlaceAssignee'

    ErreurMetier:
      type: object
      required: [code, message]
      properties:
        code:           { type: string }
        message:        { type: string }
        correlation_id: { type: string }
```

---

## Événements — JSON Schema

### `ReservationCréée`

Publié par **ContexteRéservation** → consommé par **ContexteNotification**, **ContexteContrôleAccès**.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12",
  "$id": "reservation-creee-v1",
  "title": "ReservationCréée",
  "type": "object",
  "required": ["event_type", "event_id", "correlation_id", "timestamp", "payload"],
  "properties": {
    "event_type":     { "const": "ReservationCréée" },
    "event_id":       { "type": "string" },
    "correlation_id": { "type": "string" },
    "timestamp":      { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["reservation_id", "evenement_id", "spectateur_id", "nb_places", "montant_total"],
      "properties": {
        "reservation_id": { "type": "string" },
        "evenement_id":   { "type": "string" },
        "spectateur_id":  { "type": "string" },
        "nb_places":      { "type": "integer", "minimum": 1, "maximum": 10 },
        "montant_total":  { "type": "number" }
      }
    }
  }
}
```

**Exemple :**
```json
{
  "event_type": "ReservationCréée",
  "event_id": "EVE-A1B2C3D4",
  "correlation_id": "COR-20250210-XYZ789",
  "timestamp": "2025-02-10T14:32:00Z",
  "payload": {
    "reservation_id": "RES-ABC12345",
    "evenement_id":   "EVT-2025-00010",
    "spectateur_id":  "CLI-2025-00042",
    "nb_places":      2,
    "montant_total":  76.0
  }
}
```

---

### `RéservationConfirmée`

Publié par **ContexteRéservation** → consommé par **ContexteNotification** (envoi email + billets), **ContexteContrôleAccès** (activation QR codes).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12",
  "$id": "reservation-confirmee-v1",
  "title": "RéservationConfirmée",
  "type": "object",
  "required": ["event_type", "event_id", "correlation_id", "timestamp", "payload"],
  "properties": {
    "event_type":     { "const": "RéservationConfirmée" },
    "event_id":       { "type": "string" },
    "correlation_id": { "type": "string" },
    "timestamp":      { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["reservation_id", "spectateur_id", "billets"],
      "properties": {
        "reservation_id": { "type": "string" },
        "spectateur_id":  { "type": "string" },
        "montant_paye":   { "type": "number" },
        "billets": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "billet_id": { "type": "string" },
              "qr_code":   { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

### `RéservationAnnulée`

Publié par **ContexteRéservation** → consommé par **ContexteNotification**, **ContextePaiement** (remboursement).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12",
  "$id": "reservation-annulee-v1",
  "title": "RéservationAnnulée",
  "type": "object",
  "required": ["event_type", "event_id", "correlation_id", "timestamp", "payload"],
  "properties": {
    "event_type":     { "const": "RéservationAnnulée" },
    "event_id":       { "type": "string" },
    "correlation_id": { "type": "string" },
    "timestamp":      { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["reservation_id", "evenement_id", "spectateur_id", "nb_places_liberees"],
      "properties": {
        "reservation_id":    { "type": "string" },
        "evenement_id":      { "type": "string" },
        "spectateur_id":     { "type": "string" },
        "nb_places_liberees":{ "type": "integer" },
        "montant_rembourse": { "type": "number" }
      }
    }
  }
}
```

---

## Tableau récapitulatif

| Contrat                  | Format     | Producteur              | Consommateur(s)                              | Transport    |
|--------------------------|------------|-------------------------|----------------------------------------------|--------------|
| `POST /api/reservations` | OpenAPI    | Client / Front          | ContexteRéservation                          | REST / HTTP  |
| `GET /api/reservations/{id}` | OpenAPI | Client / Front      | ContexteRéservation                          | REST / HTTP  |
| `ReservationCréée`       | JSON Schema| ContexteRéservation     | ContexteNotification, ContexteContrôleAccès  | Event Bus    |
| `RéservationConfirmée`   | JSON Schema| ContexteRéservation     | ContexteNotification, ContexteContrôleAccès  | Event Bus    |
| `RéservationAnnulée`     | JSON Schema| ContexteRéservation     | ContexteNotification, ContextePaiement       | Event Bus    |
