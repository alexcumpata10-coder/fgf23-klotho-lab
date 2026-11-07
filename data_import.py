"""V9 — import și prelucrare de date reale (sau demonstrative) pentru laborator.

Formule implementate:
- rata estimată de filtrare glomerulară: ecuația CKD-EPI 2021 cu creatinină, fără rasă [12]
- fracția de excreție a fosfatului (FEPO4) și reabsorbția tubulară a fosfatului (TRP)
- reabsorbția tubulară maximă a fosfatului raportată la filtrarea glomerulară (TmP/GFR),
  formula Payne / Kenny–Glen [13]
Toate concentrațiile din aceeași formulă trebuie să fie în aceleași unități.
"""
import numpy as np
import pandas as pd

MG_DL_TO_MMOL_PHOSPHATE = 0.3229
CREAT_UMOL_PER_MG_DL = 88.42
C_TERMINAL_ANCHOR = 100.0  # RU/mL, prag CRIC [1]
INTACT_ANCHOR = 50.0       # pg/mL, limita superioară NIH [5]

# coloanele standard ale laboratorului (șablonul CSV)
STANDARD_COLUMNS = {
    'id': 'Identificator pacient (anonim)',
    'grup': 'Grup / diagnostic (de exemplu boală cronică renală, osteomalacie)',
    'varsta_ani': 'Vârsta (ani)',
    'sex': 'Sex (F / M)',
    'creatinina_mg_dL': 'Creatinină serică (mg/dL)',
    'egfr': 'Rata estimată de filtrare glomerulară (mL/min/1,73 m²) — opțional dacă există creatinina',
    'fosfat_mg_dL': 'Fosfat seric (mg/dL)',
    'calciu_mg_dL': 'Calciu seric total (mg/dL)',
    'fosfat_urinar_mg_dL': 'Fosfat urinar (mg/dL), probă simultană',
    'creatinina_urinara_mg_dL': 'Creatinină urinară (mg/dL), probă simultană',
    'fgf23': 'FGF23 (RU/mL pentru testul C-terminal sau pg/mL pentru testul intact)',
    'fgf23_test': 'Tipul testului FGF23: C-terminal / intact (opțional)',
    'klotho_pg_mL': 'α-Klotho solubil (pg/mL)',
    'pth_pg_mL': 'Parathormon intact (pg/mL)',
    'calcitriol_pg_mL': '1,25-dihidroxivitamina D (pg/mL)',
    'hemoglobina_g_dL': 'Hemoglobină (g/dL) — sistemul sânge',
    'feritina_ug_L': 'Feritină serică (micrograme pe litru)',
    'saturatia_transferinei_%': 'Saturația transferinei (%)',
}

def ckd_epi_2021(creat_mg_dl, age, sex):
    """Ecuația CKD-EPI 2021 (creatinină, fără coeficient rasial) [12]."""
    scr = np.asarray(creat_mg_dl, dtype=float)
    age = np.asarray(age, dtype=float)
    female = np.asarray(pd.Series(sex).astype(str).str.upper().str.startswith('F'))
    kappa = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    ratio = scr / kappa
    egfr = 142 * np.minimum(ratio, 1) ** alpha * np.maximum(ratio, 1) ** -1.200 * 0.9938 ** age
    return np.where(female, egfr * 1.012, egfr)

def ckd_stage(egfr):
    if pd.isna(egfr):
        return 'necunoscut'
    if egfr >= 90: return 'G1 (≥ 90)'
    if egfr >= 60: return 'G2 (60–89)'
    if egfr >= 45: return 'G3a (45–59)'
    if egfr >= 30: return 'G3b (30–44)'
    if egfr >= 15: return 'G4 (15–29)'
    return 'G5 (< 15)'

STAGE_ORDER = ['G1 (≥ 90)', 'G2 (60–89)', 'G3a (45–59)', 'G3b (30–44)', 'G4 (15–29)', 'G5 (< 15)', 'necunoscut']

