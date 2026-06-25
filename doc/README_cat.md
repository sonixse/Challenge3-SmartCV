# SmartCV: Un Sistema Multi-Agent per a la Selecció Semàntica de Talent 🤝

> *"La persona adequada per al lloc adequat — entesa, no simplement encaixada."*

---

## Què és això?

SmartCV és un sistema multi-agent personalitzat que pren el CV d'un candidat i troba les ofertes de feina que realment li encaixen — ordenades per compatibilitat semàntica real, no per coincidència de paraules clau.

Ho hem construït des de zero. Set agents especialitzats, cadascun amb una sola responsabilitat, coordinats per un orquestrador que adapta el flux en funció del que troba a cada pas. No s'ha fet servir cap agent prefabricat. Cada rol ha estat dissenyat, justificat i implementat per l'equip.

El resultat es comporta més com un equip de revisors experts treballant en paral·lel que com un motor de cerca.

---

## El Problema

Les eines tradicionals de criba de CVs fan coincidir paraules clau. Si un CV diu `scikit-learn` i l'oferta diu `supervised ML`, no hi ha coincidència — tot i que signifiquen el mateix.

Ho solucionem amb **embeddings semàntics**: tant els CVs com els requisits de les ofertes es converteixen en vectors que representen *significat*, no lletres. Les competències conceptualment properes acaben matemàticament properes. Aleshores filtrem els requisits *imprescindibles*, ordenem semànticament i expliquem les diferències.

Això no és un pipeline. És un sistema de raonament.

---

## Coneix els Agents

Hem donat a cada agent el nom d'una figura de la història la contribució de la qual reflecteix exactament el que fa aquell agent.

---

### 🟣 JOHN VON NEUMANN — L'Orquestrador
*John von Neumann va dissenyar l'arquitectura de l'ordinador modern: una unitat central que coordina memòria, processament i E/S. El nostre orquestrador fa el mateix.*

Construït sobre **LangGraph**, John von Neumann gestiona l'estat complet del pipeline. Decideix quins agents s'activen, gestiona la ramificació condicional (p. ex., només desperta Lamarr si existeixen competències en zona grisa) i garanteix que cada agent rep exactament el context que necessita.

```
Entrada: Pujada del CV
Sortida: Coordina el graf d'agents complet
Eina:    Graf amb estat LangGraph
```

---

### 🟠 ADA LOVELACE — L'Agent Intèrpret
*Ada Lovelace va escriure el primer algoritme — la primera vegada que algú va convertir una idea humana en instruccions estructurades que una màquina podia seguir. Aquest agent fa el mateix: pren un CV, un document profundament humà, i el converteix en dades estructurades sobre les quals un sistema pot raonar.*

L'Agent Intèrpret llegeix el PDF en brut, extreu un perfil de candidat estructurat — competències, anys d'experiència per àmbit, nivell i camp educatiu, idiomes parlats — i el valida en un esquema Pydantic. Els CVs són desordenats, multilingües i inconsistents. Ada Lovelace ho gestiona tot.

```
Entrada: Text brut del CV (PDF → text)
Sortida: CandidateProfile estructurat (Pydantic)
Eina:    LLM + validació Pydantic
```

---

### 🔵 MARIE CURIE — L'Agent Qualificador

El treball de Marie Curie estava construït sobre un rigor científic absolut. O l'element era radioactiu o no ho era — sense aproximacions, sense negociació. La primera persona a guanyar dos Premis Nobel en dues ciències diferents no tractava zones grises.

El Qualificador aplica els requisits imprescindibles de manera determinista seguint quatre regles:

1. Anys d'experiència — el candidat ha d'igualar o superar el mínim de la vacant
2. Nivell educatiu — verificat contra una jerarquia (Sense titulació → Grau → Màster → Doctorat)
3. Idiomes requerits — cada idioma verificat per nom i nivell MCER mínim
4. Coincidència exacta de competències — una bonificació suau per coincidències directes de nom, abans que Alan Turing faci la comparació semàntica

S'executa com a codi pur — ràpid, auditable i immune a les al·lucinacions dels LLM. Si una vacant requereix anglès B2 i el candidat té A1, la resposta és no. No "probablement no." No.

