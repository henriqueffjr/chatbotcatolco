import os
import json
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

# Importa a nossa classe de configuração
from config import Config

def configurar_logging():
    """
    Configura o sistema de logging para o projeto.
    Salva logs em um arquivo com rotação e também exibe no console.
    """
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    )
    
    # Handler para salvar em arquivo (com rotação para não ficar gigante)
    file_handler = RotatingFileHandler(
        os.path.join(Config.LOG_DIR, 'crawler.log'),
        maxBytes=5_000_000,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(log_formatter)
    
    # Handler para exibir no console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Configuração do logger raiz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Evita adicionar handlers duplicados em re-execuções
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

def criar_diretorios():
    """
    Cria todos os diretórios necessários para o projeto, com base no config.py.
    """
    dirs_to_create = [
        Config.BASE_DIR, Config.RAW_DIR, Config.TXT_DIR,
        Config.METADATA_DIR, Config.EMBEDDINGS_DIR, Config.LOG_DIR,
        Config.BACKUP_DIR, Config.CHECKPOINT_DIR
    ]
    for dir_path in dirs_to_create:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            logging.error(f"Erro ao criar diretório {dir_path}: {e}")
            raise

def gerar_nome_arquivo_hash(url: str) -> str:
    """
    Gera um nome de arquivo único e padronizado baseado no hash MD5 da URL.
    Ex: https://.../documento.html -> 5d41402abc4b2a76b9719d911017c592
    """
    return hashlib.md5(url.encode()).hexdigest()

def salvar_json(caminho_completo: str, dados: dict) -> bool:
    """
    Salva um dicionário em um arquivo JSON de forma segura.

    Args:
        caminho_completo (str): O caminho completo onde o arquivo será salvo.
        dados (dict): O dicionário a ser salvo.

    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário.
    """
    try:
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        return True
    except (IOError, TypeError) as e:
        logging.error(f"Falha ao salvar JSON em {caminho_completo}: {e}")
        return False

def carregar_json(caminho_completo: str) -> dict:
    """
    Carrega dados de um arquivo JSON de forma segura.

    Args:
        caminho_completo (str): O caminho completo do arquivo a ser lido.

    Returns:
        dict: O dicionário com os dados carregados ou um dicionário vazio se houver erro.
    """
    if not os.path.exists(caminho_completo):
        return {}
    try:
        with open(caminho_completo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Falha ao carregar JSON de {caminho_completo}: {e}")
        return {}

def is_valid_url(url: str) -> bool:
    """
    Valida se uma URL tem o formato correto e pertence ao domínio vatican.va.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.netloc.endswith("vatican.va")
    except ValueError:
        return False