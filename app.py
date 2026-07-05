import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import google.generativeai as genai
import json
import re
from PIL import Image
import io

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Plataforma de Auditoria Inteligente RINA", page_icon="✈️", layout="wide")

# 2. CONEXÃO COM O MOTOR GEMINI
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass

# Inicializa as variáveis na memória do servidor
if "banco_conhecimento" not in st.session_state:
    st.session_state.banco_conhecimento = "Diretrizes padrão Petrobras/RINA aplicadas para auditorias de aeronavegabilidade."

# 3. CONTROLE DE ACESSO
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {"fabio.ferreira@rina.org": "administrador"}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.title("🔐 Controle de Acesso - Auditoria RINA/Petrobras")
    email_input = st.text_input("Insira seu e-mail institucional:").strip().lower()
    if st.button("Solicitar Acesso / Entrar"):
        if not (email_input.endswith("@petrobras.com.br") or email_input.endswith("@rina.org") or email_input.endswith(".prestserv@petrobras.com.br")):
            st.error("❌ Domínio não autorizado.")
        else:
            if email_input not in st.session_state.usuarios_db:
                st.session_state.usuarios_db[email_input] = "pendente"
                st.warning("⚠️ Aguarde a liberação do Supervisor Fabio Ferreira.")
            elif st.session_state.usuarios_db[email_input] in ["aprovado", "administrador"]:
                st.session_state.usuario_logado = email_input
                st.success("🔓 Acesso liberado!")
                st.rerun()
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.title("🚀 Hub de Auditoria Multimodal Baseado em IA")
st.write(f"**Auditor Responsável:** {st.session_state.usuario_logado}")

aba_auditoria, aba_dashboard, aba_conhecimento, aba_admin = st.tabs([
    "📋 Executar Checklist (ACC/ACCD/ACCI)", 
    "📊 Analisar Apenas Dashboard (60 Dias)", 
    "📚 Enriquecer Base de IA", 
    "🛠️ Painel Admin"
])

# ==========================================
# FUNÇÃO AUXILIAR PARA PROCESSAR ARQUIVOS EM MASSA
# ==========================================
def extrair_dados_multiplos_arquivos(arquivos):
    conteudo_gemini = []
    texto_acumulado = ""
    
    for i, arquivo in enumerate(arquivos):
        nome = arquivo.name.lower()
        if nome.endswith(('.png', '.jpg', '.jpeg')):
            # Se forem muitas imagens, limitamos o envio das primeiras para não estourar a memória
            if i < 10: 
                img = Image.open(arquivo)
                conteudo_gemini.append(img)
        elif nome.endswith('.pdf'):
            reader = PdfReader(arquivo)
            for page in reader.pages:
                texto_acumulado += page.extract_text() + "\n"
        elif nome.endswith('.xlsx'):
            df = pd.read_excel(arquivo).dropna(how='all')
            texto_acumulado += f"\n[Planilha {arquivo.name}]:\n{df.to_string()}\n"
            
    return conteudo_gemini, texto_acumulado

# ==========================================
# ABA: ENRIQUECER BASE DE CONHECIMENTO
# ==========================================
with aba_conhecimento:
    st.header("📝 Treinar e Alimentar o Cérebro da IA")
    st.write("Forneça manuais, procedimentos atualizados RINA ou novas portarias:")
    
    arquivos_banco = st.file_uploader("Carregar documentos de referência para o Banco de Dados:", type=["pdf", "txt", "xlsx"], accept_multiple_files=True, key="banco_up")
    
    if arquivos_banco:
        if st.button("🔄 Incorporar Arquivos ao Banco de Conhecimento"):
            _, texto_novos_manuais = extrair_dados_multiplos_arquivos(arquivos_banco)
            st.session_state.banco_conhecimento += f"\n\n[MANUAIS COMPLEMENTARES]:\n{texto_novos_manuais}"
            st.success(f"✅ {len(arquivos_banco)} documento(s) indexado(s) na memória!")
            
    st.write("---")
    texto_manual = st.text_area("Instruções e Regras de Negócio em Texto:", value=st.session_state.banco_conhecimento, height=150)
    if st.button("Salvar Regras em Texto"):
        st.session_state.banco_conhecimento = texto_manual
        st.success("Regras salvas com sucesso.")

