import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from PIL import Image
import PyPDF2
import io

# 1. Configuração da Página (Visual Escuro e Expandido)
st.set_page_config(
    page_title="RINA - Auditoria Inteligente",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para um visual "Premium Aviation"
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #0066cc; color: white; font-weight: bold; border-radius: 5px; height: 50px; }
    .stButton>button:hover { background-color: #0052a3; }
    .metric-box { padding: 15px; background-color: #1f293d; border-radius: 8px; border-left: 5px solid #0066cc; }
    </style>
""", unsafe_allow_html=True)

# 2. Conexão Segura com o Motor Gemini 2.5
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.error("⚠️ Erro de Configuração: Chave GEMINI_API_KEY não encontrada no servidor Render.")
    st.stop()

# 3. Cabeçalho Principal
st.title("✈️ RINA - Sistema de Auditoria de Aeronavegabilidade")
st.subheader("Análise Inteligente de Prints, PDFs, Planilhas Excel e Textos")
st.markdown("---")

# 4. Painel de Indicadores de Produção (Métricas)
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown('<div class="metric-box"><b>Status do Sistema:</b><br><span style="color:#00ffcc;">🟢 Multiformato Ativo</span></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown('<div class="metric-box"><b>Formatos Suportados:</b><br>PDF, Excel, PNG, JPG, TXT</div>', unsafe_allow_html=True)
with col_m3:
    st.markdown('<div class="metric-box"><b>Foco Regulatório:</b><br>Padrões RINA / ANAC</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Divisão da Tela em Duas Colunas (Entrada vs. Saída)
col_esquerda, col_direita = st.columns([1, 1.3])

with col_esquerda:
    st.markdown("### 🛠️ Central de Upload e Dados")
    
    # Upload Universal de Arquivos
    arquivo_upload = st.file_uploader(
        "Carregue seu arquivo aqui (Print/Imagem, PDF ou Excel):", 
        type=["pdf", "xlsx", "xls", "png", "jpg", "jpeg", "txt"]
    )
    
    # Campo alternativo de texto manual
    texto_auditoria = st.text_area(
        "OU digite/cole observações adicionais manualmente se desejar:",
        height=150,
        placeholder="Adicione observações complementares ao arquivo subido (opcional)..."
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Botão de Comando Centralizado
    botao_analisar = st.button("🚀 INICIAR AUDITORIA INTELIGENTE")

with col_direita:
    st.markdown("### 📋 Relatório de Análise Técnica")
    
    if botao_analisar:
        conteudo_texto = ""
        conteudo_imagem = None
        
        with st.spinner("🧠 Processando arquivo e analisando dados com IA..."):
            try:
                # Se o usuário subiu um arquivo, vamos identificar o tipo e extrair os dados
                if arquivo_upload is not None:
                    nome_arquivo = arquivo_upload.name.lower()
                    
                    # 🔎 CASO 1: IMAGEM / PRINT (PNG, JPG)
                    if nome_arquivo.endswith(('.png', '.jpg', '.jpeg')):
                        conteudo_imagem = Image.open(arquivo_upload)
                        st.info(f"📸 Print/Imagem detectado: {arquivo_upload.name}")
                    
                    # 🔎 CASO 2: PDF
                    elif nome_arquivo.endswith('.pdf'):
                        leitor_pdf = PyPDF2.PdfReader(io.BytesIO(arquivo_upload.read()))
                        texto_extraido = ""
                        for pagina in leitor_pdf.pages:
                            texto_extraido += pagina.extract_text() or ""
                        conteudo_texto = f"[Conteúdo extraído do PDF {arquivo_upload.name}]:\n{texto_extraido}"
                        st.info(f"📄 Documento PDF lido com sucesso: {arquivo_upload.name}")
                    
                    # 🔎 CASO 3: EXCEL (.xlsx, .xls)
                    elif nome_arquivo.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(arquivo_upload)
                        # Converte a planilha em um formato de texto estruturado que a IA entende perfeitamente
                        planilha_texto = df.to_string()
                        conteudo_texto = f"[Dados extraídos da Planilha Excel {arquivo_upload.name}]:\n{planilha_texto}"
                        st.info(f"📊 Planilha Excel estruturada com sucesso: {arquivo_upload.name}")
                        
                    # 🔎 CASO 4: TEXTO SIMPLES (.txt)
                    elif nome_arquivo.endswith('.txt'):
                        conteudo_texto = arquivo_upload.read().decode("utf-8")
                
                # Adiciona o texto complementar digitado na caixa de texto se houver
                if texto_auditoria:
                    conteudo_texto += f"\n\n[Observações do Auditor]: {texto_auditoria}"
                
                # Engenharia de Prompt profissional focada em auditoria aeronáutica
                prompt_profissional = """
                Você é um Auditor de Aeronavegabilidade Sênior especialista em normas aeronáuticas (RINA e ANAC).
                Analise cuidadosamente os dados fornecidos (que podem ser textos de relatórios, dados estruturados de planilhas ou o conteúdo visual de um print/imagem de tela).
                
                Gere um parecer técnico extremamente profissional estruturado rigorosamente em:
                1. 📝 Resumo Técnico e Identificação do Caso
                2. ⚠️ Impactos e Riscos na Aeronavegabilidade (Diretrizes, Cartas de Serviço, Registros de Manutenção)
                3. 🔧 Plano de Ação Recomendado (Ações Corretivas com embasamento normativo técnico)
                
                Seja direto, formal e use termos técnicos de aviação.
                """
                
                # Executa a chamada com base no tipo de entrada que capturamos
                if conteudo_imagem:
                    # Se for imagem/print, passamos a imagem e o prompt juntos (Modo Multimodal)
                    resposta = model.generate_content([prompt_profissional, conteudo_imagem])
                elif conteudo_texto.strip():
                    # Se for texto, PDF ou Excel, enviamos o texto extraído
                    resposta = model.generate_content(f"{prompt_profissional}\n\nDados para análise:\n{conteudo_texto}")
                else:
                    st.warning("⚠️ Nenum dado foi fornecido. Suba um arquivo ou digite um texto.")
                    resposta = None
                
                if resposta:
                    st.success("✅ Análise Concluída com Sucesso!")
                    st.markdown(resposta.text)
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar ou analisar o arquivo: {e}")
    else:
        st.info("💡 Pronto para decolar. Suba um Print, PDF ou Planilha no painel da esquerda e clique no botão azul para gerar a análise.")
