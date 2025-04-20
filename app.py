import streamlit as st
import pandas as pd
from io import BytesIO
import unidecode
import re

# Configuração do Streamlit
st.set_page_config(page_title="Gestão de Restaurante", layout="wide")
st.title("📊 Sistema de Gestão de Restaurante")

# ========================== AGENTE DE CONSUMO ==========================
st.header("📉 Análise de Consumo de Estoque")
file_consumo = st.file_uploader("Faça upload da planilha de CONSUMO", type=["xlsx"], key="consumo")

if file_consumo:
    try:
        df = pd.read_excel(file_consumo)
        df = df.dropna(how="all")

        if df.shape[1] < 12:
            st.error("⚠️ A planilha precisa conter as 3 seções (Estoque Inicial, Compras e Estoque Final) lado a lado.")
        else:
            # Separando as seções da planilha
            ini = df.iloc[:, :4].copy()
            compras = df.iloc[:, 4:8].copy()
            fim = df.iloc[:, 8:12].copy()

            # Definindo as colunas
            ini.columns = compras.columns = fim.columns = ["ITEM", "QUANTIDADE", "VALOR UNITÁRIO", "VALOR TOTAL"]
            ini = ini.dropna(subset=["ITEM"])
            compras = compras.dropna(subset=["ITEM"])
            fim = fim.dropna(subset=["ITEM"])

            # Função para limpar e processar os dados
            def limpar(df):
                df = df.copy()
                df["ITEM"] = df["ITEM"].astype(str).str.lower().str.strip()
                df["QUANTIDADE"] = pd.to_numeric(df["QUANTIDADE"], errors="coerce").fillna(0)

                def ajustar_valor(valor):
                    if pd.isna(valor):
                        return 0.0
                    valor = str(valor)
                    valor = re.sub(r"[^\d,]", "", valor)
                    if valor.count(",") == 1:
                        valor = valor.replace(",", ".")
                    else:
                        valor = valor.replace(",", "")
                    try:
                        return float(valor)
                    except:
                        return 0.0

                df["VALOR TOTAL"] = df["VALOR TOTAL"].apply(ajustar_valor).fillna(0)
                return df.groupby("ITEM", as_index=False).agg({"QUANTIDADE": "sum", "VALOR TOTAL": "sum"})

            # Processando as seções
            ini = limpar(ini)
            compras = limpar(compras)
            fim = limpar(fim)

            # Mesclando os dados de todas as seções
            base = pd.merge(ini, compras, on="ITEM", how="outer", suffixes=("_INI", "_ENT"))
            base = pd.merge(base, fim, on="ITEM", how="outer")
            base = base.rename(columns={"QUANTIDADE": "QUANTIDADE_FIM", "VALOR TOTAL": "TOTAL_FIM"})

            # Calculando o consumo
            base = base.fillna(0)
            base["QUANT_CONSUMO"] = base["QUANTIDADE_INI"] + base["QUANTIDADE_ENT"] - base["QUANTIDADE_FIM"]
            base["TOTAL_CONSUMO"] = base["VALOR TOTAL_INI"] + base["VALOR TOTAL_ENT"] - base["TOTAL_FIM"]

            # Resultado final
            resultado = base[["ITEM", "QUANT_CONSUMO", "TOTAL_CONSUMO"]]
            resultado = resultado[resultado["QUANT_CONSUMO"] > 0]
            resultado = resultado.sort_values(by="TOTAL_CONSUMO", ascending=False).reset_index(drop=True)

            # Exibindo o resultado
            st.subheader("📈 Relatório de Consumo de Insumos")
            st.dataframe(
                resultado.style.format({
                    "QUANT_CONSUMO": "{:.2f}",
                    "TOTAL_CONSUMO": lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                }),
                use_container_width=True
            )

            # Preparando para download
            excel_consumo = BytesIO()
            resultado.to_excel(excel_consumo, index=False, engine='openpyxl')
            st.download_button("📥 Baixar Relatório de Consumo (.xlsx)", data=excel_consumo.getvalue(), file_name="relatorio_consumo_estoque.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Erro ao processar a planilha de consumo: {e}")


# ========================== AGENTE DE VENDAS ==========================
st.header("🍽️ Análise de Maiores Vendas")
file_vendas = st.file_uploader("Faça upload da planilha de VENDAS", type=["xlsx"], key="vendas")

if file_vendas:
    try:
        df = pd.read_excel(file_vendas, skiprows=3)
        df["ITEM"] = df["ITEM"].astype(str).apply(lambda x: unidecode.unidecode(x).lower().strip())

        # Agrupar e calcular os totais de cada item de vendas
        resumo = []
        for nome, cond in pratos.items():
            f = df["ITEM"].apply(cond)
            qtd = int(df.loc[f, "QUANTIDADE"].sum())
            val = df.loc[f, "VALOR TOTAL"].sum()
            if qtd > 0:
                resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

        for nome, cond in combos.items():
            f = df["ITEM"].apply(cond)
            qtd = int(df.loc[f, "QUANTIDADE"].sum())
            val = df.loc[f, "VALOR TOTAL"].sum()
            if qtd > 0:
                resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

        for nome, tags in refrigerantes.items():
            f = df["ITEM"].apply(lambda x: contem_tags(x, tags))
            qtd = int(df.loc[f, "QUANTIDADE"].sum())
            val = df.loc[f, "VALOR TOTAL"].sum()
            if qtd > 0:
                resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

        resumo_df = pd.DataFrame(resumo)
        resumo_df["Valor Num"] = resumo_df["Valor Total"].str.replace("R\$ ", "", regex=True).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
        resumo_df = resumo_df.sort_values(by="Valor Num", ascending=False).drop(columns="Valor Num")

        st.subheader("🛒 Resumo Final Agrupado")
        st.dataframe(resumo_df, use_container_width=True)

        # Preparando para download
        excel_vendas = BytesIO()
        resumo_df.to_excel(excel_vendas, index=False, engine='openpyxl')
        st.download_button("📥 Baixar Relatório de Vendas (.xlsx)", data=excel_vendas.getvalue(), file_name="relatorio_vendas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Erro ao processar a planilha de vendas: {e}")
