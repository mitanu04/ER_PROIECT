# Descompunere celulară aproximativă - planificarea drumului

Proiect la Elemente de Robotică.
- Etapa 1: descompunere omogenă (grilă uniformă) și patru algoritmi de căutare a drumului
  (BFS, Dijkstra, A*, Greedy), cu netezirea drumului.
- Etapa 2: server API cu FastAPI + uvicorn.
- Etapa 3: descompunerea prin metoda arborelui (quadtree) și frontend-ul în JavaScript.

## Instalare

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Pornire rapidă

```bash
cd backend
uvicorn api:app --reload        # sau: python api.py
```

Deschide http://127.0.0.1:8000/: se încarcă interfața cu harta `demo`.

## Frontend-ul

HTML + CSS + JavaScript simplu (fără build), în `frontend/`. Serverul îl servește direct
la http://127.0.0.1:8000/. Codul JavaScript e împărțit în module ES (`frontend/js/`), deci
pagina trebuie servită prin HTTP (nu merge deschisă direct ca fișier). Servită de pe alt
port (de ex. Live Server), apelează automat serverul de la `http://127.0.0.1:8000`; altă
adresă se poate da cu `?api=http://...`.

| Modul | Ce face |
|---|---|
| `main.js` | punctul de intrare: leagă evenimentele, verifică serverul, încarcă harta `demo` |
| `config.js` | constante: adresa serverului, culorile, dimensiunile de desen |
| `stare.js` | starea comună: harta, ultimul rezultat, selecția, unealta curentă |
| `dom.js` | elementele paginii și valorile din panoul de comenzi |
| `coordonate.js` | transformări cm ↔ pixeli, punct în poligon |
| `api.js` | cererile către server |
| `aplicatie.js` | planificarea drumului, comparația, încărcarea / salvarea / modificarea hărții |
| `desen.js` | desenarea pe canvas, pe straturi (celule, celule vizitate, restul) |
| `animatie.js` | animația căutării |
| `panou.js` | metricile, tabelul comparativ, mesajele, starea butoanelor |
| `editor.js` | editarea hărții cu mouse-ul și tastatura |
| `controale.js` | legarea panoului de comenzi la acțiuni |

În consola browserului, `aplicatie.stare` arată starea curentă (util la depanare).

- **Editare:** tragi cu mouse-ul startul (S), ținta (T) și obstacolele; la obstacolul
  selectat poți trage și vârfurile, iar tasta Delete îl șterge. Cu „Desenează obstacol”
  pui vârfurile prin click și închizi poligonul cu click pe primul vârf, dublu-click sau
  Enter (Esc anulează). Coordonatele se rotunjesc la 0,5 cm.
- **Descompunere:** grilă uniformă sau quadtree, latura celulei (respectiv latura minimă),
  adâncimea maximă (quadtree), vecinătate 4 sau 8.
- **Căutare:** drumul se recalculează automat după fiecare modificare. „Animează” arată
  ordinea în care algoritmul vizitează celulele, iar „Compară” rulează toți algoritmii
  cu ambele vecinătăți și afișează tabelul (click pe un rând îl afișează pe hartă).
- **Hărți:** se încarcă din lista hărților salvate și se salvează sub un nume nou. Hărțile
  din exemple (`exemplu`, `culoar_ingust`, `demo`) sunt protejate la suprascriere.

Harta `demo` (120 x 80 cm) este un „apartament” cu trei camere legate prin uși, cu
obstacole de forme diferite (dreptunghiuri, triunghiuri, octogon, un U concav) și o
trecere de 6 cm spre țintă: drumul există la celule de 2 cm, dar dispare la 4 cm.

## Figuri și teste

```bash
cd backend
python demo_etapa1.py           # generează figurile în ../figuri și hărțile-exemplu în ../harti
pytest                          # rulează testele
```

## API-ul

La http://127.0.0.1:8000/docs vezi toate endpoint-urile și le poți testa direct din
browser („Try it out”).

| Metodă | Cale | Ce face |
|---|---|---|
| GET | `/api/sanatate` | verifică dacă serverul merge |
| GET | `/api/metode` | descompunerile, algoritmii și vecinătățile disponibile |
| POST | `/api/descompune` | doar descompunerea (celule + statistici) |
| POST | `/api/planifica` | descompunere + drum + drum netezit + ordinea vizitării |
| POST | `/api/compara` | toți algoritmii pe aceeași hartă, pentru tabelul comparativ |
| GET | `/api/harti` | lista hărților salvate în `harti/` |
| GET / PUT | `/api/harti/{nume}` | încarcă / salvează o hartă |

