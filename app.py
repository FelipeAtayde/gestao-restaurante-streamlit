import pandas as pd
import streamlit as st
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Gestão de Restaurante", layout="wide")
st.title("📊 Sistema de Gestão de Restaurante")

# ========================== AGENTE DE CONSUMO ==========================
st.header("📉 Análise de Consumo de Estoque")
file_consumo = st.file_uploader("Faça upload da planilha de CONSUMO", type=["xlsx"], key="consumo")

if file_consumo:
    try:
        # Leitura da planilha de consumo
        df = pd.read_excel(file_consumo, header=0)  # Carregar com o cabeçalho correto

        # Verificando as primeiras linhas da planilha
        st.write(df.head())

        # Renomeando as colunas com base na estrutura que você forneceu
        df.columns = [
            "ITEM", "QUANTIDADE_INICIAL", "VALOR_UNITARIO_INICIAL", "VALOR_TOTAL_INICIAL",  # Colunas do estoque inicial
            "ITEM_COMPRAS", "QUANTIDADE_COMPRAS", "VALOR_UNITARIO_COMPRAS", "VALOR_TOTAL_COMPRAS",  # Colunas de compras
            "ITEM_FINAL", "QUANTIDADE_FINAL", "VALOR_UNITARIO_FINAL", "VALOR_TOTAL_FINAL"  # Colunas do estoque final
        ]

        # Agora, vamos remover linhas em branco e garantir que o processamento seja feito com números
        df = df.dropna(how="all")

        # Convertendo valores numéricos para garantir que podemos realizar cálculos
        df["QUANTIDADE_INICIAL"] = pd.to_numeric(df["QUANTIDADE_INICIAL"], errors="coerce").fillna(0)
        df["VALOR_TOTAL_INICIAL"] = pd.to_numeric(df["VALOR_TOTAL_INICIAL"], errors="coerce").fillna(0)
        df["QUANTIDADE_COMPRAS"] = pd.to_numeric(df["QUANTIDADE_COMPRAS"], errors="coerce").fillna(0)
        df["VALOR_TOTAL_COMPRAS"] = pd.to_numeric(df["VALOR_TOTAL_COMPRAS"], errors="coerce").fillna(0)
        df["QUANTIDADE_FINAL"] = pd.to_numeric(df["QUANTIDADE_FINAL"], errors="coerce").fillna(0)
        df["VALOR_TOTAL_FINAL"] = pd.to_numeric(df["VALOR_TOTAL_FINAL"], errors="coerce").fillna(0)

        # Calculando o consumo
        df["QUANT_CONSUMO"] = df["QUANTIDADE_INICIAL"] + df["QUANTIDADE_COMPRAS"] - df["QUANTIDADE_FINAL"]
        df["TOTAL_CONSUMO"] = df["VALOR_TOTAL_INICIAL"] + df["VALOR_TOTAL_COMPRAS"] - df["VALOR_TOTAL_FINAL"]

        # Exibindo o relatório de consumo
        st.subheader("📊 Relatório de Consumo de Insumos")
        df_resultado = df[["ITEM", "QUANT_CONSUMO", "TOTAL_CONSUMO"]]
        st.dataframe(df_resultado, use_container_width=True)

        # Baixar o arquivo de consumo
        excel_consumo = BytesIO()
        df_resultado.to_excel(excel_consumo, index=False, engine='openpyxl')
        st.download_button("💾 Baixar Relatório de Consumo (.xlsx)", data=excel_consumo.getvalue(), file_name="relatorio_consumo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Erro ao processar a planilha de consumo: {e}")
