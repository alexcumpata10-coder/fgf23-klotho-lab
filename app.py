import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_import as di
import physiology as ph
from literature import BIBLIOGRAPHY, CRIC_FGF23, REFERENCE, DEFAULT_ANCHORS, cite
from organ_schemes import SCHEMES, diagram

st.set_page_config(page_title='FGF23–α-Klotho | Laborator multiorgan', page_icon='🧬', layout='wide')
st.title('🧬 FGF23–α-Klotho — Laborator virtual multiorgan')
st.caption('Versiunea 10 • os ↔ rinichi ↔ intestin ↔ paratiroide ↔ cord ↔ sânge • model în unități reale, cu validare pe date publicate')
st.warning('Model educațional. Cazurile din simulator sunt construite, nu sunt pacienți reali, iar parametrii cinetici nu sunt măsurați la om — vezi fila „🎯 Validare”. Nu se folosește pentru diagnostic, tratament sau decizii privind pacienți reali.')


@st.cache_data(show_spinner=False)
def ruleaza(parametri_dict, zile):
    return ph.simuleaza(ph.Parametri(**parametri_dict), zile=zile)


@st.cache_data(show_spinner=False)
def echilibru(parametri_dict, zile=240):
    return ph.stare_de_echilibru(ph.Parametri(**parametri_dict), zile=zile)


@st.cache_data(show_spinner=False)
def validare():
    return ph.ruleaza_validarea()


@st.cache_data(show_spinner=False)
def ordine():
    return ph.ordinea_aparitiei()


@st.cache_data(show_spinner=False)
def banda(parametri_dict, n, zile):
    return ph.monte_carlo(ph.Parametri(**parametri_dict), n=n, zile=zile)


CHEI = ['rfg', 'fgf23_fix', 'klotho', 'feritina', 'clivare_fgf23', 'integritate_tubulara', 'aport_fosfat_mg']


def incarca_scenariu():
    baza = ph.SCENARII[st.session_state['scenariu']]
    implicit = ph.Parametri()
    intregi = {'rfg', 'klotho', 'feritina', 'aport_fosfat_mg'}
    for cheie in CHEI:
        valoare = baza.get(cheie, getattr(implicit, cheie))
        if cheie in intregi and valoare is not None:
            valoare = int(round(float(valoare)))
        elif cheie != 'fgf23_fix' and valoare is not None:
            valoare = float(valoare)
        st.session_state['p_' + cheie] = valoare
    st.session_state['fgf_liber'] = baza.get('fgf23_fix') is None
    st.session_state.pop('p_fgf23_fix_slider', None)
    st.session_state.pop('pacient_incarcat', None)


if 'p_rfg' not in st.session_state:
    st.session_state.setdefault('scenariu', list(ph.SCENARII)[0])
    incarca_scenariu()

st.sidebar.header('Pacient virtual')
nume_scenariu = st.sidebar.selectbox('Scenariu clinic', list(ph.SCENARII), key='scenariu',
                                     on_change=incarca_scenariu)
if st.session_state.get('pacient_incarcat'):
    st.sidebar.success('Parametri din date reale: ' + st.session_state['pacient_incarcat'])

st.sidebar.caption('Toți parametrii sunt în unități reale. Modifică-i pentru a testa o ipoteză.')
rfg = st.sidebar.slider('Rata de filtrare glomerulară (mL/min/1,73 m²)', 5, 130, step=1, key='p_rfg')
klotho = st.sidebar.slider('α-Klotho (pg/mL)', 100, 1600, step=10, key='p_klotho')
st.sidebar.caption(f'Mediana în populația generală: {DEFAULT_ANCHORS["Klotho solubil (pg/mL)"]:.0f} pg/mL ' + cite(3))

fgf_liber = st.sidebar.checkbox('FGF23 reglat de model (bucla fiziologică)', key='fgf_liber')
if fgf_liber:
    fgf23_fix = None
    st.sidebar.caption('FGF23 se calculează din fosfat, calcitriol, fier și funcția renală.')
else:
    fgf23_fix = st.sidebar.slider('FGF23 intact impus (pg/mL)', 5, 1500, step=5,
                                  value=int(st.session_state.get('p_fgf23_fix') or 200),
                                  key='p_fgf23_fix_slider')
st.sidebar.markdown('**🩸 Sistemul sânge și fier**')
feritina = st.sidebar.slider('Feritină (micrograme pe litru)', 3, 400, step=1, key='p_feritina')
clivare = st.sidebar.slider('Clivarea FGF23 (1 = normală)', 0.10, 1.20, step=0.02, key='p_clivare_fgf23')
st.sidebar.caption('Sub 1 = clivare deficitară, deci mai mult hormon activ: mutația din rahitismul autozomal dominant, carboximaltoza ferică, boala renală ' + cite(21, 22, 25))
st.sidebar.markdown('**Alți parametri**')
tubul = st.sidebar.slider('Integritate tubulară (1 = normală)', 0.30, 1.20, step=0.02, key='p_integritate_tubulara')
aport = st.sidebar.slider('Aport alimentar de fosfor (mg/zi)', 200, 2500, step=50, key='p_aport_fosfat_mg')
st.sidebar.caption('Se poate calibra pe variabila DR1TPHOS din NHANES ' + cite(24))
zile = st.sidebar.slider('Durata simulării (zile)', 20, 365, 120, 10)

PARAMETRI = dict(rfg=float(rfg), klotho=float(klotho), feritina=float(feritina),
                 clivare_fgf23=float(clivare), integritate_tubulara=float(tubul),
                 aport_fosfat_mg=float(aport),
                 fgf23_fix=None if fgf_liber else float(fgf23_fix))
df = ruleaza(PARAMETRI, zile)
final = df.iloc[-1]

