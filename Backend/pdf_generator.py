# Arquivo: backend/pdf_generator.py (VERSÃO COMPLETA E FINAL)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from datetime import datetime
from pandas.tseries.offsets import DateOffset # Usando a biblioteca padrão do pandas
import io, os, sys, matplotlib.dates as mdates
from analises import analisar_dados_prodist, MAPEAMENTO_COLUNAS

def resource_path(relative_path):
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draw_header_footer = False
    def header(self):
        if not self.draw_header_footer: return
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, "Relatório de Acompanhamento Mensal", 0, 0, 'C')
        self.ln(20)
    def footer(self):
        if not self.draw_header_footer: return
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, 'C')
    def add_page(self, orientation="", *args, **kwargs):
        super().add_page(orientation, *args, **kwargs)
        self.draw_header_footer = True

def add_label_val(pdf, label, val):
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 8, label, 0, 0, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.write(8, str(val))
    pdf.ln(8)

def criar_grafico_em_memoria(data, y_cols_keys, title, ylabel, tensao_nominal=None):
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    if isinstance(y_cols_keys, str): y_cols_keys = [y_cols_keys]
    y_cols_reais = [MAPEAMENTO_COLUNAS.get(key) for key in y_cols_keys if MAPEAMENTO_COLUNAS.get(key) in data.columns]
    if not y_cols_reais or data[y_cols_reais].empty:
        plt.close(fig); return None
    data_to_plot = data.dropna(subset=y_cols_reais)
    if data_to_plot.empty:
        plt.close(fig); return None
    if len(data_to_plot) > 5000: data_to_plot = data_to_plot.resample('1H').mean().dropna()
    for col_real in y_cols_reais:
        sns.lineplot(data=data_to_plot, x=data_to_plot.index, y=col_real, label=col_real, ax=ax)
    ax.set_title(title, fontsize=14); ax.set_ylabel(ylabel); ax.set_xlabel("")
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    if tensao_nominal: ax.axhline(y=tensao_nominal, color='lime', linestyle='--', linewidth=1.2, label=f'Tensão Ideal ({tensao_nominal:.0f}V)')
    ax.legend(loc='upper left')
    plt.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=150); plt.close(fig); buf.seek(0)
    return buf

