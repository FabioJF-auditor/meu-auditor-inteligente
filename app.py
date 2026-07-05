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

# Inicializa o banco de conhecimento na memória do navegador se não existir
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

# Criação das Abas Dinâmicas do App
aba_auditoria, aba_conhecimento, aba_admin = st.tabs(["📊 Executar Auditoria", "📚 Enriquecer Base de IA", "🛠️ Painel Admin"])

# ==========================================
# ABA 2: ENRIQUECER BASE DE CONHECIMENTO (RAG MOCK)
# ==========================================
with aba_conhecimento:
    st.header("📝 Atualizar Normativas e Regras do App")
    st.write("Cole aqui textos de novos manuais, portarias da ANAC, checklists da RINA ou regras contratuais da Petrobras para treinar a IA em tempo real.")
    novo_conhecimento = st.text_area("Regras e Documentações de Suporte:", value=st.session_state.banco_conhecimento, height=200)
    if st.button("💾 Salvar e Atualizar Cérebro da IA"):
        st.session_state.banco_conhecimento = novo_conhecimento
        st.success("✅ Base de conhecimento atualizada! O Gemini aplicará estas regras na próxima análise.")

# ==========================================
# ABA 3: PAINEL ADMINISTRATIVO
# ==========================================
with aba_admin:
    if st.session_state.usuario_logado == "fabio.ferreira@rina.org":
        st.header("⚙️ Gerenciamento de Usuários")
        pendentes = [email for email, status in st.session_state.usuarios_db.items() if status == "pendente"]
        if pendentes:
            for email_pendente in pendentes:
                col_m, col_b = st.columns([3, 1])
                with col_m: st.text(email_pendente)
                with col_b:
                    if st.button("Liberar Acesso", key=email_pendente):
                        st.session_state.usuarios_db[email_pendente] = "aprovado"
                        st.rerun()
        else:
            st.info("Nenhuma solicitação pendente.")
    else:
        st.error("Acesso restrito ao Administrador.")

