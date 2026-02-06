# Scénario choisi

**Billetterie & réservation**

# Contexte métier

Le système de billetterie et réservation s'inscrit dans le secteur de l'événementiel et du spectacle vivant. Il s'agit d'une plateforme permettant à une organisation (salle de spectacle, festival, complexe culturel) de gérer la création d'événements, la mise en vente de billets et le processus complet de réservation pour ses clients. Le secteur est caractérisé par une forte saisonnalité, des pics de demande lors de l'ouverture des ventes, et des contraintes de capacité physique liées aux salles.

Les enjeux principaux sont la gestion en temps réel de la disponibilité des places, la fiabilité du processus de paiement, et la lutte contre la fraude (revente non autorisée, réservations multiples abusives). La plateforme doit supporter des montées en charge importantes lors de l'ouverture des ventes d'événements populaires, tout en garantissant l'équité d'accès pour les clients.

L'organisation exploite plusieurs salles de tailles différentes, propose des événements variés (concerts, théâtre, conférences) et applique des politiques tarifaires complexes (tarifs réduits, abonnements, préventes). Le système doit également gérer les annulations, les remboursements et la communication avec les clients tout au long du cycle de vie d'une réservation.

# Rôles utilisateurs

| Rôle | Type | Description |
|------|------|-------------|
| Responsable Programmation | Direction | Supervise la programmation des événements, définit les politiques tarifaires et les quotas de places. Valide les ouvertures de vente et analyse les performances commerciales via des tableaux de bord. |
| Agent de Billetterie | Opérationnel | Gère les ventes au guichet, traite les demandes spéciales des clients (changements de places, groupes), contrôle les billets à l'entrée des événements et gère les situations exceptionnelles (sur-réservation, incidents). |
| Spectateur | Client | Recherche des événements, consulte les disponibilités, effectue des réservations en ligne, procède au paiement et reçoit ses billets électroniques. Peut annuler ou modifier ses réservations selon les conditions en vigueur. |

# Problématiques métier

1. **Gestion de la concurrence d'accès** : Lors de l'ouverture des ventes d'événements populaires, des centaines de clients tentent simultanément de réserver les mêmes places. Le système doit garantir qu'une place ne soit jamais vendue deux fois tout en offrant une expérience fluide.

2. **Politique tarifaire complexe** : Les tarifs varient selon le type de place (fosse, balcon, catégorie), le profil du client (étudiant, senior, abonné), la date d'achat (prévente, plein tarif, dernière minute) et les promotions en cours. Le calcul du prix doit être fiable et traçable.

3. **Gestion des annulations et remboursements** : Les conditions d'annulation diffèrent selon le type d'événement, le délai avant la date et le canal d'achat. Les remboursements doivent respecter les obligations légales tout en préservant la trésorerie de l'organisation.

4. **Lutte contre la fraude et la revente** : Le système doit empêcher les réservations multiples abusives (bots, scripts) et contrôler la revente non autorisée de billets, tout en permettant le transfert légitime entre particuliers.

5. **Communication et notifications** : Les spectateurs doivent être informés en temps réel des confirmations de réservation, des changements (report, annulation d'événement) et des rappels. Le système doit gérer plusieurs canaux (email, SMS, notification push).

# Scénario fil rouge

Un spectateur, Marie, souhaite assister au concert de Jazz du 15 mars à la Grande Salle. Elle se connecte à la plateforme et recherche l'événement par date et genre musical. Le système lui affiche les événements correspondants avec les disponibilités restantes.

Marie sélectionne le concert et consulte le plan de salle interactif. Elle choisit deux places en catégorie « Orchestre » côte à côte. Le système vérifie la disponibilité en temps réel et réserve temporairement les places pendant 10 minutes (panier temporaire).

Marie renseigne ses informations et applique son code de réduction étudiant. Le système recalcule le montant total en appliquant la réduction de 20 % sur le tarif de base. Elle procède au paiement par carte bancaire.

Le système de paiement confirme la transaction. La réservation passe au statut « Confirmée ». Deux billets électroniques avec QR codes uniques sont générés et envoyés par email à Marie. Une notification de confirmation lui est également envoyée par SMS.

Le jour du concert, Marie présente son QR code à l'entrée. L'agent de billetterie scanne le code, le système valide l'authenticité et le non-usage du billet, puis autorise l'accès. Le billet est marqué comme « Utilisé » dans le système.

Après le concert, le Responsable Programmation consulte le tableau de bord : taux de remplissage de 95 %, 12 annulations, 3 remboursements traités. Ces données alimenteront les décisions de programmation future.
