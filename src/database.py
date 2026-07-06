import os
import pandas as pd
from src.nlp import normalizar

# Resolvendo o caminho relativo para garantir portabilidade independente do diretório de execução
CSV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data/pilotos_f1_2024.csv')
)

def carregar_dados():
    """Carrega a base de dados de pilotos a partir do CSV."""
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Base de dados não encontrada no caminho esperado: {CSV_PATH}")
    return pd.read_csv(CSV_PATH)

def consultar_csv(texto_usuario):
    """
    Busca de forma dinâmica no CSV de pilotos se algum piloto foi mencionado na mensagem do usuário.
    Se encontrar, retorna os dados daquele piloto estruturados.
    Se não encontrar nenhum piloto específico, retorna a classificação dos Top 5 líderes.
    """
    df = carregar_dados()
    texto = normalizar(texto_usuario)

    piloto_correspondente = None

    # Mapeamento dinâmico baseado no conteúdo do CSV
    for _, row in df.iterrows():
        nome_completo = row['piloto']
        nome_norm = normalizar(nome_completo)
        partes_nome = nome_norm.split()
        
        # Sobrenome principal (última parte do nome)
        sobrenome = partes_nome[-1] if partes_nome else ""
        # Primeiro nome (primeira parte do nome)
        primeiro_nome = partes_nome[0] if partes_nome else ""

        # Verifica se o nome completo normalizado, ou o sobrenome, ou o nome completo está contido na mensagem
        # Evita correspondências curtas demais (ex: "Al" para Alexander Albon) para não gerar falsos positivos
        if nome_norm in texto:
            piloto_correspondente = row
            break
        elif sobrenome and sobrenome in texto and len(sobrenome) > 3:
            piloto_correspondente = row
            break
        elif primeiro_nome and primeiro_nome in texto and len(primeiro_nome) > 3:
            # Caso especial onde o usuário digita apenas o primeiro nome longo (ex: Fernando)
            piloto_correspondente = row
            break

    if piloto_correspondente is not None:
        linha = piloto_correspondente
        return (
            f"Piloto: {linha['piloto']} | Equipe: {linha['equipe']} | "
            f"Nacionalidade: {linha['nacionalidade']} | Pontos: {linha['pontos']} | "
            f"Vitórias: {linha['vitorias']} | Pódios: {linha['podios']} | Poles: {linha['poles']}"
        )

    # Fallback: classificação top 5 geral do campeonato
    top = df.sort_values('pontos', ascending=False).head(5)
    linhas = ['Aqui está a classificação do Top 5 do campeonato de construtores/pilotos 2024:']
    for i, (_, row) in enumerate(top.iterrows(), 1):
        linhas.append(f"  {i}. {row['piloto']} ({row['equipe']}) - {row['pontos']} pts")
    return '\n'.join(linhas)
