# Modèle de domaine

> Chaque section ci-dessous correspond à un Bounded Context. Les entités et objets valeur sont rattachés au contexte qui en est propriétaire.

---

## ContexteProgrammation *(Supporting)*

### Entités

| Entité | Description métier | Identifiant métier |
|--------|-------------------|-------------------|
| Événement | Un spectacle ou une représentation créé et publié par le Responsable Programmation. Il est rattaché à une salle, possède une date et un statut de publication (Brouillon → Publié → Annulé). C'est la donnée de référence consommée par les autres contextes. | ÉvénementId (format : EVT-AAAA-NNNNN) |
| Salle | L'espace physique d'accueil d'un événement. Elle possède une capacité totale, une liste de zones et un plan de salle associé. Sa configuration est fixée avant la programmation des événements. | SalleId (format : SAL-AAAA-NNNNN) |
| Saison | Regroupe l'ensemble des événements programmés sur une période annuelle. Elle permet de planifier la publication groupée et de gérer les périodes de prévente pour les abonnés. | SaisonId (format : SAI-AAAA-NNNNN) |

### Objets Valeur

| Objet Valeur | Description métier | Propriétés principales |
|-------------|-------------------|----------------------|
| Place | Une place physique dans une salle, identifiée par sa position et sa catégorie tarifaire. Immuable : la place ne change pas de zone ni de rangée une fois la salle configurée. | zone, rangée, numéro, catégorie |
| PériodeDeVente | Définit la fenêtre temporelle pendant laquelle les billets sont en vente pour un événement. Elle comprend les dates de début et de fin de la prévente (abonnés) et de la vente générale. Immuable car fixée lors de la planification de l'événement. | débutPrévente, finPrévente, débutVenteGénérale, finVente |
| ConfigurationZone | Décrit une zone de la salle : nom, nombre de rangées, places par rangée et catégorie tarifaire associée. | nomZone, nbRangées, placesParRangée, catégorie |

### Diagramme UML (ContexteProgrammation)

```
┌─────────────────────────┐       ┌─────────────────────────┐
│      «Entité»           │       │      «Entité»           │
│       Saison            │       │        Salle            │
├─────────────────────────┤       ├─────────────────────────┤
│ saisonId : SaisonId     │       │ salleId : SalleId       │
│ libellé : Texte         │       │ nom : Texte             │
│ année : Année           │       │ capacitéTotale : Nombre │
└────────┬────────────────┘       │ zones : List<Config.>   │
         │ regroupe *             └────────┬────────────────┘
         │                                 │ accueille *
         ▼                                 │
┌─────────────────────────────────────────────────────┐
│                    «Entité»                         │
│                   Événement                         │
├─────────────────────────────────────────────────────┤
│ événementId : ÉvénementId                           │
│ titre : Texte                                       │
│ dateÉvénement : Date                                │
│ statut : StatutPublication                          │
│ jaugeDisponible : Nombre                            │
│ périodeDeVente : PériodeDeVente  ◄── «OV»           │
│ places : List<Place>             ◄── «OV»           │
└─────────────────────────────────────────────────────┘
```

---

## ContexteRéservation *(Core)*

### Entités

| Entité | Description métier | Identifiant métier |
|--------|-------------------|-------------------|
| Réservation | Représente l'acte de réservation d'un spectateur pour un événement donné. Elle regroupe un ou plusieurs billets, possède un statut de cycle de vie (EnAttente → Confirmée → Annulée/Remboursée) et est associée à un montant tarifé. La réservation est l'unité transactionnelle principale du système. | RéservationId (format : RES-AAAA-NNNNN) |
| Billet | Titre d'accès individuel émis à la confirmation d'une réservation. Il matérialise le droit d'entrée pour une place précise lors d'un événement, possède un QR code unique et un statut propre (Valide → Utilisé / Annulé). C'est l'entité que le spectateur présente à l'entrée. | BilletId (format : BIL-AAAA-NNNNN) |
| Spectateur | La personne physique qui crée un compte, effectue des réservations et assiste aux événements. Le spectateur possède un profil (type : étudiant, senior, standard) et un éventuel abonnement qui influencent la tarification. Son historique de réservations est conservé pour le suivi et la fidélisation. | SpectateurId (format : CLI-AAAA-NNNNN) |

### Objets Valeur

| Objet Valeur | Description métier | Propriétés principales |
|-------------|-------------------|----------------------|
| MontantTarifé | Résultat immuable du calcul du prix d'une réservation. Il encapsule le tarif de base, les réductions appliquées, les frais de service et le montant total. Une fois créé, il ne change pas et sert de preuve du prix convenu. | tarifBase, réduction, fraisDeService, total, devise |
| PlaceAssignée | Décrit la position physique d'une place occupée par un billet : zone, rangée, numéro et catégorie tarifaire. C'est une description immuable de localisation, composant du `Billet`. | zone, rangée, numéro, catégorie |

### Diagramme UML (ContexteRéservation)

```
┌─────────────────────────┐         ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│      «Entité»           │           «Réf. externe»
│     Spectateur          │         │  Événement            │
├─────────────────────────┤           (ContexteProgrammation)
│ spectateurId : Id       │         └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
│ nom : Texte             │                    │ 1
│ email : Email           │                    │ concerne *
│ profil : ProfilClient   │                    │
│ abonnement : Abonnement?│                    ▼
└────────┬────────────────┘   ┌─────────────────────────────────────┐
         │ 1                  │             «Entité»                │
         │ effectue *         │           Réservation               │
         └───────────────────►├─────────────────────────────────────┤
                              │ réservationId : RéservationId       │
                              │ statut : StatutRéservation          │
                              │ montantTotal : MontantTarifé ◄─«OV»│
                              │ dateRéservation : Date              │
                              │ billets : List<Billet>              │
                              └──────────────┬──────────────────────┘
                                             │ composition 1..*
                                             ▼
                              ┌──────────────────────────────────┐
                              │          «Entité»                │
                              │           Billet                 │
                              ├──────────────────────────────────┤
                              │ billetId : BilletId              │
                              │ qrCode : QRCode                  │
                              │ statut : StatutBillet            │
                              │ place : PlaceAssignée  ◄── «OV»  │
                              └──────────────────────────────────┘
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
```
