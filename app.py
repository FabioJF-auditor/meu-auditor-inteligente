import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import google.generativeai as genai
from openai import OpenAI
import json
import re
from PIL import Image
import io

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Plataforma de Auditoria Avançada RINA", page_icon="✈️", layout="wide")

# 2. CONFIGURAÇÃO DOS MOTORES DE IA (Puxando dos Secrets)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    client_openai = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
except:
    pass

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
st.title("🚀 Hub de Inteligência Artificial Multimotor em Auditoria")
st.write(f"**Auditor Responsável:** {st.session_state.usuario_logado}")

aba_auditoria, aba_dashboard, aba_conhecimento, aba_admin = st.tabs([
    "📋 Executar Checklist (ACC/ACCD/ACCI)", 
    "📊 Analisar Apenas Dashboard (60 Dias)", 
    "📚 Enriquecer Base de IA", 
    "🛠️ Painel Admin"
])

def extrair_dados_multiplos_arquivos(arquivos):
    conteudo_gemini = []
    texto_acumulado = ""
    for i, arquivo in enumerate(arquivos):
        nome = arquivo.name.lower()
        if nome.endswith(('.png', '.jpg', '.jpeg')) and i < 10:
            conteudo_gemini.append(Image.open(arquivo))
        elif nome.endswith('.pdf'):
            reader = PdfReader(arquivo)
            for page in reader.pages: texto_acumulado += page.extract_text() + "\n"
        elif nome.endswith('.xlsx'):
            df = pd.read_excel(arquivo).dropna(how='all')
            texto_acumulado += f"\n[Planilha {arquivo.name}]:\n{df.to_string()}\n"
    return conteudo_gemini, texto_acumulado

def chamar_ia_selecionada(motor, prompt, lista_midia):
    if motor == "Gemini 2.5 Flash":
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(lista_midia)
        return response.text
    elif motor == "GPT-4o (OpenAI)":
        response = client_openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    return ""

