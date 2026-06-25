# SmartCV: Un Sistema Multi-Agente para la Selección Semántica de Talento 🤝

> *"La persona adecuada para el puesto adecuado — comprendida, no solo emparejada."*

---

## ¿Qué es esto?

SmartCV es un sistema multi-agente personalizado que toma el CV de un candidato y encuentra las ofertas de trabajo que realmente le encajan — ordenadas por compatibilidad semántica real, no por coincidencia de palabras clave.

Lo hemos construido desde cero. Siete agentes especializados, cada uno con una sola responsabilidad, coordinados por un orquestador que adapta el flujo en función de lo que encuentra en cada paso. No se ha utilizado ningún agente prefabricado. Cada rol ha sido diseñado, justificado e implementado por el equipo.

El resultado se comporta más como un equipo de revisores expertos trabajando en paralelo que como un motor de búsqueda.

---

## El Problema

Las herramientas tradicionales de cribado de CVs hacen coincidir palabras clave. Si un CV dice `scikit-learn` y la oferta dice `supervised ML`, no hay coincidencia — aunque signifiquen lo mismo.

Lo solucionamos con **embeddings semánticos**: tanto los CVs como los requisitos de las ofertas se convierten en vectores que representan *significado*, no letras. Las competencias conceptualmente cercanas acaban matemáticamente cercanas. Luego filtramos los requisitos *imprescindibles*, ordenamos semánticamente y explicamos las diferencias.

Esto no es un pipeline. Es un sistema de razonamiento.

---

## Conoce los Agentes

Hemos dado a cada agente el nombre de una figura de la historia cuya contribución refleja exactamente lo que hace ese agente.

---

### 🟣 JOHN VON NEUMANN — El Orquestador
*John von Neumann diseñó la arquitectura del ordenador moderno: una unidad central que coordina memoria, procesamiento y E/S. Nuestro orquestador hace lo mismo.*

Construido sobre **LangGraph**, John von Neumann gestiona el estado completo del pipeline. Decide qué agentes se activan, gestiona la ramificación condicional (p. ej., solo despierta a Lamarr si existen competencias en zona gris) y garantiza que cada agente recibe exactamente el contexto que necesita.

```
Entrada: Subida del CV
Salida:  Coordina el grafo de agentes completo
Herram.: Grafo con estado LangGraph
```

---

### 🟠 ADA LOVELACE — El Agente Intérprete
*Ada Lovelace escribió el primer algoritmo — la primera vez que alguien convirtió una idea humana en instrucciones estructuradas que una máquina podía seguir. Este agente hace lo mismo: toma un CV, un documento profundamente humano, y lo convierte en datos estructurados sobre los que un sistema puede razonar.*

El Agente Intérprete lee el PDF en bruto, extrae un perfil de candidato estructurado — competencias, años de experiencia por ámbito, nivel y campo educativo, idiomas hablados — y lo valida en un esquema Pydantic. Los CVs son desordenados, multilingües e inconsistentes. Ada Lovelace lo gestiona todo.

```
Entrada: Texto bruto del CV (PDF → texto)
Salida:  CandidateProfile estructurado (Pydantic)
Herram.: LLM + validación Pydantic
```

---

### 🔵 MARIE CURIE — El Agente Calificador

El trabajo de Marie Curie estaba construido sobre un rigor científico absoluto. O el elemento era radiactivo o no lo era — sin aproximaciones, sin negociación. La primera persona en ganar dos Premios Nobel en dos ciencias diferentes no trataba zonas grises.

El Calificador aplica los requisitos imprescindibles de forma determinista siguiendo cuatro reglas:

1. Años de experiencia — el candidato debe igualar o superar el mínimo de la vacante
2. Nivel educativo — verificado contra una jerarquía (Sin titulación → Grado → Máster → Doctorado)
3. Idiomas requeridos — cada idioma verificado por nombre y nivel MCER mínimo
4. Coincidencia exacta de competencias — una bonificación suave por coincidencias directas de nombre, antes de que Alan Turing realice la comparación semántica

Se ejecuta como código puro — rápido, auditable e inmune a las alucinaciones de los LLM. Si una vacante requiere inglés B2 y el candidato tiene A1, la respuesta es no. No "probablemente no." No.