Exemplu de cerere pentru `/api/planifica` (toate câmpurile în afară de `harta` sunt opționale):

```json
{
  "harta": {
    "latime": 100, "inaltime": 70, "start": [36, 45], "tinta": [93, 9],
    "obstacole": [[[20, 52], [90, 52], [90, 60], [20, 60]]]
  },
  "descompunere": {"tip": "quadtree", "latura": 1, "adancime_max": 7, "vecinatate": 8},
  "metoda": "astar",
  "netezire": true,
  "include_celule": true,
  "include_ordine": true
}
```

`descompunere.tip` este `"grila"` sau `"quadtree"`. La grilă, `latura` este latura celulei;
la quadtree este latura minimă sub care celulele nu se mai împart, iar `adancime_max`
limitează numărul de împărțiri.

În răspuns, `descompunere.celule` este o listă `[x, y, lățime, înălțime, stare]`
(stare: 0 liberă, 1 ocupată, 2 mixtă), iar `drum.ordine_vizitare` conține indici în
această listă, în ordinea în care algoritmul a extins celulele (pentru animație).
Dacă nu există drum, răspunsul are tot codul 200, cu `drum.gasit = false` și motivul în
`drum.motiv`. Erorile au codurile 422 (date invalide), 400 (de ex. prea multe celule),
403 (suprascrierea unei hărți-exemplu) sau 404 (hartă inexistentă).

## Structura

```
backend/
  core/
    geometrie.py   punct în poligon, intersecții, clasificare celulă (liberă / ocupată / mixtă)
    harta.py       mediul: dimensiuni, obstacole poligonale, start, țintă; JSON; hărțile-exemplu
    grila.py       descompunerea omogenă + interfața de graf
    quadtree.py    descompunerea prin metoda arborelui, cu aceeași interfață
    cautare.py     BFS, Dijkstra, A*, Greedy
    netezire.py    netezirea drumului (line of sight)
  schemas.py       modelele pydantic (validarea cererilor și forma răspunsurilor)
  servicii.py      logica aplicației, independentă de FastAPI
  api.py           serverul FastAPI (servește și frontend-ul)
  vizualizare.py   desen cu matplotlib
  demo_etapa1.py   figurile pentru raport și tabelul comparativ
  tests/           teste pytest
frontend/
  index.html       structura paginii
  style.css        aspectul
  js/              modulele JavaScript (vezi tabelul de mai sus)
harti/             hărți salvate în JSON (formatul folosit și de frontend)
figuri/            figuri generate pentru raport
```

## Convenții

- Unitatea de măsură este centimetrul; originea este în colțul stânga-jos, axa y în sus.
- O celulă **mixtă** (atinsă parțial de un obstacol) este tratată ca ocupată, ceea ce dă
  o margine de siguranță în jurul obstacolelor.
- Orice descompunere oferă aceeași interfață (`nod_pentru_punct`, `pozitie`, `vecini`,
  `euristica`, `segment_liber`), deci algoritmii de căutare și netezirea funcționează
  nemodificați pe grilă și pe quadtree.
- În quadtree, costul unei muchii este distanța dintre centrele celulelor, iar euristica
  A* este distanța euclidiană, deci A* rămâne optim.
- Lungimea afișată a drumului include segmentele exacte de la start și până la țintă, deci
  două drumuri cu același cost în graf (de ex. A* și Dijkstra) pot diferi cu câțiva milimetri.

## Exemplu de utilizare

```python
from core import harta_demo, GrilaUniforma, QuadTree, cauta_drum, netezeste

harta = harta_demo()
for graf in (GrilaUniforma(harta, latura=1, vecinatate=8),
             QuadTree(harta, latura=1, vecinatate=8, adancime_max=7)):
    rez = cauta_drum(graf, harta.start, harta.tinta, metoda="astar")
    print(graf.tip, graf.statistici()["celule_total"], rez.lungime, rez.noduri_vizitate)
    drum_netezit = netezeste(graf, rez.puncte)
```
