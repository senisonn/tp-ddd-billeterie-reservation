# Architecture hexagonale

## Description des couches

### Domain (coeur métier)

La couche Domain contient l'ensemble des règles métier pures du système de billetterie. Elle regroupe les entités (Réservation, Événement, Spectateur), les objets valeur (MontantTarifé, PlaceAssignée, PériodeDeVente), les agrégats avec leurs invariants, ainsi que les événements de domaine (RéservationConfirmée, PaiementAccepté). Cette couche n'a aucune dépendance technique : elle ne connaît ni la base de données, ni les API REST, ni le broker de messages. Elle définit également les interfaces (ports) que les couches extérieures doivent implémenter, comme `RéservationRepository` ou `ServiceDePaiement`.

### Application (orchestration)

La couche Application orchestre les cas d'utilisation métier en coordonnant les appels entre le Domain et les ports. Elle contient les services applicatifs (ou « use cases ») tels que `CréerRéservation`, `ConfirmerPaiement`, `AnnulerRéservation`. Chaque service applicatif reçoit une commande, charge les agrégats nécessaires via les repositories, exécute la logique métier du domaine, persiste les changements et publie les événements de domaine. Cette couche gère également les transactions et la coordination entre bounded contexts.

### Adapters (interfaces techniques)

La couche Adapters implémente les ports définis par le domaine et fournit les connecteurs techniques concrets. Elle se divise en deux types : les **adaptateurs entrants** (driving adapters) qui reçoivent les requêtes externes — contrôleurs REST, consommateurs de messages, interfaces CLI — et les **adaptateurs sortants** (driven adapters) qui communiquent avec l'infrastructure — implémentations de repositories (PostgreSQL), clients de paiement (Stripe), services d'envoi de notifications (SendGrid, Twilio), broker de messages (RabbitMQ). Chaque adaptateur traduit entre le format technique et le modèle du domaine.

## Exemple de flux (commande → réponse)

**Cas concret : Un spectateur réserve 2 places pour le Concert Jazz**

1. Le spectateur envoie une requête HTTP `POST /api/reservations` avec les identifiants de l'événement, les places choisies et son identifiant client. Le **contrôleur REST** (adaptateur entrant) reçoit la requête et la convertit en commande `CréerRéservationCommande`.

2. Le **service applicatif** `CréerRéservation` prend en charge la commande. Il charge l'agrégat Événement via le `ÉvénementRepository` (port sortant) pour vérifier la disponibilité des places et la validité de la période de vente.

3. Le service appelle le **port** `ServiceDeTarification` pour obtenir le `MontantTarifé` des places sélectionnées. L'adaptateur sortant appelle l'API REST du contexte Tarification.

4. Le **domaine** crée l'agrégat Réservation avec les PlaceAssignée et le MontantTarifé. Les invariants sont vérifiés (nombre de places entre 1 et 10, places disponibles). L'événement de domaine `RéservationCréée` est émis.

5. Le service applicatif persiste la Réservation via le `RéservationRepository` (adaptateur sortant → PostgreSQL) et publie l'événement `RéservationCréée` sur le broker (adaptateur sortant → RabbitMQ).

6. Le **contrôleur REST** retourne la réponse HTTP 201 avec les détails de la réservation au format JSON.

```
                         Requête HTTP
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│              ADAPTERS (entrants)                    │
│         Contrôleur REST /api/reservations           │
└────────────────────────┬────────────────────────────┘
                         │ CréerRéservationCommande
                         ▼
┌─────────────────────────────────────────────────────┐
│              APPLICATION                            │
│         UseCase : CréerRéservation                  │
└──────┬─────────────────┬────────────────────────────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│   DOMAIN     │  │   DOMAIN     │
│ Événement    │  │ Réservation  │
│ (vérif.      │  │ (création,   │
│  jauge)      │  │  invariants) │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌─────────────────────────────────────────────────────┐
│              ADAPTERS (sortants)                    │
│  PostgreSQL Repository │ RabbitMQ Publisher          │
│  Stripe Client          │ SendGrid Mailer            │
└─────────────────────────────────────────────────────┘
```
