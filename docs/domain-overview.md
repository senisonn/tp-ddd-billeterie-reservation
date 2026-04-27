# Vue d'ensemble du domaine

## Liste des fonctionnalités

- **Gestion de la programmation** : Création, modification et publication d'événements avec définition des dates, salles et configurations. *Acteur : Responsable Programmation.*
- **Gestion des réservations** : Sélection de places, création de paniers temporaires, confirmation et suivi des réservations. *Acteurs : Spectateur, Agent de Billetterie.*
- **Tarification et réductions** : Calcul dynamique des prix selon la catégorie de place, le profil du spectateur et les promotions actives. *Acteur : Responsable Programmation (définition des règles), Système (calcul automatique).*
- **Paiement et remboursement** : Traitement des transactions financières, gestion des remboursements suite aux annulations. *Acteur : Spectateur.*
- **Émission et contrôle des billets** : Génération de billets électroniques avec QR codes et validation à l'entrée des événements. *Acteur : Agent de Billetterie.*
- **Gestion des comptes clients** : Création de comptes spectateurs, gestion des abonnements, historique des réservations. *Acteur : Spectateur.*
- **Notifications** : Envoi de confirmations, rappels, alertes de changements par email, SMS et push. *Acteur : Système (automatique).*
- **Reporting et pilotage** : Tableaux de bord de fréquentation, taux de remplissage, chiffre d'affaires par événement. *Acteur : Responsable Programmation.*

## Classification des sous-domaines

| Fonctionnalité | Type | Justification |
|---------------|------|---------------|
| Gestion des réservations | Core | C'est le coeur de la proposition de valeur de la plateforme. La capacité à gérer les réservations en temps réel avec verrouillage de places et gestion de la concurrence est ce qui différencie le système. |
| Tarification et réductions | Core | La politique tarifaire est un avantage concurrentiel direct. Les règles de calcul complexes (catégories, réductions, promotions) sont spécifiques au métier et constituent un levier commercial majeur. |
| Gestion de la programmation | Supporting | Nécessaire au fonctionnement du Core car les événements alimentent les réservations. Cependant, la programmation elle-même n'est pas différenciante — toute plateforme de billetterie en a besoin. |
| Émission et contrôle des billets | Supporting | Indispensable pour matérialiser la réservation et sécuriser l'accès. Toutefois, les mécanismes de QR code et de scan sont relativement standards dans l'industrie. |
| Gestion des comptes clients | Supporting | Permet l'identification des spectateurs et l'application des réductions, mais la gestion de comptes utilisateurs est un besoin commun à toute application. |
| Paiement et remboursement | Generic | Le traitement des paiements est entièrement délégable à un prestataire externe (Stripe, PayPal). Les mécanismes de paiement sont standardisés et commoditisés. |
| Notifications | Generic | L'envoi d'emails, SMS et push est un service technique standard. Des solutions SaaS (SendGrid, Twilio) couvrent ce besoin sans développement spécifique. |
| Reporting et pilotage | Generic | Les outils de reporting sont standards et peuvent être couverts par des solutions existantes (Grafana, Metabase). Les métriques sont spécifiques, mais l'outillage est générique. |

## Schéma des sous-domaines

```
┌─────────────────────────────────────────────────────────────┐
│                        CORE DOMAIN                          │
│  ┌──────────────────────┐  ┌──────────────────────────┐     │
│  │ Gestion des          │  │ Tarification &           │     │
│  │ réservations         │  │ réductions               │     │
│  └──────────────────────┘  └──────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    SUPPORTING DOMAINS                       │
│  ┌──────────────┐ ┌──────────────────┐ ┌──────────────────┐ │
│  │ Programmation│ │ Billets & Accès  │ │ Comptes clients  │ │
│  └──────────────┘ └──────────────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     GENERIC DOMAINS                         │
│  ┌────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │ Paiement   │  │ Notifications  │  │ Reporting         │  │
│  └────────────┘  └────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```
