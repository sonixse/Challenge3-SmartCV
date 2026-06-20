# Coneix SmartCV: Un Sistema Multi-Agent per a la Selecció Semàntica de Talent 🤝

> *"La persona adequada per al lloc adequat — compresa, no només emparellada."*

---

## Què és això?

SmartCV és un sistema multi-agent fet a mida que agafa el CV d'un candidat i troba les ofertes de feina que realment li encaixen — ordenades per compatibilitat semàntica real, no per coincidència de paraules clau.

Ho hem construït des de zero. Set agents especialitzats, cadascun amb una única responsabilitat, coordinats per un orquestrador que adapta el flux en funció del que troba a cada pas. No s'ha fet servir cap agent preconstruït. Cada rol ha estat dissenyat, justificat i implementat per l'equip.

El resultat s'assembla més a un equip de revisors experts treballant en paral·lel que a un motor de cerca.

---

## El Problema

Les eines tradicionals de selecció de CVs busquen per paraules clau. Si un CV diu `scikit-learn` i l'oferta diu `ML supervisat`, és un error — tot i que signifiquen el mateix.

Ho resolem amb **embeddings semàntics**: tant els CVs com els requisits de les ofertes es converteixen en vectors que representen el *significat*, no les lletres. Les skills conceptualment properes acaben matemàticament properes. Després filtrem les restriccions *must-have*, ordenem semànticament i expliquem els gaps.

Això no és un pipeline. És un sistema de raonament.

---

## Coneix els Agents

Hem posat a cada agent el nom d'una figura de la història la contribució de la qual reflecteix exactament el que fa aquell agent.

---

### 🟣 JOHN VON NEUMANN — L'Orquestrador
*John von Neumann va dissenyar l'arquitectura de l'ordinador modern: una unitat central que coordina memòria, processament i E/S. El nostre orquestrador fa exactament el mateix.*

Construït sobre **LangGraph**, John von Neumann gestiona l'estat complet del pipeline. Decideix quins agents s'activen, gestiona les branques condicionals (p. ex., només desperta Lamarr si hi ha skills en zona grisa) i s'assegura que cada agent rep exactament el context que necessita.

```
Input:  Pujada del CV
Output: Coordina el graf complet d'agents
Eina:   Graf d'estat de LangGraph
```

---

### 🟠 ADA LOVELACE — L'Agent Intèrpret
*Ada Lovelace va escriure el primer algorisme — la primera vegada que algú va convertir una idea humana en instruccions estructurades que una màquina podia seguir. Aquest agent fa el mateix: agafa un CV, un document profundament humà, i el converteix en dades estructurades sobre les quals un sistema pot raonar.*

L'Agent Intèrpret llegeix el PDF en brut, extreu un perfil estructurat del candidat — skills, anys d'experiència per domini, nivell i camp de formació, idiomes parlats — i el valida en un esquema Pydantic. Els CVs són desordenats, multilingües i inconsistents. Ada Lovelace s'encarrega de tot.

```
Input:  Text brut del CV (PDF → string)
Output: CandidateProfile estructurat (Pydantic)
Eina:   LLM + validació Pydantic
```

---

### 🔵 MARIE CURIE — L'Agent Qualificador
*El treball de Marie Curie es basava en el rigor científic absolut. O l'element era radioactiu o no ho era — sense aproximacions, sense negociació. La primera persona a guanyar dos Premis Nobel en dues ciències diferents no tractava en zones grises.*

El Qualificador aplica restriccions must-have de manera determinista: anys mínims d'experiència, nivell de formació i idiomes requerits. S'executa com a codi pur — ràpid, auditable i immune a les al·lucinacions del LLM. Si una vacant requereix anglès B2 i el candidat té A1, la resposta és no. No "probablement no." No.

> **Per què els idiomes van aquí i no als embeddings:** Un model semàntic podria col·locar "Català" a prop de "Castellà" i atorgar una coincidència parcial. Però els requisits d'idioma són restriccions operatives, no preferències difuses. El Qualificador les aplica — i és també la decisió èticament correcta.

```
Input:  CandidateProfile + Requisits de la vacant
Output: Indicador de pas/fall + penalització/bonificació de puntuació
Eina:   Motor de regles determinista (Python)
```

---

### 🟢 ALAN TURING — L'Agent Lingüista
*Alan Turing va preguntar si les màquines podien entendre el significat. Aquest agent és la resposta.*