> **Per què els idiomes van aquí i no als embeddings:** Un model semàntic podria situar "Català" a prop de "Castellà" i concedir una coincidència parcial. Però els requisits d'idioma són restriccions operatives, no preferències difuses. El Qualificador aplica això — que és també la decisió èticament correcta.

```
Entrada: CandidateProfile + requisits de la vacant
Sortida: bandera pass/fail + puntuació (0..4) + llista failed_checks + llista de motius
         failed_checks indica a Steve Jobs exactament quines regles ha fallat el candidat,
         permetent un coaching dirigit en lloc d'una anàlisi de buits genèrica
Eina:    Motor de regles determinista (Python)
```

---

### 🟢 ALAN TURING — L'Agent Lingüista
*Alan Turing va preguntar si les màquines podien entendre el significat. Aquest agent és la resposta.*

L'Agent Lingüista fa la comparació semàntica de competències: converteix cada competència requerida de la vacant en un vector d'embedding i el compara amb els vectors de competències del candidat emmagatzemats a **ChromaDB**. Per generar aquests vectors, fem servir **`intfloat/multilingual-e5-base`** — un model d'embedding multilingüe de codi obert i preentrenat de HuggingFace. Pensa-hi com un component que llegeix un fragment de text i el converteix en una llista de nombres que representa el seu *significat*. Les competències que signifiquen coses similars acaben com nombres similars. La similitud cosinus produeix tres categories:

| Categoria | Llindar | Significat |
|-----------|---------|------------|
| ✅ MATCH | > 0.87 | Semànticament equivalent ("PySpark" ≈ "processament de dades distribuït") |
| ⚠️ ZONA GRISA | 0.84 – 0.87 | Possiblement relacionat — cal raonament |
| ❌ NO MATCH | < 0.84 | No cobert |

> **Sobre els llindars:** Els valors 0.87 i 0.84 són punts de partida heurístics, informats per pràctiques habituals en tasques de similitud semàntica. Estan definits a `src/config.py` (`LINGUIST_MATCH_THRESHOLD` i `LINGUIST_GREY_THRESHOLD`) i es poden ajustar sense tocar cap altre fitxer. Els ajustem basant-nos en tres senyals: (1) **falsos positius** — si competències clarament no relacionades acaben a MATCH, pugem el llindar superior; (2) **falsos negatius** — si competències òbviament equivalents com "Python" vs "Python 3" cauen a ZONA GRISA, el baixem; (3) **volum de zona grisa** — si massa competències acaben a ZONA GRISA, el Detective es converteix en un coll d'ampolla, així que ajustem fins que la zona grisa captia només casos genuïnament ambigus.

```
Entrada: Competències del candidat + requisits de competències de la vacant
Sortida: Classificació per competència (MATCH / ZONA GRISA / NO MATCH)
Eina:    intfloat/multilingual-e5-base + cerca de veïns pròxims a ChromaDB
```

---

### 🟡 HEDY LAMARR — L'Agent Detective
*Hedy Lamarr va inventar l'espectre de salt de freqüència — la capacitat de detectar un senyal clar navegant intel·ligentment per soroll i ambigüitat. La base del WiFi, Bluetooth i GPS. Aquest agent fa el mateix: troba el senyal real en competències massa sorolloses per a una coincidència simple.*

L'Agent Detective gestiona el raonament d'ambigüitat — només s'activa quan Alan Turing marca competències com a ZONA GRISA. Llegeix el context real del CV — descripcions de projectes, historial laboral, mencions d'eines — i jutja si el candidat probablement té la competència de manera implícita. Sempre cita l'evidència específica que ha fet servir. Sense decisions silencioses.

```
Entrada: Competències en zona grisa + context complet del CV
Sortida: Veredicte MATCH / NO MATCH per competència + evidència citada
Eina:    LLM amb cadena de pensament
Activació: Condicional — només quan existeixen zones grises
```

---

### 🔴 SERENA WILLIAMS — L'Agent Podi
*Serena Williams va dominar el rànquing de la WTA durant més de 20 anys. El seu llegat no són sols els trofeus — són els punts, acumulats de manera consistent, implacable, en cada superfície i cada era. Aquest agent fa el mateix: agrega cada senyal en una puntuació final i ordena sense hesitar.*

