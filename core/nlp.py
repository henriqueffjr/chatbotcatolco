import os
import spacy
import pytextrank  # A importação é necessária para registrar a extensão no spaCy
import numpy as np
import logging
from langdetect import detect, LangDetectException
from sentence_transformers import SentenceTransformer, util

# Importa a nossa classe de configuração
from config import Config

# Pega o logger configurado
logger = logging.getLogger(__name__)

def carregar_modelos_nlp():
    """
    Carrega e inicializa os modelos de IA (spaCy e Sentence Transformer).
    Esta função deve ser chamada uma vez no início da aplicação.

    Returns:
        tuple: Uma tupla contendo os objetos dos modelos (nlp, sentence_model).
    """
    try:
        logger.info(f"Carregando modelo spaCy: {Config.SPACY_MODEL}...")
        # Desabilitamos componentes não utilizados (ner, parser) para economizar memória.
        nlp = spacy.load(Config.SPACY_MODEL, exclude=["ner", "parser"])
        nlp.add_pipe("textrank")
        logger.info("Modelo spaCy carregado com sucesso.")
        
        logger.info(f"Carregando modelo Sentence Transformer: {Config.EMBEDDING_MODEL}...")
        sentence_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        logger.info("Modelo Sentence Transformer carregado com sucesso.")
        
        return nlp, sentence_model
    except OSError as e:
        logger.error(f"Erro ao carregar modelos de IA. Verifique se os modelos foram baixados corretamente. (python -m spacy download pt_core_news_lg). Erro: {e}")
        raise
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado ao carregar os modelos de IA: {e}")
        raise

def detectar_idioma(texto: str) -> str:
    """Detecta o idioma do texto usando langdetect."""
    try:
        # Pega apenas uma amostra do texto para detecção rápida
        amostra = texto[:500]
        lang = detect(amostra)
        return lang if lang in Config.LANGUAGES else "desconhecido"
    except LangDetectException:
        logger.warning("Não foi possível detectar o idioma. O texto pode ser muito curto ou ambíguo.")
        return "desconhecido"

def gerar_resumo(texto: str, nlp_model) -> str:
    """
    Gera um resumo do texto usando o algoritmo TextRank.

    Args:
        texto (str): O conteúdo a ser resumido.
        nlp_model: O objeto do modelo spaCy já carregado.

    Returns:
        str: O resumo do texto.
    """
    try:
        # Define um limite no tamanho do texto para evitar sobrecarga de memória
        doc = nlp_model(texto[:1_000_000])
        resumo = " ".join(
            str(sent) for sent in doc._.textrank.summary(limit_sentences=Config.SUMMARY_SENTENCES)
        )
        return resumo
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        return ""

def extrair_referencias_biblicas(texto: str, nlp_model) -> list[str]:
    """Extrai referências bíblicas do texto usando regras e o spaCy Matcher."""
    # Esta função pode ser expandida com mais padrões
    # Por enquanto, deixaremos o placeholder da lógica a ser implementada.
    # A implementação original era complexa e pode ser adicionada aqui depois.
    logger.debug("Extração de referências bíblicas ainda não implementada em detalhe.")
    return []


class SemanticSearch:
    """
    Gerencia a criação de embeddings e a execução de buscas semânticas.
    
    MELHORIA: Esta versão não carrega todos os embeddings para a RAM.
    Ela os carrega do disco sob demanda durante a busca, o que é mais lento
    mas usa muito menos memória, sendo mais escalável.
    """
    def __init__(self, sentence_model):
        self.model = sentence_model
        # Garante que o diretório de embeddings exista
        os.makedirs(Config.EMBEDDINGS_DIR, exist_ok=True)

    def criar_e_salvar_embedding(self, doc_id: str, texto: str):
        """
        Gera o embedding para um texto e o salva em um arquivo .npy.
        """
        try:
            embedding = self.model.encode(texto, show_progress_bar=False)
            filepath = os.path.join(Config.EMBEDDINGS_DIR, f"{doc_id}.npy")
            np.save(filepath, embedding)
            logger.info(f"Embedding para doc_id '{doc_id}' salvo em {filepath}")
        except Exception as e:
            logger.error(f"Falha ao criar ou salvar embedding para doc_id '{doc_id}': {e}")

    def buscar(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Realiza uma busca semântica comparando a query com os embeddings salvos em disco.
        """
        logger.info(f"Iniciando busca semântica para a query: '{query[:50]}...'")
        try:
            query_embedding = self.model.encode(query, show_progress_bar=False)
            
            similaridades = {}
            embedding_files = [f for f in os.listdir(Config.EMBEDDINGS_DIR) if f.endswith('.npy')]

            if not embedding_files:
                logger.warning("Nenhum embedding encontrado para a busca.")
                return []

            for filename in embedding_files:
                doc_id = filename[:-4]
                try:
                    doc_embedding = np.load(os.path.join(Config.EMBEDDINGS_DIR, filename))
                    sim = util.pytorch_cos_sim(query_embedding, doc_embedding).item()
                    similaridades[doc_id] = sim
                except Exception as e:
                    logger.warning(f"Não foi possível carregar ou processar o embedding '{filename}': {e}")
            
            # Ordena por similaridade e retorna os k melhores resultados
            sorted_docs = sorted(similaridades.items(), key=lambda item: item[1], reverse=True)[:top_k]
            
            return [{"doc_id": doc_id, "score": score} for doc_id, score in sorted_docs]

        except Exception as e:
            logger.error(f"Erro catastrófico durante a busca semântica: {e}", exc_info=True)
            return []
