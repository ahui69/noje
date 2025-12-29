#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤝 AI NEGOCJATOR DŁUGÓW - UNIKALNY MODUŁ
=========================================

Moduł do:
- Sprawdzania przedawnienia długów
- Generowania propozycji ugód
- Oceny szans na wygraną sprawę
- Kalkulacji optymalnej kwoty do negocjacji
- Analizy ryzyka prawnego

Copyright 2024 Mordzix AI PRO - All Rights Reserved
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import math

from .auth import verify_token

router = APIRouter(prefix="/api/negocjator", tags=["AI Negocjator"])


# ============================================================================
# MODELS
# ============================================================================

class TypDlugu(str, Enum):
    KREDYT_BANKOWY = "kredyt_bankowy"
    POZYCZKA = "pozyczka"
    KARTA_KREDYTOWA = "karta_kredytowa"
    CZYNSZ = "czynsz"
    MEDIA = "media"
    TELEKOMUNIKACJA = "telekomunikacja"
    ALIMENTY = "alimenty"
    MANDAT = "mandat"
    PODATEK = "podatek"
    SKLADKI_ZUS = "skladki_zus"
    FAKTURA_B2B = "faktura_b2b"
    INNE = "inne"


class StatusWierzyciela(str, Enum):
    PIERWOTNY = "pierwotny"  # Bank, firma
    WINDYKACJA = "windykacja"  # Firma windykacyjna
    FUNDUSZ = "fundusz"  # Fundusz sekurytyzacyjny
    KOMORNIK = "komornik"  # Egzekucja komornicza


class DlugAnalysis(BaseModel):
    typ_dlugu: TypDlugu
    kwota_glowna: float = Field(..., gt=0)
    kwota_odsetek: Optional[float] = 0
    kwota_kosztow: Optional[float] = 0
    data_wymagalnosci: date
    status_wierzyciela: StatusWierzyciela = StatusWierzyciela.PIERWOTNY
    czy_nakaz_zaplaty: bool = False
    czy_klauzula_wykonalnosci: bool = False
    czy_egzekucja: bool = False
    przerwane_przedawnienie: bool = False
    dodatkowe_info: Optional[str] = None


class PropozyjaUgody(BaseModel):
    dlug: DlugAnalysis
    sytuacja_finansowa: str = Field(..., description="opis sytuacji: trudna/średnia/dobra")
    mozliwa_jednorazowa: Optional[float] = None
    mozliwa_rata: Optional[float] = None


class OcenaSzans(BaseModel):
    typ_sprawy: str
    opis_sprawy: str
    posiadane_dowody: List[str] = []
    czy_reprezentowany: bool = False


# ============================================================================
# KNOWLEDGE BASE - PRZEDAWNIENIE
# ============================================================================

PRZEDAWNIENIE_TERMINY = {
    TypDlugu.KREDYT_BANKOWY: 3,  # działalność gospodarcza banku
    TypDlugu.POZYCZKA: 6,  # ogólny lub 3 jeśli od firmy
    TypDlugu.KARTA_KREDYTOWA: 3,
    TypDlugu.CZYNSZ: 3,  # świadczenie okresowe
    TypDlugu.MEDIA: 3,
    TypDlugu.TELEKOMUNIKACJA: 3,
    TypDlugu.ALIMENTY: 3,
    TypDlugu.MANDAT: 3,
    TypDlugu.PODATEK: 5,
    TypDlugu.SKLADKI_ZUS: 5,
    TypDlugu.FAKTURA_B2B: 3,
    TypDlugu.INNE: 6
}

