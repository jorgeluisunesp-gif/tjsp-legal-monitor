# **⚖️ TJSP Legal Monitor**

Sistema de monitoramento automatizado de processos judiciais do Tribunal de Justiça de São Paulo (e-SAJ), com notificações em tempo real via Telegram.

*(Acima: O sistema acessando o e-SAJ, detectando uma nova movimentação e enviando o alerta instantâneo)*

## **🎯 Objetivo**

Este projeto resolve a necessidade de acompanhamento diário de movimentações processuais de forma passiva. Diferente de sistemas que exigem login constante, o **TJSP Legal Monitor** atua como um "sentinela", verificando periodicamente listas de processos e alertando apenas quando há novas movimentações relevantes.

**Destaques para Auditoria/Controle:**

* **Rastreabilidade:** Logs detalhados de cada execução em CSV.  
* **Resiliência:** Tratamento robusto de erros de conexão e instabilidade do tribunal.  
* **Segurança:** Gestão de credenciais via variáveis de ambiente (.env), sem exposição de dados sensíveis no código.

## **🚀 Funcionalidades**

* **Monitoramento Híbrido:**  
  * Verifica a data da última movimentação (detecta novidades do dia).  
  * Busca por palavras-chave específicas (ex: "Sentença", "Perícia").  
* **Integração Telegram:** Dispara alertas imediatos com o link e resumo da movimentação.  
* **Persistência de Sessão:** Suporte a perfis de navegador existentes para manter certificados digitais (A3/Token) ativos, evitando logins repetitivos.  
* **Modo Headless (Opcional):** Pode rodar em servidores sem interface gráfica.

## **🛠️ Tecnologias Utilizadas**

* **Core:** Python 3  
* **Automação:** Selenium Webdriver \+ GeckoDriver (Firefox)  
* **Parsing:** BeautifulSoup4  
* **Notificações:** Telegram Bot API  
* **Segurança:** python-dotenv

## **⚙️ Instalação e Uso**

1. **Clone o repositório**  
   git clone \[https://github.com/jorgeluisunesp-gif/tjsp-legal-monitor.git\](https://github.com/jorgeluisunesp-gif/tjsp-legal-monitor.git)  
   cd tjsp-legal-monitor

2. **Instale as dependências**  
   pip install \-r requirements.txt

3. Configure as Variáveis  
   Renomeie o arquivo .env.example para .env e preencha seus dados:  
   TELEGRAM\_TOKEN=seu\_token\_aqui  
   TELEGRAM\_CHAT\_ID=seu\_chat\_id

4. Prepare a Lista de Processos  
   Crie um arquivo processos.txt na raiz e adicione os números (formato CNJ ou limpo), um por linha.  
5. **Execute**  
   python main.py

## **🛡️ Disclaimer Ético**

Este software foi desenvolvido estritamente para fins de **produtividade pessoal e estudo**. O autor desencoraja o uso massivo ou abusivo que possa sobrecarregar os servidores do Tribunal de Justiça. O código implementa intervalos de espera (sleep) propositais entre as requisições para respeitar a infraestrutura pública.

## **📄 Licença**

Distribuído sob a licença MIT. Veja LICENSE para mais detalhes.