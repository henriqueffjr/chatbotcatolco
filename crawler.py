import os
import uuid
import hashlib
import logging
import requests
import pdfplumber
import html2text
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Importa nossos módulos customizados
from config import Config
from core import utils
from core.nlp import SemanticSearch
from core.storage import CheckpointManager

# Pega o logger configurado
logger = logging.getLogger(__name__)

def _criar_sessao_http() -> requests.Session:
    """Cria uma sessão de requests com retentativas automáticas para robustez."""
    session = requests.Session()
    session.headers.update({"User-Agent": Config.USER_AGENT})
    
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session

def _baixar_documento(url: str, session: requests.Session) -> bytes | None:
    """Baixa o conteúdo de uma URL usando a sessão fornecida."""
    try:
        response = session.get(url, timeout=Config.TIMEOUT)
        response.raise_for_status()
        
        if len(response.content) > Config.MAX_DOC_SIZE_MB * 1024 * 1024:
            logger.warning(f"Documento em {url} excedeu o tamanho máximo de {Config.MAX_DOC_SIZE_MB}MB.")
            return None
            
        return response.content
    except requests.RequestException as e:
        logger.error(f"Falha no download de {url}: {e}")
        return None

def _converter_conteudo_para_texto(content: bytes, url: str) -> str:
    """Converte o conteúdo bruto (bytes) para texto puro, seja de PDF ou HTML."""
    try:
        if url.lower().endswith(".pdf"):
            # Usamos um arquivo temporário para o pdfplumber ler
            with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
                temp_pdf.write(content)
                temp_pdf.flush()
                texto_completo = []
                with pdfplumber.open(temp_pdf.name) as pdf:
                    if len(pdf.pages) > Config.MAX_PDF_PAGES:
                        logger.warning(f"PDF {url} tem mais de {Config.MAX_PDF_PAGES} páginas e será ignorado.")
                        return ""
                    for page in pdf.pages:
                        texto_completo.append(page.extract_text() or "")
                return "\n".join(texto_completo)
        else:
            # Para HTML e outros formatos, usamos html2text
            return html2text.html2text(content.decode('utf-8', errors='ignore'))
    except Exception as e:
        logger.error(f"Falha ao converter conteúdo de {url} para texto: {e}")
        return ""

def processar_documento(url: str, session: requests.Session, checkpoint_manager: CheckpointManager, semantic_search: SemanticSearch, nlp_models: tuple):
    """
    Orquestra o processo completo de um único documento:
    Download -> Conversão -> Geração de Metadados -> Salvamento.
    """
    nlp_model, sentence_model = nlp_models

    if checkpoint_manager.url_ja_processada(url):
        logger.debug(f"URL já processada, pulando: {url}")
        return None

    logger.info(f"Iniciando processamento de: {url}")
    
    conteudo_bruto = _baixar_documento(url, session)
    if not conteudo_bruto:
        return None

    texto_extraido = _converter_conteudo_para_texto(conteudo_bruto, url)
    if not texto_extraido or len(texto_extraido) < 100: # Ignora documentos com muito pouco texto
        logger.warning(f"Texto extraído de {url} é muito curto ou vazio. Pulando.")
        return None
        
    doc_hash = utils.gerar_nome_arquivo_hash(url)
    doc_id = str(uuid.uuid4())
    formato = "pdf" if url.lower().endswith(".pdf") else "html"
    
    # Gerar Metadados
    metadados = {
        "id": doc_id,
        "doc_hash": doc_hash,
        "url": url,
        "formato": formato,
        "data_coleta": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tamanho_bytes_texto": len(texto_extraido.encode('utf-8')),
        "idioma": nlp.detectar_idioma(texto_extraido),
        "resumo": nlp.gerar_resumo(texto_extraido, nlp_model),
        "referencias_biblicas": nlp.extrair_referencias_biblicas(texto_extraido, nlp_model)
    }

    # Salvar artefatos
    utils.salvar_json(os.path.join(Config.METADATA_DIR, f"{doc_hash}.json"), metadados)
    with open(os.path.join(Config.TXT_DIR, f"{doc_hash}.txt"), 'w', encoding='utf-8') as f:
        f.write(texto_extraido)
    with open(os.path.join(Config.RAW_DIR, f"{doc_hash}.{formato}"), 'wb') as f:
        f.write(conteudo_bruto)
        
    # Criar e salvar embedding
    semantic_search.criar_e_salvar_embedding(doc_id, texto_extraido)

    # Marcar como processado no final
    checkpoint_manager.adicionar_url_processada(url)
    logger.info(f"Documento de {url} processado e salvo com sucesso. ID: {doc_id}")
    return url

def iniciar_coleta_em_lote(lista_urls: list[str]):
    """
    Função principal que gerencia o pool de threads para coletar documentos em paralelo.
    """
    logger.info("="*50)
    logger.info("INICIANDO PROCESSO DE COLETA EM LOTE")
    logger.info(f"Total de URLs para verificar: {len(lista_urls)}")
    logger.info("="*50)

    utils.criar_diretorios()
    
    # Inicializa os objetos necessários
    checkpoint_manager = CheckpointManager()
    nlp_models = nlp.carregar_modelos_nlp()
    semantic_search = SemanticSearch(nlp_models[1]) # Passa o sentence_model
    http_session = _criar_sessao_http()

    urls_a_processar = [url for url in lista_urls if not checkpoint_manager.url_ja_processada(url)]
    
    if not urls_a_processar:
        logger.info("Nenhuma URL nova para processar. Todos os documentos já estão atualizados.")
        return

    logger.info(f"URLs novas a serem processadas: {len(urls_a_processar)}")
    
    processados_nesta_sessao = 0
    with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        # Submete as tarefas para o executor
        future_to_url = {
            executor.submit(processar_documento, url, http_session, checkpoint_manager, semantic_search, nlp_models): url 
            for url in urls_a_processar
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    processados_nesta_sessao += 1
            except Exception as e:
                logger.error(f"Erro ao processar a future para a URL {url}: {e}", exc_info=True)

    logger.info("="*50)
    logger.info("PROCESSO DE COLETA EM LOTE CONCLUÍDO")
    logger.info(f"Total de documentos processados nesta sessão: {processados_nesta_sessao}")
    logger.info("="*50)