L'Agent Lingüista fa la comparació semàntica de skills: converteix cada skill requerida de la vacant en un vector d'embedding i els compara amb els vectors de skills del candidat emmagatzemats a **ChromaDB**. Per generar aquests vectors fem servir **BGE** (un model d'IA open-source pre-entrenat de HuggingFace — pensa-hi com el component que llegeix un tros de text i el converteix en una llista de números que representa el seu *significat*. Les skills amb significats similars acaben com a números similars). La similitud cosinus produeix tres categories:

| Categoria | Llindar | Significat |
|-----------|---------|------------|
| ✅ MATCH | > 0.85 | Semànticament equivalent ("PySpark" ≈ "processament de dades distribuïdes") |
| ⚠️ ZONA GRISA | 0.60 – 0.85 | Possiblement relacionat — cal raonament |
| ❌ NO MATCH | < 0.60 | No cobert |

> **Sobre els llindars:** Els valors 0.85 i 0.60 són punts de partida heurístics, basats en la pràctica habitual en tasques de similitud semàntica. Els ajustem en funció de tres senyals: (1) **falsos positius** — si skills clarament no relacionades aterren a MATCH, pugem el llindar superior; (2) **falsos negatius** — si skills òbviament equivalents com "Python" vs "Python 3" cauen a ZONA GRISA en lloc de MATCH, el baixem; (3) **volum de zona grisa** — si massa skills acaben a ZONA GRISA, l'Agent Detectiu es converteix en un coll d'ampolla i alenteix el sistema, per tant ajustem els límits fins que la zona grisa captura només els casos genuïnament ambigus. L'objectiu és una zona grisa petita, significativa i que valgui el cost de cridar un LLM.

```
Input:  Skills del candidat + Requisits de skills de la vacant
Output: Classificació per skill (MATCH / ZONA GRISA / NO MATCH)
Eina:   BGE (model de vectors de significat) + cerca de veïns propers a ChromaDB
```

---

### 🟡 HEDY LAMARR — L'Agent Detectiu
*Hedy Lamarr va inventar l'espectre de salt de freqüència — la capacitat de detectar un senyal clar navegant intel·ligentment a través del soroll i l'ambigüitat. La base del WiFi, Bluetooth i GPS. Aquest agent fa el mateix: troba el senyal real en skills massa sorolloses per a una coincidència simple.*

L'Agent Detectiu gestiona el raonament d'ambigüitat — només s'activa quan Alan Turing marca skills com a ZONA GRISA. Llegeix el context real del CV — descripcions de projectes, historial laboral, mencions d'eines — i jutja si el candidat probablement té la skill de manera implícita. Sempre cita l'evidència específica que ha fet servir. Cap decisió silenciosa.

```
Input:  Skills en zona grisa + context complet del CV
Output: Veredicte MATCH / NO MATCH per skill + evidència citada
Eina:   LLM amb cadena de pensament
Activació: Condicional — només quan existeixen zones grises
```

---

### 🔴 SERENA WILLIAMS — L'Agent Podi
*Serena Williams va dominar el rànquing WTA durant més de 20 anys. El seu llegat no són només els trofeus — són els punts, acumulats de manera consistent, implacable, en totes les superfícies i en totes les èpoques. Aquest agent fa el mateix: agrega cada senyal en una puntuació final i ordena sense dubtar.*

L'Agent Podi gestiona la puntuació i el rànquing: agrega les sortides de Marie Curie, Alan Turing i Lamarr en una puntuació de compatibilitat ponderada per vacant. Els pesos es calibren per categoria de skill (must-have vs. nice-to-have) i seniority del rol. El resultat és una llista ordenada de vacants, cadascuna amb una puntuació transparent i descomposta.

**Gestió del cas sense coincidències.** L'Agent Podi mai retorna un resultat buit. Fins i tot quan les puntuacions són universalment baixes — és a dir, que el candidat no encaixa bé amb cap vacant — el rànquing es produeix i es mostra igualment. Una puntuació baixa no és un carreró sense sortida; és l'entrada més honesta i útil que l'Agent Visionari podria rebre. Com pitjor és la coincidència, més rica és la sortida de coaching. Un candidat sense cap coincidència forta no veu una pantalla en blanc — veu un full de ruta precís i personalitzat d'exactament el que ha de construir per ser competitiu. El sistema converteix el seu pitjor escenari en la seva sortida més valuosa.

```
Input:  Resultats de qualificació + resultats de coincidència de skills (tots els agents)
Output: Puntuació de compatibilitat (0–100) per vacant, ordenada — sempre, independentment de la puntuació
Eina:   Fórmula de puntuació ponderada (Python)
```

---

### 🟤 STEVE JOBS — L'Agent Visionari
*Steve Jobs mai va acceptar el "prou bé." Identificava els gaps, eliminava el soroll i deia a la gent exactament el que necessitava construir — i per què importava. Aquest agent fa el mateix per a la teva carrera.*

L'Agent Visionari actua com a coach de carrera: rep l'anàlisi de gaps (skills que falten o que són febles entre les vacants millor classificades) i genera recomanacions personalitzades i prioritzades. Té en compte el que el candidat ja sap i suggereix els propers passos d'alt impacte — no una llista genèrica de skills, sinó un camí de desenvolupament raonada.

Quan les puntuacions són altes, Steve Jobs afina — *"una skill més i passes del rang 3 al rang 1"*. Quan les puntuacions són universalment baixes, Steve Jobs pren el control completament: reencadena tota la sortida d'un rànquing a un pla de desenvolupament, dient al candidat no només el que li falta sinó en quin ordre abordar-ho i per què — prioritzat per impacte en l'ocupabilitat en totes les vacants simultàniament.

> **Exemple amb bona coincidència:** *"Tens les bases de ML per a rols de Data Scientist. Afegir MLflow (ja fas servir Docker — és una rampa de 2 dies) et faria competitiu per a 3 vacants més d'aquesta llista."*

> **Exemple sense coincidència:** *"Cap de les vacants actuals és un bon encaix encara — però estàs més a prop del que creus. La teva base de Python cobreix el 60% del que requereix Data Analyst Junior. Centra't primer en SQL i Power BI: aquestes dues skills desbloquegen 5 de les 8 vacants del dataset. Podries ser competitiu en 3 mesos."*

```
Input:  CandidateProfile + vacants principals + anàlisi de gaps
Output: Recomanacions de skills ordenades amb justificació d'impacte
Eina:   LLM amb sortida estructurada
```

---

### 🏆 JOHANNES GUTENBERG — L'Agent Editor
*Johannes Gutenberg va inventar la impremta — l'acte original de fer la informació visible i accessible per a les masses. Johannes Gutenberg converteix la sortida del pipeline en quelcom que un humà pot llegir i sobre el qual pot actuar.*

L'Agent Editor gestiona els resultats i la visualització: persisteix tots els resultats a **SQLite** — incloent els resultats de l'anàlisi, les descripcions de les vacants i el perfil del CV enviat — estructura la sortida per a la interfície i impulsa el que el candidat veu realment: la llista ordenada, el desglossament per skill i la sortida de coaching de Steve Jobs — tot renderitzat en una interfície neta de **Gradio**.

> **Per què Gradio i no Streamlit?** Gradio és natiu de HuggingFace, té suport de primera classe per a pujada de fitxers, sortida estil xat i UX per a demos de models d'IA. Com que fem servir BGE (el nostre model d'embedding open-source) de HuggingFace i la sortida del Coach és conversacional, el conjunt de components de Gradio s'adapta a aquest cas d'ús de manera més natural que el paradigma de dashboard de dades de Streamlit.