def phosphate_handling(sp, scr, up, ucr):
    """Returnează FEPO4 (%), TRP (fracție) și TmP/GFR (mmol/L).
    sp, up = fosfat seric/urinar (mg/dL); scr, ucr = creatinină serică/urinară (mg/dL)."""
    sp = np.asarray(sp, float); scr = np.asarray(scr, float)
    up = np.asarray(up, float); ucr = np.asarray(ucr, float)
    with np.errstate(divide='ignore', invalid='ignore'):
        fe = (up * scr) / (sp * ucr)
    trp = 1 - fe
    sp_mmol = sp * MG_DL_TO_MMOL_PHOSPHATE
    with np.errstate(divide='ignore', invalid='ignore'):
        tmp = np.where(trp <= 0.86, trp * sp_mmol, 0.3 * trp / (1 - 0.8 * trp) * sp_mmol)
    return fe * 100, trp, tmp

def enrich(df, fgf23_anchor=100.0, klotho_anchor=803.1, pth_anchor=65.0):
    """Adaugă coloane calculate și indicii pentru simulator."""
    out = df.copy()
    if 'egfr' not in out or out['egfr'].isna().all():
        if {'creatinina_mg_dL', 'varsta_ani', 'sex'} <= set(out.columns):
            out['egfr'] = ckd_epi_2021(out['creatinina_mg_dL'], out['varsta_ani'], out['sex'])
    if 'egfr' in out:
        out['egfr'] = pd.to_numeric(out['egfr'], errors='coerce').round(1)
        out['stadiu_RFG'] = out['egfr'].apply(ckd_stage)
    needed = {'fosfat_mg_dL', 'creatinina_mg_dL', 'fosfat_urinar_mg_dL', 'creatinina_urinara_mg_dL'}
    if needed <= set(out.columns):
        fe, trp, tmp = phosphate_handling(out['fosfat_mg_dL'], out['creatinina_mg_dL'],
                                          out['fosfat_urinar_mg_dL'], out['creatinina_urinara_mg_dL'])
        out['FEPO4_%'] = np.round(fe, 1)
        out['TRP_%'] = np.round(trp * 100, 1)
        out['TmP_GFR_mmol_L'] = np.round(tmp, 2)
    if 'fosfat_mg_dL' in out:
        out['fosfat_mmol_L'] = (pd.to_numeric(out['fosfat_mg_dL'], errors='coerce') * MG_DL_TO_MMOL_PHOSPHATE).round(2)
    if 'fgf23' in out:
        anchor = pd.Series(fgf23_anchor, index=out.index, dtype=float)
        if 'fgf23_test' in out:
            anchor = np.where(out['fgf23_test'].astype(str).str.lower().str.startswith('intact'), INTACT_ANCHOR, C_TERMINAL_ANCHOR)
        out['FGF23_indice'] = (100 * pd.to_numeric(out['fgf23'], errors='coerce') / anchor).round(0)
    if 'klotho_pg_mL' in out:
        out['Klotho_indice'] = (100 * pd.to_numeric(out['klotho_pg_mL'], errors='coerce') / klotho_anchor).round(0)
    if 'pth_pg_mL' in out:
        out['PTH_indice'] = (100 * pd.to_numeric(out['pth_pg_mL'], errors='coerce') / pth_anchor).round(0)
    if 'feritina_ug_L' in out:
        f = pd.to_numeric(out['feritina_ug_L'], errors='coerce')
        out['status_fier'] = pd.cut(f, [-0.1, 15, 30, 100, 1e9],
                                    labels=['deficit sever (< 15)', 'deficit (15–30)',
                                            'rezerve mici (30–100)', 'suficient (≥ 100)'])
    return out

def template_csv():
    """Șablon gol cu un rând-exemplu (valori FICTIVE)."""
    row = {'id': 'P001', 'grup': 'exemplu fictiv', 'varsta_ani': 55, 'sex': 'F', 'creatinina_mg_dL': 1.6,
           'egfr': '', 'fosfat_mg_dL': 3.9, 'calciu_mg_dL': 9.2, 'fosfat_urinar_mg_dL': 45,
           'creatinina_urinara_mg_dL': 90, 'fgf23': 160, 'fgf23_test': 'C-terminal', 'klotho_pg_mL': 650, 'pth_pg_mL': 80,
           'calcitriol_pg_mL': 28, 'hemoglobina_g_dL': 12.4, 'feritina_ug_L': 38,
           'saturatia_transferinei_%': 14}
    return pd.DataFrame([row], columns=list(STANDARD_COLUMNS))