> **Por qué los idiomas van aquí y no en los embeddings:** Un modelo semántico podría situar "Catalán" cerca de "Español" y conceder una coincidencia parcial. Pero los requisitos de idioma son restricciones operativas, no preferencias difusas. El Calificador aplica esto — que es también la decisión éticamente correcta.

```
Entrada: CandidateProfile + requisitos de la vacante
Salida:  bandera pass/fail + puntuación (0..4) + lista failed_checks + lista de motivos
         failed_checks indica a Steve Jobs exactamente qué reglas ha fallado el candidato,
         permitiendo un coaching dirigido en lugar de un análisis de brechas genérico
Herram.: Motor de reglas determinista (Python)
```

---

### 🟢 ALAN TURING — El Agente Lingüista
*Alan Turing preguntó si las máquinas podían entender el significado. Este agente es la respuesta.*

El Agente Lingüista realiza la comparación semántica de competencias: convierte cada competencia requerida de la vacante en un vector de embedding y lo compara con los vectores de competencias del candidato almacenados en **ChromaDB**. Para generar estos vectores, usamos **`intfloat/multilingual-e5-base`** — un modelo de embedding multilingüe de código abierto y preentrenado de HuggingFace. Piénsalo como un componente que lee un fragmento de texto y lo convierte en una lista de números que representa su *significado*. Las competencias que significan cosas similares acaban como números similares. La similitud coseno produce tres categorías:

| Categoría | Umbral | Significado |
|-----------|--------|-------------|
| ✅ MATCH | > 0.87 | Semánticamente equivalente ("PySpark" ≈ "procesamiento de datos distribuido") |
| ⚠️ ZONA GRIS | 0.84 – 0.87 | Posiblemente relacionado — necesita razonamiento |
| ❌ NO MATCH | < 0.84 | No cubierto |

> **Sobre los umbrales:** Los valores 0.87 y 0.84 son puntos de partida heurísticos, informados por prácticas habituales en tareas de similitud semántica. Están definidos en `src/config.py` (`LINGUIST_MATCH_THRESHOLD` y `LINGUIST_GREY_THRESHOLD`) y se pueden ajustar sin tocar ningún otro fichero. Los ajustamos basándonos en tres señales: (1) **falsos positivos** — si competencias claramente no relacionadas acaban en MATCH, subimos el umbral superior; (2) **falsos negativos** — si competencias obviamente equivalentes como "Python" vs "Python 3" caen en ZONA GRIS, lo bajamos; (3) **volumen de zona gris** — si demasiadas competencias acaban en ZONA GRIS, el Detective se convierte en un cuello de botella, así que ajustamos hasta que la zona gris capture solo casos genuinamente ambiguos.

```
Entrada: Competencias del candidato + requisitos de competencias de la vacante
Salida:  Clasificación por competencia (MATCH / ZONA GRIS / NO MATCH)
Herram.: intfloat/multilingual-e5-base + búsqueda de vecinos próximos en ChromaDB
```

---

### 🟡 HEDY LAMARR — El Agente Detective
*Hedy Lamarr inventó el espectro de salto de frecuencia — la capacidad de detectar una señal clara navegando inteligentemente por ruido y ambigüedad. La base del WiFi, Bluetooth y GPS. Este agente hace lo mismo: encuentra la señal real en competencias demasiado ruidosas para una coincidencia simple.*

El Agente Detective gestiona el razonamiento de ambigüedad — solo se activa cuando Alan Turing marca competencias como ZONA GRIS. Lee el contexto real del CV — descripciones de proyectos, historial laboral, menciones de herramientas — y juzga si el candidato probablemente tiene la competencia de forma implícita. Siempre cita la evidencia específica que ha utilizado. Sin decisiones silenciosas.

```
Entrada: Competencias en zona gris + contexto completo del CV
Salida:  Veredicto MATCH / NO MATCH por competencia + evidencia citada
Herram.: LLM con cadena de pensamiento
Activac.: Condicional — solo cuando existen zonas grises
```

---

### 🔴 SERENA WILLIAMS — El Agente Podio
*Serena Williams dominó el ranking de la WTA durante más de 20 años. Su legado no son solo los trofeos — son los puntos, acumulados de forma consistente, implacable, en cada superficie y cada era. Este agente hace lo mismo: agrega cada señal en una puntuación final y ordena sin dudar.*

