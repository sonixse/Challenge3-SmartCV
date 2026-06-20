# Conoce SmartCV: Un Sistema Multi-Agente para la Selección Semántica de Talento 🤝

> *"La persona adecuada para el puesto adecuado — comprendida, no solo emparejada."*

---

## ¿Qué es esto?

SmartCV es un sistema multi-agente hecho a medida que toma el CV de un candidato y encuentra las ofertas de trabajo que realmente le encajan — ordenadas por compatibilidad semántica real, no por coincidencia de palabras clave.

Lo hemos construido desde cero. Siete agentes especializados, cada uno con una única responsabilidad, coordinados por un orquestador que adapta el flujo en función de lo que encuentra en cada paso. No se ha utilizado ningún agente preconstruido. Cada rol ha sido diseñado, justificado e implementado por el equipo.

El resultado se parece más a un equipo de revisores expertos trabajando en paralelo que a un motor de búsqueda.

---

## El Problema

Las herramientas tradicionales de selección de CVs buscan por palabras clave. Si un CV dice `scikit-learn` y la oferta dice `ML supervisado`, es un fallo — aunque signifiquen lo mismo.

Lo resolvemos con **embeddings semánticos**: tanto los CVs como los requisitos de las ofertas se convierten en vectores que representan el *significado*, no las letras. Las skills conceptualmente cercanas acaban matemáticamente cercanas. Después filtramos las restricciones *must-have*, ordenamos semánticamente y explicamos los gaps.

Esto no es un pipeline. Es un sistema de razonamiento.

---

## Conoce los Agentes

Hemos nombrado a cada agente con el nombre de una figura de la historia cuya contribución refleja exactamente lo que hace ese agente.

---

### 🟣 JOHN VON NEUMANN — El Orquestador
*John von Neumann diseñó la arquitectura del ordenador moderno: una unidad central que coordina memoria, procesamiento y E/S. Nuestro orquestador hace exactamente lo mismo.*

Construido sobre **LangGraph**, John von Neumann gestiona el estado completo del pipeline. Decide qué agentes se activan, gestiona las ramas condicionales (p. ej., solo despierta a Lamarr si hay skills en zona gris) y se asegura de que cada agente recibe exactamente el contexto que necesita.

```
Input:  Subida del CV
Output: Coordina el grafo completo de agentes
Herramienta: Grafo de estado de LangGraph
```

---

### 🟠 ADA LOVELACE — El Agente Intérprete
*Ada Lovelace escribió el primer algoritmo — la primera vez que alguien convirtió una idea humana en instrucciones estructuradas que una máquina podía seguir. Este agente hace lo mismo: toma un CV, un documento profundamente humano, y lo convierte en datos estructurados sobre los que un sistema puede razonar.*

El Agente Intérprete lee el PDF en bruto, extrae un perfil estructurado del candidato — skills, años de experiencia por dominio, nivel y campo de formación, idiomas hablados — y lo valida en un esquema Pydantic. Los CVs son desordenados, multilingües e inconsistentes. Ada Lovelace se encarga de todo.

```
Input:  Texto bruto del CV (PDF → string)
Output: CandidateProfile estructurado (Pydantic)
Herramienta: LLM + validación Pydantic
```

---

### 🔵 MARIE CURIE — El Agente Calificador
*El trabajo de Marie Curie se basaba en el rigor científico absoluto. O el elemento era radiactivo o no lo era — sin aproximaciones, sin negociación. La primera persona en ganar dos Premios Nobel en dos ciencias diferentes no trataba en zonas grises.*

El Calificador aplica restricciones must-have de manera determinista: años mínimos de experiencia, nivel de formación e idiomas requeridos. Se ejecuta como código puro — rápido, auditable e inmune a las alucinaciones del LLM. Si una vacante requiere inglés B2 y el candidato tiene A1, la respuesta es no. No "probablemente no." No.

> **Por qué los idiomas van aquí y no en embeddings:** Un modelo semántico podría colocar "Catalán" cerca de "Español" y otorgar una coincidencia parcial. Pero los requisitos de idioma son restricciones operativas, no preferencias difusas. El Calificador las aplica — y es también la decisión éticamente correcta.

```
Input:  CandidateProfile + Requisitos de la vacante
Output: Indicador de paso/fallo + penalización/bonificación de puntuación
Herramienta: Motor de reglas determinista (Python)
```

---

