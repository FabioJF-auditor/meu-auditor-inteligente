import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import google.generativeai as genai
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Auditor Inteligente ACCD/ACC/ACCI", page_icon="✈️", layout="wide")

# 2. CONEXÃO COM O MOTOR GEMINI (A chave fica oculta nos Secrets do Streamlit Cloud)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass  # Evita que o app quebre localmente antes de colocar a chave na nuvem

# 3. BANCO DE DADOS EM MEMÓRIA (Controle de Acesso)
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "fabio.ferreira@rina.org": "administrador"  # Seu e-mail Master de aprovação
    }

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

# --- TELA DE AUTENTICAÇÃO ---
if st.session_state.usuario_logado is None:
    st.title("🔐 Controle de Acesso - Auditoria de Aeronavegabilidade")
    st.subheader("Identificação Obrigatória")
    st.markdown("Este aplicativo é de uso restrito e monitorado para o ecossistema Petrobras/RINA.")
    
    email_input = st.text_input("Insira seu e-mail institucional:").strip().lower()
    
    if st.button("Solicitar Acesso / Entrar"):
        if not (email_input.endswith("@petrobras.com.br") or email_input.endswith("@rina.org") or email_input.endswith(".prestserv@petrobras.com.br")):
            st.error("❌ Acesso negado. Domínio de e-mail não autorizado.")
        else:
            if email_input not in st.session_state.usuarios_db:
                st.session_state.usuarios_db[email_input] = "pendente"
                st.warning("⚠️ Seu primeiro acesso foi registrado! Aguarde a liberação manual do Supervisor Fabio Ferreira.")
            elif st.session_state.usuarios_db[email_input] == "pendente":
                st.warning("⏳ Seu e-mail está na fila de espera. Aguarde a autorização do administrador.")
            elif st.session_state.usuarios_db[email_input] in ["aprovado", "administrador"]:
                st.session_state.usuario_logado = email_input
                st.success("🔓 Acesso liberado!")
                st.rerun()
    st.stop()

# --- PAINEL ADMINISTRATIVO DO FABIO ---
if st.session_state.usuario_logado == "fabio.ferreira@rina.org":
    st.header("🛠️ Painel de Controle do Fabio")
    pendentes = [email for email, status in st.session_state.usuarios_db.items() if status == "pendente"]
    if len(pendentes) > 0:
        st.write("### Solicitações de Primeiro Acesso:")
        for email_pendente in pendentes:
            col_mail, col_btn = st.columns([3, 1])
            with col_mail: st.text(f"📥 {email_pendente}")
            with col_btn:
                if st.button("Aprovar Acesso", key=email_pendente):
                    st.session_state.usuarios_db[email_pendente] = "aprovado"
                    st.success(f"Acesso liberado!")
                    st.rerun()
    else:
        st.info("Não há novas solicitações de acesso pendentes no momento.")
    st.write("---")

# ==========================================
# 🚀 CONTEÚDO PRINCIPAL DO SISTEMA
# ==========================================
st.title("🛩️ Sistema Inteligente de Auditoria Documental")
st.subheader(f"Auditor Responsável: {st.session_state.usuario_logado}")

# Seleção do Tipo de Auditoria
tipo_auditoria = st.selectbox(
    "Selecione o procedimento de auditoria a ser executado:",
    ["ACCD (Auditoria de Conformidade Contratual Documental)", "ACC (Auditoria de Conformidade Contratual - Física/Documental)", "ACCI (Auditoria de Conformidade Contratual Inicial)"]
)

st.markdown(f"### Módulo de Análise: {tipo_auditoria}")
st.write("Faça o upload dos documentos recebidos da operadora (PDF) para que o motor do Gemini preencha o checklist automaticamente.")

arquivo_pdf = st.file_uploader("Arraste o arquivo PDF aqui:", type=["pdf"])

