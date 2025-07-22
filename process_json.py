import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from utils.json_processor import JSONProcessor
from config import JSON_DIR, DATA_DIR, INDEX_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('process_json.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Iniciando o processamento de JSONs...")
    
    for directory in [DATA_DIR, JSON_DIR, INDEX_DIR]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Diretório verificado/criado: {directory}")
        
    json_processor = JSONProcessor()
    
    try:
        json_processor.process_json_directory(JSON_DIR)
        logger.info("Processamento de JSONs concluído com sucesso.")
    except Exception as e:
        logger.error(f"Erro durante o processamento de JSONs: {e}", exc_info=True)
        
if __name__ == "__main__":
    main() 