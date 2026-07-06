import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pypdf import PdfReader
import json
import re
from PIL import Image
import io
import time
from google import genai
from google.genai import types

# ==========================================
# 1. IDENTIDADE VISUAL RINA BRASIL (CSS CUSTOM)
# ==========================================
st.set_page_config(
    page_title="RINA & Petrobras - Plataforma de Auditoria Avançada", 
    page_icon="✈️", 
    layout="wide"
)

# Injeção de CSS para customizar as cores institucionais e o ambiente de aviação
st.markdown("""
    <style>
        /* Cores Principais do App */
        :root {
            --primary-color: #002060; /* Azul Escuro RINA */
            --secondary-color: #FFC000; /* Dourado Aeronáutico */
        }
        
        /* Customização de Botões */
        .stButton>button {
            background-color: #002060 !important;
            color: white !important;
            border-radius: 6px !important;
            border: 1px solid #FFC000 !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #FFC000 !important;
            color: #002060 !important;
            box-shadow: 0px 4px 10px rgba(255, 192, 0, 0.4);
        }
        
        /* Customização dos Títulos e Headers */
        h1, h2, h3 {
            color: #002060 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Estilização dos Boxes de Alerta */
        .stAlert {
            border-left: 5px solid #FFC000 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Inicialização segura das variáveis de estado (Memória do App)
if "banco_conhecimento" not in st.session_state:
    st.session_state.banco_conhecimento = "Diretrizes padrão RINA Brasil e Petrobras para auditorias de conformidade de helicópteros offshore (ACCI, ACC, ACCD)."
if "historico_raa" not in st.session_state:
    st.session_state.historico_raa = []
if "historico_rnc" not in st.session_state:
    st.session_state.historico_rnc = []

# ==========================================
# 2. CONTROLE DE ACESSO EXCLUSIVO
# ==========================================
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {"fabio.ferreira@rina.org": "administrador"}
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.title("🔐 RINA Brasil & Petrobras — Portal Aeromédico/Offshore")
    email_input = st.text_input("Insira seu e-mail institucional para acessar a cabine:").strip().lower()
    if st.button("Autenticar e Iniciar Sistemas"):
        if not (email_input.endswith("@petrobras.com.br") or email_input.endswith("@rina.org") or email_input.endswith(".prestserv@petrobras.com.br")):
            st.error("❌ Domínio de e-mail não autorizado para auditoria aeronáutica.")
        else:
            if email_input not in st.session_state.usuarios_db:
                st.session_state.usuarios_db[email_input] = "pendente"
                st.warning("⚠️ Usuário novo registrado. Aguarde a liberação do Supervisor Fabio Ferreira.")
            elif st.session_state.usuarios_db[email_input] in ["aprovado", "administrador"]:
                st.session_state.usuario_logado = email_input
                st.success("🔓 Painel liberado. Tripulação pronta para o voo!")
                st.rerun()
    st.stop()

# ==========================================
# 3. HUB DE LINKS REGULATÓRIOS (BARRA LATERAL)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #002060;'>✈️ Cockpit do Auditor</h2>", unsafe_allow_html=True)
    st.markdown(f"**Operador Logístico Ativo:** \n`{st.session_state.usuario_logado}`")
    st.write("---")
    
    st.subheader("🌐 Links de Pesquisa e Legislação")
    
    with st.expander("🦅 Autoridade Aeronáutica (ANAC)", expanded=True):
        st.link_button("🔎 Consulta RAB (Aeronaves)", "https://sistemas.anac.gov.br/aeronaves/cons_rab.asp", use_container_width=True)
        st.link_button("📚 Coleção de RBAC / RBHA", "https://www.anac.gov.br/assuntos/legislacao/legislacao-1/rbha-e-rbac/rbac", use_container_width=True)
        st.link_button("🔍 Pesquisa de Legislação ANAC", "https://www.anac.gov.br/assuntos/legislacao/busca-legislacao", use_container_width=True)
        st.link_button("📋 Instruções Suplementares (IS)", "https://www.anac.gov.br/assuntos/legislacao/instrucoes-suplementares", use_container_width=True)
        st.link_button("📄 Especificações Operativas (EO)", "https://www.gov.br/anac/pt-br/assuntos/regulados/empresas-aereas/especificacoes-operativas", use_container_width=True)
        st.link_button("🖥️ Portal SIAC", "https://sistemas.anac.gov.br/siac", use_container_width=True)
        st.link_button("🏛️ Gov.br ANAC", "https://www.gov.br/anac", use_container_width=True)

    with st.expander("⛈️ Planejamento de Voo & Clima (DECEA)", expanded=False):
        st.link_button("🗺️ AISWEB (Cartas Aeródromo)", "https://aisweb.decea.mil.br", use_container_width=True)
        st.link_button("📡 REDEMET (METAR/TAF)", "https://redemet.decea.mil.br", use_container_width=True)
        st.link_button("🚀 CENIPA (Investigação e Prevenção)", "https://www.gov.br/cenipa", use_container_width=True)

    with st.expander("⚓ Autoridade Marítima (DPC)", expanded=False):
        st.link_button("🏛️ Diretoria de Portos e Costas", "https://www.marinha.mil.br/dpc", use_container_width=True)
        st.link_button("📜 Normas NORMAM", "https://www.marinha.mil.br/dpc/normas-e-publicacoes", use_container_width=True)

    with st.expander("⛽ Contratos e Suprimentos Petrobras", expanded=False):
        st.link_button("🏢 Portal Petrobras", "https://petrobras.com.br", use_container_width=True)
        st.link_button("🤝 Portal do Fornecedor", "https://fornecedores.petrobras.com.br", use_container_width=True)
        st.link_button("💻 Petronect (Licitações)", "https://www.petronect.com.br", use_container_width=True)

    with st.expander("🌍 Órgãos e Padrões Globais", expanded=False):
        st.link_button("🇺🇳 ICAO", "https://www.icao.int", use_container_width=True)
        st.link_button("🛢️ IOGP", "https://www.iogp.org", use_container_width=True)
        st.link_button("🚁 HeliOffshore", "https://www.helioffshore.org", use_container_width=True)
        st.link_button("🇺🇸 FAA", "https://www.faa.gov", use_container_width=True)
        st.link_button("🇪🇺 EASA", "https://www.easa.europa.eu", use_container_width=True)

    st.write("---")
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.usuario_logado = None
        st.rerun()

# ==========================================
# 4. ENGENHARIA DE SIMULAÇÃO DE VOO (ANIMATION SPINNER)
# ==========================================
def simular_voo_pairado(modelo_aeronave):
    placeholder = st.empty()
    passos = [
        "Pre-flight Check & Inicialização de Sistemas de Bordo...",
        "Acionamento dos Motores e Sistemas Hidráulicos...",
        f"Giro de Rotor Principal — Aeronave {modelo_aeronave} em sustentação...",
        f"Voo Pairado Estabilizado (Hovering Mode). Executando varredura analítica..."
    ]
    for passo in passos:
        placeholder.markdown(f"""
        <div style='background-color: #002060; padding: 20px; border-radius: 8px; border: 2px solid #FFC000; text-align: center;'>
            <p style='color: #FFC000; font-size: 20px; margin: 0; font-weight: bold;'>🚁 [SIMULADOR DE VOO PAIRADO ATIVO - {modelo_aeronave}]</p>
            <p style='color: white; font-size: 16px; margin-top: 10px;'>Status da Telemetria: <b>{passo}</b></p>
            <div style='width: 100%; background-color: #ddd; height: 10px; border-radius: 5px; margin-top: 15px; overflow: hidden;'>
                <div style='width: 75%; background-color: #FFC000; height: 100%; animation: progress 2s ease-in-out infinite;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.8)
    placeholder.empty()

# ==========================================
# 5. PROCESSAMENTO DE ARQUIVOS E CHAMADA DO AGENTE
# ==========================================
def extrair_dados_multiplos_arquivos(arquivos):
    conteudo_partes = []
    texto_acumulado = ""
    for arquivo in arquivos:
        nome = arquivo.name.lower()
        if nome.endswith(('.png', '.jpg', '.jpeg')):
            try:
                img = Image.open(arquivo)
                conteudo_partes.append(img)
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
    return conteudo_partes, texto_acumulado

def executar_chamada_gemini(prompt, imagens):
    """Executa a chamada usando o SDK oficial do Google ativando o Grounding com Google Search"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except:
        return "Erro: Chave secreta GEMINI_API_KEY não configurada nos Secrets do Streamlit."
    
    conteudo_final = []
    conteudo_final.extend(imagens)
    conteudo_final.append(prompt)
    
    try:
        configuracao = types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.1
        )
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=conteudo_final,
            config=configuracao
        )
        return response.text
    except Exception as e:
        return f"Falha na execução do processamento do Agente Híbrido: {e}"

# ==========================================
# 6. ABAS OPERACIONAIS DO APLICATIVO
# ==========================================
tab_auditoria, tab_documentos, tab_dashboard, tab_conhecimento, tab_admin = st.tabs([
    "📋 Executar Checklist Regulatório",
    "📄 Emissão de RAA / RNC",
    "📊 Painel de Performance (60 Dias)",
    "📚 Base de Conhecimento & RAG",
    "🛠️ Gestão de Acessos"
])

# ------------------------------------------
# ABA 1: EXECUÇÃO DO CHECKLIST
# ------------------------------------------
with tab_auditoria:
    st.header("📋 Auditoria Avançada de Aeronavegabilidade")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a: prefixo_maquina = st.text_input("Prefixo:", value="PR-", key="p_aud").strip().upper()
    with col_b: modelo_helicoptero = st.selectbox("Modelo Homologado da Aeronave:", ["AW139 (Leonardo)", "H145 (Airbus)", "S92 (Sikorsky)"])
    with col_c: escopo_inspecao = st.selectbox("Modalidade de Inspeção Contratual:", ["ACCI (Auditoria Inicial)", "ACC (Física e Documental)", "ACCD (Auditoria Documental)"])
    with col_d: escopo_norma = st.selectbox("Normativa Principal de Busca:", ["RBAC 91 / 135 (ANAC)", "PE-3PBR (Petrobras)", "Diretriz RINA Sênior"])
    
    st.write("---")
    arquivos_auditoria = st.file_uploader("Carregue todas as evidências enviadas pela operadora (PDFs, Planilhas de Controle, Cards de Parada, Fotos de Caderneta):", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "xlsx"], key="up_aud")
    
    if arquivos_auditoria:
        if st.button("🔍 Iniciar Auditoria Híbrida Inteligente"):
            
            simular_voo_pairado(modelo_helicoptero)
            imagens, texto_arquivos = extrair_dados_multiplos_arquivos(arquivos_auditoria)
            
            prompt_auditoria = f"""
Você é um Engenheiro de Aeronavegabilidade e Auditor Líder da RINA atuando no contrato Petrobras.
Sua missão é analisar de forma ultra fiel as evidências enviadas e preencher o checklist técnico para a aeronave {prefixo_maquina} ({modelo_helicoptero}) no escopo {escopo_inspecao} sob as diretrizes de busca da {escopo_norma}.

Regras de Negócio e Conhecimento Técnico Interno Fiel:
{st.session_state.banco_conhecimento}

Varra os arquivos anexados buscando as validades literais e dados numéricos coerentes. Se necessário, utilize a ferramenta de pesquisa integrada do Google para validar portarias ou prazos de normas citadas.
Para cada item, determine o Status estritamente como: 'CF' (Conforme) ou 'NC' (Não Conforme). No campo 'info_checklist', coloque de forma exata, literal e resumida as datas de validade, Part Numbers (PN) e Serial Numbers (SN) que encontrar. Não invente nada.

Retorne estritamente um objeto JSON puro, sem formatação markdown ou blocos de código:
{{
    "item_1": {{"item": "Seguro RETA e Validade das Apólices Obrigatórias", "status": "CF", "info_checklist": "Texto literal encontrado", "justificativa": "Parecer técnico"}},
    "item_2": {{"item": "Liberações Técnicas, Ordens de Serviço e Assinaturas de APRS/RII", "status": "CF", "info_checklist": "Texto literal encontrado", "justificativa": "Parecer técnico"}},
    "item_3": {{"item": "Rastreabilidade de Componentes Críticos Classe I e II (Form 1 / FAA 8130-3)", "status": "CF", "info_checklist": "PNs e SNs verificados", "justificativa": "Parecer técnico"}},
    "item_4": {{"item": "Certificado de Verificação de Aeronavegabilidade (CVA) e Validade do CA", "status": "CF", "info_checklist": "Datas de vigência", "justificativa": "Parecer técnico"}},
    "item_5": {{"item": "Controle de Prazos e Alertas da Janela de Panes de 60 Dias", "status": "CF", "info_checklist": "Resultados de recorrência identificados", "justificativa": "Parecer técnico"}},
    "gatilhos_vermelhos": 0,
    "gatilhos_amarelos": 0
}}

Dados textuais extraídos:
{texto_arquivos[:14000]}
"""
            
            resposta_agente = executar_chamada_gemini(prompt_auditoria, imagens)
            
            try:
                res_clean = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", resposta_agente.strip()).strip()
                res_json = json.loads(res_clean)
                st.success("📋 Relatório de Checklist Técnico RINA Consolidado!")
                
                lista_itens = [res_json[f"item_{i}"] for i in range(1, 6)]
                df_excel = pd.DataFrame(lista_itens)
                df_excel.columns = ["Item do Checklist Oficial RINA", "Status Operacional", "Dados e Validades Coletadas (Fiel)", "Justificativa"]
                
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name=f"Checklist {prefixo_maquina}")
                
                st.download_button(
                    label="📥 Baixar Checklist Oficial Respondido em Excel (.xlsx)",
                    data=buffer_excel.getvalue(),
                    file_name=f"Checklist_RINA_Oficial_{prefixo_maquina}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.write("---")
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    for i in range(1, 6):
                        obj = res_json[f"item_{i}"]
                        simb = "🟢" if obj["status"] == "CF" else "🔴"
                        with st.expander(f"{simb} {obj['item']} — [{obj['status']}]", expanded=True):
                            st.markdown(f"**ℹ️ Evidência Documental:** *{obj['info_checklist']}*")
                            st.markdown(f"**💬 Julgamento Técnico:** {obj['justificativa']}")
                with col_res2:
                    fig = go.Figure(data=[go.Bar(x=["Não Conformidades (NC)", "Alertas Técnicos"], y=[int(res_json["gatilhos_vermelhos"]), int(res_json["gatilhos_amarelos"])], marker_color=['#d9534f', '#f0ad4e'])])
                    fig.update_layout(template="plotly_white", height=350)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Erro no processamento estruturado. Veja o retorno bruto:")
                st.code(resposta_agente)

# ------------------------------------------
# ABA 2: EMISSÃO DE DOCUMENTOS OFICIAIS (RAA / RNC)
# ------------------------------------------
with tab_documentos:
    st.header("📄 Módulo de Geração de Documentos Técnicos")
    sub_raa, sub_rnc = st.tabs(["📋 RAA (Relatório de Auditoria)", "⚠️ RNC (Registro de Não Conformidade)"])
    
    with sub_raa:
        st.subheader("Gerar Novo RAA Corporativo")
        c_pref = st.text_input("Prefixo Regulamentar:", value="PR-", key="raa_pref")
        c_op = st.text_input("Operadora de Logística Offshore:", value="Ex: Omni, Líder, CHC")
        c_text = st.text_area("Conclusão Técnica e Parecer Final:")
        
        if st.button("💾 Chancelar e Assinar RAA"):
            novo_raa = {"Aeronave": c_pref, "Operadora": c_op, "Parecer Técnico": c_text, "Auditor Líder": st.session_state.usuario_logado}
            st.session_state.historico_raa.append(novo_raa)
            st.success(f"✅ RAA para a aeronave {c_pref} chancelado e gravado!")
            
        if st.session_state.historico_raa:
            st.write("---")
            st.dataframe(pd.DataFrame(st.session_state.historico_raa))

    with sub_rnc:
        st.subheader("Abertura de Registro de Não Conformidade (RNC)")
        r_pref = st.text_input("Prefixo da Aeronave Bloqueada:", value="PR-", key="rnc_pref")
        r_item = st.selectbox("Item do Desvio Técnico:", ["Seguro RETA Vencido", "Rastreabilidade Incompleta Form 1", "Assinatura APRS Inexistente", "Estouro de Gatilho de Paradas de 60 Dias"])
        r_text = st.text_area("Descrição Detalhada e Evidência Física/Documental:")
        
        if st.button("🚨 Emitir e Protocolar RNC"):
            nova_rnc = {"Aeronave Infratora": r_pref, "Desvio Regulamentar": r_item, "Descrição da Evidência": r_text, "Responsável": st.session_state.usuario_logado}
            st.session_state.historico_rnc.append(nova_rnc)
            st.error(f"🔴 RNC Protocolada! Aeronave {r_pref} sinalizada com restrição.")
            
        if st.session_state.historico_rnc:
            st.write("---")
            st.dataframe(pd.DataFrame(st.session_state.historico_rnc))

# ------------------------------------------
# ABA 3: PAINEL DE PERFORMANCE (JANELA DE 60 DIAS)
# ------------------------------------------
with tab_dashboard:
    st.header("📊 Monitoramento de Confiabilidade e Janela de 60 Dias")
    st.write("Acompanhamento de indisponibilidade de frota, panes repetitivas de sistemas (ATA) e histórico de paradas.")
    
    arquivo_painel = st.file_uploader("Insira a Planilha de Disponibilidade ou Imagem do Painel de Indicadores de 60 dias:", type=["pdf", "xlsx", "png", "jpg"], key="up_dash")
    
    if arquivo_painel:
        if st.button("📊 Análise do Dashboard"):
            simular_voo_pairado("Módulo de Confiabilidade")
            midias, texto_dash = extrair_dados_multiplos_arquivos([arquivo_painel])
            
            prompt_dash = f"""
            Analise a evidência técnica buscando desvios críticos operacionais em 60 dias. 
            Busque picos de indisponibilidade e recorrência de falhas em sistemas ATA. 
            Retorne obrigatoriamente um JSON puro, sem markdown:
            {{"panes_repetitivas": {{"status": "CF", "dados": "Descrição analítica das panes"}}, "ranking_indisponibilidade": {{"status": "CF", "dados": "Impacto percentual"}}, "critico": 0}}
            Texto extraído: {texto_dash[:8000]}
            """
            
            resposta_dash = executar_chamada_gemini(prompt_dash, midias)
            try:
                clean_dash = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", resposta_dash.strip()).strip()
                json_dash = json.loads(clean_dash)
                st.subheader("🚨 Diagnóstico de Alertas Operacionais")
                if json_dash["critico"] == 1:
                    st.error("⚠️ ALERTA CRÍTICO: Esta aeronave ultrapassou os limites contratuais na janela de 60 dias!")
                else:
                    st.success("🟢 Indicadores de performance operacional em conformidade.")
                st.write(f"**🔧 Análise de Sistemas ATA (Falhas):** {json_dash['panes_repetitivas']['dados']}")
                st.write(f"**📈 Posição em Rankings de Indisponibilidade:** {json_dash['ranking_indisponibilidade']['dados']}")
            except Exception as e:
                st.error("Falha ao estruturar os dados analíticos do painel.")
                st.code(resposta_dash)

# ------------------------------------------
# ABA 4: BASE DE CONHECIMENTO E ARQUIVOS (SISTEMA RAG)
# ------------------------------------------
with tab_conhecimento:
    st.header("📚 Treinamento Base do Sistema de Auditoria (Motor RAG)")
    st.write("Alimente a memória local carregando manuais, portarias, PE da Petrobras ou regulamentos RINA.")
    
    arquivos_manuais = st.file_uploader("Selecione os Manuais Técnicos Oficiais (PDF, TXT ou XLSX):", accept_multiple_files=True, type=["pdf", "txt", "xlsx"], key="up_banco")
    if arquivos_manuais:
        if st.button("🔄 Indexar Documentos na Memória Ativa"):
            _, novos_textos = extrair_dados_multiplos_arquivos(arquivos_manuais)
            st.session_state.banco_conhecimento += f"\n\n[MANUAIS TÉCNICOS COMPLEMENTARES INDEXADOS]:\n{novos_textos}"
            st.success(f"✅ {len(arquivos_manuais)} documento(s) técnico(s) acoplado(s) com sucesso!")
            
    st.write("---")
    regras_texto = st.text_area("Regras e Diretrizes Ativas no Cérebro do Aplicativo:", value=st.session_state.banco_conhecimento, height=200)
    if st.button("Salvar Modificações de Diretrizes"):
        st.session_state.banco_conhecimento = regras_texto
        st.success("🧠 Diretrizes operacionais atualizadas!")

# ------------------------------------------
# ABA 5: GESTÃO DE ACESSOS (PAINEL DO SUPERVISOR)
# ------------------------------------------
with tab_admin:
    if st.session_state.usuario_logado == "fabio.ferreira@rina.org":
        st.header("🛠️ Painel de Comando do Supervisor Fabio Ferreira")
        usuarios_pendentes = [email for email, status in st.session_state.usuarios_db.items() if status == "pendente"]
        if usuarios_pendentes:
            for email_p in usuarios_pendentes:
                col_m, col_b = st.columns([3, 1])
                with col_m: st.text(email_p)
                with col_b:
                    if st.button("Aprovar Inspetor / Aluno", key=email_p):
                        st.session_state.usuarios_db[email_p] = "aprovado"
                        st.rerun()
        else:
            st.info("Nenhuma solicitação de acesso pendente na torre de controle.")
    else:
        st.warning("🔒 Acesso restrito. Uso exclusivo do Supervisor Fabio Ferreira.")
