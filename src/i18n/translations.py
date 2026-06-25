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

    # Offer details dropdown
    "offer.details":         "See full offer details",
    "offer.must":            "Must-have skills",
    "offer.nice":            "Nice-to-have",
    "offer.other":           "Other skills",
    "offer.tools":           "Tools",
    "offer.req_langs":       "Required languages",
    "offer.years_exp":       "≥ {n} years exp.",
    "offer.internship_yes":  "Internship available",
    "offer.internship_no":   "No internship",
    "offer.id":              "Offer ID #{id}",

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

    "offer.details":        "Ver detalles completos de la oferta",
    "offer.must":           "Skills imprescindibles",
    "offer.nice":           "Skills deseables",
    "offer.other":          "Otras skills",
    "offer.tools":          "Herramientas",
    "offer.req_langs":      "Idiomas requeridos",
    "offer.years_exp":      "≥ {n} años exp.",
    "offer.internship_yes": "Prácticas disponibles",
    "offer.internship_no":  "Sin prácticas",
    "offer.id":             "Oferta #{id}",

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

    "offer.details":        "Veure detalls complets de l'oferta",
    "offer.must":           "Skills imprescindibles",
    "offer.nice":           "Skills desitjables",
    "offer.other":          "Altres skills",
    "offer.tools":          "Eines",
    "offer.req_langs":      "Idiomes requerits",
    "offer.years_exp":      "≥ {n} anys exp.",
    "offer.internship_yes": "Pràctiques disponibles",
    "offer.internship_no":  "Sense pràctiques",
    "offer.id":             "Oferta #{id}",

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