QUESTIONS = [
 ('🟢 Nivel 1 — Atenție la prezentare','Care este sursa principală a FGF23 circulant?', ['Osteocitele și osteoblastele','Celulele beta pancreatice','Cortexul suprarenal','Hepatocitele'],0,'FGF23 este produs predominant de osteocite și osteoblaste din țesutul osos.'),
 ('🟢 Nivel 1 — Atenție la prezentare','Care este rolul clasic al α-Klotho membranar în rinichi?', ['Este transportor direct de fosfat','Este coreceptor pentru semnalizarea FGF23 prin FGFR','Este enzima care sintetizează PTH','Este canal de potasiu'],1,'α-Klotho formează cu FGFR un complex care permite semnalizarea clasică a FGF23.'),
 ('🟢 Nivel 1 — Atenție la prezentare','Ce efect are, în mod obișnuit, FGF23 asupra reabsorbției renale a fosfatului?', ['O crește','Nu o influențează','O reduce','Blochează filtrarea glomerulară'],2,'FGF23 reduce expresia/abundența transportorilor NaPi-IIa și NaPi-IIc din tubul proximal, favorizând fosfaturia.'),
 ('🟢 Nivel 1 — Atenție la prezentare','Ce efect are FGF23 asupra calcitriolului?', ['Îl crește obligatoriu','Îi reduce sinteza și favorizează degradarea','Îl transformă direct în PTH','Nu are nicio legătură'],1,'FGF23 inhibă CYP27B1 și stimulează CYP24A1, reducând în general 1,25(OH)₂D.'),
 ('🟢 Nivel 1 — Atenție la prezentare','În ce organ se află principalul loc de acțiune pentru fosfaturia indusă de FGF23?', ['Cord','Rinichi','Ficat','Splină'],1,'Rinichiul, în special tubul proximal, modifică reabsorbția fosfatului ca răspuns la semnalizarea FGF23.'),
 ('🟡 Nivel 2 — Aplicare clinică','În XLH, care este mecanismul central al hipofosfatemiei?', ['Exces de aldosteron','FGF23 inadecvat crescut/activ și pierdere renală de fosfat','Creșterea izolată a aportului alimentar','Blocarea filtrării glomerulare'],1,'Alterarea PHEX favorizează excesul de activitate FGF23, cu fosfaturie inadecvată și calcitriol inadecvat de mic.'),
 ('🟡 Nivel 2 — Aplicare clinică','Care dintre următoarele poate cauza osteomalacie indusă de tumori (TIO)?', ['O tumoră mezenchimală care secretă FGF23','O tumoră care secretă exclusiv insulină','Hipersecreția de ADH','Lipsa aldosteronului'],0,'Unele tumori mezenchimale secretă FGF23, provocând pierdere renală de fosfat și defect de mineralizare.'),
 ('🟡 Nivel 2 — Aplicare clinică','De ce poate fi fosfatemia încă normală în BCR moderată?', ['FGF23 este întotdeauna absent','Nefronii rămași cresc excreția fracțională de fosfat','Fosfatul nu se filtrează','Intestinul nu mai absoarbe deloc fosfat'],1,'Creșterea FGF23 și PTH poate favoriza eliminarea fosfatului pe nefronii rămași, compensând temporar scăderea masei nefronice.'),
 ('🟡 Nivel 2 — Aplicare clinică','Care asociere este tipică în BCR avansată cu CKD-MBD?', ['FGF23 crescut, calcitriol scăzut, PTH adesea crescut','FGF23 absent, calcitriol mereu crescut','PTH obligatoriu suprimat','α-Klotho obligatoriu crescut'],0,'În BCR avansată apar frecvent FGF23 crescut, deficit de calcitriol și hiperparatiroidism secundar; există variabilitate individuală.'),
 ('🟡 Nivel 2 — Aplicare clinică','Ce afirmăm corect despre hiperaldosteronismul primar în proiect?', ['Produce întotdeauna deficit de α-Klotho','FGF23 confirmă diagnosticul de Conn','Este un caz exploratoriu de interacțiuni endocrine indirecte','Cauzează obligatoriu XLH'],2,'Legătura RAAS–FGF23–Klotho este de interes științific, dar nu definește un profil diagnostic universal în hiperaldosteronism.'),
 ('🔴 Nivel 3 — Raționament avansat','De ce FGF23 crescut poate coexista cu hipofosfatemie în XLH, dar cu hiperfosfatemie în BCR G5?', ['FGF23 are întotdeauna efecte opuse asupra aceluiași receptor','În BCR G5 capacitatea totală de excreție este limitată de pierderea nefronilor','XLH determină oprirea completă a filtrării','FGF23 nu acționează în XLH'],1,'În XLH rinichiul poate elimina inadecvat fosfatul sub acțiunea FGF23; în BCR G5 masa nefronică este prea redusă pentru a elimina suficient fosfat, chiar dacă FGF23 este mare.'),
 ('🔴 Nivel 3 — Raționament avansat','Un pacient are hipofosfatemie și FEPO₄ inadecvat de mare. Care interpretare este cea mai bună?', ['Rinichiul conservă adecvat fosfatul','Există sugestie de pierdere renală de fosfat, de investigat în context','Diagnosticul de XLH este cert','Bilanțul corporal total este obligatoriu negativ în acel moment'],1,'Fosfaturia inadecvată în hipofosfatemie sugerează pierdere renală; etiologia cere evaluare clinică și, după caz, TmP/GFR și alte analize.'),
 ('🔴 Nivel 3 — Raționament avansat','Ce consecință este plauzibilă dacă disponibilitatea renală a α-Klotho membranar scade?', ['Crește obligatoriu răspunsul clasic la FGF23','Poate scădea sensibilitatea la FGF23, în funcție de context','FGF23 se transformă în PTH','Dispare absorbția intestinală a fosfatului'],1,'α-Klotho este coreceptor pentru semnalizarea clasică FGF23; reducerea sa poate limita răspunsul, dar efectul clinic depinde de nefroni și alte reglaje.'),
 ('🔴 Nivel 3 — Raționament avansat','Care afirmație despre FGF23 și cord este formulată riguros?', ['FGF23 crescut dovedește că pacientul are hipertrofie ventriculară','Asocierea FGF23 cu hipertrofia ventriculară există; cauzalitatea și mecanismele depind de context','Cordul exprimă obligatoriu același complex renal α-Klotho–FGFR','FGF23 nu poate avea niciun efect extra-renal'],1,'Au fost descrise asocieri și mecanisme propuse, inclusiv unele independente de α-Klotho; nu trebuie transformată asocierea într-o predicție individuală.'),
 ('🔴 Nivel 3 — Raționament avansat','Un cercetător vrea să demonstreze că reducerea α-Klotho provoacă direct creșterea FGF23 la om. Ce abordare este cea mai solidă?', ['Să compare două grafice arbitrare din simulator','Să măsoare doar FGF23 la un singur pacient','Să folosească un protocol validat, să controleze eGFR, fosfatul, PTH și vitamina D și să evite concluziile cauzale din simple asocieri','Să presupună că orice corelație dovedește cauzalitatea'],2,'Un studiu clinic necesită design adecvat, măsurători validate, controlul confuzorilor și analiză statistică. Simulatorul nu produce dovezi clinice.'),
 ('🩸 Nivel 3 — Sânge și fier','De ce deficitul de fier crește mult testul C-terminal al FGF23, dar aproape deloc testul intact?', ['Pentru că testul C-terminal este mai sensibil tehnic','Pentru că deficitul de fier crește simultan transcrierea și clivarea hormonului','Pentru că fierul se leagă direct de anticorpul testului','Pentru că hormonul intact nu există la anemici'],1,'Deficitul de fier, inflamația și eritropoieza cresc în paralel producția și clivarea FGF23, deci se acumulează fragmente C-terminale, în timp ce hormonul biologic activ se schimbă puțin.'),
 ('🩸 Nivel 3 — Sânge și fier','Ce explică criza de hipofosfatemie din rahitismul hipofosfatemic autozomal dominant?', ['Un aport alimentar excesiv de fosfat','Mutația blochează clivarea hormonului, iar deficitul de fier îi crește producția','Insuficiența renală acută','Lipsa completă de α-Klotho'],1,'Fenotipul apare la întâlnirea dintre o mutație care împiedică clivarea și o stare de deficit de fier, de exemplu la menstruație sau după sarcină. Este un exemplu clasic de interacțiune între genă și mediu.'),
 ('🩸 Nivel 3 — Sânge și fier','Un pacient primește carboximaltoză ferică pentru anemie feriprivă și dezvoltă hipofosfatemie. Care este mecanismul cel mai probabil?', ['Fierul se leagă chimic de fosfat în intestin','Preparatul reduce clivarea FGF23, deci crește hormonul biologic activ și scade pragul de reabsorbție','Perfuzia distruge nefronii','Fierul stimulează direct paratiroidele'],1,'Într-un studiu randomizat, carboximaltoza ferică a crescut hormonul activ cu aproximativ 300 la sută și a produs hipofosfatemie sub 2,0 mg/dL la 50,8 la sută dintre pacienți, față de 0,9 la sută cu ferumoxitol.'),
]

