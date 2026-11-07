# FGF23–α-Klotho — Laborator virtual multiorgan V10

## Instalare Windows
1. Extrage arhiva ZIP. Intră în folderul `fgf23_klotho_multiorgan_lab_v10`.
2. Click în bara de adresă a File Explorer (NU în Search), scrie `cmd`, Enter.
3. Rulează:

    python -m pip install --upgrade streamlit pandas numpy plotly
    python -m streamlit run app.py

4. Deschide http://localhost:8501 dacă nu se deschide automat.
5. Oprește cu Ctrl+C în CMD.

Nu folosi fișiere CSV din versiunile anterioare pentru a porni aplicația.

## Conținut
- 8 cazuri: control, BCR G3b/G5, XLH, TIO, deficit funcțional α-Klotho, hiperaldosteronism exploratoriu, aport insuficient/alcool exploratoriu.
- Hartă multiorgan: os, rinichi, intestin, paratiroide, cord, suprarenală.
- Grafice de stoc, absorbție/excreție, indici endocrini, sensibilitate eGFR, comparații.
- Modul separat FEPO4/TRP pentru pierdere renală inadecvată.
- Experiment cu publicul, export CSV și metodologie.

## Limitări
Simulare educațională conceptuală. Coeficienți nevalidați. Indicii nu sunt concentrații reale; stocul relativ nu este fosfatemie; nu reprezintă o cohortă clinică. Nu se folosește pentru diagnostic, tratament sau concluzii de cercetare clinică.


## V7
Graficele, indicatorii, analiza de sensibilitate și exportul CSV sunt integrate în prima filă «Caz clinic». Fila separată «Simulare fosfat» a fost eliminată. Schemele organelor au rămas neschimbate.


## V8 — quiz pentru public
Fila „🎤 Cu publicul” include 15 întrebări cu dificultate progresivă (5 introductive, 5 clinice, 5 avansate), verificare individuală cu explicații, punctaj și resetare. Restul aplicației și schemele organelor au fost păstrate.


## V9 — date reale și bibliografie
Fișiere noi:
- `literature.py` — 20 de surse numerotate [n]; valori agregate publicate (cohorta CRIC, NHANES, osteomalacie indusă de tumoră, hipofosfatemie legată de cromozomul X); pragurile de calibrare indice ↔ unitate reală.
- `data_import.py` — rata estimată de filtrare glomerulară CKD-EPI 2021 (fără rasă), FEPO4, reabsorbția tubulară a fosfatului, TmP/GFR (formula Payne / Kenny–Glen), potrivire automată a coloanelor (inclusiv nume NHANES), cohortă demonstrativă sintetică.
- `scripts/nhanes_klotho_download.py` — descarcă și unește NHANES 2007–2016 (Klotho, creatinină, fosfor, calciu, creatinină urinară). Rulează: `python scripts/nhanes_klotho_download.py`, apoi încarcă `data/nhanes_klotho_2007_2016.csv`.

Modificări în aplicație:
- Filă nouă „📊 Date reale”: tabel de referință cu sursă, încărcare CSV + șablon, statistici pe grupuri, grafice (rata de filtrare vs FGF23 / Klotho, fosfat vs TmP/GFR), corelații Spearman, buton „Încarcă parametrii în pacientul virtual”.
- Graficul 5 în „Caz clinic”: pacientul virtual față de medianele FGF23 din cohorta CRIC.
- Bara laterală: echivalent orientativ în unități reale; cursorul FGF23 extins până la 1200 (osteomalacia indusă de tumoră are frecvent valori de peste 10 ori limita superioară).
- Citări [n] la nivelul dovezilor fiecărui caz; filă nouă „📖 Bibliografie”.

Limite: cohorta demonstrativă este sintetică; NHANES nu conține FGF23; pentru date CRIC este necesară cererea oficială la NIDDK. `cohort.py` (cohorta didactică din versiunile anterioare) este păstrat, dar nefolosit în interfață.


## V10 — model în unități reale, validare și sistemul sânge

Fișier nou: `physiology.py` — modelul fiziologic cu fosfatemia în milimoli pe litru și timpul în zile.
Integrare Runge-Kutta de ordinul 4; nu necesită pachete suplimentare față de V9.

Ce s-a schimbat față de V9:
1. **Unități reale.** Excreția renală trece prin pragul de reabsorbție tubulară: filtrarea glomerulară înmulțită
   cu diferența dintre fosfatemie și prag. Rezultatele se compară direct cu literatura.
2. **α-Klotho acționează pe afinitate**, deplasând concentrația la care se obține jumătate din efect, nu
   înmulțind efectul ca în versiunile anterioare.
3. **Parathormonul este variabilă de stare**, condusă de calciu și calcitriol: hiperparatiroidismul secundar
   apare din model, nu este introdus ca presupunere.
4. **Compartiment osos** cu prag de mineralizare — baza osteomalaciei.
5. **Sistemul sânge și fier**, al șaptelea: schemă proprie de organ, filă dedicată, două scenarii noi
   (criză de rahitism autozomal dominant cu deficit de fier, hipofosfatemie după carboximaltoză ferică),
   coloane noi de date (hemoglobină, feritină, saturația transferinei) și trei întrebări noi în chestionar.
6. **Filă de validare**: eroarea medie absolută față de fosfatemia publicată în cohorta CRIC, verificarea
   ordinii de apariție a markerilor și bandă de incertitudine prin simulări repetate.
7. Bibliografia a crescut de la 20 la 29 de surse.

Rezultatul validării la livrare: eroare medie absolută de 0,023 miligrame pe decilitru pentru fosfatemie, iar
modelul reproduce ordinea publicată — FGF23 depășește pragul înaintea parathormonului, iar parathormonul
înaintea fosfatului. Limitare cunoscută: modelul supraestimează FGF23 la filtrare glomerulară păstrată.

Filele aplicației: Caz clinic · Organe și mecanisme · Sânge și fier · Pierdere renală · Comparație cazuri ·
Date reale · Validare · Cu publicul · Metodologie · Bibliografie.

Fișierele `cohort.py` (cohorta didactică veche) și funcția `model()` din versiunile 1–9 nu mai sunt folosite
în interfață; au fost păstrate pentru comparație istorică.
