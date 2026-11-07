"""V10 — model fiziologic în unități reale, cu timp în zile.

Deosebirea față de modelul abstract din versiunile 1–9: aici fosfatemia este în
milimoli pe litru, timpul în zile, iar excreția renală trece prin pragul de
reabsorbție tubulară a fosfatului (TmP/GFR), aşa cum este descris fiziologic [13].
Rezultatele se pot deci compara cu valori publicate, iar modelul devine
falsificabil (vezi fila „🎯 Validare”).

Structura:
  - un compartiment extracelular pentru fosfat (variabila de stare P, mmol/L)
  - parathormonul ca variabilă de stare, cu bucla calciu–calcitriol închisă
  - calcitriolul ca variabilă de stare, reglat de funcţia renală, FGF23 şi parathormon
  - FGF23 fie fixat de utilizator, fie ca variabilă de stare reglată de fosfat,
    calcitriol şi statusul fierului [21], [22]
  - un flux de mineralizare osoasă, cu prag de fosfatemie

AVERTISMENT: parametrii cinetici (constantele de timp, coeficienţii Hill,
capacităţile maxime) NU sunt măsuraţi la om. Sunt aleşi astfel încât modelul să
reproducă medianele publicate — procedeu descris în fila de validare. Modelul nu
este validat clinic şi nu se foloseşte pentru decizii privind pacienţi reali.
"""
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

MG_DL_TO_MMOL = 0.3229          # fosfat: mg/dL -> mmol/L
MMOL_TO_MG_DL = 1 / MG_DL_TO_MMOL

# Praguri de referinţă folosite pentru indici şi pentru interpretare
FGF23_C_TERMINAL_REF = 100.0    # unităţi de referinţă pe mililitru [1]
FGF23_INTACT_REF = 50.0         # picograme pe mililitru [5]
KLOTHO_REF = 803.1              # picograme pe mililitru, mediana NHANES [3]
PTH_REF = 65.0                  # picograme pe mililitru, prag CRIC [1]
FERITINA_REF = 100.0            # micrograme pe litru, valoare de referinţă aleasă


@dataclass
class Parametri:
    """Parametrii modelului. Unităţile sunt scrise lângă fiecare câmp."""
    # --- pacient
    rfg: float = 100.0            # rata de filtrare glomerulară, mL/min/1,73 m²
    aport_fosfat_mg: float = 1200.0   # aport alimentar de fosfor, mg/zi
    fractie_absorbtie_bazala: float = 0.55   # fără calcitriol, fracţie absorbită
    # --- os / FGF23
    fgf23_fix: float = None       # dacă e dat, FGF23 intact (pg/mL) rămâne constant
    fgf23_bazal: float = 40.0     # pg/mL (test intact)
    tau_fgf23: float = 2.0        # zile
    fgf23_sensibil_fosfat: float = 1.3
    fgf23_sensibil_calcitriol: float = 0.5
    clearance_fgf23: float = 0.55   # cât de mult scade eliminarea hormonului cu funcţia renală
    # --- fier (sistemul nou din V10)
    feritina: float = 100.0       # micrograme pe litru
    fier_transcriptie: float = 1.0    # amplificarea transcrierii la deficit de fier
    clivare_fgf23: float = 1.0    # 1 = clivare normală; <1 = clivare deficitară (ADHR,
                                  # carboximaltoză ferică) -> creşte hormonul intact
    # --- rinichi
    klotho: float = KLOTHO_REF    # pg/mL, folosit ca aproximare a coreceptorului renal
    tmp_max: float = 1.35         # mmol/L, pragul maxim de reabsorbţie
    ec50_fgf23: float = 85.0      # pg/mL, concentraţia la jumătate de efect, la Klotho de referinţă
    hill_fgf23: float = 1.6
    gamma_klotho: float = 0.55    # cât de mult deplasează Klotho pragul EC50
    efect_max_fgf23: float = 0.72 # scăderea maximă a pragului prin FGF23
    k_pth: float = 110.0          # pg/mL
    efect_max_pth: float = 0.35
    integritate_tubulara: float = 1.0   # 1 = tub proximal normal
    # --- paratiroide
    pth_bazal: float = 40.0       # pg/mL
    tau_pth: float = 0.5          # zile
    calciu: float = 2.35          # mmol/L, calciu total (menţinut fix în acest model)
    calciu_ref: float = 2.35
    exponent_calciu: float = 4.0
    exponent_calcitriol: float = 0.35
    # --- vitamina D
    calcitriol_bazal: float = 120.0   # pmol/L
    tau_calcitriol: float = 1.5       # zile
    calcitriol_ref: float = 120.0
    # --- os
    mineralizare_max: float = 7.0     # mmol/zi
    prag_mineralizare: float = 0.75   # mmol/L, sub acest prag mineralizarea scade
    panta_mineralizare: float = 0.18
    resorbtie_bazala: float = 5.0     # mmol/zi
    pth_resorbtie: float = 0.004      # per pg/mL
    # --- volum
    volum_extracelular: float = 14.0  # litri

    def copie(self, **modificari):
        valori = asdict(self)
        valori.update(modificari)
        return Parametri(**valori)