### 🟢 ALAN TURING — El Agente Lingüista
*Alan Turing preguntó si las máquinas podían entender el significado. Este agente es la respuesta.*

El Agente Lingüista realiza la comparación semántica de skills: convierte cada skill requerida de la vacante en un vector de embedding y los compara con los vectores de skills del candidato almacenados en **ChromaDB**. Para generar estos vectores usamos **BGE** (un modelo de IA open-source pre-entrenado de HuggingFace — piensa en él como el componente que lee un trozo de texto y lo convierte en una lista de números que representa su *significado*. Las skills con significados similares acaban como números similares). La similitud coseno produce tres categorías:

| Categoría | Umbral | Significado |
|-----------|--------|-------------|
| ✅ MATCH | > 0.85 | Semánticamente equivalente ("PySpark" ≈ "procesamiento de datos distribuidos") |
| ⚠️ ZONA GRIS | 0.60 – 0.85 | Posiblemente relacionado — necesita razonamiento |
| ❌ NO MATCH | < 0.60 | No cubierto |

> **Sobre los umbrales:** Los valores 0.85 y 0.60 son puntos de partida heurísticos, basados en la práctica habitual en tareas de similitud semántica. Los ajustamos en función de tres señales: (1) **falsos positivos** — si skills claramente no relacionadas aterrizan en MATCH, subimos el umbral superior; (2) **falsos negativos** — si skills obviamente equivalentes como "Python" vs "Python 3" caen en ZONA GRIS en lugar de MATCH, lo bajamos; (3) **volumen de zona gris** — si demasiadas skills acaban en ZONA GRIS, el Agente Detective se convierte en un cuello de botella y ralentiza el sistema, por lo que ajustamos los límites hasta que la zona gris captura solo los casos genuinamente ambiguos. El objetivo es una zona gris pequeña, significativa y que valga el coste de llamar a un LLM.

```
Input:  Skills del candidato + Requisitos de skills de la vacante
Output: Clasificación por skill (MATCH / ZONA GRIS / NO MATCH)
Herramienta: BGE (modelo de vectores de significado) + búsqueda de vecinos cercanos en ChromaDB
```

---

### 🟡 HEDY LAMARR — El Agente Detective
*Hedy Lamarr inventó el espectro de salto de frecuencia — la capacidad de detectar una señal clara navegando inteligentemente a través del ruido y la ambigüedad. La base del WiFi, Bluetooth y GPS. Este agente hace lo mismo: encuentra la señal real en skills demasiado ruidosas para una coincidencia simple.*

El Agente Detective gestiona el razonamiento de ambigüedad — solo se activa cuando Alan Turing marca skills como ZONA GRIS. Lee el contexto real del CV — descripciones de proyectos, historial laboral, menciones de herramientas — y juzga si el candidato probablemente tiene la skill de manera implícita. Siempre cita la evidencia específica que ha utilizado. Ninguna decisión silenciosa.

```
Input:  Skills en zona gris + contexto completo del CV
Output: Veredicto MATCH / NO MATCH por skill + evidencia citada
Herramienta: LLM con cadena de pensamiento
Activación: Condicional — solo cuando existen zonas grises
```

---

### 🔴 SERENA WILLIAMS — El Agente Podio
*Serena Williams dominó el ranking WTA durante más de 20 años. Su legado no son solo los trofeos — son los puntos, acumulados de manera consistente, implacable, en todas las superficies y en todas las épocas. Este agente hace lo mismo: agrega cada señal en una puntuación final y ordena sin dudar.*

El Agente Podio gestiona la puntuación y el ranking: agrega las salidas de Marie Curie, Alan Turing y Lamarr en una puntuación de compatibilidad ponderada por vacante. Los pesos se calibran por categoría de skill (must-have vs. nice-to-have) y seniority del rol. El resultado es una lista ordenada de vacantes, cada una con una puntuación transparente y descompuesta.

**Gestión del caso sin coincidencias.** El Agente Podio nunca devuelve un resultado vacío. Incluso cuando las puntuaciones son universalmente bajas — es decir, que el candidato no encaja bien con ninguna vacante — el ranking se produce y se muestra igualmente. Una puntuación baja no es un callejón sin salida; es la entrada más honesta y útil que el Agente Visionario podría recibir. Cuanto peor es la coincidencia, más rica es la salida de coaching. Un candidato sin ninguna coincidencia fuerte no ve una pantalla en blanco — ve una hoja de ruta precisa y personalizada de exactamente lo que tiene que construir para ser competitivo. El sistema convierte su peor escenario en su salida más valiosa.

