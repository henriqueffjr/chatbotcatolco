import os
import redis
import zipfile
import datetime
import logging

# Importa a nossa classe de configuração e funções utilitárias
from config import Config
from core import utils

# Pega o logger configurado em utils
logger = logging.getLogger(__name__)

class DocumentQueue:
    """
    Gerencia a fila de prioridades de URLs a serem processadas, utilizando Redis.
    Usa um Sorted Set do Redis para que URLs com maior prioridade sejam processadas primeiro.
    """
    def __init__(self):
        """Inicializa a conexão com o Redis."""
        try:
            self.conn = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                decode_responses=True # Decodifica respostas de bytes para string
            )
            # Testa a conexão na inicialização
            self.conn.ping()
            logger.info("Conexão com o Redis estabelecida com sucesso.")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Não foi possível conectar ao Redis em {Config.REDIS_HOST}:{Config.REDIS_PORT}. Verifique se o serviço está no ar. Erro: {e}")
            raise

    def adicionar_documento(self, url: str, prioridade: int = 0) -> bool:
        """
        Adiciona uma URL à fila de prioridades.
        Scores maiores são processados primeiro.

        Returns:
            bool: True se o item era novo e foi adicionado, False caso contrário.
        """
        try:
            # zadd retorna o número de elementos adicionados. 1 se for novo, 0 se já existia.
            return self.conn.zadd(Config.DOCUMENT_QUEUE_NAME, {url: prioridade}) == 1
        except redis.exceptions.RedisError as e:
            logger.error(f"Erro ao adicionar URL '{url}' na fila do Redis: {e}")
            return False

    def obter_proximo_documento(self) -> str | None:
        """
        Obtém e remove o documento de maior prioridade da fila.

        Returns:
            str | None: A URL do documento, ou None se a fila estiver vazia.
        """
        try:
            # zpopmax remove e retorna o item com o maior score (maior prioridade)
            result = self.conn.zpopmax(Config.DOCUMENT_QUEUE_NAME)
            # O resultado é uma lista de tuplas [(item, score)].
            return result[0][0] if result else None
        except redis.exceptions.RedisError as e:
            logger.error(f"Erro ao obter próximo documento da fila do Redis: {e}")
            return None

    def tamanho_fila(self) -> int:
        """Retorna o número de itens atualmente na fila."""
        try:
            return self.conn.zcard(Config.DOCUMENT_QUEUE_NAME)
        except redis.exceptions.RedisError as e:
            logger.error(f"Erro ao verificar tamanho da fila do Redis: {e}")
            return 0

class CheckpointManager:
    """Gerencia o checkpoint de URLs já processadas em um arquivo JSON."""
    def __init__(self):
        self.checkpoint_file = os.path.join(Config.CHECKPOINT_DIR, "processed_urls.json")
        self.processed_urls = self._carregar_checkpoint()

    def _carregar_checkpoint(self) -> set:
        """Carrega o conjunto de URLs processadas do arquivo."""
        dados = utils.carregar_json(self.checkpoint_file)
        return set(dados.get("urls_processadas", []))

    def salvar_checkpoint(self):
        """Salva o estado atual do checkpoint."""
        dados = {
            "ultima_atualizacao": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "total_documentos": len(self.processed_urls),
            "urls_processadas": list(self.processed_urls)
        }
        utils.salvar_json(self.checkpoint_file, dados)

    def adicionar_url_processada(self, url: str):
        """Adiciona uma nova URL ao checkpoint e salva em disco."""
        self.processed_urls.add(url)
        self.salvar_checkpoint()

    def url_ja_processada(self, url: str) -> bool:
        """Verifica se uma URL já foi processada."""
        return url in self.processed_urls

class BackupManager:
    """Gerencia a criação de backups compactados dos dados coletados."""
    @staticmethod
    def criar_backup_completo() -> str | None:
        """
        Cria um backup compactado em .zip de todos os diretórios de dados.
        
        Returns:
            str | None: O caminho para o arquivo de backup, ou None em caso de erro.
        """
        try:
            # Garante que o diretório de backup exista
            os.makedirs(Config.BACKUP_DIR, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filepath = os.path.join(Config.BACKUP_DIR, f'backup_{timestamp}.zip')
            
            logger.info(f"Criando backup em {backup_filepath}...")
            
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for dir_to_backup in [Config.RAW_DIR, Config.TXT_DIR, Config.METADATA_DIR, Config.EMBEDDINGS_DIR]:
                    if not os.path.isdir(dir_to_backup):
                        continue
                    for root, _, files in os.walk(dir_to_backup):
                        for file in files:
                            full_path = os.path.join(root, file)
                            # O 'arcname' é o caminho relativo dentro do zip para não criar toda a árvore de diretórios
                            arcname = os.path.relpath(full_path, Config.BASE_DIR)
                            zipf.write(full_path, arcname)
            
            logger.info(f"Backup criado com sucesso: {backup_filepath}")
            return backup_filepath
        except Exception as e:
            logger.error(f"Falha catastrófica ao criar backup: {e}", exc_info=True)
            return None
