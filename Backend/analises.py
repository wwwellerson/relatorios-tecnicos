# Arquivo: backend/analises.py (Versão Final com Lógica Completa)

import pandas as pd

MAPEAMENTO_COLUNAS = {
    'timestamp': 'Time', 'tensao_a': 'AVRMS', 'tensao_b': 'BVRMS', 'tensao_c': 'CVRMS',
    'corrente_a': 'AIRMS', 'corrente_b': 'BIRMS', 'corrente_c': 'CIRMS',
    'fp_a': 'AFP', 'fp_b': 'BFP', 'fp_c': 'CFP',
    'dia': 'DIA', 'mes': 'MES', 'nivel': 'NIVEL', 'total': 'TOTAL',
    'vazao': 'VAZAO', 'velocidade': 'VELOCIDADE'
}

def analisar_acessorios(df):
    textos = []
    colunas_totalizadores = {
        'dia': 'Vazão Diária (m³)', 'mes': 'Vazão Mensal (m³)',
        'vazao': 'Vazão Acumulada (m³)', 'total': 'Vazão Total da Safra (m³)'
    }
    for key, descricao in colunas_totalizadores.items():
        nome_coluna = MAPEAMENTO_COLUNAS.get(key)
        if nome_coluna and nome_coluna in df.columns:
            serie_com_valores = df[nome_coluna][df[nome_coluna] > 0]
            if not serie_com_valores.empty:
                ultimo_indice_valido = serie_com_valores.last_valid_index()
                if ultimo_indice_valido is not None:
                    valor = df.loc[ultimo_indice_valido, nome_coluna]
                    textos.append(f"- {descricao}: {valor:.2f}")
    if not textos: return ""
    return "Últimos Registros dos Totalizadores de Vazão:\n" + "\n".join(textos)

def analisar_corrente(df, corrente_nominal):
    if not isinstance(corrente_nominal, (int, float)) or corrente_nominal <= 0:
        return "Corrente nominal não fornecida ou inválida. A análise de corrente não pôde ser executada."
    cols_corrente_keys = ['corrente_a', 'corrente_b', 'corrente_c']
    cols_corrente = [MAPEAMENTO_COLUNAS.get(k) for k in cols_corrente_keys if MAPEAMENTO_COLUNAS.get(k) in df.columns]
    if len(cols_corrente) != 3: return "Para a análise de corrente, são necessárias as três colunas de fase (AIRMS, BIRMS, CIRMS)."
    df_op = df[(df[cols_corrente] > 1).any(axis=1)].copy()
    if df_op.empty: return "Não foram encontrados registros de operação do motor (corrente > 1A) para analisar."
    diagnosticos = []
    corrente_media_op = df_op[cols_corrente].mean().mean()
    if corrente_media_op > corrente_nominal: diagnosticos.append(f"- Sobrecarga: A corrente média em operação ({corrente_media_op:.1f} A) excedeu a corrente nominal ({corrente_nominal} A), indicando possível sobrecarga mecânica no eixo ou problemas no acionamento.")
    corrente_max_registrada = df_op[cols_corrente].max().max()
    if corrente_max_registrada > corrente_nominal * 4: diagnosticos.append(f"- Pico de Corrente Extremo: Foi registrado um pico de {corrente_max_registrada:.1f} A, valor que pode indicar um evento de rotor travado ou curto-circuito.")
    if corrente_media_op < (corrente_nominal * 0.4): diagnosticos.append(f"- Operação em Vazio: A corrente média em operação ({corrente_media_op:.1f} A) está abaixo de 40% da nominal, sugerindo que o motor pode operar longos períodos sem carga, o que é energeticamente ineficiente.")
    df_desequilibrio = df_op[cols_corrente].copy()
    limite_corrente_zero = corrente_nominal / 2
    df_desequilibrio[df_desequilibrio < limite_corrente_zero] = 0
    df_desequilibrio = df_desequilibrio[df_desequilibrio.sum(axis=1) > 0]
    if not df_desequilibrio.empty:
        df_desequilibrio['media'] = df_desequilibrio[cols_corrente].mean(axis=1)
        df_desequilibrio['desvio_max'] = df_desequilibrio[cols_corrente].subtract(df_desequilibrio['media'], axis=0).abs().max(axis=1)
        df_desequilibrio['desequilibrio_pct'] = (df_desequilibrio['desvio_max'] / df_desequilibrio['media'].replace(0, pd.NA) * 100)
        max_desequilibrio = df_desequilibrio['desequilibrio_pct'].max()
        if pd.notna(max_desequilibrio) and max_desequilibrio > 10: diagnosticos.append(f"- Desequilíbrio de Corrente: Foi detectado um desequilíbrio máximo de {max_desequilibrio:.1f}% entre as fases.")
    num_partidas = (df[cols_corrente[0]].gt(1) & df[cols_corrente[0]].shift(1).le(1)).sum()
    if num_partidas > 90: diagnosticos.append(f"- Ciclo de Operação Elevado: O motor teve {num_partidas} partidas durante o período, o que pode indicar mau dimensionamento ou falhas no sistema de controle.")
    df_op['fase_baixa'] = (df_op[cols_corrente] < 1).sum(axis=1)
    df_op['fase_normal'] = (df_op[cols_corrente] > corrente_nominal * 0.5).sum(axis=1)
    horas_fase_aberta = df_op[(df_op['fase_baixa'] >= 1) & (df_op['fase_normal'] == 2)].shape[0]
    if horas_fase_aberta > 0: diagnosticos.append(f"- Suspeita de Fase Aberta: Em {horas_fase_aberta} hora(s), uma das fases apresentou corrente próxima de zero enquanto as outras operavam normalmente, um forte indicativo de falha elétrica severa.")
    if not diagnosticos:
        return "A análise das correntes indicou uma operação CONFORME, sem anomalias significativas em relação à corrente nominal e aos padrões de falha monitorados."
    return "Foram detectados os seguintes pontos de atenção na análise das correntes:\n\n" + "\n\n".join(diagnosticos)