tabs = st.tabs(['🩺 Caz clinic', '🦴 Organe și mecanisme', '🩸 Sânge și fier', '🔬 Pierdere renală',
                '👥 Comparație cazuri', '📊 Date reale', '🎯 Validare', '🎤 Cu publicul',
                '📚 Metodologie', '📖 Bibliografie'])

# ---------------------------------------------------------------- 0. Caz clinic
with tabs[0]:
    st.subheader(nume_scenariu)
    st.info(ph.DESCRIERI.get(nume_scenariu, ''))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Fosfat seric', f"{final.fosfat_mmol_L:.2f} mmol/L", f"{final.fosfat_mg_dL:.2f} mg/dL",
              delta_color='off')
    c2.metric('TmP/GFR', f"{final.TmP_GFR_mmol_L:.2f} mmol/L")
    c3.metric('FGF23 intact', f"{final.FGF23_intact_pg_mL:.0f} pg/mL")
    c4.metric('FGF23 C-terminal', f"{final.FGF23_C_terminal_RU_mL:.0f} RU/mL")
    c5.metric('Parathormon', f"{final.PTH_pg_mL:.0f} pg/mL")
    d1, d2, d3 = st.columns(3)
    d1.metric('Calcitriol', f"{final.calcitriol_pmol_L:.0f} pmol/L")
    d2.metric('Fracția de excreție a fosfatului', f"{final['FEPO4_%']:.1f} %")
    d3.metric('Mineralizare osoasă', f"{final.mineralizare_mmol_zi:.1f} mmol/zi")

    mesaje = []
    if final.fosfat_mg_dL < 2.5:
        mesaje.append('Hipofosfatemie (sub 2,5 mg/dL).')
    if final.fosfat_mg_dL >= 4.6:
        mesaje.append('Hiperfosfatemie după criteriul folosit în cohorta CRIC ' + cite(1) + '.')
    if final.TmP_GFR_mmol_L < 0.81:
        mesaje.append('Prag de reabsorbție sub 0,81 mmol/L: pierdere renală de fosfat ' + cite(6) + '.')
    if final.PTH_pg_mL >= 65:
        mesaje.append('Parathormon peste pragul de hiperparatiroidism secundar ' + cite(1) + '.')
    if final.FGF23_C_terminal_RU_mL >= 100:
        mesaje.append('FGF23 C-terminal peste pragul de 100 RU/mL ' + cite(1) + '.')
    if final.mineralizare_mmol_zi < 0.5 * ph.Parametri().mineralizare_max:
        mesaje.append('Mineralizare osoasă sub jumătate din capacitate: context de osteomalacie.')
    if mesaje:
        st.warning('  \n'.join('• ' + m for m in mesaje))
    else:
        st.success('Toți indicatorii se află în intervalele folosite ca referință în acest model.')

    st.markdown('#### Evoluția în timp')
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        fig.add_scatter(x=df.zi, y=df.fosfat_mmol_L, name='Fosfat seric', line=dict(width=3))
        fig.add_scatter(x=df.zi, y=df.TmP_GFR_mmol_L, name='TmP/GFR (prag)', line=dict(dash='dash'))
        fig.add_hrect(y0=0.81, y1=1.45, fillcolor='green', opacity=0.07, line_width=0,
                      annotation_text='interval de referință')
        fig.update_layout(title='1. Fosfat seric și pragul de reabsorbție tubulară',
                          xaxis_title='Zile', yaxis_title='mmol/L')
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig2 = go.Figure()
        fig2.add_scatter(x=df.zi, y=df.FGF23_intact_pg_mL, name='FGF23 intact (pg/mL)')
        fig2.add_scatter(x=df.zi, y=df.FGF23_C_terminal_RU_mL, name='FGF23 C-terminal (RU/mL)')
        fig2.add_scatter(x=df.zi, y=df.PTH_pg_mL, name='Parathormon (pg/mL)')
        fig2.add_scatter(x=df.zi, y=df.calcitriol_pmol_L, name='Calcitriol (pmol/L)')
        fig2.update_layout(title='2. Hormonii, în unitățile lor reale', xaxis_title='Zile',
                           yaxis_title='concentrație', yaxis_type='log')
        st.plotly_chart(fig2, use_container_width=True)
    st.caption('Cele două teste FGF23 se citesc pe axe diferite ca semnificație: testul intact măsoară hormonul activ, cel C-terminal îl măsoară împreună cu fragmentele ' + cite(22) + '.')

    g3, g4 = st.columns(2)
    with g3:
        fluxuri = df[['zi', 'absorbit_mmol_zi', 'excretat_mmol_zi', 'mineralizare_mmol_zi']].melt(
            id_vars='zi', var_name='flux', value_name='mmol/zi')
        st.plotly_chart(px.line(fluxuri, x='zi', y='mmol/zi', color='flux',
                                title='3. Fluxurile de fosfat (intestin, rinichi, os)'),
                        use_container_width=True)
    with g4:
        grila = list(range(10, 131, 5))
        sens = []
        for g in grila:
            e = echilibru({**PARAMETRI, 'rfg': float(g)})
            sens.append({'RFG': g, 'fosfat_mg_dL': e['fosfat_mg_dL'], 'TmP_GFR': e['TmP_GFR_mmol_L']})
        sens = pd.DataFrame(sens)
        figs = go.Figure()
        figs.add_scatter(x=sens.RFG, y=sens.fosfat_mg_dL, name='Fosfat la echilibru (mg/dL)')
        figs.add_hline(y=4.6, line_dash='dot', annotation_text='prag hiperfosfatemie 4,6 ' + cite(1))
        figs.add_hline(y=2.5, line_dash='dot', annotation_text='prag hipofosfatemie 2,5')
        figs.add_vline(x=rfg, line_color='crimson', annotation_text='pacientul curent')
        figs.update_layout(title='4. Sensibilitate: funcția renală vs fosfatemia de echilibru',
                           xaxis_title='Rata de filtrare glomerulară', yaxis_title='mg/dL')
        st.plotly_chart(figs, use_container_width=True)

    st.markdown('#### 5. Pacientul virtual față de cohorta reală CRIC ' + cite(1, 2))
    cric = CRIC_FGF23.copy()
    figc = go.Figure()
    figc.add_bar(x=cric['categorie_RFG'], y=cric['FGF23_mediana_RU_mL'], name='CRIC: mediana',
                 error_y=dict(type='data', symmetric=False,
                              array=cric['IQR_sus'] - cric['FGF23_mediana_RU_mL'],
                              arrayminus=cric['FGF23_mediana_RU_mL'] - cric['IQR_jos']))
    figc.add_hline(y=final.FGF23_C_terminal_RU_mL, line_dash='dash', line_color='crimson',
                   annotation_text=f'pacientul virtual: {final.FGF23_C_terminal_RU_mL:.0f} RU/mL')
    figc.add_hline(y=100, line_dash='dot', line_color='gray', annotation_text='prag 100 RU/mL',
                   annotation_position='bottom right')
    figc.update_layout(title='FGF23 C-terminal pe categorii de filtrare glomerulară (bare = interval intercuartilic)',
                       yaxis_title='RU/mL', xaxis_title='Rata de filtrare glomerulară')
    st.plotly_chart(figc, use_container_width=True)
    banda_rfg = '< 30' if rfg < 30 else ('30–44' if rfg < 45 else '≥ 45')
    rand = cric[cric.categorie_RFG == banda_rfg].iloc[0]
    verdict = 'sub' if final.FGF23_C_terminal_RU_mL < rand.IQR_jos else (
        'peste' if final.FGF23_C_terminal_RU_mL > rand.IQR_sus else 'în')
    st.write(f'Pentru filtrarea {rfg} (categoria {banda_rfg}), mediana reală este **{rand.FGF23_mediana_RU_mL} RU/mL** '
             f'(interval {rand.IQR_jos}–{rand.IQR_sus}). Pacientul virtual este **{verdict}** acest interval.')
    if rfg >= 60:
        st.info('Cohorta CRIC a inclus pacienți cu boală cronică renală, în principal cu filtrare între 20 și 70; pentru valori normale comparația este doar orientativă.')

    export = df.copy()
    for k, v in PARAMETRI.items():
        export['parametru_' + k] = v
    export['versiune'] = 'V10'
    st.download_button('⬇️ Descarcă simularea (CSV, cu toți parametrii de intrare)',
                       export.to_csv(index=False).encode('utf-8-sig'),
                       'simulare_fgf23_klotho_v10.csv', 'text/csv')