El Agente Podio gestiona la puntuación y el ranking: agrega las salidas de Marie Curie, Alan Turing y Lamarr en una puntuación de compatibilidad ponderada por vacante. Los pesos se calibran por categoría de competencia (imprescindibles vs. valoradas) y seniority del rol. El resultado es una lista ordenada de vacantes, cada una con una puntuación transparente y desglosada.

**Gestión del caso sin coincidencia.** El Agente Podio nunca devuelve un resultado vacío. Incluso cuando las puntuaciones son universalmente bajas — es decir, cuando el candidato no encaja bien en ninguna vacante — el ranking se elabora y se presenta igualmente. Una puntuación baja no es un punto muerto; es la entrada más honesta y útil que el Agente Visionario podría recibir jamás. Cuanto peor es la coincidencia, más rica es la salida de coaching. Un candidato sin coincidencias fuertes no ve una pantalla en blanco — ve una hoja de ruta precisa y personalizada de exactamente qué tiene que construir para ser competitivo. El sistema convierte su peor escenario en su salida más valiosa.

```
Entrada: Resultados de calificación + resultados de coincidencia de competencias (todos los agentes)
Salida:  Puntuación de compatibilidad (0–100) por vacante, ordenada — siempre, independientemente de la puntuación
Herram.: Fórmula de puntuación ponderada (Python)
```

---

### 🟤 STEVE JOBS — El Agente Visionario
*Steve Jobs nunca aceptó "suficientemente bueno". Identificaba brechas, eliminaba el ruido y decía a la gente exactamente lo que necesitaba construir — y por qué importaba. Este agente hace lo mismo para tu carrera.*

El Agente Visionario actúa como coach de carrera: recibe el análisis de brechas (competencias ausentes o débiles en las vacantes mejor clasificadas) y genera recomendaciones personalizadas y priorizadas. Tiene en cuenta lo que el candidato ya sabe y sugiere los pasos de mayor impacto — no una lista genérica de competencias, sino un camino de desarrollo razonado.

Cuando las puntuaciones son altas, Steve Jobs afina — *"una competencia más y pasas del rango 3 al rango 1"*. Cuando las puntuaciones son universalmente bajas, Steve Jobs toma el control completamente: reenfoca toda la salida de un ranking a un plan de desarrollo, diciéndole al candidato no solo lo que le falta sino en qué orden abordarlo y por qué — priorizado por impacto en la empleabilidad en todas las vacantes simultáneamente.

> **Ejemplo de buena coincidencia:** *"Tienes las bases de ML para roles de Data Scientist. Añadir MLflow (ya usas Docker — es una rampa de 2 días) te haría competitivo para 3 vacantes más de esta lista."*

> **Ejemplo de ninguna coincidencia:** *"Ninguna de las vacantes actuales encaja bien por ahora — pero estás más cerca de lo que crees. Tu base de Python cubre el 60% de lo que requiere Data Analyst Junior. Céntrate primero en SQL y Power BI: esas dos competencias desbloquean 5 de las 8 vacantes del conjunto de datos. Podrías ser competitivo en 3 meses."*

```
Entrada: CandidateProfile + vacantes principales + análisis de brechas
Salida:  Recomendaciones de competencias ordenadas con justificación de impacto
Herram.: LLM con salida estructurada
```

---

### 🏆 JOHANNES GUTENBERG — El Agente Editor
*Johannes Gutenberg inventó la imprenta — el acto original de hacer la información visible y accesible para las masas. Johannes Gutenberg convierte la salida del pipeline en algo que un humano puede realmente leer y sobre lo que puede actuar.*

El Agente Editor gestiona los resultados y la visualización: persiste todos los resultados en **SQLite** — incluyendo los resultados del análisis, las descripciones de las vacantes y el perfil del CV presentado — estructura la salida para la interfaz e impulsa lo que el candidato realmente ve: la lista ordenada, el desglose por competencia y la salida de coaching de Steve Jobs — todo renderizado en una interfaz **Streamlit** personalizada.

```
Entrada: Resultados finales ordenados + salida de coaching
Salida:  Interfaz Streamlit renderizada para el candidato
Herram.: SQLite + Streamlit
```

---

## Arquitectura Completa del Sistema