if arquivo_pdf is not None:
    st.info("⚙️ O Gemini está realizando a varredura e leitura profunda dos documentos. Aguarde...")
    
    # 1. Extração preliminar de texto do PDF para suporte
    reader = PdfReader(arquivo_pdf)
    texto_extraido = "".join([page.extract_text() + "\n" for page in reader.pages])
    
    # Tenta capturar a matrícula da aeronave no texto
    busca_matricula = re.search(r"PR-[A-Z]{3}", texto_extraido)
    matricula_aeronave = busca_matricula.group(0) if busca_matricula else "PR-XXX"
    
    # 2. CHAMADA DA API DO GEMINI COM O PROMPT TÉCNICO REGULAMENTAR
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt_engenharia = f"""
        Você é um Auditor Especialista em Aeronavegabilidade Aeronáutica trabalhando em conjunto com a Petrobras e RINA.
        Sua tarefa é analisar o texto extraído de um documento de auditoria para a modalidade {tipo_auditoria}.
        Avalie estritamente a conformidade documental com base nos seguintes critérios regulamentares:
        - Registro de Liberação de Aeronavegabilidade / APRS assinado por pessoal devidamente designado (RBAC 135.429 / RBAC 145.161).
        - Rastreabilidade de componentes trocados classe I e II com formulários válidos (FAA Form 8130-3 ou EASA Form 1).
        - Verificação de Diretrizes de Aeronavegabilidade (DA/AD) e validade de documentos obrigatórios como Seguro RETA (validade e 5 adendos), Certificado de Aeronavegabilidade (CA) e CVA.
        - Para análises de painel e dashboard, verifique se há panes repetitivas (ATA) no período de 60 dias ou quebra no prazo de 30 dias para abertura de cards de paradas programadas.

        Analise o texto abaixo e preencha os itens do checklist. 
        Retorne SUA RESPOSTA ESTRITAMENTE em formato JSON estruturado igual ao exemplo abaixo, não use markdown ou blocos de código na resposta, apenas o JSON puro:
        {{
            "seguro_reta": {{"status": "CF ou NC", "justificativa": "Sua explicação técnica aqui"}},
            "aprs_assinaturas": {{"status": "CF ou NC", "justificativa": "Sua explicação técnica aqui"}},
            "rastreabilidade_pecas": {{"status": "CF ou NC", "justificativa": "Sua explicação técnica aqui"}},
            "prazos_paradas": {{"status": "CF ou NC", "justificativa": "Sua explicação técnica aqui"}},
            "gatilhos_vermelhos": 0,
            "gatilhos_amarelos": 0
        }}

        Texto extraído para análise:
        {texto_extraido[:8000]}
        """
        
        response = model.generate_content(prompt_engenharia)
        resultado_json = json.loads(response.text.strip())
        
        # --- EXIBIÇÃO DOS RESULTADOS DO CHECKLIST AUTOMATIZADO ---
        st.success(f"✅ Checklist Processado pelo Gemini para a aeronave {matricula_aeronave}!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Status do Checklist Documental")
            
            def exibir_item_checklist(titulo, dados_item):
                if dados_item["status"] == "CF":
                    st.success(f"🟢 **{titulo}: CONFORME (CF)**\n\n{dados_item['justificativa']}")
                else:
                    st.error(f"🔴 **{titulo}: NÃO CONFORME (NC) / IMPEDITIVO**\n\n{dados_item['justificativa']}")
            
            exibir_item_checklist("Verificação de Seguro RETA e Validades", resultado_json["seguro_reta"])
            exibir_item_checklist("Liberações Técnicas e Assinaturas (APRS/RII)", resultado_json["aprs_assinaturas"])
            exibir_item_checklist("Rastreabilidade de Componentes (Form 1)", resultado_json["rastreabilidade_pecas"])
            exibir_item_checklist("Previsibilidade de Paradas e Prazos", resultado_json["prazos_paradas"])

        with col2:
            st.subheader("📊 Indicadores de Severidade Gerados")
            st.caption("Gráfico gerado dinamicamente pelas não-conformidades apontadas pela IA:")
            
            categorias = ["Críticos (Vermelho)", "Alertas (Amarelo)"]
            valores = [resultado_json["gatilhos_vermelhos"], resultado_json["gatilhos_amarelos"]]
            
            fig = go.Figure(data=[go.Bar(x=categorias, y=valores, marker_color=['#EF553B', '#FF9900'], text=valores, textposition='auto')])
            fig.update_layout(template="plotly_white", height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Aviso Pedagógico:** Use este preenchimento automatizado para revisar suas próprias marcações de auditoria e calibrar sua assertividade técnica!")
            
    except Exception as e:
        st.error(f"❌ Erro ao processar análise com o Gemini. Verifique se a sua chave de API está configurada corretamente nos Secrets. Detalhes: {e}")