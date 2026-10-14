import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='FGF23–α-Klotho | Laborator multiorgan', page_icon='🧬', layout='wide')
st.title('🧬 FGF23–α-Klotho — Laborator virtual multiorgan')
st.caption('Versiunea 8 • os ↔ rinichi ↔ intestin ↔ paratiroide ↔ cord • scenarii educaționale')
st.warning('TOATE cazurile sunt fictive. Indicii sunt adimensionali și NU sunt rezultate de laborator, predicții de boală sau recomandări medicale. Modelul nu este validat clinic.')

CASES = {
 'Adult sănătos': {'organ':'Control','mechanism':'Axa os–rinichi menține echilibrul fosfatului.','egfr':100,'fgf':100,'klotho':100,'pth':100,'intake':100,'tubule':100,'bone':100,'heart':100,'evidence':'fiziologie consacrată','clinical':'Fără semne clinice specifice; referință didactică.'},
 'BCR G3b — compensare': {'organ':'Rinichi / paratiroide','mechanism':'Masa nefronică scade; FGF23 crește precoce, Klotho renal poate scădea; fosfatemia poate rămâne normală.','egfr':35,'fgf':250,'klotho':60,'pth':165,'intake':100,'tubule':100,'bone':115,'heart':125,'evidence':'asociere clinică + mecanisme bine descrise','clinical':'Tulburări CKD-MBD, uneori fără hiperfosfatemie în faze timpurii.'},
 'BCR G5 — compensare insuficientă': {'organ':'Rinichi / os / cord','mechanism':'Capacitatea excretorie totală foarte mică, FGF23 și PTH crescute; calcitriol scăzut, retenție de fosfat mai probabilă.','egfr':12,'fgf':370,'klotho':30,'pth':260,'intake':100,'tubule':100,'bone':145,'heart':160,'evidence':'mecanisme + asocieri clinice','clinical':'Hiperfosfatemie, hiperparatiroidism secundar, osteodistrofie renală și risc cardiovascular crescut pot coexista.'},
 'XLH — rahitism hipofosfatemic X-linkat': {'organ':'Os / rinichi','mechanism':'Alterarea PHEX favorizează excesul de FGF23 activ → fosfaturie inadecvată și calcitriol inadecvat de mic.','egfr':100,'fgf':250,'klotho':100,'pth':105,'intake':100,'tubule':70,'bone':150,'heart':100,'evidence':'mecanism clinic bine stabilit','clinical':'Rahitism/osteomalacie, deformări osoase, durere osoasă, probleme dentare; debut frecvent în copilărie.'},
 'TIO — osteomalacie indusă de tumoră': {'organ':'Tumoră / os / rinichi','mechanism':'O tumoră mezenchimală poate secreta FGF23 în exces → pierdere renală de fosfat și mineralizare osoasă deficitară.','egfr':95,'fgf':340,'klotho':100,'pth':110,'intake':100,'tubule':75,'bone':170,'heart':100,'evidence':'mecanism clinic bine stabilit','clinical':'Durere osoasă, fracturi de fragilitate, slăbiciune musculară; afecțiune rară.'},
 'Deficit funcțional α-Klotho — ipoteză': {'organ':'Rinichi / semnalizare','mechanism':'Scăderea disponibilității coreceptorului limitează răspunsul clasic la FGF23; consecințele depind de cauză și context.','egfr':80,'fgf':230,'klotho':25,'pth':125,'intake':100,'tubule':100,'bone':120,'heart':110,'evidence':'scenariu mecanistic, nu diagnostic individual','clinical':'Nu reprezintă un sindrom clinic unic; folosit pentru a izola rolul coreceptorului.'},
 'Hiperaldosteronism primar — exploratoriu': {'organ':'Suprarenală / rinichi','mechanism':'Aldosteronul influențează Na+, K+ și volumul; interacțiunile cu FGF23/Klotho nu au un profil clinic universal.','egfr':90,'fgf':100,'klotho':100,'pth':125,'intake':100,'tubule':100,'bone':105,'heart':125,'evidence':'legătură indirectă/exploratorie','clinical':'Hipertensiune, renină suprimată, potasiu uneori scăzut; FGF23 nu este marker diagnostic.'},
 'Aport insuficient / alcool — exploratoriu': {'organ':'Intestin / nutriție / rinichi','mechanism':'Aportul mic, malnutriția, redistribuirea și uneori tubulopatia pot afecta fosfatul; FGF23 nu are răspuns unic.','egfr':95,'fgf':100,'klotho':100,'pth':110,'intake':55,'tubule':85,'bone':110,'heart':100,'evidence':'multifactorial, nespecific axei','clinical':'Hipofosfatemia poate apărea în contexte specifice, mai ales cu malnutriție/refeeding.'},
}