# --------------------------------------------------------------------------
# Funcţii de legătură
# --------------------------------------------------------------------------
def efect_fier(feritina, p: Parametri):
    """Deficitul de fier creşte transcrierea FGF23 [21], [27].
    Întoarce un factor multiplicativ pentru producţia de hormon."""
    f = max(float(feritina), 1.0)
    return 1.0 + p.fier_transcriptie * np.clip((FERITINA_REF - f) / FERITINA_REF, 0.0, 0.9)


def ec50_efectiv(klotho, p: Parametri):
    """α-Klotho creşte afinitatea, deci coboară concentraţia la jumătate de efect [11]."""
    k = max(float(klotho), 1.0)
    return p.ec50_fgf23 * (KLOTHO_REF / k) ** p.gamma_klotho


def tmp_gfr(fgf23_intact, klotho, pth, p: Parametri):
    """Pragul de reabsorbţie tubulară a fosfatului, mmol/L."""
    f = max(float(fgf23_intact), 0.0)
    ec50 = ec50_efectiv(klotho, p)
    hill_f = f ** p.hill_fgf23 / (ec50 ** p.hill_fgf23 + f ** p.hill_fgf23)
    hill_h = max(float(pth), 0.0) / (p.k_pth + max(float(pth), 0.0))
    prag = p.tmp_max * (1 - p.efect_max_fgf23 * hill_f) * (1 - p.efect_max_pth * hill_h)
    return float(np.clip(prag * p.integritate_tubulara, 0.05, p.tmp_max))


def excretie_renala(fosfat, prag, p: Parametri):
    """Peste prag, rinichiul elimină excesul filtrat; sub prag, reţine aproape tot.
    Rezultat în mmol/zi. Factorul 1,44 converteşte mL/min în litri pe zi."""
    rfg_l_zi = p.rfg * 1.44
    return max(0.0, float(fosfat) - float(prag)) * rfg_l_zi


def absorbtie_intestinala(calcitriol, p: Parametri):
    """Fosfatul absorbit, mmol/zi. Calcitriolul creşte fracţia absorbită."""
    aport_mmol = p.aport_fosfat_mg / 30.97
    factor = p.fractie_absorbtie_bazala * (0.7 + 0.3 * float(calcitriol) / p.calcitriol_ref)
    return aport_mmol * float(np.clip(factor, 0.2, 0.95))


def flux_mineralizare(fosfat, p: Parametri):
    """Mineralizarea scade abrupt sub pragul de fosfatemie — baza osteomalaciei."""
    x = (float(fosfat) - p.prag_mineralizare) / p.panta_mineralizare
    return p.mineralizare_max / (1 + np.exp(-x))


def flux_resorbtie(pth, p: Parametri):
    return p.resorbtie_bazala * (1 + p.pth_resorbtie * max(0.0, float(pth) - p.pth_bazal))


def pth_tinta(calciu, calcitriol, p: Parametri):
    """Secreţia de parathormon creşte la calciu mic şi la calcitriol mic."""
    t = p.pth_bazal * (p.calciu_ref / max(float(calciu), 1.5)) ** p.exponent_calciu
    t *= (p.calcitriol_ref / max(float(calcitriol), 5.0)) ** p.exponent_calcitriol
    return float(np.clip(t, 5.0, 2000.0))


def fgf23_tinta(fosfat, calcitriol, p: Parametri):
    """Fosfatul şi calcitriolul stimulează producţia; deficitul de fier o amplifică.
    Clivarea redusă creşte proporţia de hormon intact [22]."""
    baza = p.fgf23_bazal
    baza *= (max(float(fosfat), 0.2) / 1.15) ** p.fgf23_sensibil_fosfat
    baza *= (max(float(calcitriol), 5.0) / p.calcitriol_ref) ** p.fgf23_sensibil_calcitriol
    baza *= efect_fier(p.feritina, p)
    # eliminarea renală a hormonului scade odată cu funcţia renală, deci concentraţia creşte
    baza *= (100.0 / max(p.rfg, 5.0)) ** p.clearance_fgf23
    baza /= max(p.clivare_fgf23, 0.05)
    return float(np.clip(baza, 1.0, 20000.0))


