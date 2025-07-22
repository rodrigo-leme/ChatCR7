import spacy
import numpy as np
from config import SPACY_MODEL
import os

class TextProcessor:
    def __init__(self):
        """Inicializa o processador de texto com o modelo spaCy."""
        print(f"Carregando modelo spaCy: {SPACY_MODEL}")
        try:
            self.nlp = spacy.load(SPACY_MODEL)
        except OSError:
            print(f"Modelo {SPACY_MODEL} não encontrado. Baixando...")
            os.system(f"python -m spacy download {SPACY_MODEL}")
            self.nlp = spacy.load(SPACY_MODEL)
        print("Modelo spaCy carregado com sucesso!")

    def preprocess(self, text):
        """
        Pré-processa o texto para reduzir tokens e manter apenas informações relevantes.
        
        Args:
            text (str): Texto a ser processado
            
        Returns:
            str: Texto processado
        """
        if not text or not text.strip():
            return ""
            
        doc = self.nlp(text)
        
        filtered_tokens = [
            token.lemma_ for token in doc
            #if not token.is_punct
            if not token.is_stop and not token.is_punct 
        ]
        
        
        entities = [ent.text for ent in doc.ents]
        
        
        processed_text = " ".join(filtered_tokens + entities)
        
        return processed_text
    
    def summarize(self, text, max_length=150):
        """
        Sumariza textos longos para reduzir o consumo de tokens.
        
        Args:
            text (str): Texto a ser sumarizado
            max_length (int): Comprimento máximo do texto (em palavras) antes de ser sumarizado
            
        Returns:
            str: Texto original ou sumarizado
        """
        if not text or not text.strip():
            return ""
            
        words = text.split()
        if len(words) <= max_length:
            return text
            
        doc = self.nlp(text)
        
        sentences = [sent for sent in doc.sents]
        if not sentences:
            return text[:500]  
            
        keyword_freq = {}
        for token in doc:
            if not token.is_stop and not token.is_punct and len(token.text) > 2:
                keyword_freq[token.lemma_] = keyword_freq.get(token.lemma_, 0) + 1
                
        for ent in doc.ents:
            for token in ent:
                if token.lemma_ in keyword_freq:
                    keyword_freq[token.lemma_] *= 2
        
        sentence_scores = {}
        for i, sent in enumerate(sentences):
            score = 0
            for token in sent:
                if token.lemma_ in keyword_freq:
                    score += keyword_freq[token.lemma_]
            
            if i < len(sentences) * 0.2 or i > len(sentences) * 0.8:
                score *= 1.5
                
            sentence_scores[sent] = score / max(len(sent), 1)
        
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        top_sentences = top_sentences[:min(5, len(top_sentences))]
        
        selected_sentences = [sent for sent, _ in sorted(top_sentences, key=lambda x: sentences.index(x[0]))]
        
        summary = " ".join([sent.text for sent in selected_sentences])
        
        return summary
    
    def get_embedding(self, text):
        """
        Gera embedding para o texto usando spaCy.
        
        Args:
            text (str): Texto para gerar embedding
            
        Returns:
            numpy.ndarray: Vetor de embedding normalizado
        """
        doc = self.nlp(text)
        
        
        embedding = doc.vector
        
        
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding