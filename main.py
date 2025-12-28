import time
import re
import os
import requests  # NECESSÁRIO INSTALAR: pip install requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Carrega variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO TELEGRAM ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- CONFIGURAÇÃO PERFIL FIREFOX (PERSISTÊNCIA) ---
# Cole aqui o caminho do 'about:profiles' para manter extensões e certificado
# Exemplo: r"C:\Users\Jorge\AppData\Roaming\Mozilla\Firefox\Profiles\xxxx.default-release"
# Deixe vazio "" se quiser usar um perfil temporário novo
CAMINHO_PERFIL_FIREFOX = r"" 

# --- CONFIGURAÇÃO ARQUIVOS ---
ARQUIVO_ENTRADA = 'processos.txt'
ARQUIVO_SAIDA = 'resultados_monitoramento.csv'
URL_INICIAL = "https://esaj.tjsp.jus.br/cpopg/open.do"

def enviar_telegram(mensagem):
    """Envia alerta para o celular com tratamento de erros de Token."""
    token_limpo = TELEGRAM_TOKEN.strip().replace(" ", "")
    if token_limpo.lower().startswith('bot') and len(token_limpo) > 3 and token_limpo[3].isdigit():
        token_limpo = token_limpo[3:]
    
    chat_id_limpo = TELEGRAM_CHAT_ID.strip().replace(" ", "")

    if "SEU_TOKEN" in token_limpo or not token_limpo:
        return # Silencia erro se não configurado

    try:
        url = f"https://api.telegram.org/bot{token_limpo}/sendMessage"
        data = {"chat_id": chat_id_limpo, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"❌ Erro de Conexão Telegram: {e}")

def formatar_numero_processo(numero_processo_raw):
    numeros = re.sub(r'\D', '', numero_processo_raw)
    if len(numeros) != 20:
        return None, None
    numero_digito_ano = numeros[:13]
    foro = numeros[-4:]
    return numero_digito_ano, foro

def configurar_driver():
    options = FirefoxOptions()
    
    # Lógica de Perfil Persistente
    if CAMINHO_PERFIL_FIREFOX:
        print(f"🔄 Carregando perfil do usuário: {CAMINHO_PERFIL_FIREFOX}")
        options.add_argument("-profile")
        options.add_argument(CAMINHO_PERFIL_FIREFOX)
    else:
        print("⚠️ Usando perfil temporário (extensões não serão salvas).")

    try:
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Erro crítico ao abrir navegador: {e}")
        print("DICA: Se usou um perfil existente, certifique-se de fechar o Firefox antes de rodar.")
        return None

