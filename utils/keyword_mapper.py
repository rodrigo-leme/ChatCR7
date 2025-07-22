"""
Módulo para mapear palavras-chave relacionadas e sinônimos.

Este módulo permite melhorar a correspondência entre os termos usados pelos usuários
e os termos oficiais presentes nos documentos e FAQs.
"""

class KeywordMapper:
    def __init__(self):
        """Inicializa o mapeador de palavras-chave com termos relacionados."""
        

        self.synonym_map = {
            "SPTrans": ["bilhete único", "bilhete unico", "transporte público", "transporte publico", "carteirinha de ônibus", "carteirinha de onibus", "passe escolar", "meia passagem"],
            "matrícula": ["inscrição", "registro", "cadastro", "ingresso", "entrada", "adesão"],
            "rematrícula": ["renovação", "continuidade", "renovar matrícula"],
            "histórico escolar": ["histórico", "notas", "boletim", "desempenho acadêmico"],
            "carteirinha": ["identificação", "cartão estudante", "cartão de acesso", "crachá", "id estudantil"],
            "declaração": ["comprovante", "atestado", "certificado"],
            "documentos": ["pendência", "pendentes", "entrega", "lista", "status"],
            
            "secretaria": ["atendimento", "administração escolar", "administração acadêmica", "setor acadêmico"],
            "coordenação": ["coordenador", "coordenadora", "direção do curso", "chefia de departamento"],
            "financeiro": ["tesouraria", "setor de pagamentos", "departamento financeiro", "setor de cobranças"],
            "biblioteca": ["acervo", "livros", "consulta bibliográfica"],
            
            "trancamento": ["trancar", "suspender", "interromper", "pausa", "pausar curso"],
            "cancelamento": ["cancelar", "desistir", "encerrar vínculo", "abandono", "desligamento"],
            "transferência": ["transferir", "mudar de faculdade", "mudar de instituição", "trocar"],
            "aproveitamento": ["equivalência", "dispensa de disciplina", "validação de créditos", "aproveitamento de estudos"],
            
            "perder": ["perdido", "encontrado", "achados e perdidos", "achado"],
            "mensalidade": ["pagamento", "parcela", "valor mensal", "prestação", "cobrança", "vencimento"],
            "abono de faltas": ["abono", "falta", "frequência", "justificativa de falta", "dispensa de presença"],
            "boleto": ["fatura", "débito", "crédito", "pagamento", "acordo", "negociação"],
            "bolsa": ["desconto", "auxílio", "ajuda financeira", "apoio financeiro", "incentivo"],
            "FIES": ["financiamento estudantil", "crédito educativo", "financiamento de mensalidade"],
            "PROUNI": ["programa universidade para todos", "bolsa governo", "bolsa federal"],
            
            "calendário acadêmico": ["datas", "prazos", "agenda", "cronograma"],
            "férias": ["recesso", "descanso", "pausa entre semestres"],
            "formatura": ["colação de grau", "cerimônia de conclusão", "outorga de grau"],
            
            "prova": ["avaliação", "teste", "exame", "verificação"],
            "trabalho": ["atividade", "projeto", "tarefa", "exercício"],
            "TCC": ["trabalho de conclusão", "monografia", "projeto final", "trabalho final"],
            "dependência": ["dp", "disciplina pendente", "reprovação", "recuperação", "reprovei"],

            "portal do aluno": ["sistema acadêmico", "área do aluno", "intranet", "ambiente virtual", "portal acadêmico"],
            "AVA": ["ambiente virtual de aprendizagem", "plataforma de ensino", "sala virtual", "moodle"],
            "adobe": ["laboratório", "informática", "software", "computador", "Photoshop", "Acrobat", "Illustrator"],
            
            "EAD": ["ensino a distância", "curso online", "educação a distância", "remoto", "virtual"],
            "presencial": ["aula física", "no campus", "na faculdade", "unidade"],
            "semi-presencial": ["híbrido", "parte online parte presencial", "flexível", "phygital"]
        }
        
        self.thematic_keywords = {
            "financeiro": ["desconto", "preço", "valor", "custo", "pagamento", "parcela", "fatura", "débito", "crédito", "boleto", "mensalidade", "vencimento"],
            
            "processo_seletivo": ["vestibular", "prova", "processo seletivo", "inscrição", "vaga", 
                                 "classificação", "nota de corte", "edital", "cronograma", "lista de espera"],
            
            "documentação": ["documento", "certificado", "diploma", "comprovante", "protocolo", 
                            "identidade", "histórico", "certificação", "atestado"],
            
            "calendário": ["data", "prazo", "período", "início", "término", "final", "começo", "cronograma"]
        }
    
    def expand_query(self, query):
        """
        Expande a consulta do usuário com termos relacionados.
        
        Args:
            query (str): Consulta original do usuário
            
        Returns:
            str: Consulta expandida com termos relacionados
        """
        original_query = query.lower()
        expanded_terms = []
        
        # expansão no synonym_map
        for official_term, synonyms in self.synonym_map.items():
            if official_term.lower() in original_query:
                expanded_terms.extend(synonyms)
        
        for official_term, synonyms in self.synonym_map.items():
            for synonym in synonyms:
                if synonym.lower() in original_query:
                    expanded_terms.append(official_term)
                    expanded_terms.extend([s for s in synonyms if s.lower() != synonym.lower()])
                    break
        
        expanded_terms = list(set(expanded_terms))
        expanded_terms = [term for term in expanded_terms if term.lower() not in original_query]
        
        if not expanded_terms:
            return query
        
        expanded_query = query
        if expanded_terms:
            expanded_query += " " + " ".join(expanded_terms)
            
        return expanded_query
    
    def get_related_terms(self, query):
        """
        Obtém os termos relacionados à consulta do usuário.
        
        Args:
            query (str): Consulta original do usuário
            
        Returns:
            list: Lista de termos relacionados
        """
        query_lower = query.lower()
        related_terms = []
        
        for official_term, synonyms in self.synonym_map.items():
            if official_term.lower() in query_lower:
                related_terms.extend(synonyms)
            else:
                for synonym in synonyms:
                    if synonym.lower() in query_lower:
                        related_terms.append(official_term)
                        related_terms.extend([s for s in synonyms if s.lower() != synonym.lower()])
                        break
        
        related_terms = list(set(related_terms))
        
        return related_terms 