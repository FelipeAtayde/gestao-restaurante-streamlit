import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sistema de Análise de Vendas e Consumo de Estoque", layout="wide")
st.title("📊 Sistema Integrado de Vendas e Consumo")

menu = st.sidebar.radio("Selecione o agente:", ["Análise de Vendas", "Consumo de Estoque"])

# Função auxiliar para exportar para Excel
def converte_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

if menu == "Análise de Vendas":
    st.subheader("🧾 Análise de Vendas")
    vendas_file = st.file_uploader("Envie a planilha de vendas", type=["xlsx"], key="vendas")

    if vendas_file:
        df_vendas = pd.read_excel(vendas_file)

        df_vendas.columns = [col.strip().lower() for col in df_vendas.columns]
        df_vendas = df_vendas.dropna(subset=['itens e opções'])

        df_vendas['itens e opções'] = df_vendas['itens e opções'].astype(str).str.lower()

        def classificar(item):
            if any(p in item for p in ['pequeno']): return 'PEQUENO'
            if any(g in item for g in ['grande']): return 'GRANDE'
            if any(r in item for r in ['guaraná', 'coca', 'refrigerante']): return 'BEBIDA'
            if 'combo' in item: return 'COMBO'
            return 'PRATO'

        df_vendas['categoria'] = df_vendas['itens e opções'].apply(classificar)

        agrupado = df_vendas.groupby(['categoria', 'itens e opções'], as_index=False).agg({
            'quantidade': 'sum',
            'valor total': 'sum'
        })
        agrupado = agrupado.sort_values(by='valor total', ascending=False)

        # Totais pequenos e grandes
        pequenos = df_vendas[df_vendas['categoria'] == 'PEQUENO']['quantidade'].sum()
        grandes = df_vendas[df_vendas['categoria'] == 'GRANDE']['quantidade'].sum()
        total = pequenos + grandes

        st.markdown(f"### Totais Gerais")
        st.markdown(f"**Pequenos:** {pequenos:.0f} | **Grandes:** {grandes:.0f} | **Total:** {total:.0f}")

        st.markdown("### Detalhamento por Item")
        st.dataframe(agrupado, use_container_width=True)

        st.download_button(
            label="💾 Baixar Relatório em Excel",
            data=converte_para_excel(agrupado),
            file_name="relatorio_vendas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif menu == "Consumo de Estoque":
    st.subheader("📊 Relatório de Consumo de Estoque")
    uploaded_file = st.file_uploader("Envie a planilha de estoque", type=["xlsx"], key="estoque")

    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        df_raw = xls.parse(xls.sheet_names[0], header=None)

        estoque_inicial = df_raw.iloc[2:, 0:4]
        compras = df_raw.iloc[2:, 5:9]
        estoque_final = df_raw.iloc[2:, 10:14]

        estoque_inicial.columns = ['Item', 'Qtd_EI', 'VU_EI', 'VT_EI']
        compras.columns = ['Item', 'Qtd_C', 'VU_C', 'VT_C']
        estoque_final.columns = ['Item', 'Qtd_EF', 'VU_EF', 'VT_EF']

        def normaliza(df):
            df = df.dropna(subset=['Item'])
            df['Item'] = df['Item'].astype(str).str.strip().str.upper()
            return df

        estoque_inicial = normaliza(estoque_inicial)
        compras = normaliza(compras)
        estoque_final = normaliza(estoque_final)

        def agrupar(df, qtd_col, valor_col):
            return df.groupby('Item', as_index=False)[[qtd_col, valor_col]].sum()

        ei = agrupar(estoque_inicial, 'Qtd_EI', 'VT_EI')
        c = agrupar(compras, 'Qtd_C', 'VT_C')
        ef = agrupar(estoque_final, 'Qtd_EF', 'VT_EF')

        df = pd.merge(ei, c, on='Item', how='outer')
        df = pd.merge(df, ef, on='Item', how='outer')
        df = df.fillna(0)

        df['Qtd_Consumida'] = df['Qtd_EI'] + df['Qtd_C'] - df['Qtd_EF']
        df['Valor_Consumido'] = df['VT_EI'] + df['VT_C'] - df['VT_EF']

        df = df[['Item', 'Qtd_EI', 'Qtd_C', 'Qtd_EF', 'Qtd_Consumida', 'Valor_Consumido']]
        df = df.sort_values(by='Valor_Consumido', ascending=False).reset_index(drop=True)

        st.markdown("### Detalhamento de Consumo")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            label="💾 Baixar Relatório em Excel",
            data=converte_para_excel(df),
            file_name="relatorio_consumo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Por favor, envie a planilha para iniciar a análise.")
