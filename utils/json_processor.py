import os
import json
import logging
import pickle
import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from config import (
    EMBEDDING_MODEL, FAISS_INDEX_DIR, FAISS_JSON_INDEX_PATH, FAISS_JSON_MAPPING_PATH,
    EMBEDDING_BATCH_SIZE, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP,
    SPACY_MODEL, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE
)
from utils.text_processor import TextProcessor

try:
    import spacy
    nlp = spacy.load(SPACY_MODEL)
except Exception as e:
    logging.error(f"Erro ao carregar o modelo spaCy '{SPACY_MODEL}': {e}")
    nlp = None

logger = logging.getLogger(__name__)

class JSONProcessor:
    def __init__(self):
        self.embedding_model = self._load_embedding_model()
        self.index = None
        self.id_to_text_map = {}
        self.text_processor = TextProcessor()
        self._load_or_create_index()
        
    def _load_embedding_model(self):
        logger.info(f"Usando dispositivo: {'cuda' if os.environ.get('CUDA_VISIBLE_DEVICES', None) else 'cpu'}")
        logger.info("Carregando modelo SentenceTransformer...")
        try:
            model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Dimensão dos embeddings: {model.get_sentence_embedding_dimension()}")
            logger.info("Modelo SentenceTransformer carregado com sucesso")
            return model
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo SentenceTransformer: {e}")
            raise

    def _load_or_create_index(self):
        if os.path.exists(FAISS_JSON_INDEX_PATH) and os.path.exists(FAISS_JSON_MAPPING_PATH):
            logger.info(f"Carregando índice JSON existente: {FAISS_JSON_INDEX_PATH}")
            self.index = faiss.read_index(FAISS_JSON_INDEX_PATH)
            with open(FAISS_JSON_MAPPING_PATH, 'rb') as f:
                self.id_to_text_map = pickle.load(f)
            logger.info(f"Índice carregado com sucesso. Total de vetores: {self.index.ntotal}")
        else:
            logger.info("Criando novo índice FAISS para JSONs...")
            embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(embedding_dimension) # L2 para distância euclidiana
            logger.info("Novo índice FAISS para JSONs criado.")
        os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

    def _save_index(self):
        if self.index is not None and self.index.ntotal > 0:
            logger.info(f"Salvando índice FAISS para JSONs com {self.index.ntotal} vetores...")
            faiss.write_index(self.index, FAISS_JSON_INDEX_PATH)
            with open(FAISS_JSON_MAPPING_PATH, 'wb') as f:
                pickle.dump(self.id_to_text_map, f)
            logger.info("Índice FAISS para JSONs salvo com sucesso.")
        else:
            logger.warning("Índice FAISS para JSONs vazio, não foi salvo.")

    def extract_chunks_from_json(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks = []
        for item in json_data:
            chunk_id = item.get("id")
            text = item.get("text")
            metadata = item.get("metadata", {})

            if not chunk_id or not text:
                logger.warning(f"Item JSON inválido encontrado (faltando 'id' ou 'text'): {item}")
                continue
            
            cleaned_text = self.text_processor.preprocess(text)
            if not cleaned_text:
                logger.warning(f"Texto limpo vazio para o chunk {chunk_id}")
                continue

            chunks.append({
                "id": chunk_id,
                "text": cleaned_text,
                "metadata": metadata
            })
        return chunks

    def process_json_directory(self, json_dir: str):
        logger.info(f"Iniciando processamento do diretório JSON: {json_dir}")
        if not os.path.exists(json_dir):
            logger.error(f"Diretório JSON não encontrado: {json_dir}")
            return
        
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        logger.info(f"Encontrados {len(json_files)} arquivos JSON em {json_dir}")

        all_chunks = []
        for json_file in json_files:
            json_path = os.path.join(json_dir, json_file)
            logger.info(f"Processando arquivo JSON: {json_file}")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                if isinstance(json_data, dict):
                    json_data = [json_data]

                chunks = self.extract_chunks_from_json(json_data)
                all_chunks.extend(chunks)
                logger.info(f"Extraídos {len(chunks)} chunks do arquivo {json_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do arquivo {json_file}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Erro inesperado ao processar {json_file}: {e}", exc_info=True)
        
        if not all_chunks:
            logger.warning("Nenhum chunk válido extraído de todos os arquivos JSON.")
            return

        logger.info(f"Total de chunks extraídos de todos os JSONs: {len(all_chunks)}")

        self.index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
        self.id_to_text_map = {}

        texts = [chunk['text'] for chunk in all_chunks]
        ids = [chunk['id'] for chunk in all_chunks]
        metadatas = [chunk['metadata'] for chunk in all_chunks]

        logger.info(f"Gerando embeddings para {len(texts)} textos...")
        all_embeddings = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch_texts = texts[i:i + EMBEDDING_BATCH_SIZE]
            batch_embeddings = self.embedding_model.encode(batch_texts, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Lote {i//EMBEDDING_BATCH_SIZE + 1} de embeddings gerado.")
        
        embeddings_array = np.array(all_embeddings).astype('float32')
        logger.info(f"Embeddings gerados. Shape: {embeddings_array.shape}")

        self.index.add(embeddings_array)
        logger.info(f"{self.index.ntotal} vetores adicionados ao índice FAISS.")

        for i, chunk_id in enumerate(ids):
            self.id_to_text_map[chunk_id] = {
                'text': all_chunks[i]['text'],
                'metadata': all_chunks[i]['metadata']
            }
        
        self._save_index()
        logger.info("Processamento de diretório JSON concluído e índice salvo.")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Índice JSON vazio, não há documentos para buscar")
            return []

        cleaned_query = self.text_processor.preprocess(query)
        if not cleaned_query:
            return []
            
        query_embedding = self.embedding_model.encode([cleaned_query]).astype('float32')
        
        D, I = self.index.search(query_embedding, k)
        
        results = []
        for i in range(k):
            if I[0][i] != -1:
                chunk_id = list(self.id_to_text_map.keys())[I[0][i]]
                score = D[0][i]  # D é a distância, menor é melhor
                original_text = self.id_to_text_map[chunk_id]['text']
                metadata = self.id_to_text_map[chunk_id]['metadata']
                results.append({'id': chunk_id, 'score': score, 'text': original_text, 'metadata': metadata})
                
        return results 