# ---------------------------------------------------------------- 1. Organe
with tabs[1]:
    st.subheader('Atlas interactiv: o schemă pentru fiecare sistem')
    st.caption('Liniile punctate marchează mecanisme propuse sau asocieri, nu relații clinice demonstrate.')
    organ = st.selectbox('Alege sistemul', list(SCHEMES.keys()))
    st.markdown('#### ' + SCHEMES[organ][0])
    st.graphviz_chart(diagram(organ), use_container_width=True)
    descrieri = {
        '🦴 Os': 'Osteocitele produc FGF23. Excesul poate cauza hipofosfatemie și mineralizare deficitară în hipofosfatemia legată de cromozomul X și în osteomalacia indusă de tumoră. Parathormonul persistent crescut accelerează resorbția prin RANKL. ' + cite(9, 10, 11),
        '🫘 Rinichi': 'Complexul FGF23 cu receptorul și α-Klotho reduce transportorii NaPi-IIa și NaPi-IIc în tubul proximal, scade CYP27B1 și stimulează CYP24A1. În boala cronică renală scad și masa nefronică, și expresia de α-Klotho. ' + cite(11, 15),
        '🥬 Intestin': 'Calcitriolul stimulează absorbția calciului și a fosfatului. FGF23 reduce calcitriolul, deci influențează indirect intestinul. Aportul alimentar se poate măsura ' + cite(24) + '.',
        '🟣 Paratiroide': 'Scăderea calcitriolului și modificările calciului favorizează hiperparatiroidismul secundar în boala renală. Relația directă dintre FGF23 și paratiroide depinde de context. ' + cite(1, 8),
        '❤️ Cord': 'FGF23 crescut se asociază cu hipertrofia ventriculară stângă și cu riscul cardiovascular în boala renală. Asocierea nu dovedește cauzalitatea la om. ' + cite(8),
        '🩸 Sânge și fier': 'Deficitul de fier, inflamația și eritropoietina cresc simultan transcrierea și clivarea FGF23, astfel că hormonul activ se modifică puțin, dar testul C-terminal crește mult. Când clivarea este blocată — mutația din rahitismul autozomal dominant sau carboximaltoza ferică — crește și hormonul activ, deci apare hipofosfatemia. ' + cite(21, 22, 25, 27),
        '🟠 Suprarenale': 'Hiperaldosteronismul primar produce hipertensiune, retenție de sodiu și uneori hipokaliemie. Relația cu FGF23 și α-Klotho este indirectă și exploratorie.',
    }
    st.info(descrieri.get(organ, ''))

# ---------------------------------------------------------------- 2. Sânge și fier
with tabs[2]:
    st.subheader('🩸 Fierul, eritropoieza și cele două fețe ale FGF23')
    st.markdown('Acesta este al șaptelea sistem al proiectului, adăugat în versiunea 10. Mecanismul explică o problemă practică: '
                '**de ce testul C-terminal și testul intact dau rezultate atât de diferite la același pacient** ' + cite(22) + '.')
    st.markdown('Deficitul de fier crește transcrierea genei FGF23, dar crește și clivarea hormonului, deci hormonul biologic '
                'activ se modifică puțin. Când clivarea este blocată — mutația din rahitismul hipofosfatemic autozomal dominant, '
                'sau după carboximaltoză ferică — crește și hormonul activ, iar fosfatemia scade ' + cite(21, 27) + '.')

    e1, e2 = st.columns(2)
    with e1:
        fer_exp = st.slider('Feritină în experiment (micrograme pe litru)', 3, 300, 100, 1)
    with e2:
        cliv_exp = st.slider('Clivarea FGF23 în experiment', 0.10, 1.20, 1.00, 0.02)
    p_exp = {**PARAMETRI, 'feritina': float(fer_exp), 'clivare_fgf23': float(cliv_exp), 'fgf23_fix': None}
    e = echilibru(p_exp)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('FGF23 intact', f"{e['FGF23_intact_pg_mL']:.0f} pg/mL")
    k2.metric('FGF23 C-terminal', f"{e['FGF23_C_terminal_RU_mL']:.0f} RU/mL")
    k3.metric('Raport C-terminal / intact', f"{e['FGF23_C_terminal_RU_mL'] / max(e['FGF23_intact_pg_mL'], 1):.1f}")
    k4.metric('Fosfat seric', f"{e['fosfat_mg_dL']:.2f} mg/dL")

    st.markdown('**Experimentul care arată mecanismul:** deplasează feritina spre valori mici cu clivarea la 1,00. '
                'Testul C-terminal crește mult, testul intact aproape deloc, iar fosfatemia rămâne stabilă. '
                'Apoi coboară clivarea sub 0,4 — abia atunci apare hipofosfatemia. Aceasta este diferența dintre '
                'un deficit de fier obișnuit și o criză de rahitism autozomal dominant.')

    grila_fer = [3, 8, 15, 25, 40, 60, 90, 130, 180, 250, 300]
    randuri_fer = []
    for f in grila_fer:
        for cl, et in [(1.0, 'clivare normală (1,00)'), (0.35, 'clivare blocată (0,35)')]:
            ee = echilibru({**PARAMETRI, 'feritina': float(f), 'clivare_fgf23': cl, 'fgf23_fix': None})
            randuri_fer.append({'feritina': f, 'situatie': et,
                                'FGF23 intact (pg/mL)': ee['FGF23_intact_pg_mL'],
                                'FGF23 C-terminal (RU/mL)': ee['FGF23_C_terminal_RU_mL'],
                                'fosfat (mg/dL)': ee['fosfat_mg_dL']})
    tf = pd.DataFrame(randuri_fer)
    f1, f2 = st.columns(2)
    with f1:
        lung = tf.melt(id_vars=['feritina', 'situatie'],
                       value_vars=['FGF23 intact (pg/mL)', 'FGF23 C-terminal (RU/mL)'],
                       var_name='test', value_name='valoare')
        st.plotly_chart(px.line(lung, x='feritina', y='valoare', color='test', line_dash='situatie',
                                log_y=True, markers=True,
                                title='6. Feritina și cele două teste FGF23',
                                labels={'feritina': 'Feritină (micrograme pe litru)'}),
                        use_container_width=True)
    with f2:
        figf = px.line(tf, x='feritina', y='fosfat (mg/dL)', color='situatie', markers=True,
                       title='7. Feritina și fosfatemia',
                       labels={'feritina': 'Feritină (micrograme pe litru)'})
        figf.add_hline(y=2.5, line_dash='dot', annotation_text='prag hipofosfatemie 2,5 mg/dL')
        figf.add_hline(y=2.0, line_dash='dot', line_color='crimson',
                       annotation_text='pragul folosit în studiul cu carboximaltoză ' + cite(25))
        st.plotly_chart(figf, use_container_width=True)

    st.markdown('#### Ce spun datele clinice')
    st.dataframe(REFERENCE[REFERENCE['sursă'].str.contains('21|22|25|27|28')],
                 hide_index=True, use_container_width=True)
    st.caption('Într-un studiu randomizat pe aproape 2.000 de pacienți cu anemie feriprivă, carboximaltoza ferică a produs '
               'hipofosfatemie sub 2,0 mg/dL la 50,8 la sută dintre pacienți, față de 0,9 la sută cu ferumoxitol, prin creșterea '
               'hormonului biologic activ ' + cite(25) + '. Este cea mai clară dovadă clinică a legăturii dintre fier și axa FGF23.')

