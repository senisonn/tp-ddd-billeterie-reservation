# Pipeline CI — Tests d'intégration

## Objectif

Exécuter automatiquement les tests d'intégration à chaque push ou pull request
sur la branche `master`, et garantir qu'aucune régression ne passe inaperçue.

---

## Configuration GitHub Actions

Fichier : `.github/workflows/ci.yml`

```yaml
name: CI – Tests d'intégration

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  integration-tests:
    name: Tests d'intégration (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Installation de Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Installation des dépendances
        run: pip install pytest

      - name: Exécution des tests d'intégration
        run: pytest tests/integration/test_scenario.py -v
```

---

## Couverture des tests

| Classe de test                    | Scénarios | Invariant(s) couverts          |
|-----------------------------------|-----------|-------------------------------|
| `TestINV_R1_LimitePlaces`         | 3         | INV-R1 (limite 1–10 places)   |
| `TestINV_R2_UnicitePlaces`        | 3         | INV-R2 (unicité des places)   |
| `TestINV_R3_ConfirmationPaiement` | 3         | INV-R3 (paiement requis)      |
| `TestINV_R4_StatutTerminal`       | 3         | INV-R4 (statuts terminaux)    |
| `TestINV_E1_JaugeNonNegative`     | 2         | INV-E1 (jauge ≥ 0)            |
| `TestINV_E2_EvenementComplet`     | 3         | INV-E2 (complet bloque vente) |
| `TestINV_E3_PeriodeVente`         | 3         | INV-E3 (période autorisée)    |
| `TestScenarioFilRouge`            | 2         | Fil rouge inter-agrégats      |
| **Total**                         | **22**    | 7 invariants + scénario complet |

---

## Capture pipeline vert (exécution locale)

```
============================= test session starts ==============================
platform linux -- Python 3.13.12, pytest-8.3.5, pluggy-1.5.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/soheil/Bureau/DDD/tp-ddd-billeterie-reservation
plugins: Faker-37.1.0, cov-6.0.0
collecting ... collected 22 items

tests/integration/test_scenario.py::TestINV_R1_LimitePlaces::test_happy_3_places_crees_en_attente PASSED [  4%]
tests/integration/test_scenario.py::TestINV_R1_LimitePlaces::test_sad_12_places_refusees PASSED [  9%]
tests/integration/test_scenario.py::TestINV_R1_LimitePlaces::test_sad_0_places_refusees PASSED [ 13%]
tests/integration/test_scenario.py::TestINV_R2_UnicitePlaces::test_happy_places_distinctes PASSED [ 18%]
tests/integration/test_scenario.py::TestINV_R2_UnicitePlaces::test_sad_place_deja_reservee_autre_spectateur PASSED [ 22%]
tests/integration/test_scenario.py::TestINV_R2_UnicitePlaces::test_sad_place_dupliquee_meme_reservation PASSED [ 27%]
tests/integration/test_scenario.py::TestINV_R3_ConfirmationPaiement::test_happy_paiement_exact_confirme PASSED [ 31%]
tests/integration/test_scenario.py::TestINV_R3_ConfirmationPaiement::test_sad_paiement_refuse_annule_reservation PASSED [ 36%]
tests/integration/test_scenario.py::TestINV_R3_ConfirmationPaiement::test_sad_montant_incorrect PASSED [ 40%]
tests/integration/test_scenario.py::TestINV_R4_StatutTerminal::test_happy_confirmee_puis_annulee_libere_jauge PASSED [ 45%]
tests/integration/test_scenario.py::TestINV_R4_StatutTerminal::test_sad_modifier_reservation_annulee PASSED [ 50%]
tests/integration/test_scenario.py::TestINV_R4_StatutTerminal::test_sad_reannuler_reservation_annulee PASSED [ 54%]
tests/integration/test_scenario.py::TestINV_E1_JaugeNonNegative::test_happy_2_places_jauge_tombe_a_zero_devient_complet PASSED [ 59%]
tests/integration/test_scenario.py::TestINV_E1_JaugeNonNegative::test_sad_3_places_pour_1_dispo PASSED [ 63%]
tests/integration/test_scenario.py::TestINV_E2_EvenementComplet::test_happy_annulation_rouvre_ventes PASSED [ 68%]
tests/integration/test_scenario.py::TestINV_E2_EvenementComplet::test_sad_reservation_sur_evenement_complet PASSED [ 72%]
tests/integration/test_scenario.py::TestINV_E2_EvenementComplet::test_happy_apres_annulation_nouveau_spectateur_peut_reserver PASSED [ 77%]
tests/integration/test_scenario.py::TestINV_E3_PeriodeVente::test_happy_reservation_dans_periode PASSED [ 81%]
tests/integration/test_scenario.py::TestINV_E3_PeriodeVente::test_sad_avant_ouverture_des_ventes PASSED [ 86%]
tests/integration/test_scenario.py::TestINV_E3_PeriodeVente::test_sad_apres_fin_des_ventes PASSED [ 90%]
tests/integration/test_scenario.py::TestScenarioFilRouge::test_parcours_nominal_complet PASSED [ 95%]
tests/integration/test_scenario.py::TestScenarioFilRouge::test_double_reservation_concurrente_bloquee PASSED [100%]

============================== 22 passed in 0.15s ==============================
```

**22 tests passés, 0 échec.**