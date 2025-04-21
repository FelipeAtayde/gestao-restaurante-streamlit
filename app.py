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

    st.subheader("Resumo de Pequenos e Grandes")
    st.write(f"Pequeno: {total_p}")
    st.write(f"Grande: {total_g}")
    st.write(f"Total: {total_geral}")

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
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": val})

    for nome, cond in combos.items():
        f = df_vendas["Itens e Opções"].apply(cond)
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": val})

    for nome, tags in refrigerantes.items():
        f = df_vendas["Itens e Opções"].apply(lambda x: contem_tags(x, tags))
        qtd = int(df_vendas.loc[f, "Quantidade"].sum())
        val = df_vendas.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": val})

    resumo_df = pd.DataFrame(resumo)
    resumo_df = resumo_df.sort_values(by="Valor Total", ascending=False)
    top5 = resumo_df.nlargest(5, "Valor Total")
    def azul_escuro(val):
        return 'color: #003366' if val in top5["Valor Total"].values else 'color: black'

    st.subheader("📋 Resumo Final Agrupado")
    st.dataframe(resumo_df.style.applymap(azul_escuro, subset=["Valor Total"]), use_container_width=True)

    output = BytesIO()
    resumo_df.to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="📅 Baixar Análise de Vendas (.xlsx)",
        data=output.getvalue(),
        file_name="analise_maiores_vendas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ========================== AGENTE DE CONSUMO ==========================
st.header("📦 Analisador de Consumo de Estoque")



do_df.sort_values(by="Valor consumido", ascending=False)
    top5 = resultado_df.nlargest(5, "Valor consumido")

    def destaque(val):
        return 'color: red' if val in top5["Valor consumido"].values else 'color: black'

    file = st.file_uploader("📤 Envie sua planilha de estoque .xlsx", type=["xlsx"], key="estoque")
    if file:
        resultado = analisar_consumo_estoque(file)
        if resultado is not None:
            st.success("✅ Análise concluída com sucesso!")
            st.dataframe(resultado.style.applymap(destaque, subset=["Valor consumido"]))
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