# ---------------------------------------------------------------- 3. Pierdere renală
with tabs[3]:
    st.subheader('Fosfaturie inadecvată: cum se demonstrează')
    st.write('În hipofosfatemie, rinichiul sănătos ar trebui să conserve fosfatul. Pragul de reabsorbție tubulară '
             'este marker-ul standard: sub 0,81 mmol/L, în context de hipofosfatemie, sugerează pierdere renală ' + cite(6, 13) + '.')
    a, b = st.columns(2)
    with a:
        fosfat_ip = st.slider('Fosfat seric măsurat (mmol/L)', 0.20, 2.00, 0.55, 0.05)
        rfg_ip = st.slider('Filtrare glomerulară în experiment', 15, 130, 95, 5)
    with b:
        trp_ip = st.slider('Reabsorbție tubulară a fosfatului (%)', 20, 99, 65)
        aport_ip = st.slider('Aport absorbit (mmol/zi)', 5.0, 40.0, 20.0, 0.5)
    trp = trp_ip / 100
    fepo = 100 - trp_ip
    tmp = (trp * fosfat_ip) if trp <= 0.86 else (0.3 * trp / (1 - 0.8 * trp) * fosfat_ip)
    excretat = max(0.0, fosfat_ip - tmp) * rfg_ip * 1.44
    x1, x2, x3, x4 = st.columns(4)
    x1.metric('Fracția de excreție', f'{fepo}%')
    x2.metric('TmP/GFR', f'{tmp:.2f} mmol/L')
    x3.metric('Excreție', f'{excretat:.1f} mmol/zi')
    x4.metric('Bilanț', f'{aport_ip - excretat:+.1f} mmol/zi')
    st.plotly_chart(px.bar(pd.DataFrame({'Flux': ['Absorbit', 'Excretat'], 'mmol/zi': [aport_ip, excretat]}),
                           x='Flux', y='mmol/zi', title='8. Fluxurile de fosfat în scenariu'),
                    use_container_width=True)
    if fosfat_ip < 0.81 and tmp < 0.81:
        st.warning('Fosfatemie mică împreună cu prag de reabsorbție mic: tipar de pierdere renală de fosfat. Nu este un diagnostic.')
    elif fosfat_ip < 0.81:
        st.info('Fosfatemie mică, dar pragul de reabsorbție este păstrat: caută cauze extrarenale (aport, redistribuire).')
    st.caption('Formula TmP/GFR cere probe simultane de sânge și urină, pe nemâncate, și nu este validă la filtrare glomerulară foarte scăzută ' + cite(13) + '.')

# ---------------------------------------------------------------- 4. Comparație
with tabs[4]:
    st.subheader('Comparație între scenarii, în unități reale')
    randuri_cmp = []
    for nume in ph.SCENARII:
        p = ph.SCENARII[nume]
        implicit = ph.Parametri()
        d = {c: p.get(c, getattr(implicit, c)) for c in CHEI}
        e = echilibru(d)
        randuri_cmp.append({
            'scenariu': nume,
            'RFG': d['rfg'],
            'fosfat_mg_dL': round(e['fosfat_mg_dL'], 2),
            'TmP_GFR_mmol_L': round(e['TmP_GFR_mmol_L'], 2),
            'FGF23_intact_pg_mL': round(e['FGF23_intact_pg_mL'], 0),
            'FGF23_C_terminal_RU_mL': round(e['FGF23_C_terminal_RU_mL'], 0),
            'PTH_pg_mL': round(e['PTH_pg_mL'], 0),
            'calcitriol_pmol_L': round(e['calcitriol_pmol_L'], 0),
            'FEPO4_%': round(e['FEPO4_%'], 1),
            'feritina': d['feritina'],
            'clivare': d['clivare_fgf23'],
        })
    cmp = pd.DataFrame(randuri_cmp)
    st.dataframe(cmp, hide_index=True, use_container_width=True)
    y = st.selectbox('Compară', ['fosfat_mg_dL', 'TmP_GFR_mmol_L', 'FGF23_intact_pg_mL',
                                 'FGF23_C_terminal_RU_mL', 'PTH_pg_mL', 'calcitriol_pmol_L', 'FEPO4_%'])
    st.plotly_chart(px.bar(cmp.sort_values(y), x='scenariu', y=y, color='scenariu',
                           title='9. Comparația scenariilor').update_layout(showlegend=False),
                    use_container_width=True)
    st.plotly_chart(px.scatter(cmp, x='TmP_GFR_mmol_L', y='fosfat_mg_dL', color='scenariu',
                               size='FGF23_intact_pg_mL', size_max=40,
                               title='10. Pragul de reabsorbție explică fosfatemia în toate scenariile',
                               labels={'TmP_GFR_mmol_L': 'TmP/GFR (mmol/L)', 'fosfat_mg_dL': 'Fosfat (mg/dL)'}),
                    use_container_width=True)
    st.info('Graficul 10 este mesajul central al proiectului: aproape toată variația fosfatemiei dintre boli se explică prin '
            'pragul de reabsorbție tubulară, iar pragul este controlat de FGF23, de α-Klotho și de parathormon.')
    st.download_button('⬇️ Descarcă comparația (CSV)', cmp.to_csv(index=False).encode('utf-8-sig'),
                       'comparatie_scenarii_v10.csv', 'text/csv')