def fgf23_c_terminal(fgf23_intact, p: Parametri):
    """Testul C-terminal măsoară hormonul intact plus fragmentele. Când clivarea este
    normală, fragmentele domină; când clivarea scade, cele două teste se apropie [22]."""
    fragmente = fgf23_intact * p.clivare_fgf23 * 1.5 * efect_fier(p.feritina, p)
    return fgf23_intact + fragmente


# --------------------------------------------------------------------------
# Integrarea în timp
# --------------------------------------------------------------------------
def simuleaza(p: Parametri, zile=120, pas=0.25, stare_initiala=None):
    """Integrează modelul cu metoda Runge-Kutta de ordinul 4. Întoarce un tabel
    cu o linie pe zi simulată."""
    if stare_initiala is None:
        stare = np.array([1.15, p.pth_bazal, p.calcitriol_bazal,
                          p.fgf23_fix if p.fgf23_fix else p.fgf23_bazal], dtype=float)
    else:
        stare = np.array(stare_initiala, dtype=float)

    def derivate(y):
        fosfat, pth, calcitriol, fgf = y
        fosfat = max(fosfat, 0.05)
        prag = tmp_gfr(fgf, p.klotho, pth, p)
        absorbit = absorbtie_intestinala(calcitriol, p)
        excretat = excretie_renala(fosfat, prag, p)
        mineralizat = flux_mineralizare(fosfat, p)
        resorbit = flux_resorbtie(pth, p)
        d_fosfat = (absorbit - excretat - mineralizat + resorbit) / p.volum_extracelular
        d_pth = (pth_tinta(p.calciu, calcitriol, p) - pth) / p.tau_pth
        # producţia renală de calcitriol scade cu funcţia renală, cu FGF23 şi creşte cu parathormonul
        tinta_d = (p.calcitriol_bazal * (0.15 + 0.85 * p.rfg / 100.0)
                   * (1 / (1 + (fgf / max(ec50_efectiv(p.klotho, p), 1.0)) ** 1.2))
                   * (1 + 0.45 * np.log1p(max(0.0, pth - p.pth_bazal) / 60.0)))
        d_calcitriol = (float(np.clip(tinta_d, 3.0, 400.0)) - calcitriol) / p.tau_calcitriol
        if p.fgf23_fix is not None:
            d_fgf = 0.0
        else:
            d_fgf = (fgf23_tinta(fosfat, calcitriol, p) - fgf) / p.tau_fgf23
        return np.array([d_fosfat, d_pth, d_calcitriol, d_fgf])

    randuri = []
    n = int(zile / pas)
    for i in range(n + 1):
        t = i * pas
        fosfat, pth, calcitriol, fgf = stare
        prag = tmp_gfr(fgf, p.klotho, pth, p)
        absorbit = absorbtie_intestinala(calcitriol, p)
        excretat = excretie_renala(fosfat, prag, p)
        if abs(t - round(t)) < pas / 2:
            randuri.append({
                'zi': round(t, 2),
                'fosfat_mmol_L': fosfat,
                'fosfat_mg_dL': fosfat * MMOL_TO_MG_DL,
                'PTH_pg_mL': pth,
                'calcitriol_pmol_L': calcitriol,
                'FGF23_intact_pg_mL': fgf,
                'FGF23_C_terminal_RU_mL': fgf23_c_terminal(fgf, p),
                'TmP_GFR_mmol_L': prag,
                'absorbit_mmol_zi': absorbit,
                'excretat_mmol_zi': excretat,
                'mineralizare_mmol_zi': flux_mineralizare(fosfat, p),
                'FEPO4_%': 100 * excretat / max(fosfat * p.rfg * 1.44, 1e-9),
            })
        k1 = derivate(stare)
        k2 = derivate(stare + pas / 2 * k1)
        k3 = derivate(stare + pas / 2 * k2)
        k4 = derivate(stare + pas * k3)
        stare = stare + pas / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        stare[0] = np.clip(stare[0], 0.05, 6.0)
        stare[1] = np.clip(stare[1], 1.0, 3000.0)
        stare[2] = np.clip(stare[2], 1.0, 500.0)
        stare[3] = np.clip(stare[3], 0.5, 30000.0)
    return pd.DataFrame(randuri)


def stare_de_echilibru(p: Parametri, zile=240):
    """Valorile la care ajunge modelul după stabilizare — ce se compară cu literatura."""
    df = simuleaza(p, zile=zile)
    return df.iloc[-1].to_dict()


