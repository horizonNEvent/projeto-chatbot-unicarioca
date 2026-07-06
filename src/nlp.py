import re
import math
from collections import Counter

# Corpus de intenções e padrões para classificação NLP local
CORPUS = {
    'boas_vindas': {
        'padroes': [
            'oi', 'ola', 'hey', 'hello', 'bom dia', 'boa tarde',
            'boa noite', 'e ai', 'tudo bem', 'oi tudo bem', 'oi bot'
        ]
    },
    'despedida': {
        'padroes': [
            'tchau', 'ate logo', 'xau', 'bye', 'adeus',
            'ate mais', 'encerrar', 'sair', 'obrigado tchau'
        ]
    },
    'tema_geral': {
        'padroes': [
            'o que voce sabe', 'sobre o que fala', 'quais temas',
            'me ajude', 'quais assuntos', 'o que e formula 1',
            'me fale sobre f1', 'o que e f1'
        ]
    },
    'piloto': {
        'padroes': [
            'quem e verstappen', 'fale sobre hamilton', 'quem pilota pela red bull',
            'quem e leclerc', 'pilotos da f1', 'melhores pilotos',
            'quem sao os pilotos', 'quem e o melhor piloto',
            'piloto mais vitorioso', 'quantos titulos hamilton tem', 'fale sobre norris'
        ]
    },
    'equipe': {
        'padroes': [
            'quais sao as equipes', 'fale sobre red bull', 'fale sobre ferrari',
            'fale sobre mercedes', 'equipes da f1', 'construtores',
            'campeonato de construtores', 'melhor equipe', 'equipe mais vitoriosa'
        ]
    },
    'corrida': {
        'padroes': [
            'quando e o proximo gp', 'calendario f1', 'quantas corridas tem',
            'resultado da corrida', 'quem ganhou', 'gp do brasil',
            'monaco', 'silverstone', 'monza', 'circuito mais rapido'
        ]
    },
    'campeonato': {
        'padroes': [
            'classificacao', 'quem lidera', 'lider do campeonato',
            'pontuacao', 'tabela de pontos', 'standings',
            'quem esta na frente', 'campeonato 2024'
        ]
    },
    'consulta_csv': {
        'padroes': [
            'pontuacao dos pilotos', 'mostrar classificacao', 'tabela campeonato',
            'dados de verstappen', 'dados de hamilton', 'dados de leclerc',
            'dados de norris', 'dados de sainz', 'dados de russell',
            'dados de perez', 'quem tem mais pontos', 'top pilotos'
        ]
    }
}

LIMIAR_MINIMO = 0.35  # score mínimo para aceitar uma intenção

def normalizar(texto):
    """Remove acentos simples, converte para minúsculas e remove pontuação especial."""
    texto = str(texto).lower().strip()
    substituicoes = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u',
        'ç': 'c'
    }
    for orig, sub in substituicoes.items():
        texto = texto.replace(orig, sub)
    return re.sub(r'[^a-z0-9 ]', '', texto)


def levenshtein(s1, s2):
    """Retorna similaridade de Levenshtein entre 0 e 1 (1 = idêntico)."""
    s1, s2 = normalizar(s1), normalizar(s2)
    if s1 == s2:
        return 1.0
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 0.0
    
    # Matriz de programação dinâmica unidimensional (otimizada para espaço)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            custo = 0 if s1[i-1] == s2[j-1] else 1
            dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev[j-1] + custo)
            
    distancia = dp[n]
    return 1.0 - distancia / max(m, n)


def cosseno(s1, s2):
    """Retorna similaridade cosseno baseada em saco de palavras (Bag of Words) entre 0 e 1."""
    s1, s2 = normalizar(s1), normalizar(s2)
    v1 = Counter(s1.split())
    v2 = Counter(s2.split())
    palavras = set(v1) | set(v2)
    if not palavras:
        return 0.0
        
    dot = sum(v1[p] * v2[p] for p in palavras)
    mag1 = math.sqrt(sum(v ** 2 for v in v1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def similaridade_combinada(s1, s2, peso_lev=0.5, peso_cos=0.5):
    """Média ponderada entre similaridade de Levenshtein e Cosseno."""
    return peso_lev * levenshtein(s1, s2) + peso_cos * cosseno(s1, s2)


def detectar_intencao(texto_usuario):
    """Detecta a intenção do usuário cruzando a entrada com o CORPUS de padrões."""
    melhor_intencao = 'desvio'
    melhor_score = 0.0
    melhor_padrao = ''

    for intencao, dados in CORPUS.items():
        for padrao in dados['padroes']:
            score = similaridade_combinada(texto_usuario, padrao)
            if score > melhor_score:
                melhor_score = score
                melhor_intencao = intencao
                melhor_padrao = padrao

    if melhor_score < LIMIAR_MINIMO:
        return 'desvio', melhor_score, melhor_padrao

    return melhor_intencao, melhor_score, melhor_padrao
