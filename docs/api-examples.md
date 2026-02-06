# Exemples d'API REST

## Endpoint 1 : Créer une réservation

- **Méthode + URL** : `POST /api/reservations`
- **Description** : Crée une nouvelle réservation pour un spectateur. Le système vérifie la disponibilité des places, calcule le tarif via le contexte Tarification, crée l'agrégat Réservation au statut « EnAttente » et réserve temporairement les places (panier de 10 minutes).

**Exemple de requête :**

```json
{
  "événementId": "EVT-2025-00034",
  "spectateurId": "CLI-2025-00089",
  "places": [
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 12
    },
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 13
    }
  ],
  "codeRéduction": "ETUDIANT2025"
}
```

**Exemple de réponse (201 Created) :**

```json
{
  "réservationId": "RES-2025-00142",
  "statut": "EnAttente",
  "événement": {
    "événementId": "EVT-2025-00034",
    "nom": "Concert Jazz - Miles & Friends",
    "date": "2025-03-15T20:30:00"
  },
  "places": [
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 12,
      "catégorie": "Premium"
    },
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 13,
      "catégorie": "Premium"
    }
  ],
  "montant": {
    "tarifBase": 90.00,
    "réduction": 18.00,
    "fraisDeService": 4.00,
    "total": 76.00,
    "devise": "EUR"
  },
  "expiration": "2025-02-10T15:35:00",
  "dateRéservation": "2025-02-10T15:25:00"
}
```

## Endpoint 2 : Consulter une réservation

- **Méthode + URL** : `GET /api/reservations/{réservationId}`
- **Description** : Récupère l'état complet d'une réservation existante, incluant les détails de l'événement, les places assignées, le montant tarifé, le statut courant et les billets associés (si la réservation est confirmée).

**Exemple de requête :**

```
GET /api/reservations/RES-2025-00142
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple de réponse (200 OK) :**

```json
{
  "réservationId": "RES-2025-00142",
  "statut": "Confirmée",
  "événement": {
    "événementId": "EVT-2025-00034",
    "nom": "Concert Jazz - Miles & Friends",
    "date": "2025-03-15T20:30:00",
    "salle": "Grande Salle"
  },
  "spectateur": {
    "spectateurId": "CLI-2025-00089",
    "nom": "Marie Dupont"
  },
  "places": [
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 12,
      "catégorie": "Premium"
    },
    {
      "zone": "Orchestre",
      "rangée": "A",
      "numéro": 13,
      "catégorie": "Premium"
    }
  ],
  "montant": {
    "tarifBase": 90.00,
    "réduction": 18.00,
    "fraisDeService": 4.00,
    "total": 76.00,
    "devise": "EUR"
  },
  "billets": [
    {
      "billetId": "BIL-2025-00283",
      "place": "Orchestre A12",
      "qrCode": "QR-X7K9M-2025-00283",
      "statut": "Valide"
    },
    {
      "billetId": "BIL-2025-00284",
      "place": "Orchestre A13",
      "qrCode": "QR-P3L2N-2025-00284",
      "statut": "Valide"
    }
  ],
  "dateRéservation": "2025-02-10T15:25:00",
  "dateConfirmation": "2025-02-10T15:27:00"
}
```