# ---------------------------------------------------------------- 5. Date reale
with tabs[5]:
    st.subheader('📊 Date reale: valori publicate și datele tale')
    st.markdown('#### A. Valori de referință din literatură')
    st.dataframe(REFERENCE, hide_index=True, use_container_width=True)
    st.download_button('⬇️ Descarcă tabelul de referință (CSV)',
                       REFERENCE.to_csv(index=False).encode('utf-8-sig'),
                       'valori_referinta_literatura_v10.csv', 'text/csv')
    st.info('Testele FGF23 nu sunt interschimbabile: testul C-terminal (RU/mL) măsoară molecula întreagă și fragmentele, '
            'testul intact (pg/mL) doar hormonul activ ' + cite(22) + '.')

    st.markdown('#### B. Încarcă date individuale')
    src = st.radio('Sursa datelor', ['Cohortă demonstrativă sintetică (construită din medianele publicate)',
                                     'Încarc fișierul meu CSV'])
    st.download_button('⬇️ Descarcă șablonul CSV gol', di.template_csv().to_csv(index=False).encode('utf-8-sig'),
                       'sablon_date_fgf23_klotho_v10.csv', 'text/csv')
    raw = None
    if src.startswith('Cohortă'):
        raw = di.demo_cohort()
        st.warning('Cohortă SINTETICĂ: valorile sunt generate în jurul medianelor din ' + cite(1, 2, 3, 4, 5, 6, 7, 25) +
                   '. Nu sunt pacienți reali.')
    else:
        up = st.file_uploader('Fișier CSV', type=['csv'])
        if up is not None:
            try:
                raw = pd.read_csv(up, sep=None, engine='python')
            except Exception as exc:
                st.error(f'Nu am putut citi fișierul: {exc}')
        st.caption('Pentru NHANES rulează pe calculator `python scripts/nhanes_klotho_download.py`, apoi încarcă '
                   '`data/nhanes_klotho_2007_2016.csv` ' + cite(17, 29) + '.')

    if raw is not None and len(raw):
        guess = di.guess_mapping(list(raw.columns))
        with st.expander('🔗 Potrivirea coloanelor (verifică!)', expanded=not src.startswith('Cohortă')):
            options = ['— lipsește —'] + list(raw.columns)
            mapping = {}
            cols_m = st.columns(2)
            for i, (std, desc) in enumerate(di.STANDARD_COLUMNS.items()):
                default = guess.get(std)
                sel = cols_m[i % 2].selectbox(desc, options,
                                              index=options.index(default) if default in options else 0,
                                              key='map_' + std)
                if sel != '— lipsește —':
                    mapping[std] = sel
        assay = st.radio('Tipul testului FGF23 din fișier (dacă nu există coloana `fgf23_test`)',
                         ['C-terminal (RU/mL)', 'intact (pg/mL)'], horizontal=True)
        anchor_fgf = DEFAULT_ANCHORS['FGF23 C-terminal (RU/mL)'] if assay.startswith('C') else DEFAULT_ANCHORS['FGF23 intact (pg/mL)']
        data = di.enrich(di.apply_mapping(raw, mapping), fgf23_anchor=anchor_fgf)
        st.write(f'**{len(data)} rânduri**, {data["grup"].nunique()} grupuri.')
        st.dataframe(data, hide_index=True, use_container_width=True, height=260)
        st.download_button('⬇️ Descarcă datele prelucrate (CSV)', data.to_csv(index=False).encode('utf-8-sig'),
                           'date_prelucrate_v10.csv', 'text/csv')

        num = [c for c in ['egfr', 'fosfat_mmol_L', 'FEPO4_%', 'TmP_GFR_mmol_L', 'fgf23', 'klotho_pg_mL',
                           'pth_pg_mL', 'hemoglobina_g_dL', 'feritina_ug_L', 'saturatia_transferinei_%']
               if c in data and data[c].notna().sum() > 2]
        if num:
            st.markdown('**Statistică descriptivă pe grupuri (mediana [interval intercuartilic])**')

            def miqr(x):
                x = x.dropna()
                return '—' if x.empty else f'{x.median():.1f} [{x.quantile(.25):.1f}–{x.quantile(.75):.1f}]'
            desc = data.groupby('grup')[num].agg(miqr)
            desc.insert(0, 'n', data.groupby('grup').size())
            st.dataframe(desc, use_container_width=True)
        if 'stadiu_RFG' in data:
            st.plotly_chart(px.histogram(data, x='stadiu_RFG', color='grup',
                                         category_orders={'stadiu_RFG': di.STAGE_ORDER},
                                         title='11. Distribuția pe stadii KDIGO'), use_container_width=True)
        pc1, pc2 = st.columns(2)
        if 'egfr' in data and 'fgf23' in data and data['fgf23'].notna().any():
            with pc1:
                st.plotly_chart(px.scatter(data, x='egfr', y='fgf23', color='grup', log_y=True,
                                           title='12. Filtrare glomerulară vs FGF23'), use_container_width=True)
        if 'feritina_ug_L' in data and 'fgf23' in data and data['feritina_ug_L'].notna().any():
            with pc2:
                st.plotly_chart(px.scatter(data, x='feritina_ug_L', y='fgf23', color='grup', log_x=True, log_y=True,
                                           title='13. 🩸 Feritină vs FGF23 — mecanismul fierului ' + cite(21),
                                           labels={'feritina_ug_L': 'Feritină (micrograme pe litru)'}),
                                use_container_width=True)
        if 'fosfat_mmol_L' in data and 'TmP_GFR_mmol_L' in data:
            fig_t = px.scatter(data, x='fosfat_mmol_L', y='TmP_GFR_mmol_L', color='grup',
                               title='14. Fosfat seric vs prag de reabsorbție ' + cite(13))
            fig_t.add_vline(x=0.81, line_dash='dot', annotation_text='fosfat 0,81')
            fig_t.add_hline(y=0.81, line_dash='dot', annotation_text='prag 0,81 ' + cite(6))
            st.plotly_chart(fig_t, use_container_width=True)
            st.caption('Cadranul stânga-jos sugerează pierdere renală de fosfat.')
        if len(num) >= 3 and len(data) >= 10:
            st.plotly_chart(px.imshow(data[num].corr(method='spearman'), text_auto='.2f', zmin=-1, zmax=1,
                                      color_continuous_scale='RdBu_r',
                                      title='15. Corelații Spearman (descriptive, fără ajustare)'),
                            use_container_width=True)
            st.caption('Corelația nu demonstrează cauzalitate. Pentru publicare: ajustare pentru vârstă, sex, albuminurie, '
                       'tratament, plus ponderi statistice în cazul NHANES.')

        st.markdown('#### Trimite un pacient în simulator')
        pick = st.selectbox('Alege rândul', data.index,
                            format_func=lambda i: f"{data.loc[i, 'id'] if 'id' in data else i} — {data.loc[i, 'grup']}")

        def trimite(i=pick):
            r = data.loc[i]
            if 'egfr' in r and pd.notna(r['egfr']):
                st.session_state['p_rfg'] = int(np.clip(round(float(r['egfr'])), 5, 130))
            if 'klotho_pg_mL' in r and pd.notna(r['klotho_pg_mL']):
                st.session_state['p_klotho'] = int(np.clip(10 * round(float(r['klotho_pg_mL']) / 10), 100, 1600))
            if 'feritina_ug_L' in r and pd.notna(r['feritina_ug_L']):
                st.session_state['p_feritina'] = int(np.clip(round(float(r['feritina_ug_L'])), 3, 400))
            if 'fgf23' in r and pd.notna(r['fgf23']) and str(r.get('fgf23_test', '')).lower().startswith('intact'):
                st.session_state['p_fgf23_fix'] = float(np.clip(float(r['fgf23']), 5, 1500))
                st.session_state['fgf_liber'] = False
            else:
                st.session_state['fgf_liber'] = True
            st.session_state['pacient_incarcat'] = f"{r.get('id', i)} ({r['grup']})"
        st.button('➡️ Încarcă parametrii în pacientul virtual', on_click=trimite, type='primary')
        st.caption('Filtrarea glomerulară, α-Klotho și feritina se copiază direct, fiind în unități reale. FGF23 se impune '
                   'numai dacă testul este intact; pentru testul C-terminal, modelul își calculează singur hormonul.')