def demo_cohort(seed=2026):
    """Cohortă SINTETICĂ în unități reale, construită în jurul medianelor publicate
    (CRIC [1,2], NHANES [3,4], osteomalacie indusă de tumoră [5], hipofosfatemie legată
    de cromozomul X [6,7]). Este o simulare: NU sunt pacienți reali.
    FGF23: test C-terminal (RU/mL) pentru boala renală și control; test intact (pg/mL)
    pentru osteomalacie și hipofosfatemia legată de cromozomul X, ca în sursele citate.
    Distribuțiile fără sursă (grupul control, Klotho și parathormon în bolile osoase,
    FEPO4 țintă) sunt presupuneri didactice."""
    rng = np.random.default_rng(seed)
    def ln(median, iqr_low, iqr_high, n):
        sigma = (np.log(iqr_high) - np.log(iqr_low)) / 1.349
        return np.exp(rng.normal(np.log(median), sigma, n))
    groups = [
        # grup, n, interval creatinină, fgf23 (mediana, IQR) RU/mL, fosfat (medie, sd) mg/dL, klotho, pth, FEPO4 țintă
        ('Boală cronică renală, RFG ≥ 45', 25, (1.0, 1.5), (110, 76, 174), (3.5, .5), (780, 640, 960), (50, 35, 70), (.18, .05)),
        ('Boală cronică renală, RFG 30–44', 25, (1.5, 2.2), (154, 105, 249), (3.7, .55), (720, 590, 900), (70, 48, 100), (.27, .07)),
        ('Boală cronică renală, RFG < 30', 25, (2.3, 4.5), (256, 161, 388), (4.1, .7), (640, 520, 820), (110, 70, 170), (.40, .10)),
        ('Osteomalacie indusă de tumoră', 10, (0.6, 1.0), (546, 300, 1000), (1.7, .25), (800, 650, 980), (60, 45, 80), (.35, .08)),
        ('Hipofosfatemie legată de cromozomul X', 10, (0.5, 0.9), (180, 120, 260), (2.1, .3), (800, 650, 980), (55, 40, 75), (.30, .07)),
        ('Control (fără boală renală)', 15, (0.6, 1.0), (60, 45, 80), (3.5, .4), (850, 700, 1050), (40, 30, 52), (.10, .03)),
        ('Deficit de fier, fără boală renală', 15, (0.6, 1.0), (150, 100, 230), (3.2, .4), (830, 690, 1000), (45, 33, 60), (.14, .04)),
        ('După carboximaltoză ferică', 10, (0.6, 1.0), (260, 180, 380), (1.9, .35), (820, 680, 990), (70, 50, 95), (.28, .07)),
    ]
    rows = []
    for name, n, cr, fg, ph, kl, pt, fe in groups:
        age = rng.integers(25, 76, n)
        sex = rng.choice(['F', 'M'], n)
        creat = rng.uniform(*cr, n)
        fgf = ln(*fg, n)
        phos = np.clip(rng.normal(*ph, n), 0.9, 8)
        klo = ln(*kl, n)
        pth = ln(*pt, n)
        fe_target = np.clip(rng.normal(*fe, n), 0.03, 0.8)
        ucr = rng.uniform(60, 140, n)
        if name.startswith('Deficit de fier'):
            hb = rng.normal(11.2, 1.1, n); fer = ln(9, 5, 15, n); sat = rng.normal(9, 3, n)
        elif name.startswith('După carboximaltoză'):
            hb = rng.normal(12.6, 1.0, n); fer = ln(180, 120, 260, n); sat = rng.normal(26, 7, n)
        elif name.startswith('Boală cronică renală'):
            hb = rng.normal(11.8, 1.4, n); fer = ln(120, 70, 220, n); sat = rng.normal(20, 7, n)
        else:
            hb = rng.normal(14.0, 1.2, n); fer = ln(95, 55, 160, n); sat = rng.normal(28, 8, n)
        up = fe_target * phos * ucr / creat  # inversul formulei FEPO4
        for i in range(n):
            rows.append({'id': f'S{len(rows)+1:03d}', 'grup': name, 'varsta_ani': int(age[i]), 'sex': sex[i],
                         'creatinina_mg_dL': round(creat[i], 2), 'fosfat_mg_dL': round(phos[i], 2),
                         'calciu_mg_dL': round(rng.normal(9.3, .4), 1), 'fosfat_urinar_mg_dL': round(up[i], 1),
                         'creatinina_urinara_mg_dL': round(ucr[i], 1), 'fgf23': round(fgf[i], 1),
                         'fgf23_test': 'intact' if name.startswith(('Osteomalacie', 'Hipofosfatemie', 'După carboximaltoză')) else 'C-terminal',
                         'klotho_pg_mL': round(klo[i], 0), 'pth_pg_mL': round(pth[i], 1),
                         'hemoglobina_g_dL': round(max(6.5, hb[i]), 1), 'feritina_ug_L': round(fer[i], 1),
                         'saturatia_transferinei_%': round(max(2.0, sat[i]), 1)})
    return pd.DataFrame(rows)