```
Input:  Resultados de calificación + resultados de coincidencia de skills (todos los agentes)
Output: Puntuación de compatibilidad (0–100) por vacante, ordenada — siempre, independientemente de la puntuación
Herramienta: Fórmula de puntuación ponderada (Python)
```

---

### 🟤 STEVE JOBS — El Agente Visionario
*Steve Jobs nunca aceptó el "suficientemente bueno." Identificaba los gaps, eliminaba el ruido y decía a la gente exactamente lo que necesitaba construir — y por qué importaba. Este agente hace lo mismo para tu carrera.*

El Agente Visionario actúa como coach de carrera: recibe el análisis de gaps (skills que faltan o que son débiles entre las vacantes mejor clasificadas) y genera recomendaciones personalizadas y priorizadas. Tiene en cuenta lo que el candidato ya sabe y sugiere los próximos pasos de alto impacto — no una lista genérica de skills, sino un camino de desarrollo razonado.

Cuando las puntuaciones son altas, Steve Jobs afina — *"una skill más y pasas del rango 3 al rango 1"*. Cuando las puntuaciones son universalmente bajas, Steve Jobs toma el control completamente: reencuadra toda la salida de un ranking a un plan de desarrollo, diciéndole al candidato no solo lo que le falta sino en qué orden abordarlo y por qué — priorizado por impacto en la empleabilidad en todas las vacantes simultáneamente.

> **Ejemplo con buena coincidencia:** *"Tienes las bases de ML para roles de Data Scientist. Añadir MLflow (ya usas Docker — es una rampa de 2 días) te haría competitivo para 3 vacantes más de esta lista."*

> **Ejemplo sin coincidencia:** *"Ninguna de las vacantes actuales es un buen encaje todavía — pero estás más cerca de lo que crees. Tu base de Python cubre el 60% de lo que requiere Data Analyst Junior. Céntrate primero en SQL y Power BI: esas dos skills desbloquean 5 de las 8 vacantes del dataset. Podrías ser competitivo en 3 meses."*

```
Input:  CandidateProfile + vacantes principales + análisis de gaps
Output: Recomendaciones de skills ordenadas con justificación de impacto
Herramienta: LLM con salida estructurada
```

---

### 🏆 JOHANNES GUTENBERG — El Agente Editor
*Johannes Gutenberg inventó la imprenta — el acto original de hacer la información visible y accesible para las masas. Johannes Gutenberg convierte la salida del pipeline en algo que un humano puede leer y sobre lo que puede actuar.*

El Agente Editor gestiona los resultados y la visualización: persiste todos los resultados en **SQLite** — incluyendo los resultados del análisis, las descripciones de las vacantes y el perfil del CV enviado — estructura la salida para la interfaz y dirige lo que el candidato ve realmente: la lista ordenada, el desglose por skill y la salida de coaching de Steve Jobs — todo renderizado en una interfaz limpia de **Gradio**.

> **¿Por qué Gradio y no Streamlit?** Gradio es nativo de HuggingFace, tiene soporte de primera clase para subida de archivos, salida estilo chat y UX para demos de modelos de IA. Como usamos BGE (nuestro modelo de embedding open-source) de HuggingFace y la salida del Coach es conversacional, el conjunto de componentes de Gradio se adapta a este caso de uso de manera más natural que el paradigma de dashboard de datos de Streamlit.

```
Input:  Resultados finales ordenados + salida de coaching
Output: Interfaz Gradio renderizada para el candidato
Herramienta: SQLite + Gradio
```

---

## Arquitectura Completa del Sistema

```
                        ┌─────────────────────┐
                        │  Interfaz Gradio    │
                        │  (el candidato sube │
                        │     CV en PDF)      │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ 🟣 JOHN VON NEUMANN │
                        │    Orquestador      │
                        │    (LangGraph)      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               │                   │                   │
    ┌──────────▼──────────┐        │        ┌──────────▼──────────┐
    │  🟠 ADA LOVELACE    │        │        │   🔵 MARIE CURIE    │
    │  Agente Intérprete  │        │        │  Agente Calificador │
    │  LLM + Pydantic     │        │        │   Motor de Reglas   │
    └──────────┬──────────┘        │        └──────────┬──────────┘
               │                   │                   │
               └───────────────────▼───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟢 ALAN TURING   │
                        │  Agente Lingüista   │
                        │ Vectores BGE+ChromaDB│
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  ¿Zonas grises encontradas?  │
                    │  SÍ ──► 🟡 HEDY LAMARR     │
                    │        Agente Detective      │
                    │          LLM + Evidencia     │
                    │  NO  ──► omitir             │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🔴 SERENA WILLIAMS │
                        │   Agente Podio      │
                        │  Ranking Ponderado  │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟤 STEVE JOBS    │
                        │  Agente Visionario  │
                        │  LLM + Análisis Gaps│
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🏆 J. GUTENBERG    │
                        │    Agente Editor    │
                        │  SQLite + Gradio    │
                        └─────────────────────┘
```

