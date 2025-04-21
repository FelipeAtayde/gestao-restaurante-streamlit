import streamlit as st
import pandas as pd
from io import BytesIO
from unidecode import unidecode
import re
import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="📊 Análise de Vendas e Consumo de Estoque", layout="centered")
st.title("📊 Sistema Integrado de Vendas e Consumo")

# ========================== AGENTE DE VENDAS ==========================
st.header("🍽️ Análise de Maiores Vendas")
file_vendas = st.file_uploader("Faça upload da planilha de VENDAS", type=["xlsx"], key="vendas")

# (mantido o agente de vendas completo sem alterações)
# ... (mantém tudo acima como estava no agente de vendas) ...

# ========================== AGENTE DE CONSUMO ==========================
st.header("📦 Analisador de Consumo de Estoque")
st.markdown("Faça upload da planilha Excel com as colunas horizontais para obter um relatório de consumo.")

HIST_DIR = "historico_relatorios"
os.makedirs(HIST_DIR, exist_ok=True)

URL_DRIVE = "https://drive.google.com/drive/my-drive"

def normalizar_nome(nome):
    if pd.isna(nome): return ""
    return unidecode(str(nome)).strip().lower()

def extrair_valor(valor):
    if pd.isna(valor): return 0.0
    valor_str = str(valor).replace("R$", "").replace(" ", "").strip()
    valor_str = re.sub(r"[^0-9,\.]+", "", valor_str)
    if "," in valor_str and "." in valor_str:
        if valor_str.rfind(",") > valor_str.rfind("."):
            valor_str = valor_str.replace(".", "").replace(",", ".")
        else:
            valor_str = valor_str.replace(",", "")
    elif "," in valor_str:
        valor_str = valor_str.replace(",", ".")
    try:
        return float(valor_str)
    except:
        return 0.0

def detectar_unidade(item):
    item = item.lower()
    if any(x in item for x in ["kg", "quilo", "grama", "g"]): return "KG"
    elif any(x in item for x in ["litro", "ml"]): return "L"
    elif any(x in item for x in ["caixa", "pct", "pacote"]): return "PCT"
    else: return "UN"

def extrair_bloco_horizontal(df, col_inicio, col_fim):
    dados = []
    for i in range(1, len(df)):
        linha = df.iloc[i, col_inicio:col_fim].tolist()
        if len(linha) >= 4 and pd.notna(linha[0]):
            item = normalizar_nome(linha[0])
            try:
                qtd = extrair_valor(linha[1])
                val = extrair_valor(linha[3])
                if item:
                    dados.append({'Item': item, 'Quantidade': qtd, 'Valor total': val})
            except:
                continue
    return pd.DataFrame(dados)

def exportar_excel_formatado(df, path):
    df.to_excel(path, index=False)
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    for column_cells in ws.columns:
        max_length = 0
        column = column_cells[0].column_letter
        for cell in column_cells:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2
    col_idx = [cell.column for cell in ws[1] if cell.value == "Valor consumido"]
    if col_idx:
        col_letter = get_column_letter(col_idx[0])
        top5_vals = df.nlargest(5, "Valor consumido")["Valor consumido"].tolist()
        for row in range(2, len(df)+2):
            cell = ws[f"{col_letter}{row}"]
            if cell.value in top5_vals:
                cell.font = Font(color="FF0000")
    wb.save(path)

def analisar_consumo_estoque(file):
    df = pd.read_excel(file, sheet_name=0, header=None)
    colunas = df.iloc[0].astype(str).apply(lambda x: unidecode(str(x)).strip().lower())

    col_estoque_ini_idx = colunas[colunas.str.contains("estoque.*inicial")]
    col_compras_idx = colunas[colunas.str.contains("compras")]
    col_estoque_fim_idx = colunas[colunas.str.contains("estoque.*final")]

    if col_estoque_ini_idx.empty or col_compras_idx.empty or col_estoque_fim_idx.empty:
        st.error("❌ Não foi possível localizar os blocos de dados. Verifique os títulos da planilha.")
        return None

    col_estoque_ini = col_estoque_ini_idx.index[0]
    col_compras = col_compras_idx.index[0]
    col_estoque_fim = col_estoque_fim_idx.index[0]

    estoque_inicial = extrair_bloco_horizontal(df, col_estoque_ini, col_compras)
    compras = extrair_bloco_horizontal(df, col_compras, col_estoque_fim)
    estoque_final = extrair_bloco_horizontal(df, col_estoque_fim, col_estoque_fim + 4)

    def agrupar(df):
        return df.groupby('Item', as_index=False).agg({'Quantidade': 'sum', 'Valor total': 'sum'})

    estoque_inicial = agrupar(estoque_inicial)
    compras = agrupar(compras)
    estoque_final = agrupar(estoque_final)

    ini_qtd = dict(zip(estoque_inicial['Item'], estoque_inicial['Quantidade']))
    ini_val = dict(zip(estoque_inicial['Item'], estoque_inicial['Valor total']))

    comp_qtd = dict(zip(compras['Item'], compras['Quantidade']))
    comp_val = dict(zip(compras['Item'], compras['Valor total']))

    fin_qtd = dict(zip(estoque_final['Item'], estoque_final['Quantidade']))
    fin_val = dict(zip(estoque_final['Item'], estoque_final['Valor total']))

    itens_ordem = list(set(list(ini_qtd.keys()) + list(comp_qtd.keys()) + list(fin_qtd.keys())))
    resultado = []

    for item in itens_ordem:
        if item.strip() == "" or item.lower() == "item":
            continue
        qtd_ini = ini_qtd.get(item, 0)
        qtd_comp = comp_qtd.get(item, 0)
        qtd_fin = fin_qtd.get(item, 0)
        val_ini = ini_val.get(item, 0)
        val_comp = comp_val.get(item, 0)
        val_fin = fin_val.get(item, 0)
        qtd_consumida = qtd_ini + qtd_comp - qtd_fin
        val_consumido = val_ini + val_comp - val_fin
        if qtd_consumida == 0 and val_consumido == 0:
            continue
        unidade = detectar_unidade(item)
        resultado.append({
            'Item': item,
            'Quantidade consumida': round(qtd_consumida, 2),
            'Valor consumido': round(val_consumido, 2),
            'Unidade': unidade
        })

    resultado_df = pd.DataFrame(resultado)
    resultado_df = resultado_df.sort_values(by="Valor consumido", ascending=False)
    return resultado_df

def formatar_resultado(df):
    top5 = df.nlargest(5, "Valor consumido")
    def destaque(val):
        return 'color: red' if val in top5["Valor consumido"].values else 'color: black'
    return df.style.applymap(destaque, subset=["Valor consumido"])

file = st.file_uploader("📤 Envie sua planilha .xlsx", type=["xlsx"], key="estoque")
if file:
    if st.button("🔍 Analisar consumo"):
        resultado = analisar_consumo_estoque(file)
        if resultado is not None:
            st.success("✅ Análise concluída com sucesso!")
            st.dataframe(formatar_resultado(resultado))
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            historico_path = os.path.join(HIST_DIR, f"consumo_{now}.xlsx")
            exportar_excel_formatado(resultado, historico_path)
            with open(historico_path, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar relatório Excel",
                    data=f,
                    file_name="relatorio_consumo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            if st.button("📤 Abrir Google Drive para upload"):
                js = f"window.open('{URL_DRIVE}')"
                st.components.v1.html(f"<script>{js}</script>", height=0)
