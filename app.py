import calendar
from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Configuração da página do aplicativo
st.set_page_config(
    page_title="Calendário Dinâmico de Aulas", layout="centered"
)

# Inicializar os estados da sessão do Streamlit
if "dia_selecionado" not in st.session_state:
    st.session_state.dia_selecionado = None
if "mes_anterior" not in st.session_state:
    st.session_state.mes_anterior = 10  # Outubro
if "ano_anterior" not in st.session_state:
    st.session_state.ano_anterior = 2026

# Configurando o calendário do Python explicitamente para Português do Brasil
try:
    calendar.setlocale(calendar.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        calendar.setlocale(calendar.LC_ALL, 'ptb') # Alternativa para Windows
    except:
        pass

# Dicionário de tradução manual de contingência para os meses
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# -------------------------------------------------------------
# INJEÇÃO DE CSS DE ESTRUTURA GERAL (AMBIENTE ESCURO)
# -------------------------------------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #040805 !important;
    }
    h1, h2, h3, p, span, label {
        color: #f0fdf4 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 10px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
    .caixa-dia-foco {
        background: linear-gradient(90deg, rgba(255, 94, 0, 0.15), rgba(255, 153, 0, 0.05)) !important;
        border: 1px solid #ff5e00 !important;
        padding: 12px 18px !important;
        border-radius: 8px !important;
        color: #ff9900 !important;
        font-weight: bold;
    }
    .card-metrica-topo {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(0, 255, 102, 0.2) !important;
        border-radius: 8px; padding: 14px; text-align: center;
    }
    div.stButton > button {
        background-color: rgba(0, 255, 102, 0.05) !important;
        color: #00ff66 !important;
        border: 1px solid rgba(0, 255, 102, 0.4) !important;
        border-radius: 8px !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background-color: rgba(0, 255, 102, 0.18) !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

excel_file = "Quantidade_de_Aulas_por_Dia_Novas_Disciplinas.xlsx"

# --- GESTÃO DE UPLOAD SEGURO ANTI-ACÚMULO ---
with st.expander("📂 Clique aqui para ADICIONAR novas aulas dadas à tabela existente (Upload Excel)"):
    arquivo_updated = st.file_uploader("Arraste as novas aulas dadas aqui", type=["xlsx"])
    if arquivo_updated is not None:
        try:
            abas_finais = {}
            if os.path.exists(excel_file):
                try:
                    xls_antigo = pd.ExcelFile(excel_file)
                    for nome_aba in xls_antigo.sheet_names:
                        df_carregado = pd.read_excel(excel_file, sheet_name=nome_aba)
                        if not df_carregado.empty:
                            abas_finais[nome_aba] = df_carregado
                except:
                    pass

            xls_novo = pd.ExcelFile(arquivo_updated)
            for nome_aba in xls_novo.sheet_names:
                df_nova_aba = pd.read_excel(arquivo_updated, sheet_name=nome_aba)
                
                if not df_nova_aba.empty and 'Data' in df_nova_aba.columns:
                    df_nova_aba['Data'] = pd.to_datetime(df_nova_aba['Data'], dayfirst=True, errors='coerce')
                    df_nova_aba.dropna(subset=['Data'], inplace=True)
                    
                    if nome_aba in abas_finais:
                        df_antiga_aba = abas_finais[nome_aba]
                        df_antiga_aba['Data'] = pd.to_datetime(df_antiga_aba['Data'], dayfirst=True, errors='coerce')
                        
                        datas_novas = df_nova_aba['Data'].unique()
                        disciplinas_novas = df_nova_aba['Disciplina'].unique() if 'Disciplina' in df_nova_aba.columns else []
                        
                        df_antiga_filtrada = df_antiga_aba[
                            ~(df_antiga_aba['Data'].isin(datas_novas) & df_antiga_aba['Disciplina'].isin(disciplinas_novas))
                        ]
                        
                        df_unificado = pd.concat([df_antiga_filtrada, df_nova_aba], ignore_index=True)
                        abas_finais[nome_aba] = df_unificado
                    else:
                        abas_finais[nome_aba] = df_nova_aba

            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for nome_aba, df_gravar in abas_finais.items():
                    df_gravar['Data'] = pd.to_datetime(df_gravar['Data'], errors='coerce')
                    df_gravar = df_gravar.dropna(subset=['Data'])
                    
                    col_quant = next((c for c in df_gravar.columns if 'quant' in c.lower()), 'Quantidade')
                    if col_quant in df_gravar.columns:
                        df_gravar[col_quant] = pd.to_numeric(df_gravar[col_quant], errors='coerce').fillna(1)
                        df_gravar = df_gravar.groupby(['Data', 'Disciplina'], as_index=False).agg({col_quant: 'sum'})
                    
                    df_gravar['Data'] = df_gravar['Data'].dt.strftime('%Y-%m-%d')
                    df_gravar.to_excel(writer, sheet_name=nome_aba, index=False)
                    
            st.success("✓ Dados consolidados de forma limpa!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar arquivo: {e}")

# --- ANTI-TRAVAMENTO DOS FILTROS ---
if not os.path.exists(excel_file):
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df_inicial = pd.DataFrame([{"Data": "2026-10-19", "Disciplina": "Biologia", "Quantidade": 2}])
            df_inicial.to_excel(writer, sheet_name="103", index=False)
    except:
        pass

try:
    xls = pd.ExcelFile(excel_file)
    turmas_disponiveis = sorted(xls.sheet_names)
except:
    st.warning("Aguardando arquivo de dados padrão ou upload inicial...")
    st.stop()

# --- FILTROS SIDEBAR ---
st.sidebar.header("Filtros")
turma_selecionada = st.sidebar.selectbox("Selecione a Turma", turmas_disponiveis)

df_turma = pd.read_excel(excel_file, sheet_name=turma_selecionada)
df_turma.columns = df_turma.columns.str.strip()
if 'Disciplina' in df_turma.columns:
    df_turma['Disciplina'] = df_turma['Disciplina'].astype(str).str.strip()

df_turma["Data"] = pd.to_datetime(df_turma["Data"], errors='coerce')
df_turma.dropna(subset=["Data"], inplace=True)
df_turma = df_turma[df_turma["Data"] != "2026-06-07"]

disciplinas = sorted(df_turma["Disciplina"].dropna().unique().tolist())
if not disciplinas:
    disciplinas = ["Biologia"]
disciplina_selecionada = st.sidebar.selectbox("Selecione a Disciplina", disciplinas)

col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    mes = st.selectbox("Mês", range(1, 13), format_func=lambda x: MESES_PT[x], index=9) # Outubro padrão
with col_m2:
    ano = st.number_input("Ano", value=2026, min_value=2024, max_value=2030)

if mes != st.session_state.mes_anterior or ano != st.session_state.ano_anterior:
    st.session_state.dia_selecionado = None
    st.session_state.mes_anterior = mes
    st.session_state.ano_anterior = ano

coluna_quantidade = next((col for col in df_turma.columns if 'quant' in col.lower()), "Quantidade")

# --- FILTRAGEM E CÁLCULO SEGURO ---
df_filtrado_disc = df_turma[df_turma["Disciplina"] == disciplina_selecionada]
df_ano = df_filtrado_disc[df_filtrado_disc["Data"].dt.year == ano]

if coluna_quantidade in df_ano.columns and not df_ano.empty:
    df_ano[coluna_quantidade] = pd.to_numeric(df_ano[coluna_quantidade], errors='coerce').fillna(0)
    total_periodos_ano = int(df_ano[coluna_quantidade].sum())
else:
    total_periodos_ano = len(df_ano)

df_mes = df_ano[df_ano["Data"].dt.month == mes]

if coluna_quantidade in df_mes.columns and not df_mes.empty:
    df_mes[coluna_quantidade] = pd.to_numeric(df_mes[coluna_quantidade], errors='coerce').fillna(0)
    total_periodos_mes = int(df_mes[coluna_quantidade].sum())
else:
    total_periodos_mes = len(df_mes)

# Interface de Métricas (Top)
st.markdown(f"""
    <table style='width:100%; border:none; margin-bottom:20px;'>
        <tr>
            <td style='width:50%; border:none;'>
                <div class='card-metrica-topo'>
                    <span style='font-size:14px; color:#a7f3d0;'>Total no Mês ({MESES_PT[mes]})</span><br>
                    <span style='font-size:32px; font-weight:bold; color:#00ff66;'>{total_periodos_mes} pd</span>
                </div>
            </td>
            <td style='width:50%; border:none;'>
                <div class='card-metrica-topo'>
                    <span style='font-size:14px; color:#a7f3d0;'>Total no Ano ({ano})</span><br>
                    <span style='font-size:32px; font-weight:bold; color:#00ff66;'>{total_periodos_ano} pd</span>
                </div>
            </td>
        </tr>
    </table>
""", unsafe_allow_html=True)

# SOLICITAÇÃO ATENDIDA: Inclusão do Mês ativo diretamente ao lado do nome da Disciplina
st.markdown(f"### Turma: {turma_selecionada} | Disciplina: {disciplina_selecionada} - {MESES_PT[mes]}")

# CONTAGEM REAL POR DATA REAL
aulas_por_dia = {}
if not df_mes.empty:
    if coluna_quantidade in df_mes.columns:
        contagem_df = df_mes.groupby(df_mes["Data"].dt.day)[coluna_quantidade].sum().to_dict()
    else:
        contagem_df = df_mes.groupby(df_mes["Data"].dt.day).size().to_dict()
        
    for d, total in contagem_df.items():
        if total > 0:
            aulas_por_dia[d] = int(total)

# --- CONSTRUÇÃO DA GRADE DO CALENDÁRIO EMBUTIDO (HTML + JS INTEGRADOR) ---

cal = calendar.Calendar(firstweekday=0)
semanas = cal.monthdayscalendar(ano, mes)
html_calendario = """
<div style="background-color:#040805; padding:5px; border-radius:12px; font-family:sans-serif;">
    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; text-align: center; margin-bottom: 12px;">
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Seg</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Ter</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Qua</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Qui</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Sex</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Sáb</div>
        <div style="color:#00ff66; font-weight:bold; font-size:14px;">Dom</div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px;">
"""

for semana in semanas:
    for dia_num in semana:
        if dia_num == 0:
            html_calendario += '<div style="height: 75px;"></div>'
        else:
            if dia_num in aulas_por_dia:
                qtd_pds = aulas_por_dia[dia_num]
                html_calendario += f"""
                <button onclick="Streamlit.setComponentValue({dia_num})"
                    style="height: 75px; background-color: rgba(0, 255, 102, 0.25); border: 2px solid #00ff66;
                    color: #ffffff; font-size: 19px; font-weight: 900; border-radius: 8px; cursor: pointer;
                    box-shadow: 0 0 15px rgba(0, 255, 102, 0.5), inset 0 0 5px rgba(0, 255, 102, 0.2); transition: 0.2s;">
                    {dia_num:02d}<br><span style="font-size: 13px; color: #00ff66; font-weight: bold;">{qtd_pds} pd</span>
                </button>
                """
            else:
                html_calendario += f"""
                <button onclick="Streamlit.setComponentValue({dia_num})"
                    style="height: 75px; background-color: rgba(255, 255, 255, 0.02) !important; border: 1px solid rgba(240, 253, 244, 0.12) !important;
                    color: rgba(240, 253, 244, 0.35) !important; font-size: 18px; font-weight: normal; border-radius: 8px; cursor: pointer; transition: 0.2s;">
                    {dia_num:02d}
                </button>
                """

html_calendario += """
    </div>
</div>
<script>
    const Streamlit = {
        setComponentValue: function(value) {
            window.parent.postMessage({
                type: 'streamlit:set_component_value',
                value: value
            }, '*');
        }
    };
</script>
"""

resposta_iframe = st.components.v1.html(html_calendario, height=450, scrolling=False)

# CORREÇÃO DO TRAVAMENTO BLINDADA: Só executa a conversão se o valor retornado não for vazio/nulo
if resposta_iframe is not None and resposta_iframe != "":
    st.session_state.dia_selecionado = int(resposta_iframe)

# --- FORMULÁRIO DE LANÇAMENTO INFERIOR ---

st.write("---")
dia_escolhido = st.session_state.dia_selecionado

if dia_escolhido is not None:
    st.markdown(f"⚡ Dia Selecionado para Gerenciamento: {dia_escolhido:02d}/{mes:02d}/{ano}", unsafe_allow_html=True)
    data_alvo = pd.to_datetime(f"{ano}-{mes}-{dia_escolhido}")
    registro_existente = df_mes[df_mes["Data"] == data_alvo]
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nova_disciplina = st.text_input("Disciplina do Lançamento", value=disciplina_selecionada)
    with col_f2:
        if coluna_quantidade in registro_existente.columns and not registro_existente.empty:
            periodos_sugeridos = int(registro_existente[coluna_quantidade].sum())
        else:
            periodos_sugeridos = int(len(registro_existente)) if not registro_existente.empty else 1
        num_periodos = st.number_input("Quantidade de Períodos", min_value=1, max_value=10, value=max(1, periodos_sugeridos))
        
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("💾 Salvar/Alterar Registro", key="btn_salvar_inf", use_container_width=True):
            df_limpo = df_turma[~((df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == nova_disciplina))]
            novas_linhas = [{"Data": data_alvo, "Disciplina": nova_disciplina, coluna_quantidade: num_periodos}]
            df_final_turma = pd.concat([df_limpo, pd.DataFrame(novas_linhas)], ignore_index=True)
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for nome_aba in turmas_disponiveis:
                    if nome_aba == turma_selecionada:
                        df_final_turma["Data"] = df_final_turma["Data"].dt.strftime('%Y-%m-%d')
                        df_final_turma.to_excel(writer, sheet_name=nome_aba, index=False)
                    else:
                        df_carregada_outra = pd.read_excel(excel_file, sheet_name=nome_aba)
                        if 'Data' in df_carregada_outra.columns:
                            df_carregada_outra['Data'] = pd.to_datetime(df_carregada_outra['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
                        df_carregada_outra.to_excel(writer, sheet_name=nome_aba, index=False)
            st.success("✓ Registro updated!")
            st.rerun()
            
    with col_b2:
        if st.button("🗑️ Deletar Aula do Calendário", key="btn_deletar_inf", use_container_width=True):
            df_restante = df_turma[~((df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == disciplina_selecionada))]
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for nome_aba in turmas_disponiveis:
                    if nome_aba == turma_selecionada:
                        df_restante["Data"] = df_restante["Data"].dt.strftime('%Y-%m-%d')
                        df_restante.to_excel(writer, sheet_name=nome_aba, index=False)
                    else:
                        df_carregada_outra = pd.read_excel(excel_file, sheet_name=nome_aba)
                        if 'Data' in df_carregada_outra.columns:
                            df_carregada_outra['Data'] = pd.to_datetime(df_carregada_outra['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
                        df_carregada_outra.to_excel(writer, sheet_name=nome_aba, index=False)
            st.session_state.dia_selecionado = None
            st.rerun()
else:
    st.info("💡 Clique em qualquer botão de dia na grade do calendário acima para gerenciar os dados.")