def verificar_processo(driver, numero_processo, palavra_busca):
    """
    Retorna uma tupla: (Status para CSV, Mensagem para Telegram ou None)
    """
    # CORREÇÃO DE LÓGICA: Garantir que estamos na tela de pesquisa ANTES de começar
    try:
        driver.get(URL_INICIAL)
    except:
        return "Erro de Conexão ao abrir busca", None

    numero_unificado, foro = formatar_numero_processo(numero_processo)
    
    if not numero_unificado:
        return "Número Inválido", None

    try:
        # 1. Preenche campos
        campo_processo = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado"))
        )
        campo_processo.clear()
        campo_processo.send_keys(numero_unificado)
        
        campo_foro = driver.find_element(By.ID, "foroNumeroUnificado")
        campo_foro.clear()
        campo_foro.send_keys(foro)
        
        driver.find_element(By.ID, "botaoConsultarProcessos").click()
        
        # 2. Seleção de Processos (Rádio Buttons)
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "listagemDeProcessos"))
            )
            radio = driver.find_element(By.CSS_SELECTOR, f"input[type='radio'][value*='{numero_unificado}']")
            radio.click()
            driver.find_element(By.ID, "botaoEnviarIncidente").click()
        except TimeoutException:
            pass 

        # 3. Espera a página carregar
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "tabelaTodasMovimentacoes"))
        )

        # 4. Extração
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        #hoje_str = datetime.now().strftime("%d/%m/%Y")
        hoje_str = "22/07/2025"
        
        tabela = soup.find('tbody', id='tabelaTodasMovimentacoes')
        status_final = "Sem novidades"
        msg_telegram = None

        if tabela:
            ultima_linha = tabela.find('tr')
            if ultima_linha:
                colunas = ultima_linha.find_all('td')
                if len(colunas) >= 3:
                    data_mov = colunas[0].get_text(strip=True)
                    desc_mov = colunas[2].get_text(strip=True)

                    if data_mov == hoje_str:
                        status_final = f"MOVIMENTOU HOJE: {desc_mov[:50]}..."
                        msg_telegram = (
                            f"🚨 **Movimentação Detectada!**\n\n"
                            f"📂 Proc: `{numero_processo}`\n"
                            f"📅 Data: {data_mov}\n"
                            f"📝 Desc: {desc_mov}"
                        )
                    else:
                        status_final = f"Última em {data_mov}"

        # Backup Palavra Chave
        if palavra_busca and palavra_busca.lower() in soup.get_text().lower():
            status_final += f" | Palavra '{palavra_busca}' Encontrada!"
            if not msg_telegram: 
                msg_telegram = f"🔍 Palavra '{palavra_busca}' encontrada no processo {numero_processo}!"

        return status_final, msg_telegram

    except TimeoutException:
        return "Processo não encontrado / Timeout", None
    except Exception as e:
        return f"Erro: {str(e)}", None

def main():
    print("="*50)
    print("MONITOR ESAJ V3 - PERFIL PERSISTENTE")
    print("="*50)
    
    # Verifica o caminho do perfil antes de tentar abrir
    if CAMINHO_PERFIL_FIREFOX and not os.path.exists(CAMINHO_PERFIL_FIREFOX):
        print(f"❌ ERRO: O caminho do perfil não existe:\n{CAMINHO_PERFIL_FIREFOX}")
        print("Copie o 'Diretório Raiz' de about:profiles corretamente.")
        return

    driver = configurar_driver()
    if not driver:
        return
    
    try:
        driver.get(URL_INICIAL)
        print("\n⚠️  O navegador foi aberto com seu perfil.")
        print("Se necessário, faça o LOGIN manual (o certificado deve estar pronto).")
        input("👉 Pressione ENTER aqui quando estiver logado para começar...")
        
        palavra_busca = input("Digite a palavra-chave (ou ENTER para pular): ").strip()

        if not os.path.exists(ARQUIVO_ENTRADA):
            with open(ARQUIVO_ENTRADA, 'w') as f:
                f.write("1000000-00.2023.8.26.0000")
            print(f"Arquivo '{ARQUIVO_ENTRADA}' criado. Preencha e reinicie.")
            return

        with open(ARQUIVO_ENTRADA, 'r', encoding='utf-8') as f_in, \
             open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f_out:
            
            f_out.write("NumeroDoProcesso,Status,DataVerificacao\n")
            processos = [line.strip() for line in f_in if line.strip() and not line.startswith('#')]
            total = len(processos)
            
            print(f"\n🚀 Iniciando monitoramento de {total} processos...")

            for i, num_proc in enumerate(processos, 1):
                num_proc_limpo = num_proc.split('#')[0].strip()
                print(f"[{i}/{total}] Verificando {num_proc_limpo}...", end="")
                
                status, msg_alerta = verificar_processo(driver, num_proc_limpo, palavra_busca)
                print(f" -> {status}")
                
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f_out.write(f'"{num_proc_limpo}","{status}","{data_hora}"\n')
                
                if msg_alerta:
                    enviar_telegram(msg_alerta)

                time.sleep(2) # Delay um pouco menor já que volta pra home

            print(f"\n✅ Concluído! Verifique '{ARQUIVO_SAIDA}'.")

    finally:
        if driver:
            driver.quit()
            print("Navegador fechado.")

if __name__ == "__main__":
    main()