# Entités et Objets Valeur – Vue conceptuelle

## Entités

### Réservation

| Attribut | Type métier | Description |
|----------|------------|-------------|
| réservationId | Identifiant de réservation | Identifiant unique généré au format RES-AAAA-NNNNN, attribué dès la création de la réservation. |
| spectateur | Référence vers Spectateur | Le spectateur qui a effectué la réservation, identifié par son compte client. |
| événement | Référence vers Événement | L'événement pour lequel la réservation est faite. |
| billets | Collection de Billets | Les billets émis pour cette réservation, un par place (au moins 1, maximum 10). Générés à la confirmation. |
| statut | Statut de réservation | L'état courant de la réservation : EnAttente, Confirmée, Annulée, Remboursée. |
| montantTotal | Montant monétaire | Le prix total de la réservation, calculé par le contexte Tarification. |
| dateRéservation | Date et heure | La date et l'heure de création de la réservation. |

**Invariants :**
- Une réservation doit contenir entre 1 et 10 billets.
- Une réservation ne peut être confirmée que si le paiement a été accepté.
- Une réservation au statut « Annulée » ou « Remboursée » ne peut plus être modifiée.

### Billet *(ContexteRéservation)*

| Attribut | Type métier | Description |
|----------|------------|-------------|
| billetId | Identifiant de billet | Identifiant unique au format BIL-AAAA-NNNNN, attribué à la confirmation de la réservation. |
| qrCode | Code QR | Code bidimensionnel unique généré à la confirmation, servant de titre d'accès à l'entrée. |
| statut | Statut de billet | L'état courant du billet : Valide, Utilisé, Annulé. |
| place | PlaceAssignée (OV) | La position physique de la place associée à ce billet (zone, rangée, numéro, catégorie). |

**Invariants :**
- Un billet Valide ne peut être utilisé qu'une seule fois (passage Valide → Utilisé irréversible).
- Un billet Annulé ne peut pas être présenté à l'entrée.
- Le QR code est unique dans tout le système.

### Événement *(ContexteProgrammation)*

| Attribut | Type métier | Description |
|----------|------------|-------------|
| événementId | Identifiant d'événement | Identifiant unique au format EVT-AAAA-NNNNN. |
| titre | Nom d'événement | Le titre de l'événement tel qu'affiché au public. |
| dateÉvénement | Date et heure | La date et l'heure de début de l'événement. |
| salle | Référence vers Salle | La salle dans laquelle se déroule l'événement. |
| statut | Statut de publication | L'état de l'événement : Brouillon, Publié, Annulé. |
| jaugeDisponible | Nombre de places | Le nombre de places encore disponibles à la vente. |
| statutVente | Statut de vente | L'état des ventes : Fermé, Prévente, OuvertAuPublic, Complet, Terminé. |
| périodeDeVente | PériodeDeVente (OV) | La fenêtre temporelle d'ouverture des ventes. |
| places | Collection de Place (OV) | L'ensemble des places physiques disponibles dans la salle pour cet événement. |

**Invariants :**
- La jauge disponible ne peut jamais être négative.
- Un événement au statut « Complet » ne peut accepter aucune nouvelle réservation.

### Salle *(ContexteProgrammation)*

| Attribut | Type métier | Description |
|----------|------------|-------------|
| salleId | Identifiant de salle | Identifiant unique au format SAL-AAAA-NNNNN. |
| nom | Nom de salle | Le nom de l'espace d'accueil. |
| capacitéTotale | Nombre | La capacité maximale de la salle, somme de toutes les places. |
| zones | Collection de ConfigurationZone (OV) | La description de chaque zone (nombre de rangées, places par rangée, catégorie). |

## Objets Valeur

### MontantTarifé *(ContexteRéservation)*

**Propriétés :**
- `tarifBase` : le prix de base de la catégorie de place (ex : 45 €)
- `réduction` : le montant de la réduction appliquée (ex : 9 €)
- `fraisDeService` : les frais de gestion de la plateforme (ex : 2 €)
- `total` : le montant net à payer (ex : 38 €)
- `devise` : la devise du montant (EUR)

**Explication de l'immuabilité :** Le MontantTarifé est un objet valeur car il représente le résultat d'un calcul à un instant donné. Une fois calculé, il ne doit pas être modifié : si les conditions changent (nouvelle réduction, changement de catégorie), un nouveau MontantTarifé est recalculé. L'immuabilité garantit la traçabilité des prix appliqués et empêche toute altération du montant après la confirmation de la réservation.

### PlaceAssignée *(ContexteRéservation, composant de Billet)*

**Propriétés :**
- `zone` : le nom de la zone dans la salle (ex : Orchestre, Balcon)
- `rangée` : l'identifiant de la rangée (ex : A, B, C)
- `numéro` : le numéro du siège dans la rangée (ex : 12)
- `catégorie` : la catégorie tarifaire de la place (ex : Premium, Standard)

**Explication de l'immuabilité :** PlaceAssignée décrit où est assis le spectateur. Une fois un billet émis, la position ne change pas. C'est une description de localisation, pas une entité traçable — elle n'a pas de cycle de vie propre.

### Place *(ContexteProgrammation, composant d'Événement)*

**Propriétés :**
- `zone` : la zone de la salle
- `rangée` : la rangée dans la zone
- `numéro` : le numéro du siège
- `catégorie` : la catégorie tarifaire

**Rôle :** Décrit un siège physique tel que configuré dans la salle. Consommée par le ContexteRéservation pour créer les `PlaceAssignée` lors de la confirmation.

### PériodeDeVente *(ContexteProgrammation, composant d'Événement)*

**Propriétés :**
- `débutPrévente` : date d'ouverture pour les abonnés
- `finPrévente` : date de fin de la prévente
- `débutVenteGénérale` : date d'ouverture au grand public
- `finVente` : date de clôture des ventes

### ConfigurationZone *(ContexteProgrammation, composant de Salle)*

**Propriétés :**
- `nomZone` : nom de la zone (ex : Orchestre)
- `nbRangées` : nombre de rangées dans la zone
- `placesParRangée` : nombre de places par rangée
- `catégorie` : catégorie tarifaire de la zone
