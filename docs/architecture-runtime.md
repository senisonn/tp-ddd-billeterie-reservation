# Architecture d'exécution (Runtime) — Billetterie & Réservation

## 6.2 Docker Compose — Vision des services

### Schéma des services et de leurs liens

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          docker-compose                                  │
│                                                                         │
│  ┌──────────────────┐        ┌──────────────────┐                       │
│  │  api-reservation  │◄──────►│    api-tarif      │                      │
│  │  :8080            │  REST  │    :8081          │                      │
│  │  (ContexteRéserv.)│        │  (ContexteTarif.) │                      │
│  └────────┬─────────┘        └──────────────────┘                       │
│           │                                                              │
│           │ SQL                      publish/subscribe                   │
│           ▼                                   ▼                          │
│  ┌──────────────────┐        ┌──────────────────────────────────┐       │
│  │    postgres       │        │           rabbitmq               │       │
│  │    :5432          │        │           :5672 (AMQP)           │       │
│  │  DB billetterie   │        │           :15672 (Management UI) │       │
│  └──────────────────┘        └──────┬─────────────┬────────────┘       │
│                                      │             │                     │
│                              subscribe│             │subscribe            │
│                                      ▼             ▼                     │
│                        ┌─────────────────┐  ┌───────────────────┐       │
│                        │ api-notification │  │ api-controle-acces│       │
│                        │ :8082            │  │ :8083             │       │
│                        │ (ContexteNotif.) │  │ (ContexteCtrlAcc.)│       │
│                        └─────────────────┘  └───────────────────┘       │
│                                                                         │
│  ┌──────────────────┐        ┌──────────────────┐                       │
│  │   prometheus      │scrape  │     grafana       │                      │
│  │   :9090           │◄───────│     :3000         │                      │
│  │  (métriques)      │  /metrics│  (dashboards)   │                      │
│  └──────────────────┘        └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### docker-compose.yml conceptuel

```yaml
version: "3.9"

services:

  # ── Cœur métier ─────────────────────────────────────────────────────────
  api-reservation:
    build: ./services/reservation
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL:        postgresql://billetterie:secret@postgres:5432/billetterie
      RABBITMQ_URL:        amqp://guest:guest@rabbitmq:5672/
      TARIFICATION_URL:    http://api-tarification:8081
      LOG_LEVEL:           INFO
    depends_on:
      - postgres
      - rabbitmq
      - api-tarification
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/metrics"]
      interval: 30s
      timeout: 5s
      retries: 3

  api-tarification:
    build: ./services/tarification
    ports:
      - "8081:8081"
    environment:
      LOG_LEVEL: INFO
    networks:
      - backend

  api-notification:
    build: ./services/notification
    environment:
      RABBITMQ_URL:     amqp://guest:guest@rabbitmq:5672/
      SENDGRID_API_KEY: ${SENDGRID_API_KEY}   # injecté depuis .env (non versionné)
      LOG_LEVEL:        INFO
    depends_on:
      - rabbitmq
    networks:
      - backend

  api-controle-acces:
    build: ./services/controle-acces
    ports:
      - "8083:8083"
    environment:
      RABBITMQ_URL:  amqp://guest:guest@rabbitmq:5672/
      DATABASE_URL:  postgresql://billetterie:secret@postgres:5432/billetterie
      LOG_LEVEL:     INFO
    depends_on:
      - postgres
      - rabbitmq
    networks:
      - backend

  # ── Infrastructure ───────────────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB:       billetterie
      POSTGRES_USER:     billetterie
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    ports:
      - "15672:15672"    # UI de management (dev uniquement)
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    networks:
      - backend

  # ── Observabilité ────────────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./infra/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    networks:
      - backend

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - backend

volumes:
  postgres_data:
  grafana_data:

networks:
  backend:
    driver: bridge
```

---

### Description des liens entre services

| Lien                                          | Type       | Protocole | Raison                                                         |
|-----------------------------------------------|------------|-----------|----------------------------------------------------------------|
| `api-reservation` → `postgres`                | Synchrone  | SQL/TCP   | Persistance des réservations, billets et événements            |
| `api-reservation` → `api-tarification`        | Synchrone  | HTTP REST | Calcul du tarif avant création de la réservation (Customer/Supplier) |
| `api-reservation` → `rabbitmq`                | Asynchrone | AMQP      | Publication de `RéservationCréée`, `RéservationConfirmée`, `RéservationAnnulée` |
| `api-notification` → `rabbitmq`               | Asynchrone | AMQP      | Consommation des événements pour envoi d'emails (Conformist)   |
| `api-controle-acces` → `rabbitmq`             | Asynchrone | AMQP      | Consommation de `RéservationConfirmée` pour activer les QR codes |
| `api-controle-acces` → `postgres`             | Synchrone  | SQL/TCP   | Registre local des QR codes valides                            |
| `prometheus` → `api-reservation` (`/metrics`) | Polling    | HTTP      | Collecte des métriques toutes les 15 secondes                  |
| `grafana` → `prometheus`                      | Synchrone  | HTTP      | Lecture des métriques pour affichage des dashboards            |

---

### Fichier `infra/prometheus.yml` (configuration du scraping)

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "api-reservation"
    static_configs:
      - targets: ["api-reservation:8080"]
    metrics_path: /metrics

  - job_name: "api-controle-acces"
    static_configs:
      - targets: ["api-controle-acces:8083"]
    metrics_path: /metrics
```

---

### Notes de déploiement

- **Secrets** : les valeurs sensibles (`SENDGRID_API_KEY`, `POSTGRES_PASSWORD`, `STRIPE_WEBHOOK_SECRET`)
  ne sont jamais versionnées. Elles sont injectées via un fichier `.env` local (dev) ou via
  les secrets du CI/CD en production (GitHub Actions secrets / Vault).

- **Ordre de démarrage** : `depends_on` garantit que `postgres` et `rabbitmq` démarrent
  avant les services applicatifs. Les `healthcheck` assurent que les services ne reçoivent
  du trafic qu'une fois prêts.

- **Scalabilité** : `api-notification` est stateless et peut être scalé horizontalement
  (`docker compose up --scale api-notification=3`) sans modification de configuration.