def analisar_fator_potencia(df):
    cols_fp_keys = ['fp_a', 'fp_b', 'fp_c']
    cols_fp = [MAPEAMENTO_COLUNAS.get(k) for k in cols_fp_keys if MAPEAMENTO_COLUNAS.get(k) in df.columns]
    col_corrente_ref = MAPEAMENTO_COLUNAS.get('corrente_a')
    if not cols_fp or not col_corrente_ref or col_corrente_ref not in df.columns: return "Dados de Fator de Potência ou Corrente insuficientes para uma análise completa."
    df_operacional = df[df[col_corrente_ref] > 1].copy()
    if df_operacional.empty: return "Não foram encontrados registros de operação do motor (corrente > 1A) para analisar o Fator de Potência."
    fp_filtrado = df_operacional[cols_fp].copy()
    fp_filtrado[fp_filtrado < 0.6] = pd.NA
    fp_medio = fp_filtrado.mean().mean()
    if pd.isna(fp_medio): return "Não foi possível calcular o Fator de Potência médio (valores de operação podem estar todos abaixo de 0.6)."
    texto_analise = f"O Fator de Potência médio registrado durante a operação (descartando valores < 0.6) foi de {fp_medio:.3f}.\n\n"
    if fp_medio < 0.91: texto_analise += "Diagnóstico: SITUAÇÃO CRÍTICA.\n\nAnálise:\nO fator de potência médio ficou abaixo de 0,91, indicando uma utilização ineficiente da energia elétrica.\n\nRecomendação:\nRecomenda-se avaliar a instalação de bancos de capacitores."
    elif 0.91 <= fp_medio < 0.95: texto_analise += "Diagnóstico: SITUAÇÃO DE ATENÇÃO.\n\nAnálise:\nO fator de potência médio ficou próximo do mínimo aceitável (0,92).\n\nRecomendação:\nÉ indicado analisar os períodos com FP mais baixo e considerar manutenções preventivas."
    else: texto_analise += "Diagnóstico: SITUAÇÃO IDEAL.\n\nAnálise:\nO fator de potência médio foi superior a 0,95, demonstrando excelente eficiência energética.\n\nRecomendação:\nSugere-se monitoramento contínuo, mas nenhuma ação corretiva é necessária."
    return texto_analise

