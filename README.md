# Chatbot Católico - Coletor e API de Documentos

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Sobre o Projeto

Este projeto é uma plataforma completa para a coleta, processamento e consulta de documentos do site oficial do Vaticano. O objetivo final é servir como a base de conhecimento (backend) para um chatbot inteligente, capaz de responder perguntas sobre a doutrina e documentos da Igreja Católica com base em fontes oficiais.

A aplicação é dividida em dois componentes principais:
1.  **Crawler:** Um robô robusto que navega no site do Vaticano, baixa documentos em HTML e PDF, extrai o texto e gera metadados.
2.  **API:** Um servidor web que expõe os dados processados através de endpoints, incluindo uma funcionalidade de busca semântica para encontrar os documentos mais relevantes para uma determinada pergunta.

## ✨ Funcionalidades

* **Coleta Modular:** Crawler configurado para baixar documentos de uma lista de URLs iniciais.
* **Processamento de NLP:** Utiliza **spaCy** e **Sentence-Transformers** para:
    * Gerar resumos automáticos dos textos.
    * Criar embeddings vetoriais para busca semântica.
    * (Futuro) Extrair referências bíblicas e outras entidades.
* **Armazenamento Robusto:** Usa **Redis** para gerenciar a fila de documentos a serem processados.
* **API Inteligente:** Serve os dados através de uma API **FastAPI**, com um endpoint de busca que retorna documentos por similaridade de significado, não apenas por palavras-chave.
* **Estrutura Profissional:** O código é organizado de forma modular para facilitar a manutenção e a expansão.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3
* **API:** FastAPI
* **Banco de Dados (Fila):** Redis
* **NLP:** spaCy, Sentence-Transformers, PyTextRank
* **Web Scraping:** Requests, BeautifulSoup, PDFPlumber
* **Servidor:** Linux (Ubuntu 20.04 LTS recomendado)

## 🚀 Configuração do Ambiente

Siga os passos abaixo para configurar o ambiente em um servidor Linux (Ubuntu):

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/chatbot-catolico.git](https://github.com/seu-usuario/chatbot-catolico.git)
    cd chatbot-catolico
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Baixe o modelo de linguagem do spaCy:**
    ```bash
    python -m spacy download pt_core_news_lg
    ```

## 🏃 Como Usar

Após a configuração, você pode executar as principais funções do projeto.

* **Para iniciar a coleta de dados:**
    ```bash
    python main.py --crawl
    ```

* **Para iniciar o servidor da API (futuramente):**
    ```bash
    python main.py --api
    ```

## 📜 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