# Czynniki wpływające na negocjacje
CZYNNIKI_NEGOCJACYJNE = {
    StatusWierzyciela.PIERWOTNY: {
        "elastycznosc": 0.3,
        "min_procent": 0.7,
        "opis": "Pierwotny wierzyciel - mniej skłonny do dużych ustępstw"
    },
    StatusWierzyciela.WINDYKACJA: {
        "elastycznosc": 0.5,
        "min_procent": 0.4,
        "opis": "Firma windykacyjna - kupili dług taniej, więcej miejsca na negocjacje"
    },
    StatusWierzyciela.FUNDUSZ: {
        "elastycznosc": 0.7,
        "min_procent": 0.2,
        "opis": "Fundusz sekurytyzacyjny - kupili za grosze, bardzo elastyczni"
    },
    StatusWierzyciela.KOMORNIK: {
        "elastycznosc": 0.2,
        "min_procent": 0.8,
        "opis": "Egzekucja komornicza - trudne negocjacje, ale możliwe"
    }
}


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def sprawdz_przedawnienie(dlug: DlugAnalysis) -> Dict[str, Any]:
    """
    Sprawdza czy dług jest przedawniony
    """
    termin_lat = PRZEDAWNIENIE_TERMINY.get(dlug.typ_dlugu, 6)
    
    # Data przedawnienia
    data_przedawnienia = dlug.data_wymagalnosci + timedelta(days=termin_lat * 365)
    
    # Koniec roku (nowe przepisy od 2018)
    if dlug.data_wymagalnosci >= date(2018, 7, 9):
        # Przedawnienie na koniec roku kalendarzowego
        data_przedawnienia = date(data_przedawnienia.year, 12, 31)
    
    dzisiaj = date.today()
    
    # Czy nakaz zapłaty przerywa bieg?
    if dlug.czy_nakaz_zaplaty or dlug.przerwane_przedawnienie:
        # Po przerwaniu biegnie od nowa
        if dlug.czy_klauzula_wykonalnosci:
            # Klauzula = tytuł wykonawczy, 6 lat od uprawomocnienia
            termin_lat = 6
            # Zakładamy że minęło ~6 miesięcy od nakazu do klauzuli
            data_przedawnienia = dlug.data_wymagalnosci + timedelta(days=180) + timedelta(days=termin_lat * 365)
    
    dni_do_przedawnienia = (data_przedawnienia - dzisiaj).days
    czy_przedawniony = dni_do_przedawnienia < 0
    
    return {
        "czy_przedawniony": czy_przedawniony,
        "data_przedawnienia": data_przedawnienia.isoformat(),
        "dni_do_przedawnienia": max(0, dni_do_przedawnienia),
        "termin_lat": termin_lat,
        "uwagi": [],
        "rekomendacja": ""
    }


def oblicz_propozycje_ugody(dlug: DlugAnalysis, sytuacja: str) -> Dict[str, Any]:
    """
    Generuje optymalne propozycje ugody
    """
    kwota_calkowita = dlug.kwota_glowna + dlug.kwota_odsetek + dlug.kwota_kosztow
    
    # Sprawdź przedawnienie
    przedawnienie = sprawdz_przedawnienie(dlug)
    
    # Czynniki wierzyciela
    czynnik = CZYNNIKI_NEGOCJACYJNE.get(dlug.status_wierzyciela, CZYNNIKI_NEGOCJACYJNE[StatusWierzyciela.PIERWOTNY])
    
    # Bazowy procent do zapłaty
    if przedawnienie["czy_przedawniony"]:
        min_procent = 0.05  # Dług przedawniony - można negocjować bardzo nisko
        max_procent = 0.30
        rekomendacja = "PRZEDAWNIONY"
    elif przedawnienie["dni_do_przedawnienia"] < 180:
        min_procent = 0.15  # Blisko przedawnienia
        max_procent = 0.50
        rekomendacja = "BLISKO_PRZEDAWNIENIA"
    else:
        min_procent = czynnik["min_procent"]
        max_procent = min(1.0, min_procent + 0.3)
        rekomendacja = "AKTYWNY"
    
    # Korekta za sytuację finansową
    if sytuacja.lower() in ["trudna", "ciężka", "zła", "bezrobotny"]:
        min_procent *= 0.7
        max_procent *= 0.8
    elif sytuacja.lower() in ["dobra", "stabilna"]:
        min_procent *= 1.1
        max_procent *= 1.05
    
    # Korekta za typ wierzyciela
    min_procent *= (1 - czynnik["elastycznosc"] * 0.5)
    
    # Propozycje
    propozycja_optymalna = kwota_calkowita * min_procent
    propozycja_realistyczna = kwota_calkowita * ((min_procent + max_procent) / 2)
    propozycja_maksymalna = kwota_calkowita * max_procent
    
    # Raty (12, 24, 36 miesięcy)
    raty_12 = propozycja_realistyczna / 12
    raty_24 = propozycja_realistyczna / 24
    raty_36 = propozycja_realistyczna / 36
    
    return {
        "kwota_calkowita": round(kwota_calkowita, 2),
        "status_przedawnienia": rekomendacja,
        "propozycje": {
            "optymalna_jednorazowa": round(propozycja_optymalna, 2),
            "realistyczna_jednorazowa": round(propozycja_realistyczna, 2),
            "maksymalna_jednorazowa": round(propozycja_maksymalna, 2),
            "procent_oszczednosci_min": round((1 - max_procent) * 100, 1),
            "procent_oszczednosci_max": round((1 - min_procent) * 100, 1)
        },
        "raty": {
            "rata_12_miesiecy": round(raty_12, 2),
            "rata_24_miesiecy": round(raty_24, 2),
            "rata_36_miesiecy": round(raty_36, 2)
        },
        "argumenty_negocjacyjne": generuj_argumenty(dlug, przedawnienie),
        "strategia": generuj_strategie(dlug, przedawnienie, sytuacja),
        "info_wierzyciel": czynnik["opis"]
    }


