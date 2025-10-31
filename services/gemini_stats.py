"""
Sistema de Monitoramento de Uso do Gemini 2.5 Flash (FREE Tier)
Rastreia uso em tempo real e valida limites
"""

from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
import json

class GeminiStats:
    """
    Rastreador de estatísticas do Gemini 2.5 Flash
    
    FREE Tier Limits (verificado em 27/10/2025):
    - RPM (Requests Per Minute): 10
    - TPM (Tokens Per Minute): 250.000
    - RPD (Requests Per Day): 250
    - TPD (Tokens Per Day): Unlimited
    - Google Search RPD: 500 (FREE)
    
    Modelo: gemini-2.5-flash
    - Input Tokens: 1.048.576 (1M)
    - Output Tokens: 65.536 (64K)
    """
    
    def __init__(self):
        self.lock = Lock()
        
        # Limites FREE tier do Gemini 2.5 Flash
        self.RPM_LIMIT = 10        # Requests por minuto
        self.TPM_LIMIT = 250_000   # Tokens por minuto
        self.RPD_LIMIT = 250       # Requests por dia
        self.SEARCH_RPD_LIMIT = 500 # Google Search por dia
        
        # Contadores por usuário
        self.requests_minute = defaultdict(list)  # {user_id: [(timestamp, tokens)]}
        self.requests_day = defaultdict(list)     # {user_id: [(timestamp, tokens)]}
        self.searches_day = defaultdict(list)     # {user_id: [timestamps]}
        
        # Estatísticas globais
        self.total_requests = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_searches = 0
        
        # Histórico (últimas 24h)
        self.history = []
        
        # Cache de estatísticas (atualizado a cada minuto)
        self.cached_stats = {}
        self.last_cache_update = None
    
    def record_request(self, user_id, tokens_input=0, tokens_output=0):
        """
        Registra uma requisição ao Gemini
        
        Args:
            user_id: ID do usuário (ou None para global)
            tokens_input: Tokens de entrada
            tokens_output: Tokens de saída
        """
        with self.lock:
            now = datetime.now()
            total_tokens = tokens_input + tokens_output
            
            # Registra por usuário
            if user_id:
                self.requests_minute[user_id].append((now, total_tokens))
                self.requests_day[user_id].append((now, total_tokens))
            
            # Estatísticas globais
            self.total_requests += 1
            self.total_tokens_input += tokens_input
            self.total_tokens_output += tokens_output
            
            # Histórico
            self.history.append({
                'timestamp': now.isoformat(),
                'user_id': user_id,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'total_tokens': total_tokens
            })
            
            # Limpa histórico antigo (> 24h)
            cutoff = now - timedelta(hours=24)
            self.history = [h for h in self.history 
                          if datetime.fromisoformat(h['timestamp']) > cutoff]
    
    def record_search(self, user_id):
        """
        Registra uso do Google Search
        
        Args:
            user_id: ID do usuário
        """
        with self.lock:
            now = datetime.now()
            
            if user_id:
                self.searches_day[user_id].append(now)
            
            self.total_searches += 1
    
    def check_limits(self, user_id, estimated_tokens=0):
        """
        Verifica se o usuário pode fazer uma requisição
        
        Args:
            user_id: ID do usuário
            estimated_tokens: Estimativa de tokens da requisição
        
        Returns:
            (bool, str): (pode_fazer, mensagem_erro)
        """
        with self.lock:
            now = datetime.now()
            
            # Limpa dados antigos
            self._cleanup_old_data(user_id, now)
            
            # Verifica RPM
            requests_last_minute = len(self.requests_minute.get(user_id, []))
            if requests_last_minute >= self.RPM_LIMIT:
                return False, f"Limite de {self.RPM_LIMIT} requisições/minuto excedido. Aguarde."
            
            # Verifica TPM
            tokens_last_minute = sum(tokens for _, tokens in self.requests_minute.get(user_id, []))
            if tokens_last_minute + estimated_tokens > self.TPM_LIMIT:
                return False, f"Limite de {self.TPM_LIMIT:,} tokens/minuto excedido. Aguarde."
            
            # Verifica RPD
            requests_today = len(self.requests_day.get(user_id, []))
            if requests_today >= self.RPD_LIMIT:
                return False, f"Limite diário de {self.RPD_LIMIT} requisições excedido. Volte amanhã."
            
            return True, ""
    
    def check_search_limit(self, user_id):
        """
        Verifica se pode usar Google Search
        
        Args:
            user_id: ID do usuário
        
        Returns:
            (bool, str): (pode_fazer, mensagem_erro)
        """
        with self.lock:
            now = datetime.now()
            
            # Limpa buscas antigas (> 24h)
            cutoff = now - timedelta(days=1)
            if user_id in self.searches_day:
                self.searches_day[user_id] = [
                    ts for ts in self.searches_day[user_id] if ts > cutoff
                ]
            
            searches_today = len(self.searches_day.get(user_id, []))
            
            if searches_today >= self.SEARCH_RPD_LIMIT:
                return False, f"Limite de {self.SEARCH_RPD_LIMIT} buscas/dia excedido."
            
            return True, ""
    
    def _cleanup_old_data(self, user_id, now):
        """
        ✅ CORRIGIDO: Limpa dados antigos dos contadores com verificações de segurança
        """
        # Limpa requests_minute (> 1 minuto)
        cutoff_minute = now - timedelta(minutes=1)
        
        # ✅ CORRIGIDO: Verifica se user_id existe antes de limpar
        if user_id and user_id in self.requests_minute:
            self.requests_minute[user_id] = [
                (ts, tokens) for ts, tokens in self.requests_minute[user_id]
                if ts > cutoff_minute
            ]
        
        # Limpa requests_day (> 24h)
        cutoff_day = now - timedelta(days=1)
        
        if user_id and user_id in self.requests_day:
            self.requests_day[user_id] = [
                (ts, tokens) for ts, tokens in self.requests_day[user_id]
                if ts > cutoff_day
            ]
        
        # Limpa searches_day (> 24h)
        if user_id and user_id in self.searches_day:
            self.searches_day[user_id] = [
                ts for ts in self.searches_day[user_id] if ts > cutoff_day
            ]
    
    def get_user_stats(self, user_id):
        """
        Retorna estatísticas de um usuário
        
        Args:
            user_id: ID do usuário
        
        Returns:
            dict: Estatísticas do usuário
        """
        with self.lock:
            now = datetime.now()
            self._cleanup_old_data(user_id, now)
            
            requests_minute = len(self.requests_minute.get(user_id, []))
            requests_day = len(self.requests_day.get(user_id, []))
            searches_day = len(self.searches_day.get(user_id, []))
            
            tokens_minute = sum(tokens for _, tokens in self.requests_minute.get(user_id, []))
            tokens_day = sum(tokens for _, tokens in self.requests_day.get(user_id, []))
            
            return {
                'requests_minute': requests_minute,
                'requests_minute_limit': self.RPM_LIMIT,
                'requests_minute_percent': int((requests_minute / self.RPM_LIMIT) * 100),
                
                'requests_day': requests_day,
                'requests_day_limit': self.RPD_LIMIT,
                'requests_day_percent': int((requests_day / self.RPD_LIMIT) * 100),
                
                'tokens_minute': tokens_minute,
                'tokens_minute_limit': self.TPM_LIMIT,
                'tokens_minute_percent': int((tokens_minute / self.TPM_LIMIT) * 100),
                
                'tokens_day': tokens_day,
                
                'searches_day': searches_day,
                'searches_day_limit': self.SEARCH_RPD_LIMIT,
                'searches_day_percent': int((searches_day / self.SEARCH_RPD_LIMIT) * 100),
            }
    
    def get_global_stats(self):
        """
        Retorna estatísticas globais do sistema
        
        Returns:
            dict: Estatísticas globais
        """
        with self.lock:
            # Calcula totais das últimas 24h do histórico
            now = datetime.now()
            cutoff = now - timedelta(hours=24)
            
            recent_history = [
                h for h in self.history
                if datetime.fromisoformat(h['timestamp']) > cutoff
            ]
            
            requests_24h = len(recent_history)
            tokens_24h = sum(h['total_tokens'] for h in recent_history)
            
            # Usuários únicos
            unique_users = len(set(h['user_id'] for h in recent_history if h['user_id']))
            
            # Média de tokens por request
            avg_tokens = int(tokens_24h / requests_24h) if requests_24h > 0 else 0
            
            return {
                'total_requests': self.total_requests,
                'total_tokens_input': self.total_tokens_input,
                'total_tokens_output': self.total_tokens_output,
                'total_searches': self.total_searches,
                
                'requests_24h': requests_24h,
                'tokens_24h': tokens_24h,
                'unique_users_24h': unique_users,
                'avg_tokens_per_request': avg_tokens,
                
                'history': recent_history[-50:]  # Últimas 50 requisições
            }
    
    def get_limits_info(self):
        """
        Retorna informações sobre os limites do FREE tier
        
        Returns:
            dict: Informações de limites
        """
        return {
            'model': 'gemini-2.5-flash',
            'tier': 'FREE',
            'limits': {
                'rpm': self.RPM_LIMIT,
                'tpm': self.TPM_LIMIT,
                'rpd': self.RPD_LIMIT,
                'tpd': 'Unlimited',
                'google_search_rpd': self.SEARCH_RPD_LIMIT
            },
            'model_limits': {
                'max_input_tokens': 1_048_576,  # 1M
                'max_output_tokens': 65_536     # 64K
            },
            'pricing': 'Free (no cost)',
            'docs': 'https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash'
        }
    
    def export_stats(self):
        """
        Exporta todas as estatísticas em formato JSON
        
        Returns:
            str: JSON com todas as estatísticas
        """
        with self.lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'global': self.get_global_stats(),
                'limits': self.get_limits_info()
            }
            
            return json.dumps(data, indent=2)
    
    def get_stats(self):
        """
        Retorna estatísticas combinadas (compatibilidade)
        
        Returns:
            dict: Estatísticas
        """
        return {
            'global': self.get_global_stats()
        }
    
    def get_all_users_stats(self):
        """
        Retorna estatísticas de todos os usuários
        
        Returns:
            dict: {user_id: stats}
        """
        all_stats = {}
        
        for user_id in set(list(self.requests_minute.keys()) + list(self.requests_day.keys())):
            all_stats[user_id] = self.get_user_stats(user_id)
        
        return all_stats
    
    def reset_user(self, user_id):
        """
        Reseta estatísticas de um usuário
        
        Args:
            user_id: ID do usuário
        """
        with self.lock:
            if user_id in self.requests_minute:
                del self.requests_minute[user_id]
            if user_id in self.requests_day:
                del self.requests_day[user_id]
            if user_id in self.searches_day:
                del self.searches_day[user_id]


# Instância global
gemini_stats = GeminiStats()