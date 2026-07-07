import streamlit as st
import google.generativeai as genai
import os

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
    .stButton>button { width: 100%; background-color: #0066cc; color: white; font-weight: bold; border-radius: 5px; }
    .stButton>button:hover { background-color: #0052a3; }
    .metric-box { padding: 15px; background-color: #1f293d; border-radius: 8px; border-left: 5px solid #0066cc; }
    </style>
""", unsafe_allow_html=True)

# 2. Conexão Segura com o Novo Motor Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    # Atualizado para o motor de última geração
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.error("⚠️ Erro de Configuração: Chave GEMINI_API_KEY não encontrada no servidor Render.")
    st.stop()

# 3. Cabeçalho Principal
st.title("✈️ RINA - Sistema de Auditoria de Aeronavegabilidade")
st.subheader("Assistente de Inteligência Artificial para Análise de Conformidade")
st.markdown("---")

# 4. Painel de Indicadores de Produção (Métricas)
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.markdown('<div class="metric-box"><b>Status do Sistema:</b><br><span style="color:#00ffcc;">🟢 Pronto para Análise</span></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown('<div class="metric-box"><b>Motor de IA:</b><br>Gemini 2.5 Flash Ativo</div>', unsafe_allow_html=True)
with col_m3:
    st.markdown('<div class="metric-box"><b>Foco Regulatório:</b><br>Padrões RINA / ANAC</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Divisão da Tela em Duas Colunas (Entrada vs. Saída)
col_esquerda, col_direita = st.columns([1, 1.5])

with col_esquerda:
    st.markdown("### 🛠️ Painel de Controle e Dados")
    
    # Campo para texto manual ou ordens de serviço
    texto_auditoria = st.text_area(
        "Cole aqui o texto do relatório, não-conformidade ou dados da aeronave:",
        height=250,
        placeholder="Ex: Durante a inspeção no prefixo PT-XXX, constatou-se que a diretriz de aeronavegabilidade..."
    )
    
    # Upload de arquivos (caso queira expandir depois)
    arquivo_upload = st.file_uploader("Opcional: Anexar documento da auditoria (.txt)", type=["txt"])
    
    # Botão de Comando Centralizado
    botao_analisar = st.button("🚀 INICIAR AUDITORIA INTELIGENTE")

with col_direita:
    st.markdown("### 📋 Relatório de Análise Técnica")
    
    if botao_analisar:
        # Se houver arquivo, lê o conteúdo dele
        conteudo_para_analisar = ""
        if arquivo_upload is not None:
            conteudo_para_analisar = arquivo_upload.read().decode("utf-8")
        elif texto_auditoria:
            conteudo_para_analisar = texto_auditoria
            
        if conteudo_para_analisar:
            with st.spinner("🧠 Analisando dados e cruzando regulamentações..."):
                try:
                    # Engenharia de Prompt profissional focada em auditoria aeronáutica
                    prompt_profissional = f"""
                    Você é um Auditor de Aeronavegabilidade Sênior especialista em normas aeronáuticas. 
                    Analise o seguinte relato técnico com base nos critérios de segurança, conformidade e engenharia de manutenção.
                    Forneça um relatório estruturado em:
                    1. Resumo Técnico do Caso
                    2. Possíveis Impactos na Aeronavegabilidade
                    3. Sugestão de Ações Corretivas / Próximos Passos
                    
                    Dados para análise:
                    {conteudo_para_analisar}
                    """
                    
                    resposta = model.generate_content(prompt_profissional)
                    st.success("✅ Análise Concluída com Sucesso!")
                    st.markdown(resposta.text)
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar análise da IA: {e}")
        else:
            st.warning("⚠️ Por favor, insira algum texto ou anexe um arquivo antes de iniciar.")
    else:
        st.info("💡 Aguardando comandos. Insira os dados no painel da esquerda e clique em iniciar para gerar o parecer técnico.")