L'Agent Podi gestiona la puntuació i el rànquing: agrega les sortides de Marie Curie, Alan Turing i Lamarr en una puntuació de compatibilitat ponderada per vacant. Els pesos es calibren per categoria de competència (imprescindibles vs. valorades) i seniority del rol. El resultat és una llista ordenada de vacants, cadascuna amb una puntuació transparent i desglossada.

**Gestió del cas sense coincidència.** L'Agent Podi mai retorna un resultat buit. Fins i tot quan les puntuacions són universalment baixes — és a dir, quan el candidat no encaixa bé en cap vacant — el rànquing s'elabora i es presenta igualment. Una puntuació baixa no és un punt mort; és l'entrada més honesta i útil que l'Agent Visionari podria rebre mai. Com pitjor és la coincidència, més rica és la sortida de coaching. Un candidat sense coincidències fortes no veu una pantalla en blanc — veu un full de ruta precís i personalitzat d'exactament què ha de construir per ser competitiu. El sistema converteix el seu pitjor escenari en la seva sortida més valuosa.

```
Entrada: Resultats de qualificació + resultats de coincidència de competències (tots els agents)
Sortida: Puntuació de compatibilitat (0–100) per vacant, ordenada — sempre, independentment de la puntuació
Eina:    Fórmula de puntuació ponderada (Python)
```

---

### 🟤 STEVE JOBS — L'Agent Visionari
*Steve Jobs mai va acceptar "prou bé". Identificava buits, eliminava el soroll i deia a la gent exactament el que necessitava construir — i per què era important. Aquest agent fa el mateix per a la teva carrera.*

L'Agent Visionari actua com a coach de carrera: rep l'anàlisi de buits (competències absents o febles a les vacants millor classificades) i genera recomanacions personalitzades i prioritzades. Té en compte el que el candidat ja sap i suggereix els passos de major impacte — no una llista genèrica de competències, sinó un camí de desenvolupament raonat.

Quan les puntuacions són altes, Steve Jobs afina — *"una competència més i passes del rang 3 al rang 1"*. Quan les puntuacions són universalment baixes, Steve Jobs pren el control completament: reenfoca tota la sortida d'un rànquing a un pla de desenvolupament, dient al candidat no sols el que li falta sinó en quin ordre abordar-ho i per què — prioritzat per impacte en l'ocupabilitat a totes les vacants simultàniament.

> **Exemple de bona coincidència:** *"Tens les bases d'ML per a rols de Data Scientist. Afegir MLflow (ja fas servir Docker — és una rampa de 2 dies) et faria competitiu per a 3 vacants més d'aquesta llista."*

> **Exemple de cap coincidència:** *"Cap de les vacants actuals és un bon encaix per ara — però estàs més a prop del que creus. La teva base de Python cobreix el 60% del que requereix Data Analyst Junior. Centra't primer en SQL i Power BI: aquestes dues competències desbloquegen 5 de les 8 vacants del conjunt de dades. Podries ser competitiu en 3 mesos."*

```
Entrada: CandidateProfile + vacants principals + anàlisi de buits
Sortida: Recomanacions de competències ordenades amb justificació d'impacte
Eina:    LLM amb sortida estructurada
```

---

### 🏆 JOHANNES GUTENBERG — L'Agent Editor
*Johannes Gutenberg va inventar la impremta — l'acte original de fer la informació visible i accessible per a les masses. Johannes Gutenberg converteix la sortida del pipeline en alguna cosa que un humà pot realment llegir i sobre la qual pot actuar.*

L'Agent Editor gestiona els resultats i la visualització: persisteix tots els resultats a **SQLite** — incloent els resultats de l'anàlisi, les descripcions de les vacants i el perfil del CV presentat — estructura la sortida per a la interfície i impulsa el que el candidat realment veu: la llista ordenada, el desglossament per competència i la sortida de coaching de Steve Jobs — tot renderitzat en una interfície **Streamlit** personalitzada.

```
Entrada: Resultats finals ordenats + sortida de coaching
Sortida: Interfície Streamlit renderitzada per al candidat
Eina:    SQLite + Streamlit
```

---

## Arquitectura Completa del Sistema

