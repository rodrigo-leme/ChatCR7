from flask import Flask, render_template, request, jsonify
import os
from utils.json_processor import JSONProcessor
from utils.gemini_client import GeminiClient
from utils.text_processor import TextProcessor
from utils.cache import LRUCache
from utils.keyword_mapper import KeywordMapper
from config import (
    EMBEDDING_MODEL, FAISS_INDEX_DIR, FAISS_JSON_INDEX_PATH, FAISS_JSON_MAPPING_PATH,
    EMBEDDING_BATCH_SIZE, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP,
    JSON_SIMILARITY_THRESHOLD, CACHE_SIZE, SIMILARITY_THRESHOLD,
    MAX_CHUNK_SIZE, MIN_CHUNK_SIZE, MAX_USER_MESSAGE_LENGTH, SPACY_MODEL, GEMINI_MODEL
)
import logging

#   logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info(f"Inicializando processadores e clientes...")
json_processor = JSONProcessor()
gemini_client = GeminiClient()
text_processor = TextProcessor()
keyword_mapper = KeywordMapper()
cache = LRUCache(CACHE_SIZE)

conversation_history = {}

@app.route('/')
def index():
    """Renderiza a página principal do chatbot."""
    initial_message = gemini_client.get_initial_greeting()
    return render_template('index.html', initial_message=initial_message)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint para processar mensagens do usuário e retornar respostas.
    
    Fluxo:
    1. Verifica se a mensagem é longa e resume se necessário
    2. Expande a consulta com termos relacionados usando o KeywordMapper
    3. Verifica se a resposta está no cache
    4. Busca nos JSONs
    5. Se não encontrar nos JSONs ou similaridade baixa, usa a API do Gemini
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message.strip():
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        original_message = user_message
            
        if len(user_message.split()) > MAX_USER_MESSAGE_LENGTH:
            logger.info(f"Mensagem longa detectada ({len(user_message.split())} palavras). Resumindo...")
            user_message = text_processor.summarize(user_message, MAX_USER_MESSAGE_LENGTH)
            logger.info(f"Mensagem resumida para {len(user_message.split())} palavras")
            
        if session_id not in conversation_history:
            conversation_history[session_id] = []
            
        conversation_history[session_id].append({
            'role': 'user',
            'content': original_message
        })
        
        if any(word in user_message.lower() for word in ['tchau', 'adeus', 'até logo', 'até mais']):
            response = gemini_client.get_goodbye_message()
            source = "persona"
        else:
            cached_response = cache.get(user_message)
            if cached_response:
                logger.info("Resposta encontrada no cache")
                response = cached_response
                source = "cache"
            else:
                processed_user_message = text_processor.preprocess(user_message)
                expanded_message = keyword_mapper.expand_query(processed_user_message)
                logger.info(f"Mensagem processada antes da expansão: {processed_user_message}")
                logger.info(f"Mensagem expandida: {expanded_message}")
                
                if expanded_message != processed_user_message: 
                    logger.info(f"Consulta expandida com termos relacionados: {expanded_message}")
                    related_terms = keyword_mapper.get_related_terms(processed_user_message)
                    if related_terms:
                        logger.info(f"Termos relacionados encontrados: {', '.join(related_terms)}")
                

                processed_message = text_processor.preprocess(expanded_message)
                
                json_results = json_processor.search(expanded_message, k=5)
                logger.info(f"Resultados da busca JSON (primeiros k={len(json_results)}):")
                for i, res in enumerate(json_results):
                    logger.info(f"  [{i+1}] ID: {res['id']}, Score: {res['score']:.4f}, Texto: {res['text'][:100]}...")
                
                if json_results and json_results[0]['score'] <= JSON_SIMILARITY_THRESHOLD:
                    logger.info(f"Informações encontradas nos JSONs (score: {json_results[0]['score']})")
                    
                    json_context = "Baseado nas seguintes informações dos nossos documentos:\n\n"
                    for result in json_results:
                        # Adiciona o ID do chunk e o sub_assunto ao contexto
                        sub_assunto = result['metadata'].get('sub_assunto', 'N/A')
                        json_context += f"- ID: {result['id']}\n"
                        json_context += f"  Subtópico: {sub_assunto}\n"
                        json_context += f"  Texto: {result['text']}\n"
                        json_context += f"  (Fonte: {result['id']})\n\n"
                    logger.info(f"Contexto JSON enviado ao Gemini:\n{json_context}")
                    
                    response = gemini_client.generate_response(
                        user_message,
                        conversation_history[session_id],
                        json_context
                    )
                    source = "json+gemini"
                else:
                    related_terms = keyword_mapper.get_related_terms(user_message)
                    if related_terms:
                        explicit_query = user_message + " " + " ".join(related_terms[:3])  #  3 termos
                        logger.info(f"Tentando busca com consulta explícita: {explicit_query}")
                        json_results = json_processor.search(explicit_query, k=3)
                        logger.info(f"Resultados da busca JSON (segunda tentativa, primeiros k={len(json_results)}):")
                        for i, res in enumerate(json_results):
                            logger.info(f"  [{i+1}] ID: {res['id']}, Score: {res['score']:.4f}, Texto: {res['text'][:100]}...")
                        
                        if json_results and json_results[0]['score'] <= JSON_SIMILARITY_THRESHOLD:
                            logger.info(f"Informações encontradas nos JSONs com termos explícitos (score: {json_results[0]['score']})")
                            
                            json_context = "Baseado nas seguintes informações dos nossos documentos:\n\n"
                            for result in json_results:
                                # Adiciona o ID do chunk e o sub_assunto ao contexto (segunda tentativa)
                                sub_assunto = result['metadata'].get('sub_assunto', 'N/A')
                                json_context += f"- ID: {result['id']}\n"
                                json_context += f"  Subtópico: {sub_assunto}\n"
                                json_context += f"  Texto: {result['text']}\n"
                                json_context += f"  (Fonte: {result['id']})\n\n"
                            logger.info(f"Contexto JSON (segunda tentativa) enviado ao Gemini:\n{json_context}")
                            
                            response = gemini_client.generate_response(
                                user_message,
                                conversation_history[session_id],
                                json_context
                            )
                            source = "json+gemini+keywords"
                        else:
                            logger.info("Nenhuma informação relevante encontrada. Gerando resposta com Gemini API")
                            response = gemini_client.generate_response(
                                user_message, 
                                conversation_history[session_id]
                            )
                            source = "gemini"
                    else:
                        logger.info("Nenhuma informação relevante encontrada. Gerando resposta com Gemini API")
                        response = gemini_client.generate_response(
                            user_message, 
                            conversation_history[session_id]
                        )
                        source = "gemini"
                
                if response and len(response) > 10:
                    cache.put(user_message, response)
        
        conversation_history[session_id].append({
            'role': 'assistant',
            'content': response
        })
        
        if len(conversation_history[session_id]) > 50:
            conversation_history[session_id] = conversation_history[session_id][-50:]
            
        return jsonify({
            'response': response,
            'source': source
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        return jsonify({
            'error': str(e),
            'response': gemini_client.persona['comportamento']['nao_entendeu']
        }), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Limpa o histórico de conversa de uma sessão específica."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in conversation_history:
            conversation_history[session_id] = []
            
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("APP.PY INICIADO: Lendo as últimas modificações do código.")
    text_processor = TextProcessor()
    json_processor = JSONProcessor()
    keyword_mapper = KeywordMapper()
    gemini_client = GeminiClient()
    app.run(debug=True)