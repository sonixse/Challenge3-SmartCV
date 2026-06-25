"""All UI strings for SmartCV — English, Spanish, Catalan."""

TRANSLATIONS: dict[str, dict[str, str]] = {

# ─────────────────────────────────────────────────────────────────────
    "en": {
# ─────────────────────────────────────────────────────────────────────

    # Hero
    "hero.tagline":         "AI   Job   Matching",
    "hero.headline":        "Find the jobs where you truly fit.",

    # Landing — left column
    "landing.decoded":      "Your CV, decoded in seconds.",
    "landing.desc":         (
        "We read your CV, match your skills semantically against real job offers, "
        "and return a ranked list with the exact reasons behind every score. No black boxes."
    ),
    "landing.extract_label":    "What we extract",
    "landing.extract.skills":   "Skills &amp; years of experience",
    "landing.extract.edu":      "Education level &amp; field",
    "landing.extract.langs":    "Languages &amp; proficiency",
    "landing.assessor_desc":    (
        "Not sure why a match failed or how to improve? "
        "<strong style='color:white;'>Ask our AI assessor</strong> — "
        "it explains every decision and gives you concrete advice."
    ),

    # Upload card
    "upload.title":     "📤 Upload your CV!",
    "upload.desc":      "Use a PDF. Once loaded, press Analyse — your profile and ranking will open.",
    "upload.extract":   "We will extract",
    "upload.ready":     "ready!",
    "upload.btn":       "🚀  Show ranking",
    "upload.no_cvs":    "No sample CVs found in data/raw/",

    # Sample card
    "sample.title":       "🗂️ Try a sample profile",
    "sample.desc":        "No CV handy? Pick one of our pre-loaded profiles and see the full analysis live — no upload needed.",
    "sample.profiles":    "Available profiles",
    "sample.placeholder": "Select a sample profile…",

    # Stats grid labels
    "stat.vacancies":       "Vacancies indexed",
    "stat.agents":          "Specialized agents",
    "stat.keywords":        "Keywords used",
    "stat.keywords_sub":    "Pure semantic AI &mdash;<br>we match meaning, not words",
    "stat.local":           "Runs locally",
    "stat.axes":            "Evaluation axes",
    "stat.axes_sub":        "Semantic skills &middot; Experience<br>Education &middot; Language",
    "stat.speed":           "Average analysis",

    # Ticker / pipeline
    "ticker.label":  "7 AI agents &nbsp;&middot;&nbsp; one pipeline",
    "ticker.msg1":   "READING YOUR CV &middot; PLEASE WAIT",
    "ticker.msg2":   "MATCHING YOUR SKILLS &middot; HANG TIGHT",
    "ticker.msg3":   "RESOLVING GREY ZONES &middot; ALMOST THERE",
    "ticker.msg4":   "RANKING YOUR MATCHES &middot; FINAL STEP",
    "ticker.ada":     "Reads your CV",
    "ticker.marie":   "Filters hard rules",
    "ticker.alan":    "Matches your skills",
    "ticker.hedy":    "Resolves grey zones",
    "ticker.serena":  "Scores & ranks",
    "ticker.steve":   "Coaches you",
    "ticker.johannes":"Publishes results",

    # Loader overlay
    "loader.agents":   "7 Agents Working",
    "loader.subtitle": "Analysing your CV against 1,000 job offers",

    # Detail view — top bar
    "detail.tab_pdf":       "📄 Original PDF",
    "detail.tab_profile":   "📋 Extracted Profile",
    "detail.change_cv":     "← Change CV",
    "detail.no_profile":    "No profile data yet — process the CV first.",
    "detail.no_ranking":    "Process the CV to see job matches.",
    "detail.pdf_not_found": "PDF not found.",
    "detail.back":          "← Back",

    # Profile section
    "profile.experience":    "💼 Experience",
    "profile.years":         "years",
    "profile.education":     "🎓 Education",
    "profile.skills":        "🛠 Skills",
    "profile.no_skills":     "No skills detected",
    "profile.languages":     "🌐 Languages",
    "profile.no_langs":      "No languages detected",

    # Ranking section
    "ranking.title":         "🏆 Best Job Matches",
    "ranking.caption":       "Showing {n} of {total} offers · sorted by AI match score",
    "ranking.no_matches":    (
        "No matches found among {total} offers — "
        "candidate is eliminated by language or experience requirements."
    ),
    "ranking.pct":           "% match",
    "ranking.sig_lang":      "Language",
    "ranking.sig_exp":       "Experience",
    "ranking.sig_edu":       "Education",

    # SmartCV Assessor
    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Full Screen",
    "assessor.desc":           "Ask why a match is low or how to improve your profile.",
    "assessor.placeholder":    "Ask the assessor…",
    "assessor.fs_placeholder": "Ask anything about your CV or matches…",
    "assessor.expand":         "⛶ Full screen",
    "assessor.back":           "← Back to results",
    "assessor.error":          "Could not connect to Ollama: {err}",

    # Errors
    "err.pdf_read":  "Could not read PDF: {err}",
    "err.ollama":    (
        "Cannot connect to Ollama. Make sure `ollama serve` is running "
        "and `llama3` is installed (`ollama pull llama3`)."
    ),
    "err.cv":        "Error processing CV: {err}",

    # Language switcher labels
    "lang.label": "Language",
    },

# ─────────────────────────────────────────────────────────────────────
    "es": {
# ─────────────────────────────────────────────────────────────────────

    "hero.tagline":     "Búsqueda de Empleo con IA",
    "hero.headline":    "Encuentra los trabajos donde realmente encajas.",

    "landing.decoded":  "Tu CV, descifrado en segundos.",
    "landing.desc":     (
        "Leemos tu CV, comparamos tus habilidades semánticamente con ofertas de trabajo reales, "
        "y te devolvemos una lista ordenada con las razones exactas de cada puntuación. Sin cajas negras."
    ),
    "landing.extract_label":    "Qué extraemos",
    "landing.extract.skills":   "Habilidades y años de experiencia",
    "landing.extract.edu":      "Nivel y campo de educación",
    "landing.extract.langs":    "Idiomas y nivel",
    "landing.assessor_desc":    (
        "¿No sabes por qué falló un match o cómo mejorar? "
        "<strong style='color:white;'>Pregunta a nuestro asesor IA</strong> — "
        "explica cada decisión y da consejos concretos."
    ),

    "upload.title":   "📤 ¡Sube tu CV!",
    "upload.desc":    "Usa un PDF. Una vez cargado, pulsa Analizar — se abrirán tu perfil y el ranking.",
    "upload.extract": "Extraeremos",
    "upload.ready":   "¡listo!",
    "upload.btn":     "🚀  Ver ranking",
    "upload.no_cvs":  "No se encontraron CVs de muestra en data/raw/",

    "sample.title":       "🗂️ Prueba un perfil de ejemplo",
    "sample.desc":        "¿Sin CV a mano? Elige uno de nuestros perfiles precargados y ve el análisis completo en vivo — sin necesidad de subir nada.",
    "sample.profiles":    "Perfiles disponibles",
    "sample.placeholder": "Selecciona un perfil de ejemplo…",

    "stat.vacancies":    "Vacantes indexadas",
    "stat.agents":       "Agentes especializados",
    "stat.keywords":     "Palabras clave usadas",
    "stat.keywords_sub": "IA semántica pura &mdash;<br>coincidimos por significado, no por palabras",
    "stat.local":        "Se ejecuta localmente",
    "stat.axes":         "Ejes de evaluación",
    "stat.axes_sub":     "Habilidades semánticas &middot; Experiencia<br>Educación &middot; Idioma",
    "stat.speed":        "Análisis promedio",

    "ticker.label": "7 agentes IA &nbsp;&middot;&nbsp; un pipeline",
    "ticker.msg1":  "LEYENDO TU CV &middot; POR FAVOR ESPERA",
    "ticker.msg2":  "COMPARANDO TUS HABILIDADES &middot; UN MOMENTO",
    "ticker.msg3":  "RESOLVIENDO ZONAS GRISES &middot; CASI LISTO",
    "ticker.msg4":  "ORDENANDO TUS MATCHES &middot; PASO FINAL",
    "ticker.ada":      "Lee tu CV",
    "ticker.marie":    "Filtra requisitos",
    "ticker.alan":     "Compara tus habilidades",
    "ticker.hedy":     "Resuelve zonas grises",
    "ticker.serena":   "Puntúa y ordena",
    "ticker.steve":    "Te asesora",
    "ticker.johannes": "Publica resultados",

    "loader.agents":   "7 Agentes Trabajando",
    "loader.subtitle": "Analizando tu CV contra 1.000 ofertas",

    "detail.tab_pdf":       "📄 PDF Original",
    "detail.tab_profile":   "📋 Perfil Extraído",
    "detail.change_cv":     "← Cambiar CV",
    "detail.no_profile":    "Sin datos aún — procesa el CV primero.",
    "detail.no_ranking":    "Procesa el CV para ver los matches.",
    "detail.pdf_not_found": "PDF no encontrado.",
    "detail.back":          "← Volver",

    "profile.experience": "💼 Experiencia",
    "profile.years":      "años",
    "profile.education":  "🎓 Educación",
    "profile.skills":     "🛠 Habilidades",
    "profile.no_skills":  "No se detectaron habilidades",
    "profile.languages":  "🌐 Idiomas",
    "profile.no_langs":   "No se detectaron idiomas",

    "ranking.title":      "🏆 Mejores Puestos",
    "ranking.caption":    "Mostrando {n} de {total} ofertas · ordenadas por puntuación IA",
    "ranking.no_matches": (
        "Sin matches entre {total} ofertas — "
        "el candidato es eliminado por idioma o experiencia."
    ),
    "ranking.pct":     "% match",
    "ranking.sig_lang": "Idioma",
    "ranking.sig_exp":  "Experiencia",
    "ranking.sig_edu":  "Educación",

    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Pantalla completa",
    "assessor.desc":           "Pregunta por qué un match es bajo o cómo mejorar tu perfil.",
    "assessor.placeholder":    "Pregunta al asesor…",
    "assessor.fs_placeholder": "Pregunta lo que quieras sobre tu CV o matches…",
    "assessor.expand":         "⛶ Pantalla completa",
    "assessor.back":           "← Volver a resultados",
    "assessor.error":          "No se pudo conectar a Ollama: {err}",

    "err.pdf_read": "No se pudo leer el PDF: {err}",
    "err.ollama":   (
        "No se puede conectar a Ollama. Asegúrate de que `ollama serve` "
        "esté en ejecución y `llama3` instalado (`ollama pull llama3`)."
    ),
    "err.cv":       "Error procesando el CV: {err}",

    "lang.label": "Idioma",
    },

# ─────────────────────────────────────────────────────────────────────
    "ca": {
# ─────────────────────────────────────────────────────────────────────

    "hero.tagline":     "Revoluciona la cerca de feina amb IA",
    "hero.headline":    "Troba les feines on realment encaixes.",

    "landing.decoded":  "El teu CV, desxifrat en segons.",
    "landing.desc":     (
        "Llegim el teu CV, comparem les teves habilitats semànticament amb ofertes de feina reals, "
        "i et retornem una llista ordenada amb els motius exactes de cada puntuació. Sense caixes negres."
    ),
    "landing.extract_label":    "Què extraiem",
    "landing.extract.skills":   "Habilitats i anys d'experiència",
    "landing.extract.edu":      "Nivell i àmbit d'educació",
    "landing.extract.langs":    "Idiomes i nivell",
    "landing.assessor_desc":    (
        "No saps per què ha fallat un match o com millorar? "
        "<strong style='color:white;'>Pregunta al nostre assessor IA</strong> — "
        "explica cada decisió i dona consells concrets."
    ),

    "upload.title":   "📤 Puja el teu CV!",
    "upload.desc":    "Usa un PDF. Un cop carregat, prem Analitza — s'obriran el teu perfil i el rànquing.",
    "upload.extract": "Extraurem",
    "upload.ready":   "llest!",
    "upload.btn":     "🚀  Veure rànquing",
    "upload.no_cvs":  "No s'han trobat CVs d'exemple a data/raw/",

    "sample.title":       "🗂️ Prova un perfil d'exemple",
    "sample.desc":        "Sense CV a mà? Tria un dels nostres perfils precarregats i veu l'anàlisi completa en directe — sense necessitat de pujar res.",
    "sample.profiles":    "Perfils disponibles",
    "sample.placeholder": "Selecciona un perfil d'exemple…",

    "stat.vacancies":    "Vacants indexades",
    "stat.agents":       "Agents especialitzats",
    "stat.keywords":     "Paraules clau usades",
    "stat.keywords_sub": "IA semàntica pura &mdash;<br>coincidim per significat, no per paraules",
    "stat.local":        "S'executa localment",
    "stat.axes":         "Eixos d'avaluació",
    "stat.axes_sub":     "Habilitats semàntiques &middot; Experiència<br>Educació &middot; Idioma",
    "stat.speed":        "Anàlisi mitjana",

    "ticker.label": "7 agents IA &nbsp;&middot;&nbsp; un pipeline",
    "ticker.msg1":  "LLEGINT EL TEU CV &middot; SI US PLAU ESPERA",
    "ticker.msg2":  "COMPARANT LES TEVES HABILITATS &middot; UN MOMENT",
    "ticker.msg3":  "RESOLENT ZONES GRISES &middot; GAIREBÉ LLEST",
    "ticker.msg4":  "ORDENANT ELS TEUS MATCHES &middot; DARRER PAS",
    "ticker.ada":      "Llegeix el teu CV",
    "ticker.marie":    "Filtra requisits",
    "ticker.alan":     "Compara les teves habilitats",
    "ticker.hedy":     "Resol zones grises",
    "ticker.serena":   "Puntua i ordena",
    "ticker.steve":    "T'assessora",
    "ticker.johannes": "Publica resultats",

    "loader.agents":   "7 Agents Treballant",
    "loader.subtitle": "Analitzant el teu CV contra 1.000 ofertes",

    "detail.tab_pdf":       "📄 PDF Original",
    "detail.tab_profile":   "📋 Perfil Extret",
    "detail.change_cv":     "← Canviar CV",
    "detail.no_profile":    "Encara no hi ha dades — processa el CV primer.",
    "detail.no_ranking":    "Processa el CV per veure els matches.",
    "detail.pdf_not_found": "PDF no trobat.",
    "detail.back":          "← Tornar",

    "profile.experience": "💼 Experiència",
    "profile.years":      "anys",
    "profile.education":  "🎓 Educació",
    "profile.skills":     "🛠 Habilitats",
    "profile.no_skills":  "No s'han detectat habilitats",
    "profile.languages":  "🌐 Idiomes",
    "profile.no_langs":   "No s'han detectat idiomes",

    "ranking.title":      "🏆 Millors Compatitibilitats",
    "ranking.caption":    "Mostrant {n} de {total} ofertes · ordenades per puntuació IA",
    "ranking.no_matches": (
        "Sense matches entre {total} ofertes — "
        "el candidat és eliminat per idioma o experiència."
    ),
    "ranking.pct":      "% match",
    "ranking.sig_lang": "Idioma",
    "ranking.sig_exp":  "Experiència",
    "ranking.sig_edu":  "Educació",

    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Pantalla completa",
    "assessor.desc":           "Pregunta per què un match és baix o com millorar el teu perfil.",
    "assessor.placeholder":    "Pregunta a l'assessor…",
    "assessor.fs_placeholder": "Pregunta el que vulguis sobre el teu CV o matches…",
    "assessor.expand":         "⛶ Pantalla completa",
    "assessor.back":           "← Tornar als resultats",
    "assessor.error":          "No s'ha pogut connectar amb Ollama: {err}",

    "err.pdf_read": "No s'ha pogut llegir el PDF: {err}",
    "err.ollama":   (
        "No es pot connectar amb Ollama. Assegura't que `ollama serve` "
        "estigui en funcionament i `llama3` instal·lat (`ollama pull llama3`)."
    ),
    "err.cv":       "Error processant el CV: {err}",

    "lang.label": "Idioma",
    },
}