# ==========================================
# ABA: EXECUÇÃO DO CHECKLIST DOCUMENTAL
# ==========================================
with aba_auditoria:
    c1, c2, c3 = st.columns(3)
    with c1: prefixo = st.text_input("Prefixo (Ex: PR-XYZ):", value="PR-").strip().upper()
    with c2: modelo = st.text_input("Modelo da Aeronave (Ex: AW139):").strip().upper()
    with c3: escopo = st.selectbox("Escopo:", ["ACCD (Documental)", "ACC (Física/Documental)", "ACCI (Inicial)"])

    st.write("---")
    st.subheader("📥 Carregar Evidências para Cruzamento de Dados")
    arquivos_auditoria = st.file_uploader("Selecione um ou mais arquivos simultaneamente:", type=["pdf", "png", "jpg", "jpeg", "xlsx"], accept_multiple_files=True, key="aud_up")

    if arquivos_auditoria:
        if st.button(f"🔍 Executar Checklist Combinado ({len(arquivos_auditoria)} arquivos)"):
            st.info("⚙️ Conectando ao motor de produção Gemini... Cruzando informações...")
            
            lista_midia, texto_total = extrair_dados_multiplos_arquivos(arquivos_auditoria)
            
            prompt = f"""
            Você é um Engenheiro de Aeronavegabilidade e Auditor Sênior para Petrobras/RINA.
            Analise as evidências fornecidas para a aeronave {prefixo} ({modelo}) no escopo {escopo}.
            Use como regra estrita esta base de conhecimentos: \"\"\"{st.session_state.banco_conhecimento}\"\"\"

            Examine as imagens e os textos. Monte o checklist extraindo validades, datas de execução e pareceres técnicos.
            Retorne um JSON estrito, sem tags markdown:
            {{
                "seguro_reta": {{"status": "CF", "info_checklist": "Validade DD/MM/AAAA, 5 adendos", "justificativa": "Texto"}},
                "aprs_assinaturas": {{"status": "CF", "info_checklist": "Data da assinatura e responsável", "justificativa": "Texto"}},
                "rastreabilidade_pecas": {{"status": "CF", "info_checklist": "Dados do Form 1 coletados", "justificativa": "Texto"}},
                "prazos_paradas": {{"status": "CF", "info_checklist": "Prazos contratuais identificados", "justificativa": "Texto"}},
                "gatilhos_vermelhos": 0, "gatilhos_amarelos": 0
            }}
            Textos extraídos: {texto_total[:12000]}
            """
            lista_midia.append(prompt)
            
            try:
                # 🔄 UTILIZANDO O MODELO DE PRODUÇÃO ATUALIZADO
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(lista_midia)
                res_clean = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", response.text.strip()).strip()
                res_json = json.loads(res_clean)
                
                st.success("📋 Resultados do Checklist Técnico Analisados!")
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    def bloco(nome, obj):
                        simb = "🟢" if obj["status"] == "CF" else "🔴"
                        with st.expander(f"{simb} {nome} [{obj['status']}]", expanded=True):
                            st.write(f"**ℹ️ Dados do Documento:** {obj['info_checklist']}")
                            st.write(f"**💬 Parecer da IA:** {obj['justificativa']}")
                    bloco("Seguro RETA e Validades", res_json["seguro_reta"])
                    bloco("Liberações e Assinaturas (APRS/RII)", res_json["aprs_assinaturas"])
                    bloco("Rastreabilidade (Form 1)", res_json["rastreabilidade_pecas"])
                    bloco("Prazos e Alertas Contratuais", res_json["prazos_paradas"])
                with col_res2:
                    fig = go.Figure(data=[go.Bar(x=["Críticos", "Alertas"], y=[int(res_json["gatilhos_vermelhos"]), int(res_json["gatilhos_amarelos"])], marker_color=['#EF553B', '#FF9900'])])
                    fig.update_layout(template="plotly_white", height=300)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro no processamento. Detalhes: {e}")

# ==========================================
# ABA: ANÁLISE ISOLADA DE DASHBOARD
# ==========================================
with aba_dashboard:
    st.header("📊 Análise de Tendências e Janela de 60 Dias")
    arquivo_dash = st.file_uploader("Carregar PDF ou Print do Painel de Indicadores:", type=["pdf", "png", "jpg", "jpeg", "xlsx"], key="dash_up")
    
    if arquivo_dash:
        if st.button("⚡ Analisar Apenas Gatilhos de Performance"):
            st.info("Buscando picos de indisponibilidade no modelo de produção...")
            
            midias, texto_dash = extrair_dados_multiplos_arquivos([arquivo_dash])
            prompt_dash = f"""
            Você é um auditor de performance operacional de helicópteros offshore.
            Analise a evidência enviada buscando eventos críticos nos últimos 60 dias (TOP 10 indisponibilidade, TOP 3 cortes, panes repetitivas ou quebra de prazo de 30 dias).

            Retorne um JSON estruturado sem markdown:
            {{
                "panes_repetitivas": {{"status": "CF", "dados": "Detalhamento encontrado"}},
                "ranking_indisponibilidade": {{"status": "CF", "dados": "Posição encontrada"}},
                "prazo_abertura": {{"status": "CF", "dados": "Janela identificada"}},
                "critico": 0
            }}
            Texto complementar: {texto_dash[:10000]}
            """
            midias.append(prompt_dash)
            
            try:
                # 🔄 UTILIZANDO O MODELO DE PRODUÇÃO ATUALIZADO
                model = genai.GenerativeModel('gemini-2.5-flash')
                res_dash = model.generate_content(midias)
                clean_dash = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", res_dash.text.strip()).strip()
                json_dash = json.loads(clean_dash)
                
                st.subheader("🚨 Diagnóstico de Alertas Operacionais")
                if json_dash["critico"] == 1:
                    st.error("⚠️ ALERTA: Esta aeronave atingiu gatilhos contratuais críticos!")
                else:
                    st.success("🟢 Performance operacional em conformidade.")
                    
                st.write(f"**🔧 Panes Repetitivas (ATA):** {json_dash['panes_repetitivas']['dados']}")
                st.write(f"**📈 Posição em Rankings:** {json_dash['ranking_indisponibilidade']['dados']}")
                st.write(f"**📅 Antecedência de Paradas:** {json_dash['prazo_abertura']['dados']}")
            except Exception as e:
                st.error(f"Erro ao processar o dashboard: {e}")

# ==========================================
# ABA: CONTROLE ADMINISTRATIVO
# ==========================================
with aba_admin:
    if st.session_state.usuario_logado == "fabio.ferreira@rina.org":
        st.header("⚙️ Gerenciamento de Alunos")
        pendentes = [email for email, status in st.session_state.usuarios_db.items() if status == "pendente"]
        if pendentes:
            for email_p in pendentes:
                col_m, col_b = st.columns([3, 1])
                with col_m: st.text(email_p)
                with col_b:
                    if st.button("Aprovar Aluno", key=email_p):
                        st.session_state.usuarios_db[email_p] = "aprovado"
                        st.rerun()
        else:
            st.info("Nenhuma solicitação pendente.")
