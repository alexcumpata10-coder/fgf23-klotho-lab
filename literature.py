"""V9 — valori de referință extrase din literatură + bibliografie numerotată.

Toate valorile de mai jos sunt AGREGATE publicate (mediane, intervale intercuartilice,
criterii de includere), nu date individuale de pacient. Fiecare rând are sursa [n]
din lista BIBLIOGRAPHY. Testele de laborator diferă între ele (FGF23 intact în pg/mL
vs FGF23 C-terminal în RU/mL), deci valorile nu se compară direct între teste.
"""
import pandas as pd

# ---------------------------------------------------------------------------
# Bibliografie numerotată (folosită în toată aplicația ca [n])
# ---------------------------------------------------------------------------
BIBLIOGRAPHY = [
    (1, 'Isakova T, Wahl P, Vargas GS, Gutiérrez OM, Scialla J, Xie H, et al. Fibroblast growth factor 23 is elevated before parathyroid hormone and phosphate in chronic kidney disease. Kidney Int. 2011;79(12):1370–1378.',
     'https://doi.org/10.1038/ki.2011.47'),
    (2, 'Wolf M. FGF-23 and other emerging diagnostic markers (prezentare KDIGO Controversies Conference, CKD-MBD) — mediane FGF23 pe categorii de rată de filtrare glomerulară din cohorta CRIC.',
     'https://kdigo.org/wp-content/uploads/2017/02/5-FGF-23-and-Other-Emerging-Diagnostic-Markers-M.-Wolf.pdf'),
    (3, 'Zhang Z, Zhou X, Deng L, Jin K, Xiong X, Su X, Qiu S, Yang L. The association between serum soluble Klotho and chronic kidney disease among US adults ages 40 to 79 years: cross-sectional study. Front Public Health. 2022;10:995314.',
     'https://doi.org/10.3389/fpubh.2022.995314'),
    (4, 'Association between serum Klotho and all-cause mortality in chronic kidney disease (NHANES 2007–2016). Am J Nephrol. 55(3):273.',
     'https://karger.com/ajn/article/55/3/273/871809/Association-between-Serum-Klotho-and-All-Cause'),
    (5, 'Chong WH, et al. Tumor localization and biochemical response to cure in tumor-induced osteomalacia (31 de pacienți, NIH).',
     'https://pmc.ncbi.nlm.nih.gov/articles/PMC3900247'),
    (6, 'Kyowa Kirin. Study of KRN23 (burosumab) in adults with X-linked hypophosphatemia — criterii de includere (ClinicalTrials.gov NCT02526160).',
     'https://clinicaltrials.gov/study/NCT02526160'),
    (7, 'Self-administration of burosumab in children and adults with X-linked hypophosphataemia in two open-label, single-arm clinical studies — date suplimentare (caracteristici inițiale pediatrice). Adv Ther.',
     'https://www.springermedizin.de/resource/supplementary/12325_2022_2412_MOESM1_ESM.pdf/23974744'),
    (8, 'Kidney Disease: Improving Global Outcomes (KDIGO) CKD-MBD Update Work Group. KDIGO 2017 Clinical Practice Guideline Update for the Diagnosis, Evaluation, Prevention, and Treatment of Chronic Kidney Disease–Mineral and Bone Disorder.',
     'https://kdigo.org/guidelines/ckd-mbd/'),
    (9, 'Ruppe MD. X-Linked Hypophosphatemia. GeneReviews®. National Center for Biotechnology Information.',
     'https://www.ncbi.nlm.nih.gov/books/NBK83985/'),
    (10, 'Tumor-Induced Osteomalacia. Endotext. National Center for Biotechnology Information.',
     'https://www.ncbi.nlm.nih.gov/books/NBK279148/'),
    (11, 'Martin A, David V, Quarles LD. Regulation and function of the FGF23/klotho endocrine pathways. Physiol Rev. 2012;92(1):131–155.',
     'https://doi.org/10.1152/physrev.00002.2011'),
    (12, 'Inker LA, Eneanya ND, Coresh J, et al. New creatinine- and cystatin C–based equations to estimate GFR without race. N Engl J Med. 2021;385:1737–1749.',
     'https://doi.org/10.1056/NEJMoa2102953'),
    (13, 'Payne RB. Renal tubular reabsorption of phosphate (TmP/GFR): indications and interpretation. Ann Clin Biochem. 1998;35:201–206. (Formula folosită pentru reabsorbția tubulară maximă a fosfatului; nomograma originală: Walton RJ, Bijvoet OL. Lancet. 1975;2:309–310.)',
     'https://doi.org/10.1177/000456329803500203'),
    (14, 'Álvarez-Rivas N, Lugo-Rodríguez G, Maneiro JR, et al. Tumor-induced osteomalacia: a systematic literature review.',
     'https://doaj.org/article/edf557c5f34b434c9276d22478073b85'),
    (15, 'Sakan H, Nakatani K, Asai O, Imura A, Tanaka T, et al. Reduced renal α-Klotho expression in CKD patients and its effect on renal phosphate handling and vitamin D metabolism. PLoS One. 2014;9(1):e86301.',
     'https://pmc.ncbi.nlm.nih.gov/articles/PMC3900516'),
    (16, 'Gutiérrez O, Isakova T, Rhee E, et al. Fibroblast growth factor-23 mitigates hyperphosphatemia but accentuates calcitriol deficiency in chronic kidney disease. J Am Soc Nephrol. 2005;16(7):2205–2215.',
     'https://doi.org/10.1681/ASN.2005010052'),
    (17, 'National Center for Health Statistics. NHANES 2007–2008 — Klotho seric (SSKL_E), documentație și date.',
     'https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/SSKL_E.htm'),
    (18, 'Feldman H, Dember L. Chronic Renal Insufficiency Cohort Study (CRIC), versiunea 13 [set de date]. NIDDK Central Repository. 2024.',
     'https://doi.org/10.58020/6dxf-ed78'),
    (19, 'Gene Expression Omnibus GSE104954 — expresie genică în tubulointerstițiu, biopsii renale din boala cronică renală.',
     'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE104954'),
    (20, 'Johnson A, Bulgarelli L, Pollard T, et al. MIMIC-IV Clinical Database Demo (versiunea 2.2). PhysioNet. 2023.',
     'https://physionet.org/content/mimic-iv-demo/'),
    (21, 'Wheeler JA, Clinkenbeard EL. Regulation of fibroblast growth factor 23 by iron, EPO, and HIF. Curr Mol Biol Rep. 2019;5(1):8–17.',
     'https://doi.org/10.1007/s40610-019-0110-9'),
    (22, 'Edmonston D, Wolf M. FGF23 at the crossroads of phosphate, iron economy and erythropoiesis. Nat Rev Nephrol. 2020;16(1):7–19.',
     'https://doi.org/10.1038/s41581-019-0189-5'),
    (23, 'National Center for Health Statistics. NHANES — parathormon seric (fișierul PTH_D). Variabila LBXPT21, numai ciclurile 2003–2006.',
     'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles/PTH_D.htm'),
    (24, 'National Center for Health Statistics. NHANES — fișierele de aport nutrițional total (DR1TOT). Variabila DR1TPHOS, aportul de fosfor în miligrame pe zi.',
     'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DR1TOT_J.htm'),
    (25, 'Wolf M, Chertow GM, Macdougall IC, Kaper R, Krop J, Strauss W. Randomized trial of intravenous iron-induced hypophosphatemia. JCI Insight. 2018;3(23):e124486.',
     'https://doi.org/10.1172/jci.insight.124486'),
    (26, 'Wolf M, Koch TA, Bregman DB. Effects of iron deficiency anemia and its treatment on fibroblast growth factor 23 and phosphate homeostasis in women. J Bone Miner Res. 2013;28(8):1793–803.',
     'https://doi.org/10.1002/jbmr.1923'),
    (27, 'Farrow EG, Yu X, Summers LJ, et al. Iron deficiency drives an autosomal dominant hypophosphatemic rickets (ADHR) phenotype in fibroblast growth factor-23 (Fgf23) knock-in mice. Proc Natl Acad Sci U S A. 2011;108(46):E1146–55.',
     'https://doi.org/10.1073/pnas.1110905108'),
    (28, 'David V, Martin A, Isakova T, et al. Inflammation and functional iron deficiency regulate fibroblast growth factor 23 production. Kidney Int. 2016;89(1):135–46.',
     'https://doi.org/10.1038/ki.2015.290'),
    (29, 'National Center for Health Statistics. NHANES — feritină (fișierele FERTIN) și fier, capacitate totală de legare, saturația transferinei (fișierele FETIB). Variabilele LBXFER, LBXIRN, LBXTIB, LBDPCT.',
     'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2007/DataFiles/FERTIN_E.htm'),
]

