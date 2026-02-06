# Repositories métier

## RéservationRepository

Le `RéservationRepository` gère la persistance de l'agrégat Réservation et de ses composants internes (PlaceAssignée, Billet, MontantTarifé).

| Opération métier | Description | Contraintes / règles métier |
|-----------------|-------------|---------------------------|
| CréerRéservation | Enregistre une nouvelle réservation avec ses places assignées et son montant tarifé. L'opération persiste l'ensemble de l'agrégat en une seule transaction atomique. Le statut initial est « EnAttente ». | L'identifiant RéservationId doit être unique dans tout le système. Les places référencées doivent être disponibles au moment de l'enregistrement (vérifié par un verrou optimiste). La réservation doit respecter l'invariant INV-R1 (1 à 10 places). |
| RechercherParId | Récupère une réservation complète (avec ses places, billets et montant) à partir de son identifiant unique RéservationId. Retourne l'agrégat complet ou une indication d'absence. | L'agrégat retourné doit être complet et cohérent, incluant toutes les entités et objets valeur internes. Aucune réservation partielle ne doit être retournée. |
| RechercherParSpectateur | Liste toutes les réservations d'un spectateur donné, triées par date de réservation décroissante. Permet l'affichage de l'historique des réservations dans le compte client. | Seules les réservations du spectateur identifié sont retournées. Les réservations dans tous les statuts sont incluses (EnAttente, Confirmée, Annulée, Remboursée). |
| MettreÀJourStatut | Met à jour le statut d'une réservation existante (ex : EnAttente → Confirmée, Confirmée → Annulée). L'opération vérifie la validité de la transition de statut avant de persister. | Les transitions de statut doivent respecter le cycle de vie : EnAttente → Confirmée ou Annulée ; Confirmée → Annulée ; Annulée → Remboursée. L'invariant INV-R4 (irréversibilité des statuts terminaux) doit être vérifié. |
| SupprimerPanierExpiré | Supprime les réservations au statut « EnAttente » dont le panier a dépassé le délai d'expiration (10 minutes). Libère automatiquement les places associées. | L'opération doit être exécutée périodiquement. Seules les réservations « EnAttente » expirées sont concernées. Les places libérées doivent être réinjectées dans la jauge de l'événement. |

## ÉvénementRepository

Le `ÉvénementRepository` gère la persistance de l'agrégat Événement et de ses composants internes (PériodeDeVente, Catégorie, ConfigurationSalle).

| Opération métier | Description | Contraintes / règles métier |
|-----------------|-------------|---------------------------|
| CréerÉvénement | Enregistre un nouvel événement avec sa configuration de salle, ses catégories tarifaires et sa période de vente. L'événement est créé avec une jauge initiale égale à la capacité de la salle. | L'identifiant ÉvénementId doit être unique. La date de l'événement doit être dans le futur. La jauge initiale ne peut pas dépasser la capacité physique de la salle assignée. La période de vente doit commencer avant la date de l'événement. |
| RechercherParId | Récupère un événement complet à partir de son identifiant ÉvénementId. Retourne l'agrégat avec toutes ses données (jauge actuelle, catégories, période de vente). | L'agrégat retourné reflète l'état courant de la jauge. Les données doivent être cohérentes avec les réservations en cours. |
| RechercherDisponibles | Liste les événements dont la vente est ouverte et qui disposent de places disponibles. Permet la recherche par date, genre, salle avec pagination. | Seuls les événements avec un statutVente « Prévente » ou « OuvertAuPublic » et une jauge > 0 sont retournés. Les événements passés ou au statut « Terminé » sont exclus. |
| MettreÀJourJauge | Met à jour la jauge disponible d'un événement suite à une réservation ou une annulation. Décrémente ou incrémente le compteur et met à jour le statut de vente si nécessaire. | La jauge ne peut jamais être négative (INV-E1). Si la jauge atteint 0, le statut passe automatiquement à « Complet » (INV-E2). Si la jauge repasse au-dessus de 0 après une annulation, le statut repasse à « OuvertAuPublic ». Utilisation d'un verrou optimiste pour gérer la concurrence. |
