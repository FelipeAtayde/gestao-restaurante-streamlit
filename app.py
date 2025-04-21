import streamlit as st
import pandas as pd
import io
from io import BytesIO

st.set_page_config(page_title="Sistema de Análise de Vendas e Consumo de Estoque", layout="wide")
st.title("📊 Sistema Integrado de Vendas e Consumo")

# --------------------- AGENTE DE ANÁLISE DE VENDAS ---------------------

st.header("🍽️ Análise de Maiores Vendas")
file_vendas = st.file_uploader("Faça upload da planilha de VENDAS", type=["xlsx"], key="vendas")

def normalizar(texto):
    return str(texto).lower().strip()

if file_vendas:
    df_vendas = pd.read_excel(file_vendas, skiprows=3)
    df_vendas["Itens e Opções"] = df_vendas["Itens e Opções"].astype(str).apply(normalizar)

    mult = {
        "- 2 pequenos": 2, "- 3 pequenos": 3, "- 4 pequenos": 4,
        "- 2 grandes": 2, "- 3 grandes": 3, "- 4 grandes": 4
    }
    for k, m in mult.items():
        df_vendas.loc[df_vendas["Itens e Opções"].str.contains(k), "Quantidade"] *= m

    pequeno = df_vendas["Itens e Opções"].str.contains("pequeno") & ~df_vendas["Itens e Opções"].str.contains("combo")
    grande = df_vendas["Itens e Opções"].str.contains("grande") & ~df_vendas["Itens e Opções"].str.contains("combo")
    total_p = int(df_vendas.loc[pequeno, "Quantidade"].sum())
    total_g = int(df_vendas.loc[grande, "Quantidade"].sum())
    total_geral = total_p + total_g

    pratos = {
        "Boi": lambda x: "boi" in x and "combo" not in x,
        "Parmegiana": lambda x: "parmegiana" in x and "combo" not in x,
        "Strogonoff": lambda x: "strogonoff" in x and "combo" not in x,
        "Feijoada": lambda x: "feijoada" in x and "2 feijoadas" not in x,
        "Tropeiro": lambda x: "tropeiro" in x and "tropeguete" not in x,
        "Tropeguete": lambda x: "tropeguete" in x,
        "Espaguete": lambda x: "espaguete" in x and "tropeguete" not in x,
        "Porco": lambda x: "porco" in x and "combo" not in x,
        "Frango": lambda x: "frango" in x and "parmegiana" not in x and "2 frangos + fritas" not in x
    }

    combos = {
        "Combo Todo Dia": lambda x: "combo todo dia" in x,
        "2 Pratos - À Sua Escolha": lambda x: "2 pratos" in x and "escolha" in x,
        "Combo Supremo": lambda x: "combo supremo" in x,
        "2 Feijoadas": lambda x: "2 feijoadas" in x,
        "2 Frangos + Fritas": lambda x: "2 frangos" in x and "fritas" in x
    }

    refrigerantes = {
        "Coca-Cola Original 350 ml": [["coca", "original", "350"]],
        "Coca-Cola Zero e Sem Açúcar 350 ml": [["coca", "zero", "350"], ["coca", "sem acucar", "350"]],
        "Coca-Cola Original 600 ml": [["coca", "original", "600"]],
        "Coca-Cola Zero 600 ml": [["coca", "zero", "600"], ["coca", "sem acucar", "600"]],
        "Coca-Cola 2 Litros": [["coca", "2l"], ["coca", "2 l"], ["coca", "2litro"]],
        "Guaraná Antarctica 350 ml": [["guarana", "350"]],
        "Guaraná Antarctica 1 Litro": [["guarana", "antarctica", "1l"], ["guarana", "antarctica", "1 l"], ["guarana", "antarctica", "1litro"]],
        "Guaraná Antarctica 2 Litros": [["guarana", "2l"], ["guarana", "2 l"], ["guarana", "2litro"]],
        "Suco": [["suco"]],
        "Refrigerante Mate Couro 1 Litro": [["mate couro", "1l"], ["guarana mate", "1l"], ["mate couro", "1 l"], ["guarana mate", "1 l"], ["mate couro", "1litro"], ["guarana mate", "1litro"]]
    }

    def contem_tags(texto, listas):
        return any(all(tag in texto for tag in tags) for tags in listas)

    resumo = []
    for nome, cond in pratos.items():
        f = df_vendas["Itens e Opções"].apply(cond)
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, cond in combos.items():
        f = df_vendas["Itens e Opções"].apply(cond)
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, tags in refrigerantes.items():
        f = df_vendas["Itens e Opções"].apply(lambda x: contem_tags(x, tags))
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    resumo_df = pd.DataFrame(resumo)
    resumo_df["Valor Num"] = resumo_df["Valor Total"].str.replace("R\$ ", "", regex=True).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    resumo_df = resumo_df.sort_values(by="Valor Num", ascending=False).drop(columns="Valor Num")

    st.subheader("Resumo de Pequenos e Grandes")
    st.write(f"Pequeno: {total_p}")
    st.write(f"Grande: {total_g}")
    st.write(f"Total: {total_geral}")

    st.subheader("📋 Resumo Final Agrupado")
    st.dataframe(resumo_df, use_container_width=True)

    excel_vendas = BytesIO()
    resumo_df.to_excel(excel_vendas, index=False, engine='openpyxl')
    st.download_button("📅 Baixar Análise de Vendas (.xlsx)", data=excel_vendas.getvalue(), file_name="analise_maiores_vendas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --------------------- AGENTE DE CONSUMO DE ESTOQUE ---------------------

st.header("📦 Analisador de Consumo de Estoque")
file_estoque = st.file_uploader("Faça upload da planilha de ESTOQUE", type=["xlsx"], key="estoque")

if file_estoque:
    xls = pd.ExcelFile(file_estoque)
    df_raw = xls.parse(xls.sheet_names[0], header=None)

    def extrair_bloco(df, start_row, col_start, col_end):
        bloco = df.iloc[start_row:, col_start:col_end].copy()
        bloco.columns = bloco.iloc[0]
        bloco = bloco[1:]
        bloco = bloco.dropna(subset=[bloco.columns[0]])
        bloco.columns = ['Item', 'Qtd', 'VU', 'VT']
        bloco['Item'] = bloco['Item'].astype(str).str.strip().str.upper()
        bloco[['Qtd', 'VU', 'VT']] = bloco[['Qtd', 'VU', 'VT']].apply(pd.to_numeric, errors='coerce').fillna(0)
        return bloco

    ei = extrair_bloco(df_raw, 2, 0, 4)
    c = extrair_bloco(df_raw, 2, 5, 9)
    ef = extrair_bloco(df_raw, 2, 10, 14)

    df = pd.merge(ei.groupby('Item', as_index=False).sum(),
                  c.groupby('Item', as_index=False).sum(),
                  on='Item', how='outer', suffixes=('_EI', '_C'))
    df = pd.merge(df, ef.groupby('Item', as_index=False).sum(),
                  on='Item', how='outer')
    df = df.rename(columns={'Qtd': 'Qtd_EF', 'VU': 'VU_EF', 'VT': 'VT_EF'})
    df = df.fillna(0)

    df['Qtd_Consumida'] = df['Qtd_EI'] + df['Qtd_C'] - df['Qtd_EF']
    df['Valor_Consumido'] = df['VT_EI'] + df['VT_C'] - df['VT_EF']

    total_qtd = df['Qtd_Consumida'].sum()
    total_valor = df['Valor_Consumido'].sum()

    st.markdown("### Totais Gerais de Consumo")
    st.markdown(f"**Quantidade Consumida:** {total_qtd:.2f}")
    st.markdown(f"**Valor Total Gasto:** R$ {total_valor:,.2f}")

    top5 = df.sort_values(by='Qtd_Consumida', ascending=False).head(5)
    st.markdown("### 🟥 Top 5 Itens Mais Consumidos")
    st.dataframe(top5.style.set_properties(**{'color': 'red'}), use_container_width=True)

    def converte_para_excel_resumo(qtd_total, valor_total):
        df_resumo = pd.DataFrame({
            "Descrição": ["Quantidade Total Consumida", "Valor Total Gasto"],
            "Valor": [qtd_total, f"R$ {valor_total:,.2f}"]
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_resumo.to_excel(writer, index=False, sheet_name='Resumo')
        return output.getvalue()

    st.download_button(
        label="📥 Baixar Relatório de Consumo (.xlsx)",
        data=converte_para_excel_resumo(total_qtd, total_valor),
        file_name="relatorio_consumo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