def cite(*nums):
    return '[' + ', '.join(str(n) for n in nums) + ']'

# ---------------------------------------------------------------------------
# Cohorta CRIC — FGF23 C-terminal (RU/mL) pe categorii de rată estimată
# de filtrare glomerulară; fosfat seric mediu (mg/dL). Sursa [1, 2].
# ---------------------------------------------------------------------------
CRIC_FGF23 = pd.DataFrame([
    {'categorie_RFG': '≥ 45', 'n': 1649, 'FGF23_mediana_RU_mL': 110, 'IQR_jos': 76, 'IQR_sus': 174, 'fosfat_mg_dL': 3.5},
    {'categorie_RFG': '30–44', 'n': 1472, 'FGF23_mediana_RU_mL': 154, 'IQR_jos': 105, 'IQR_sus': 249, 'fosfat_mg_dL': 3.7},
    {'categorie_RFG': '< 30', 'n': 752, 'FGF23_mediana_RU_mL': 256, 'IQR_jos': 161, 'IQR_sus': 388, 'fosfat_mg_dL': 4.1},
    {'categorie_RFG': 'Toată cohorta', 'n': 3879, 'FGF23_mediana_RU_mL': 145, 'IQR_jos': 96, 'IQR_sus': 239, 'fosfat_mg_dL': 3.7},
])