# ==========================================
# ABA: EXECUÇÃO DO CHECKLIST COM MOTOR SELECIONÁVEL
# ==========================================
with aba_auditoria:
    c1, c2, c3, c4 = st.columns(4)
    with c1: prefixo = st.text_input("Prefixo:", value="PR-").strip().upper()
    with c2: modelo = st.text_input("Modelo da Aeronave:").strip().upper()
    with c3: escopo = st.selectbox("Escopo:", ["ACCD (Documental)", "ACC (Física/Documental)", "ACCI (Inicial)"])
    with c4: motor_ia = st.selectbox("🧠 Escolha o Motor de Inteligência Artificial:", ["Gemini 2.5 Flash", "GPT-4o (OpenAI)"])

    st.write("---")
    arquivos_auditoria = st.file_uploader("Selecione um ou mais arquivos simultaneamente:", type=["pdf", "png", "jpg", "jpeg", "xlsx"], accept_multiple_files=True, key="aud_up")

    if arquivos_auditoria:
        if st.button(f"🔍 Executar Checklist de Auditoria Avançado ({len(arquivos_auditoria)} arquivos)"):
            st.info(f"⚙️ Processando análise através do motor {motor_ia}...")
            
            lista_midia, texto_total = extrair_dados_multiplos_arquivos(arquivos_auditoria)
            
            prompt_auditoria = f"""
            Você é um Engenheiro de Aeronavegabilidade e Auditor Sênior especialista Petrobras/RINA.
            Analise rigorosamente os dados da aeronave {prefixo} ({modelo}) no escopo {escopo}.
            Base normativa de suporte: \"\"\"{st.session_state.banco_conhecimento}\"\"\"

            Varra os documentos fornecidos buscando preencher com precisão milimétrica o checklist.
            Para cada item, determine o status (CF para Conforme, NC para Não Conforme) e extraia dados textuais exatos do arquivo no campo 'info_checklist' (Validades exatas encontradas, datas de realização e dados numéricos coerentes).

            Retorne um JSON puro, sem formatação markdown:
            {{
                "seguro_reta": {{"status": "CF", "info_checklist": "Texto com validades e adendos encontrados no documento", "justificativa": "Parecer técnico"}},
                "aprs_assinaturas": {{"status": "CF", "info_checklist": "Dados de assinaturas e ordens de serviço identificadas", "justificativa": "Parecer técnico"}},
                "rastreabilidade_pecas": {{"status": "CF", "info_checklist": "Dados do Form 1, part numbers e serial numbers analisados", "justificativa": "Parecer técnico"}},
                "prazos_paradas": {{"status": "CF", "info_checklist": "Datas e contagem de dias identificadas nos cards", "justificativa": "Parecer técnico"}},
                "gatilhos_vermelhos": 0, "gatilhos_amarelos": 0
            }}
            Documentação recebida: {texto_total[:12000]}
            """
            lista_midia.append(prompt_auditoria)
            
            try:
                raw_response = chamar_ia_selecionada(motor_ia, prompt_auditoria, lista_midia)
                res_clean = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", raw_response.strip()).strip()
                res_json = json.loads(res_clean)
                
                st.success("📋 Resultados do Checklist Técnico Coletados!")
                
                # --- MONTAGEM DA TABELA DE DADOS PARA DOWNLOAD ---
                dados_tabela = {
                    "Item do Checklist": ["Seguro RETA e Validades", "Liberações e Assinaturas (APRS)", "Rastreabilidade (Form 1)", "Prazos e Alertas Contratuais"],
                    "Status Analisado": [res_json["seguro_reta"]["status"], res_json["aprs_assinaturas"]["status"], res_json["rastreabilidade_pecas"]["status"], res_json["prazos_paradas"]["status"]],
                    "Informações Coletadas (Validades/Datas)": [res_json["seguro_reta"]["info_checklist"], res_json["aprs_assinaturas"]["info_checklist"], res_json["rastreabilidade_pecas"]["info_checklist"], res_json["prazos_paradas"]["info_checklist"]],
                    "Justificativa Técnica do Auditor IA": [res_json["seguro_reta"]["justificativa"], res_json["aprs_assinaturas"]["justificativa"], res_json["rastreabilidade_pecas"]["justificativa"], res_json["prazos_paradas"]["justificativa"]]
                }
                df_checklist_respondido = pd.DataFrame(dados_tabela)
                
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_checklist_respondido.to_excel(writer, index=False, sheet_name=f"Checklist {prefixo}")
                dados_excel_bytes = output_excel.getvalue()

                st.download_button(
                    label="📥 Baixar Checklist Respondido em Excel (.xlsx)",
                    data=dados_excel_bytes,
                    file_name=f"Checklist_Auditoria_{prefixo}_{escopo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.write("---")
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    def bloco(nome, obj):
                        simb = "🟢" if obj["status"] == "CF" else "🔴"
                        with st.expander(f"{simb} {nome} [{obj['status']}]", expanded=True):
                            st.write(f"**ℹ️ Dados do Documento (Validades/Datas):** *{obj['info_checklist']}*")
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
                st.error(f"Erro no processamento multimotor. Detalhes: {e}")

# ==========================================
# OUTRAS ABAS MANTIDAS
# ==========================================
with aba_dashboard:
    st.header("📊 Análise de Tendências e Janela de 60 Dias")
    arquivo_dash = st.file_uploader("Carregar PDF ou Print do Painel de Indicadores:", type=["pdf", "png", "jpg", "jpeg", "xlsx"], key="dash_up")
    if arquivo_dash:
        if st.button("⚡ Analisar Apenas Gatilhos de Performance"):
            st.info("Buscando picos de indisponibilidade operacional...")
            midias, texto_dash = extrair_dados_multiplos_arquivos([arquivo_dash])
            prompt_dash = f"Analise a evidência buscando eventos críticos operacionais em 60 dias (TOP 10, TOP 3, prazos). Retorne JSON puro:\n{{\"panes_repetitivas\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"ranking_indisponibilidade\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"prazo_abertura\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"critico\": 0}}\nTexto: {texto_dash[:10000]}"
            midias.append(prompt_dash)
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                res_dash = model.generate_content(midias)
                clean_dash = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", res_dash.text.strip()).strip()
                json_dash = json.loads(clean_dash)
                st.subheader("🚨 Diagnóstico de Alertas Operacionais")
                if json_dash["critico"] == 1: st.error("⚠️ ALERTA: Esta aeronave atingiu gatilhos críticos!")
                else: st.success("🟢 Performance operacional em conformidade.")
                st.write(f"**🔧 Panes Repetitivas (ATA):** {json_dash['panes_repetitivas']['dados']}")
                st.write(f"**📈 Posição em Rankings:** {json_dash['ranking_indisponibilidade']['dados']}")
                st.write(f"**📅 Antecedência de Paradas:** {json_dash['prazo_abertura']['dados']}")
            except Exception as e: st.error(f"Erro: {e}")

with aba_conhecimento:
    st.header("📝 Treinar e Alimentar o Cérebro da IA")
    arquivos_banco = st.file_uploader("Carregar manuais para o Banco de Dados:", type=["pdf", "txt", "xlsx"], accept_multiple_files=True, key="banco_up")
    if arquivos_banco:
        if st.button("🔄 Incorporar Arquivos ao Banco de Conhecimento"):
            _, texto_novos_manuais = extrair_dados_multiplos_arquivos(arquivos_banco)
            st.session_state.banco_conhecimento += f"\n\n[MANUAIS COMPLEMENTARES]:\n{texto_novos_manuais}"
            st.success(f"✅ {len(arquivos_banco)} documento(s) indexado(s)!")
    st.write("---")
    texto_manual = st.text_area("Instruções em Texto:", value=st.session_state.banco_conhecimento, height=150)
    if st.button("Salvar Regras"):
        st.session_state.banco_conhecimento = texto_manual
        st.success("Salvo.")

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
        else: st.info("Nenhuma solicitação pendente.")