# ==========================================
# ABA 1: EXECUÇÃO DA AUDITORIA MULTIMODAL
# ==========================================
with aba_auditoria:
    col_dados_1, col_dados_2, col_dados_3 = st.columns(3)
    with col_dados_1:
        prefixo = st.text_input("Prefixo da Aeronave (Ex: PR-XPT):", value="PR-").strip().upper()
    with col_dados_2:
        modelo_aeronave = st.text_input("Modelo da Aeronave (Ex: AW139, H175):").strip().upper()
    with col_dados_3:
        tipo_auditoria = st.selectbox("Escopo da Inspeção:", ["ACCD (Documental)", "ACC (Física/Documental)", "ACCI (Inicial)", "Análise de Dashboard / Indicadores"])

    st.write("---")
    st.subheader("📥 Carregamento de Evidências Documentais")
    st.caption("Suporta: PDFs de auditoria, Prints/Fotos de Diários de Bordo (PNG/JPG) e Planilhas de Controle (Excel).")
    
    arquivo_carregado = st.file_uploader("Arraste ou selecione o arquivo/imagem:", type=["pdf", "png", "jpg", "jpeg", "xlsx"])

    if arquivo_carregado is not None:
        st.info("⚡ Analisando evidências com o motor Gemini Pro...")
        
        # Variáveis de envio para a API
        conteudo_para_gemini = []
        texto_suporte = ""
        nome_arquivo = arquivo_carregado.name.lower()

        # TRATAMENTO DE ACORDO COM O TIPO DE ARQUIVO
        if nome_arquivo.endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(arquivo_carregado)
            conteudo_para_gemini.append(image)
            st.image(image, caption="Imagem carregada para análise visual/OCR", width=400)
        elif nome_arquivo.endswith('.pdf'):
            reader = PdfReader(arquivo_carregado)
            texto_suporte = "".join([page.extract_text() + "\n" for page in reader.pages])
        elif nome_arquivo.endswith('.xlsx'):
            df_excel = pd.read_excel(arquivo_carregado)
            texto_suporte = f"Dados extraídos da planilha Excel:\n{df_excel.to_string()}"
            st.dataframe(df_excel.head(5))

        # PROMPT DE ENGENHARIA DE CONTEXTO REFORÇADO
        prompt_final = f"""
        Você é um Auditor Especialista Língua Portuguesa Aeronáutica trabalhando para a Petrobras e RINA.
        Execute a análise para a aeronave Prefixo: {prefixo} | Modelo: {modelo_aeronave} sob o escopo: {tipo_auditoria}.

        Utilize OBRIGATORIAMENTE esta base de conhecimento complementar atualizada pelo supervisor técnico:
        \"\"\"{st.session_state.banco_conhecimento}\"\"\"

        Analise os dados extraídos, tabelas ou imagens fornecidas e preencha o checklist técnico.
        Para cada item, você DEVE extrair as INFORMAÇÕES CRÍTICAS do documento (Validades textuais, Datas de realização do evento, Dados numéricos encontrados).

        Retorne a resposta estritamente em formato JSON bruto, sem blocos markdown. Exemplo estruturado:
        {{
            "seguro_reta": {{"status": "CF", "info_checklist": "Validade encontrada DD/MM/AAAA, contendo 5 adendos", "justificativa": "Texto explicativo"}},
            "aprs_assinaturas": {{"status": "NC", "info_checklist": "Inspeção realizada em DD/MM/AAAA, assinatura ilegível", "justificativa": "Texto explicativo"}},
            "rastreabilidade_pecas": {{"status": "CF", "info_checklist": "Form 1 verificado para componente de série XYZ", "justificativa": "Texto explicativo"}},
            "prazos_paradas": {{"status": "CF", "info_checklist": "Card aberto com 32 dias de antecedência", "justificativa": "Texto explicativo"}},
            "gatilhos_vermelhos": 0,
            "gatilhos_amarelos": 1
        }}

        Dados textuais complementares de suporte:
        {texto_suporte[:8000]}
        """
        conteudo_para_gemini.append(prompt_final)

        try:
            # Modelo multimodal oficial do Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(conteudo_para_gemini)
            
            texto_resposta = response.text.strip()
            if texto_resposta.startswith("```"):
                texto_resposta = re.sub(r"^```[a-zA-Z]*\n", "", texto_resposta)
                texto_resposta = re.sub(r"\n```$", "", texto_resposta)
            
            resultado_json = json.loads(texto_resposta.strip())
            
            st.success(f"✅ Análise concluída com sucesso para a aeronave {prefixo} ({modelo_aeronave})!")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📋 Relatório Dinâmico do Checklist")
                
                def renderizar_bloco(nome_campo, dados):
                    cor = "green" if dados["status"] == "CF" else "red"
                    simbolo = "🟢" if dados["status"] == "CF" else "🔴"
                    with st.expander(f"{simbolo} {nome_campo} - Status: {dados['status']}", expanded=True):
                        st.markdown(f"**ℹ️ Dados extraídos do documento:** *{dados['info_checklist']}*")
                        st.markdown(f"**💬 Parecer Técnico do Auditor IA:** {dados['justificativa']}")
                
                renderizar_bloco("Seguro RETA e Validades de Portaria", resultado_json["seguro_reta"])
                renderizar_bloco("Assinaturas Técnicas / APRS / Designações", resultado_json["aprs_assinaturas"])
                renderizar_bloco("Rastreabilidade de Peças e Componentes (Form 1 / 8130)", resultado_json["rastreabilidade_pecas"])
                renderizar_bloco("Prazos de Paradas e Alertas de Dashboard", resultado_json["prazos_paradas"])

            with c2:
                st.subheader("📊 Métricas de Risco do Escopo")
                cats = ["Críticos (NC)", "Alertas"]
                vls = [int(resultado_json["gatilhos_vermelhos"]), int(resultado_json["gatilhos_amarelos"])]
                fig = go.Figure(data=[go.Bar(x=cats, y=vls, marker_color=['#EF553B', '#FF9900'], text=vls, textposition='auto')])
                fig.update_layout(template="plotly_white", height=300, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as err:
            st.error(f"❌ Falha no processamento. Verifique o formato do arquivo ou sua chave API. Erro: {err}")
