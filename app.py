import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Agente de Consumo de Estoque", layout="wide")
st.title("📊 Relatório de Consumo de Estoque")

uploaded_file = st.file_uploader("Envie a planilha no formato original", type=["xlsx"])

if uploaded_file:
    # Leitura da planilha
    xls = pd.ExcelFile(uploaded_file)
    df_raw = xls.parse(xls.sheet_names[0], header=None)

    # Definindo os blocos
    estoque_inicial = df_raw.iloc[2:, 0:4]
    compras = df_raw.iloc[2:, 5:9]
    estoque_final = df_raw.iloc[2:, 10:14]

    estoque_inicial.columns = ['Item', 'Qtd_EI', 'VU_EI', 'VT_EI']
    compras.columns = ['Item', 'Qtd_C', 'VU_C', 'VT_C']
    estoque_final.columns = ['Item', 'Qtd_EF', 'VU_EF', 'VT_EF']

    # Padronizar nomes
    def normaliza(df):
        df = df.dropna(subset=['Item'])
        df['Item'] = df['Item'].astype(str).str.strip().str.upper()
        return df

    estoque_inicial = normaliza(estoque_inicial)
    compras = normaliza(compras)
    estoque_final = normaliza(estoque_final)

    # Agrupar somando por item (caso repetido)
    def agrupar(df, qtd_col, valor_col):
        return df.groupby('Item', as_index=False)[[qtd_col, valor_col]].sum()

    ei = agrupar(estoque_inicial, 'Qtd_EI', 'VT_EI')
    c = agrupar(compras, 'Qtd_C', 'VT_C')
    ef = agrupar(estoque_final, 'Qtd_EF', 'VT_EF')

    # Unificar dados
    df = pd.merge(ei, c, on='Item', how='outer')
    df = pd.merge(df, ef, on='Item', how='outer')
    df = df.fillna(0)

    # Cálculo do consumo
    df['Qtd_Consumida'] = df['Qtd_EI'] + df['Qtd_C'] - df['Qtd_EF']
    df['Valor_Consumido'] = df['VT_EI'] + df['VT_C'] - df['VT_EF']

    df = df[['Item', 'Qtd_EI', 'Qtd_C', 'Qtd_EF', 'Qtd_Consumida', 'Valor_Consumido']]
    df = df.sort_values(by='Valor_Consumido', ascending=False).reset_index(drop=True)

    st.subheader("📋 Relatório Final")
    st.dataframe(df, use_container_width=True)

    # Download Excel
    def converte_para_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Consumo')
        return output.getvalue()

    st.download_button(
        label="💾 Baixar Relatório em Excel",
        data=converte_para_excel(df),
        file_name="relatorio_consumo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Por favor, envie a planilha para iniciar a análise.")
