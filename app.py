import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sistema de Análise de Vendas e Consumo de Estoque", layout="wide")
st.title("📊 Sistema Integrado de Vendas e Consumo")

# Função auxiliar para exportar para Excel

def converte_para_excel_resumo(qtd_total, valor_total):
    df = pd.DataFrame({
        "Descrição": ["Quantidade Total Consumida", "Valor Total Gasto"],
        "Valor": [qtd_total, f"R$ {valor_total:,.2f}"]
    })
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resumo')
    return output.getvalue()

# --------------------- AGENTE DE ANÁLISE DE VENDAS ---------------------
st.subheader("🧾 Análise de Vendas")
vendas_file = st.file_uploader("Envie a planilha de vendas", type=["xlsx"], key="vendas")

if vendas_file:
    df_vendas = pd.read_excel(vendas_file)

    df_vendas.columns = [col.strip().lower() for col in df_vendas.columns]
    col_itens = next((col for col in df_vendas.columns if "item" in col and "op" in col), None)

    if col_itens:
        df_vendas = df_vendas.dropna(subset=[col_itens])
        df_vendas[col_itens] = df_vendas[col_itens].astype(str).str.lower()

        def classificar(item):
            if any(p in item for p in ['pequeno']): return 'PEQUENO'
            if any(g in item for g in ['grande']): return 'GRANDE'
            if any(r in item for r in ['guaraná', 'coca', 'refrigerante']): return 'BEBIDA'
            if 'combo' in item: return 'COMBO'
            return 'PRATO'

        df_vendas['categoria'] = df_vendas[col_itens].apply(classificar)

        agrupado = df_vendas.groupby(['categoria', col_itens], as_index=False).agg({
            'quantidade': 'sum',
            'valor total': 'sum'
        })
        agrupado = agrupado.sort_values(by='valor total', ascending=False)

        pequenos = df_vendas[df_vendas['categoria'] == 'PEQUENO']['quantidade'].sum()
        grandes = df_vendas[df_vendas['categoria'] == 'GRANDE']['quantidade'].sum()
        total = pequenos + grandes

        st.markdown(f"### Totais Gerais")
        st.markdown(f"**Pequenos:** {pequenos:.0f} | **Grandes:** {grandes:.0f} | **Total:** {total:.0f}")

        st.markdown("### Detalhamento por Item")
        st.dataframe(agrupado, use_container_width=True)

        st.download_button(
            label="💾 Baixar Relatório em Excel",
            data=converte_para_excel_resumo(total, agrupado['valor total'].sum()),
            file_name="relatorio_vendas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("A planilha precisa conter uma coluna com os nomes dos itens e opções.")

# --------------------- AGENTE DE CONSUMO DE ESTOQUE ---------------------
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

    total_qtd = df['Qtd_Consumida'].sum()
    total_valor = df['Valor_Consumido'].sum()

    st.markdown("### Totais Gerais de Consumo")
    st.markdown(f"**Quantidade Consumida:** {total_qtd:.2f}")
    st.markdown(f"**Valor Total Gasto:** R$ {total_valor:,.2f}")

    top5 = df.sort_values(by='Qtd_Consumida', ascending=False).head(5)
    st.markdown("### 🟥 Top 5 Itens Mais Consumidos")
    st.dataframe(top5.style.set_properties(**{'color': 'red'}), use_container_width=True)

    st.download_button(
        label="💾 Baixar Resumo em Excel",
        data=converte_para_excel_resumo(total_qtd, total_valor),
        file_name="relatorio_consumo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Por favor, envie a planilha para iniciar a análise.")