# ---------------------------------------------------------------- 6. Validare
with tabs[6]:
    st.subheader('🎯 Validarea modelului pe date publicate')
    st.markdown('Un model care nu se poate compara cu nimic nu este cercetare. Aici modelul este pus față în față cu '
                'valorile publicate, iar eroarea este raportată deschis.')
    tabel_val, eroare = validare()
    st.metric('Eroarea medie absolută a fosfatemiei', f'{eroare:.3f} mg/dL')
    st.dataframe(tabel_val, hide_index=True, use_container_width=True)
    st.caption('Țintele sunt fosfatemia medie pe categorii de filtrare glomerulară din cohorta CRIC ' + cite(1, 2) + '.')

    st.markdown('#### Criteriul calitativ: ce marker crește primul')
    o = ordine()
    figo = go.Figure()
    figo.add_scatter(x=o.RFG, y=o.FGF23_C_terminal_RU_mL / 100, name='FGF23 C-terminal / prag 100')
    figo.add_scatter(x=o.PTH_pg_mL * 0 + o.RFG, y=o.PTH_pg_mL / 65, name='Parathormon / prag 65')
    figo.add_scatter(x=o.RFG, y=o.fosfat_mg_dL / 4.6, name='Fosfat / prag 4,6')
    figo.add_hline(y=1.0, line_dash='dash', annotation_text='pragul fiecărui marker')
    figo.update_layout(title='16. Fiecare marker raportat la pragul său, pe măsură ce funcția renală scade',
                       xaxis_title='Rata de filtrare glomerulară', yaxis_title='valoare / prag',
                       xaxis=dict(autorange='reversed'))
    st.plotly_chart(figo, use_container_width=True)
    praguri = {
        'FGF23 C-terminal peste 100 RU/mL': ph.prag_depasire(o, 'FGF23_C_terminal_RU_mL', 100),
        'Parathormon peste 65 pg/mL': ph.prag_depasire(o, 'PTH_pg_mL', 65),
        'Fosfat peste 4,6 mg/dL': ph.prag_depasire(o, 'fosfat_mg_dL', 4.6),
    }
    st.dataframe(pd.DataFrame([{'marker': k, 'filtrarea la care depășește pragul': v} for k, v in praguri.items()]),
                 hide_index=True, use_container_width=True)
    ordonat = [v for v in praguri.values() if v is not None]
    if len(ordonat) == 3 and ordonat[0] > ordonat[1] > ordonat[2]:
        st.success('✅ Modelul reproduce rezultatul central al literaturii: FGF23 depășește pragul **înaintea** '
                   'parathormonului, iar parathormonul înaintea fosfatului ' + cite(1) + '. Acest tipar nu a fost impus; '
                   'rezultă din ecuații.')
    else:
        st.error('Modelul nu reproduce ordinea publicată a markerilor. Recalibrează înainte de a-l folosi.')

    st.markdown('#### Banda de incertitudine')
    st.caption('O singură linie pe grafic sugerează o precizie care nu există. Simulările de mai jos variază aleatoriu '
               'parametrii cinetici, pentru care nu avem valori măsurate la om.')
    n_mc = st.slider('Număr de simulări', 20, 200, 80, 20)
    var_mc = st.slider('Variația relativă a parametrilor', 0.05, 0.40, 0.15, 0.05)
    with st.spinner('Rulez simulările...'):
        mc = banda(PARAMETRI, n_mc, min(zile, 150))
    figm = go.Figure()
    figm.add_scatter(x=mc.zi, y=mc.percentila_95, line=dict(width=0), showlegend=False)
    figm.add_scatter(x=mc.zi, y=mc.percentila_5, fill='tonexty', line=dict(width=0),
                     name='interval 5–95%', fillcolor='rgba(31,119,180,0.2)')
    figm.add_scatter(x=mc.zi, y=mc.mediana, name='mediana', line=dict(width=3))
    figm.update_layout(title='17. Fosfatemia prezisă, cu banda de incertitudine',
                       xaxis_title='Zile', yaxis_title='mg/dL')
    st.plotly_chart(figm, use_container_width=True)

    st.markdown('#### Ce nu reproduce modelul')
    st.warning('Valorile simulate de FGF23 sunt mai mari decât medianele CRIC la filtrare glomerulară păstrată: modelul '
               'supraestimează hormonul la boala renală incipientă, chiar dacă reproduce corect tendința și fosfatemia. '
               'Declară acest lucru în lucrare; este o limitare onestă, nu un eșec.')

# ---------------------------------------------------------------- 7. Cu publicul
with tabs[7]:
    st.subheader('🎤 Chestionar pentru public')
    st.write('18 întrebări cu dificultate progresivă. Ultimele trei acoperă sistemul sânge și fier, adăugat în versiunea 10.')
    for i, (nivel, intrebare, optiuni, corect, explicatie) in enumerate(QUESTIONS):
        st.markdown(f'**{i + 1}. {intrebare}**')
        st.caption(nivel)
        selectat = st.radio('Răspuns', optiuni, index=None, key=f'quiz_v10_answer_{i}',
                            label_visibility='collapsed')
        if st.button('Verifică și explică', key=f'quiz_v10_check_{i}'):
            if selectat is None:
                st.warning('Selectează mai întâi un răspuns.')
            elif optiuni.index(selectat) == corect:
                st.success('Corect!')
            else:
                st.error('Răspunsul corect: ' + optiuni[corect])
            if selectat is not None:
                st.info(explicatie)
        st.divider()
    if st.button('🏆 Calculează scorul', type='primary'):
        scor = sum(st.session_state.get(f'quiz_v10_answer_{i}') == o[corect]
                   for i, (_, _, o, corect, _) in enumerate(QUESTIONS))
        st.metric('Scor', f'{scor}/{len(QUESTIONS)}')
        if scor <= len(QUESTIONS) * 0.4:
            st.info('Recapitulează rolul FGF23, al α-Klotho și al transportorilor de fosfat.')
        elif scor <= len(QUESTIONS) * 0.7:
            st.info('Bază bună; aprofundează diferențele dintre bolile cu exces de FGF23.')
        else:
            st.success('Foarte bine! Ai integrat mecanisme moleculare, clinică și raționament de cercetare.')
    if st.button('🔄 Resetează răspunsurile'):
        for i in range(len(QUESTIONS)):
            st.session_state.pop(f'quiz_v10_answer_{i}', None)
        st.rerun()