# --------------------------------------------------------------------------
# Scenarii clinice, în unităţi reale
# --------------------------------------------------------------------------
SCENARII = {
    'Adult sănătos': dict(rfg=100, klotho=KLOTHO_REF, feritina=100, clivare_fgf23=1.0,
                          integritate_tubulara=1.0, aport_fosfat_mg=1200),
    'Boală cronică renală G3b': dict(rfg=35, klotho=620, feritina=70, clivare_fgf23=0.75,
                                     integritate_tubulara=1.0, aport_fosfat_mg=1200),
    'Boală cronică renală G5': dict(rfg=12, klotho=430, feritina=55, clivare_fgf23=0.55,
                                    integritate_tubulara=1.0, aport_fosfat_mg=1200),
    'Hipofosfatemie legată de cromozomul X': dict(rfg=100, klotho=KLOTHO_REF, feritina=100,
                                                  clivare_fgf23=0.35, integritate_tubulara=1.0,
                                                  aport_fosfat_mg=1200, fgf23_fix=200),
    'Osteomalacie indusă de tumoră': dict(rfg=95, klotho=KLOTHO_REF, feritina=100,
                                          clivare_fgf23=1.0, integritate_tubulara=1.0,
                                          aport_fosfat_mg=1200, fgf23_fix=546),
    'Deficit funcțional de α-Klotho': dict(rfg=80, klotho=200, feritina=100, clivare_fgf23=0.8,
                                           integritate_tubulara=1.0, aport_fosfat_mg=1200),
    'Rahitism hipofosfatemic autozomal dominant, criză cu deficit de fier':
        dict(rfg=100, klotho=KLOTHO_REF, feritina=8, clivare_fgf23=0.20,
             integritate_tubulara=1.0, aport_fosfat_mg=1200),
    'După perfuzie cu carboximaltoză ferică': dict(rfg=95, klotho=KLOTHO_REF, feritina=160,
                                                   clivare_fgf23=0.14, integritate_tubulara=1.0,
                                                   aport_fosfat_mg=1200),
    'Aport alimentar foarte redus': dict(rfg=95, klotho=KLOTHO_REF, feritina=90, clivare_fgf23=1.0,
                                         integritate_tubulara=0.85, aport_fosfat_mg=350),
}

DESCRIERI = {
    'Adult sănătos':
        'Referinţă fiziologică: axa os–rinichi menţine fosfatemia în interval.',
    'Boală cronică renală G3b':
        'Masa nefronică scade, FGF23 creşte precoce, Klotho renal scade. Fosfatemia poate fi încă normală [1].',
    'Boală cronică renală G5':
        'Capacitatea excretorie este prea mică; retenţia de fosfat şi hiperparatiroidismul secundar devin probabile [1], [8].',
    'Hipofosfatemie legată de cromozomul X':
        'Mutaţia PHEX duce la exces de FGF23 activ, cu fosfaturie inadecvată şi calcitriol inadecvat de mic [9].',
    'Osteomalacie indusă de tumoră':
        'O tumoră mezenchimală secretă FGF23; rinichiul este sănătos, deci pierderea de fosfat este masivă [5], [10].',
    'Deficit funcțional de α-Klotho':
        'Coreceptorul scade, deci rinichiul răspunde mai slab la acelaşi hormon — rezistenţă renală la FGF23 [15].',
    'Rahitism hipofosfatemic autozomal dominant, criză cu deficit de fier':
        'Mutaţia blochează clivarea hormonului; deficitul de fier creşte transcrierea, iar criza apare când cele două se suprapun [21], [27].',
    'După perfuzie cu carboximaltoză ferică':
        'Această formulă de fier creşte hormonul biologic activ şi a produs hipofosfatemie la 50,8 la sută dintre pacienţi într-un studiu randomizat [25].',
    'Aport alimentar foarte redus':
        'Hipofosfatemie prin aport mic şi tubulopatie uşoară; FGF23 nu are un răspuns specific aici.',
}


def scenariu(nume, **modificari):
    p = Parametri(**SCENARII[nume])
    return p.copie(**modificari) if modificari else p


# --------------------------------------------------------------------------
# Validare pe date publicate
# --------------------------------------------------------------------------
# Ţintele vin din cohorta CRIC [1], [2]: fosfatemia medie pe categorii de filtrare.
TINTE_VALIDARE = [
    {'nume': 'Filtrare glomerulară ≈ 50 (CRIC, categoria ≥ 45)', 'rfg': 50,
     'fosfat_mg_dL_tinta': 3.5, 'sursa': '[1], [2]'},
    {'nume': 'Filtrare glomerulară ≈ 37 (CRIC, categoria 30–44)', 'rfg': 37,
     'fosfat_mg_dL_tinta': 3.7, 'sursa': '[1], [2]'},
    {'nume': 'Filtrare glomerulară ≈ 22 (CRIC, categoria < 30)', 'rfg': 22,
     'fosfat_mg_dL_tinta': 4.1, 'sursa': '[1], [2]'},
]