# ─────────────────────────────────────────────────────────────────────
    "ru": {
# ─────────────────────────────────────────────────────────────────────

    "hero.tagline":     "ИИ   Работа   Подбор",
    "hero.headline":    "Найди вакансии, где ты действительно подходишь.",

    "landing.decoded":  "Твоё резюме, расшифровано за секунды.",
    "landing.desc":     (
        "Мы читаем твоё резюме, семантически сравниваем твои навыки с реальными вакансиями "
        "и возвращаем ранжированный список с точными причинами каждой оценки. Без чёрных ящиков."
    ),
    "landing.extract_label":    "Что мы извлекаем",
    "landing.extract.skills":   "Навыки и годы опыта",
    "landing.extract.edu":      "Уровень и направление образования",
    "landing.extract.langs":    "Языки и уровень владения",
    "landing.assessor_desc":    (
        "Не знаешь, почему нет совпадения или как улучшить резюме? "
        "<strong style='color:white;'>Спроси нашего ИИ-консультанта</strong> — "
        "он объясняет каждое решение и даёт конкретные советы."
    ),

    "upload.title":   "📤 Загрузи резюме!",
    "upload.desc":    "Используй PDF. После загрузки нажми Анализ — откроется твой профиль и рейтинг.",
    "upload.extract": "Мы извлечём",
    "upload.ready":   "готово!",
    "upload.btn":     "🚀  Показать рейтинг",
    "upload.no_cvs":  "Примеры резюме не найдены в data/raw/",

    "sample.title":       "🗂️ Попробуй пример профиля",
    "sample.desc":        "Нет резюме под рукой? Выбери один из готовых профилей и посмотри полный анализ — загружать ничего не нужно.",
    "sample.profiles":    "Доступные профили",
    "sample.placeholder": "Выбери пример профиля…",

    "stat.vacancies":    "Вакансий проиндексировано",
    "stat.agents":       "Специализированных агентов",
    "stat.keywords":     "Ключевых слов использовано",
    "stat.keywords_sub": "Чистый семантический ИИ &mdash;<br>мы ищем смысл, а не слова",
    "stat.local":        "Работает локально",
    "stat.axes":         "Оси оценки",
    "stat.axes_sub":     "Семантика навыков &middot; Опыт<br>Образование &middot; Языки",
    "stat.speed":        "Средний анализ",

    "ticker.label": "7 ИИ-агентов &nbsp;&middot;&nbsp; один пайплайн",
    "ticker.msg1":  "ЧИТАЕМ РЕЗЮМЕ И ПОДОЖДИ",
    "ticker.msg2":  "СРАВНИВАЕМ НАВЫКИ И ЕЩЁ НЕМНОГО",
    "ticker.msg3":  "РАЗРЕШАЕМ СЕРЫЕ ЗОНЫ И ПОЧТИ ГОТОВО",
    "ticker.msg4":  "РАНЖИРУЕМ СОВПАДЕНИЯ И ФИНАЛЬНЫЙ ШАГ",
    "ticker.ada":      "Читает резюме",
    "ticker.marie":    "Фильтрует требования",
    "ticker.alan":     "Сравнивает навыки",
    "ticker.hedy":     "Разрешает серые зоны",
    "ticker.serena":   "Оценивает и ранжирует",
    "ticker.steve":    "Консультирует тебя",
    "ticker.johannes": "Публикует результаты",

    "loader.agents":   "7 агентов работают",
    "loader.subtitle": "Анализируем резюме по 1 000 вакансиям",

    "detail.tab_pdf":       "📄 Оригинал PDF",
    "detail.tab_profile":   "📋 Извлечённый профиль",
    "detail.change_cv":     "← Сменить резюме",
    "detail.no_profile":    "Данных пока нет — сначала обработай резюме.",
    "detail.no_ranking":    "Обработай резюме, чтобы увидеть совпадения.",
    "detail.pdf_not_found": "PDF не найден.",
    "detail.back":          "← Назад",

    "profile.experience": "💼 Опыт",
    "profile.years":      "лет",
    "profile.education":  "🎓 Образование",
    "profile.skills":     "🛠 Навыки",
    "profile.no_skills":  "Навыки не обнаружены",
    "profile.languages":  "🌐 Языки",
    "profile.no_langs":   "Языки не обнаружены",

    "ranking.title":      "🏆 Лучшие совпадения",
    "ranking.caption":    "Топ {n} из {total} вакансий · отсортировано по оценке ИИ",
    "ranking.no_matches": (
        "Совпадений среди {total} вакансий не найдено — "
        "кандидат исключён по требованиям к языку или опыту."
    ),
    "ranking.pct":      "% совпадение",
    "ranking.sig_lang": "Язык",
    "ranking.sig_exp":  "Опыт",
    "ranking.sig_edu":  "Образование",

    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Полный экран",
    "assessor.desc":           "Спроси, почему совпадение низкое или как улучшить профиль.",
    "assessor.placeholder":    "Спроси консультанта…",
    "assessor.fs_placeholder": "Спроси что угодно о своём резюме или совпадениях…",
    "assessor.expand":         "⛶ Полный экран",
    "assessor.back":           "← Вернуться к результатам",
    "assessor.error":          "Не удалось подключиться к Ollama: {err}",

    "err.pdf_read": "Не удалось прочитать PDF: {err}",
    "err.ollama":   (
        "Не удаётся подключиться к Ollama. Убедись, что `ollama serve` запущен "
        "и `llama3` установлен (`ollama pull llama3`)."
    ),
    "err.cv":       "Ошибка обработки резюме: {err}",

    "lang.label": "Язык",
    },

