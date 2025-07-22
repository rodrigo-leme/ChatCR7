import os
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "jsons")
INDEX_DIR = os.path.join(DATA_DIR, "indices")

# --- API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

# --- Embeddings ---
EMBEDDING_MODEL = "distiluse-base-multilingual-cased-v2"
EMBEDDING_BATCH_SIZE = 100

# --- RAG ---
RAG_TOP_K = 5
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 100

FAISS_INDEX_DIR = os.path.join(DATA_DIR, "indices")
FAISS_JSON_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, "json_docs.index")
FAISS_JSON_MAPPING_PATH = os.path.join(FAISS_INDEX_DIR, "json_mapping.pkl")

CACHE_SIZE = 1000
SIMILARITY_THRESHOLD = 0.75
JSON_SIMILARITY_THRESHOLD = 1.30
#JSON_SIMILARITY_THRESHOLD = 1.0

SPACY_MODEL = "pt_core_news_md"

MAX_CHUNK_SIZE = 400
MIN_CHUNK_SIZE = 50
CHUNK_OVERLAP = 100

MAX_CONTEXT_LENGTH = 2000
MAX_HISTORY_LENGTH = 5
MAX_USER_MESSAGE_LENGTH = 100

MIN_SIMILARITY_SCORE = 0.7
MAX_CHUNK_SIMILARITY = 0.8

for directory in [DATA_DIR, JSON_DIR, FAISS_INDEX_DIR]:
    os.makedirs(directory, exist_ok=True)
    print(f"Diretório criado/verificado: {directory}")