```
                        ┌─────────────────────┐
                        │ Interfície Streamlit │
                        │  (el candidat puja  │
                        │     el CV en PDF)   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟣 JOHN VON NEUMANN   │
                        │      Orquestrador   │
                        │    (LangGraph)      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               │                   │                   │
    ┌──────────▼──────────┐        │        ┌──────────▼──────────┐
    │  🟠 ADA LOVELACE     │        │        │   🔵 MARIE CURIE      │
    │  Agent Intèrpret    │        │        │  Agent Qualificador │
    │  LLM + Pydantic     │        │        │   Motor de Regles   │
    └──────────┬──────────┘        │        └──────────┬──────────┘
               │                   │                   │
               └───────────────────▼───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟢 ALAN TURING        │
                        │  Agent Lingüista    │
                        │ Vectors BGE+ChromaDB│
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Hi ha zones grises?         │
                    │  SÍ  ──► 🟡 HEDY LAMARR    │
                    │        Agent Detective       │
                    │          LLM + Evidència     │
                    │  NO  ──► ometre             │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🔴 SERENA WILLIAMS  │
                        │    Agent Podi       │
                        │  Rànquing Ponderat  │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟤 STEVE JOBS          │
                        │  Agent Visionari    │
                        │  LLM + Anàlisi Buits│
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   🏆 JOHANNES GUTENBERG     │
                        │    Agent Editor     │
                        │ SQLite + Streamlit  │
                        └─────────────────────┘
```

### Llegenda d'agents

| Símbol | Agent | Tipus |
|--------|-------|-------|
| 🟣 | John von Neumann | Orquestrador — LangGraph |
| 🟠 | Ada Lovelace | Agent LLM — Intèrpret |
| 🔵 | Marie Curie | Determinista — Motor de regles |
| 🟢 | Alan Turing | Agent de Dades — BGE + ChromaDB |
| 🟡 | Hedy Lamarr | Agent LLM — Cadena de pensament |
| 🔴 | Serena Williams | Determinista — Fórmula de puntuació |
| 🟤 | Steve Jobs | Agent LLM — Anàlisi de buits |
| 🏆 | Johannes Gutenberg | Determinista — SQLite + Streamlit |

---

## Stack Tecnològic

| Component | Eina | Motiu |
|-----------|------|-------|
| Orquestració | LangGraph | Graf d'agents amb estat i condicional — no un pipeline fix |
| LLM | Llama 3 (Ollama) | Codi obert, local, sense cost d'API |
| Model d'embedding | **`intfloat/multilingual-e5-base`** | Model d'embedding multilingüe de codi obert. Converteix text en vectors de significat — les competències que signifiquen coses similars acaben com nombres similars. Gestiona anglès, espanyol, català i més sense preprocessament. Es fa servir tal qual, sense entrenament. |
| BD vectorial | ChromaDB | Cerca de veïns pròxims nativa, fitxer local, sense servidor |
| BD relacional | SQLite | Emmagatzema resultats d'anàlisi, puntuacions, descripcions de vacants i perfils de CV presentats |
| Validació de dades | Pydantic | Sortida estructurada i tipada dels agents LLM |
| Frontend | Streamlit | Interfície fosca personalitzada, i18n en 7 idiomes, vista de rànquing semàntic |

---

## Dades

- **Ofertes de feina:** 8 posicions a l'stack d'IA/Dades — des de Data Analyst Junior fins a AI Researcher i MLOps Engineer
- **CVs:** 10 perfils de candidats sintètics, cobrint una varietat de nivells de seniority, combinacions de competències i perfils

---

## Primers Passos — Reproduir aquest Projecte

Tot el que necessites per executar SmartCV localment, de zero a una app funcionant.

### 1. Requisits

| Requisit | Versió / Notes |
|---|---|
| Python | 3.10 o superior |
| RAM | 8 GB mínim (16 GB recomanat per a inferència LLM fluida) |
| Disc | ~5 GB lliures (pesos del model + índex ChromaDB) |
| SO | Linux, macOS, o Windows (WSL2 recomanat a Windows) |

---

### 2. Clonar i instal·lar dependències

```bash
git clone https://github.com/sonixse/Challenge3-SmartCV
cd Challenge3-SmartCV
pip install -r requirements.txt
```