```
Input:  Resultats finals ordenats + sortida de coaching
Output: Interfície Gradio renderitzada per al candidat
Eina:   SQLite + Gradio
```

---

## Arquitectura Completa del Sistema

```
                        ┌─────────────────────┐
                        │   Interfície Gradio │
                        │  (el candidat puja  │
                        │     CV en PDF)      │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ 🟣 JOHN VON NEUMANN │
                        │    Orquestrador     │
                        │    (LangGraph)      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               │                   │                   │
    ┌──────────▼──────────┐        │        ┌──────────▼──────────┐
    │  🟠 ADA LOVELACE    │        │        │   🔵 MARIE CURIE    │
    │  Agent Intèrpret    │        │        │  Agent Qualificador │
    │  LLM + Pydantic     │        │        │   Motor de Regles   │
    └──────────┬──────────┘        │        └──────────┬──────────┘
               │                   │                   │
               └───────────────────▼───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟢 ALAN TURING   │
                        │  Agent Lingüista    │
                        │ Vectors BGE+ChromaDB│
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Zones grises trobades?      │
                    │  SÍ ──► 🟡 HEDY LAMARR     │
                    │        Agent Detectiu        │
                    │          LLM + Evidència     │
                    │  NO  ──► ometre              │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🔴 SERENA WILLIAMS │
                        │    Agent Podi       │
                        │  Rànquing Ponderat  │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟤 STEVE JOBS    │
                        │   Agent Visionari   │
                        │  LLM + Anàlisi Gaps │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🏆 J. GUTENBERG    │
                        │    Agent Editor     │
                        │  SQLite + Gradio    │
                        └─────────────────────┘
```