def generuj_argumenty(dlug: DlugAnalysis, przedawnienie: Dict) -> List[str]:
    """Generuje argumenty do negocjacji"""
    argumenty = []
    
    if przedawnienie["czy_przedawniony"]:
        argumenty.append("🔴 Dług jest PRZEDAWNIONY - nie ma obowiązku prawnego zapłaty")
        argumenty.append("Propozycja ugody jest wyłącznie dobrowolna i z dobrej woli")
    
    if przedawnienie["dni_do_przedawnienia"] < 180 and not przedawnienie["czy_przedawniony"]:
        argumenty.append(f"⚠️ Do przedawnienia pozostało tylko {przedawnienie['dni_do_przedawnienia']} dni")
        argumenty.append("Wierzyciel ryzykuje utratę roszczenia - warto się dogadać")
    
    if dlug.status_wierzyciela == StatusWierzyciela.FUNDUSZ:
        argumenty.append("💰 Fundusz kupił dług za 5-15% wartości - ma duży margines")
        argumenty.append("Nawet 20% spłaty to dla nich dobry zysk")
    
    if dlug.status_wierzyciela == StatusWierzyciela.WINDYKACJA:
        argumenty.append("📊 Firma windykacyjna nabyła wierzytelność z dyskontem")
        argumenty.append("Mają budżet na negocjacje - warto próbować")
    
    if dlug.kwota_odsetek > dlug.kwota_glowna * 0.5:
        argumenty.append("📈 Odsetki stanowią ponad 50% długu")
        argumenty.append("Można wnioskować o umorzenie lub znaczne obniżenie odsetek")
    
    argumenty.append("✅ Deklaruję chęć polubownego rozwiązania sprawy")
    argumenty.append("✅ Spłata jednorazowa/regularne raty = pewność dla wierzyciela")
    
    return argumenty


def generuj_strategie(dlug: DlugAnalysis, przedawnienie: Dict, sytuacja: str) -> List[Dict]:
    """Generuje strategie negocjacyjne"""
    strategie = []
    
    if przedawnienie["czy_przedawniony"]:
        strategie.append({
            "nazwa": "🛡️ Strategia obronna",
            "opis": "Podnieś zarzut przedawnienia. Nie ma obowiązku płacenia.",
            "ryzyko": "niskie",
            "rekomendacja": "Jeśli wierzyciel skieruje sprawę do sądu, podnieś zarzut przedawnienia w sprzeciwie."
        })
    
    strategie.append({
        "nazwa": "💵 Jednorazowa spłata z rabatem",
        "opis": "Zaproponuj jednorazową spłatę w zamian za umorzenie części długu",
        "ryzyko": "niskie",
        "rekomendacja": "Zacznij od najniższej propozycji i stopniowo podnoś. Nie zdradzaj maksymalnej kwoty."
    })
    
    strategie.append({
        "nazwa": "📅 Rozłożenie na raty",
        "opis": "Poproś o rozłożenie na dogodne raty bez dalszych odsetek",
        "ryzyko": "niskie",
        "rekomendacja": "Wnioskuj o zamrożenie odsetek na czas spłaty rat."
    })
    
    if dlug.czy_egzekucja:
        strategie.append({
            "nazwa": "⚖️ Powództwo przeciwegzekucyjne",
            "opis": "Jeśli są podstawy (przedawnienie, błędy), rozważ pozew przeciwegzekucyjny",
            "ryzyko": "średnie",
            "rekomendacja": "Skonsultuj z prawnikiem. Może wstrzymać egzekucję."
        })
    
    strategie.append({
        "nazwa": "🤝 Mediacja",
        "opis": "Zaproponuj mediację jako neutralne rozwiązanie",
        "ryzyko": "niskie",
        "rekomendacja": "Mediacja jest tańsza niż sąd i często skuteczna."
    })
    
    return strategie


