import os

class Config:
    """
    Classe central de configuração para o projeto Chatbot Católico.
    Todos os parâmetros e caminhos são definidos aqui.
    """

    # --- Configurações Gerais do Crawler ---
    BASE_URL = "https://www.vatican.va"
    LANGUAGES = ["pt", "en", "la", "it", "es", "fr"]  # Idiomas de interesse
    MAX_DEPTH = 5  # Profundidade máxima de navegação (sugestão de aumento)
    MAX_FILES = 50000  # Limite de arquivos a serem baixados
    MAX_WORKERS = 4  # Número de threads paralelas para o download
    TIMEOUT = 30  # Timeout em segundos para requisições HTTP
    USER_AGENT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" # User agent para simular o Googlebot

    # --- Limites de Processamento ---
    MAX_PDF_PAGES = 100  # Evita processar PDFs excessivamente longos
    MAX_DOC_SIZE_MB = 25  # Tamanho máximo de um documento em MB
    
    # --- Caminhos (Paths) ---
    # O BASE_DIR aponta para um diretório no servidor. Ex: /home/ubuntu/chatbot_catolico
    # Usamos os.path.dirname(__file__) para garantir que os caminhos sejam relativos ao local do projeto.
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    BASE_DIR = os.path.join(PROJECT_ROOT, "vatican_docs")
    
    RAW_DIR = os.path.join(BASE_DIR, "raw")
    TXT_DIR = os.path.join(BASE_DIR, "txt")
    METADATA_DIR = os.path.join(BASE_DIR, "metadata")
    EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    BACKUP_DIR = os.path.join(BASE_DIR, "backups")
    CHECKPOINT_DIR = os.path.join(BASE_DIR, "checkpoints")

    # --- Configurações do Redis ---
    # Assume que o Redis será instalado localmente no mesmo servidor da aplicação.
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    DOCUMENT_QUEUE_NAME = "vatican_document_queue"
    
    # --- Modelos de IA ---
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    SPACY_MODEL = "pt_core_news_lg"
    SUMMARY_SENTENCES = 5  # Número de sentenças no resumo gerado

    # --- API e Monitoramento ---
    API_HOST = "0.0.0.0"  # Permite que a API seja acessível externamente
    API_PORT = 8000
    MONITOR_PORT = 8001