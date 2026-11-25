"""V11 — logica momentelor interactive din fila „Cu publicul”.

Deosebirea față de chestionarul cu 18 întrebări: aici răspunsul NU este scris
dinainte. Este calculat din model în momentul prezentării, prin aceleași ecuații
care produc toate graficele. Deci publicul poate cere orice variantă, inclusiv
una la care nu te-ai gândit, iar modelul răspunde.

Modulul nu importă streamlit: conține numai logică, deci poate fi testat
separat de interfață.

Cele patru moduri:
  1. duel  — sala prezice direcția, modelul dezvăluie răspunsul
  2. panel — diagnostic ascuns, publicul votează dintre scenarii
  3. tinta — provocare: atinge o stare fiziologică mișcând cursoarele
  4. test  — cinci întrebări înainte și aceleași cinci după, cu diferența de scor
"""

import physiology as ph

# --------------------------------------------------------------------------
# Markerii pe care sala poate prezice o direcție

MARKERI = {
    'fosfat_mg_dL': ('Fosfat seric', 'mg/dL', 2),
    'TmP_GFR_mmol_L': ('Pragul de reabsorbție (TmP/GFR)', 'mmol/L', 2),
    'FGF23_intact_pg_mL': ('FGF23 intact (hormonul activ)', 'pg/mL', 0),
    'FGF23_C_terminal_RU_mL': ('FGF23 C-terminal (hormon + fragmente)', 'RU/mL', 0),
    'PTH_pg_mL': ('Parathormon', 'pg/mL', 0),
    'calcitriol_pmol_L': ('Calcitriol', 'pmol/L', 0),
    'FEPO4_%': ('Fracția de excreție a fosfatului', '%', 1),
}

# Sub acest prag relativ, schimbarea se declară „rămâne aproape neschimbat”.
# 5% este sub rezoluția unui buletin de analize, deci diferența nu ar fi
# observabilă clinic.
PRAG_NESCHIMBAT = 0.05


def _stare(scenariu, modificari=None):
    """Starea de echilibru pentru un scenariu, cu modificări opționale."""
    baza = dict(ph.SCENARII[scenariu])
    if modificari:
        baza.update(modificari)
    return ph.stare_de_echilibru(ph.Parametri(**baza))


def ruleaza_duel(scenariu, modificari, marker):
    """Calculează răspunsul la o predicție, din model.

    Întoarce valoarea de dinainte, cea de după, direcția și schimbarea
    relativă. Direcția este una din: 'crește', 'scade', 'rămâne'.
    """
    inainte = _stare(scenariu)[marker]
    dupa = _stare(scenariu, modificari)[marker]
    baza = abs(inainte) if abs(inainte) > 1e-9 else 1e-9
    relativ = (dupa - inainte) / baza
    if abs(relativ) < PRAG_NESCHIMBAT:
        direcitie = 'rămâne'
    elif relativ > 0:
        direcitie = 'crește'
    else:
        direcitie = 'scade'
    return {
        'marker': marker,
        'nume': MARKERI[marker][0],
        'unitate': MARKERI[marker][1],
        'zecimale': MARKERI[marker][2],
        'inainte': inainte,
        'dupa': dupa,
        'relativ': relativ,
        'directie': direcitie,
    }


# --------------------------------------------------------------------------
# Modul 1 — dueluri pregătite
#
# 'lectia' se afișează DUPĂ dezvăluire. Nu conține răspunsul, ca să poată fi
# citită cu voce tare fără să strice surpriza celor care n-au votat încă.

