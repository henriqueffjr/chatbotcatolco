import os
import argparse
import logging

# Importa os módulos principais da nossa aplicação
from config import Config
from core import utils
from core import crawler
# from api import server  # Deixamos comentado para quando formos ativar a API

def _carregar_urls_iniciais(caminho_arquivo: str) -> list[str]:
    """Carrega a lista de URLs iniciais de um arquivo de texto."""
    if not os.path.exists(caminho_arquivo):
        logging.warning(f"Arquivo de URLs não encontrado em {caminho_arquivo}. O crawler não terá por onde começar.")
        return []
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        # Retorna apenas as linhas não vazias e que são URLs válidas
        urls = [linha.strip() for linha in f if linha.strip()]
        urls_validas = [url for url in urls if utils.is_valid_url(url)]
        
    logging.info(f"{len(urls_validas)} URLs válidas carregadas de {caminho_arquivo}")
    return urls_validas

def main():
    """
    Função principal que inicializa e executa a aplicação.
    """
    # 1. Configura o logging para toda a aplicação
    utils.configurar_logging()
    
    # 2. Configura os argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Chatbot Católico - Coletor e API de Documentos do Vaticano")
    parser.add_argument(
        '--crawl', 
        action='store_true', 
        help="Executa o processo de coleta e processamento dos documentos."
    )
    parser.add_argument(
        '--api', 
        action='store_true', 
        help="Inicia o servidor da API para consulta dos documentos."
    )
    args = parser.parse_args()

    # 3. Executa a ação solicitada
    if args.crawl:
        caminho_urls = os.path.join(Config.PROJECT_ROOT, 'urls.txt')
        urls_iniciais = _carregar_urls_iniciais(caminho_urls)
        if urls_iniciais:
            crawler.iniciar_coleta_em_lote(urls_iniciais)
        else:
            logging.error("Nenhuma URL inicial válida para processar. Encerrando o crawler.")
            
    elif args.api:
        logging.info("Iniciando o servidor da API...")
        # server.iniciar_api() # Futura chamada para iniciar a API
        logging.warning("A funcionalidade da API será implementada nos próximos passos.")
        
    else:
        # Se nenhum argumento for fornecido, exibe a ajuda
        parser.print_help()

if __name__ == "__main__":
    main()