### Leyenda de agentes

| Símbolo | Agente | Tipo |
|---------|--------|------|
| 🟣 | John von Neumann | Orquestador — LangGraph |
| 🟠 | Ada Lovelace | Agente LLM — Intérprete |
| 🔵 | Marie Curie | Determinista — Motor de reglas |
| 🟢 | Alan Turing | Agente de datos — BGE + ChromaDB |
| 🟡 | Hedy Lamarr | Agente LLM — Cadena de pensamiento |
| 🔴 | Serena Williams | Determinista — Fórmula de puntuación |
| 🟤 | Steve Jobs | Agente LLM — Análisis de gaps |
| 🏆 | Johannes Gutenberg | Determinista — SQLite + Gradio |

---

## Stack Tecnológico

| Componente | Herramienta | Motivo |
|------------|-------------|--------|
| Orquestación | LangGraph | Grafo de agentes con estado y condicional — no es un pipeline fijo |
| LLM | Llama 3 (Ollama) | Open source, local, coste cero de API |
| Modelo de embeddings | **BGE** (BAAI/bge-base-en-v1.5) | Modelo de IA open-source que convierte texto en vectores de significado. Pre-entrenado por HuggingFace — lo usamos tal cual, sin entrenamiento. Top en tareas de búsqueda semántica. |
| Base de datos vectorial | ChromaDB | Búsqueda de vecinos cercanos nativa, archivo local, cero servidor |
| Base de datos relacional | SQLite | Almacena resultados de análisis, puntuaciones, descripciones de vacantes y perfiles de CV enviados |
| Validación de datos | Pydantic | Salida estructurada y tipada de los agentes LLM |
| Frontend | Gradio | Nativo de HuggingFace, UX de chat + subida de archivos, ideal para demos de IA |

---

## Datos

- **Ofertas de trabajo:** 8 posiciones en el stack de IA/Datos — desde Data Analyst Junior hasta AI Researcher y MLOps Engineer
- **CVs:** 10 perfiles sintéticos de candidatos, cubriendo una variedad de niveles de seniority, combinaciones de skills y backgrounds

---

## Cómo Ejecutarlo

```bash
# 1. Clona e instala
git clone https://github.com/sonixse/Challenge3-SmartCV
cd Challenge3-SmartCV
pip install -r requirements.txt

# 2. Inicia Ollama con Llama 3
ollama run llama3

# 3. Indexa las vacantes en ChromaDB (ejecuta una vez)
python scripts/index_vacancies.py

# 4. Lanza la interfaz
python app.py
```

Sube un CV (PDF). En segundos:
- Mejores ofertas de trabajo ordenadas con puntuaciones de compatibilidad
- Desglose por skill: MATCH / ZONA GRIS (con el razonamiento de Lamarr) / NO MATCH
- Análisis de gaps personalizado de Jobs y hoja de ruta de desarrollo

---

## Por Qué Esto Es un Sistema Multi-Agente Genuino

La restricción era clara: ningún agente preconstruido. Aquí explicamos cómo la cumplimos — y vamos más allá:

- **7 agentes, 7 roles** — cada agente tiene una única responsabilidad definida con entradas y salidas tipadas
- **Activación condicional** — Lamarr solo se ejecuta cuando Turing encuentra ambigüedad. Johannes Gutenberg solo renderiza cuando Serena Williams tiene una puntuación final. El sistema no es un pipeline fijo; se adapta.
- **Separación deliberada LLM vs. código** — Marie Curie y Serena Williams se ejecutan como código puro porque sus tareas son deterministas. Ada Lovelace, Lamarr y Steve Jobs usan LLMs porque sus tareas requieren comprensión del lenguaje. Esta es una decisión arquitectónica, no un valor por defecto.
- **El orquestador tiene estado** — Von Neumann hace seguimiento de lo que se ha ejecutado, lo que está pendiente y cómo es el perfil del candidato actual en cada paso.

