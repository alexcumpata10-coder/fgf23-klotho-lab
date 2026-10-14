"""Synthetic teaching cohort. Values are not clinical measurements or validated predictions."""
import numpy as np
import pandas as pd

GROUPS = [
    ('Sănătos (scenariu)', 10),
    ('BRC moderată (scenariu)', 10),
    ('BRC avansată (scenariu)', 10),
    ('Hiperaldosteronism (scenariu)', 10),
    ('Consum cronic de alcool (scenariu)', 10),
]

def generate_cohort(seed=2026):
    rng = np.random.default_rng(seed)
    rows = []
    for group, count in GROUPS:
        for _ in range(count):
            age = int(rng.integers(25, 75))
            sex = str(rng.choice(['F', 'M']))
            if group.startswith('Sănătos'):
                egfr = rng.uniform(90, 120); fgf = rng.normal(100, 12); klotho = rng.normal(100, 9); pth = rng.normal(100, 12)
                phosphate = rng.normal(1.10, .10); ca = rng.normal(2.34,.07); mg = rng.normal(.85,.07); k = rng.normal(4.2,.3)
            elif group.startswith('BRC moderată'):
                egfr = rng.uniform(30, 59); fgf = rng.normal(190, 32); klotho = rng.normal(70, 10); pth = rng.normal(145, 24)
                phosphate = rng.normal(1.20,.13); ca = rng.normal(2.28,.08); mg = rng.normal(.91,.09); k = rng.normal(4.5,.35)
            elif group.startswith('BRC avansată'):
                egfr = rng.uniform(10, 29); fgf = rng.normal(300, 45); klotho = rng.normal(45, 9); pth = rng.normal(220, 32)
                phosphate = rng.normal(1.60,.22); ca = rng.normal(2.20,.11); mg = rng.normal(1.00,.12); k = rng.normal(4.9,.48)
            elif group.startswith('Hiperaldosteronism'):
                egfr = rng.uniform(65, 115); fgf = rng.normal(105, 18); klotho = rng.normal(95, 12); pth = rng.normal(125, 20)
                phosphate = rng.normal(1.05,.12); ca = rng.normal(2.34,.09); mg = rng.normal(.77,.09); k = rng.normal(3.2,.35)
            else:
                egfr = rng.uniform(65, 115); fgf = rng.normal(105, 18); klotho = rng.normal(95, 12); pth = rng.normal(115, 23)
                phosphate = rng.normal(.85,.18); ca = rng.normal(2.25,.11); mg = rng.normal(.68,.11); k = rng.normal(3.6,.42)
            fgf = float(np.clip(fgf,20,400)); klotho = float(np.clip(klotho,10,150)); pth=float(np.clip(pth,20,300))
            # Teaching-only index, not serum calcitriol measurement.
            calcitriol_index = float(np.clip(100*(.25+.75*egfr/100)/(.65+.35*(fgf/100)*(klotho/100)),10,180))
            rows.append({
                'id_virtual':f'V{len(rows)+1:03d}', 'grup':group, 'varsta_ani':age, 'sex':sex,
                'egfr_ml_min_1_73m2':round(egfr,1), 'fosfat_mmol_L_simulat':round(max(.35,phosphate),2),
                'calciu_total_mmol_L_simulat':round(max(1.7,ca),2),
                'magneziu_mmol_L_simulat':round(max(.35,mg),2), 'potasiu_mmol_L_simulat':round(max(2.2,k),2),
                'FGF23_indice':round(fgf,1), 'alpha_Klotho_indice':round(klotho,1),
                'PTH_indice':round(pth,1), 'calcitriol_indice':round(calcitriol_index,1),
            })
    return pd.DataFrame(rows)
