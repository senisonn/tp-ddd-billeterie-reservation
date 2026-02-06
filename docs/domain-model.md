# Modèle de domaine

## Entités

| Entité | Description métier | Identifiant métier |
|--------|-------------------|-------------------|
| Réservation | Représente l'acte de réservation d'un spectateur pour un événement donné. Elle regroupe une ou plusieurs places, possède un statut de cycle de vie (EnAttente → Confirmée → Annulée/Remboursée) et est associée à un montant tarifé. La réservation est l'unité transactionnelle principale du système. | RéservationId (format : RES-AAAA-NNNNN) |
| Événement | Un spectacle ou une représentation programmé dans une salle à une date précise. L'événement détermine la capacité d'accueil, les catégories de places disponibles et le calendrier des ventes. Il constitue le point d'entrée de la recherche pour les spectateurs et la référence pour la jauge de disponibilité. | ÉvénementId (format : EVT-AAAA-NNNNN) |
| Spectateur | La personne physique qui crée un compte, effectue des réservations et assiste aux événements. Le spectateur possède un profil (type : étudiant, senior, standard) et un éventuel abonnement qui influencent la tarification. Son historique de réservations est conservé pour le suivi et la fidélisation. | SpectateurId (format : CLI-AAAA-NNNNN) |

## Objets Valeur

| Objet Valeur | Description métier | Propriétés principales |
|-------------|-------------------|----------------------|
| MontantTarifé | Résultat immuable du calcul du prix d'une réservation. Il encapsule le tarif de base, les réductions appliquées, les frais de service et le montant total. Une fois créé, il ne change pas et sert de preuve du prix convenu. | tarifBase, réduction, fraisDeService, total, devise |
| PlaceAssignée | Représente l'attribution d'une place spécifique dans le cadre d'une réservation. Elle combine les coordonnées physiques de la place (zone, rangée, numéro) avec la catégorie tarifaire. Deux PlaceAssignée sont égales si elles désignent le même emplacement. | zone, rangée, numéro, catégorie |
| PériodeDeVente | Définit la fenêtre temporelle pendant laquelle les billets sont en vente pour un événement. Elle comprend les dates de début et de fin de la prévente (abonnés) et de la vente générale. Immuable car fixée lors de la planification de l'événement. | débutPrévente, finPrévente, débutVenteGénérale, finVente |

## Diagramme UML (conceptuel)

```
┌─────────────────────────┐         ┌─────────────────────────┐
│      «Entité»           │         │      «Entité»           │
│     Spectateur          │         │     Événement           │
├─────────────────────────┤         ├─────────────────────────┤
│ spectateurId : Id       │         │ événementId : Id        │
│ nom : Texte             │         │ nom : Texte             │
│ email : Email           │         │ dateÉvénement : Date    │
│ profil : ProfilClient   │         │ jaugeDisponible : Nb    │
│ abonnement : Abonnement?│         │ statutVente : StatutV.  │
└────────┬────────────────┘         │ périodeDeVente : PDV     │
         │                          └────────┬────────────────┘
         │ 1                                  │ 1
         │                                    │
         │ effectue *                          │ concerne *
         │                                    │
         ▼                                    ▼
┌─────────────────────────────────────────────────┐
│                   «Entité»                      │
│                 Réservation                      │
├─────────────────────────────────────────────────┤
│ réservationId : RéservationId                   │
│ statut : StatutRéservation                      │
│ montantTotal : MontantTarifé  ◄── «OV»         │
│ dateRéservation : Date                          │
│ places : List<PlaceAssignée>  ◄── «OV»         │
└─────────────────────────────────────────────────┘
         │
         │ composition
         ▼
┌──────────────────────┐    ┌──────────────────────┐
│   «Objet Valeur»     │    │   «Objet Valeur»     │
│   PlaceAssignée      │    │   MontantTarifé      │
├──────────────────────┤    ├──────────────────────┤
│ zone : Texte         │    │ tarifBase : Montant  │
│ rangée : Texte       │    │ réduction : Montant  │
│ numéro : Nombre      │    │ fraisService : Mont. │
│ catégorie : Catégorie│    │ total : Montant      │
└──────────────────────┘    │ devise : Devise      │
                            └──────────────────────┘

┌──────────────────────┐
│   «Objet Valeur»     │
│   PériodeDeVente     │
├──────────────────────┤
│ débutPrévente : Date │
│ finPrévente : Date   │
│ débutVenteGén : Date │
│ finVente : Date      │
└──────────────────────┘
```
