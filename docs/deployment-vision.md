# Vision du déploiement — Billetterie & Réservation

## 6.1 Conteneurisation par Bounded Context

### Principe : un service par Bounded Context

Chaque Bounded Context est déployé dans son propre conteneur Docker. Cette séparation
garantit l'autonomie opérationnelle de chaque contexte : mise à jour indépendante,
scalabilité ciblée et isolation des pannes.

| Service (conteneur)       | Bounded Context         | Rôle                                          |
|---------------------------|-------------------------|-----------------------------------------------|
| `api-reservation`         | ContexteRéservation     | Cœur métier : réservations, billets, paiement |
| `api-programmation`       | ContexteProgrammation   | Gestion des événements, salles, jauges        |
| `api-notification`        | ContexteNotification    | Envoi d'emails et SMS (appel SendGrid)        |
| `api-controle-acces`      | ContexteContrôleAccès   | Validation des QR codes à l'entrée            |
| `api-tarification`        | ContexteTarification    | Calcul des tarifs et réductions               |
| `postgres`                | Infrastructure          | Persistance relationnelle (réservations, events) |
| `rabbitmq`                | Infrastructure          | Broker de messages (événements asynchrones)   |
| `prometheus`              | Infrastructure          | Collecte des métriques `/metrics`             |
| `grafana`                 | Infrastructure          | Visualisation des métriques                   |

---

### Services prioritairement conteneurisés

Les services critiques (déployés en priorité) sont :

1. **`api-reservation`** — cœur du domaine, toutes les routes REST du ContexteRéservation
2. **`postgres`** — persistance des réservations et des événements
3. **`rabbitmq`** — découplage asynchrone entre contextes

Les services secondaires (déployables indépendamment) :

4. **`api-notification`** — stateless, peut être scalé horizontalement
5. **`api-controle-acces`** — déployé sur site (tablette de l'agent de billetterie)

---

### Configuration des conteneurs

Chaque service est configuré via **variables d'environnement** (pas de secrets dans l'image) :

| Variable                    | Service             | Valeur exemple                          |
|-----------------------------|---------------------|-----------------------------------------|
| `DATABASE_URL`              | api-reservation     | `postgresql://user:pass@postgres:5432/billetterie` |
| `RABBITMQ_URL`              | tous les api-*      | `amqp://guest:guest@rabbitmq:5672/`     |
| `SENDGRID_API_KEY`          | api-notification    | `SG.xxx` (secret, injecté par CI/CD)    |
| `STRIPE_WEBHOOK_SECRET`     | api-reservation     | `whsec_xxx` (secret)                    |
| `LOG_LEVEL`                 | tous les api-*      | `INFO`                                  |
| `PORT`                      | tous les api-*      | `8080`                                  |

---

### Dockerfile annoté — service `api-reservation`

```dockerfile
# ── Étape 1 : image de base légère ──────────────────────────────────────────
FROM python:3.12-slim AS base
# python:3.12-slim = Python officiel sans outils de compilation inutiles
# réduit la surface d'attaque et le poids de l'image

WORKDIR /app
# tous les fichiers applicatifs seront sous /app

# ── Étape 2 : installation des dépendances ───────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# --no-cache-dir évite de stocker le cache pip dans l'image (image plus légère)

# ── Étape 3 : copie du code applicatif ───────────────────────────────────────
COPY domain/      ./domain/
COPY application/ ./application/
COPY adapters/    ./adapters/
# On ne copie PAS les tests ni les fichiers de dev (voir .dockerignore)

# ── Étape 4 : utilisateur non-root (sécurité) ────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser
USER appuser
# Ne jamais exécuter l'application en tant que root dans un conteneur

# ── Étape 5 : exposition du port et lancement ────────────────────────────────
EXPOSE 8080
# Port interne du conteneur (mappé vers l'hôte dans docker-compose)

CMD ["python", "-m", "adapters.rest_api"]
# Point d'entrée : démarre le serveur HTTP de l'adaptateur REST
```

**`.dockerignore` associé :**

```
tests/
docs/
*.md
*.pdf
.git/
__pycache__/
*.pyc
.env
```

---

### Stratégie de build et de tag

```
# Build de l'image avec tag de version et de commit
docker build \
  -t billetterie/api-reservation:1.2.0 \
  -t billetterie/api-reservation:latest \
  --label "git-commit=$(git rev-parse --short HEAD)" \
  -f services/reservation/Dockerfile \
  .
```

Les tags suivent la convention `MAJEUR.MINEUR.PATCH` (SemVer). Chaque merge sur `main`
déclenche un build automatique via la CI (voir `docs/ci-pipeline.md`).
