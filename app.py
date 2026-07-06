import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import json
import re
from PIL import Image
import io
import requests
import base64

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Plataforma de Auditoria Avançada RINA", page_icon="✈️", layout="wide")

# 2. CONFIGURAÇÃO DA BASE DE CONHECIMENTO INICIAL
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
st.title("🚀 Hub de Inteligência Artificial RINA — Auditoria Automatizada")
st.write(f"**Auditor Responsável:** {st.session_state.usuario_logado}")

aba_auditoria, aba_dashboard, aba_conhecimento, aba_admin = st.tabs([
    "📋 Executar Checklist Padrão RINA", 
    "📊 Analisar Apenas Dashboard (60 Dias)", 
    "📚 Enriquecer Base de IA", 
    "🛠️ Painel Admin"
])

# Função para extrair textos e preparar imagens para envio via API nativa
def extrair_dados_multiplos_arquivos(arquivos):
    conteudo_imagens_api = []
    texto_acumulado = ""
    for arquivo in arquivos:
        nome = arquivo.name.lower()
        if nome.endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = Image.open(arquivo)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                conteudo_imagens_api.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_str
                    }
                })
            except:
                pass
        elif nome.endswith('.pdf'):
            try:
                reader = PdfReader(arquivo)
                for page in reader.pages: 
                    texto_acumulado += page.extract_text() + "\n"
            except:
                pass
        elif nome.endswith('.xlsx'):
            try:
                df = pd.read_excel(arquivo).dropna(how='all')
                texto_acumulado += f"\n[Planilha {arquivo.name}]:\n{df.to_string()}\n"
            except:
                pass
    return conteudo_imagens_api, texto_acumulado