# ---------------------------------------------------------------------------
# Tabel general de referință (agregate publicate)
# ---------------------------------------------------------------------------
REFERENCE_ROWS = [
    # grup, parametru, valoare, unitate, test / observații, sursă
    ('Boală cronică renală (CRIC, stadiile 2–4)', 'FGF23 C-terminal — mediana (IQR)', '145 (96–239)', 'RU/mL', 'Immutopics, a doua generație; 72% au ≥ 100 RU/mL', cite(1, 2)),
    ('Boală cronică renală (CRIC)', 'Prag „exces FGF23”', '≥ 100', 'RU/mL', 'definiție folosită în CRIC', cite(1)),
    ('Boală cronică renală (CRIC)', 'Prag hiperparatiroidism secundar', '≥ 65', 'pg/mL (parathormon)', 'definiție folosită în CRIC', cite(1)),
    ('Boală cronică renală (CRIC)', 'Prag hiperfosfatemie', '≥ 4,6', 'mg/dL (≈ 1,49 mmol/L)', 'definiție folosită în CRIC', cite(1)),
    ('Populație generală 40–79 ani (NHANES 2007–2016)', 'Klotho solubil seric — mediana', '803,1', 'pg/mL', 'ELISA IBL; n = 13.589', cite(3)),
    ('Boală cronică renală (NHANES 2007–2016)', 'Klotho solubil seric — mediana (IQR)', '760 (624–958)', 'pg/mL', 'ELISA IBL', cite(4)),
    ('Donatori sănătoși (validarea testului NHANES)', 'Klotho solubil — interval', '285,8–1.638,6 (medie 698)', 'pg/mL', '114 probe', cite(4)),
    ('Osteomalacie indusă de tumoră (NIH, n = 31)', 'FGF23 intact — mediana (interval)', '546,4 (76–2.742)', 'pg/mL', 'referință laborator 10–50 pg/mL', cite(5)),
    ('Osteomalacie indusă de tumoră (NIH, n = 31)', 'Fosfor seric — mediana', '1,69', 'mg/dL (≈ 0,55 mmol/L)', 'referință 2,5–4,8 mg/dL', cite(5)),
    ('Osteomalacie indusă de tumoră (recenzie sistematică)', 'Hipofosfatemie / FGF23 crescut la diagnostic', '99,8% / 95,5%', 'din pacienți', 'serii de cazuri publicate', cite(14)),
    ('Hipofosfatemie legată de cromozomul X — adulți (criterii studiu clinic)', 'FGF23 intact', '> 30', 'pg/mL', 'test Kainos', cite(6)),
    ('Hipofosfatemie legată de cromozomul X — adulți (criterii studiu clinic)', 'Fosfor seric și reabsorbția tubulară maximă', '< 2,5 / < 2,5', 'mg/dL', 'pe nemâncate', cite(6)),
    ('Hipofosfatemie legată de cromozomul X — copii (n = 20)', 'FGF23 intact — medie ± deviație standard', '182,6 ± 67,3', 'pg/mL', 'valori inițiale, înainte de tratament', cite(7)),
    ('Hipofosfatemie legată de cromozomul X — copii (n = 20)', 'Reabsorbția tubulară maximă a fosfatului', '2,3 ± 0,5', 'mg/dL', 'valori inițiale', cite(7)),
    ('Hipofosfatemie legată de cromozomul X — copii (n = 20)', '1,25-dihidroxivitamina D', '29,3 ± 17,3', 'pg/mL', 'valori inițiale', cite(7)),
    ('Anemie feriprivă tratată cu carboximaltoză ferică (studiu randomizat, n = 1.000)', 'Hipofosfatemie sub 2,0 mg/dL', '50,8%', 'din pacienți', 'față de 0,9% cu ferumoxitol; hipofosfatemie sub 1,3 mg/dL la 10,0%', cite(25)),
    ('Aceeași sursă', 'Hipofosfatemie persistentă la 5 săptămâni', '29,1%', 'din pacienți', 'niciun pacient tratat cu ferumoxitol', cite(25)),
    ('Aceeași sursă', 'Creșterea FGF23 biologic activ', '+302,8 ± 326,2%', 'față de valoarea inițială, la 2 săptămâni', 'ferumoxitol: +10,1 ± 61,0%', cite(25)),
    ('Rahitism hipofosfatemic autozomal dominant', 'Fier seric scăzut ↔ FGF23 C-terminal crescut', 'corelație negativă', '—', 'observată și la martori sănătoși; FGF23 intact crește numai la purtătorii mutației', cite(21, 27)),
    ('Mecanism general', 'Deficitul de fier, inflamația și eritropoieza', 'cresc simultan producția și clivarea', '—', 'de aceea hormonul biologic activ se modifică puțin, dar testul C-terminal crește mult', cite(22, 28)),
    ('Boală cronică renală (biopsii, n = 236)', 'Expresia renală α-Klotho', 'scade odată cu stadiul', '—', 'asociată cu creșterea FGF23 seric', cite(15)),
]
REFERENCE = pd.DataFrame(REFERENCE_ROWS, columns=['grup', 'parametru', 'valoare', 'unitate', 'test / observații', 'sursă'])

# ---------------------------------------------------------------------------
# Calibrare orientativă indice ↔ unitate reală
# Indicele 100 = pragul ales (modificabil în aplicație). Alegerea pragului este
# o convenție didactică, nu o echivalență validată.
# ---------------------------------------------------------------------------
DEFAULT_ANCHORS = {
    'Feritină (micrograme pe litru)': 100.0,
    'FGF23 C-terminal (RU/mL)': 100.0,   # prag „exces FGF23” în CRIC [1]
    'FGF23 intact (pg/mL)': 50.0,        # limita superioară a intervalului de referință NIH [5]
    'Klotho solubil (pg/mL)': 803.1,     # mediana NHANES [3]
    'Parathormon (pg/mL)': 65.0,         # prag hiperparatiroidism secundar CRIC [1]
}

def to_index(value, anchor):
    return 100.0 * float(value) / float(anchor)

def from_index(index, anchor):
    return float(index) * float(anchor) / 100.0