DUELURI = [
    {
        'id': 'feritina',
        'titlu': 'Scad feritina de la 100 la 8 micrograme pe litru',
        'intrebare': 'Ce se întâmplă cu fosfatul seric?',
        'scenariu': 'Adult sănătos',
        'modificari': {'feritina': 8.0},
        'marker': 'fosfat_mg_dL',
        'lectia': ('Fosfatul se mișcă puțin și rămâne în intervalul de referință, deși testul '
                   'C-terminal aproape se triplează — comparați cu duelul următor. Deficitul de fier '
                   'crește simultan producția și clivarea, deci se acumulează mai ales fragmente '
                   'inactive. Pentru hipofosfatemie adevărată trebuie ca și clivarea să fie blocată.'),
        'cine': 'persoana 1',
        'nota_model': ('În model, hormonul activ crește cu aproximativ jumătate la această scădere '
                       'de feritină, mai mult decât arată literatura, unde testul intact se mișcă '
                       'foarte puțin. Declarați acest lucru: este o limită a modelului, nu un '
                       'rezultat.'),
    },
    {
        'id': 'feritina_c_terminal',
        'titlu': 'Aceeași scădere de feritină, dar urmărim testul C-terminal',
        'intrebare': 'Ce se întâmplă cu FGF23 C-terminal?',
        'scenariu': 'Adult sănătos',
        'modificari': {'feritina': 8.0},
        'marker': 'FGF23_C_terminal_RU_mL',
        'lectia': ('Acesta este motivul pentru care există două teste de laborator. '
                   'Același pacient, în același moment: un test se mișcă mult, celălalt aproape '
                   'deloc. Dacă le compari între ele, interpretezi greșit.'),
        'cine': 'persoana 1',
    },
    {
        'id': 'clivare',
        'titlu': 'Blochez clivarea hormonului: de la 1,00 la 0,20',
        'intrebare': 'Ce se întâmplă cu fosfatul seric?',
        'scenariu': 'Adult sănătos',
        'modificari': {'clivare_fgf23': 0.20},
        'marker': 'fosfat_mg_dL',
        'lectia': ('Clivarea este foarfeca moleculară. Blocată, rămâne mai mult hormon activ, '
                   'pragul de reabsorbție scade și rinichiul pierde fosfat. Așa apare criza din '
                   'rahitismul autozomal dominant și efectul carboximaltozei ferice.'),
        'cine': 'persoana 1',
    },
    {
        'id': 'klotho',
        'titlu': 'Scad α-Klotho de la 803 la 200 picograme pe mililitru',
        'intrebare': 'Ce se întâmplă cu pragul de reabsorbție?',
        'scenariu': 'Adult sănătos',
        'modificari': {'klotho': 200.0},
        'marker': 'TmP_GFR_mmol_L',
        'lectia': ('Aici intuiția înșală pe aproape toată lumea. Mai puțin coreceptor nu '
                   'înseamnă că rinichiul pierde fosfat — înseamnă că nu mai aude ordinul de '
                   'a-l elimina. Hormonul strigă mai tare, iar organul aude mai slab.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'compensare',
        'titlu': 'Iau 65 la sută din nefroni: filtrarea de la 100 la 35',
        'intrebare': 'Ce se întâmplă cu fosfatul seric?',
        'scenariu': 'Adult sănătos',
        'modificari': {'rfg': 35.0},
        'marker': 'fosfat_mg_dL',
        'lectia': ('Compensarea. Am luat două treimi din nefroni, iar fosfatemia a urcat doar cu '
                   'câteva procente și a rămas în intervalul de referință. Fracția de excreție, în '
                   'schimb, s-a dublat: nefronii rămași lucrează mult mai intens. De aceea o analiză '
                   'normală nu exclude boala, și de aceea FGF23 a fost propus ca marker precoce.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'decompensare',
        'titlu': 'Continui: filtrarea de la 35 la 12',
        'intrebare': 'Ce se întâmplă cu fosfatul seric?',
        'scenariu': 'Boală cronică renală G3b',
        'modificari': {'rfg': 12.0},
        'marker': 'fosfat_mg_dL',
        'lectia': ('Compensarea cedează. Nu treptat — brusc, pe ultima porțiune de funcție '
                   'renală. Capacitatea totală de excreție este pragul înmulțit cu filtrarea, '
                   'iar filtrarea a devenit factorul limitant.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'fractia_renala',
        'titlu': 'Același pacient cu boală renală avansată',
        'intrebare': 'Fracția de excreție a fosfatului este mai mare sau mai mică decât la omul sănătos?',
        'scenariu': 'Adult sănătos',
        'modificari': {'rfg': 12.0, 'klotho': 430.0, 'feritina': 55.0, 'clivare_fgf23': 0.55},
        'marker': 'FEPO4_%',
        'lectia': ('Rinichiul bolnav elimină procentual mult mai mult din ce filtrează — și tot '
                   'reține fosfat, pentru că filtrează de opt ori mai puțin. Procentul crescut nu '
                   'înseamnă că rinichiul funcționează bine; înseamnă că fiecare nefron rămas '
                   'lucrează la capacitate maximă.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'aport',
        'titlu': 'Reduc aportul alimentar de fosfor de la 1200 la 350 mg pe zi',
        'intrebare': 'Ce se întâmplă cu fracția de excreție a fosfatului?',
        'scenariu': 'Adult sănătos',
        'modificari': {'aport_fosfat_mg': 350.0},
        'marker': 'FEPO4_%',
        'lectia': ('Contra-exemplul proiectului. Fosfatul poate fi mic fără ca rinichiul să fie '
                   'vinovat: aici el conservă corect, și fracția de excreție o dovedește. Acesta este '
                   'testul care separă hipofosfatemia renală de cea extrarenală.'),
        'cine': 'persoana 3',
    },
    {
        'id': 'tumora',
        'titlu': 'O tumoră secretă hormon: FGF23 intact impus la 546 pg/mL, rinichi sănătos',
        'intrebare': 'Ce se întâmplă cu fosfatul seric?',
        'scenariu': 'Adult sănătos',
        'modificari': {'fgf23_fix': 546.0},
        'marker': 'fosfat_mg_dL',
        'lectia': ('Hormon mult, rinichi sănătos, deci pierdere masivă. Comparați cu boala renală '
                   'în stadiul 5, unde hormonul este tot crescut și fosfatul este mare: diferența o '
                   'face capacitatea de excreție, nu hormonul.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'tubul',
        'titlu': 'Nefronii sunt acolo, dar tubul proximal nu mai lucrează: integritate 1,00 la 0,35',
        'intrebare': 'Ce se întâmplă cu pragul de reabsorbție?',
        'scenariu': 'Adult sănătos',
        'modificari': {'integritate_tubulara': 0.35},
        'marker': 'TmP_GFR_mmol_L',
        'lectia': ('Pierderea renală de fosfat nu cere nici hormon crescut, nici nefroni pierduți. '
                   'Un tub proximal bolnav este suficient — și de aceea pragul de reabsorbție nu este '
                   'un test pentru FGF23, este un test pentru funcția tubulară.'),
        'cine': 'persoana 2',
    },
    {
        'id': 'calcitriol',
        'titlu': 'Boală renală în stadiul 5, față de omul sănătos',
        'intrebare': 'Ce se întâmplă cu calcitriolul?',
        'scenariu': 'Adult sănătos',
        'modificari': {'rfg': 12.0, 'klotho': 430.0, 'feritina': 55.0, 'clivare_fgf23': 0.55},
        'marker': 'calcitriol_pmol_L',
        'lectia': ('Lovitura dublă: hormonul oprește enzima care activează vitamina D și pornește '
                   'enzima care o degradează. De aici pleacă brațul calcitriol–calciu, spre intestin '
                   'și paratiroide.'),
        'cine': 'persoana 3',
    },
]


def duel(id_duel):
    """Un duel după identificator, cu răspunsul calculat din model."""
    for d in DUELURI:
        if d['id'] == id_duel:
            rezultat = ruleaza_duel(d['scenariu'], d['modificari'], d['marker'])
            return {**d, 'rezultat': rezultat}
    raise KeyError(id_duel)


def duel_liber(scenariu, modificari, marker):
    """Un duel improvizat, pentru o întrebare venită din sală."""
    return ruleaza_duel(scenariu, modificari, marker)


def scor_sala(voturi, directie_reala):
    """Procentul sălii care a nimerit direcția.

    'voturi' este un dicționar direcție → număr de mâini ridicate.
    """
    total = sum(voturi.values())
    if total <= 0:
        return None
    return 100.0 * voturi.get(directie_reala, 0) / total


# --------------------------------------------------------------------------
# Modul 2 — diagnosticul ascuns
#
# Panelul este calculat din model, deci nu există o listă de valori scrise de
# mână care s-ar putea desincroniza de ecuații.

PANEL_MARKERI = ['fosfat_mg_dL', 'TmP_GFR_mmol_L', 'FGF23_intact_pg_mL',
                 'FGF23_C_terminal_RU_mL', 'PTH_pg_mL', 'FEPO4_%']

LECTII_SCENARII = {
    'Adult sănătos': 'Punctul de pornire: pragul stă peste fosfatemie, deci rinichiul nu pierde.',
    'Boală cronică renală G3b': 'Fosfatemia este încă normală, deși hormonii s-au mișcat deja — compensarea.',
    'Boală cronică renală G5': 'Compensarea a cedat: fosfat mare și fracție de excreție foarte mare.',
    'Hipofosfatemie legată de cromozomul X': 'Hormon mult, rinichi sănătos, deci pierdere masivă.',
    'Osteomalacie indusă de tumoră': 'Forma extremă a aceluiași mecanism: pragul se prăbușește.',
    'Deficit funcțional de α-Klotho': 'Fără coreceptor, același hormon face mai puțin — rezistența renală.',
    'Rahitism hipofosfatemic autozomal dominant, criză cu deficit de fier':
        'Genă plus mediu: mutația singură nu ajunge, trebuie și deficitul de fier.',
    'După perfuzie cu carboximaltoză ferică': 'Un medicament poate reproduce o boală genetică.',
    'Aport alimentar foarte redus': 'Hipofosfatemie fără pierdere renală — fracția de excreție este mică.',
}


def panel_orb(scenariu):
    """Panelul de laborator al unui scenariu, fără numele diagnosticului."""
    stare = _stare(scenariu)
    randuri = []
    for m in PANEL_MARKERI:
        nume, unitate, zecimale = MARKERI[m]
        randuri.append({'marker': nume, 'valoare': round(float(stare[m]), zecimale),
                        'unitate': unitate})
    rfg = ph.SCENARII[scenariu].get('rfg', ph.Parametri().rfg)
    randuri.append({'marker': 'Rata de filtrare glomerulară', 'valoare': round(float(rfg)),
                    'unitate': 'mL/min/1,73 m²'})
    return {'panel': randuri, 'raspuns': scenariu,
            'lectia': LECTII_SCENARII.get(scenariu, '')}


def variante_diagnostic(corect, n=4, ordine=None):
    """Variante de răspuns pentru diagnosticul ascuns, cu cea corectă inclusă.

    'ordine' permite reproductibilitatea: la prezentare vrei aceleași variante
    de fiecare dată, nu o selecție nouă la fiecare reîncărcare a paginii.
    """
    toate = list(ph.SCENARII)
    celelalte = [s for s in toate if s != corect]
    if ordine is not None:
        celelalte = [celelalte[i % len(celelalte)] for i in ordine]
        vazute, unice = set(), []
        for s in celelalte:
            if s not in vazute:
                vazute.add(s)
                unice.append(s)
        celelalte = unice
    alese = celelalte[:max(0, n - 1)]
    rezultat = sorted(alese + [corect])
    return rezultat


# --------------------------------------------------------------------------
# Modul 3 — provocarea: atinge ținta
#
# Fiecare țintă este o stare fiziologică de atins mișcând cursoarele. Sala
# strigă ce cursor să miști. Verificarea se face pe starea de echilibru, nu pe
# valorile de intrare, deci nu se poate trișa.

TINTE = [
    {
        'id': 'hipo_nerenal',
        'titlu': 'Fosfat în scădere, cu rinichi nevinovat',
        'cerinta': ('Coboară fosfatul sub 3,45 mg/dL aducând fracția de excreție sub 5 la sută, '
                    'cu pragul de reabsorbție păstrat peste 0,85 mmol/L.'),
        'verifica': lambda s: s['fosfat_mg_dL'] < 3.45 and s['TmP_GFR_mmol_L'] > 0.85 and s['FEPO4_%'] < 5.0,
        'indiciu': 'Nu atinge niciun cursor hormonal. Gândește-te de unde intră fosfatul în organism.',
        'soluitie': 'Aportul alimentar de fosfor, coborât sub aproximativ 500 mg pe zi.',
        'lectia': ('Ați produs un fosfat în scădere fără nicio pierdere renală: pragul a rămas sus, '
                   'iar fracția de excreție a căzut la câteva procente, fiindcă rinichiul conservă '
                   'corect. Comparați cu ținta „pierdere renală fără hormon crescut”, unde fosfatul '
                   'scade mult mai mult și pragul se prăbușește. Același simptom, cauze opuse.'),
    },
    {
        'id': 'doua_teste',
        'titlu': 'Fă cele două teste să se contrazică',
        'cerinta': ('Adu FGF23 C-terminal peste 200 RU/mL, menținând FGF23 intact sub '
                    '60 pg/mL.'),
        'verifica': lambda s: s['FGF23_C_terminal_RU_mL'] > 200.0 and s['FGF23_intact_pg_mL'] < 60.0,
        'indiciu': 'Ai nevoie de ceva care crește producția fără să blocheze foarfeca moleculară.',
        'soluitie': 'Feritina coborâtă la 10 micrograme pe litru sau mai jos, cu clivarea lăsată normală.',
        'lectia': ('Acesta este cel mai bun argument pentru de ce nu se compară valori între cele '
                   'două teste: același pacient poate avea un test mult crescut și celălalt normal.'),
    },
    {
        'id': 'pierdere_tubulara',
        'titlu': 'Pierdere renală fără hormon crescut',
        'cerinta': ('Coboară pragul de reabsorbție sub 0,55 mmol/L, păstrând FGF23 intact '
                    'sub 60 pg/mL și filtrarea peste 85.'),
        'verifica': lambda s: s['TmP_GFR_mmol_L'] < 0.55 and s['FGF23_intact_pg_mL'] < 60.0,
        'indiciu': 'Nefronii pot fi toți la locul lor și totuși tubul să nu lucreze.',
        'soluitie': 'Integritatea tubulară, coborâtă mult.',
        'lectia': ('Pragul de reabsorbție nu este un test pentru FGF23. Este un test pentru funcția '
                   'tubulară, iar cauzele pot fi cu totul altele — de exemplu un sindrom Fanconi.'),
    },
    {
        'id': 'rezistenta',
        'titlu': 'Rezistență renală la propriul hormon',
        'cerinta': ('Adu fosfatul peste 3,85 mg/dL fără să cobori filtrarea sub 75.'),
        'verifica': lambda s: s['fosfat_mg_dL'] > 3.85,
        'indiciu': 'Rinichiul poate avea toți nefronii și totuși să nu audă mesajul.',
        'soluitie': 'α-Klotho, coborâtă mult, eventual împreună cu o filtrare ușor redusă.',
        'lectia': ('Fără coreceptor, același hormon face mai puțin. Fosfatul urcă nu pentru că '
                   'rinichiul e distrus, ci pentru că a devenit surd la ordinul de a elimina.'),
    },
]


def verifica_tinta(id_tinta, parametri):
    """Verifică dacă starea de echilibru a parametrilor curenți atinge ținta."""
    tinta = next((t for t in TINTE if t['id'] == id_tinta), None)
    if tinta is None:
        raise KeyError(id_tinta)
    stare = ph.stare_de_echilibru(ph.Parametri(**parametri))
    # Constrângerile pe parametrii de intrare se verifică separat de cele pe stare.
    conditii_intrare = True
    if id_tinta == 'pierdere_tubulara':
        conditii_intrare = float(parametri.get('rfg', 100)) > 85
    if id_tinta == 'rezistenta':
        conditii_intrare = float(parametri.get('rfg', 100)) >= 75
    atins = bool(tinta['verifica'](stare)) and conditii_intrare
    return {'atins': atins, 'tinta': tinta, 'stare': stare}


# --------------------------------------------------------------------------
# Modul 4 — testul înainte și după
#
# Aceleași cinci întrebări la începutul și la sfârșitul prezentării. Diferența
# de scor este un rezultat măsurat, care se poate pune în lucrarea scrisă.

TEST_PRE_POST = [
    ('Ce rol are α-Klotho în semnalizarea FGF23 în rinichi?',
     ['Este receptorul propriu-zis al hormonului',
      'Este coreceptor: formează un complex cu receptorul și crește afinitatea',
      'Este transportorul care duce fosfatul în celulă',
      'Este enzima care activează vitamina D'], 1),
    ('FGF23 acționează asupra reabsorbției renale a fosfatului în principal prin:',
     ['Creșterea filtrării glomerulare',
      'Scăderea transportorilor de fosfat din tubul proximal, deci coborârea pragului',
      'Blocarea directă a parathormonului',
      'Creșterea absorbției intestinale'], 1),
    ('Un pacient are FGF23 mult crescut și fosfat scăzut; altul are FGF23 mult crescut și fosfat crescut. Ce explică diferența?',
     ['Hormonul are efecte opuse la concentrații diferite',
      'Capacitatea totală de excreție, adică pragul înmulțit cu filtrarea glomerulară',
      'Numai aportul alimentar de fosfor',
      'Diferența este o eroare de laborator'], 1),
    ('De ce poate fi fosfatemia normală într-o boală cronică renală moderată?',
     ['Pentru că FGF23 lipsește în stadiile moderate',
      'Pentru că nefronii rămași cresc fracția de excreție și compensează',
      'Pentru că fosfatul nu se mai filtrează',
      'Pentru că intestinul oprește complet absorbția'], 1),
    ('Care formulare este corectă despre FGF23 și hipertrofia ventriculară stângă la om?',
     ['FGF23 crescut provoacă hipertrofie ventriculară',
      'FGF23 crescut se asociază cu hipertrofia ventriculară; mecanismele propuse sunt studiate',
      'Hipertrofia ventriculară este cauza creșterii FGF23',
      'Nu există nicio legătură descrisă'], 1),
]


def scor_test(raspunsuri):
    """Numărul de răspunsuri corecte dintr-o listă de indici (None = fără răspuns)."""
    return sum(1 for i, r in enumerate(raspunsuri)
               if r is not None and r == TEST_PRE_POST[i][2])


# --------------------------------------------------------------------------
# Parametrii pe care interfața îi poate modifica într-un duel improvizat.
# Formatul: cheie → (eticheta, minim, maxim, pas)

PARAMETRI_UI = {
    'rfg': ('Rata de filtrare glomerulară (mL/min/1,73 m²)', 5.0, 130.0, 1.0),
    'klotho': ('α-Klotho (pg/mL)', 100.0, 1600.0, 10.0),
    'feritina': ('Feritină (µg/L)', 3.0, 400.0, 1.0),
    'clivare_fgf23': ('Clivarea FGF23 (1 = normală)', 0.10, 1.20, 0.02),
    'integritate_tubulara': ('Integritate tubulară (1 = normală)', 0.30, 1.20, 0.02),
    'aport_fosfat_mg': ('Aport alimentar de fosfor (mg/zi)', 200.0, 2500.0, 50.0),
    'fgf23_fix': ('FGF23 intact impus (pg/mL)', 5.0, 1500.0, 5.0),
}

DIRECTII = ['crește', 'scade', 'rămâne']
