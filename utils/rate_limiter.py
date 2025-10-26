"""
Rate Limiter para FREE tier do Gemini
10 RPM, 250k TPM, 250 RPD
"""

from collections import defaultdict
from time import time
from flask import jsonify

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)  # {user_id: [timestamps]}
        self.daily_requests = defaultdict(int)  # {user_id: count}
        self.last_reset = {}  # {user_id: timestamp}
        
        # Limites FREE tier
        self.RPM = 10
        self.RPD = 250
    
    def check_limit(self, user_id):
        """
        Verifica se usuário pode fazer request
        
        Returns:
            (bool, str): (pode_fazer, mensagem_erro)
        """
        now = time()
        
        # Reset diário (meia-noite Pacific Time)
        if user_id not in self.last_reset or (now - self.last_reset[user_id]) > 86400:
            self.daily_requests[user_id] = 0
            self.last_reset[user_id] = now
        
        # Remove requests antigas (> 1 minuto)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < 60
        ]
        
        # Verifica RPM
        if len(self.requests[user_id]) >= self.RPM:
            return False, f"Limite de {self.RPM} requests/minuto excedido. Aguarde."
        
        # Verifica RPD
        if self.daily_requests[user_id] >= self.RPD:
            return False, f"Limite diário de {self.RPD} requests excedido. Volte amanhã."
        
        # Adiciona request
        self.requests[user_id].append(now)
        self.daily_requests[user_id] += 1
        
        return True, ""

# Instância global
rate_limiter = RateLimiter()