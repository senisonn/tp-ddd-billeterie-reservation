# Scénarios de test de domaine

### Invariant 1 : INV-R1 – Limite de places par réservation

#### Scénario 1 – Happy path

- **Given** : Un spectateur authentifié et un événement « Concert Jazz » avec 50 places disponibles.
- **When** : Le spectateur crée une réservation avec 3 places (A1, A2, A3) en catégorie Orchestre.
- **Then** : La réservation est créée avec succès au statut « EnAttente », contenant les 3 places sélectionnées. La jauge de l'événement est décrémentée de 3 (47 places restantes).

#### Scénario 2 – Sad path

- **Given** : Un spectateur authentifié et un événement « Concert Jazz » avec 50 places disponibles.
- **When** : Le spectateur tente de créer une réservation avec 12 places.
- **Then** : Le système refuse la réservation avec l'erreur « Le nombre de places doit être compris entre 1 et 10 ». Aucune réservation n'est créée et la jauge reste à 50.

---

### Invariant 2 : INV-R2 – Unicité des places dans une réservation

#### Scénario 1 – Happy path

- **Given** : Un événement « Concert Jazz » avec les places A1, A2, A3, A4 toutes disponibles.
- **When** : Un spectateur sélectionne les places A1 et A2 pour sa réservation.
- **Then** : La réservation est créée avec les deux places distinctes. Les places A1 et A2 sont marquées comme réservées et ne sont plus disponibles pour d'autres spectateurs.

#### Scénario 2 – Sad path

- **Given** : Un événement « Concert Jazz » où la place A1 est déjà réservée dans la réservation RES-2025-00140 (statut « Confirmée »).
- **When** : Un autre spectateur tente de créer une réservation incluant la place A1.
- **Then** : Le système refuse la réservation avec l'erreur « La place A1 n'est plus disponible ». La réservation existante RES-2025-00140 n'est pas impactée.

---

### Invariant 3 : INV-R3 – Confirmation conditionnée au paiement

#### Scénario 1 – Happy path

- **Given** : Une réservation RES-2025-00142 au statut « EnAttente » avec un montant total de 76 €.
- **When** : Le système reçoit la confirmation du paiement PAY-2025-00198 d'un montant de 76 € (statut « Accepté »).
- **Then** : La réservation passe au statut « Confirmée ». Les billets électroniques sont générés avec des QR codes uniques. Une notification de confirmation est déclenchée.

#### Scénario 2 – Sad path

- **Given** : Une réservation RES-2025-00142 au statut « EnAttente » avec un montant total de 76 €.
- **When** : Le système reçoit un refus de paiement PAY-2025-00198 (statut « Refusé » – fonds insuffisants).
- **Then** : La réservation passe au statut « Annulée ». Les places sont libérées et la jauge de l'événement est incrémentée. Le spectateur est notifié de l'échec du paiement.

---

### Invariant 4 : INV-R4 – Irréversibilité des statuts terminaux

#### Scénario 1 – Happy path

- **Given** : Une réservation RES-2025-00142 au statut « Confirmée ».
- **When** : Le spectateur demande l'annulation de sa réservation (dans le délai autorisé).
- **Then** : La réservation passe au statut « Annulée ». Un remboursement est initié. Les places sont libérées et la jauge est mise à jour.

#### Scénario 2 – Sad path

- **Given** : Une réservation RES-2025-00142 au statut « Annulée ».
- **When** : Le spectateur tente de réactiver ou modifier cette réservation.
- **Then** : Le système refuse l'opération avec l'erreur « Une réservation annulée ne peut pas être modifiée ». Le spectateur est invité à créer une nouvelle réservation.

---

### Invariant 5 : INV-E1 – Jauge non négative

#### Scénario 1 – Happy path

- **Given** : Un événement « Concert Jazz » avec une jauge disponible de 2 places.
- **When** : Un spectateur crée une réservation pour 2 places.
- **Then** : La réservation est créée avec succès. La jauge passe à 0 et le statut de vente de l'événement passe à « Complet ».

#### Scénario 2 – Sad path

- **Given** : Un événement « Concert Jazz » avec une jauge disponible de 1 place.
- **When** : Un spectateur tente de créer une réservation pour 3 places.
- **Then** : Le système refuse la réservation avec l'erreur « Nombre de places demandées supérieur à la disponibilité (1 place restante) ». La jauge reste inchangée.

---

### Invariant 6 : INV-E2 – Événement complet bloque les ventes

#### Scénario 1 – Happy path

- **Given** : Un événement « Concert Jazz » au statut « Complet » (jauge = 0). Un spectateur annule sa réservation de 2 places.
- **When** : La jauge est incrémentée à 2 et le statut repasse à « OuvertAuPublic ».
- **Then** : Un nouveau spectateur peut désormais réserver jusqu'à 2 places pour cet événement.

#### Scénario 2 – Sad path

- **Given** : Un événement « Concert Jazz » au statut « Complet » (jauge = 0).
- **When** : Un spectateur tente de créer une réservation pour 1 place.
- **Then** : Le système refuse avec l'erreur « Cet événement est complet, plus aucune place n'est disponible ». Le spectateur peut s'inscrire sur une liste d'attente.

---

### Invariant 7 : INV-E3 – Ventes dans la période autorisée

#### Scénario 1 – Happy path

- **Given** : Un événement « Concert Jazz » avec une période de vente du 1er février au 14 mars 2025. La date courante est le 10 février 2025.
- **When** : Un spectateur tente de réserver des places.
- **Then** : La réservation est acceptée car la date courante est dans la période de vente autorisée.

#### Scénario 2 – Sad path

- **Given** : Un événement « Concert Jazz » avec une ouverture des ventes prévue le 1er février 2025. La date courante est le 25 janvier 2025.
- **When** : Un spectateur tente de réserver des places.
- **Then** : Le système refuse avec l'erreur « Les ventes ne sont pas encore ouvertes pour cet événement. Ouverture prévue le 01/02/2025 ». Les places sont visibles mais non réservables.
