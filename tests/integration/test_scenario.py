"""
Tests d'intégration – Billetterie & Réservation
Scénarios GWT couvrant les 7 invariants du domaine (INV-R1 à INV-E3)
+ scénarios bout-en-bout inter-contextes (Partie 5.4).

Le domaine et l'infrastructure événementielle sont implémentés en-ligne
afin que ce fichier soit autonome et exécutable sans dépendances externes
(pytest uniquement).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, auto
from typing import List, Optional


# ---------------------------------------------------------------------------
# Exceptions métier
# ---------------------------------------------------------------------------

class ErreurDomaine(Exception):
    """Base des exceptions métier."""


class LimitePlacesDepassee(ErreurDomaine):
    pass


class AucunePlaceSelectionnee(ErreurDomaine):
    pass


class PlaceDupliquee(ErreurDomaine):
    pass


class PlaceDejaReservee(ErreurDomaine):
    pass


class PaiementRequis(ErreurDomaine):
    pass


class MontantIncorrect(ErreurDomaine):
    pass


class StatutTerminalError(ErreurDomaine):
    pass


class JaugeInsuffisante(ErreurDomaine):
    pass


class EvenementComplet(ErreurDomaine):
    pass


class VentesNonOuvertes(ErreurDomaine):
    pass


class VentesTerminees(ErreurDomaine):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StatutReservation(Enum):
    EN_ATTENTE = auto()
    CONFIRMEE  = auto()
    ANNULEE    = auto()
    REMBOURSEE = auto()


class StatutVente(Enum):
    FERME          = auto()
    PREVENTE       = auto()
    OUVERT_PUBLIC  = auto()
    COMPLET        = auto()
    TERMINE        = auto()


# ---------------------------------------------------------------------------
# Objets Valeur
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlaceAssignee:
    zone: str
    rangee: str
    numero: int
    categorie: str = "Orchestre"

    def __str__(self) -> str:
        return f"{self.zone}{self.rangee}{self.numero}"


@dataclass(frozen=True)
class MontantTarife:
    tarif_base: float
    reduction: float
    frais_service: float
    devise: str = "EUR"

    @property
    def total(self) -> float:
        return round(self.tarif_base - self.reduction + self.frais_service, 2)


@dataclass(frozen=True)
class PeriodeDeVente:
    debut_vente: date
    fin_vente: date

    def est_dans_periode(self, aujourd_hui: date) -> bool:
        return self.debut_vente <= aujourd_hui <= self.fin_vente

    def est_avant_ouverture(self, aujourd_hui: date) -> bool:
        return aujourd_hui < self.debut_vente


# ---------------------------------------------------------------------------
# Agrégat Événement
# ---------------------------------------------------------------------------

@dataclass
class Evenement:
    evenement_id: str
    nom: str
    date_evenement: date
    capacite: int
    jauge_disponible: int
    statut_vente: StatutVente
    periode_de_vente: PeriodeDeVente

    def reserver_places(self, nb_places: int, aujourd_hui: date) -> None:
        # INV-E3 : période de vente
        if self.periode_de_vente.est_avant_ouverture(aujourd_hui):
            raise VentesNonOuvertes(
                f"Les ventes ne sont pas encore ouvertes. "
                f"Ouverture prévue le {self.periode_de_vente.debut_vente.strftime('%d/%m/%Y')}."
            )
        if not self.periode_de_vente.est_dans_periode(aujourd_hui):
            raise VentesTerminees("Les ventes sont terminées pour cet événement.")

        # INV-E2 : événement complet
        if self.statut_vente == StatutVente.COMPLET:
            raise EvenementComplet(
                "Cet événement est complet, plus aucune place n'est disponible."
            )

        # INV-E1 : jauge non négative
        if nb_places > self.jauge_disponible:
            raise JaugeInsuffisante(
                f"Nombre de places demandées supérieur à la disponibilité "
                f"({self.jauge_disponible} place(s) restante(s))."
            )

        self.jauge_disponible -= nb_places
        if self.jauge_disponible == 0:
            self.statut_vente = StatutVente.COMPLET

    def liberer_places(self, nb_places: int) -> None:
        self.jauge_disponible = min(self.jauge_disponible + nb_places, self.capacite)
        if self.statut_vente == StatutVente.COMPLET and self.jauge_disponible > 0:
            self.statut_vente = StatutVente.OUVERT_PUBLIC


# ---------------------------------------------------------------------------
# Agrégat Réservation
# ---------------------------------------------------------------------------

@dataclass
class Billet:
    billet_id: str
    place: PlaceAssignee
    qr_code: str


@dataclass
class Reservation:
    reservation_id: str
    evenement_id: str
    spectateur_id: str
    statut: StatutReservation
    places: List[PlaceAssignee]
    montant: MontantTarife
    billets: List[Billet] = field(default_factory=list)

    # ---- invariants à la création (appelés depuis le service) ----

    @staticmethod
    def valider_places(places: List[PlaceAssignee]) -> None:
        # INV-R1
        if len(places) < 1:
            raise AucunePlaceSelectionnee("Le nombre de places doit être au moins 1.")
        if len(places) > 10:
            raise LimitePlacesDepassee(
                "Le nombre de places doit être compris entre 1 et 10."
            )
        # INV-R2 – doublons internes
        ids = [(p.zone, p.rangee, p.numero) for p in places]
        if len(ids) != len(set(ids)):
            raise PlaceDupliquee("Deux places identiques dans la même réservation.")

    # ---- transitions d'état ----

    def confirmer(self, montant_paye: float) -> None:
        self._verifier_non_terminal()
        # INV-R3
        if montant_paye <= 0:
            raise PaiementRequis("Un paiement accepté est requis pour confirmer.")
        if round(montant_paye, 2) != self.montant.total:
            raise MontantIncorrect(
                f"Montant attendu : {self.montant.total} €, "
                f"montant reçu : {montant_paye} €."
            )
        self.statut = StatutReservation.CONFIRMEE
        self._generer_billets()

    def annuler(self) -> None:
        self._verifier_non_terminal()
        self.statut = StatutReservation.ANNULEE

    def rembourser(self) -> None:
        if self.statut != StatutReservation.ANNULEE:
            raise ErreurDomaine("Seule une réservation annulée peut être remboursée.")
        self.statut = StatutReservation.REMBOURSEE

    def _verifier_non_terminal(self) -> None:
        # INV-R4
        if self.statut in (StatutReservation.ANNULEE, StatutReservation.REMBOURSEE):
            raise StatutTerminalError(
                "Une réservation annulée ou remboursée ne peut pas être modifiée."
            )

    def _generer_billets(self) -> None:
        self.billets = [
            Billet(
                billet_id=f"BIL-{uuid.uuid4().hex[:8].upper()}",
                place=p,
                qr_code=f"QR-{self.reservation_id}-{p}",
            )
            for p in self.places
        ]


# ---------------------------------------------------------------------------
# Repositories en mémoire
# ---------------------------------------------------------------------------

class EvenementRepository:
    def __init__(self) -> None:
        self._store: dict[str, Evenement] = {}
        self._places_actives: dict[str, List[PlaceAssignee]] = {}

    def sauvegarder(self, evt: Evenement) -> None:
        self._store[evt.evenement_id] = evt

    def trouver_par_id(self, evenement_id: str) -> Evenement:
        if evenement_id not in self._store:
            raise KeyError(f"Événement introuvable : {evenement_id}")
        return self._store[evenement_id]

    def places_reservees(self, evenement_id: str) -> List[PlaceAssignee]:
        """Retourne toutes les places actives (non annulées/remboursées) pour un événement."""
        return self._places_actives.get(evenement_id, [])

    def enregistrer_places_actives(
        self, evenement_id: str, places: List[PlaceAssignee]
    ) -> None:
        existing = self._places_actives.get(evenement_id, [])
        self._places_actives[evenement_id] = existing + places

    def liberer_places_actives(
        self, evenement_id: str, places: List[PlaceAssignee]
    ) -> None:
        existing = self._places_actives.get(evenement_id, [])
        self._places_actives[evenement_id] = [p for p in existing if p not in places]


class ReservationRepository:
    def __init__(self) -> None:
        self._store: dict[str, Reservation] = {}

    def sauvegarder(self, res: Reservation) -> None:
        self._store[res.reservation_id] = res

    def trouver_par_id(self, reservation_id: str) -> Reservation:
        if reservation_id not in self._store:
            raise KeyError(f"Réservation introuvable : {reservation_id}")
        return self._store[reservation_id]


# ---------------------------------------------------------------------------
# Service applicatif
# ---------------------------------------------------------------------------

class ServiceReservation:
    def __init__(
        self,
        repo_reservations: ReservationRepository,
        repo_evenements: EvenementRepository,
    ) -> None:
        self._reservations = repo_reservations
        self._evenements = repo_evenements

    def creer_reservation(
        self,
        spectateur_id: str,
        evenement_id: str,
        places: List[PlaceAssignee],
        montant: MontantTarife,
        aujourd_hui: Optional[date] = None,
    ) -> Reservation:
        if aujourd_hui is None:
            aujourd_hui = date.today()

        evt = self._evenements.trouver_par_id(evenement_id)

        # INV-R1 + INV-R2 (interne)
        Reservation.valider_places(places)

        # INV-R2 – conflit avec d'autres réservations actives
        places_prises = self._evenements.places_reservees(evenement_id)
        for p in places:
            if p in places_prises:
                raise PlaceDejaReservee(f"La place {p} n'est plus disponible.")

        # INV-E1, E2, E3
        evt.reserver_places(len(places), aujourd_hui)

        reservation = Reservation(
            reservation_id=f"RES-{uuid.uuid4().hex[:8].upper()}",
            evenement_id=evenement_id,
            spectateur_id=spectateur_id,
            statut=StatutReservation.EN_ATTENTE,
            places=places,
            montant=montant,
        )
        self._reservations.sauvegarder(reservation)
        self._evenements.sauvegarder(evt)
        self._evenements.enregistrer_places_actives(evenement_id, places)
        return reservation

    def confirmer_paiement(self, reservation_id: str, montant_paye: float) -> Reservation:
        res = self._reservations.trouver_par_id(reservation_id)
        res.confirmer(montant_paye)
        self._reservations.sauvegarder(res)
        return res

    def annuler_reservation(self, reservation_id: str) -> Reservation:
        res = self._reservations.trouver_par_id(reservation_id)
        res.annuler()
        evt = self._evenements.trouver_par_id(res.evenement_id)
        evt.liberer_places(len(res.places))
        self._evenements.sauvegarder(evt)
        self._evenements.liberer_places_actives(res.evenement_id, res.places)
        self._reservations.sauvegarder(res)
        return res


# ---------------------------------------------------------------------------
# Fixtures partagées
# ---------------------------------------------------------------------------

AUJOURD_HUI    = date(2025, 2, 10)
OUVERTURE      = date(2025, 2, 1)
FIN_VENTE      = date(2025, 3, 14)
AVANT_OUVERTURE = date(2025, 1, 25)

MONTANT_STD = MontantTarife(tarif_base=90.0, reduction=18.0, frais_service=4.0)
# total = 90 - 18 + 4 = 76.0 €


def _creer_evenement(
    capacite: int = 50,
    jauge: Optional[int] = None,
    statut: StatutVente = StatutVente.OUVERT_PUBLIC,
    debut: Optional[date] = None,
    fin: Optional[date] = None,
) -> Evenement:
    return Evenement(
        evenement_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
        nom="Concert Jazz",
        date_evenement=date(2025, 3, 15),
        capacite=capacite,
        jauge_disponible=capacite if jauge is None else jauge,
        statut_vente=statut,
        periode_de_vente=PeriodeDeVente(
            debut_vente=debut or OUVERTURE,
            fin_vente=fin or FIN_VENTE,
        ),
    )


def _creer_service(
    evt: Optional[Evenement] = None,
) -> tuple[ServiceReservation, EvenementRepository, ReservationRepository]:
    repo_evt = EvenementRepository()
    repo_res = ReservationRepository()
    if evt:
        repo_evt.sauvegarder(evt)
    return ServiceReservation(repo_res, repo_evt), repo_evt, repo_res


# ===========================================================================
# INV-R1 : Limite de places par réservation
# ===========================================================================

class TestINV_R1_LimitePlaces:

    def test_happy_3_places_crees_en_attente(self):
        """Given concert 50 places / When 3 places / Then EnAttente, jauge 47."""
        evt = _creer_evenement(capacite=50)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", i) for i in range(1, 4)]

        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        assert res.statut == StatutReservation.EN_ATTENTE
        assert len(res.places) == 3
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 47

    def test_sad_12_places_refusees(self):
        """Given concert 50 places / When 12 places / Then LimitePlacesDepassee, jauge 50."""
        evt = _creer_evenement(capacite=50)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", i) for i in range(1, 13)]

        try:
            svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
            assert False, "Devait lever LimitePlacesDepassee"
        except LimitePlacesDepassee as e:
            assert "1 et 10" in str(e)

        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 50

    def test_sad_0_places_refusees(self):
        """Given concert / When 0 places / Then AucunePlaceSelectionnee."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)

        try:
            svc.creer_reservation("CLI-001", evt.evenement_id, [], MONTANT_STD, AUJOURD_HUI)
            assert False, "Devait lever AucunePlaceSelectionnee"
        except AucunePlaceSelectionnee:
            pass


