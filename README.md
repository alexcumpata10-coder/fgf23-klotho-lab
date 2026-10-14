# FGF23–α-Klotho — Laborator virtual multiorgan V5

## Instalare Windows
1. Extrage arhiva ZIP. Intră în folderul `fgf23_klotho_multiorgan_lab_v5`.
2. Click în bara de adresă a File Explorer (NU în Search), scrie `cmd`, Enter.
3. Rulează:

    python -m pip install --upgrade streamlit pandas numpy plotly
    python -m streamlit run app.py

4. Deschide http://localhost:8501 dacă nu se deschide automat.
5. Oprește cu Ctrl+C în CMD.

Nu folosi `simulare_fosfat.csv` din versiunile anterioare pentru a porni V5.

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
