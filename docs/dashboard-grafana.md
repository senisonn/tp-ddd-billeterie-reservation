# Dashboard Grafana — Mockup

## 6.3 Vision du tableau de bord d'observabilité

Le dashboard Grafana agrège deux types de visualisation : un graphique **technique** et un
graphique **métier**. Il est alimenté par Prometheus qui scrape l'endpoint `/metrics` de
chaque service toutes les 15 secondes.

---

## Mockup du dashboard

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║  🎟  Billetterie & Réservation — Dashboard Opérationnel          [Last 1h ▼]   ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ┌──────────────────────────────────────┐  ┌──────────────────────────────────┐ ║
║  │  [TECHNIQUE] Temps de réponse HTTP   │  │  [TECHNIQUE] Taux d'erreurs HTTP │ ║
║  │  api-reservation — p50/p95/p99       │  │  api-reservation (4xx + 5xx)     │ ║
║  │                                      │  │                                  │ ║
║  │  ms                                  │  │  %                               │ ║
║  │  300 ┤                  ·p99         │  │  5 ┤                             │ ║
║  │  250 ┤            ·····/             │  │  4 ┤                             │ ║
║  │  200 ┤        ···/   ·p95            │  │  3 ┤    ·                        │ ║
║  │  150 ┤    ···/   ···/                │  │  2 ┤   ···        ·              │ ║
║  │  100 ┤···/   ···/ ·p50              │  │  1 ┤ ·····  ·   ···              │ ║
║  │   50 ┤   ···/                        │  │  0 ┼────────────────────── time  │ ║
║  │    0 ┼──────────────────── time      │  │    14:00     14:30     15:00     │ ║
║  │      14:00     14:30     15:00       │  └──────────────────────────────────┘ ║
║  └──────────────────────────────────────┘                                        ║
║                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                  ║
║  ┌──────────────────────────────────────┐  ┌──────────────────────────────────┐ ║
║  │  [METIER] Réservations créées/heure  │  │  [METIER] Jauge disponible       │ ║
║  │  ContexteRéservation                 │  │  Places restantes par événement  │ ║
║  │                                      │  │                                  ║
║  │  nb/h                                │  │  places                          │ ║
║  │  60 ┤           ██                   │  │  500 ┤ EVT-2025-00034 ━━━━━━━━━  │ ║
║  │  50 ┤       ██  ██  ██               │  │  400 ┤                           │ ║
║  │  40 ┤    ██  ██  ██  ██              │  │  300 ┤                           │ ║
║  │  30 ┤ ██  ██  ██  ██  ██            │  │  200 ┤ EVT-2025-00035 ━━━━━       │ ║
║  │  20 ┤ ██  ██  ██  ██  ██  ██       │  │  100 ┤              ▼ 21 places   │ ║
║  │  10 ┤ ██  ██  ██  ██  ██  ██  ██  │  │   0  ┤ EVT-2025-00036 ████ Complet│ ║
║  │   0 ┼──────────────────── time      │  │      EVT-034  EVT-035  EVT-036    │ ║
║  │    13h  14h  15h  16h  17h  18h  19h│  └──────────────────────────────────┘ ║
║  └──────────────────────────────────────┘                                        ║
║                                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  Stat panels (KPI en temps réel)                                                 ║
║                                                                                  ║
║  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ ║
║  │ Réservations     │ │ Confirmées       │ │ Taux succès     │ │ QR scannés    │ ║
║  │ créées (24h)     │ │ (24h)            │ │ paiement        │ │ aujourd'hui   │ ║
║  │                  │ │                  │ │                 │ │               │ ║
║  │   1 247          │ │   1 182          │ │   94.8 %        │ │    842        │ ║
║  │   ↑ +12% vs hier │ │   ↑ +10% vs hier │ │   ↓ -0.2%      │ │   ↑ +5%       │ ║
║  └─────────────────┘ └─────────────────┘ └─────────────────┘ └───────────────┘ ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

---

## Description des graphiques

### Graphique technique 1 — Temps de réponse HTTP (p50 / p95 / p99)

**Source de données :** `http_request_duration_seconds` (histogramme Prometheus)

**Requête PromQL :**
```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="api-reservation"}[5m]))
```

**Interprétation :**
- La ligne **p50** (médiane) représente l'expérience de l'utilisateur typique.
- La ligne **p95** signale que 95 % des requêtes sont sous ce seuil.
- La ligne **p99** détecte les pics de latence rares mais impactants.
- **Seuil d'alerte** : p99 > 500 ms → alerte Slack pour l'équipe SRE.

---

### Graphique technique 2 — Taux d'erreurs HTTP (4xx + 5xx)

**Source de données :** `http_errors_total` / `http_requests_total`

**Requête PromQL :**
```promql
rate(http_errors_total{job="api-reservation"}[5m]) /
rate(http_requests_total{job="api-reservation"}[5m]) * 100
```

**Interprétation :**
- Un taux > 1 % déclenche une alerte (erreurs fonctionnelles — INV-R1/R2).
- Un taux > 5 % déclenche une alerte critique (problème système).

---

### Graphique métier 1 — Réservations créées par heure (histogramme)

**Source de données :** `reservations_creees_total` (counter Prometheus)

**Requête PromQL :**
```promql
increase(reservations_creees_total{job="api-reservation"}[1h])
```

**Interprétation :**
- Mesure l'activité commerciale réelle (non le trafic technique).
- Pic attendu entre 14h et 19h (ouverture des ventes de nouveaux concerts).
- Une chute brutale à 0 signale une panne du ContexteRéservation.

---

### Graphique métier 2 — Jauge disponible par événement (bar gauge)

**Source de données :** `jauge_disponible` (gauge Prometheus, label `evenement_id`)

**Requête PromQL :**
```promql
jauge_disponible{job="api-reservation"}
```

**Interprétation :**
- Affiche en temps réel les places restantes pour chaque événement en cours de vente.
- Une valeur à 0 confirme le statut « Complet » (INV-E2 respecté).
- Permet à l'équipe marketing de détecter les événements en tension et d'anticiper
  la communication sur les listes d'attente.

---

## Alertes associées

| Alerte                    | Condition PromQL                                     | Sévérité | Action                          |
|---------------------------|------------------------------------------------------|----------|---------------------------------|
| `HighLatency`             | p99 > 500ms pendant 5 min                            | warning  | Notif Slack #ops                |
| `HighErrorRate`           | taux erreurs > 5% pendant 2 min                      | critical | PagerDuty + astreinte           |
| `NoReservationsCreated`   | `increase(reservations_creees_total[30m]) == 0`      | warning  | Vérification ContexteRéservation |
| `EventSoldOut`            | `jauge_disponible == 0`                              | info     | Notification équipe marketing   |