def model(egfr,fgf,klotho,pth,intake,tubule,steps=30):
    """Bilanț demonstrativ, unități arbitrare. Nu modelează concentrația serică."""
    renal = egfr/100
    signal = (fgf/100)*(klotho/100)
    calcitriol = float(np.clip(100*(0.25+0.75*renal)/(0.65+0.35*signal),10,180))
    absorbed = (intake/100)*(0.65+0.35*calcitriol/100)
    drive = float(np.clip(0.5*signal+0.5*pth/100,0.1,4))
    capacity = renal*(100/tubule)**0.8*(0.6+0.4*drive)
    stock=100.
    records=[]
    for step in range(steps+1):
        excretion=capacity*(stock/100)**0.7
        records.append({'pas':step,'stoc_relativ':stock,'aport_absorbit':absorbed,'excretie':excretion,'bilant':absorbed-excretion})
        stock=float(np.clip(stock+7*(absorbed-excretion),5,350))
    return pd.DataFrame(records),{'semnal':100*signal,'calcitriol':calcitriol,'capacitate':100*capacity,'absorbtie':absorbed}

st.sidebar.header('Pacient virtual')
chosen=st.sidebar.selectbox('Profil clinic',list(CASES))
c=CASES[chosen]
st.sidebar.caption('Poți modifica parametrii pentru a testa o ipoteză; nu sunt valori clinice calibrate.')
egfr=st.sidebar.slider('eGFR (mL/min/1,73 m²)',10,120,int(c['egfr']),5)
fgf=st.sidebar.slider('FGF23 (indice, 100=referință)',20,450,int(c['fgf']),5)
klotho=st.sidebar.slider('α-Klotho membranar (indice)',10,150,int(c['klotho']),5)
pth=st.sidebar.slider('PTH (indice)',20,320,int(c['pth']),5)
intake=st.sidebar.slider('Aport fosfat (indice)',20,200,int(c['intake']),5)
tubule=st.sidebar.slider('Integritate tubulară (indice)',20,120,int(c['tubule']),5)
steps=st.sidebar.slider('Pași abstracți',10,60,30,5)
df,derived=model(egfr,fgf,klotho,pth,intake,tubule,steps)

