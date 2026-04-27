# Context Map

## Schéma général

```
                    ┌─────────────────────┐
                    │   ContexteCompte    │
                    │      Client         │
                    └────────┬────────────┘
                             │ Customer/Supplier
                             ▼
┌──────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│  Contexte    │◄───│    Contexte         │───►│   Contexte       │
│Programmation │ CS │   Réservation       │ CS │  Tarification    │
└──────────────┘    └──────┬──────┬───────┘    └──────────────────┘
                           │      │
              Partnership  │      │ ACL
                           ▼      ▼
               ┌───────────┐  ┌──────────────┐
               │ Contexte  │  │  Contexte    │
               │ Contrôle  │  │  Paiement   │
               │  Accès    │  │              │
               └───────────┘  └──────────────┘
                                     │
                           Conformist│
                                     ▼
                           ┌──────────────────┐
                           │    Contexte      │
                           │  Notification    │
                           └──────────────────┘

Légende :
  CS  = Customer/Supplier
  ACL = Anticorruption Layer
  ──► = Direction de la dépendance
```

## Relations et patterns

| Contexte source | Contexte cible | Pattern de relation | Justification |
|----------------|---------------|--------------------|----|
| ContexteRéservation | ContexteProgrammation | Customer/Supplier | Le contexte Réservation (Customer) consomme les données d'événements et de salles fournies par le contexte Programmation (Supplier). La Programmation définit les événements et leurs configurations, la Réservation les utilise sans les modifier. Le Supplier s'engage à fournir une API stable. |
| ContexteRéservation | ContexteTarification | Customer/Supplier | Le contexte Réservation demande au contexte Tarification de calculer le prix des places sélectionnées. La Tarification est le Supplier qui expose un service de calcul de prix. La Réservation n'a pas besoin de connaître les règles tarifaires internes. |
| ContexteRéservation | ContextePaiement | Anticorruption Layer (ACL) | Le contexte Paiement repose sur un prestataire externe avec son propre modèle (transactions, refunds, webhooks). L'ACL traduit les concepts du prestataire en concepts métier (PaiementAccepté, RemboursementEffectué). Cela protège le domaine Réservation des changements d'API du prestataire de paiement. |
| ContexteRéservation | ContexteContrôleAccès | Partnership | Les deux contextes collaborent étroitement : la Réservation génère les billets confirmés et le Contrôle d'Accès les valide. Ils partagent un intérêt commun à maintenir la cohérence des billets. Les deux équipes coordonnent leurs évolutions. |
| ContexteCompteClient | ContexteRéservation | Customer/Supplier | Le contexte Réservation (Customer) a besoin des informations client (profil, abonnement) pour associer une réservation à un spectateur. Le contexte CompteClient (Supplier) fournit ces données via une API. |
| ContexteCompteClient | ContexteTarification | Customer/Supplier | Le contexte Tarification (Customer) a besoin du profil client (étudiant, abonné, senior) pour appliquer les réductions. Le contexte CompteClient (Supplier) fournit ces informations de profil. |
| ContextePaiement | ContexteNotification | Conformist | Le contexte Notification s'adapte au modèle du contexte Paiement pour envoyer les confirmations de paiement et les avis de remboursement. Il accepte le modèle du Paiement tel quel sans transformation. |
| ContexteRéservation | ContexteNotification | Conformist | Le contexte Notification s'adapte aux événements émis par le contexte Réservation (réservation confirmée, annulée, transférée) pour envoyer les messages correspondants aux spectateurs. |

## Intégrations techniques envisagées

### 1. API REST synchrone : Réservation → Tarification
- **Type** : REST synchrone (HTTP/JSON)
- **BCs impliqués** : ContexteRéservation (appelant) → ContexteTarification (appelé)
- **Cas d'usage** : Lorsqu'un spectateur sélectionne des places et demande le calcul du prix total, le contexte Réservation appelle l'API REST du contexte Tarification avec les identifiants de places, l'identifiant client et l'événement. Le service retourne le montant détaillé (tarif de base, réductions, frais de service, total).

### 2. Événements asynchrones via broker : Réservation → Notification
- **Type** : Événements asynchrones (message broker – RabbitMQ)
- **BCs impliqués** : ContexteRéservation (publisher) → ContexteNotification (subscriber)
- **Cas d'usage** : Lorsqu'une réservation est confirmée, annulée ou modifiée, le contexte Réservation publie un événement (ex : `RéservationConfirmée`, `RéservationAnnulée`). Le contexte Notification consomme ces événements et envoie les messages appropriés (email de confirmation, alerte d'annulation) au spectateur.

### 3. Webhook externe avec ACL : Paiement → Réservation
- **Type** : Webhook HTTP (callback asynchrone) avec couche anticorruption
- **BCs impliqués** : Prestataire de paiement externe → ContextePaiement (ACL) → ContexteRéservation
- **Cas d'usage** : Le prestataire de paiement (Stripe) envoie un webhook lors de la confirmation ou du refus d'un paiement. L'ACL du contexte Paiement traduit le webhook Stripe en événement métier (`PaiementAccepté` ou `PaiementRefusé`). Le contexte Réservation réagit en confirmant ou en annulant la réservation.

### 4. API REST synchrone : Réservation → Programmation
- **Type** : REST synchrone (HTTP/JSON)
- **BCs impliqués** : ContexteRéservation (appelant) → ContexteProgrammation (appelé)
- **Cas d'usage** : Le contexte Réservation interroge le contexte Programmation pour obtenir les informations d'un événement (date, salle, plan de salle, disponibilité des ventes). Cette intégration est utilisée lors de la recherche d'événements et de l'affichage du plan de salle.