# ===========================================================================
# INV-R2 : Unicité des places
# ===========================================================================

class TestINV_R2_UnicitePlaces:

    def test_happy_places_distinctes(self):
        """Given A1 A2 A3 A4 libres / When A1+A2 / Then réservées, plus dispo."""
        evt = _creer_evenement()
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]

        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        assert len(res.places) == 2
        prises = repo_evt.places_reservees(evt.evenement_id)
        assert PlaceAssignee("A", "1", 1) in prises
        assert PlaceAssignee("A", "1", 2) in prises

    def test_sad_place_deja_reservee_autre_spectateur(self):
        """Given A1 confirmée / When autre spectateur réserve A1 / Then PlaceDejaReservee."""
        evt = _creer_evenement(capacite=50)
        svc, repo_evt, _ = _creer_service(evt)
        place_a1 = PlaceAssignee("A", "1", 1)

        svc.creer_reservation("CLI-001", evt.evenement_id, [place_a1], MONTANT_STD, AUJOURD_HUI)

        try:
            svc.creer_reservation(
                "CLI-002", evt.evenement_id, [place_a1], MONTANT_STD, AUJOURD_HUI
            )
            assert False, "Devait lever PlaceDejaReservee"
        except PlaceDejaReservee as e:
            assert "A1" in str(e)

    def test_sad_place_dupliquee_meme_reservation(self):
        """Given A1 présente deux fois / Then PlaceDupliquee."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        place_a1 = PlaceAssignee("A", "1", 1)

        try:
            svc.creer_reservation(
                "CLI-001", evt.evenement_id, [place_a1, place_a1], MONTANT_STD, AUJOURD_HUI
            )
            assert False, "Devait lever PlaceDupliquee"
        except PlaceDupliquee:
            pass


# ===========================================================================
# INV-R3 : Confirmation conditionnée au paiement
# ===========================================================================

class TestINV_R3_ConfirmationPaiement:

    def test_happy_paiement_exact_confirme(self):
        """Given EnAttente 76€ / When paiement 76€ / Then Confirmée + billets générés."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        res = svc.confirmer_paiement(res.reservation_id, 76.0)

        assert res.statut == StatutReservation.CONFIRMEE
        assert len(res.billets) == 2
        for b in res.billets:
            assert b.qr_code.startswith("QR-")

    def test_sad_paiement_refuse_annule_reservation(self):
        """Given EnAttente 76€ / When paiement refusé (0€) / Then PaiementRequis."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        try:
            svc.confirmer_paiement(res.reservation_id, 0.0)
            assert False, "Devait lever PaiementRequis"
        except PaiementRequis:
            pass

    def test_sad_montant_incorrect(self):
        """Given EnAttente 76€ / When paiement 50€ / Then MontantIncorrect."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        try:
            svc.confirmer_paiement(res.reservation_id, 50.0)
            assert False, "Devait lever MontantIncorrect"
        except MontantIncorrect:
            pass


