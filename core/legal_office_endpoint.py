#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGAL OFFICE MODULE - Profesjonalna obsługa pism urzędowych
============================================================

Moduł do:
- Analizy skanów pism urzędowych (OCR)
- Identyfikacji typu pisma i instytucji
- Generowania profesjonalnych odpowiedzi
- Podstaw prawnych i argumentacji

Obsługiwane instytucje:
- Urząd Skarbowy (US)
- Zakład Ubezpieczeń Społecznych (ZUS)
- Komornik Sądowy
- Sąd (cywilny, karny, administracyjny)
- Prokuratura
- Urząd Miasta/Gminy
- Inspekcja Pracy (PIP)
- Sanepid
- Straż Miejska / Policja
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import os
import json
import base64
import asyncio
import re

# Auth
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "changeme")

def _auth(req: Request):
    auth = req.headers.get("Authorization", "")
    token = req.query_params.get("token", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    if token != AUTH_TOKEN:
        raise HTTPException(401, "Unauthorized")
    return True


router = APIRouter(prefix="/api/legal", tags=["Legal Office"])


# ============================================================================
# ENUMS & MODELS
# ============================================================================

class InstitutionType(str, Enum):
    URZAD_SKARBOWY = "urzad_skarbowy"
    ZUS = "zus"
    KOMORNIK = "komornik"
    SAD_CYWILNY = "sad_cywilny"
    SAD_KARNY = "sad_karny"
    SAD_ADMINISTRACYJNY = "sad_administracyjny"
    PROKURATURA = "prokuratura"
    URZAD_MIASTA = "urzad_miasta"
    PIP = "pip"
    SANEPID = "sanepid"
    POLICJA = "policja"
    STRAZ_MIEJSKA = "straz_miejska"
    INNE = "inne"


class DocumentType(str, Enum):
    WEZWANIE = "wezwanie"
    DECYZJA = "decyzja"
    POSTANOWIENIE = "postanowienie"
    NAKAZ = "nakaz"
    UPOMNIENIE = "upomnienie"
    ZAWIADOMIENIE = "zawiadomienie"
    MANDAT = "mandat"
    POZEW = "pozew"
    WYROK = "wyrok"
    ZAJECIE = "zajecie"
    EGZEKUCJA = "egzekucja"
    KONTROLA = "kontrola"
    INNE = "inne"


class ResponseType(str, Enum):
    ODWOLANIE = "odwolanie"
    ZAZALENIE = "zazalenie"
    SPRZECIW = "sprzeciw"
    WNIOSEK = "wniosek"
    WYJASNENIE = "wyjasnenie"
    SKARGA = "skarga"
    APELACJA = "apelacja"
    PISMO_PROCESOWE = "pismo_procesowe"


class AnalyzeDocumentRequest(BaseModel):
    content: str = Field(..., description="Treść pisma (tekst lub base64 obrazu)")
    is_image: bool = Field(False, description="Czy content to obraz base64")
    additional_info: Optional[str] = Field(None, description="Dodatkowe informacje od użytkownika")


class GenerateResponseRequest(BaseModel):
    document_analysis: Dict[str, Any] = Field(..., description="Wynik analizy dokumentu")
    response_type: ResponseType = Field(..., description="Typ odpowiedzi do wygenerowania")
    user_arguments: Optional[str] = Field(None, description="Argumenty użytkownika")
    user_data: Optional[Dict[str, str]] = Field(None, description="Dane użytkownika (imię, adres, PESEL)")
    deadline_extension: bool = Field(False, description="Czy wnioskować o przedłużenie terminu")
    

# ============================================================================
# LEGAL KNOWLEDGE BASE
# ============================================================================

# ============================================================================
# OMNIBUS LEGAL & ECONOMIC KNOWLEDGE BASE
# Pełna baza wiedzy prawnej i ekonomicznej
# ============================================================================

LEGAL_KNOWLEDGE = {
    "urzad_skarbowy": {
        "name": "Urząd Skarbowy",
        "laws": [
            "Ordynacja podatkowa (Dz.U. 2023 poz. 2383)",
            "Ustawa o podatku dochodowym od osób fizycznych (PIT)",
            "Ustawa o podatku dochodowym od osób prawnych (CIT)",
            "Ustawa o podatku od towarów i usług (VAT)",
            "Ustawa o podatku akcyzowym",
            "Ustawa o podatku od czynności cywilnoprawnych (PCC)",
            "Kodeks postępowania administracyjnego (KPA)",
            "Kodeks karny skarbowy (KKS)",
            "Ustawa o kontroli skarbowej"
        ],
        "deadlines": {
            "odwolanie": 14,
            "zazalenie": 7,
            "wniosek_o_przywrocenie_terminu": 7,
            "skarga_do_wsa": 30,
            "skarga_kasacyjna_nsa": 30,
            "korekta_deklaracji": 0,
            "czynny_zal": 0
        },
        "common_issues": [
            "Zaległości podatkowe",
            "Kontrola podatkowa",
            "Wezwanie do złożenia deklaracji",
            "Zajęcie rachunku bankowego",
            "Egzekucja administracyjna",
            "Błędy w deklaracji PIT/VAT",
            "Odsetki za zwłokę",
            "Kary porządkowe",
            "Odpowiedzialność członków zarządu"
        ],
        "economic_aspects": [
            "Optymalizacja podatkowa",
            "Ulgi i zwolnienia podatkowe",
            "Rozliczanie strat",
            "Koszty uzyskania przychodu",
            "Amortyzacja środków trwałych"
        ]
    },
    "zus": {
        "name": "Zakład Ubezpieczeń Społecznych",
        "laws": [
            "Ustawa o systemie ubezpieczeń społecznych (Dz.U. 2023 poz. 1230)",
            "Ustawa o świadczeniach pieniężnych z ubezpieczenia społecznego w razie choroby i macierzyństwa",
            "Ustawa o emeryturach i rentach z Funduszu Ubezpieczeń Społecznych",
            "Ustawa o ubezpieczeniu społecznym z tytułu wypadków przy pracy i chorób zawodowych",
            "Ustawa o świadczeniach rodzinnych",
            "Ustawa o promocji zatrudnienia i instytucjach rynku pracy",
            "Kodeks postępowania administracyjnego",
            "Ustawa o postępowaniu egzekucyjnym w administracji"
        ],
        "deadlines": {
            "odwolanie": 30,
            "sprzeciw_od_orzeczenia_lekarza": 14,
            "wniosek_o_rozlozenie_na_raty": 0,
            "odwolanie_do_sadu_pracy": 30,
            "wniosek_o_umorzenie": 0,
            "apelacja": 14
        },
        "common_issues": [
            "Zaległe składki ZUS",
            "Odmowa świadczenia",
            "Kontrola płatnika składek",
            "Emerytura - błędne obliczenie",
            "Renta z tytułu niezdolności do pracy",
            "Zasiłek chorobowy - odmowa",
            "Zasiłek macierzyński",
            "Świadczenie rehabilitacyjne",
            "Odpowiedzialność członków zarządu za składki",
            "Zbieg tytułów ubezpieczeń"
        ],
        "economic_aspects": [
            "Podstawa wymiaru składek",
            "Ulga na start (6 miesięcy)",
            "Preferencyjne składki ZUS (24 miesiące)",
            "Mały ZUS Plus",
            "Dobrowolne ubezpieczenie chorobowe"
        ]
    },
    "komornik": {
        "name": "Komornik Sądowy",
        "laws": [
            "Kodeks postępowania cywilnego (art. 758-1088) - postępowanie egzekucyjne",
            "Ustawa o komornikach sądowych (Dz.U. 2023 poz. 1691)",
            "Ustawa o kosztach komorniczych",
            "Rozporządzenie w sprawie określenia przedmiotów należących do dłużnika, które nie podlegają egzekucji",
            "Kodeks pracy (art. 87-91) - potrącenia z wynagrodzenia",
            "Prawo bankowe - zajęcie rachunku"
        ],
        "deadlines": {
            "skarga_na_czynnosci": 7,
            "wniosek_o_umorzenie": 0,
            "powodztwo_przeciwegzekucyjne": 0,
            "zazalenie_na_postanowienie_sadu": 7,
            "wniosek_o_obnizenie_kosztow": 0
        },
        "common_issues": [
            "Zajęcie wynagrodzenia za pracę",
            "Zajęcie rachunku bankowego",
            "Zajęcie ruchomości",
            "Licytacja nieruchomości",
            "Zawyżone koszty egzekucji",
            "Egzekucja alimentów",
            "Zbieg egzekucji",
            "Zajęcie świadczeń wolnych od egzekucji",
            "Wyjawienie majątku"
        ],
        "economic_aspects": [
            "Kwota wolna od zajęcia (minimalne wynagrodzenie)",
            "Ograniczenia zajęcia emerytury/renty (75%/50%/25%)",
            "Świadczenia niepodlegające egzekucji (500+, alimenty)",
            "Koszty egzekucyjne (10% wartości)",
            "Opłata stosunkowa vs. stała"
        ]
    },
    "sad_cywilny": {
        "name": "Sąd Cywilny",
        "laws": [
            "Kodeks postępowania cywilnego (Dz.U. 2023 poz. 1550)",
            "Kodeks cywilny (Dz.U. 2023 poz. 1610)",
            "Ustawa o kosztach sądowych w sprawach cywilnych",
            "Kodeks rodzinny i opiekuńczy",
            "Ustawa o własności lokali",
            "Prawo upadłościowe",
            "Prawo restrukturyzacyjne",
            "Ustawa o ochronie praw lokatorów"
        ],
        "deadlines": {
            "sprzeciw_od_nakazu": 14,
            "sprzeciw_od_nakazu_epu": 14,
            "apelacja": 14,
            "zazalenie": 7,
            "skarga_kasacyjna": 60,
            "skarga_o_wznowienie": 90,
            "wniosek_o_uzasadnienie": 7,
            "pozew_wzajemny": 14
        },
        "common_issues": [
            "Nakaz zapłaty w postępowaniu upominawczym",
            "Nakaz zapłaty w postępowaniu nakazowym",
            "E-Sąd (EPU) - elektroniczne postępowanie upominawcze",
            "Pozew o zapłatę",
            "Przedawnienie roszczeń",
            "Sprawa spadkowa - dział spadku",
            "Rozwód i podział majątku",
            "Alimenty",
            "Eksmisja",
            "Odszkodowanie i zadośćuczynienie"
        ],
        "economic_aspects": [
            "Opłata sądowa (5% wartości przedmiotu sporu)",
            "Zwolnienie od kosztów sądowych",
            "Odsetki ustawowe za opóźnienie (11.25% rocznie)",
            "Odsetki maksymalne (20% rocznie)",
            "Przedawnienie - terminy (6 lat ogólny, 3 lata działalność gospodarcza)",
            "Klauzula wykonalności"
        ]
    },
    "prokuratura": {
        "name": "Prokuratura",
        "laws": [
            "Kodeks postępowania karnego (Dz.U. 2022 poz. 1375)",
            "Kodeks karny (Dz.U. 2022 poz. 1138)",
            "Kodeks karny skarbowy",
            "Ustawa o prokuraturze",
            "Kodeks wykroczeń",
            "Ustawa o przeciwdziałaniu praniu pieniędzy"
        ],
        "deadlines": {
            "zazalenie_na_postanowienie": 7,
            "wniosek_o_dostep_do_akt": 0,
            "apelacja_od_wyroku": 14,
            "kasacja": 30,
            "wniosek_o_wznowienie": 0,
            "sprzeciw_od_wyroku_nakazowego": 7
        },
        "common_issues": [
            "Wezwanie na przesłuchanie w charakterze świadka",
            "Przedstawienie zarzutów",
            "Postanowienie o umorzeniu śledztwa",
            "Akt oskarżenia",
            "Zawiadomienie o popełnieniu przestępstwa",
            "Tymczasowe aresztowanie",
            "Dozór policyjny",
            "Poręczenie majątkowe",
            "Wyrok nakazowy"
        ],
        "economic_aspects": [
            "Kaucja/poręczenie majątkowe",
            "Przepadek korzyści majątkowej",
            "Naprawienie szkody",
            "Nawiązka",
            "Grzywna (stawka dzienna 10-2000 zł)"
        ]
    },
    "sad_administracyjny": {
        "name": "Wojewódzki Sąd Administracyjny / NSA",
        "laws": [
            "Prawo o postępowaniu przed sądami administracyjnymi",
            "Kodeks postępowania administracyjnego",
            "Ordynacja podatkowa",
            "Prawo budowlane",
            "Ustawa o planowaniu i zagospodarowaniu przestrzennym"
        ],
        "deadlines": {
            "skarga_do_wsa": 30,
            "skarga_kasacyjna_nsa": 30,
            "zazalenie": 7,
            "wniosek_o_wstrzymanie_wykonania": 0
        },
        "common_issues": [
            "Decyzje podatkowe",
            "Pozwolenia na budowę",
            "Decyzje środowiskowe",
            "Odmowa wydania zezwolenia",
            "Bezczynność organu"
        ]
    },
    "urzad_pracy": {
        "name": "Powiatowy Urząd Pracy",
        "laws": [
            "Ustawa o promocji zatrudnienia i instytucjach rynku pracy",
            "Kodeks pracy",
            "Ustawa o szczególnych rozwiązaniach związanych z ochroną miejsc pracy"
        ],
        "deadlines": {
            "odwolanie": 14,
            "wniosek_o_przywrocenie_statusu": 14
        },
        "common_issues": [
            "Utrata statusu bezrobotnego",
            "Odmowa przyznania zasiłku",
            "Zwrot nienależnie pobranych świadczeń",
            "Dotacja na rozpoczęcie działalności"
        ]
    },
    "inspekcja_pracy": {
        "name": "Państwowa Inspekcja Pracy",
        "laws": [
            "Kodeks pracy",
            "Ustawa o Państwowej Inspekcji Pracy",
            "Rozporządzenia BHP"
        ],
        "deadlines": {
            "odwolanie_od_nakazu": 14,
            "skarga": 0
        },
        "common_issues": [
            "Nakaz usunięcia naruszeń",
            "Kary za naruszenie BHP",
            "Kontrola legalności zatrudnienia"
        ]
    },
    "urzad_miasta": {
        "name": "Urząd Miasta/Gminy",
        "laws": [
            "Kodeks postępowania administracyjnego",
            "Ustawa o samorządzie gminnym",
            "Prawo budowlane",
            "Ustawa o gospodarce nieruchomościami",
            "Ustawa o podatkach i opłatach lokalnych"
        ],
        "deadlines": {
            "odwolanie": 14,
            "zazalenie": 7,
            "skarga_do_wsa": 30
        },
        "common_issues": [
            "Podatek od nieruchomości",
            "Opłaty lokalne",
            "Pozwolenia i zezwolenia",
            "Warunki zabudowy",
            "Dodatek mieszkaniowy"
        ]
    }
}

# ============================================================================
# ECONOMIC & FINANCIAL KNOWLEDGE
# ============================================================================

ECONOMIC_KNOWLEDGE = {
    "przedawnienie": {
        "ogolne": 6,  # lat
        "dzialalnosc_gospodarcza": 3,
        "roszczenia_okresowe": 3,
        "roszczenia_z_umowy_o_prace": 3,
        "mandat_karny": 3,
        "podatki": 5,
        "skladki_zus": 5,
        "wykroczenia": 2
    },
    "odsetki": {
        "ustawowe_kapitałowe": 9.0,  # % rocznie
        "ustawowe_za_opoznienie": 11.25,
        "maksymalne": 20.0,
        "od_zaleglosci_podatkowych": 14.5,
        "od_zaleglosci_zus": 14.5
    },
    "kwoty_wolne": {
        "minimalne_wynagrodzenie_2024": 4242,
        "wolne_od_zajecia_komorniczego": 4242,  # minimalne wynagrodzenie
        "wolne_emerytura_renta": 75,  # % - alimenty, 50% - inne, 25% - bez tytułu
        "kwota_wolna_pit": 30000
    },
    "oplaty_sadowe": {
        "pozew_o_zaplate_do_500": 30,
        "pozew_o_zaplate_500_1500": 100,
        "pozew_o_zaplate_1500_4000": 200,
        "pozew_o_zaplate_4000_7500": 400,
        "pozew_o_zaplate_7500_10000": 500,
        "pozew_o_zaplate_10000_15000": 750,
        "pozew_o_zaplate_15000_20000": 1000,
        "pozew_o_zaplate_powyzej_20000_procent": 5,  # % wartości
        "apelacja": "jak oplata od pozwu",
        "skarga_kasacyjna": "jak oplata od pozwu",
        "sprzeciw_od_nakazu": 0,
        "skarga_do_wsa": 200,
        "skarga_kasacyjna_nsa": 100
    }
}

RESPONSE_TEMPLATES = {
    "header": """
{miejscowosc}, dnia {data}

{nadawca_imie_nazwisko}
{nadawca_adres}
{nadawca_kod_miasto}
{nadawca_kontakt}

{adresat_nazwa}
{adresat_adres}

Sygnatura akt: {sygnatura}

""",
    
    "odwolanie": """ODWOŁANIE
od {typ_decyzji} z dnia {data_decyzji}

Na podstawie art. {podstawa_prawna} wnoszę odwołanie od {typ_decyzji} z dnia {data_decyzji}, 
doręczonej mi w dniu {data_doreczenia}, i wnoszę o:

1. Uchylenie zaskarżonej decyzji w całości / zmianę decyzji poprzez {zadanie}

UZASADNIENIE

{uzasadnienie}

PODSTAWA PRAWNA

{podstawy_prawne}

WNIOSKI DOWODOWE

{wnioski_dowodowe}

Z poważaniem,
{podpis}

Załączniki:
{zalaczniki}
""",

    "zazalenie": """ZAŻALENIE
na postanowienie z dnia {data_postanowienia}

Na podstawie art. {podstawa_prawna} wnoszę zażalenie na postanowienie {organ} 
z dnia {data_postanowienia} w przedmiocie {przedmiot}.

Zaskarżonemu postanowieniu zarzucam:
{zarzuty}

W związku z powyższym wnoszę o:
{wnioski}

UZASADNIENIE
{uzasadnienie}

Z poważaniem,
{podpis}
""",

    "sprzeciw": """SPRZECIW
od nakazu zapłaty z dnia {data_nakazu}
w sprawie o sygn. akt {sygnatura}

Działając w imieniu własnym, wnoszę sprzeciw od nakazu zapłaty wydanego przez 
{sad} w dniu {data_nakazu} w sprawie o sygn. akt {sygnatura}.

Zaskarżam nakaz zapłaty w całości i wnoszę o:
1. Uchylenie nakazu zapłaty
2. Oddalenie powództwa w całości
3. Zasądzenie od powoda na rzecz pozwanego kosztów procesu

UZASADNIENIE
{uzasadnienie}

ZARZUTY
{zarzuty}

WNIOSKI DOWODOWE
{wnioski_dowodowe}

{podpis}
""",

    "wniosek_o_raty": """WNIOSEK
o rozłożenie zaległości na raty

Zwracam się z prośbą o rozłożenie zaległości w kwocie {kwota} zł 
na {liczba_rat} miesięcznych rat.

UZASADNIENIE
{uzasadnienie}

Moja aktualna sytuacja finansowa:
- Dochód miesięczny: {dochod} zł
- Wydatki stałe: {wydatki} zł
- Osoby na utrzymaniu: {osoby}

Proponuję spłatę w ratach po {rata} zł miesięcznie, począwszy od {data_pierwszej_raty}.

Zobowiązuję się do terminowego regulowania rat. W przypadku braku spłaty którejkolwiek 
raty w terminie, wyrażam zgodę na natychmiastową wymagalność całej pozostałej kwoty.

{podpis}

Załączniki:
1. Zaświadczenie o dochodach
2. Dokumenty potwierdzające wydatki
""",

    "skarga_na_komornika": """SKARGA
na czynności Komornika Sądowego {komornik}
przy Sądzie Rejonowym w {sad}

Sygn. akt komorniczych: {sygnatura_km}

Na podstawie art. 767 k.p.c. wnoszę skargę na czynności Komornika polegające na:
{opis_czynnosci}

dokonane w dniu {data_czynnosci}.

Zaskarżonym czynnościom zarzucam:
{zarzuty}

W związku z powyższym wnoszę o:
{wnioski}

UZASADNIENIE
{uzasadnienie}

{podpis}
"""
}


# ============================================================================
# OCR & DOCUMENT ANALYSIS
# ============================================================================

async def perform_ocr(image_base64: str) -> str:
    """
    Wykonuje OCR na obrazie używając Vision API
    """
    try:
        # Próbuj użyć lokalnego Vision API
        from core.llm import get_llm_client
        
        client = get_llm_client()
        
        # Jeśli mamy dostęp do vision modelu
        response = await client.chat.completions.create(
            model="glm-4v-flash",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Przeczytaj dokładnie cały tekst z tego dokumentu urzędowego. 
                        Zwróć pełną treść pisma zachowując formatowanie, daty, numery, paragrafy.
                        Jeśli są pieczątki lub podpisy, zaznacz ich lokalizację."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }],
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback - spróbuj Replicate
        try:
            import httpx
            
            replicate_key = os.getenv("REPLICATE_API_KEY", "")
            if not replicate_key:
                raise Exception("No vision API available")
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {replicate_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "version": "yorickvp/llava-13b:latest",
                        "input": {
                            "image": f"data:image/jpeg;base64,{image_base64}",
                            "prompt": "Read and transcribe all text from this official document. Include all dates, numbers, paragraphs."
                        }
                    }
                )
                
                if response.status_code == 201:
                    result = response.json()
                    # Poll for result
                    for _ in range(30):
                        await asyncio.sleep(2)
                        poll = await client.get(
                            result["urls"]["get"],
                            headers={"Authorization": f"Token {replicate_key}"}
                        )
                        poll_data = poll.json()
                        if poll_data["status"] == "succeeded":
                            return poll_data["output"]
                        elif poll_data["status"] == "failed":
                            break
                            
        except:
            pass
            
        return f"[OCR Error: {str(e)}] - Proszę wkleić tekst pisma ręcznie"


def identify_institution(text: str) -> InstitutionType:
    """Identyfikuje instytucję na podstawie treści"""
    text_lower = text.lower()
    
    patterns = {
        InstitutionType.URZAD_SKARBOWY: [
            "urząd skarbowy", "naczelnik urzędu skarbowego", "pit", "vat", 
            "podatek", "ordynacja podatkowa", "zeznanie podatkowe"
        ],
        InstitutionType.ZUS: [
            "zakład ubezpieczeń społecznych", "zus", "składki", "emerytur",
            "rent", "zasiłek", "ubezpieczenie społeczne"
        ],
        InstitutionType.KOMORNIK: [
            "komornik", "egzekucja", "zajęcie", "tytuł wykonawczy",
            "postępowanie egzekucyjne", "km ", "kmp "
        ],
        InstitutionType.SAD_CYWILNY: [
            "sąd rejonowy", "sąd okręgowy", "nakaz zapłaty", "pozew",
            "powód", "pozwany", "k.p.c.", "sprawa cywilna"
        ],
        InstitutionType.SAD_KARNY: [
            "oskarżony", "k.k.", "k.p.k.", "przestępstwo", "wyrok karny",
            "akt oskarżenia"
        ],
        InstitutionType.PROKURATURA: [
            "prokuratura", "prokurator", "postępowanie przygotowawcze",
            "podejrzany", "przesłuchanie", "śledztwo", "dochodzenie"
        ],
        InstitutionType.PIP: [
            "państwowa inspekcja pracy", "pip", "inspektor pracy"
        ],
        InstitutionType.POLICJA: [
            "komenda policji", "komisariat", "mandaty", "wykroczenie"
        ]
    }
    
    for inst, keywords in patterns.items():
        if any(kw in text_lower for kw in keywords):
            return inst
            
    return InstitutionType.INNE


def identify_document_type(text: str) -> DocumentType:
    """Identyfikuje typ dokumentu"""
    text_lower = text.lower()
    
    patterns = {
        DocumentType.WEZWANIE: ["wezwanie", "wzywam", "wzywa się"],
        DocumentType.DECYZJA: ["decyzja", "postanawiam", "orzekam"],
        DocumentType.POSTANOWIENIE: ["postanowienie", "postanawia się"],
        DocumentType.NAKAZ: ["nakaz zapłaty", "nakazuję"],
        DocumentType.UPOMNIENIE: ["upomnienie", "upominam"],
        DocumentType.ZAWIADOMIENIE: ["zawiadomienie", "zawiadamiam"],
        DocumentType.ZAJECIE: ["zajęcie", "zajmuję", "zajęto"],
        DocumentType.EGZEKUCJA: ["egzekucja", "tytuł wykonawczy"],
        DocumentType.WYROK: ["wyrok", "sąd orzeka", "zasądza"],
        DocumentType.POZEW: ["pozew", "powód wnosi"]
    }
    
    for doc_type, keywords in patterns.items():
        if any(kw in text_lower for kw in keywords):
            return doc_type
            
    return DocumentType.INNE


def extract_key_info(text: str) -> Dict[str, Any]:
    """Wyciąga kluczowe informacje z pisma"""
    info = {}
    
    # Sygnatura
    sig_patterns = [
        r'sygn(?:atura)?\.?\s*(?:akt)?:?\s*([A-Z0-9\-/\.]+)',
        r'nr\s*sprawy:?\s*([A-Z0-9\-/\.]+)',
        r'([A-Z]{1,3}\s*\d+/\d+)',
        r'(KM\s*\d+/\d+)',
        r'(Km\s*\d+/\d+)'
    ]
    for pattern in sig_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['sygnatura'] = match.group(1).strip()
            break
    
    # Kwota
    amount_patterns = [
        r'kwot[aęy]\s*:?\s*([\d\s]+[,\.]\d{2})\s*(?:zł|PLN)',
        r'([\d\s]+[,\.]\d{2})\s*(?:zł|PLN)',
        r'należność[^0-9]*([\d\s]+[,\.]\d{2})'
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['kwota'] = match.group(1).replace(' ', '').replace(',', '.')
            break
    
    # Daty
    date_patterns = [
        r'(?:z dnia|dnia|w dniu)\s*(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})',
        r'(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{4})'
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    if dates:
        info['daty'] = list(set(dates))[:5]
    
    # Termin
    deadline_patterns = [
        r'(?:w terminie|termin)\s*(\d+)\s*dni',
        r'do dnia\s*(\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4})'
    ]
    for pattern in deadline_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['termin'] = match.group(1)
            break
    
    # Paragraf/artykuły
    art_pattern = r'art\.?\s*(\d+[a-z]?(?:\s*§\s*\d+)?(?:\s*(?:ust|pkt)\.?\s*\d+)?)'
    articles = re.findall(art_pattern, text, re.IGNORECASE)
    if articles:
        info['artykuly'] = list(set(articles))[:10]
    
    return info


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze")
async def analyze_document(
    req: Request,
    content: str = Form(...),
    is_image: bool = Form(False),
    additional_info: str = Form(None),
    _=Depends(_auth)
):
    """
    📄 ANALIZA PISMA URZĘDOWEGO
    
    Analizuje pismo (tekst lub skan) i zwraca:
    - Typ instytucji
    - Typ dokumentu
    - Kluczowe informacje (sygnatura, kwoty, terminy)
    - Podstawy prawne
    - Sugerowane odpowiedzi
    """
    try:
        # OCR jeśli to obraz
        if is_image:
            text_content = await perform_ocr(content)
        else:
            text_content = content
        
        # Identyfikacja
        institution = identify_institution(text_content)
        doc_type = identify_document_type(text_content)
        key_info = extract_key_info(text_content)
        
        # Pobierz wiedzę prawną
        inst_knowledge = LEGAL_KNOWLEDGE.get(institution.value, {})
        
        # Oblicz termin na odpowiedź
        deadline_days = None
        if doc_type in [DocumentType.DECYZJA, DocumentType.POSTANOWIENIE]:
            deadline_days = inst_knowledge.get("deadlines", {}).get("odwolanie", 14)
        elif doc_type == DocumentType.NAKAZ:
            deadline_days = 14  # sprzeciw od nakazu
        
        # Sugerowane typy odpowiedzi
        suggested_responses = []
        if doc_type == DocumentType.DECYZJA:
            suggested_responses = [ResponseType.ODWOLANIE, ResponseType.WNIOSEK]
        elif doc_type == DocumentType.POSTANOWIENIE:
            suggested_responses = [ResponseType.ZAZALENIE]
        elif doc_type == DocumentType.NAKAZ:
            suggested_responses = [ResponseType.SPRZECIW]
        elif doc_type == DocumentType.WEZWANIE:
            suggested_responses = [ResponseType.WYJASNENIE, ResponseType.WNIOSEK]
        elif doc_type == DocumentType.ZAJECIE:
            suggested_responses = [ResponseType.SKARGA, ResponseType.WNIOSEK]
        
        return {
            "ok": True,
            "analysis": {
                "institution": {
                    "type": institution.value,
                    "name": inst_knowledge.get("name", institution.value)
                },
                "document": {
                    "type": doc_type.value,
                    "key_info": key_info
                },
                "legal": {
                    "applicable_laws": inst_knowledge.get("laws", []),
                    "deadlines": inst_knowledge.get("deadlines", {}),
                    "deadline_days": deadline_days
                },
                "suggested_responses": [r.value for r in suggested_responses],
                "extracted_text": text_content[:2000] if is_image else None,
                "warnings": []
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.post("/generate-response")
async def generate_response(
    req: Request,
    body: GenerateResponseRequest,
    _=Depends(_auth)
):
    """
    📝 GENEROWANIE ODPOWIEDZI NA PISMO
    
    Generuje profesjonalną odpowiedź z:
    - Prawidłowym formatowaniem
    - Podstawami prawnymi
    - Argumentacją
    - Wnioskami
    """
    try:
        from core.llm import ask_llm
        
        analysis = body.document_analysis
        institution = analysis.get("institution", {}).get("type", "inne")
        doc_info = analysis.get("document", {})
        legal_info = analysis.get("legal", {})
        
        # Pobierz szablon
        template_key = body.response_type.value
        if template_key == "odwolanie" and institution == "zus":
            template_key = "odwolanie"
        
        # Buduj prompt dla LLM
        prompt = f"""Jesteś prawnikiem specjalizującym się w postępowaniach administracyjnych i sądowych.
        
Wygeneruj profesjonalne pismo - {body.response_type.value.upper()} w odpowiedzi na:
- Instytucja: {analysis.get("institution", {}).get("name", institution)}
- Typ dokumentu: {doc_info.get("type", "nieznany")}
- Sygnatura: {doc_info.get("key_info", {}).get("sygnatura", "do uzupełnienia")}
- Kwota (jeśli dotyczy): {doc_info.get("key_info", {}).get("kwota", "nie dotyczy")} zł

Argumenty strony:
{body.user_arguments or "Brak dodatkowych argumentów"}

Dane nadawcy:
{json.dumps(body.user_data or {}, ensure_ascii=False)}

Podstawy prawne do wykorzystania:
{json.dumps(legal_info.get("applicable_laws", []), ensure_ascii=False)}

{"UWAGA: Wnioskuj również o przedłużenie terminu!" if body.deadline_extension else ""}

WYMAGANIA:
1. Pismo musi mieć prawidłową strukturę formalną (nagłówek, sygnatura, treść, uzasadnienie, wnioski, podpis)
2. Używaj odpowiednich paragrafów i artykułów prawnych
3. Argumentacja musi być logiczna i profesjonalna
4. Język formalny, prawniczy
5. Zaproponuj konkretne rozwiązanie problemu
6. Dodaj pouczenie o środkach odwoławczych jeśli dotyczy
7. Na końcu dodaj listę załączników

Wygeneruj kompletne pismo:"""

        # Generuj odpowiedź
        response = await ask_llm(prompt, max_tokens=4000, temperature=0.3)
        
        # Formatowanie
        today = datetime.now().strftime("%d.%m.%Y")
        
        return {
            "ok": True,
            "response": {
                "type": body.response_type.value,
                "content": response,
                "generated_at": today,
                "deadline_info": {
                    "original_deadline_days": legal_info.get("deadline_days"),
                    "extension_requested": body.deadline_extension
                },
                "legal_basis": legal_info.get("applicable_laws", []),
                "tips": [
                    "Wyślij pismo listem poleconym za potwierdzeniem odbioru",
                    "Zachowaj kopię pisma dla siebie",
                    "Pamiętaj o podpisie własnoręcznym",
                    "Dołącz wszystkie wymienione załączniki"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")


@router.get("/templates")
async def get_templates(_=Depends(_auth)):
    """
    📋 LISTA SZABLONÓW PISM
    
    Zwraca dostępne szablony odpowiedzi
    """
    return {
        "ok": True,
        "templates": [
            {
                "id": "odwolanie",
                "name": "Odwołanie od decyzji",
                "description": "Odwołanie od decyzji administracyjnej (US, ZUS, Urząd)",
                "deadline": "14 dni od doręczenia"
            },
            {
                "id": "zazalenie", 
                "name": "Zażalenie",
                "description": "Zażalenie na postanowienie",
                "deadline": "7 dni od doręczenia"
            },
            {
                "id": "sprzeciw",
                "name": "Sprzeciw od nakazu zapłaty",
                "description": "Sprzeciw od nakazu zapłaty w postępowaniu upominawczym",
                "deadline": "14 dni od doręczenia"
            },
            {
                "id": "wniosek",
                "name": "Wniosek",
                "description": "Wniosek o rozłożenie na raty / umorzenie / przywrócenie terminu",
                "deadline": "Brak terminu"
            },
            {
                "id": "skarga",
                "name": "Skarga",
                "description": "Skarga na czynności komornika / organu",
                "deadline": "7 dni od czynności"
            },
            {
                "id": "wyjasnenie",
                "name": "Wyjaśnienie / Odpowiedź",
                "description": "Odpowiedź na wezwanie z wyjaśnieniami",
                "deadline": "Zgodnie z wezwaniem"
            }
        ]
    }


@router.get("/institutions")
async def get_institutions(_=Depends(_auth)):
    """
    🏛️ LISTA INSTYTUCJI
    
    Zwraca obsługiwane instytucje z informacjami prawnymi
    """
    return {
        "ok": True,
        "institutions": [
            {
                "id": inst,
                "name": data.get("name", inst),
                "laws": data.get("laws", []),
                "deadlines": data.get("deadlines", {}),
                "common_issues": data.get("common_issues", [])
            }
            for inst, data in LEGAL_KNOWLEDGE.items()
        ]
    }


@router.post("/calculate-deadline")
async def calculate_deadline(
    document_date: str = Form(...),
    institution: str = Form(...),
    response_type: str = Form("odwolanie"),
    _=Depends(_auth)
):
    """
    📅 KALKULATOR TERMINÓW
    
    Oblicza termin na złożenie odpowiedzi
    """
    try:
        # Parse daty
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
            try:
                doc_date = datetime.strptime(document_date, fmt)
                break
            except:
                continue
        else:
            raise ValueError("Nieprawidłowy format daty")
        
        # Pobierz termin
        inst_data = LEGAL_KNOWLEDGE.get(institution, {})
        deadlines = inst_data.get("deadlines", {})
        days = deadlines.get(response_type, 14)
        
        # Oblicz deadline
        deadline_date = doc_date + timedelta(days=days)
        
        # Sprawdź czy nie wypada w weekend
        while deadline_date.weekday() >= 5:
            deadline_date += timedelta(days=1)
        
        days_left = (deadline_date - datetime.now()).days
        
        return {
            "ok": True,
            "deadline": {
                "document_date": doc_date.strftime("%d.%m.%Y"),
                "deadline_date": deadline_date.strftime("%d.%m.%Y"),
                "days_allowed": days,
                "days_left": max(0, days_left),
                "is_urgent": days_left <= 3,
                "is_expired": days_left < 0
            },
            "tips": [
                "Termin liczy się od dnia następnego po doręczeniu",
                "Pismo nadane w placówce pocztowej w ostatnim dniu terminu jest złożone w terminie",
                "Soboty, niedziele i święta - jeśli termin kończy się w taki dzień, przesuwa się na następny dzień roboczy"
            ]
        }
        
    except Exception as e:
        raise HTTPException(400, f"Calculation failed: {str(e)}")


@router.post("/upload-scan")
async def upload_scan(
    file: UploadFile = File(...),
    _=Depends(_auth)
):
    """
    📤 UPLOAD SKANU PISMA
    
    Przyjmuje skan i wykonuje OCR
    """
    try:
        # Sprawdź typ pliku
        if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
            raise HTTPException(400, "Tylko obrazy (JPG, PNG) lub PDF")
        
        # Odczytaj zawartość
        content = await file.read()
        
        # Konwertuj do base64
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # OCR
        extracted_text = await perform_ocr(image_base64)
        
        # Analiza
        institution = identify_institution(extracted_text)
        doc_type = identify_document_type(extracted_text)
        key_info = extract_key_info(extracted_text)
        
        return {
            "ok": True,
            "filename": file.filename,
            "extracted_text": extracted_text,
            "analysis": {
                "institution": institution.value,
                "document_type": doc_type.value,
                "key_info": key_info
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
