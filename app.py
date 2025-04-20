import streamlit as st
import pandas as pd
import unidecode
from io import BytesIO
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

st.set_page_config(page_title="Gestão de Restaurante", layout="wide")
st.title("📊 Sistema de Gestão de Restaurante")

# ========================== ANÁLISE DE CONSUMO ==========================

st.header("📦 Análise de Consumo de Estoque")
file_consumo = st.file_uploader("Faça upload da planilha de CONSUMO", type=["xlsx"], key="consumo")

if file_consumo:
    try:
        df = pd.read_excel(file_consumo)
        df = df.dropna(how="all")

        if df.shape[1] < 12:
            st.error("⚠️ A planilha precisa conter as 3 seções (Estoque Inicial, Compras e Estoque Final) lado a lado.")
        else:
            ini = df.iloc[:, :4].copy()
            compras = df.iloc[:, 4:8].copy()
            fim = df.iloc[:, 8:12].copy()

            ini.columns = compras.columns = fim.columns = ["item", "quantidade", "valor unitario", "valor total"]
            ini = ini.dropna(subset=["item"])
            compras = compras.dropna(subset=["item"])
            fim = fim.dropna(subset=["item"])

            def limpar(df):
                df = df.copy()
                df["item"] = df["item"].astype(str).str.lower().str.strip()
                df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)

                def converter_valor(valor):
                    try:
                        if isinstance(valor, str):
                            valor = valor.replace("R$", "").strip()
                            return locale.atof(valor)
                        return float(valor)
                    except:
                        return 0.0

                df["valor total"] = df["valor total"].apply(converter_valor)
                return df.groupby("item")[["quantidade", "valor total"]].sum().reset_index()

            ini = limpar(ini)
            compras = limpar(compras)
            fim = limpar(fim)

            base = pd.merge(ini, compras, on="item", how="outer", suffixes=("_ini", "_ent"))
            base = pd.merge(base, fim, on="item", how="outer")
            base = base.rename(columns={"quantidade": "quant_fim", "valor total": "total_fim"})

            base = base.fillna(0)
            base["quant_consumo"] = base["quantidade_ini"] + base["quantidade_ent"] - base["quant_fim"]
            base["total_consumo"] = base["valor total_ini"] + base["valor total_ent"] - base["total_fim"]

            resultado = base[["item", "quant_consumo", "total_consumo"]]
            resultado = resultado[resultado["quant_consumo"] > 0]
            resultado = resultado.sort_values(by="total_consumo", ascending=False).reset_index(drop=True)

            def destacar_top_5(val):
                cor = 'color: red; font-weight: bold' if val.name < 5 else ''
                return [cor] * len(val)

            st.subheader("📦 Relatório de Consumo de Insumos")
            st.dataframe(resultado.style.apply(destacar_top_5, axis=1).format({"quant_consumo": "{:.2f}", "total_consumo": "R$ {:.2f}"}), use_container_width=True)

            excel_consumo = BytesIO()
            resultado.to_excel(excel_consumo, index=False, engine='openpyxl')
            st.download_button("📥 Baixar Consumo de Estoque (.xlsx)", data=excel_consumo.getvalue(), file_name="analise_consumo_estoque.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Erro ao processar a planilha de consumo: {e}")

# ========================== ANÁLISE DE VENDAS ==========================
# [restante do código omitido por brevidade — pode ser colado aqui conforme necessário]