```
                        ┌─────────────────────┐
                        │ Interfaz Streamlit  │
                        │  (el candidato sube │
                        │     el CV en PDF)   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟣 JOHN VON NEUMANN   │
                        │      Orquestador    │
                        │    (LangGraph)      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               │                   │                   │
    ┌──────────▼──────────┐        │        ┌──────────▼──────────┐
    │  🟠 ADA LOVELACE     │        │        │   🔵 MARIE CURIE      │
    │  Agente Intérprete  │        │        │ Agente Calificador  │
    │  LLM + Pydantic     │        │        │   Motor de Reglas   │
    └──────────┬──────────┘        │        └──────────┬──────────┘
               │                   │                   │
               └───────────────────▼───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟢 ALAN TURING        │
                        │  Agente Lingüista   │
                        │ Vectores BGE+ChromaDB│
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  ¿Hay zonas grises?          │
                    │  SÍ  ──► 🟡 HEDY LAMARR    │
                    │        Agente Detective      │
                    │          LLM + Evidencia     │
                    │  NO  ──► omitir            │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🔴 SERENA WILLIAMS  │
                        │   Agente Podio      │
                        │  Ranking Ponderado  │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟤 STEVE JOBS          │
                        │  Agente Visionario  │
                        │  LLM + Análisis Brechas│
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   🏆 JOHANNES GUTENBERG     │
                        │    Agente Editor    │
                        │ SQLite + Streamlit  │
                        └─────────────────────┘
```

### Leyenda de agentes

| Símbolo | Agente | Tipo |
|---------|--------|------|
| 🟣 | John von Neumann | Orquestador — LangGraph |
| 🟠 | Ada Lovelace | Agente LLM — Intérprete |
| 🔵 | Marie Curie | Determinista — Motor de reglas |
| 🟢 | Alan Turing | Agente de Datos — BGE + ChromaDB |
| 🟡 | Hedy Lamarr | Agente LLM — Cadena de pensamiento |
| 🔴 | Serena Williams | Determinista — Fórmula de puntuación |
| 🟤 | Steve Jobs | Agente LLM — Análisis de brechas |
| 🏆 | Johannes Gutenberg | Determinista — SQLite + Streamlit |

---

## Stack Tecnológico

| Componente | Herramienta | Motivo |
|------------|-------------|--------|
| Orquestación | LangGraph | Grafo de agentes con estado y condicional — no un pipeline fijo |
| LLM | Llama 3 (Ollama) | Código abierto, local, sin coste de API |
| Modelo de embedding | **`intfloat/multilingual-e5-base`** | Modelo de embedding multilingüe de código abierto. Convierte texto en vectores de significado — las competencias que significan cosas similares acaban como números similares. Gestiona inglés, español, catalán y más sin preprocesamiento. Se usa tal cual, sin entrenamiento. |
| BD vectorial | ChromaDB | Búsqueda de vecinos próximos nativa, fichero local, sin servidor |
| BD relacional | SQLite | Almacena resultados de análisis, puntuaciones, descripciones de vacantes y perfiles de CV presentados |
| Validación de datos | Pydantic | Salida estructurada y tipada de los agentes LLM |
| Frontend | Streamlit | Interfaz oscura personalizada, i18n en 7 idiomas, vista de ranking semántico |

---

## Datos

- **Ofertas de trabajo:** 8 posiciones en el stack de IA/Datos — desde Data Analyst Junior hasta AI Researcher y MLOps Engineer
- **CVs:** 10 perfiles de candidatos sintéticos, cubriendo una variedad de niveles de seniority, combinaciones de competencias y perfiles

---

## Primeros Pasos — Reproducir este Proyecto

Todo lo que necesitas para ejecutar SmartCV localmente, de cero a una app funcionando.

### 1. Requisitos

| Requisito | Versión / Notas |
|---|---|
| Python | 3.10 o superior |
| RAM | 8 GB mínimo (16 GB recomendado para inferencia LLM fluida) |
| Disco | ~5 GB libres (pesos del modelo + índice ChromaDB) |
| SO | Linux, macOS, o Windows (WSL2 recomendado en Windows) |

---

### 2. Clonar e instalar dependencias

```bash
git clone https://github.com/sonixse/Challenge3-SmartCV
cd Challenge3-SmartCV
pip install -r requirements.txt
```

---

