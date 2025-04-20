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
        df = pd.read_excel(file_consumo)

        # Exibe as informações da planilha
        st.write("Número de colunas:", len(df.columns))
        st.write("Cabeçalho da planilha:", df.columns)

        # Verificando se a planilha tem o número de colunas esperado (14 colunas)
        if len(df.columns) != 14:
            st.error(f"Erro: A planilha precisa ter 14 colunas, mas ela tem {len(df.columns)} colunas.")
        else:
            # Nomeação das colunas para facilitar o manuseio
            df.columns = ['item_inicial', 'quantidade_inicial', 'valor_unitario_inicial', 'valor_total_inicial',
                          'item_compras', 'quantidade_compras', 'valor_unitario_compras', 'valor_total_compras',
                          'item_final', 'quantidade_final', 'valor_unitario_final', 'valor_total_final', 'coluna_extra_1', 'coluna_extra_2']

            # Limpando os dados
            df['item_inicial'] = df['item_inicial'].astype(str).str.strip()
            df['item_compras'] = df['item_compras'].astype(str).str.strip()
            df['item_final'] = df['item_final'].astype(str).str.strip()

            # Agrupando itens e somando as quantidades e valores totais
            df_grouped = df.groupby('item_inicial', as_index=False).agg({
                'quantidade_inicial': 'sum',
                'valor_total_inicial': 'sum',
                'quantidade_compras': 'sum',
                'valor_total_compras': 'sum',
                'quantidade_final': 'sum',
                'valor_total_final': 'sum'
            })

            # Calculando o consumo
            df_grouped['quant_consumo'] = df_grouped['quantidade_inicial'] + df_grouped['quantidade_compras'] - df_grouped['quantidade_final']
            df_grouped['total_consumo'] = df_grouped['valor_total_inicial'] + df_grouped['valor_total_compras'] - df_grouped['valor_total_final']

            # Exibindo o resultado
            st.subheader("📊 Relatório de Consumo de Insumos")
            st.dataframe(df_grouped[['item_inicial', 'quant_consumo', 'total_consumo']], use_container_width=True)

            # Baixar o arquivo de consumo
            excel_consumo = BytesIO()
            df_grouped.to_excel(excel_consumo, index=False, engine='openpyxl')
            st.download_button("💾 Baixar Relatório de Consumo (.xlsx)", data=excel_consumo.getvalue(), file_name="relatorio_consumo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Erro ao processar a planilha de consumo: {e}")