def ruleaza_validarea(p_baza: Parametri = None):
    """Compară fosfatemia de echilibru a modelului cu mediile publicate."""
    baza = p_baza or Parametri(**SCENARII['Boală cronică renală G3b'])
    randuri = []
    for t in TINTE_VALIDARE:
        # Klotho renal scade odată cu funcţia renală [15]; relaţie liniară simplă, presupusă.
        klotho = float(np.clip(300 + 5.2 * t['rfg'], 250, KLOTHO_REF))
        p = baza.copie(rfg=t['rfg'], klotho=klotho, fgf23_fix=None)
        e = stare_de_echilibru(p)
        randuri.append({
            'scenariu': t['nume'],
            'RFG': t['rfg'],
            'fosfat_simulat_mg_dL': round(e['fosfat_mg_dL'], 2),
            'fosfat_publicat_mg_dL': t['fosfat_mg_dL_tinta'],
            'eroare_mg_dL': round(e['fosfat_mg_dL'] - t['fosfat_mg_dL_tinta'], 2),
            'FGF23_C_terminal_simulat': round(e['FGF23_C_terminal_RU_mL'], 0),
            'PTH_simulat_pg_mL': round(e['PTH_pg_mL'], 0),
            'sursa': t['sursa'],
        })
    tabel = pd.DataFrame(randuri)
    eroare_medie = float(tabel['eroare_mg_dL'].abs().mean())
    return tabel, eroare_medie


def ordinea_aparitiei(p_baza: Parametri = None, rfg_grila=None):
    """Criteriul calitativ cel mai important din literatură: FGF23 creşte înaintea
    parathormonului şi a fosfatului, pe măsură ce funcţia renală scade [1]."""
    baza = p_baza or Parametri(**SCENARII['Boală cronică renală G3b'])
    grila = rfg_grila if rfg_grila is not None else list(range(90, 9, -5))
    randuri = []
    for g in grila:
        klotho = float(np.clip(300 + 5.2 * g, 250, KLOTHO_REF))
        e = stare_de_echilibru(baza.copie(rfg=g, klotho=klotho, fgf23_fix=None))
        randuri.append({
            'RFG': g,
            'FGF23_C_terminal_RU_mL': e['FGF23_C_terminal_RU_mL'],
            'PTH_pg_mL': e['PTH_pg_mL'],
            'fosfat_mg_dL': e['fosfat_mg_dL'],
            'TmP_GFR_mmol_L': e['TmP_GFR_mmol_L'],
            'calcitriol_pmol_L': e['calcitriol_pmol_L'],
        })
    return pd.DataFrame(randuri)


def prag_depasire(tabel, coloana, prag):
    """Prima valoare a filtrării glomerulare (în scădere) la care marker-ul depăşeşte pragul."""
    peste = tabel[tabel[coloana] >= prag]
    return float(peste['RFG'].max()) if len(peste) else None


def monte_carlo(p: Parametri, n=200, zile=120, variatie=0.15, seed=2026):
    """Bandă de incertitudine: repetă simularea cu parametri extraşi din distribuţii."""
    rng = np.random.default_rng(seed)
    campuri = ['tmp_max', 'ec50_fgf23', 'hill_fgf23', 'gamma_klotho', 'efect_max_fgf23',
               'mineralizare_max', 'resorbtie_bazala', 'fractie_absorbtie_bazala',
               'calcitriol_bazal', 'pth_bazal']
    traiectorii = []
    for _ in range(n):
        modificari = {}
        for c in campuri:
            baza = getattr(p, c)
            modificari[c] = float(baza * rng.normal(1.0, variatie))
        df = simuleaza(p.copie(**modificari), zile=zile)
        traiectorii.append(df['fosfat_mg_dL'].to_numpy())
    matrice = np.vstack(traiectorii)
    zile_axa = simuleaza(p, zile=zile)['zi'].to_numpy()
    return pd.DataFrame({
        'zi': zile_axa,
        'percentila_5': np.percentile(matrice, 5, axis=0),
        'mediana': np.percentile(matrice, 50, axis=0),
        'percentila_95': np.percentile(matrice, 95, axis=0),
    })