# Função de Conexão Direta HTTP usando a rota v1beta com o nome corrigido do modelo
def chamar_gemini_via_http(prompt, imagens_api):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        return "Erro: Chave secreta GEMINI_API_KEY não encontrada no Streamlit."
        
    # Corrigido para gemini-1.5-flash-latest exigido pela versão v1beta da sua conta
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    parts = []
    for img_part in imagens_api:
        parts.append(img_part)
    parts.append({"text": prompt})
    
    payload = {
        "contents": [{
            "parts": parts
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Erro HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return f"Falha na conexão com o servidor do Google: {e}"

# ==========================================
# ABA: EXECUÇÃO DO CHECKLIST
# ==========================================
with aba_auditoria:
    c1, c2, c3 = st.columns(3)
    with c1: prefixo = st.text_input("Prefixo da Aeronave:", value="PR-").strip().upper()
    with c2: modelo = st.text_input("Modelo da Aeronave:").strip().upper()
    with c3: escopo = st.selectbox("Modalidade de Inspeção:", ["ACCD (Auditoria de Conformidade Contratual Documental)", "ACC (Auditoria de Conformidade Contratual - Física/Documental)", "ACCI (Auditoria de Conformidade Contratual Inicial)"])

    st.write("---")
    arquivos_auditoria = st.file_uploader("Selecione os arquivos enviados pela operadora (PDFs, Fotos, Planilhas):", type=["pdf", "png", "jpg", "jpeg", "xlsx"], accept_multiple_files=True, key="aud_up")

    if arquivos_auditoria:
        if st.button(f"🔍 Rodar Auditoria Otimizada ({len(arquivos_auditoria)} arquivos)"):
            st.info("⚙️ Processando evidências através de conexão direta na nuvem Google... Cruzando dados...")
            
            lista_midia, texto_total = extrair_dados_multiplos_arquivos(arquivos_auditoria)
            
            prompt_auditoria_final = f"""
            Você é um Engenheiro de Aeronavegabilidade e Auditor Sênior da RINA atuando em contrato Petrobras.
            Sua tarefa é analisar as evidências e preencher rigorosamente o padrão de Checklist de Auditoria Documental para a aeronave {prefixo} ({modelo}) no escopo {escopo}.
            Base normativa complementar: \"\"\"{st.session_state.banco_conhecimento}\"\"\"

            Varra minuciosamente as imagens e os textos fornecidos. Identifique as validades e os dados reais.
            Determine o Status de cada item estritamente como: 'CF' (Conforme) ou 'NC' (Não Conforme). 
            No campo 'info_checklist', coloque de forma exata e literal as datas, validades e números de série que encontrar. 
            No campo 'justificativa', apresente o parecer técnico fundamentado com rigor de auditoria.

            Retorne estritamente um objeto JSON puro (sem tags markdown, blocos de código ```json ou caracteres extras):
            {{
                "item_1": {{"item": "Seguro RETA e Validades de Portarias", "status": "CF", "info_checklist": "Validades exatas e número de adendos encontrados", "justificativa": "Análise técnica fundamentada"}},
                "item_2": {{"item": "Liberações Técnicas, Ordens de Serviço e Assinaturas (APRS/RII)", "status": "CF", "info_checklist": "Datas de realização e dados das assinaturas identificadas", "justificativa": "Análise técnica fundamentada"}},
                "item_3": {{"item": "Rastreabilidade de Componentes Classe I e II (Form 1 / FAA 8130-3)", "status": "CF", "info_checklist": "Part Numbers e Serial Numbers verificados nos documentos", "justificativa": "Análise técnica fundamentada"}},
                "item_4": {{"item": "Certificado de Verificação de Aeronavegabilidade (CVA) e Validade do CA", "status": "CF", "info_checklist": "Datas de vigência e conformidade regulamentar", "justificativa": "Análise técnica fundamentada"}},
                "item_5": {{"item": "Análise de Histórico de Panes Repetitivas (ATA) - Janela de 60 Dias", "status": "CF", "info_checklist": "Recorrências encontradas ou declaração de conformidade", "justificativa": "Análise técnica fundamentada"}},
                "gatilhos_vermelhos": 0,
                "gatilhos_amarelos": 0
            }}

            Textos e Planilhas Extraídos:
            {texto_total[:15000]}
            """
            
            resposta_texto = chamar_gemini_via_http(prompt_auditoria_final, lista_midia)
            
            if "Erro" in resposta_texto or "Falha" in resposta_texto:
                st.error(resposta_texto)
            else:
                try:
                    res_clean = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", resposta_texto.strip()).strip()
                    res_json = json.loads(res_clean)
                    
                    st.success("📋 Relatório de Checklist Técnico RINA Concluído!")
                    
                    # --- MONTAGEM DA TABELA FIEL PARA DOWNLOAD ---
                    lista_itens = [res_json[f"item_{i}"] for i in range(1, 6)]
                    df_checklist_respondido = pd.DataFrame(lista_itens)
                    df_checklist_respondido.columns = ["Item de Inspeção", "Status (CF/NC)", "Dados Coletados (Validades/Datas/Séries)", "Parecer Técnico Fundamentado"]
                    
                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        df_checklist_respondido.to_excel(writer, index=False, sheet_name="Checklist RINA")
                    dados_excel_bytes = output_excel.getvalue()

                    st.download_button(
                        label="📥 Baixar Checklist Oficial Respondido em Excel (.xlsx)",
                        data=dados_excel_bytes,
                        file_name=f"Checklist_Oficial_RINA_{prefixo}_{escopo}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.write("---")
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        for i in range(1, 6):
                            obj = res_json[f"item_{i}"]
                            simb = "🟢" if obj["status"] == "CF" else "🔴"
                            with st.expander(f"{simb} {obj['item']} — [{obj['status']}]", expanded=True):
                                st.markdown(f"**ℹ️ Dados do Checklist:** *{obj['info_checklist']}*")
                                st.markdown(f"**💬 Parecer Técnico IA:** {obj['justificativa']}")
                    with col_res2:
                        fig = go.Figure(data=[go.Bar(x=["Não Conformidades (NC)", "Alertas"], y=[int(res_json["gatilhos_vermelhos"]), int(res_json["gatilhos_amarelos"])], marker_color=['#EF553B', '#FF9900'])])
                        fig.update_layout(template="plotly_white", height=350)
                        st.plotly_chart(fig, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Erro ao processar o formato do relatório. Detalhes: {e}")
                    st.text("Resposta bruta recebida:")
                    st.code(resposta_texto)

# ==========================================
# ABA: DASHBOARD DE PERFORMANCE (60 DIAS)
# ==========================================
with aba_dashboard:
    st.header("📊 Análise de Tendências e Janela de 60 Dias")
    arquivo_dash = st.file_uploader("Carregar PDF ou Print do Painel de Indicadores:", type=["pdf", "png", "jpg", "jpeg", "xlsx"], key="dash_up")
    if arquivo_dash:
        if st.button("⚡ Analisar Apenas Gatilhos de Performance"):
            st.info("Buscando picos de indisponibilidade operacional...")
            midias, texto_dash = extrair_dados_multiplos_arquivos([arquivo_dash])
            prompt_dash = f"Analise a evidência buscando eventos críticos operacionais em 60 dias (TOP 10, TOP 3, prazos). Retorne JSON puro sem formatação markdown:\n{{\"panes_repetitivas\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"ranking_indisponibilidade\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"prazo_abertura\": {{\"status\": \"CF\", \"dados\": \"Texto\"}}, \"critico\": 0}}\nTexto: {texto_dash[:10000]}"
            
            resposta_dash = chamar_gemini_via_http(prompt_dash, midias)
            
            if "Erro" in resposta_dash or "Falha" in resposta_dash:
                st.error(resposta_dash)
            else:
                try:
                    clean_dash = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", resposta_dash.strip()).strip()
                    json_dash = json.loads(clean_dash)
                    st.subheader("🚨 Diagnóstico de Alertas Operacionais")
                    if json_dash["critico"] == 1: st.error("⚠️ ALERTA: Esta aeronave atingiu gatilhos críticos!")
                    else: st.success("🟢 Performance operacional em conformidade.")
                    st.write(f"**🔧 Panes Operativas (ATA):** {json_dash['panes_repetitivas']['dados']}")
                    st.write(f"**📈 Posição em Rankings:** {json_dash['ranking_indisponibilidade']['dados']}")
                    st.write(f"**📅 Antecedência de Paradas:** {json_dash['prazo_abertura']['dados']}")
                except Exception as e: 
                    st.error(f"Erro: {e}")
                    st.code(resposta_dash)

# ==========================================
# ABA: BASE DE CONHECIMENTO
# ==========================================
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