---

### 3. Instal·lar Ollama i descarregar el LLM

Els agents que fan servir un model de llenguatge (Ada Lovelace, Hedy Lamarr, Steve Jobs) s'executen **localment** via [Ollama](https://ollama.com). No cal cap clau d'API.

```bash
# a) Instal·lar Ollama — descarrega des de https://ollama.com per al teu SO

# b) Descarregar el model (única vegada, ~4 GB)
ollama pull llama3

# c) Iniciar el servidor d'Ollama (mantén aquest terminal obert)
ollama serve
```

> Si veus un error de connexió en llançar l'app, Ollama no està en execució. Inicia'l amb `ollama serve` primer.

---

### 4. Indexar les ofertes de feina a ChromaDB

Alan Turing (Lingüista) fa servir ChromaDB + embeddings BGE per a la coincidència semàntica de competències. Cal indexar les dades de les vacants **una vegada** abans de la primera execució.

```bash
python scripts/index_vacancies.py
```

Això crea l'índex vectorial a `data/chroma/`. Només cal executar-ho una vegada (o de nou si canvien les dades de les vacants).

---

### 5. Llançar l'app

```bash
streamlit run app.py
```

Obre el teu navegador a `http://localhost:8501`, puja un CV en format PDF i fes clic a **Veure rànquing**.

---

### Llista de verificació abans de llançar

- [ ] `pip install -r requirements.txt` completat
- [ ] `ollama pull llama3` completat (única vegada, ~4 GB)
- [ ] `ollama serve` en execució en un terminal separat
- [ ] `python scripts/index_vacancies.py` executat sense errors

---

### Resolució de Problemes

| Símptoma | Causa | Solució |
|---|---|---|
| `Cannot connect to Ollama` | `ollama serve` no en execució | Executa'l en un terminal separat |
| `index_vacancies.py` falla | Ruta de ChromaDB absent | L'script crea `data/chroma/` automàticament; comprova els permisos d'escriptura |
| La primera execució és lenta (~30 s) | `intfloat/multilingual-e5-base` descarregant | Descàrrega única (~500 MB); les execucions posteriors fan servir el model en caché |
| `streamlit: command not found` | Streamlit no instal·lat | Torna a executar `pip install -r requirements.txt` |
| 0 coincidències per a un CV | Totes les ofertes eliminades pel Qualificador | Comprova que els noms d'idioma al CV estan en anglès (p. ex. "Spanish", no "Español") |

> El pipeline LangGraph es troba a `src/orchestrator/graph.py`. Els llindars i pesos dels agents es troben a `src/config.py`.

---

## Com Usar l'App

Un cop en funcionament, puja qualsevol CV en format PDF i fes clic a **Veure rànquing**. En qüestió de segons obtens:
- Coincidències de feina millor classificades amb puntuacions de compatibilitat semàntica
- Desglossament per competència: MATCH / ZONA GRISA (amb el raonament de Lamarr) / NO MATCH
- Anàlisi de buits personalitzada i coaching del SmartCV Assessor

---

## Per Què Això És un Sistema Multi-Agent Genuí

La restricció era clara: cap agent prefabricat. Aquí és com la complim — i anem més lluny:

- **7 agents, 7 rols** — cada agent té una responsabilitat única i definida amb entrades i sortides tipades
- **Activació condicional** — Lamarr només s'executa quan Turing troba ambigüitat. Johannes Gutenberg només renderitza quan Serena Williams té una puntuació final. El sistema no és un pipeline fix; s'adapta.
- **Separació deliberada LLM vs. codi** — Marie Curie i Serena Williams s'executen com a codi pur perquè les seves tasques són deterministes. Ada Lovelace, Lamarr i Steve Jobs fan servir LLMs perquè les seves tasques requereixen comprensió del llenguatge. Aquesta és una decisió arquitectònica, no un comportament per defecte.
- **L'orquestrador té estat** — Von Neumann fa un seguiment del que s'ha executat, del que està pendent i de com és el perfil del candidat actual a cada pas.

---

## Les 5 Dimensions d'Avaluació