### 3. Instalar Ollama y descargar el LLM

Los agentes que usan un modelo de lenguaje (Ada Lovelace, Hedy Lamarr, Steve Jobs) se ejecutan **localmente** via [Ollama](https://ollama.com). No se necesita ninguna clave de API.

```bash
# a) Instalar Ollama — descarga desde https://ollama.com para tu SO

# b) Descargar el modelo (única vez, ~4 GB)
ollama pull llama3

# c) Iniciar el servidor de Ollama (mantén este terminal abierto)
ollama serve
```

> Si ves un error de conexión al lanzar la app, Ollama no está en ejecución. Inícialo con `ollama serve` primero.

---

### 4. Indexar las ofertas de trabajo en ChromaDB

Alan Turing (Lingüista) usa ChromaDB + embeddings BGE para la coincidencia semántica de competencias. Hay que indexar los datos de las vacantes **una vez** antes de la primera ejecución.

```bash
python scripts/index_vacancies.py
```

Esto crea el índice vectorial en `data/chroma/`. Solo hay que ejecutarlo una vez (o de nuevo si cambian los datos de las vacantes).

---

### 5. Lanzar la app

```bash
streamlit run app.py
```

Abre tu navegador en `http://localhost:8501`, sube un CV en formato PDF y haz clic en **Ver ranking**.

---

### Lista de verificación antes de lanzar

- [ ] `pip install -r requirements.txt` completado
- [ ] `ollama pull llama3` completado (única vez, ~4 GB)
- [ ] `ollama serve` en ejecución en un terminal separado
- [ ] `python scripts/index_vacancies.py` ejecutado sin errores

---

### Resolución de Problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `Cannot connect to Ollama` | `ollama serve` no en ejecución | Ejecútalo en un terminal separado |
| `index_vacancies.py` falla | Ruta de ChromaDB ausente | El script crea `data/chroma/` automáticamente; comprueba los permisos de escritura |
| La primera ejecución es lenta (~30 s) | `intfloat/multilingual-e5-base` descargando | Descarga única (~500 MB); las ejecuciones posteriores usan el modelo en caché |
| `streamlit: command not found` | Streamlit no instalado | Vuelve a ejecutar `pip install -r requirements.txt` |
| 0 coincidencias para un CV | Todas las ofertas eliminadas por el Calificador | Comprueba que los nombres de idioma en el CV están en inglés (p. ej. "Spanish", no "Español") |

> El pipeline LangGraph se encuentra en `src/orchestrator/graph.py`. Los umbrales y pesos de los agentes se encuentran en `src/config.py`.

---

## Cómo Usar la App

Una vez en funcionamiento, sube cualquier CV en formato PDF y haz clic en **Ver ranking**. En cuestión de segundos obtienes:
- Coincidencias de trabajo mejor clasificadas con puntuaciones de compatibilidad semántica
- Desglose por competencia: MATCH / ZONA GRIS (con el razonamiento de Lamarr) / NO MATCH
- Análisis de brechas personalizado y coaching del SmartCV Assessor

---

## Por Qué Esto Es un Sistema Multi-Agente Genuino

La restricción era clara: ningún agente prefabricado. Así es como la cumplimos — y vamos más lejos:

- **7 agentes, 7 roles** — cada agente tiene una responsabilidad única y definida con entradas y salidas tipadas
- **Activación condicional** — Lamarr solo se ejecuta cuando Turing encuentra ambigüedad. Johannes Gutenberg solo renderiza cuando Serena Williams tiene una puntuación final. El sistema no es un pipeline fijo; se adapta.
- **Separación deliberada LLM vs. código** — Marie Curie y Serena Williams se ejecutan como código puro porque sus tareas son deterministas. Ada Lovelace, Lamarr y Steve Jobs usan LLMs porque sus tareas requieren comprensión del lenguaje. Esta es una decisión arquitectónica, no un comportamiento por defecto.
- **El orquestador tiene estado** — Von Neumann hace un seguimiento de lo que se ha ejecutado, de lo que está pendiente y de cómo es el perfil del candidato actual en cada paso.

---

## Las 5 Dimensiones de Evaluación

**1. Innovación y Originalidad**
Embeddings semánticos + una capa de razonamiento condicional (Lamarr) + un agente de coaching de carrera personalizado (Steve Jobs). La mayoría de herramientas de CV hacen coincidencia de palabras clave. Nosotros hacemos comprensión semántica con explicabilidad y una hoja de ruta de desarrollo. El nombre de los agentes no es decoración — es una estrategia de comunicación que hace la arquitectura instantáneamente memorable.

**2. Viabilidad y Escalabilidad**
Cada componente es realista para producción. ChromaDB escala a millones de vectores. BGE (nuestro modelo de embedding) es suficientemente rápido para consultas en tiempo real. SQLite cambia a PostgreSQL con un cambio de configuración. La app Streamlit se puede containerizar y servir detrás de un proxy inverso. El patrón de orquestador LangGraph funciona a cualquier escala.

**3. Claridad y Concisión**
Un agente, un trabajo. La arquitectura es legible: puedes señalar cualquier nodo y explicar lo que hace, por qué está ahí y por qué usa la herramienta que usa. La ramificación condicional es un único punto de decisión (¿existen zonas grises?).

**4. Colaboración e Impacto**
Jobs hace el sistema valioso para los *candidatos*, no solo para los reclutadores. Esto convierte una herramienta de cribado B2B en algo con valor directo para el usuario — un asesor de carrera que te da una lista de tareas ordenada para tu próximo rol.

**5. Consideraciones Éticas**
- Ningún atributo protegido (edad, género, nacionalidad) entra en la puntuación
- Las reglas de Marie Curie son transparentes y auditables — sin descalificaciones silenciosas de LLM
- Lamarr siempre cita su evidencia — sin decisiones de caja negra en zonas grises
- Los requisitos de idioma son restricciones operativas, no señales culturales (gestionados por Marie Curie, no por Alan Turing)
- Todos los modelos se ejecutan localmente — ningún dato del candidato sale del sistema

---

## Qué Construiríamos con Más Tiempo

- **Recuperación en dos etapas:** usar una versión más ligera de BGE para la recuperación rápida de los 50 mejores candidatos, y luego el modelo completo para el reordenamiento final. Así es como funcionan los sistemas de búsqueda semántica en producción — lo prototipamos en teoría y lo implementaríamos en una versión de producción.
- **Bucle de retroalimentación:** recopilar las decisiones de aceptación/rechazo de los reclutadores y ajustar los pesos de Serena Williams a lo largo del tiempo. Aprendizaje en línea ligero sin reentrenamiento.
- **Panel de explicabilidad:** Johannes Gutenberg ampliado con un desglose visual de cada componente de la puntuación — útil para auditorías de RRHH y cumplimiento normativo.
- **Soporte multilingüe de CVs:** BGE (nuestro modelo de embedding) gestiona texto multilingüe; Ada Lovelace se ampliaría para analizar CVs nativamente en español, catalán e inglés sin preprocesamiento.
- **Capa de API REST:** exponer el grafo de agentes completo como una API para que pueda integrarse en sistemas ATS existentes. John von Neumann se convierte en un servicio, no en un script.
- **Generación sintética de CVs a escala:** generación programática de CVs de casos extremos para poner a prueba a Lamarr y calibrar los umbrales de Alan Turing.

---

## Descargar datos externos de currículums

* https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
* Coloca los ficheros en `data/kaggle/` una vez fuera de `data/`

## El Equipo

Cinco personas, dos tracks, un sistema.

**Backend · Agentes · Orquestación · Pipeline**
Un ingeniero industrial, un ingeniero informático y un ingeniero de IA — las personas que construyeron los agentes y los hicieron comunicarse entre sí.

**Frontend · Presentación · Documentación · Impacto**
Una especialista en biomedicina y una experta en negocio y tecnología — las personas que hicieron el sistema legible, defendible y digno de presentar.

Los nombres de los agentes son un pequeño homenaje a esa estructura: cada uno lleva el espíritu de una disciplina en la que alguien de este equipo vive.

---

> *"No hemos utilizado ningún agente prefabricado. Hemos diseñado una arquitectura multi-agente personalizada donde cada uno de los siete agentes tiene un rol específico y justificado — desde el procesamiento del CV hasta la coincidencia semántica, el filtrado estricto, el razonamiento de ambigüedad, la puntuación, el coaching y la visualización — coordinados por un orquestador que adapta el flujo en función de lo que encuentra en cada paso."*