# ─────────────────────────────────────────────────────────────────────
    "it": {
# ─────────────────────────────────────────────────────────────────────
    "hero.tagline":     "IA   Lavoro   Matching",
    "hero.headline":    "Trova i lavori dove sei davvero adatto.",
    "landing.decoded":  "Il tuo CV, decodificato in secondi.",
    "landing.desc":     ("Leggiamo il tuo CV, confrontiamo le tue competenze semanticamente con offerte reali "
                         "e restituiamo una lista ordinata con le ragioni esatte di ogni punteggio. Nessuna scatola nera."),
    "landing.extract_label":  "Cosa estraiamo",
    "landing.extract.skills": "Competenze e anni di esperienza",
    "landing.extract.edu":    "Livello e campo di istruzione",
    "landing.extract.langs":  "Lingue e livello",
    "landing.assessor_desc":  ("Non sai perché un match è fallito o come migliorare? "
                                "<strong style='color:white;'>Chiedi al nostro consulente IA</strong> — "
                                "spiega ogni decisione e dà consigli concreti."),
    "upload.title":   "📤 Carica il tuo CV!",
    "upload.desc":    "Usa un PDF. Una volta caricato, premi Analizza — si apriranno il profilo e la classifica.",
    "upload.extract": "Estrarremo",
    "upload.ready":   "pronto!",
    "upload.btn":     "🚀  Mostra classifica",
    "upload.no_cvs":  "Nessun CV di esempio trovato in data/raw/",
    "sample.title":       "🗂️ Prova un profilo di esempio",
    "sample.desc":        "Senza CV? Scegli uno dei nostri profili precaricati e guarda l'analisi completa in diretta.",
    "sample.profiles":    "Profili disponibili",
    "sample.placeholder": "Seleziona un profilo di esempio…",
    "stat.vacancies":    "Offerte indicizzate",
    "stat.agents":       "Agenti specializzati",
    "stat.keywords":     "Parole chiave usate",
    "stat.keywords_sub": "IA semantica pura &mdash;<br>abbiniamo significati, non parole",
    "stat.local":        "Funziona localmente",
    "stat.axes":         "Assi di valutazione",
    "stat.axes_sub":     "Competenze semantiche &middot; Esperienza<br>Istruzione &middot; Lingua",
    "stat.speed":        "Analisi media",
    "ticker.label": "7 agenti IA &nbsp;&middot;&nbsp; un pipeline",
    "ticker.msg1":  "LEGGENDO IL TUO CV &middot; ATTENDI",
    "ticker.msg2":  "CONFRONTANDO LE COMPETENZE &middot; UN ATTIMO",
    "ticker.msg3":  "RISOLVENDO ZONE GRIGIE &middot; QUASI PRONTO",
    "ticker.msg4":  "CLASSIFICANDO I MATCH &middot; PASSO FINALE",
    "ticker.ada":      "Legge il tuo CV",
    "ticker.marie":    "Filtra i requisiti",
    "ticker.alan":     "Confronta le competenze",
    "ticker.hedy":     "Risolve le zone grigie",
    "ticker.serena":   "Valuta e classifica",
    "ticker.steve":    "Ti consiglia",
    "ticker.johannes": "Pubblica i risultati",
    "loader.agents":   "7 Agenti al lavoro",
    "loader.subtitle": "Analisi del tuo CV su 1.000 offerte",
    "detail.tab_pdf":       "📄 PDF Originale",
    "detail.tab_profile":   "📋 Profilo Estratto",
    "detail.change_cv":     "← Cambia CV",
    "detail.no_profile":    "Nessun dato ancora — elabora il CV prima.",
    "detail.no_ranking":    "Elabora il CV per vedere i match.",
    "detail.pdf_not_found": "PDF non trovato.",
    "detail.back":          "← Indietro",
    "profile.experience": "💼 Esperienza",
    "profile.years":      "anni",
    "profile.education":  "🎓 Istruzione",
    "profile.skills":     "🛠 Competenze",
    "profile.no_skills":  "Nessuna competenza rilevata",
    "profile.languages":  "🌐 Lingue",
    "profile.no_langs":   "Nessuna lingua rilevata",
    "ranking.title":      "🏆 Migliori Match",
    "ranking.caption":    "Top {n} di {total} offerte · ordinate per punteggio IA",
    "ranking.no_matches": "Nessun match tra {total} offerte — il candidato è escluso per lingua o esperienza.",
    "ranking.pct":      "% match",
    "ranking.sig_lang": "Lingua",
    "ranking.sig_exp":  "Esperienza",
    "ranking.sig_edu":  "Istruzione",
    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Schermo intero",
    "assessor.desc":           "Chiedi perché un match è basso o come migliorare il profilo.",
    "assessor.placeholder":    "Chiedi al consulente…",
    "assessor.fs_placeholder": "Chiedi qualsiasi cosa sul tuo CV o i match…",
    "assessor.expand":         "⛶ Schermo intero",
    "assessor.back":           "← Torna ai risultati",
    "assessor.error":          "Impossibile connettersi a Ollama: {err}",
    "err.pdf_read": "Impossibile leggere il PDF: {err}",
    "err.ollama":   ("Impossibile connettersi a Ollama. Assicurati che `ollama serve` sia in esecuzione "
                     "e `llama3` installato (`ollama pull llama3`)."),
    "err.cv":       "Errore nell'elaborazione del CV: {err}",
    "lang.label": "Lingua",
    },