def ocen_szanse_sprawy(sprawa: OcenaSzans) -> Dict[str, Any]:
    """
    Ocenia szanse na wygraną sprawę sądową
    """
    punkty = 50  # Bazowo 50/50
    czynniki = []
    
    # Analiza typu sprawy
    typ_lower = sprawa.typ_sprawy.lower()
    
    if "przedawnienie" in typ_lower or "przedawnion" in sprawa.opis_sprawy.lower():
        punkty += 30
        czynniki.append({"czynnik": "Przedawnienie", "wplyw": "+30%", "opis": "Zarzut przedawnienia to silna obrona"})
    
    if "brak doręczenia" in sprawa.opis_sprawy.lower() or "niedoręczon" in sprawa.opis_sprawy.lower():
        punkty += 20
        czynniki.append({"czynnik": "Brak doręczenia", "wplyw": "+20%", "opis": "Wadliwe doręczenie może unieważnić nakaz"})
    
    if "cesja" in sprawa.opis_sprawy.lower() or "fundusz" in sprawa.opis_sprawy.lower():
        punkty += 10
        czynniki.append({"czynnik": "Cesja wierzytelności", "wplyw": "+10%", "opis": "Można kwestionować prawidłowość cesji"})
    
    # Dowody
    if len(sprawa.posiadane_dowody) >= 3:
        punkty += 15
        czynniki.append({"czynnik": "Mocne dowody", "wplyw": "+15%", "opis": "Wiele dowodów wzmacnia pozycję"})
    elif len(sprawa.posiadane_dowody) == 0:
        punkty -= 15
        czynniki.append({"czynnik": "Brak dowodów", "wplyw": "-15%", "opis": "Brak dowodów osłabia sprawę"})
    
    # Reprezentacja
    if sprawa.czy_reprezentowany:
        punkty += 10
        czynniki.append({"czynnik": "Reprezentacja prawna", "wplyw": "+10%", "opis": "Profesjonalny pełnomocnik zwiększa szanse"})
    
    # Ograniczenie do 0-100
    punkty = max(5, min(95, punkty))
    
    # Interpretacja
    if punkty >= 75:
        ocena = "WYSOKIE"
        kolor = "🟢"
    elif punkty >= 50:
        ocena = "ŚREDNIE"
        kolor = "🟡"
    elif punkty >= 25:
        ocena = "NISKIE"
        kolor = "🟠"
    else:
        ocena = "BARDZO NISKIE"
        kolor = "🔴"
    
    return {
        "szanse_procent": punkty,
        "ocena": ocena,
        "kolor": kolor,
        "czynniki": czynniki,
        "rekomendacja": generuj_rekomendacje_szans(punkty)
    }


def generuj_rekomendacje_szans(punkty: int) -> str:
    """Generuje rekomendację na podstawie szans"""
    if punkty >= 75:
        return "Masz mocną pozycję. Rozważ walkę w sądzie lub negocjuj z pozycji siły."
    elif punkty >= 50:
        return "Szanse są wyrównane. Rozważ ugodę lub przygotuj się dobrze do sprawy."
    elif punkty >= 25:
        return "Szanse są słabe. Skup się na ugodzie i minimalizacji strat."
    else:
        return "Szanse są bardzo niskie. Priorytetem powinna być ugoda na najlepszych warunkach."


def oblicz_koszty_postepowania(wartosc_sporu: float, typ: str = "cywilne") -> Dict[str, Any]:
    """
    Oblicza koszty postępowania sądowego
    """
    koszty = {}
    
    # Opłata sądowa od pozwu (5% ale z widełkami)
    if wartosc_sporu <= 500:
        oplata_sadowa = 30
    elif wartosc_sporu <= 1500:
        oplata_sadowa = 100
    elif wartosc_sporu <= 4000:
        oplata_sadowa = 200
    elif wartosc_sporu <= 7500:
        oplata_sadowa = 400
    elif wartosc_sporu <= 10000:
        oplata_sadowa = 500
    elif wartosc_sporu <= 15000:
        oplata_sadowa = 750
    elif wartosc_sporu <= 20000:
        oplata_sadowa = 1000
    else:
        oplata_sadowa = min(wartosc_sporu * 0.05, 200000)  # max 200k
    
    koszty["oplata_sadowa"] = round(oplata_sadowa, 2)
    
    # Koszty zastępstwa (minimalne stawki)
    if wartosc_sporu <= 500:
        zastestwo = 90
    elif wartosc_sporu <= 1500:
        zastestwo = 270
    elif wartosc_sporu <= 5000:
        zastestwo = 900
    elif wartosc_sporu <= 10000:
        zastestwo = 1800
    elif wartosc_sporu <= 50000:
        zastestwo = 3600
    elif wartosc_sporu <= 200000:
        zastestwo = 5400
    else:
        zastestwo = 10800
    
    koszty["koszty_zastepstwa"] = round(zastestwo, 2)
    
    # Dodatkowe koszty
    koszty["koszty_komornicze"] = round(wartosc_sporu * 0.1, 2)  # 10%
    koszty["biegly_szacunkowo"] = 1500 if wartosc_sporu > 10000 else 500
    
    # Suma
    koszty["suma_przy_przegranej"] = round(
        oplata_sadowa + zastestwo * 2 + koszty["koszty_komornicze"], 2
    )
    koszty["suma_przy_wygranej"] = 0  # Przegrana strona płaci
    
    return {
        "wartosc_sporu": wartosc_sporu,
        "koszty": koszty,
        "ostrzezenie": "Przy przegranej zapłacisz koszty obu stron!",
        "porada": "Rozważ czy gra jest warta świeczki. Często ugoda jest tańsza."
    }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/sprawdz-przedawnienie")
