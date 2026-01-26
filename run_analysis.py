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

# ======================================================================================================================================================================
# 🔟 Extensão - Shapes   -------confirmar -------
# ======================================================================================================================================================================

extension_oferta, _, alerts_df = compare_extension(gtfs_oferta['trips'], gtfs_oferta['shapes'], gtfs_oferta['stop_times'], format_plan_name_for_alert("PLANO DE OFERTA"), alerts_df)
extension_operacao, _, alerts_df = compare_extension(gtfs_operacao['trips'], gtfs_operacao['shapes'], gtfs_operacao['stop_times'], format_plan_name_for_alert("PLANO DE OPERAÇÃO"), alerts_df)

extension_comparison_df, alerts_df = compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df)

# ======================================================================================================================================================================
# 1️⃣1️⃣ 🔥 Circulações por hora do dia (pattern_id + hora início)
# ======================================================================================================================================================================

#circulacoes_por_hora, alerts_df = compare_circulations_by_hour(os.path.join(TARGET_FOLDER, GTFS_OFFERPLAN_NAME), os.path.join(TARGET_FOLDER, GTFS_OPERATIONPLAN_NAME), alerts_df)

# ======================================================================================================================================================================
# 1️⃣2️⃣ Summaries
# ======================================================================================================================================================================

merged_trips_oferta = compute_trips_per_pattern_day_type_period(gtfs_oferta['trips'], gtfs_oferta['calendar_dates'])
merged_trips_operacao = compute_trips_per_pattern_day_type_period(gtfs_operacao['trips'], gtfs_operacao['calendar_dates'])

resumo_oferta = build_plan_summary(merged_trips_oferta, stops_count_oferta, extension_oferta, "Plano de Oferta")
resumo_operacao = build_plan_summary(merged_trips_operacao, stops_count_operacao, extension_operacao, "Plano de Operação")

merged_all = build_global_comparison(resumo_oferta, resumo_operacao)

grand_total_df = build_contract_summary(
    gtfs_POferta = gtfs_oferta,
    gtfs_POperacao = gtfs_operacao,
    start_date = START_DATE,
    end_date = END_DATE,
    vkm_contrato = vkm_contrato,
    gtfs_offer_name = GTFS_OFFERPLAN_NAME,
    gtfs_operation_name = GTFS_OPERATIONPLAN_NAME
)

analysis_period_df = build_analysis_period_table(START_DATE, END_DATE)

# ======================================================================================================================================================================
# 1️⃣3️⃣ Circulações por dia
# ======================================================================================================================================================================

pivot_dates_oferta, alerts_df = trips_per_date(gtfs_oferta['trips'], gtfs_oferta['calendar_dates'], START_DATE, END_DATE, alerts_df)
pivot_dates_operacao, alerts_df = trips_per_date(gtfs_operacao['trips'], gtfs_operacao['calendar_dates'], START_DATE, END_DATE, alerts_df)

# ======================================================================================================================================================================
# 1️⃣4️⃣ Circulações por hora
# ======================================================================================================================================================================

circulacoes_por_hora, alerts_df = compare_circulations_by_hour(
    os.path.join(TARGET_FOLDER, GTFS_OFFERPLAN_NAME),
    os.path.join(TARGET_FOLDER, GTFS_OPERATIONPLAN_NAME),
    alerts_df
)

# ======================================================================================================================================================================
# 1️⃣5️⃣ Exportação 
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

# # ======================================================================================================================================================================
# # 1️⃣6️⃣ Output extra – Sequência de Paragens (Plano de Oferta)
# # ======================================================================================================================================================================

# # Definir identificador do plano (ex: A1, A2, etc.)
# PLANO_ANALISADO = "A1"   # 👈 podes tornar isto dinâmico depois

# export_filename = EXPORT_STOP_SEQUENCE_FILENAME.format(
#     plan=PLANO_ANALISADO
# )

# export_path = os.path.join(TARGET_FOLDER, f"{export_filename}.xlsx")

# # Adiciona stop_name à tabela existente
# stop_sequence_oferta_export = (stop_sequence_oferta.merge(gtfs_oferta['stops'][['stop_id', 'stop_name']], on='stop_id', how='left'))

# # Guardar o novo output
# with pd.ExcelWriter(export_path, engine="xlsxwriter") as writer: stop_sequence_oferta_export.to_excel(writer, sheet_name="Sequência Paragens", index=False)

# print(f"📄 Sequência de paragens exportada: {export_path}")

# # ========================================================================================================================================================
# # 1️⃣7️⃣ Output extra – Total Circulações e VKM
# # ========================================================================================================================================================

# PLANO_ANALISADO = "A1"

# export_filename = EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME.format(plan=PLANO_ANALISADO)

# export_path = os.path.join(TARGET_FOLDER, f"{export_filename}.xlsx")

# print(f"📄 Sequência de paragens exportada: {export_path}")

# # 👉 Exportar diretamente o DataFrame correto
# export_total_circulacoes_vkm(df=merged_all, output_excel_path=export_path)

# print(f"📄 Total de Circulações e VKM exportados: {export_path}")

# ======================================================================================================================================================================
# 1️⃣6️⃣ Output extra – Sequência de Paragens (Plano de Oferta)
# ======================================================================================================================================================================

PLANO_ANALISADO = "A1"

export_filename = EXPORT_STOP_SEQUENCE_FILENAME.format(plan=PLANO_ANALISADO)
export_path_seq = os.path.join(TARGET_FOLDER, f"{export_filename}.xlsx")

export_stop_sequence(
    df_seq=stop_sequence_oferta,
    stops_df=gtfs_oferta['stops'],
    output_path=export_path_seq
)

print(f"📄 Sequência de paragens exportada: {export_path_seq}")


# ========================================================================================================================================================
# 1️⃣7️⃣ Output extra – Total Circulações e VKM
# ========================================================================================================================================================

export_filename = EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME.format(plan=PLANO_ANALISADO)
export_path_total = os.path.join(TARGET_FOLDER, f"{export_filename}.xlsx")

export_total_circulacoes_vkm(
    df=merged_all,
    output_excel_path=export_path_total
)

print(f"📄 Total de Circulações e VKM exportados: {export_path_total}")




# ========================================================================================================================================================
# 2️⃣ Compara a sequênia de paragens entre planos
# ========================================================================================================================================================

    # -------------------------------------------------------------------------------------------
    # 📌 Para os patterns em comum verifica a sequências de paragens
    # -------------------------------------------------------------------------------------------