---

## Las 5 Dimensiones de Evaluación

**1. Innovación y Originalidad**
Embeddings semánticos + una capa de razonamiento condicional (Lamarr) + un agente de coaching de carrera personalizado (Steve Jobs). La mayoría de herramientas de CVs hacen coincidencia por palabras clave. Nosotros hacemos comprensión semántica con explicabilidad y una hoja de ruta de desarrollo. El nombre de los agentes no es decoración — es una estrategia de comunicación que hace la arquitectura instantáneamente memorable.

**2. Viabilidad y Escalabilidad**
Cada componente es realista para producción. ChromaDB escala a millones de vectores. BGE (nuestro modelo de embedding) es suficientemente rápido para consultas en tiempo real. SQLite cambia a PostgreSQL con un cambio de configuración. La interfaz Gradio se convierte en un endpoint REST API. El patrón de orquestador LangGraph funciona a cualquier escala.

**3. Claridad y Concisión**
Un agente, un trabajo. La arquitectura es legible: puedes apuntar a cualquier nodo y explicar qué hace, por qué está ahí y por qué usa la herramienta que usa. La rama condicional es un único punto de decisión (¿existen zonas grises?).

**4. Colaboración y Engagement**
Jobs hace el sistema valioso para los *candidatos*, no solo para los reclutadores. Esto convierte una herramienta de selección B2B en algo con valor directo para el usuario — un asesor de carrera que te da una lista de tareas ordenadas para tu próximo rol.

**5. Consideraciones Éticas**
- Ningún atributo protegido (edad, género, nacionalidad) entra en la puntuación
- Las reglas de Marie Curie son transparentes y auditables — sin descalificaciones silenciosas por LLM
- Lamarr siempre cita su evidencia — ninguna decisión en zonas grises es opaca
- Los requisitos de idioma son restricciones operativas, no señales culturales (gestionados por Marie Curie, no por Alan Turing)
- Todos los modelos se ejecutan localmente — ningún dato del candidato sale del sistema

---

## Lo Que Construiríamos Con Más Tiempo

- **Recuperación en dos fases:** usar una versión ligera de BGE para la recuperación rápida de los 50 mejores candidatos, después el modelo completo para el re-ranking final. Así es como funcionan los sistemas de búsqueda semántica en producción — lo hemos prototipado en teoría y lo implementaríamos en una versión de producción.
- **Bucle de retroalimentación:** recoger las decisiones de aceptación/rechazo del reclutador y ajustar los pesos de Serena Williams con el tiempo. Aprendizaje en línea ligero sin entrenamiento.
- **Panel de explicabilidad:** Johannes Gutenberg ampliado con un desglose visual de cada componente de la puntuación — útil para auditorías de RRHH y cumplimiento normativo.
- **Soporte multilingüe de CVs:** BGE (nuestro modelo de embedding) gestiona texto multilingüe; Ada Lovelace se ampliaría para parsear CVs nativamente en español, catalán e inglés sin preprocesamiento.
- **Capa REST API:** exponer el grafo completo de agentes como API para que se pueda integrar en los sistemas ATS existentes. John von Neumann se convierte en un servicio, no en un script.
- **Generación sintética de CVs a escala:** generación programática de CVs de casos límite para testear Lamarr y calibrar los umbrales de Alan Turing.

---

## El Equipo

Cinco personas, dos caminos, un sistema.

**Backend · Agentes · Orquestación · Pipeline**
Un ingeniero industrial, un ingeniero informático y un ingeniero de IA — las personas que han construido los agentes y los han hecho hablar entre ellos.

**Frontend · Presentación · Documentación · Impacto**
Un especialista en biomedicina y un experto en negocio y tecnología — las personas que han hecho el sistema legible, defendible y que vale la pena presentar.

Los nombres de los agentes son un pequeño homenaje a esa estructura: cada uno lleva el espíritu de una disciplina que alguien del equipo vive.

---

> *"No hemos utilizado ningún agente preconstruido. Hemos diseñado una arquitectura multi-agente a medida donde cada uno de los siete agentes tiene un rol específico y justificado — desde el parseo del CV hasta la coincidencia semántica, el filtrado duro, el razonamiento de ambigüedad, la puntuación, el coaching y la visualización — coordinados por un orquestador que adapta el flujo en función de lo que encuentra en cada paso."*