def analisar_operacao(df, tensao_nominal):
    try:
        cols_tensao = [MAPEAMENTO_COLUNAS.get(k) for k in ['tensao_a', 'tensao_b', 'tensao_c'] if MAPEAMENTO_COLUNAS.get(k) in df.columns]
        cols_fp = [MAPEAMENTO_COLUNAS.get(k) for k in ['fp_a', 'fp_b', 'fp_c'] if MAPEAMENTO_COLUNAS.get(k) in df.columns]
        tempo_desligado_horas = int((df[cols_fp].mean(axis=1) < 0.3).sum()) if cols_fp and not df[cols_fp].empty else 0
        tempo_sem_energia_horas = int((df[cols_tensao] < 30).all(axis=1).sum()) if len(cols_tensao) == 3 else 0
        tempo_falta_fase_horas = 0
        if len(cols_tensao) == 3:
            limite_normal, limite_baixo = tensao_nominal * 0.80, tensao_nominal * 0.50
            df_operando = df[(df[cols_tensao] >= 30).any(axis=1)]
            if not df_operando.empty:
                condicao = df_operando.apply(lambda row: (row[cols_tensao] > limite_normal).sum() >= 2 and (row[cols_tensao] < limite_baixo).sum() >= 1, axis=1)
                tempo_falta_fase_horas = int(condicao.sum())
        return (f"- Tempo total com motor desligado (FP < 0.3): {tempo_desligado_horas} horas.\n\n"
                f"- Tempo total com falta de energia (Tensões < 30V): {tempo_sem_energia_horas} horas.\n\n"
                f"- Tempo total com suspeita de falta de fase: {tempo_falta_fase_horas} horas.")
    except Exception as e: return f"Ocorreu um erro ao processar os dados de operação: {e}"

def analisar_dados_prodist(df, corrente_nominal, tensao_nominal):
    comentarios = {'tensao_nominal': tensao_nominal}
    alertas_gerais = []
    try:
        cols_tensao_keys = ['tensao_a', 'tensao_b', 'tensao_c']
        cols_tensao = [MAPEAMENTO_COLUNAS.get(k) for k in cols_tensao_keys if MAPEAMENTO_COLUNAS.get(k) in df.columns]
        if len(cols_tensao) != 3: raise ValueError("Colunas de tensão (AVRMS, BVRMS, CVRMS) não encontradas no CSV.")
        if not isinstance(df.index, pd.DatetimeIndex): df.index = pd.to_datetime(df[MAPEAMENTO_COLUNAS['timestamp']], dayfirst=True, errors='coerce')
        limites = {'adequado_sup': tensao_nominal * 1.05, 'adequado_inf': tensao_nominal * 0.92, 'critico_sup': tensao_nominal * 1.06, 'critico_inf': tensao_nominal * 0.91, 'desequilibrio_max_pct': 3.0}
        comentarios_tensao = []
        df_tensao = df[cols_tensao]
        stats = df_tensao.agg(['min', 'max', 'mean'])
        min_geral, max_geral = stats.min().min(), stats.max().max()
        comentarios_tensao.append(f"Análise baseada em uma Tensão Nominal de referência de {tensao_nominal:.0f}V. Valores registrados: Mín. de {min_geral:.1f}V, Média de {stats.mean().mean():.1f}V e Máx. de {max_geral:.1f}V.")
        if max_geral > limites['critico_sup'] or min_geral < limites['critico_inf']:
            alerta = f"níveis de tensão CRÍTICOS foram atingidos (Pico de {max_geral:.1f}V)"
            comentarios_tensao.append(f"ALERTA: {alerta.capitalize()}. Violações desta natureza podem indicar problemas graves na rede.")
            alertas_gerais.append(alerta)
        comentarios['tensao'] = "\n\n".join(comentarios_tensao)
        comentarios['corrente'] = analisar_corrente(df, corrente_nominal)
        comentarios['fp'] = analisar_fator_potencia(df)
        comentarios['acessorios'] = analisar_acessorios(df)
        comentarios['dados_operacao'] = analisar_operacao(df, tensao_nominal)
        if not alertas_gerais:
            comentarios['conclusao_final'] = "Diagnóstico Geral: CONFORME.\nA análise dos dados indica que o sistema operou de forma estável e dentro dos parâmetros de qualidade de energia estabelecidos."
        else:
            texto_alertas = "- " + "\n- ".join(alertas_gerais)
            comentarios['conclusao_final'] = f"Diagnóstico Geral: NÃO CONFORME.\nO sistema apresentou instabilidades. Não conformidades principais:\n\n{texto_alertas}"
    except Exception as e:
        print(f"Erro na análise: {e}"); import traceback; traceback.print_exc()
        comentarios = {k: "Ocorreu um erro ao processar os dados." for k in ['tensao', 'corrente', 'fp', 'acessorios', 'conclusao_final', 'dados_operacao']}
        comentarios['tensao_nominal'] = tensao_nominal
    return comentarios