# Entités et Objets Valeur – Vue conceptuelle

## Entités

### Réservation

| Attribut | Type métier | Description |
|----------|------------|-------------|
| réservationId | Identifiant de réservation | Identifiant unique généré au format RES-AAAA-NNNNN, attribué dès la création de la réservation. |
| spectateur | Référence vers Spectateur | Le spectateur qui a effectué la réservation, identifié par son compte client. |
| événement | Référence vers Événement | L'événement pour lequel la réservation est faite. |
| places | Collection de Places | La liste des places réservées pour cet événement (au moins 1, maximum 10). |
| statut | Statut de réservation | L'état courant de la réservation : EnAttente, Confirmée, Annulée, Remboursée. |
| montantTotal | Montant monétaire | Le prix total de la réservation, calculé par le contexte Tarification. |
| dateRéservation | Date et heure | La date et l'heure de création de la réservation. |

**Invariants :**
- Une réservation doit contenir entre 1 et 10 places.
- Une réservation ne peut être confirmée que si le paiement a été accepté.
- Une réservation au statut « Annulée » ou « Remboursée » ne peut plus être modifiée.

### Événement

| Attribut | Type métier | Description |
|----------|------------|-------------|
| événementId | Identifiant d'événement | Identifiant unique au format EVT-AAAA-NNNNN. |
| nom | Nom d'événement | Le titre de l'événement tel qu'affiché au public. |
| dateÉvénement | Date et heure | La date et l'heure de début de l'événement. |
| salle | Référence vers Salle | La salle dans laquelle se déroule l'événement. |
| jaugeDisponible | Nombre de places | Le nombre de places encore disponibles à la vente. |
| statutVente | Statut de vente | L'état des ventes : Fermé, Prévente, OuvertAuPublic, Complet, Terminé. |
| dateLimiteAnnulation | Date | La date au-delà de laquelle les annulations ne sont plus possibles. |

**Invariants :**
- La jauge disponible ne peut jamais être négative.
- Un événement au statut « Complet » ne peut accepter aucune nouvelle réservation.

## Objet Valeur

### MontantTarifé

**Propriétés :**
- `tarifBase` : le prix de base de la catégorie de place (ex : 45 €)
- `réduction` : le montant de la réduction appliquée (ex : 9 €)
- `fraisDeService` : les frais de gestion de la plateforme (ex : 2 €)
- `total` : le montant net à payer (ex : 38 €)
- `devise` : la devise du montant (EUR)

**Explication de l'immuabilité :** Le MontantTarifé est un objet valeur car il représente le résultat d'un calcul à un instant donné. Une fois calculé, il ne doit pas être modifié : si les conditions changent (nouvelle réduction, changement de catégorie), un nouveau MontantTarifé est recalculé. L'immuabilité garantit la traçabilité des prix appliqués et empêche toute altération du montant après la confirmation de la réservation.
