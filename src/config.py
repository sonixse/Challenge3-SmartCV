# Configuració central de SmartCV
# Canvia aquí i tot el pipeline ho recull automàticament.

# Model
MODEL = "llama3"          # model Ollama per a tots els agents LLM

# Lingüista
LINGUIST_TOP_K           = 50    # vacants a analitzar (filtre ChromaDB previ)
LINGUIST_MATCH_THRESHOLD = 0.87  # similitud cosinus mínima per a MATCH  (e5-base: rang comprimit 0.78-1.0)
LINGUIST_GREY_THRESHOLD  = 0.855 # per sota (NO MATCH); entre els dos, (GREY ZONE)

# Detectiu
DETECTIVE_MAX_WORKERS    = 8     # crides Ollama en paral·lel (ajusta a la teva GPU)
DETECTIVE_OLLAMA_TIMEOUT = 30.0  # segons màxims per crida
DETECTIVE_CONTEXT_WINDOW = 400   # caràcters de context del CV enviats al LLM

# Visionari
VISIONARY_TOP_N = 5              # quantes ofertes top s'analitzen per gaps i coaching

# Podium
PODIUM_TOP_N          = 10       # resultats màxims al rànquing final
PODIUM_WEIGHT_MUST    = 2.0      # pes skill must-have al score semàntic
PODIUM_WEIGHT_NICE    = 1.0      # pes skill nice-to-have
PODIUM_WEIGHT_OTHER   = 1.0      # pes tools i skills sense tipus
PODIUM_CREDIT_MATCH   = 1.0      # crèdit per MATCH
PODIUM_CREDIT_GREY    = 0.5      # crèdit per GREY ZONE (mig punt, per sinònims)
PODIUM_CREDIT_NO      = 0.0      # crèdit per NO MATCH

# Resiliència (compartit entre agents LLM)
MAX_RETRIES = 3
RETRY_DELAY = 2.0                # segons (es dobla a cada reintent)

# Rutes de dades locals
DB_PATH       = "data/smartcv.db"
CHROMA_PATH   = "data/chroma"
PROCESSED_DIR = "data/processed"
