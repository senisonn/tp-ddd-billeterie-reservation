# Scénarios d'intégration

## Scénario end-to-end : Réservation complète avec paiement

Ce scénario décrit le parcours complet d'un spectateur qui réserve des billets pour un concert, depuis la requête initiale jusqu'à la génération des billets électroniques, en traversant plusieurs bounded contexts et couches de l'architecture hexagonale.

Marie, spectatrice authentifiée (CLI-2025-00089), souhaite réserver 2 places pour le Concert Jazz (EVT-2025-00034). Elle envoie une requête `POST /api/reservations` via l'application web. Le contrôleur REST (adaptateur entrant du ContexteRéservation) reçoit la requête et la transforme en commande `CréerRéservationCommande`.

Le service applicatif `CréerRéservation` commence par interroger le ContexteProgrammation via une API REST synchrone pour vérifier que l'événement existe, que les ventes sont ouvertes et que les places A12 et A13 sont disponibles. Le ContexteProgrammation confirme la disponibilité.

Le service applicatif appelle ensuite le ContexteTarification via une API REST synchrone, en fournissant les identifiants des places, l'identifiant du spectateur et le code de réduction « ETUDIANT2025 ». Le ContexteTarification consulte le ContexteCompteClient pour vérifier le profil étudiant de Marie, calcule le montant (90 € de base - 18 € de réduction + 4 € de frais = 76 €) et retourne le MontantTarifé.

Le domaine Réservation crée l'agrégat avec les invariants vérifiés (2 places, places disponibles). La réservation est persistée en base via le RéservationRepository (PostgreSQL). Un événement `RéservationCréée` est publié sur le broker RabbitMQ. La jauge de l'événement est décrémentée de 2 dans le ContexteProgrammation.

Marie procède au paiement. Le ContexteRéservation redirige vers le formulaire de paiement du ContextePaiement. Celui-ci transmet la requête à Stripe via l'ACL. Stripe traite la transaction et envoie un webhook de confirmation. L'ACL traduit le webhook en événement métier `PaiementAccepté`.

Le service applicatif `ConfirmerRéservation` reçoit l'événement `PaiementAccepté`, met à jour le statut de la réservation à « Confirmée » et génère les billets avec QR codes uniques. L'événement `RéservationConfirmée` est publié sur le broker.

Le ContexteNotification consomme l'événement `RéservationConfirmée` et envoie un email de confirmation à Marie avec les billets en pièce jointe (PDF avec QR codes).

## Diagramme de séquence

```
Spectateur    Ctrl REST     SvcApp         Programmation   Tarification   Paiement    Notification
    │             │            │                │               │             │             │
    │──POST /api──►│            │                │               │             │             │
    │  réservation │            │                │               │             │             │
    │             │──Commande──►│                │               │             │             │
    │             │            │──GET événement─►│               │             │             │
    │             │            │◄──Dispo OK──────│               │             │             │
    │             │            │──POST calcul───────────────────►│             │             │
    │             │            │◄──MontantTarifé────────────────│             │             │
    │             │            │                │               │             │             │
    │             │            │  Créer agrégat  │               │             │             │
    │             │            │  Vérifier inv.  │               │             │             │
    │             │            │  Persister      │               │             │             │
    │             │            │──Publier evt────────────────────────────────────────────────►│
    │             │◄──201──────│                │               │             │             │
    │◄──Réponse───│            │                │               │             │             │
    │             │            │                │               │             │             │
    │──Paiement──────────────────────────────────────────────────►│             │             │
    │             │            │                │               │ │──Stripe───►│             │
    │             │            │                │               │ │◄──Webhook──│             │
    │             │            │◄──PaiementOK──────────────────────│             │             │
    │             │            │                │               │             │             │
    │             │            │  Confirmer rés. │               │             │             │
    │             │            │  Générer billets│               │             │             │
    │             │            │──Publier evt────────────────────────────────────────────────►│
    │             │            │                │               │             │  Envoi email │
    │◄──────────────────────────────────────────────────────────────────────────Email+billets│
    │             │            │                │               │             │             │
```