# ===========================================================================
# INV-R4 : Irréversibilité des statuts terminaux
# ===========================================================================

class TestINV_R4_StatutTerminal:

    def test_happy_confirmee_puis_annulee_libere_jauge(self):
        """Given Confirmée / When annulation / Then Annulée, jauge restaurée."""
        evt = _creer_evenement(capacite=10)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        svc.confirmer_paiement(res.reservation_id, 76.0)

        res = svc.annuler_reservation(res.reservation_id)

        assert res.statut == StatutReservation.ANNULEE
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 10

    def test_sad_modifier_reservation_annulee(self):
        """Given Annulée / When confirmation / Then StatutTerminalError."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        svc.annuler_reservation(res.reservation_id)

        try:
            svc.confirmer_paiement(res.reservation_id, 76.0)
            assert False, "Devait lever StatutTerminalError"
        except StatutTerminalError as e:
            assert "annulée" in str(e)

    def test_sad_reannuler_reservation_annulee(self):
        """Given Annulée / When annulation à nouveau / Then StatutTerminalError."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        svc.annuler_reservation(res.reservation_id)

        try:
            svc.annuler_reservation(res.reservation_id)
            assert False, "Devait lever StatutTerminalError"
        except StatutTerminalError:
            pass


# ===========================================================================
# INV-E1 : Jauge non négative
# ===========================================================================

