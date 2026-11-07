"""Descarcă și unește date publice NHANES 2007–2016 pentru laboratorul FGF23–α-Klotho.

Rulează pe calculatorul tău (are nevoie de internet):
    python scripts/nhanes_klotho_download.py

Rezultat: data/nhanes_klotho_2007_2016.csv — se încarcă direct în fila „📊 Date reale”.

Fișiere folosite din fiecare ciclu (sufix E=2007–08, F=2009–10, G=2011–12, H=2013–14, I=2015–16):
  DEMO   — vârstă (RIDAGEYR), sex (RIAGENDR)
  BIOPRO — creatinină (LBXSCR), fosfor (LBXSPH), calciu (LBXSCA), în mg/dL
  ALB_CR — creatinină urinară (URXUCR) și albumină urinară
  SSKL   — α-Klotho solubil seric (pg/mL), doar adulți 40–79 de ani
  CBC    — hemoglobină (LBXHGB), pentru sistemul sânge
  FERTIN — feritină (LBXFER); FETIB — fier, capacitate de legare, saturația transferinei (LBDPCT)
Atenție: la unele cicluri, feritina și fierul au fost măsurate doar la copii mici și la femei
de anumite vârste, deci numărul de participanți cu aceste valori este mult mai mic.
Atenție: NHANES NU conține FGF23, parathormon pentru toate ciclurile sau fosfat urinar,
deci FEPO4 și TmP/GFR nu se pot calcula din aceste fișiere. Datele sunt dintr-un sondaj
cu ponderi statistice; pentru estimări la nivel de populație trebuie folosite ponderile
(WTSSKL... sau ponderile de examinare) — scriptul le păstrează dacă există.
Documentație: https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/SSKL_E.htm
"""
import io
import os
import sys
import urllib.request

import pandas as pd

CYCLES = {'E': ('2007-2008', 2007), 'F': ('2009-2010', 2009), 'G': ('2011-2012', 2011),
          'H': ('2013-2014', 2013), 'I': ('2015-2016', 2015)}
FILES = ['DEMO', 'BIOPRO', 'ALB_CR', 'SSKL', 'CBC', 'FERTIN', 'FETIB']


def fetch_xpt(name, suffix):
    years, start = CYCLES[suffix]
    urls = [
        f'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{start}/DataFiles/{name}_{suffix}.xpt',
        f'https://wwwn.cdc.gov/Nchs/Nhanes/{years}/{name}_{suffix}.XPT',
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'fgf23-klotho-lab'})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if data[:6] == b'HEADER':  # fișier SAS transport valid
                return pd.read_sas(io.BytesIO(data), format='xport')
        except Exception as exc:  # noqa: BLE001
            print(f'  nu am putut descărca {url}: {exc}')
    return None


def klotho_column(df):
    candidates = [c for c in df.columns if c != 'SEQN' and 'KL' in c.upper() and not c.upper().startswith('WT')]
    return candidates[0] if candidates else None


def main():
    frames = []
    for suffix in CYCLES:
        print(f'Ciclul {CYCLES[suffix][0]} ...')
        parts = {name: fetch_xpt(name, suffix) for name in FILES}
        if parts['SSKL'] is None or parts['DEMO'] is None:
            print('  lipsește DEMO sau SSKL, sar peste ciclu'); continue
        df = parts['SSKL']
        kcol = klotho_column(df)
        if kcol is None:
            print('  nu am găsit coloana Klotho, sar peste ciclu'); continue
        df = df.rename(columns={kcol: 'klotho_pg_mL'})
        for name in ['DEMO', 'BIOPRO', 'ALB_CR', 'CBC', 'FERTIN', 'FETIB']:
            if parts[name] is not None:
                df = df.merge(parts[name], on='SEQN', how='left')
        df['ciclu'] = CYCLES[suffix][0]
        frames.append(df)
    if not frames:
        sys.exit('Nu s-a descărcat niciun ciclu. Verifică conexiunea la internet.')
    allc = pd.concat(frames, ignore_index=True)
    keep = {'SEQN': 'id', 'ciclu': 'grup', 'RIDAGEYR': 'varsta_ani', 'RIAGENDR': 'sex',
            'LBXSCR': 'creatinina_mg_dL', 'LBXSPH': 'fosfat_mg_dL', 'LBXSCA': 'calciu_mg_dL',
            'URXUCR': 'creatinina_urinara_mg_dL', 'klotho_pg_mL': 'klotho_pg_mL',
            'LBXHGB': 'hemoglobina_g_dL', 'LBXFER': 'feritina_ug_L', 'LBDPCT': 'saturatia_transferinei_%'}
    weights = [c for c in allc.columns if c.upper().startswith('WT')]
    out = allc[[c for c in keep if c in allc.columns] + weights].rename(columns=keep)
    out['sex'] = out['sex'].map({1: 'M', 2: 'F'})
    out = out.dropna(subset=['klotho_pg_mL'])
    os.makedirs('data', exist_ok=True)
    path = os.path.join('data', 'nhanes_klotho_2007_2016.csv')
    out.to_csv(path, index=False)
    print(f'Gata: {len(out)} participanți cu Klotho salvați în {path}')


if __name__ == '__main__':
    main()
