from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        """
        Inicializa o cache LRU (Least Recently Used).
        
        Args:
            capacity (int): Capacidade máxima do cache
        """
        self.cache = OrderedDict()
        self.capacity = capacity
        
    def get(self, key):
        """
        Obtém um valor do cache, atualizando sua posição como mais recentemente usado.
        
        Args:
            key (str): Chave a ser buscada
            
        Returns:
            any: Valor associado à chave ou None se não encontrado
        """
        if key not in self.cache:
            return None
            
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
        
    def put(self, key, value):
        """
        Insere ou atualiza um valor no cache.
        
        Args:
            key (str): Chave a ser inserida/atualizada
            value (any): Valor a ser armazenado
        """
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
            
        # add o novo item
        self.cache[key] = value
        
    def clear(self):
        """Limpa todo o cache."""
        self.cache.clear()
        
    def __len__(self):
        """Retorna o número de itens no cache."""
        return len(self.cache)