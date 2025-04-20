import pandas as pd
import streamlit as st

# Carregar a planilha
file = st.file_uploader("Faça o upload da planilha", type=["xlsx"])

if file is not None:
    # Lê a planilha
    df = pd.read_excel(file)
    
    # Limpar dados
    df = df.dropna(how="all")  # Remover linhas vazias
    df = df.fillna(0)  # Substituir valores nulos por 0
    
    # Ajustando os nomes das colunas
    df.columns = ["ITEM", "QUANTIDADE_INICIAL", "VALOR_UNITARIO_INICIAL", "VALOR_TOTAL_INICIAL",
                  "ITEM_COMPRAS", "QUANTIDADE_COMPRAS", "VALOR_UNITARIO_COMPRAS", "VALOR_TOTAL_COMPRAS",
                  "ITEM_FINAL", "QUANTIDADE_FINAL", "VALOR_UNITARIO_FINAL", "VALOR_TOTAL_FINAL"]
    
    # Agrupando os itens e somando as quantidades e os valores totais apenas para a coluna de compras
    df_compras_agrupado = df.groupby("ITEM_COMPRAS").agg({
        "QUANTIDADE_COMPRAS": "sum",
        "VALOR_TOTAL_COMPRAS": "sum"
    }).reset_index()
    
    # Juntando os dados de compras agregados com o restante da planilha
    df_final = pd.merge(df, df_compras_agrupado, left_on="ITEM_COMPRAS", right_on="ITEM_COMPRAS", how="left")
    
    # Calculando o CONSUMO
    df_final["CONSUMO_QUANTIDADE"] = df_final["QUANTIDADE_INICIAL"] + df_final["QUANTIDADE_COMPRAS"] - df_final["QUANTIDADE_FINAL"]
    df_final["CONSUMO_VALOR"] = df_final["VALOR_TOTAL_INICIAL"] + df_final["VALOR_TOTAL_COMPRAS"] - df_final["VALOR_TOTAL_FINAL"]
    
    # Exibindo a tabela resultante
    st.write("Relatório de Consumo de Estoque")
    st.dataframe(df_final[["ITEM_COMPRAS", "CONSUMO_QUANTIDADE", "CONSUMO_VALOR"]])

    # Gerar arquivo para download
    excel_output = df_final[["ITEM_COMPRAS", "CONSUMO_QUANTIDADE", "CONSUMO_VALOR"]].to_excel(index=False, engine='openpyxl')
    st.download_button(
        label="Baixar Relatório de Consumo (.xlsx)",
        data=excel_output,
        file_name="relatorio_consumo_estoque.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
