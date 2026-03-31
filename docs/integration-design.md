# Design des intégrations inter-contextes

Ce document décrit la conception des intégrations entre les Bounded Contexts, sans les implémenter. Deux types d'intégration sont couverts : une intégration REST synchrone et une intégration par événements asynchrones.

---

## Intégration REST

### Contextes impliqués

**ContexteRéservation** (appelant) → **ContexteTarification** (appelé)

### Schéma de flux

```
  ContexteRéservation                  ContexteTarification
        │                                       │
        │  POST /tarification/calculer          │
        │  {evenement_id, spectateur_id,        │
        │   places, code_reduction}             │
        │──────────────────────────────────────►│
        │                                       │  Applique règles tarifaires
        │                                       │  (tarif de base, réductions,
        │                                       │  frais de service)
        │         200 OK                        │
        │  {tarif_base, reduction,              │
        │   frais_service, total, devise}       │
        │◄──────────────────────────────────────│
        │                                       │
        │  Crée l'agrégat Réservation           │
        │  avec le MontantTarifé reçu           │
        │                                       │
```

### Narration

Lorsqu'un spectateur sélectionne ses places et demande le récapitulatif du prix, le **ContexteRéservation** envoie une requête REST synchrone au **ContexteTarification**. La requête transmet l'identifiant de l'événement, l'identifiant du spectateur (pour récupérer son profil via le ContexteCompteClient), les places choisies et l'éventuel code de réduction.

Le ContexteTarification applique ses règles internes : tarif de base par catégorie, réductions liées au profil (étudiant, senior, abonné) et frais de service de la plateforme. Il retourne un objet `MontantTarifé` immuable contenant le détail du calcul.

Le ContexteRéservation utilise ce montant pour créer l'agrégat Réservation et le présenter au spectateur avant confirmation du paiement. Cette intégration est **synchrone** car le spectateur attend immédiatement le prix avant de décider d'acheter.

La relation est de type **Customer/Supplier** : le ContexteTarification (Supplier) s'engage à fournir une API stable, et le ContexteRéservation (Customer) en dépend sans connaître les règles tarifaires internes.

---

## Intégration par événements

### Contextes impliqués

**ContexteRéservation** (publisher) → **ContexteNotification** (subscriber) + **ContexteContrôleAccès** (subscriber)

### Schéma de flux

```
  ContexteRéservation        Event Bus (broker)       ContexteNotification
        │                          │                          │
        │  Réservation confirmée   │                          │
        │  → publie événement      │                          │
        │  RéservationConfirmée    │                          │
        │─────────────────────────►│                          │
        │                          │  RéservationConfirmée    │
        │                          │─────────────────────────►│
        │                          │                          │  Envoie email
        │                          │                          │  + billets PDF
        │                          │                          │  au spectateur
        │                          │
        │                          │       ContexteContrôleAccès
        │                          │                │
        │                          │  RéservationConfirmée
        │                          │───────────────►│
        │                          │                │  Active les QR codes
        │                          │                │  des billets générés
        │                          │                │
        │  Réservation annulée     │
        │  → publie événement      │
        │  RéservationAnnulée      │
        │─────────────────────────►│
        │                          │  RéservationAnnulée      │
        │                          │─────────────────────────►│  Email annulation
        │                          │
        │                          │  RéservationAnnulée    ContexteContrôleAccès
        │                          │───────────────────────►│  Invalide QR codes
```

### Narration

Lorsque la réservation passe au statut « Confirmée » (après réception du paiement), le **ContexteRéservation** publie l'événement `RéservationConfirmée` sur le broker de messages. Cet événement contient l'identifiant de la réservation, l'identifiant du spectateur et la liste des billets générés (avec leurs QR codes).

Le **ContexteNotification** consomme cet événement de manière asynchrone et envoie un email de confirmation au spectateur, incluant les billets électroniques en pièce jointe (format PDF avec QR codes). Le canal d'envoi (email, SMS, push) est déterminé par les préférences du spectateur stockées dans le ContexteCompteClient.

Le **ContexteContrôleAccès** consomme le même événement pour activer les QR codes dans son registre local, les rendant valides pour la vérification à l'entrée le jour de l'événement.

En cas d'annulation, le ContexteRéservation publie `RéservationAnnulée`. Le ContexteNotification envoie une alerte d'annulation et le ContexteContrôleAccès invalide les QR codes correspondants.

Cette intégration est **asynchrone** car ni la notification ni l'activation des QR codes ne bloquent la réponse au spectateur. La relation est de type **Conformist** : le ContexteNotification et le ContexteContrôleAccès s'adaptent au modèle d'événement publié par le ContexteRéservation sans négociation.
