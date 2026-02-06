# Agrégats et invariants

## Agrégat 1 : Réservation

**Racine de l'agrégat :** Réservation

**Entités / Objets Valeur internes :**
- PlaceAssignée (OV) — les places sélectionnées
- MontantTarifé (OV) — le montant calculé
- Billet (Entité interne) — les billets générés après confirmation

### Invariants

| Invariant | Description métier | Conséquence si non respecté |
|-----------|-------------------|----------------------------|
| INV-R1 : Limite de places par réservation | Une réservation doit contenir entre 1 et 10 places. Cette limite prévient les achats massifs par des revendeurs et garantit un accès équitable pour tous les spectateurs. La vérification est effectuée à la création et à chaque modification du panier. | Si moins d'1 place : la réservation n'a pas de sens et ne peut être créée. Si plus de 10 places : risque de monopolisation des places par un seul acheteur au détriment des autres spectateurs. |
| INV-R2 : Unicité des places dans une réservation | Chaque place (identifiée par zone + rangée + numéro) ne peut apparaître qu'une seule fois dans une même réservation et ne doit pas être déjà réservée pour le même événement dans une autre réservation active. | Double attribution de la même place physique à deux spectateurs différents, entraînant un conflit le jour de l'événement et une perte de confiance dans le système. |
| INV-R3 : Confirmation conditionnée au paiement | Une réservation ne peut passer au statut « Confirmée » que si un paiement accepté lui est associé. Le montant du paiement doit correspondre exactement au montant total de la réservation. | Si la confirmation se fait sans paiement : perte financière pour l'organisation. Si le montant ne correspond pas : incohérence comptable et litige potentiel avec le spectateur. |
| INV-R4 : Irréversibilité des statuts terminaux | Une réservation au statut « Annulée » ou « Remboursée » ne peut plus être modifiée ni réactivée. Ces statuts sont des états terminaux du cycle de vie de la réservation. | Risque de réactivation frauduleuse de réservations annulées, entraînant des billets non payés ou des incohérences dans la jauge de disponibilité. |

## Agrégat 2 : Événement

**Racine de l'agrégat :** Événement

**Entités / Objets Valeur internes :**
- PériodeDeVente (OV) — la fenêtre de vente
- Catégorie (OV) — les catégories de places avec tarifs de base
- ConfigurationSalle (OV) — la configuration des places dans la salle

### Invariants

| Invariant | Description métier | Conséquence si non respecté |
|-----------|-------------------|----------------------------|
| INV-E1 : Jauge non négative | La jauge disponible (nombre de places restantes) ne peut jamais être inférieure à zéro. À chaque réservation confirmée, la jauge est décrémentée. À chaque annulation, elle est incrémentée. La jauge est bornée par la capacité totale de la salle. | Des places seraient vendues alors qu'elles n'existent pas physiquement, entraînant une sur-réservation avec des spectateurs sans siège le jour de l'événement. |
| INV-E2 : Événement complet bloque les ventes | Lorsque la jauge atteint zéro, le statut de vente de l'événement doit automatiquement passer à « Complet » et aucune nouvelle réservation ne peut être acceptée tant que des places ne sont pas libérées (annulation). | Acceptation de réservations au-delà de la capacité, même situation de sur-réservation que INV-E1. |
| INV-E3 : Ventes dans la période autorisée | Les réservations ne peuvent être acceptées que pendant la période de vente définie. Avant l'ouverture des ventes, les places sont visibles mais non réservables. Après la fin des ventes (ou après la date de l'événement), plus aucune réservation n'est possible. | Ventes prématurées avant l'annonce officielle, ou ventes après la tenue de l'événement, ce qui n'a aucun sens métier et crée des obligations de remboursement. |

## Schéma UML des agrégats

```
┌─────────────────────────────────────────────────────────────┐
│                  Agrégat « Réservation »                    │
│  ┌─────────────────────────────────────────────────┐        │
│  │           «Racine» Réservation                  │        │
│  │  réservationId, statut, dateRéservation         │        │
│  │                                                 │        │
│  │  ┌──────────────┐  ┌──────────────┐             │        │
│  │  │«OV» Place    │  │«OV» Montant  │             │        │
│  │  │ Assignée     │  │  Tarifé      │             │        │
│  │  │ [1..10]      │  │ [1]          │             │        │
│  │  └──────────────┘  └──────────────┘             │        │
│  │                                                 │        │
│  │  ┌──────────────┐                               │        │
│  │  │«Entité»      │                               │        │
│  │  │ Billet       │                               │        │
│  │  │ [0..10]      │                               │        │
│  │  └──────────────┘                               │        │
│  └─────────────────────────────────────────────────┘        │
│  Invariants : INV-R1, INV-R2, INV-R3, INV-R4               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Agrégat « Événement »                      │
│  ┌─────────────────────────────────────────────────┐        │
│  │           «Racine» Événement                    │        │
│  │  événementId, nom, dateÉvénement, jauge, statut │        │
│  │                                                 │        │
│  │  ┌──────────────┐  ┌──────────────────────┐     │        │
│  │  │«OV» Période  │  │«OV» Configuration   │     │        │
│  │  │  DeVente     │  │     Salle            │     │        │
│  │  │ [1]          │  │ [1]                  │     │        │
│  │  └──────────────┘  └──────────────────────┘     │        │
│  │                                                 │        │
│  │  ┌──────────────┐                               │        │
│  │  │«OV» Catégorie│                               │        │
│  │  │ [1..*]       │                               │        │
│  │  └──────────────┘                               │        │
│  └─────────────────────────────────────────────────┘        │
│  Invariants : INV-E1, INV-E2, INV-E3                        │
└─────────────────────────────────────────────────────────────┘
```
