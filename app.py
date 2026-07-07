import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from PIL import Image
import PyPDF2
import io

# 1. Configuração Visual da Página (Tema Escuro Avançado)
st.set_page_config(
    page_title="RINA - Auditoria Inteligente",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização para deixar os botões bem destacados e nomeados
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #0066cc; color: white; font-weight: bold; border-radius: 5px; height: 50px; font-size: 16px; }
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

# 3. Cabeçalho do Cockpit
st.title("✈️ RINA - Sistema de Auditoria de Aeronavegabilidade")
st.subheader("Análise Inteligente Multiformato: Prints, PDFs, Planilhas Excel e Textos")
st.markdown("---")

# 4. Indicadores de Status (Painel de Controle)
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown('<div class="metric-box"><b>Status do Leitor:</b><br><span style="color:#00ffcc;">🟢 Pronto para Arquivos</span></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown('<div class="metric-box"><b>Formatos Aceitos:</b><br>Imagens/Prints, PDF, Excel, TXT</div>', unsafe_allow_html=True)
with col_m3:
    st.markdown('<div class="metric-box"><b>Foco Regulatório:</b><br>Padrões RINA / ANAC</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Organização da Tela (Esquerda: Entrada de Dados | Direita: Resultado)
col_esquerda, col_direita = st.columns([1, 1.3])

with col_esquerda:
    st.markdown("### 📥 Passo 1: Enviar Documentos ou Imagens")
    
    # Campo de Upload Centralizado com Nome Claro
    arquivo_upload = st.file_uploader(
        "Clique aqui para subir o seu arquivo (Aceita Print de Tela, Fotos JPG/PNG, Manuais em PDF ou Planilhas Excel):", 
        type=["pdf", "xlsx", "xls", "png", "jpg", "jpeg", "txt"]
    )
    
    st.markdown("---")
    st.markdown("### ✍️ Passo 2: Informações Adicionais (Opcional)")
    # Caixa de texto explicada
    texto_auditoria = st.text_area(
        "Se quiser, digite ou cole observações manuais complementares aqui:",
        height=120,
        placeholder="Ex: Cruzar dados do print acima com a última ordem de serviço..."
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # BOTÃO CENTRAL DE COMANDO - Totalmente identificado e funcional
    botao_analisar = st.button("🚀 CLIQUE AQUI PARA INICIAR A AUDITORIA DA IA")

with col_direita:
    st.markdown("### 📋 Resultado: Parecer Técnico da Auditoria")
    
    if botao_analisar:
        conteudo_texto = ""
        conteudo_imagem = None
        
        with st.spinner("🧠 Processando os arquivos e gerando o relatório normativo..."):
            try:
                # Processamento inteligente dependendo do formato que você subiu
                if arquivo_upload is not None:
                    nome_arquivo = arquivo_upload.name.lower()
                    
                    # Se for Print ou Foto (PNG, JPG)
                    if nome_arquivo.endswith(('.png', '.jpg', '.jpeg')):
                        conteudo_imagem = Image.open(arquivo_upload)
                        st.info(f"📸 Imagem/Print identificado com sucesso: {arquivo_upload.name}")
                    
                    # Se for arquivo PDF
                    elif nome_arquivo.endswith('.pdf'):
                        leitor_pdf = PyPDF2.PdfReader(io.BytesIO(arquivo_upload.read()))
                        texto_extraido = ""
                        for pagina in leitor_pdf.pages:
                            texto_extraido += pagina.extract_text() or ""
                        conteudo_texto = f"[Conteúdo extraído do PDF {arquivo_upload.name}]:\n{texto_extraido}"
                        st.info(f"📄 Documento PDF lido com sucesso: {arquivo_upload.name}")
                    
                    # Se for Planilha do Excel
                    elif nome_arquivo.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(arquivo_upload)
                        planilha_texto = df.to_string()
                        conteudo_texto = f"[Dados estruturados da Planilha Excel {arquivo_upload.name}]:\n{planilha_texto}"
                        st.info(f"📊 Dados da Planilha Excel consolidados: {arquivo_upload.name}")
                        
                    # Se for texto puro
                    elif nome_arquivo.endswith('.txt'):
                        conteudo_texto = arquivo_upload.read().decode("utf-8")
                
                # Junta o texto digitado se houver
                if texto_auditoria:
                    conteudo_texto += f"\n\n[Observações Complementares do Auditor]: {texto_auditoria}"
                
                # Instrução de engenharia de prompt para a IA agir como auditor aeronáutico sênior
                prompt_profissional = """
                Você é um Auditor de Aeronavegabilidade Sênior especialista em manutenção aeronáutica e normas (RINA e ANAC).
                Analise detalhadamente as informações enviadas (seja o texto extraído de documentos/planilhas ou o conteúdo visual de um print de tela).
                
                Gere um parecer técnico rigoroso estruturado estritamente nos seguintes tópicos:
                1. 📝 RESUMO TÉCNICO DA NÃO-CONFORMIDADE / SITUAÇÃO DETECTADA
                2. ⚠️ RISCOS E IMPACTOS DIRETOS NA AERONAVEGABILIDADE DA AERONAVE
                3. 🔧 RECOMENDAÇÃO DE PLANO DE AÇÃO CORRETIVA (Baseado nas melhores práticas regulatórias)
                
                Mantenha um tom técnico, formal e preciso de aviação.
                """
                
                # Executa a chamada correta para o Gemini 2.5 Flash
                if conteudo_imagem:
                    resposta = model.generate_content([prompt_profissional, conteudo_imagem])
                elif conteudo_texto.strip():
                    resposta = model.generate_content(f"{prompt_profissional}\n\nDados para análise:\n{conteudo_texto}")
                else:
                    st.warning("⚠️ Nenum dado foi detectado. Por favor, faça o upload de um arquivo ou escreva algo na caixa de texto antes de clicar em analisar.")
                    resposta = None
                
                if resposta:
                    st.success("✅ Análise Finalizada com Sucesso!")
                    st.markdown(resposta.text)
                    
            except Exception as e:
                st.error(f"❌ Ocorreu um erro ao processar este tipo de arquivo: {e}")
    else:
        st.info("💡 Pronto para análise. Insira seus documentos, prints ou relatórios no painel esquerdo e clique no botão azul para receber o parecer da IA.")