tabs=st.tabs(['🩺 Caz clinic','🦴 Organe și mecanisme','🔬 Pierdere renală','👥 Comparație cazuri','🎤 Cu publicul','📚 Metodologie'])
with tabs[0]:
 st.subheader(chosen)
 st.info(f"**Organ/e:** {c['organ']}  |  **Nivelul dovezilor:** {c['evidence']}")
 st.markdown('**Mecanism:** '+c['mechanism'])
 st.markdown('**Manifestări / relevanță clinică:** '+c['clinical'])
 cols=st.columns(4)
 for col,(label,value) in zip(cols,[('eGFR',f'{egfr}'),('FGF23 (indice)',f'{fgf}'),('α-Klotho (indice)',f'{klotho}'),('Semnal FGF23–Klotho',f"{derived['semnal']:.0f}")]): col.metric(label,value)
 st.markdown('**Întrebări pentru audiență:** De unde provine FGF23? De ce se modifică excreția fosfatului? Este problema secreția hormonului, răspunsul țesutului-țintă sau numărul de nefroni?')
 st.caption('Scenariul este un exemplu conceptual. Valorile FGF23/Klotho nu sunt măsurători reale și nu pot fi folosite pentru diagnosticul cazului.')
 st.subheader('Graficele și parametrii pacientului')
 m1,m2,m3,m4=st.columns(4)
 m1.metric('Stoc final relativ',f'{df.iloc[-1].stoc_relativ:.1f}')
 m2.metric('Absorbit (u.a./pas)',f"{derived['absorbtie']:.2f}")
 m3.metric('Excretat final (u.a./pas)',f"{df.iloc[-1].excretie:.2f}")
 m4.metric('Calcitriol (indice)',f"{derived['calcitriol']:.0f}")
 st.plotly_chart(px.line(df,x='pas',y='stoc_relativ',title='1. Stoc relativ de fosfat (NU fosfatemie)'),use_container_width=True)
 flux=df[['pas','aport_absorbit','excretie']].melt(id_vars='pas',var_name='flux',value_name='unitati')
 left,right=st.columns(2)
 with left: st.plotly_chart(px.line(flux,x='pas',y='unitati',color='flux',title='2. Absorbție vs excreție (unități arbitrare)'),use_container_width=True)
 with right:
  hormones=pd.DataFrame({'indice':['FGF23','α-Klotho','PTH','Calcitriol'], 'valoare':[fgf,klotho,pth,derived['calcitriol']]})
  st.plotly_chart(px.bar(hormones,x='indice',y='valoare',title='3. Indici relativi — NU analize sanguine'),use_container_width=True)
 sensitivity=[]
 for g in range(10,121,5):
  d,_=model(g,fgf,klotho,pth,intake,tubule,steps)
  sensitivity.append({'eGFR':g,'stoc_final':d.iloc[-1].stoc_relativ})
 st.plotly_chart(px.line(pd.DataFrame(sensitivity),x='eGFR',y='stoc_final',markers=True,title='4. Sensibilitate: eGFR vs stoc final în model'),use_container_width=True)
 st.download_button('⬇️ Descarcă traiectoria CSV',df.to_csv(index=False).encode('utf-8-sig'),'traiectorie_fosfat_v8.csv','text/csv')
 st.warning('O creștere a stocului din model NU dovedește hiperfosfatemie; un diagnostic de pierdere renală nu se stabilește din bilanțul abstract.')
with tabs[1]:
 from organ_schemes import SCHEMES, diagram
 st.subheader('Atlas interactiv FGF23–α-Klotho: scheme distincte pentru fiecare organ')
 st.caption('Selectează un organ: fiecare schemă are propriul circuit celular, hormonal și clinic. Liniile punctate marchează mecanisme propuse sau asocieri, nu relații clinice demonstrate.')
 organ=st.selectbox('Alege organul',list(SCHEMES.keys()))
 st.markdown('#### '+SCHEMES[organ][0])
 st.graphviz_chart(diagram(organ),use_container_width=True)
 st.markdown('**Interpretare clinică și fiziologică**')
 organ_key={'🦴 Os':'Os','🫘 Rinichi':'Rinichi','🥬 Intestin':'Intestin','🟣 Paratiroide':'Paratiroide','❤️ Cord':'Cord','🟠 Suprarenale':'Glanda suprarenală'}[organ]
 descriptions={
 'Os':'Osteocitele produc FGF23. Excesul FGF23 poate cauza hipofosfatemie și mineralizare deficitară în XLH și TIO. PTH persistent crescut poate accelera resorbția osoasă prin RANKL.',
 'Rinichi':'FGF23 + FGFR/α-Klotho reduce transportorii NaPi-IIa/IIc în tubul proximal, crescând fosfaturia; reduce CYP27B1 și stimulează CYP24A1. În BCR scade masa nefronică și expresia Klotho.',
 'Intestin':'Calcitriolul stimulează absorbția calciului și fosfatului. FGF23 reduce calcitriolul, influențând indirect intestinul. Absorbția reală nu este constantă și depinde de dietă.',
 'Paratiroide':'Reducerea calcitriolului și modificările calciului/fosfatului favorizează hiperparatiroidismul secundar în BCR. Relația directă FGF23–paratiroide este dependentă de context.',
 'Cord':'FGF23 crescut se asociază cu hipertrofia ventriculară stângă și risc cardiovascular în BCR. Unele mecanisme cardiace pot fi independente de α-Klotho; asocierea nu dovedește automat cauzalitate.',
 'Glanda suprarenală':'Hiperaldosteronismul primar produce hipertensiune, retenție de Na+ și uneori hipokaliemie. Relația cu FGF23/α-Klotho este indirectă și exploratorie, nu o regulă diagnostică.'}
 st.info(descriptions[organ_key])
 st.caption('Săgețile punctate reprezintă asocieri sau mecanisme încă investigate, nu efecte clinice garantate.')