class TestINV_E1_JaugeNonNegative:

    def test_happy_2_places_jauge_tombe_a_zero_devient_complet(self):
        """Given jauge 2 / When 2 places / Then jauge=0, statut=COMPLET."""
        evt = _creer_evenement(capacite=2, jauge=2)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]

        svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        evt_maj = repo_evt.trouver_par_id(evt.evenement_id)
        assert evt_maj.jauge_disponible == 0
        assert evt_maj.statut_vente == StatutVente.COMPLET

    def test_sad_3_places_pour_1_dispo(self):
        """Given jauge 1 / When 3 places / Then JaugeInsuffisante."""
        evt = _creer_evenement(capacite=10, jauge=1)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", i) for i in range(1, 4)]

        try:
            svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
            assert False, "Devait lever JaugeInsuffisante"
        except JaugeInsuffisante as e:
            assert "1" in str(e)

        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 1


# ===========================================================================
# INV-E2 : Événement complet bloque les ventes
# ===========================================================================

class TestINV_E2_EvenementComplet:

    def test_happy_annulation_rouvre_ventes(self):
        """Given COMPLET / When annulation 2 places / Then jauge=2, OUVERT_PUBLIC."""
        evt = _creer_evenement(capacite=2, jauge=2)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        assert repo_evt.trouver_par_id(evt.evenement_id).statut_vente == StatutVente.COMPLET

        svc.annuler_reservation(res.reservation_id)

        evt_maj = repo_evt.trouver_par_id(evt.evenement_id)
        assert evt_maj.jauge_disponible == 2
        assert evt_maj.statut_vente == StatutVente.OUVERT_PUBLIC

    def test_sad_reservation_sur_evenement_complet(self):
        """Given COMPLET / When nouvelle réservation / Then EvenementComplet."""
        evt = _creer_evenement(capacite=1, jauge=0, statut=StatutVente.COMPLET)
        svc, _, _ = _creer_service(evt)

        try:
            svc.creer_reservation(
                "CLI-001",
                evt.evenement_id,
                [PlaceAssignee("A", "1", 1)],
                MONTANT_STD,
                AUJOURD_HUI,
            )
            assert False, "Devait lever EvenementComplet"
        except EvenementComplet as e:
            assert "complet" in str(e)

    def test_happy_apres_annulation_nouveau_spectateur_peut_reserver(self):
        """Given COMPLET → annulation → nouveau spectateur réserve avec succès."""
        evt = _creer_evenement(capacite=2, jauge=2)
        svc, repo_evt, _ = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]
        res = svc.creer_reservation("CLI-001", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        svc.annuler_reservation(res.reservation_id)

        res2 = svc.creer_reservation(
            "CLI-002",
            evt.evenement_id,
            [PlaceAssignee("B", "1", 1)],
            MONTANT_STD,
            AUJOURD_HUI,
        )

        assert res2.statut == StatutReservation.EN_ATTENTE
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 1


# ===========================================================================
# INV-E3 : Ventes dans la période autorisée
# ===========================================================================

class TestINV_E3_PeriodeVente:

    def test_happy_reservation_dans_periode(self):
        """Given période 01/02–14/03, date=10/02 / When réservation / Then acceptée."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)

        res = svc.creer_reservation(
            "CLI-001",
            evt.evenement_id,
            [PlaceAssignee("A", "1", 1)],
            MONTANT_STD,
            AUJOURD_HUI,   # 10/02/2025 ∈ [01/02, 14/03]
        )

        assert res.statut == StatutReservation.EN_ATTENTE

    def test_sad_avant_ouverture_des_ventes(self):
        """Given ouverture 01/02, date=25/01 / When réservation / Then VentesNonOuvertes."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)

        try:
            svc.creer_reservation(
                "CLI-001",
                evt.evenement_id,
                [PlaceAssignee("A", "1", 1)],
                MONTANT_STD,
                AVANT_OUVERTURE,  # 25/01/2025 < 01/02/2025
            )
            assert False, "Devait lever VentesNonOuvertes"
        except VentesNonOuvertes as e:
            assert "01/02/2025" in str(e)

    def test_sad_apres_fin_des_ventes(self):
        """Given fin ventes 14/03, date=20/03 / When réservation / Then VentesTerminees."""
        evt = _creer_evenement()
        svc, _, _ = _creer_service(evt)

        try:
            svc.creer_reservation(
                "CLI-001",
                evt.evenement_id,
                [PlaceAssignee("A", "1", 1)],
                MONTANT_STD,
                date(2025, 3, 20),   # 20/03/2025 > 14/03/2025
            )
            assert False, "Devait lever VentesTerminees"
        except VentesTerminees:
            pass


# ===========================================================================
# Scénario fil rouge : Marie réserve 2 places Concert Jazz
# ===========================================================================

class TestScenarioFilRouge:
    """
    Scénario complet : création → paiement → billets QR codes → annulation → réouverture.
    Correspond au scénario « Marie » décrit dans docs/integration-scenarios.md.
    """

    def test_parcours_nominal_complet(self):
        """
        Given  Concert Jazz 50 places, ventes ouvertes.
        When   Marie (CLI-MARIE) réserve 2 places Orchestre A1+A2,
               le système calcule 76 € (90-18+4),
               le paiement de 76 € est accepté.
        Then   Réservation Confirmée, 2 billets QR générés, jauge 48.
        """
        evt = _creer_evenement(capacite=50)
        svc, repo_evt, repo_res = _creer_service(evt)
        places = [PlaceAssignee("A", "1", 1, "Orchestre"), PlaceAssignee("A", "1", 2, "Orchestre")]

        # Étape 1 – Création de la réservation
        res = svc.creer_reservation("CLI-MARIE", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        assert res.statut == StatutReservation.EN_ATTENTE
        assert res.montant.total == 76.0
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 48

        # Étape 2 – Confirmation du paiement
        res = svc.confirmer_paiement(res.reservation_id, 76.0)
        assert res.statut == StatutReservation.CONFIRMEE
        assert len(res.billets) == 2
        for b in res.billets:
            assert b.qr_code.startswith(f"QR-{res.reservation_id}")

        # Étape 3 – Annulation et libération de la jauge
        res = svc.annuler_reservation(res.reservation_id)
        assert res.statut == StatutReservation.ANNULEE
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 50

    def test_double_reservation_concurrente_bloquee(self):
        """
        Given 1 place disponible A1.
        When  CLI-001 et CLI-002 tentent de réserver A1 simultanément.
        Then  Le second est bloqué par PlaceDejaReservee (INV-R2).
        """
        evt = _creer_evenement(capacite=5)
        svc, _, _ = _creer_service(evt)
        place_a1 = PlaceAssignee("A", "1", 1)

        svc.creer_reservation("CLI-001", evt.evenement_id, [place_a1], MONTANT_STD, AUJOURD_HUI)

        try:
            svc.creer_reservation("CLI-002", evt.evenement_id, [place_a1], MONTANT_STD, AUJOURD_HUI)
            assert False, "Devait lever PlaceDejaReservee"
        except PlaceDejaReservee:
            pass


# ===========================================================================
# Infrastructure événementielle (inline — Partie 5)
# ===========================================================================

from collections import defaultdict
from datetime import datetime, timezone


class _DomainEvent:
    def __init__(self, event_type: str, payload: dict, correlation_id: str | None = None) -> None:
        self.event_id       = f"EVE-{uuid.uuid4().hex[:8].upper()}"
        self.event_type     = event_type
        self.correlation_id = correlation_id or f"COR-{uuid.uuid4().hex[:12].upper()}"
        self.timestamp      = datetime.now(timezone.utc).isoformat()
        self.payload        = payload


class _EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list] = defaultdict(list)
        self.history: list[_DomainEvent] = []

    def subscribe(self, event_type: str, handler) -> None:
        self._subs[event_type].append(handler)

    def publish(self, event: _DomainEvent) -> None:
        self.history.append(event)
        for h in self._subs.get(event.event_type, []):
            h(event)

    def published(self, event_type: str) -> list[_DomainEvent]:
        return [e for e in self.history if e.event_type == event_type]


class _ContexteNotification:
    def __init__(self, bus: _EventBus) -> None:
        self.notifications: list[dict] = []
        bus.subscribe("RéservationConfirmée", self._on_confirmee)
        bus.subscribe("RéservationAnnulée",   self._on_annulee)

    def _on_confirmee(self, evt: _DomainEvent) -> None:
        self.notifications.append({
            "type": "email_confirmation",
            "spectateur_id":  evt.payload["spectateur_id"],
            "reservation_id": evt.payload["reservation_id"],
            "nb_billets":     len(evt.payload.get("billets", [])),
            "correlation_id": evt.correlation_id,
        })

    def _on_annulee(self, evt: _DomainEvent) -> None:
        self.notifications.append({
            "type": "email_annulation",
            "spectateur_id":  evt.payload["spectateur_id"],
            "reservation_id": evt.payload["reservation_id"],
            "correlation_id": evt.correlation_id,
        })


class _ContexteControleAcces:
    def __init__(self, bus: _EventBus) -> None:
        self.qr_codes_actifs: set[str] = set()
        bus.subscribe("RéservationConfirmée", self._on_confirmee)
        bus.subscribe("RéservationAnnulée",   self._on_annulee)

    def _on_confirmee(self, evt: _DomainEvent) -> None:
        for b in evt.payload.get("billets", []):
            self.qr_codes_actifs.add(b["qr_code"])

    def _on_annulee(self, evt: _DomainEvent) -> None:
        rid = evt.payload["reservation_id"]
        self.qr_codes_actifs = {qr for qr in self.qr_codes_actifs if rid not in qr}


# ===========================================================================
# Partie 5.4 — Scénario bout-en-bout inter-contextes
# Réservation → Paiement validé → Confirmation envoyée → QR codes activés
# ===========================================================================

class TestScenarioBoutEnBout:
    """
    Scénarios inter-contextes reliant ContexteRéservation, ContexteNotification
    et ContexteContrôleAccès via l'event bus (Partie 5.4).
    """

    def _setup(self, capacite: int = 50):
        evt = _creer_evenement(capacite=capacite)
        repo_evt = EvenementRepository()
        repo_res = ReservationRepository()
        repo_evt.sauvegarder(evt)
        svc = ServiceReservation(repo_res, repo_evt)
        bus = _EventBus()
        notif = _ContexteNotification(bus)
        acces = _ContexteControleAcces(bus)
        return evt, svc, repo_evt, bus, notif, acces

    def test_reservation_confirmee_declenche_notification_et_qr(self):
        """
        Given  Concert Jazz 50 places, ventes ouvertes.
               ContexteNotification et ContexteContrôleAccès abonnés au bus.
        When   Marie crée une réservation (2 places),
               le paiement de 76 € est confirmé,
               RéservationConfirmée est publié sur le bus.
        Then   ContexteNotification reçoit 1 email de confirmation.
               ContexteContrôleAccès active 2 QR codes.
               Le Correlation ID est propagé dans les deux contextes.
        """
        evt, svc, _, bus, notif, acces = self._setup()
        places = [PlaceAssignee("A", "1", 1), PlaceAssignee("A", "1", 2)]
        correlation_id = f"COR-{uuid.uuid4().hex[:12].upper()}"

        # Étape 1 — Créer la réservation
        res = svc.creer_reservation("CLI-MARIE", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)

        bus.publish(_DomainEvent("ReservationCréée", {
            "reservation_id": res.reservation_id,
            "evenement_id":   res.evenement_id,
            "spectateur_id":  res.spectateur_id,
            "nb_places":      len(res.places),
            "montant_total":  res.montant.total,
        }, correlation_id))

        # Étape 2 — Confirmer le paiement
        res = svc.confirmer_paiement(res.reservation_id, 76.0)
        assert res.statut == StatutReservation.CONFIRMEE

        bus.publish(_DomainEvent("RéservationConfirmée", {
            "reservation_id": res.reservation_id,
            "spectateur_id":  res.spectateur_id,
            "montant_paye":   76.0,
            "billets": [{"billet_id": b.billet_id, "qr_code": b.qr_code} for b in res.billets],
        }, correlation_id))

        # Vérifications inter-contextes
        assert len(notif.notifications) == 1
        n = notif.notifications[0]
        assert n["type"] == "email_confirmation"
        assert n["spectateur_id"] == "CLI-MARIE"
        assert n["nb_billets"] == 2
        assert n["correlation_id"] == correlation_id

        assert len(acces.qr_codes_actifs) == 2
        for b in res.billets:
            assert b.qr_code in acces.qr_codes_actifs

        assert len(bus.published("RéservationConfirmée")) == 1

    def test_annulation_declenche_notification_et_invalide_qr(self):
        """
        Given  Réservation confirmée, QR codes actifs.
        When   Le spectateur annule la réservation,
               RéservationAnnulée est publié sur le bus.
        Then   ContexteNotification reçoit 1 email d'annulation.
               ContexteContrôleAccès invalide les QR codes.
        """
        evt, svc, repo_evt, bus, notif, acces = self._setup()
        places = [PlaceAssignee("A", "1", 1)]
        correlation_id = f"COR-{uuid.uuid4().hex[:12].upper()}"

        res = svc.creer_reservation("CLI-PAUL", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        res = svc.confirmer_paiement(res.reservation_id, 76.0)

        # Activation QR
        bus.publish(_DomainEvent("RéservationConfirmée", {
            "reservation_id": res.reservation_id,
            "spectateur_id":  res.spectateur_id,
            "montant_paye":   76.0,
            "billets": [{"billet_id": b.billet_id, "qr_code": b.qr_code} for b in res.billets],
        }, correlation_id))
        assert len(acces.qr_codes_actifs) == 1

        # Annulation
        res = svc.annuler_reservation(res.reservation_id)
        assert res.statut == StatutReservation.ANNULEE

        bus.publish(_DomainEvent("RéservationAnnulée", {
            "reservation_id":     res.reservation_id,
            "evenement_id":       res.evenement_id,
            "spectateur_id":      "CLI-PAUL",
            "nb_places_liberees": len(res.places),
        }, correlation_id))

        # 2 notifications : 1 confirmation + 1 annulation
        assert len(notif.notifications) == 2
        assert notif.notifications[1]["type"] == "email_annulation"
        assert notif.notifications[1]["correlation_id"] == correlation_id
        assert len(acces.qr_codes_actifs) == 0
        assert repo_evt.trouver_par_id(evt.evenement_id).jauge_disponible == 50

    def test_correlation_id_propage_sur_tous_les_contextes(self):
        """
        Given  Un Correlation ID unique généré à l'entrée (POST /api/reservations).
        When   Le scénario complet se déroule (création → confirmation).
        Then   Le même Correlation ID se retrouve dans tous les événements publiés.
        """
        evt, svc, _, bus, notif, acces = self._setup()
        places = [PlaceAssignee("B", "2", 5)]
        correlation_id = "COR-TEST-PROPAGATION"

        res = svc.creer_reservation("CLI-TEST", evt.evenement_id, places, MONTANT_STD, AUJOURD_HUI)
        res = svc.confirmer_paiement(res.reservation_id, 76.0)

        bus.publish(_DomainEvent("RéservationConfirmée", {
            "reservation_id": res.reservation_id,
            "spectateur_id":  "CLI-TEST",
            "montant_paye":   76.0,
            "billets": [{"billet_id": b.billet_id, "qr_code": b.qr_code} for b in res.billets],
        }, correlation_id))

        # Le Correlation ID est tracé dans la notification
        assert notif.notifications[0]["correlation_id"] == correlation_id

        # Tous les événements publiés portent le même Correlation ID
        for event in bus.history:
            assert event.correlation_id == correlation_id