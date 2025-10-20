import pandas as pd
import plotly.express as px

def create_cumplimiento_bar_chart(df_raw):
    """Crea y devuelve un gráfico de barras de cumplimiento de Call Center."""
    if df_raw.empty:
        return None

    df_chart = df_raw.sort_values(by='CALL_CENTER', ascending=False).copy()
    df_chart['texto_cumplimiento'] = (df_chart['Cumplimiento'] * 100).map('{:.2f}%'.format).str.replace('.', ',')

    fig_bar = px.bar(
        df_chart, x='Cumplimiento', y='CALL_CENTER', orientation='h', text='texto_cumplimiento',
        labels={'CALL_CENTER': 'Call Center', 'Cumplimiento': 'Porcentaje de Cumplimiento'}
    )
    fig_bar.update_layout(xaxis_tickformat='.0%', yaxis_title=None, margin=dict(l=20, r=20, t=40, b=20))
    fig_bar.update_traces(textposition='auto', marker_color='#1f77b4')
    
    return fig_bar

def create_rodamiento_pie_chart(df_rodamiento_count):
    """Crea y devuelve un gráfico de torta de rodamientos."""
    if df_rodamiento_count.empty:
        return None

    fig_pie = px.pie(
        df_rodamiento_count,
        names='Rodamiento',
        values='count',
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent'
    )
    fig_pie.update_layout(
        showlegend=True,
        legend_title_text='Rodamiento',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig_pie

def create_styled_summary_table(df_raw, style_function, expected_compliance):
    """Crea y devuelve el HTML de una tabla de resumen con estilos."""
    if df_raw.empty:
        return ""
        
    df_styled = df_raw.copy()
    df_styled = df_styled.rename(columns={
        'META_$': 'Meta ($)', 'Recaudo_Meta': 'Recaudo ($)', 'Cumplimiento': 'Cumplimiento (%)',
        'NOMBRE': 'Nombre', 'Faltante': 'Faltante ($)'
    })
    
    column_order = ['CALL_CENTER', 'Nombre', 'Meta ($)', 'Recaudo ($)', 'Faltante ($)', 'Cumplimiento (%)']
    df_styled = df_styled[column_order]
    
    styled_df = df_styled.style.map(
        lambda x: style_function(x, expected_compliance),
        subset=['Cumplimiento (%)']
    ).format({
        'Meta ($)': '${:,.0f}', 'Recaudo ($)': '${:,.0f}', 'Faltante ($)': '${:,.0f}',
        'Cumplimiento (%)': '{:.2%}'
    }).hide(axis="index").set_table_attributes('width="100%"').set_table_styles([
        {'selector': 'th, td', 'props': [('padding', '4px 10px'), ('text-align', 'center')]}
    ])
    
    return styled_df.to_html()