with tabs[2]:
 st.subheader('Fosfaturie inadecvată ≠ bilanț total negativ')
 st.write('În hipofosfatemie, rinichiul sănătos ar trebui să conserve fosfatul. FEPO₄ poate fi inadecvat de mare chiar dacă excreția absolută este sub aportul absorbit.')
 a,b=st.columns(2)
 with a:
  phosphate=st.slider('Fosfat seric ipotetic (mmol/L)',0.3,1.8,0.55,0.05)
  renal_gfr=st.slider('eGFR în experiment',20,120,95,5)
 with b:
  trp=st.slider('TRP presupus (%)',40,99,65)
  absorbed=st.slider('Aport absorbit (u.a./pas)',0.2,1.5,0.7,0.05)
 fepo=100-trp
 filtered=3*(renal_gfr/100)*phosphate
 excreted=filtered*fepo/100
 delta=absorbed-excreted
 a,b,c=st.columns(3)
 a.metric('FEPO₄',f'{fepo}%'); b.metric('Excreție abstractă',f'{excreted:.2f}'); c.metric('Bilanț abstract',f'{delta:+.2f}')
 st.plotly_chart(px.bar(pd.DataFrame({'Flux':['Absorbit','Excretat'],'u.a./pas':[absorbed,excreted]}),x='Flux',y='u.a./pas',title='5. Fluxuri de fosfat în scenariu'),use_container_width=True)
 if phosphate<0.8 and fepo>=10: st.warning('FEPO₄ relativ mare în context de fosfatemie scăzută: exemplu de excreție renală inadecvată, NU diagnostic.')
 st.caption('FEPO₄=100−TRP doar în această definiție simplificată. În practică se calculează din probe simultane plasmă/urină și se interpretează cu TmP/GFR, contextul și momentul recoltării. Nu sunt modelate compartimentele osoase și intracelulare.')
with tabs[3]:
 st.subheader('Comparație între boli și organe')
 rows=[]
 for name,vals in CASES.items():
  sim,derived_case=model(vals['egfr'],vals['fgf'],vals['klotho'],vals['pth'],vals['intake'],vals['tubule'],steps)
  rows.append({'caz':name,'organ':vals['organ'],'eGFR':vals['egfr'],'FGF23_indice':vals['fgf'],'Klotho_indice':vals['klotho'],'PTH_indice':vals['pth'],'semnal_indice':round(derived_case['semnal'],1),'stoc_final_abstract':round(sim.iloc[-1].stoc_relativ,1),'nivel_dovezi':vals['evidence']})
 cmp=pd.DataFrame(rows)
 st.dataframe(cmp,hide_index=True,use_container_width=True)
 y=st.selectbox('Compară indicele',['FGF23_indice','Klotho_indice','PTH_indice','semnal_indice','eGFR','stoc_final_abstract'])
 st.plotly_chart(px.bar(cmp,x='caz',y=y,color='organ',title='6. Comparația cazurilor fictive'),use_container_width=True)
 st.download_button('⬇️ Descarcă comparația (CSV)',cmp.to_csv(index=False).encode('utf-8-sig'),'comparatie_multiorgan_v8.csv','text/csv')
 st.info('Graficele reflectă valori alese pentru demonstrație, NU distribuții clinice, efecte măsurate sau diferențe validate statistic.')
