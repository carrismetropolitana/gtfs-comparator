"""
Este script orquestra toda a análise comparativa entre o Plano de Oferta e o Plano de Operação, desde a leitura GTFS até à exportação dos resultados.

Funcionalidades principais:
- Importa e aplica as configurações definidas (paths, nomes de ficheiros, período de análise e nomes de output).
- Lê os ficheiros GTFS de ambos os planos e filtra o calendário pelo intervalo de análise.
- Calcula o VKM contratual com base no ficheiro agency do plano de operação.
- Verifica e gera alertas para datas com exception_type = 2 nos calendários.
- Consolida e compara os calendários de oferta e operação, identificando divergências.
- Valida a sequência de paragens por pattern_id dentro de cada plano e entre planos.
- Identifica e alerta diferenças nas paragens (stop_name, stop_lat, stop_lon) entre os planos.
- Compara rotas entre os dois planos e regista inconsistências.
- Calcula e compara a extensão de shapes entre planos, com alertas associados.
- Calcula circulações por padrão, período e tipo de dia, e constrói resumos por plano.
- Constrói uma comparação global consolidada entre planos com o schema final de circulações e VKM.
- Calcula um resumo de contrato (VKM) comparando valores dos planos com o VKM contratado.
- Gera tabelas de análise (período de análise, circulações por dia e por hora).
- Exporta os resultados para um ficheiro Excel com múltiplos sheets.
- Exporta outputs extra em Excel: sequência de paragens e total de circulações/VKM.

Outputs:
- 1 ficheiro Excel consolidado com todos os resultados e comparações.
- 1 ficheiro Excel com a sequência de paragens do Plano de Oferta.
- 1 ficheiro Excel com o total de circulações e VKM (comparação global).
- 1 DataFrame de alertas com todas as inconformidades detetadas ao longo do processo.
"""


import os
import pandas as pd
import numpy as np

# ======================================================================================================================================================================
# 🔧 Configurações
# ======================================================================================================================================================================

from config.settings import (
    TARGET_FOLDER, START_DATE, END_DATE,
    GTFS_OFFERPLAN_NAME, GTFS_OPERATIONPLAN_NAME,
    RESULT_NAME
)

# ======================================================================================================================================================================
#📥 Leitura e processamento GTFS
# ======================================================================================================================================================================

from analysis.read_gtfs import read_gtfs, process_agency_file

# ======================================================================================================================================================================
# 🚨 Alertas
# ======================================================================================================================================================================

from analysis.alerts import init_alerts_df

# ======================================================================================================================================================================
# 🔍 Comparações
# ======================================================================================================================================================================

from analysis.check_calendar import (check_exception_type,compare_calendar_dates_consolidated)
from analysis.compare_extension import compare_extension, compare_extension_between_plans
from analysis.compare_routes import compare_routes
from analysis.compare_stop_sequences import (merge_and_check_stop_sequences, merge_and_check_stop_sequences_between_plans)
from analysis.compare_stops import compare_stops_between_plans
from analysis.compare_trips_per_date import trips_per_date
from analysis.circulation_time import compare_circulations_by_hour

# ======================================================================================================================================================================
# 📤 Exportação
# ======================================================================================================================================================================

from analysis.exports import save_to_excel,export_stop_sequence,export_total_circulacoes_vkm
from config.settings import EXPORT_STOP_SEQUENCE_FILENAME
from config.settings import EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME

# ======================================================================================================================================================================
# 🧾 Summaries
# ======================================================================================================================================================================

from analysis.summaries import (
    compute_trips_per_pattern_day_type_period,
    build_global_comparison,
    build_contract_summary,
    build_analysis_period_table,
    build_plan_summary
)

# ======================================================================================================================================================================
# 🔁 Padronização de GTFS
# ======================================================================================================================================================================

def format_plan_name_for_alert(plan_name: str) -> str:
    plan_name_lower = plan_name.lower()
    if "oferta" in plan_name_lower:
        return "Plano de Oferta"
    elif "operação" in plan_name_lower or "operacao" in plan_name_lower:
        return "Plano de Operação"
    return plan_name