def gerar_relatorio_final(df_dados_brutos, dados_motor, checkboxes={}):
    try:
        corrente_nominal = float(dados_motor.get('corrente_nominal', 0))
        tensao_nominal = float(dados_motor.get('tensao_nominal_v', 380.0))
        
        coluna_tempo = MAPEAMENTO_COLUNAS.get('timestamp')
        if coluna_tempo in df_dados_brutos.columns:
            df_dados_brutos[coluna_tempo] = pd.to_datetime(df_dados_brutos[coluna_tempo], dayfirst=True, errors='coerce')
            df_dados_brutos.dropna(subset=[coluna_tempo], inplace=True)
            df_dados_brutos = df_dados_brutos.set_index(coluna_tempo).sort_index()
        
        comentarios = analisar_dados_prodist(df_dados_brutos, corrente_nominal, tensao_nominal)

        if isinstance(df_dados_brutos.index, pd.DatetimeIndex) and not df_dados_brutos.empty:
            data_final_real = df_dados_brutos.index.max()
            data_referencia = data_final_real - DateOffset(months=1)
            meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_referencia = f"{meses_pt[data_referencia.month - 1]} de {data_referencia.year}"
        else:
            mes_referencia = f"Dados de {datetime.now().strftime('%B de %Y')}"
        
        nome_cliente_safe = dados_motor.get('nome_cliente', 'Cliente').replace(' ', '_')
        descricao_motor_safe = dados_motor.get('descricao_motor', 'Motor').replace('/', '-').replace(' ', '_')
        mes_ref_safe = mes_referencia.replace(' de ', '_')
        nome_arquivo = f"Relatorio_{nome_cliente_safe}_{descricao_motor_safe}_{mes_ref_safe}.pdf"
        caminho_saida_pdf = os.path.join("reports_generated", nome_arquivo)
        os.makedirs("reports_generated", exist_ok=True)

        pdf = PDF(orientation='P', unit='mm', format='A4')
        
        # CAPA
        pdf.add_page(); pdf.draw_header_footer = False
        logo_jw_path = resource_path('Logo2.png'); logo_levantec_path = resource_path('Logo.png')
        if os.path.exists(logo_levantec_path): pdf.image(logo_levantec_path, x=155, y=20, h=25)
        if os.path.exists(logo_jw_path): pdf.image(logo_jw_path, x=145, y=50, h=12)
        pdf.set_xy(20, 25); pdf.set_font('Arial', 'B', 14); pdf.cell(100, 10, 'JW Automação', 0, 1, 'L')
        pdf.set_font('Arial', '', 12); pdf.set_x(20); pdf.cell(100, 10, 'Sistema Levantec', 0, 1, 'L')
        pdf.set_y(100); pdf.set_x(20); pdf.set_font('Arial', 'B', 36); pdf.cell(0, 15, 'Relatório Técnico', 0, 1, 'L')
        pdf.set_font('Arial', 'B', 30); pdf.set_x(20); pdf.cell(0, 15, 'Mensal', 0, 1, 'L')
        pdf.set_font('Arial', '', 12); pdf.set_x(20); pdf.cell(0, 10, f'Mês de referência: {mes_referencia}', 0, 1, 'L')
        pdf.set_y(220); pdf.set_x(20)
        add_label_val(pdf, 'Cliente:', dados_motor.get('nome_cliente', 'Não informado'))
        pdf.set_x(20); add_label_val(pdf, 'Instalação:', dados_motor.get('local_instalacao', 'Não informado'))
        pdf.set_x(20); add_label_val(pdf, 'Equipamento:', dados_motor.get('descricao_motor', 'Não informado'))
        pdf.set_y(244); pdf.set_font('Arial', '', 11); pdf.cell(0, 8, 'Alegrete - RS', 0, 1, 'R')
        pdf.set_y(252); pdf.cell(0, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')

        # SEÇÕES DO RELATÓRIO
        secao_num = 0
        def nova_secao(titulo):
            nonlocal secao_num
            secao_num += 1
            pdf.add_page(); pdf.set_font('Arial', 'B', 16); pdf.cell(0, 10, f"{secao_num}. {titulo}", 0, 1, 'L'); pdf.ln(5)

        nova_secao("Introdução")
        texto_intro = ("O presente relatório tem como objetivo apresentar uma análise técnica das principais grandezas elétricas envolvidas no funcionamento do sistema de automação de bombeamento. As informações aqui disponibilizadas foram coletadas por meio de sensores instalados no sistema, com registros realizados em intervalos regulares.\n\nO foco principal deste relatório é fornecer um diagnóstico objetivo sobre o comportamento do sistema, com ênfase na identificação de falhas operacionais, paradas inesperadas e variações anormais de desempenho, contribuindo para o aumento da confiabilidade do sistema.")
        pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, texto_intro, align='J')

        nova_secao("Análise das Tensões (PRODIST)")
        grafico = criar_grafico_em_memoria(df_dados_brutos, ['tensao_a', 'tensao_b', 'tensao_c'], "Tensões RMS por Fase", "Tensão (V)", tensao_nominal=tensao_nominal)
        if grafico: pdf.image(grafico, w=190); pdf.ln(5)
        pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, comentarios.get('tensao', ''), align='J')

        nova_secao("Análise das Correntes")
        grafico = criar_grafico_em_memoria(df_dados_brutos, ['corrente_a', 'corrente_b', 'corrente_c'], "Correntes RMS por Fase", "Corrente (A)")
        if grafico: pdf.image(grafico, w=190); pdf.ln(5)
        pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, comentarios.get('corrente', ''), align='J')

        nova_secao("Análise do Fator de Potência")
        grafico = criar_grafico_em_memoria(df_dados_brutos, ['fp_a', 'fp_b', 'fp_c'], "Fator de Potência por Fase", "FP")
        if grafico: pdf.image(grafico, w=190); pdf.ln(3)
        pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, comentarios.get('fp', ''), align='J')
        
        if checkboxes.get('tem_vazao') or checkboxes.get('tem_nivel'):
            nova_secao("Análise de Acessórios")
            if checkboxes.get('tem_vazao'):
                pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, comentarios.get('acessorios', ''), align='J'); pdf.ln(3)
                grafico = criar_grafico_em_memoria(df_dados_brutos, 'velocidade', 'Velocidade do Fluido', 'm/s')
                if grafico: pdf.image(grafico, w=190); pdf.ln(3)
            if checkboxes.get('tem_nivel'):
                grafico = criar_grafico_em_memoria(df_dados_brutos, 'nivel', 'Nível do Reservatório', 'Nível (%)')
                if grafico:
                    if checkboxes.get('tem_vazao') and pdf.get_y() > 150: pdf.add_page()
                    pdf.image(grafico, w=190); pdf.ln(3)

        nova_secao("Dados de Operação")
        pdf.set_font('Arial', '', 12); pdf.multi_cell(0, 7, comentarios.get('dados_operacao', ''), align='J')
        
        nova_secao("Conclusões Finais")
        pdf.set_font('Arial', 'B', 12); pdf.multi_cell(0, 7, comentarios.get('conclusao_final', ''), align='J')

        # Página de Agradecimento
        pdf.add_page(); pdf.draw_header_footer = False 
        pdf.set_y(120); pdf.set_font('Arial', 'B', 16); pdf.multi_cell(w=0, h=10, text='Agradecimento', align='C'); pdf.ln(10)
        texto_agradecimento = ("A JW Automação agradece a confiança em nossos serviços e no sistema Levantec. "
                               "Estamos comprometidos com a eficiência e produtividade da sua operação.\n\n"
                               "Para mais informações ou suporte técnico, não hesite em nos contatar.")
        pdf.set_font('Arial', '', 12); pdf.multi_cell(w=0, h=8, text=texto_agradecimento, align='C'); pdf.ln(5)
        pdf.set_font('Arial', 'I', 10); pdf.multi_cell(w=0, h=7, text="Contato: (55) 99710-4386 | gestao@jwautomacao.com.br", align='C')
        
        pdf.output(caminho_saida_pdf)
        return caminho_saida_pdf
        
    except Exception as e:
        print(f"ERRO CRÍTICO AO GERAR PDF: {e}")
        import traceback
        traceback.print_exc()
        raise e