def guess_mapping(columns):
    """Potrivire automată a coloanelor din fișierul încărcat cu coloanele standard
    (inclusiv nume uzuale din NHANES: LBXSCR, LBXSPH, LBXSCA, RIDAGEYR, RIAGENDR)."""
    aliases = {
        'id': ['id', 'seqn', 'pacient', 'patient'],
        'grup': ['grup', 'group', 'diagnostic', 'diagnosis'],
        'varsta_ani': ['varsta_ani', 'varsta', 'age', 'ridageyr'],
        'sex': ['sex', 'gender', 'riagendr'],
        'creatinina_mg_dL': ['creatinina_mg_dl', 'creatinine', 'lbxscr', 'scr'],
        'egfr': ['egfr', 'rfg', 'gfr'],
        'fosfat_mg_dL': ['fosfat_mg_dl', 'phosphorus', 'phosphate', 'lbxsph'],
        'calciu_mg_dL': ['calciu_mg_dl', 'calcium', 'lbxsca'],
        'fosfat_urinar_mg_dL': ['fosfat_urinar_mg_dl', 'urine_phosphate', 'urinary_phosphate'],
        'creatinina_urinara_mg_dL': ['creatinina_urinara_mg_dl', 'urine_creatinine', 'urxucr'],
        'fgf23': ['fgf23', 'fgf-23'],
        'fgf23_test': ['fgf23_test', 'assay', 'test'],
        'klotho_pg_mL': ['klotho_pg_ml', 'klotho', 'kl'],
        'pth_pg_mL': ['pth_pg_ml', 'pth', 'parathormon'],
        'calcitriol_pg_mL': ['calcitriol_pg_ml', 'calcitriol', '1,25d'],
        'hemoglobina_g_dL': ['hemoglobina_g_dl', 'hemoglobina', 'hemoglobin', 'lbxhgb', 'hgb'],
        'feritina_ug_L': ['feritina_ug_l', 'feritina', 'ferritin', 'lbxfer', 'lbdfersi'],
        'saturatia_transferinei_%': ['saturatia_transferinei_%', 'saturatia_transferinei', 'transferrin_saturation', 'lbdpct'],
    }
    lower = {c.lower(): c for c in columns}
    mapping = {}
    for std, names in aliases.items():
        for n in names:
            if n in lower:
                mapping[std] = lower[n]; break
        else:
            for c in columns:
                if any(n in c.lower() for n in names if len(n) > 3):
                    mapping[std] = c; break
    return mapping

def apply_mapping(raw, mapping):
    df = pd.DataFrame()
    for std, col in mapping.items():
        if col and col in raw.columns:
            df[std] = raw[col]
    if 'sex' in df:  # NHANES codifică 1 = bărbat, 2 = femeie
        df['sex'] = df['sex'].replace({1: 'M', 2: 'F', '1': 'M', '2': 'F', 1.0: 'M', 2.0: 'F'})
    for c in df.columns:
        if c not in ('id', 'grup', 'sex', 'fgf23_test'):
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if 'grup' not in df:
        df['grup'] = 'fără grup'
    return df