### Llegenda d'agents

| Símbol | Agent | Tipus |
|--------|-------|-------|
| 🟣 | John von Neumann | Orquestrador — LangGraph |
| 🟠 | Ada Lovelace | Agent LLM — Intèrpret |
| 🔵 | Marie Curie | Determinista — Motor de regles |
| 🟢 | Alan Turing | Agent de dades — BGE + ChromaDB |
| 🟡 | Hedy Lamarr | Agent LLM — Cadena de pensament |
| 🔴 | Serena Williams | Determinista — Fórmula de puntuació |
| 🟤 | Steve Jobs | Agent LLM — Anàlisi de gaps |
| 🏆 | Johannes Gutenberg | Determinista — SQLite + Gradio |

---

## Stack Tecnològic

| Component | Eina | Motiu |
|-----------|------|-------|
| Orquestració | LangGraph | Graf d'agents amb estat i condicional — no és un pipeline fix |
| LLM | Llama 3 (Ollama) | Open source, local, cost zero d'API |
| Model d'embeddings | **BGE** (BAAI/bge-base-en-v1.5) | Model d'IA open-source que converteix text en vectors de significat. Pre-entrenat per HuggingFace — l'usem tal qual, sense entrenament. Top en tasques de cerca semàntica. |
| Base de dades vectorial | ChromaDB | Cerca de veïns propers nativa, fitxer local, zero servidor |
| Base de dades relacional | SQLite | Emmagatzema resultats d'anàlisi, puntuacions, descripcions de vacants i perfils de CV enviats |
| Validació de dades | Pydantic | Sortida estructurada i tipada dels agents LLM |
| Frontend | Gradio | Natiu de HuggingFace, UX de xat + pujada de fitxers, ideal per a demos d'IA |

---

## Dades

- **Ofertes de feina:** 8 posicions a l'stack d'IA/Dades — des de Data Analyst Junior fins a AI Researcher i MLOps Engineer
- **CVs:** 10 perfils sintètics de candidats, cobrint una varietat de nivells de seniority, combinacions de skills i backgrounds

---

## Com Executar-ho

```bash
# 1. Clona i instal·la
git clone https://github.com/sonixse/Challenge3-SmartCV
cd Challenge3-SmartCV
pip install -r requirements.txt

# 2. Inicia Ollama amb Llama 3
ollama run llama3

# 3. Indexa les vacants a ChromaDB (executa una vegada)
python scripts/index_vacancies.py

# 4. Llança la interfície
python app.py
```

Puja un CV (PDF). En segons:
- Millors ofertes de feina ordenades amb puntuacions de compatibilitat
- Desglossament per skill: MATCH / ZONA GRISA (amb el raonament de Lamarr) / NO MATCH
- Anàlisi de gaps personalitzada de Jobs i full de ruta de desenvolupament

---

## Per Què Això És un Sistema Multi-Agent Genuí

La restricció era clara: cap agent preconstruït. Aquí expliquem com la complim — i anem més enllà:

- **7 agents, 7 rols** — cada agent té una única responsabilitat definida amb entrades i sortides tipades
- **Activació condicional** — Lamarr només s'executa quan Turing troba ambigüitat. Johannes Gutenberg només renderitza quan Serena Williams té una puntuació final. El sistema no és un pipeline fix; s'adapta.
- **Separació deliberada LLM vs. codi** — Marie Curie i Serena Williams s'executen com a codi pur perquè les seves tasques són deterministes. Ada Lovelace, Lamarr i Steve Jobs fan servir LLMs perquè les seves tasques requereixen comprensió del llenguatge. Aquesta és una decisió arquitectònica, no un valor per defecte.
- **L'orquestrador té estat** — Von Neumann fa seguiment del que s'ha executat, el que està pendent i com és el perfil del candidat actual a cada pas.