**1. Innovació i Originalitat**
Embeddings semàntics + una capa de raonament condicional (Lamarr) + un agent de coaching de carrera personalitzat (Steve Jobs). La majoria d'eines de CV fan coincidència de paraules clau. Nosaltres fem comprensió semàntica amb explicabilitat i un full de ruta de desenvolupament. El nom dels agents no és decoració — és una estratègia de comunicació que fa l'arquitectura instantàniament memorable.

**2. Viabilitat i Escalabilitat**
Cada component és realista per a producció. ChromaDB escala a milions de vectors. BGE (el nostre model d'embedding) és prou ràpid per a consultes en temps real. SQLite canvia a PostgreSQL amb un canvi de configuració. L'app Streamlit es pot containeritzar i servir darrere d'un proxy invers. El patró d'orquestrador LangGraph funciona a qualsevol escala.

**3. Claredat i Concisió**
Un agent, una feina. L'arquitectura és llegible: pots assenyalar qualsevol node i explicar el que fa, per què és allà i per què fa servir l'eina que fa servir. La ramificació condicional és un únic punt de decisió (existeixen zones grises?).

**4. Col·laboració i Impacte**
Jobs fa el sistema valuós per als *candidats*, no sols per als reclutadors. Això converteix una eina de cribratge B2B en alguna cosa amb valor directe per a l'usuari — un assessor de carrera que et dóna una llista de tasques ordenada per al teu proper rol.

**5. Consideracions Ètiques**
- Cap atribut protegit (edat, gènere, nacionalitat) entra a la puntuació
- Les regles de Marie Curie són transparents i auditables — sense descalificacions silencioses de LLM
- Lamarr sempre cita la seva evidència — sense decisions de caixa negra en zones grises
- Els requisits d'idioma són restriccions operatives, no senyals culturals (gestionats per Marie Curie, no per Alan Turing)
- Tots els models s'executen localment — cap dada del candidat surt del sistema

---

## Què Construiríem amb Més Temps

- **Recuperació en dues etapes:** fer servir una versió més lleugera de BGE per a la recuperació ràpida dels 50 millors candidats, i després el model complet per al reordenament final. Així és com funcionen els sistemes de cerca semàntica en producció — ho vam prototipejar en teoria i ho implementaríem en una versió de producció.
- **Bucle de retroalimentació:** recopilar les decisions d'acceptació/rebuig dels reclutadors i ajustar els pesos de Serena Williams al llarg del temps. Aprenentatge en línia lleuger sense reentrenament.
- **Tauler d'explicabilitat:** Johannes Gutenberg ampliat amb un desglossament visual de cada component de la puntuació — útil per a auditories de RRHH i compliment normatiu.
- **Suport multilingüe de CVs:** BGE (el nostre model d'embedding) gestiona text multilingüe; Ada Lovelace s'amplaria per analitzar CVs nativament en espanyol, català i anglès sense preprocessament.
- **Capa d'API REST:** exposar el graf d'agents complet com una API perquè es pugui integrar en sistemes ATS existents. John von Neumann es converteix en un servei, no en un script.
- **Generació sintètica de CVs a escala:** generació programàtica de CVs de casos extrems per posar a prova Lamarr i calibrar els llindars d'Alan Turing.

---

## Descarregar dades externes de currículums

* https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
* Col·loca els fitxers a `data/kaggle/` una vegada fora de `data/`

## L'Equip

Cinc persones, dos tracks, un sistema.

**Backend · Agents · Orquestració · Pipeline**
Un enginyer industrial, un enginyer informàtic i un enginyer d'IA — les persones que van construir els agents i els van fer comunicar-se entre si.

**Frontend · Presentació · Documentació · Impacte**
Una especialista en biomedicina i una experta en negoci i tecnologia — les persones que van fer el sistema llegible, defensable i digne de presentar.

Els noms dels agents són un petit homenatge a aquesta estructura: cadascun porta l'esperit d'una disciplina en la qual algú d'aquest equip viu.

---

> *"No hem fet servir cap agent prefabricat. Hem dissenyat una arquitectura multi-agent personalitzada on cadascun dels set agents té un rol específic i justificat — des del processament del CV fins a la coincidència semàntica, el filtratge estricte, el raonament d'ambigüitat, la puntuació, el coaching i la visualització — coordinats per un orquestrador que adapta el flux en funció del que troba a cada pas."*