# ─────────────────────────────────────────────────────────────────────
    "fr": {
# ─────────────────────────────────────────────────────────────────────
    "hero.tagline":     "IA   Emploi   Matching",
    "hero.headline":    "Trouve les emplois où tu corresponds vraiment.",
    "landing.decoded":  "Ton CV, décodé en quelques secondes.",
    "landing.desc":     ("Nous lisons ton CV, comparons tes compétences sémantiquement avec de vraies offres d'emploi "
                         "et te renvoyons une liste classée avec les raisons exactes de chaque score. Aucune boîte noire."),
    "landing.extract_label":  "Ce que nous extrayons",
    "landing.extract.skills": "Compétences et années d'expérience",
    "landing.extract.edu":    "Niveau et domaine d'éducation",
    "landing.extract.langs":  "Langues et niveau",
    "landing.assessor_desc":  ("Tu ne sais pas pourquoi un match a échoué ou comment t'améliorer ? "
                                "<strong style='color:white;'>Demande à notre conseiller IA</strong> — "
                                "il explique chaque décision et donne des conseils concrets."),
    "upload.title":   "📤 Télécharge ton CV !",
    "upload.desc":    "Utilise un PDF. Une fois chargé, appuie sur Analyser — ton profil et le classement s'ouvriront.",
    "upload.extract": "Nous extrairons",
    "upload.ready":   "prêt !",
    "upload.btn":     "🚀  Voir le classement",
    "upload.no_cvs":  "Aucun CV d'exemple trouvé dans data/raw/",
    "sample.title":       "🗂️ Essaie un profil exemple",
    "sample.desc":        "Pas de CV sous la main ? Choisis l'un de nos profils préchargés et vois l'analyse complète en direct.",
    "sample.profiles":    "Profils disponibles",
    "sample.placeholder": "Sélectionne un profil exemple…",
    "stat.vacancies":    "Offres indexées",
    "stat.agents":       "Agents spécialisés",
    "stat.keywords":     "Mots-clés utilisés",
    "stat.keywords_sub": "IA sémantique pure &mdash;<br>on associe les sens, pas les mots",
    "stat.local":        "Fonctionne localement",
    "stat.axes":         "Axes d'évaluation",
    "stat.axes_sub":     "Compétences sémantiques &middot; Expérience<br>Éducation &middot; Langue",
    "stat.speed":        "Analyse moyenne",
    "ticker.label": "7 agents IA &nbsp;&middot;&nbsp; un pipeline",
    "ticker.msg1":  "LECTURE DU CV &middot; VEUILLEZ PATIENTER",
    "ticker.msg2":  "COMPARAISON DES COMPÉTENCES &middot; UN INSTANT",
    "ticker.msg3":  "RÉSOLUTION DES ZONES GRISES &middot; PRESQUE PRÊT",
    "ticker.msg4":  "CLASSEMENT DES MATCHES &middot; ÉTAPE FINALE",
    "ticker.ada":      "Lit ton CV",
    "ticker.marie":    "Filtre les exigences",
    "ticker.alan":     "Compare les compétences",
    "ticker.hedy":     "Résout les zones grises",
    "ticker.serena":   "Évalue et classe",
    "ticker.steve":    "Te conseille",
    "ticker.johannes": "Publie les résultats",
    "loader.agents":   "7 Agents au travail",
    "loader.subtitle": "Analyse de ton CV sur 1 000 offres",
    "detail.tab_pdf":       "📄 PDF Original",
    "detail.tab_profile":   "📋 Profil Extrait",
    "detail.change_cv":     "← Changer de CV",
    "detail.no_profile":    "Aucune donnée pour l'instant — traite le CV d'abord.",
    "detail.no_ranking":    "Traite le CV pour voir les matches.",
    "detail.pdf_not_found": "PDF introuvable.",
    "detail.back":          "← Retour",
    "profile.experience": "💼 Expérience",
    "profile.years":      "ans",
    "profile.education":  "🎓 Formation",
    "profile.skills":     "🛠 Compétences",
    "profile.no_skills":  "Aucune compétence détectée",
    "profile.languages":  "🌐 Langues",
    "profile.no_langs":   "Aucune langue détectée",
    "ranking.title":      "🏆 Meilleurs Matches",
    "ranking.caption":    "Top {n} de {total} offres · triées par score IA",
    "ranking.no_matches": "Aucun match parmi {total} offres — le candidat est éliminé par langue ou expérience.",
    "ranking.pct":      "% match",
    "ranking.sig_lang": "Langue",
    "ranking.sig_exp":  "Expérience",
    "ranking.sig_edu":  "Formation",
    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Plein écran",
    "assessor.desc":           "Demande pourquoi un match est faible ou comment améliorer ton profil.",
    "assessor.placeholder":    "Pose ta question au conseiller…",
    "assessor.fs_placeholder": "Pose n'importe quelle question sur ton CV ou tes matches…",
    "assessor.expand":         "⛶ Plein écran",
    "assessor.back":           "← Retour aux résultats",
    "assessor.error":          "Impossible de se connecter à Ollama : {err}",
    "err.pdf_read": "Impossible de lire le PDF : {err}",
    "err.ollama":   ("Impossible de se connecter à Ollama. Assure-toi que `ollama serve` est en cours "
                     "et que `llama3` est installé (`ollama pull llama3`)."),
    "err.cv":       "Erreur lors du traitement du CV : {err}",
    "lang.label": "Langue",
    },