---

## Les 5 Dimensions d'Avaluació

**1. Innovació i Originalitat**
Embeddings semàntics + una capa de raonament condicional (Lamarr) + un agent de coaching de carrera personalitzat (Steve Jobs). La majoria d'eines de CVs fan coincidència per paraules clau. Nosaltres fem comprensió semàntica amb explicabilitat i un full de ruta de desenvolupament. El nom dels agents no és decoració — és una estratègia de comunicació que fa l'arquitectura instantàniament memorable.

**2. Viabilitat i Escalabilitat**
Cada component és realista per a producció. ChromaDB escala a milions de vectors. BGE (el nostre model d'embedding) és prou ràpid per a consultes en temps real. SQLite canvia a PostgreSQL amb un canvi de configuració. La interfície Gradio es converteix en un endpoint REST API. El patró d'orquestrador LangGraph funciona a qualsevol escala.

**3. Claredat i Concisió**
Un agent, una feina. L'arquitectura és llegible: pots apuntar a qualsevol node i explicar què fa, per què hi és i per què fa servir l'eina que fa servir. La branca condicional és un únic punt de decisió (existeixen zones grises?).

**4. Col·laboració i Engagement**
Jobs fa el sistema valuós per als *candidats*, no només per als reclutadors. Això converteix una eina de selecció B2B en quelcom amb valor directe per a l'usuari — un assessor de carrera que et dona una llista de tasques ordenades per al teu proper rol.

**5. Consideracions Ètiques**
- Cap atribut protegit (edat, gènere, nacionalitat) entra a la puntuació
- Les regles de Marie Curie són transparents i auditables — sense descalificacions silencioses per LLM
- Lamarr sempre cita la seva evidència — cap decisió en zones grises és opaca
- Els requisits d'idioma són restriccions operatives, no senyals culturals (gestionats per Marie Curie, no per Alan Turing)
- Tots els models s'executen localment — cap dada del candidat surt del sistema

---

## El Que Construiríem Amb Més Temps

- **Recuperació en dues fases:** fer servir una versió lleugera de BGE per a la recuperació ràpida dels 50 millors candidats, després el model complet per al re-rànquing final. Així és com funcionen els sistemes de cerca semàntica en producció — ho hem prototipat en teoria i ho implementaríem en una versió de producció.
- **Bucle de retroalimentació:** recollir les decisions d'acceptació/rebuig del reclutador i ajustar els pesos de Serena Williams amb el temps. Aprenentatge en línia lleuger sense entrenament.
- **Panell d'explicabilitat:** Johannes Gutenberg ampliat amb un desglossament visual de cada component de la puntuació — útil per a auditories de RRHH i compliment normatiu.
- **Suport multilingüe de CVs:** BGE (el nostre model d'embedding) gestiona text multilingüe; Ada Lovelace s'ampliaria per parsejar CVs nativament en castellà, català i anglès sense preprocessament.
- **Capa REST API:** exposar el graf complet d'agents com a API perquè es pugui integrar als sistemes ATS existents. John von Neumann es converteix en un servei, no en un script.
- **Generació sintètica de CVs a escala:** generació programàtica de CVs de casos límit per a testejar Lamarr i calibrar els llindars d'Alan Turing.

---

## L'Equip

Cinc persones, dos camins, un sistema.

**Backend · Agents · Orquestració · Pipeline**
Un enginyer industrial, un enginyer informàtic i un enginyer d'IA — les persones que han construït els agents i els han fet parlar entre ells.

**Frontend · Presentació · Documentació · Impacte**
Un especialista en biomedicina i un expert en negoci i tecnologia — les persones que han fet el sistema llegible, defensable i que val la pena presentar.

Els noms dels agents són un petit homenatge a aquesta estructura: cada un porta l'esperit d'una disciplina que algú de l'equip viu.

---

> *"No hem fet servir cap agent preconstruït. Hem dissenyat una arquitectura multi-agent a mida on cadascun dels set agents té un rol específic i justificat — des del parseig del CV fins a la coincidència semàntica, el filtratge dur, el raonament d'ambigüitat, la puntuació, el coaching i la visualització — coordinats per un orquestrador que adapta el flux en funció del que troba a cada pas."*