async def endpoint_sprawdz_przedawnienie(
    dlug: DlugAnalysis,
    token: str = Depends(verify_token)
):
    """
    🔍 Sprawdza czy dług jest przedawniony
    """
    wynik = sprawdz_przedawnienie(dlug)
    
    # Dodaj uwagi
    if wynik["czy_przedawniony"]:
        wynik["uwagi"].append("✅ Dług jest przedawniony!")
        wynik["uwagi"].append("Możesz podnieść zarzut przedawnienia w sądzie")
        wynik["uwagi"].append("Wierzyciel nie może skutecznie dochodzić roszczenia")
        wynik["rekomendacja"] = "Nie płać. Jeśli sprawa trafi do sądu, podnieś zarzut przedawnienia."
    else:
        wynik["uwagi"].append(f"⏳ Dług przedawni się za {wynik['dni_do_przedawnienia']} dni")
        if wynik["dni_do_przedawnienia"] < 180:
            wynik["uwagi"].append("⚠️ Blisko przedawnienia - wierzyciel może przyspieszyć działania")
        wynik["rekomendacja"] = "Rozważ negocjacje lub poczekaj na przedawnienie."
    
    return {"ok": True, "przedawnienie": wynik}


@router.post("/propozycja-ugody")
async def endpoint_propozycja_ugody(
    request: PropozyjaUgody,
    token: str = Depends(verify_token)
):
    """
    💰 Generuje optymalne propozycje ugody z wierzycielem
    """
    wynik = oblicz_propozycje_ugody(request.dlug, request.sytuacja_finansowa)
    
    return {"ok": True, "ugoda": wynik}


@router.post("/ocen-szanse")
async def endpoint_ocen_szanse(
    sprawa: OcenaSzans,
    token: str = Depends(verify_token)
):
    """
    📊 Ocenia szanse na wygraną sprawę sądową
    """
    wynik = ocen_szanse_sprawy(sprawa)
    
    return {"ok": True, "ocena": wynik}


@router.post("/koszty-postepowania")
async def endpoint_koszty_postepowania(
    wartosc_sporu: float,
    typ: str = "cywilne",
    token: str = Depends(verify_token)
):
    """
    💸 Oblicza koszty postępowania sądowego
    """
    wynik = oblicz_koszty_postepowania(wartosc_sporu, typ)
    
    return {"ok": True, "koszty": wynik}


@router.get("/typy-dlugow")
async def endpoint_typy_dlugow(token: str = Depends(verify_token)):
    """
    📋 Lista typów długów i ich terminów przedawnienia
    """
    typy = []
    for typ, lat in PRZEDAWNIENIE_TERMINY.items():
        typy.append({
            "typ": typ.value,
            "nazwa": typ.name.replace("_", " ").title(),
            "przedawnienie_lat": lat
        })
    
    return {"ok": True, "typy": typy}


@router.get("/info")
async def endpoint_info():
    """
    ℹ️ Informacje o module Negocjatora AI
    """
    return {
        "ok": True,
        "modul": "AI Negocjator Długów",
        "wersja": "1.0.0",
        "funkcje": [
            "Sprawdzanie przedawnienia długów",
            "Generowanie propozycji ugód",
            "Ocena szans na wygraną sprawę",
            "Kalkulator kosztów postępowania",
            "Strategie negocjacyjne",
            "Argumenty do negocjacji"
        ],
        "disclaimer": "Moduł ma charakter informacyjny. Nie stanowi porady prawnej."
    }