# ─────────────────────────────────────────────────────────────────────
    "de": {
# ─────────────────────────────────────────────────────────────────────
    "hero.tagline":     "KI   Arbeit   Matching",
    "hero.headline":    "Finde Jobs, wo du wirklich passt.",
    "landing.decoded":  "Dein Lebenslauf, in Sekunden entschlüsselt.",
    "landing.desc":     ("Wir lesen deinen Lebenslauf, vergleichen deine Fähigkeiten semantisch mit echten Stellenangeboten "
                         "und geben dir eine Rangliste mit den genauen Gründen für jede Bewertung. Keine schwarzen Boxen."),
    "landing.extract_label":  "Was wir extrahieren",
    "landing.extract.skills": "Fähigkeiten und Berufsjahre",
    "landing.extract.edu":    "Bildungsniveau und -bereich",
    "landing.extract.langs":  "Sprachen und Niveau",
    "landing.assessor_desc":  ("Weißt du nicht, warum ein Match fehlschlug oder wie du dich verbessern kannst? "
                                "<strong style='color:white;'>Frag unseren KI-Berater</strong> — "
                                "er erklärt jede Entscheidung und gibt konkrete Ratschläge."),
    "upload.title":   "📤 Lade deinen Lebenslauf hoch!",
    "upload.desc":    "Nutze ein PDF. Nach dem Laden drücke Analysieren — dein Profil und das Ranking öffnen sich.",
    "upload.extract": "Wir extrahieren",
    "upload.ready":   "bereit!",
    "upload.btn":     "🚀  Ranking anzeigen",
    "upload.no_cvs":  "Keine Beispiel-Lebensläufe in data/raw/ gefunden",
    "sample.title":       "🗂️ Beispielprofil ausprobieren",
    "sample.desc":        "Kein Lebenslauf zur Hand? Wähle eines unserer vorgeladenen Profile und sieh die vollständige Analyse live.",
    "sample.profiles":    "Verfügbare Profile",
    "sample.placeholder": "Beispielprofil auswählen…",
    "stat.vacancies":    "Indexierte Stellen",
    "stat.agents":       "Spezialisierte Agenten",
    "stat.keywords":     "Verwendete Schlüsselwörter",
    "stat.keywords_sub": "Reine semantische KI &mdash;<br>wir gleichen Bedeutungen ab, nicht Wörter",
    "stat.local":        "Läuft lokal",
    "stat.axes":         "Bewertungsachsen",
    "stat.axes_sub":     "Semantische Fähigkeiten &middot; Erfahrung<br>Bildung &middot; Sprache",
    "stat.speed":        "Durchschnittliche Analyse",
    "ticker.label": "7 KI-Agenten &nbsp;&middot;&nbsp; eine Pipeline",
    "ticker.msg1":  "LEBENSLAUF WIRD GELESEN &middot; BITTE WARTEN",
    "ticker.msg2":  "FÄHIGKEITEN WERDEN VERGLICHEN &middot; EINEN MOMENT",
    "ticker.msg3":  "GRAUZONEN WERDEN AUFGELÖST &middot; FAST FERTIG",
    "ticker.msg4":  "MATCHES WERDEN BEWERTET &middot; LETZTER SCHRITT",
    "ticker.ada":      "Liest deinen Lebenslauf",
    "ticker.marie":    "Filtert Anforderungen",
    "ticker.alan":     "Vergleicht Fähigkeiten",
    "ticker.hedy":     "Löst Grauzonen auf",
    "ticker.serena":   "Bewertet und sortiert",
    "ticker.steve":    "Berät dich",
    "ticker.johannes": "Veröffentlicht Ergebnisse",
    "loader.agents":   "7 Agenten arbeiten",
    "loader.subtitle": "Dein Lebenslauf wird gegen 1.000 Stellen analysiert",
    "detail.tab_pdf":       "📄 Original-PDF",
    "detail.tab_profile":   "📋 Extrahiertes Profil",
    "detail.change_cv":     "← Lebenslauf wechseln",
    "detail.no_profile":    "Noch keine Daten — verarbeite zuerst den Lebenslauf.",
    "detail.no_ranking":    "Verarbeite den Lebenslauf, um Matches zu sehen.",
    "detail.pdf_not_found": "PDF nicht gefunden.",
    "detail.back":          "← Zurück",
    "profile.experience": "💼 Erfahrung",
    "profile.years":      "Jahre",
    "profile.education":  "🎓 Bildung",
    "profile.skills":     "🛠 Fähigkeiten",
    "profile.no_skills":  "Keine Fähigkeiten erkannt",
    "profile.languages":  "🌐 Sprachen",
    "profile.no_langs":   "Keine Sprachen erkannt",
    "ranking.title":      "🏆 Beste Matches",
    "ranking.caption":    "Top {n} von {total} Stellen · nach KI-Score sortiert",
    "ranking.no_matches": "Keine Matches unter {total} Stellen — Kandidat durch Sprache oder Erfahrung ausgeschlossen.",
    "ranking.pct":      "% Match",
    "ranking.sig_lang": "Sprache",
    "ranking.sig_exp":  "Erfahrung",
    "ranking.sig_edu":  "Bildung",
    "assessor.title":          "SmartCV Assessor",
    "assessor.fullscreen":     "SmartCV Assessor — Vollbild",
    "assessor.desc":           "Frag, warum ein Match niedrig ist oder wie du dein Profil verbessern kannst.",
    "assessor.placeholder":    "Frag den Berater…",
    "assessor.fs_placeholder": "Frag alles über deinen Lebenslauf oder deine Matches…",
    "assessor.expand":         "⛶ Vollbild",
    "assessor.back":           "← Zurück zu den Ergebnissen",
    "assessor.error":          "Verbindung zu Ollama fehlgeschlagen: {err}",
    "err.pdf_read": "PDF konnte nicht gelesen werden: {err}",
    "err.ollama":   ("Keine Verbindung zu Ollama. Stelle sicher, dass `ollama serve` läuft "
                     "und `llama3` installiert ist (`ollama pull llama3`)."),
    "err.cv":       "Fehler bei der Verarbeitung des Lebenslaufs: {err}",
    "lang.label": "Sprache",
    },
}