# ---------------------------------------------------------------- 8. Metodologie
with tabs[8]:
    st.markdown('''### Ce este nou în versiunea 10

**1. Model în unități reale.** Fosfatemia este în milimoli pe litru, timpul în zile, iar excreția renală trece prin
pragul de reabsorbție tubulară a fosfatului, formularea fiziologică standard ''' + cite(13) + '''. Rezultatele se pot
compara direct cu valori publicate, deci modelul este falsificabil.

**2. α-Klotho acționează asupra afinității, nu a amplitudinii.** Coreceptorul deplasează concentrația la care se obține
jumătate din efect, nu înmulțește efectul ''' + cite(11) + '''. Deficitul de α-Klotho nu desființează răspunsul, ci cere
mai mult hormon pentru același efect — rezistența renală descrisă în boala cronică renală ''' + cite(15) + '''.

**3. Bucla parathormonului este închisă.** Parathormonul este variabilă de stare, condusă de calciu și calcitriol, deci
hiperparatiroidismul secundar **apare din model**, nu este introdus ca presupunere.

**4. Compartiment osos.** Mineralizarea scade sub un prag de fosfatemie, ceea ce dă direct defectul de mineralizare din
rahitism și osteomalacie.

**5. Sistemul sânge și fier**, al șaptelea din proiect: deficitul de fier și eritropoietina cresc transcrierea FGF23, iar
clivarea hormonului decide dacă crește și fracțiunea activă ''' + cite(21, 22, 27) + '''.

**6. Validare și incertitudine.** Fila „🎯 Validare” compară modelul cu medianele publicate, verifică ordinea de apariție
a markerilor și desenează banda între percentila 5 și percentila 95.

### Ecuațiile principale

Excreția renală trece prin prag:''')
    st.latex(r'E_{\text{renal}} = \mathrm{GFR} \times \max\left(0,\; P_s - \mathrm{TmP/GFR}\right)')
    st.markdown('Pragul este controlat de FGF23 și parathormon, iar α-Klotho îi deplasează sensibilitatea:')
    st.latex(r'\mathrm{TmP/GFR} = \mathrm{TmP}_{\max}\left(1 - E_F\frac{F^{n}}{EC_{50}(K)^{n} + F^{n}}\right)'
             r'\left(1 - E_H\frac{H}{K_H + H}\right)')
    st.latex(r'EC_{50}(K) = EC_{50}^{0}\left(\frac{K_{\text{ref}}}{K}\right)^{\gamma}')
    st.markdown('Bilanțul fosfatului în compartimentul extracelular:')
    st.latex(r'V_{ec}\frac{dP_s}{dt} = A_{\text{intestin}} - E_{\text{renal}} - J_{\text{mineralizare}} + J_{\text{resorbție}}')
    st.markdown('Parathormonul și calcitriolul urmăresc fiecare o țintă, cu propria constantă de timp:')
    st.latex(r'\frac{dH}{dt} = \frac{H_{\text{țintă}}(Ca, D) - H}{\tau_H}, \qquad'
             r'H_{\text{țintă}} = H_0\left(\frac{Ca_{\text{ref}}}{Ca}\right)^{p}\left(\frac{D_{\text{ref}}}{D}\right)^{q}')
    st.markdown('Producția de FGF23, cu efectul fierului și al clivării:')
    st.latex(r'F_{\text{țintă}} = F_0\left(\frac{P_s}{P_{\text{ref}}}\right)^{a}'
             r'\left(\frac{D}{D_{\text{ref}}}\right)^{b} \cdot \phi(\text{feritină}) \cdot'
             r'\left(\frac{100}{\mathrm{GFR}}\right)^{c} \Big/ \kappa')
    st.markdown('''unde φ este amplificarea prin deficit de fier și κ este clivarea. Testul C-terminal măsoară hormonul
intact plus fragmentele, deci crește și atunci când clivarea este intensă, ceea ce explică de ce cele două teste
diverg ''' + cite(22) + '''.

### Limite — de declarat în prezentare
- Parametrii cinetici (constantele de timp, coeficienții Hill, capacitățile maxime) **nu sunt măsurați la om**; sunt
  aleși astfel încât modelul să reproducă medianele publicate.
- Calciul este menținut fix; modelul nu are bucla completă calciu–parathormon–os.
- Modelul supraestimează FGF23 la filtrare glomerulară păstrată (vezi fila de validare).
- Cohorta demonstrativă din fila de date este **sintetică**; nu sunt pacienți reali.
- Un singur compartiment extracelular; nu există redistribuire intracelulară, importantă în sindromul de realimentare.
- Modelul nu este validat clinic și nu se folosește pentru decizii privind pacienți reali.

### Cum rulezi analiza pe date reale
1. `python scripts/nhanes_klotho_download.py` descarcă datele publice NHANES, inclusiv feritina și hemoglobina.
2. Încarcă fișierul rezultat în fila „📊 Date reale”.
3. Folosește ponderile de sondaj pentru orice procent raportat ca național.
''')

# ---------------------------------------------------------------- 9. Bibliografie
with tabs[9]:
    st.subheader('📖 Bibliografie')
    st.caption('Numerele [n] din aplicație trimit la lista de mai jos.')
    for n, ref, url in BIBLIOGRAPHY:
        st.markdown(f'**[{n}]** {ref} — [{url}]({url})')
    bib = pd.DataFrame(BIBLIOGRAPHY, columns=['nr', 'referinta', 'link'])
    st.download_button('⬇️ Descarcă bibliografia (CSV)', bib.to_csv(index=False).encode('utf-8-sig'),
                       'bibliografie_v10.csv', 'text/csv')
    st.markdown('''#### Unde găsești date individuale

| Sursă | Ce conține | Acces |
|---|---|---|
| NHANES 2007–2016 [17] | α-Klotho, creatinină, fosfor, calciu, albuminurie | public, gratuit — script inclus |
| NHANES, fișierele de fier [29] | feritină, fier, saturația transferinei | public, gratuit |
| NHANES, parathormon [23] | parathormon, **numai 2003–2006** | public, gratuit |
| NHANES, aport alimentar [24] | fosfor și calciu din dietă | public, gratuit |
| CRIC [18] | FGF23, parathormon, fosfat urinar, evoluție în timp | cerere la depozitul institutului |
| GEO GSE104954 [19] | expresia genei Klotho în biopsii renale | public, gratuit |
| MIMIC-IV Demo [20] | fosfat, calciu, creatinină la 100 de pacienți | public, gratuit |
''')