with tabs[4]:
 st.subheader('🎤 Quiz pentru public: de la noțiuni de bază la raționament de cercetare')
 st.write('15 întrebări cu dificultate progresivă. Poți răspunde în ordine, poți verifica fiecare răspuns și poți afișa explicațiile după discuția cu publicul.')
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
 ]
 levels = ['🟢 Nivel 1 — Atenție la prezentare','🟡 Nivel 2 — Aplicare clinică','🔴 Nivel 3 — Raționament avansat']
 st.progress(sum(st.session_state.get(f'quiz_v8_answer_{i}') is not None for i in range(len(QUESTIONS)))/len(QUESTIONS),text=f"Răspunsuri selectate: {sum(st.session_state.get(f'quiz_v8_answer_{i}') is not None for i in range(len(QUESTIONS)))}/15")
 for level in levels:
  st.markdown('### '+level)
  for i,(tier,question,options,correct,explanation) in enumerate(QUESTIONS):
   if tier != level: continue
   with st.container(border=True):
    st.markdown(f'**Întrebarea {i+1}.** {question}')
    selected=st.radio('Alege un răspuns',options,index=None,key=f'quiz_v8_answer_{i}',label_visibility='collapsed')
    if st.button('Verifică și explică',key=f'quiz_v8_check_{i}'):
     if selected is None: st.warning('Selectează mai întâi un răspuns.')
     elif options.index(selected)==correct: st.success('Corect!')
     else: st.error('Răspunsul corect: '+options[correct])
     if selected is not None: st.info(explanation)
 st.divider()
 if st.button('🏆 Calculează scorul și afișează feedbackul',type='primary'):
  answered=sum(st.session_state.get(f'quiz_v8_answer_{i}') is not None for i in range(15))
  score=sum(st.session_state.get(f'quiz_v8_answer_{i}') == options[correct] for i,(_,_,options,correct,_) in enumerate(QUESTIONS))
  st.metric('Scor',f'{score}/15')
  st.write(f'Întrebări completate: {answered}/15. Fiecare răspuns corect valorează 1 punct; întrebările necompletate valorează 0 puncte.')
  if score<=5: st.info('Recapitulează rolul FGF23, α-Klotho și transportorilor NaPi.')
  elif score<=10: st.info('Bază fiziologică bună; merită aprofundate diferențele dintre XLH și BCR.')
  elif score<=13: st.success('Foarte bine! Poți interpreta mecanismele și scenariile clinice.')
  else: st.success('Excelent! Ai integrat mecanisme moleculare, clinică și raționament de cercetare.')
 if st.button('🔄 Resetează răspunsurile'):
  for i in range(15):
   st.session_state.pop(f'quiz_v8_answer_{i}',None)
  st.rerun()
 st.caption('Quiz educațional pentru discuții, nu instrument de evaluare clinică. Întrebările finale testează și interpretarea critică a dovezilor.')
with tabs[5]:
 st.markdown('''### Ce reprezintă programul
**Model educațional necalibrat.** Parametrii hormonali sunt indici arbitrar aleși pentru a ilustra mecanisme; pașii nu sunt zile; „stocul” nu este fosfatemie. Datele exportate sunt exclusiv sintetice. Nu folosiți pentru diagnostic, tratament, estimarea riscului sau publicarea unor asocieri clinice.

### Interpretare și limite
- FGF23 produs în os reduce reabsorbția renală a fosfatului și calcitriolul; α-Klotho membranar este coreceptorul clasic renal.
- În **XLH** și **TIO**, excesul FGF23 poate produce fosfaturie inadecvată și hipofosfatemie.
- În **BCR**, FGF23 crescut coexistă cu scăderea capacității excretorii; fosfatemia poate rămâne normală inițial, apoi poate crește.
- **Cordul:** unele efecte propuse ale FGF23 pot fi independente de α-Klotho; nu sunt echivalente cu relații cauzale demonstrate în toate populațiile.
- **Hiperaldosteronismul** și **alcoolul** sunt exemple exploratorii; nu există profiluri universale FGF23/Klotho pentru ele.
- Formula modelului pentru semnal este doar **indice FGF23 × indice Klotho / 100**; nu reprezintă cinetica reală a receptorilor.
- Excreția și absorbția sunt în unități arbitrare, fără bilanț osos, redistribuire intracelulară sau reglare hormonală dinamică.

### Lecturi și ghiduri de pornire
- KDIGO CKD-MBD (2017): https://kdigo.org/guidelines/ckd-mbd/
- GeneReviews, X-Linked Hypophosphatemia: https://www.ncbi.nlm.nih.gov/books/NBK83985/
- Endotext, Tumor-Induced Osteomalacia: https://www.ncbi.nlm.nih.gov/books/NBK279148/
- Martin et al., FGF23 physiology (2012): https://doi.org/10.1152/physrev.00002.2011

**Pentru cercetare clinică reală:** sunt necesare date anonimizate colectate cu aprobările relevante, protocol, metode de dozare, analiză statistică și validarea modelului.''')
