# Scénario complet inter-contextes

## Scénario : Réservation → Paiement → Confirmation → Contrôle d'accès

### Contextes impliqués

- **ContexteProgrammation** — fournit les données de l'événement et des places
- **ContexteRéservation** — orchestre la réservation et génère les billets
- **ContexteTarification** — calcule le prix final
- **ContextePaiement** — traite la transaction financière
- **ContexteNotification** — envoie les communications au spectateur
- **ContexteContrôleAccès** — valide les billets à l'entrée

---

### Description narrative détaillée

Marie Dupont, spectatrice abonnée (CLI-2025-00089), souhaite réserver deux places pour le Concert Jazz du 15 mars 2025 à la Grande Salle. Elle ouvre l'application web et sélectionne les places A12 et A13 en zone Orchestre.

**Étape 1 — Vérification de la disponibilité**
Le **ContexteRéservation** interroge le **ContexteProgrammation** via une API REST synchrone pour vérifier que l'événement EVT-2025-00034 existe, que la période de vente est ouverte (INV-E3) et que les places A12 et A13 sont disponibles dans la jauge (INV-E1). Le ContexteProgrammation confirme : 23 places restantes, ventes ouvertes jusqu'au 14 mars 2025.

**Étape 2 — Calcul du tarif**
Le ContexteRéservation appelle le **ContexteTarification** en transmettant les deux places et l'identifiant de Marie. Le ContexteTarification consulte le ContexteCompteClient pour vérifier le profil abonnée de Marie, applique le tarif Orchestre (45 € × 2 = 90 €), la réduction abonné de 20 % (-18 €) et les frais de service (+4 €). Il retourne un `MontantTarifé` immuable : total = 76 €.

**Étape 3 — Création de la réservation**
Le ContexteRéservation crée l'agrégat Réservation (RES-2025-00142) au statut « EnAttente » avec les deux places choisies et le MontantTarifé de 76 €. Les invariants sont vérifiés : 2 places dans la limite 1–10 (INV-R1), pas de doublons (INV-R2). La jauge de l'événement est décrémentée de 2 (21 places restantes, INV-E1). L'événement de domaine `RéservationCréée` est publié sur le broker.

**Étape 4 — Paiement**
Marie est redirigée vers le formulaire de paiement du **ContextePaiement**. Elle saisit ses coordonnées bancaires. Le ContextePaiement transmet la demande au prestataire externe (Stripe) via une couche anticorruption (ACL). Stripe traite la transaction et envoie un webhook de confirmation. L'ACL traduit ce webhook en événement métier `PaiementAccepté` avec le montant exact de 76 €.

**Étape 5 — Confirmation et génération des billets**
Le ContexteRéservation reçoit `PaiementAccepté` et vérifie que le montant correspond exactement au montant de la réservation (INV-R3). La réservation passe au statut « Confirmée ». Deux billets sont générés : BIL-2025-00283 (place A12, QR-X7K9M) et BIL-2025-00284 (place A13, QR-P3L2N), chacun avec un QR code unique. L'événement `RéservationConfirmée` est publié sur le broker.

**Étape 6 — Notification au spectateur**
Le **ContexteNotification** consomme `RéservationConfirmée` et envoie un email à Marie avec les deux billets électroniques en pièce jointe (PDF avec QR codes). L'email est envoyé via SendGrid en moins de 30 secondes. Marie reçoit la confirmation sur son téléphone.

**Étape 7 — Activation des QR codes**
Le **ContexteContrôleAccès** consomme `RéservationConfirmée` et enregistre les deux QR codes comme valides dans son registre. Les billets sont prêts pour le contrôle d'accès le jour de l'événement.

**Étape 8 — Contrôle à l'entrée (le 15 mars 2025)**
Marie arrive au concert. L'agent de billetterie scanne le QR code QR-X7K9M du premier billet. Le ContexteContrôleAccès vérifie l'authenticité du QR code, son appartenance à l'événement du jour, et son non-usage préalable. Le billet passe au statut « Utilisé » (irréversible). L'agent scanne ensuite QR-P3L2N pour la deuxième place. Accès autorisé pour les deux places.

---

### Liste des événements déclenchés (dans l'ordre)

| Ordre | Événement | Publié par | Consommé par |
|-------|-----------|-----------|--------------|
| 1 | `RéservationCréée` | ContexteRéservation | ContexteNotification (email de panier) |
| 2 | `PaiementAccepté` | ContextePaiement (ACL Stripe) | ContexteRéservation |
| 3 | `RéservationConfirmée` | ContexteRéservation | ContexteNotification, ContexteContrôleAccès |
| 4 | `BilletScanné` | ContexteContrôleAccès | — (log interne, détection fraude) |

---

### Rappel des invariants concernés

| Invariant | Moment de vérification | Résultat dans ce scénario |
|-----------|----------------------|--------------------------|
| **INV-R1** — Limite 1–10 places | Création de la réservation (étape 3) | ✅ 2 places — dans les limites |
| **INV-R2** — Unicité des places | Création de la réservation (étape 3) | ✅ A12 ≠ A13, places disponibles |
| **INV-R3** — Paiement = montant | Confirmation (étape 5) | ✅ 76 € payés = 76 € attendus |
| **INV-R4** — Statuts terminaux | Non concerné dans ce scénario nominal | — |
| **INV-E1** — Jauge ≥ 0 | Décrémentation à l'étape 3 | ✅ 23 → 21 places, jamais négatif |
| **INV-E2** — Complet bloque ventes | Vérification à l'étape 1 | ✅ Événement non complet |
| **INV-E3** — Période de vente | Vérification à l'étape 1 | ✅ Date dans la période autorisée |
