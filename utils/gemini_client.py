import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from data.persona import get_persona, get_saudacao, get_despedida, get_resposta_contextual
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        """Inicializa o cliente da API do Gemini."""
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            self.persona = get_persona()
            print(f"Cliente Gemini inicializado com modelo: {GEMINI_MODEL}")
        except Exception as e:
            print(f"Erro ao inicializar cliente Gemini: {e}")
            raise
            
    def generate_response(self, prompt, conversation_history=None, json_context=None):
        """
        Gera uma resposta usando a API do Gemini.
        
        Args:
            prompt (str): Prompt do usuário
            conversation_history (list): Histórico da conversa
            json_context (str): Contexto extraído dos documentos JSON
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            context = ""
            if conversation_history and len(conversation_history) > 0:
                for message in conversation_history[-10:]:  # últimas 10 mensagens como contexto
                    role = "Usuário" if message['role'] == 'user' else "Assistente"
                    context += f"{role}: {message['content']}\n"

            # persona
            persona_instructions = f"""
            Você é {self.persona['nome']}, uma {self.persona['cargo']} de {self.persona['idade']}.
            
            Suas características de personalidade são:
            - Tom de voz: {self.persona['personalidade']['tom_de_voz']}
            - Nível de formalidade: {self.persona['personalidade']['nivel_formalidade']}
            - Traços principais: {', '.join(self.persona['personalidade']['tracos_principais'])}
            
            Suas especialidades incluem:
            {', '.join(self.persona['especialidades'])}
            
            Diretrizes de comunicação:
            - Usar linguagem acadêmica apropriada
            - usar emojis
            - Manter profissionalismo e empatia
            - Priorizar soluções claras e objetivas
            
            Se a pergunta envolver temas sensíveis ou restritos como {', '.join(self.persona['restricoes']['nao_fornecer'])}, 
            você deve informar que não pode fornecer essas informações por questões de segurança e privacidade.
            
            Se a situação exigir encaminhamento como em casos de {', '.join(self.persona['restricoes']['encaminhar_para_humano'])}, 
            você deve sugerir o contato com o setor apropriado.
            """
            
            if json_context:
                structured_context = """
                VOCÊ É UM ASSISTENTE DE ALUNOS E DEVE RESPONDER ÀS PERGUNTAS **SOMENTE** BASEANDO-SE NAS "INFORMAÇÕES RELEVANTES DOS DOCUMENTOS" FORNECIDAS ABAIXO. NÃO INVENTE INFORMAÇÕES NEM USE CONHECIMENTO PRÉVIO. SE A RESPOSTA NÃO PUDER SER FORMULADA DIRETAMENTE DO CONTEXTO, INDIQUE CLARAMENTE QUE A INFORMAÇÃO NÃO FOI ENCONTRADA.
                
                INFORMAÇÕES RELEVANTES DOS DOCUMENTOS:
                """
                structured_context += json_context

                structured_context += """\nDIRETRIZES ADICIONAIS DE RESPOSTA:\n"
                structured_context += "1. Ao responder sobre abono de faltas, baseie-se estritamente nas informações dos documentos, especialmente no chunk_4_2 e chunk_5_1_1. Se o motivo da ausência não estiver explicitamente listado como justificativa para ABONO (apenas reservista ou luto), informe que o abono não é possível. Se a informação sobre 'Licença Médica' (chunk_5_1_1) for relevante para a pergunta do usuário e a duração do afastamento for de 7 dias ou mais (para graduação), forneça os detalhes sobre o 'Regime Especial de Trabalhos Domiciliares' e a necessidade de protocolar o atestado original em até 72 horas via Portal Acadêmico. Doenças simples ou \"fiquei doente\" sem atestado e sem atender aos critérios de duração de licença médica NÃO são motivos válidos para abono de faltas ou regime especial.\n"
                structured_context += "2. Se a pergunta for sobre 'Achados e Perdidos' e o contexto incluir o chunk_1_1, informe que o local para procurar e registrar itens perdidos é a Central de Atendimento ao Aluno.\n"
                structured_context += "3. Extrema importância: Responda de forma concisa e direta, extraindo a informação principal do contexto.\n"
                structured_context += "4. Mantenha um tom profissional e empático, utilizando linguagem acadêmica apropriada.\n"
                structured_context += "5. Ao citar informações que contenham links (URLs), evite repetir a URL explicitamente se ela já estiver incorporada em uma frase ou instrução no texto do documento. Em vez disso, foque em integrar a informação do link na sua explicação de forma fluida, referenciando o local ou a ação sem duplicar a URL literal.\n"
                structured_context += "6. Se as informações fornecidas não forem suficientes para uma resposta completa ou não abordarem a pergunta, use a frase EXATA: 'Peço desculpas, mas não encontrei informações detalhadas sobre isso em meus documentos. Recomendo que você procure em outros canais de comunicação oficial para obter a informação completa.'\n"
                structured_context += "7. Evite generalizações ou conselhos que não estejam explicitamente nos documentos."
                structured_context += "8. Seja compreensivo e auxilie o usuário, caso ele não entenda a resposta, tente explicar de forma clara e objetiva."
                """


                full_prompt = f"{persona_instructions}\n\n{structured_context}\n\nHistórico da conversa:\n{context}\nUsuário: {prompt}\nAssistente:"
            else:
                full_prompt = f"{persona_instructions}\n\nHistórico da conversa:\n{context}\nUsuário: {prompt}\nAssistente:"
            
            try:
                token_count = self.model.count_tokens(full_prompt).total_tokens
                logger.info(f"Tokens enviados para a API do Gemini: {token_count}")
                response = self.model.generate_content(full_prompt)
                if response and hasattr(response, 'text'):
                    return response.text
                else:
                    print("Resposta vazia ou inválida do modelo")
                    return self.persona['comportamento']['nao_entendeu']
            except Exception as e:
                print(f"Erro específico na geração de conteúdo: {e}")
                return self.persona['comportamento']['nao_entendeu']
            
        except Exception as e:
            print(f"Erro ao gerar resposta com Gemini: {e}")
            return self.persona['comportamento']['nao_entendeu']

    def get_initial_greeting(self):
        """Retorna a saudação inicial da persona."""
        return get_saudacao()

    def get_goodbye_message(self):
        """Retorna a mensagem de despedida da persona."""
        return get_despedida()

    def get_contextual_response(self, context_type):
        """Retorna uma resposta contextual específica."""
        return get_resposta_contextual(context_type)