# ======================================================================================================================================================================
# 1️⃣ Configuração Inicial
# ======================================================================================================================================================================

alerts_df = init_alerts_df()
excel_file_path = os.path.join(TARGET_FOLDER, f"{RESULT_NAME}.xlsx")

# ======================================================================================================================================================================
# 2️⃣ Leitura GTFS
# ======================================================================================================================================================================

gtfs_oferta = read_gtfs(os.path.join(TARGET_FOLDER, GTFS_OFFERPLAN_NAME), calendar_dates_start_date=START_DATE,calendar_dates_end_date=END_DATE)
gtfs_operacao = read_gtfs(os.path.join(TARGET_FOLDER, GTFS_OPERATIONPLAN_NAME), calendar_dates_start_date=START_DATE, calendar_dates_end_date=END_DATE)

# ======================================================================================================================================================================
# 3️⃣ VKM Contratados
# ======================================================================================================================================================================

vkm_contrato = process_agency_file(gtfs_operacao['agency'])

# ======================================================================================================================================================================
# 4️⃣ Verificação de exception_type
# ======================================================================================================================================================================

alerts_df = check_exception_type(gtfs_oferta['calendar_dates'], START_DATE, END_DATE, format_plan_name_for_alert('PLANO DE OFERTA'), alerts_df)
alerts_df = check_exception_type(gtfs_operacao['calendar_dates'], START_DATE, END_DATE, format_plan_name_for_alert('PLANO DE OPERAÇÃO'), alerts_df)

# ======================================================================================================================================================================
# 5️⃣ Calendários
# ======================================================================================================================================================================

calendar_oferta = gtfs_oferta['calendar_dates'].copy()
calendar_oferta['plan'] = 'Plano de Oferta'

calendar_operacao = gtfs_operacao['calendar_dates'].copy()
calendar_operacao['plan'] = 'Plano de Operação'

calendar_consolidated = pd.concat([calendar_oferta, calendar_operacao], ignore_index=True).rename(columns={'periodo_ano': 'period', 'dia_tipo': 'day_type'})

compare_calendars, alerts_df = compare_calendar_dates_consolidated(calendar_consolidated, alerts_df)

# ======================================================================================================================================================================
# 6️⃣ Sequência de paragens
# ======================================================================================================================================================================

stops_count_oferta, stop_sequence_oferta, alerts_df = merge_and_check_stop_sequences(gtfs_oferta['trips'], gtfs_oferta['stop_times'], format_plan_name_for_alert("PLANO DE OFERTA"), alerts_df)
stops_count_operacao, stop_sequence_operacao, alerts_df = merge_and_check_stop_sequences(gtfs_operacao['trips'], gtfs_operacao['stop_times'], format_plan_name_for_alert("PLANO DE OPERAÇÃO"), alerts_df)

alerts_df = merge_and_check_stop_sequences_between_plans(gtfs_oferta['trips'], gtfs_operacao['trips'], gtfs_oferta['stop_times'], gtfs_operacao['stop_times'], alerts_df)

# ======================================================================================================================================================================
# 8️⃣ Paragens (Identificação de diferenças do 'stops.txt')
# ======================================================================================================================================================================

stops_oferta = gtfs_oferta['stops'][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].copy()
stops_operacao = gtfs_operacao['stops'][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']].copy()

stops_comparison_detalhada, alerts_df = compare_stops_between_plans(stops_oferta, stops_operacao, alerts_df)

# ======================================================================================================================================================================
# 9️⃣ Rotas
# ======================================================================================================================================================================

merged_routes, alerts_df = compare_routes(gtfs_oferta['routes'], gtfs_operacao['routes'], alerts_df)

# ======================================================================================================
# 🔟 Extensão - Shapes
# ======================================================================================================

ext_shape_oferta, ext_stops_oferta, alerts_df = compare_extension(
    gtfs_oferta['trips'],
    gtfs_oferta['shapes'],
    gtfs_oferta['stop_times'],
    "POferta",
    alerts_df
)

ext_shape_operacao, ext_stops_operacao, alerts_df = compare_extension(
    gtfs_operacao['trips'],
    gtfs_operacao['shapes'],
    gtfs_operacao['stop_times'],
    "POperação",
    alerts_df
)

extension_comparison_df, alerts_df = compare_extension_between_plans(
    gtfs_oferta,
    gtfs_operacao,
    alerts_df
)

# ======================================================================================================================================================================
# 1️⃣1️⃣ Summaries
# ======================================================================================================================================================================

merged_trips_oferta = compute_trips_per_pattern_day_type_period(gtfs_oferta['trips'], gtfs_oferta['calendar_dates'])
merged_trips_operacao = compute_trips_per_pattern_day_type_period(gtfs_operacao['trips'], gtfs_operacao['calendar_dates'])

resumo_oferta = build_plan_summary(merged_trips_oferta, stops_count_oferta, ext_shape_oferta, "POferta")
resumo_operacao = build_plan_summary(merged_trips_operacao, stops_count_operacao, ext_shape_operacao, "POperação")

merged_all = build_global_comparison(resumo_oferta, resumo_operacao)

grand_total_df = build_contract_summary(
    gtfs_oferta,
    gtfs_operacao,
    START_DATE,
    END_DATE,
    vkm_contrato,
    GTFS_OFFERPLAN_NAME,
    GTFS_OPERATIONPLAN_NAME
)

analysis_period_df = build_analysis_period_table(START_DATE, END_DATE)

# ======================================================================================================================================================================
# 1️⃣2️⃣ Circulações por dia
# ======================================================================================================================================================================

pivot_dates_oferta, alerts_df = trips_per_date(gtfs_oferta['trips'], gtfs_oferta['calendar_dates'], START_DATE, END_DATE, alerts_df)
pivot_dates_operacao, alerts_df = trips_per_date(gtfs_operacao['trips'], gtfs_operacao['calendar_dates'], START_DATE, END_DATE, alerts_df)

# ======================================================================================================================================================================
# 1️⃣3️⃣ Circulações por hora
# ======================================================================================================================================================================

circulacoes_por_hora, alerts_df = compare_circulations_by_hour(
    os.path.join(TARGET_FOLDER, GTFS_OFFERPLAN_NAME),
    os.path.join(TARGET_FOLDER, GTFS_OPERATIONPLAN_NAME),
    alerts_df
)

# ======================================================================================================================================================================
# 1️⃣4️⃣ Exportação 
# ======================================================================================================================================================================

save_to_excel(
    excel_file_path,
    alerts_df,
    grand_total_df,
    analysis_period_df,
    merged_all,
    compare_calendars,
    stops_comparison_detalhada,
    extension_comparison_df,
    merged_routes,
    stop_sequence_oferta,
    stop_sequence_operacao,
    resumo_oferta,
    resumo_operacao,
    pivot_dates_oferta,
    pivot_dates_operacao,
    circulacoes_por_hora
)

print(f"✅ Análise concluída. Resultados guardados em {excel_file_path}")

# ======================================================================================================================================================================
# 1️⃣5️⃣ Output extra – Sequência de Paragens (Plano de Oferta)
# ======================================================================================================================================================================

export_path_seq = TARGET_FOLDER / f"{EXPORT_STOP_SEQUENCE_FILENAME}.xlsx"

export_stop_sequence(
    df_seq=stop_sequence_oferta,
    stops_df=gtfs_oferta['stops'],
    output_path=export_path_seq
)

print(f"📄 Sequência de paragens exportada: {export_path_seq}")


# ========================================================================================================================================================
# 1️⃣6️⃣ Output extra – Total Circulações e VKM
# ========================================================================================================================================================

export_path_total = TARGET_FOLDER / f"{EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME}.xlsx"

export_total_circulacoes_vkm(df=merged_all, output_excel_path=export_path_total)

print(f"📄 Total de Circulações e VKM exportados: {export_path_total}")
