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


# import os
# import pandas as pd
# import numpy as np
# import time

# # ======================================================================================================================================================================
# # 🔧 Configurações
# # ======================================================================================================================================================================

# from config.settings import (
#     TARGET_FOLDER, START_DATE, END_DATE,
#     GTFS_OFFERPLAN_NAME, GTFS_OPERATIONPLAN_NAME,
#     RESULT_NAME
# )

# # ======================================================================================================================================================================
# #📥 Leitura e processamento GTFS
# # ======================================================================================================================================================================

# from analysis.read_gtfs import read_gtfs, process_agency_file

# # ======================================================================================================================================================================
# # 🚨 Alertas
# # ======================================================================================================================================================================

# from analysis.alerts import init_alerts_df

# # ======================================================================================================================================================================
# # 🔍 Comparações
# # ======================================================================================================================================================================

# from analysis.check_calendar import (check_exception_type,compare_calendar_dates_consolidated)
# from analysis.compare_extension import compare_extension, compare_extension_between_plans
# from analysis.compare_routes import compare_routes
# from analysis.compare_stop_sequences import (merge_and_check_stop_sequences, merge_and_check_stop_sequences_between_plans)
# from analysis.compare_stops import compare_stops_between_plans
# from analysis.compare_trips_per_date import trips_per_date
# from analysis.circulation_time import compare_circulations_by_hour

# # ======================================================================================================================================================================
# # 📤 Exportação
# # ======================================================================================================================================================================

# from analysis.exports import save_to_excel,export_stop_sequence,export_total_circulacoes_vkm
# from config.settings import EXPORT_STOP_SEQUENCE_FILENAME
# from config.settings import EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME

# # ======================================================================================================================================================================
# # 🧾 Summaries
# # ======================================================================================================================================================================

# from analysis.summaries import (
#     compute_trips_per_pattern_day_type_period,
#     build_global_comparison,
#     build_contract_summary,
#     build_analysis_period_table,
#     build_plan_summary
# )

# # ======================================================================================================================================================================
# # 🔁 Padronização de GTFS
# # ======================================================================================================================================================================

# def format_plan_name_for_alert(plan_name: str) -> str:
#     plan_name_lower = plan_name.lower()
#     if "oferta" in plan_name_lower:
#         return "Plano de Oferta"
#     elif "operação" in plan_name_lower or "operacao" in plan_name_lower:
#         return "Plano de Operação"
#     return plan_name


# def log_step(step_name: str):
#     """Helper simples para printar o início de cada etapa."""
#     print("\n" + "=" * 120)
#     print(f"📌 {step_name}")
#     print("=" * 120)


# def main() -> None:

#     # ======================================================================================================================================================================
#     # 1️⃣ Configuração Inicial
#     # ======================================================================================================================================================================

#     log_step("1️⃣ Configuração Inicial")
#     alerts_df = init_alerts_df()
#     excel_file_path = os.path.join(TARGET_FOLDER, f"{RESULT_NAME}.xlsx")
#     print(f"✔️ Output principal: {excel_file_path}")

#     # ======================================================================================================================================================================
#     # 2️⃣ Leitura GTFS
#     # ======================================================================================================================================================================

#     log_step("2️⃣ Leitura GTFS")
#     start_time = time.time()

#     gtfs_paths = {
#         "oferta": os.path.join(TARGET_FOLDER, GTFS_OFFERPLAN_NAME),
#         "operacao": os.path.join(TARGET_FOLDER, GTFS_OPERATIONPLAN_NAME)
#     }

#     gtfs_oferta = read_gtfs(gtfs_paths["oferta"], calendar_dates_start_date=START_DATE, calendar_dates_end_date=END_DATE)
#     gtfs_operacao = read_gtfs(gtfs_paths["operacao"], calendar_dates_start_date=START_DATE, calendar_dates_end_date=END_DATE)

#     print(f"✔️ GTFS Oferta carregado: {len(gtfs_oferta['trips'])} trips, {len(gtfs_oferta['stops'])} stops")
#     print(f"✔️ GTFS Operação carregado: {len(gtfs_operacao['trips'])} trips, {len(gtfs_operacao['stops'])} stops")
#     print(f"⏱ Tempo leitura GTFS: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 3️⃣ VKM Contratados
#     # ======================================================================================================================================================================

#     log_step("3️⃣ VKM Contratados")
#     start_time = time.time()

#     vkm_contrato = process_agency_file(gtfs_operacao["agency"])
#     print(f"✔️ VKM contratual calculado: {vkm_contrato}")

#     print(f"⏱ Tempo VKM: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 4️⃣ Verificação de exception_type
#     # ======================================================================================================================================================================

#     log_step("4️⃣ Verificação de exception_type")
#     start_time = time.time()

#     alerts_df = check_exception_type(
#         gtfs_oferta["calendar_dates"], START_DATE, END_DATE,
#         format_plan_name_for_alert("PLANO DE OFERTA"),
#         alerts_df
#     )
#     alerts_df = check_exception_type(
#         gtfs_operacao["calendar_dates"], START_DATE, END_DATE,
#         format_plan_name_for_alert("PLANO DE OPERAÇÃO"),
#         alerts_df
#     )

#     print(f"✔️ Exception types verificados")
#     print(f"⏱ Tempo exception check: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 5️⃣ Calendários
#     # ======================================================================================================================================================================

#     log_step("5️⃣ Calendários")
#     start_time = time.time()

#     calendar_oferta = gtfs_oferta["calendar_dates"].copy()
#     calendar_oferta["plan"] = "Plano de Oferta"

#     calendar_operacao = gtfs_operacao["calendar_dates"].copy()
#     calendar_operacao["plan"] = "Plano de Operação"

#     calendar_consolidated = pd.concat(
#         [calendar_oferta, calendar_operacao],
#         ignore_index=True
#     ).rename(columns={"periodo_ano": "period", "dia_tipo": "day_type"})

#     compare_calendars, alerts_df = compare_calendar_dates_consolidated(calendar_consolidated, alerts_df)

#     print(f"✔️ Calendários comparados")
#     print(f"⏱ Tempo calendário: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 6️⃣ Sequência de paragens
#     # ======================================================================================================================================================================

#     log_step("6️⃣ Sequência de paragens")
#     start_time = time.time()

#     stops_count_oferta, stop_sequence_oferta, alerts_df = merge_and_check_stop_sequences(
#         gtfs_oferta["trips"], gtfs_oferta["stop_times"],
#         format_plan_name_for_alert("PLANO DE OFERTA"), alerts_df
#     )
#     stops_count_operacao, stop_sequence_operacao, alerts_df = merge_and_check_stop_sequences(
#         gtfs_operacao["trips"], gtfs_operacao["stop_times"],
#         format_plan_name_for_alert("PLANO DE OPERAÇÃO"), alerts_df
#     )

#     alerts_df = merge_and_check_stop_sequences_between_plans(
#         gtfs_oferta["trips"], gtfs_operacao["trips"],
#         gtfs_oferta["stop_times"], gtfs_operacao["stop_times"],
#         alerts_df
#     )

#     print(f"✔️ Sequência de paragens processada")
#     print(f"📍 Stops oferta: {stops_count_oferta} | Stops operação: {stops_count_operacao}")
#     print(f"⏱ Tempo stop sequence: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 8️⃣ Paragens (Identificação de diferenças do 'stops.txt')
#     # ======================================================================================================================================================================

#     log_step("8️⃣ Paragens (diferenças entre planos)")
#     start_time = time.time()

#     stops_oferta = gtfs_oferta["stops"][["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()
#     stops_operacao = gtfs_operacao["stops"][["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()

#     stops_comparison_detalhada, alerts_df = compare_stops_between_plans(stops_oferta, stops_operacao, alerts_df)

#     print(f"✔️ Comparação de paragens concluída")
#     print(f"⏱ Tempo stops comparison: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 9️⃣ Rotas
#     # ======================================================================================================================================================================

#     log_step("9️⃣ Rotas")
#     start_time = time.time()

#     merged_routes, alerts_df = compare_routes(gtfs_oferta["routes"], gtfs_operacao["routes"], alerts_df)

#     print(f"✔️ Rotas comparadas")
#     print(f"⏱ Tempo rotas: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 🔟 Extensão - Shapes   -------confirmar -------
#     # ======================================================================================================================================================================

#     log_step("🔟 Extensão - Shapes")
#     start_time = time.time()

#     extension_oferta, _, alerts_df = compare_extension(
#         gtfs_oferta["trips"], gtfs_oferta["shapes"], gtfs_oferta["stop_times"],
#         format_plan_name_for_alert("PLANO DE OFERTA"), alerts_df
#     )
#     extension_operacao, _, alerts_df = compare_extension(
#         gtfs_operacao["trips"], gtfs_operacao["shapes"], gtfs_operacao["stop_times"],
#         format_plan_name_for_alert("PLANO DE OPERAÇÃO"), alerts_df
#     )

#     extension_comparison_df, alerts_df = compare_extension_between_plans(gtfs_oferta, gtfs_operacao, alerts_df)

#     print(f"✔️ Extensões calculadas")
#     print(f"⏱ Tempo extension: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 1️⃣1️⃣ Summaries
#     # ======================================================================================================================================================================

#     log_step("1️⃣1️⃣ Summaries")
#     start_time = time.time()

#     merged_trips_oferta = compute_trips_per_pattern_day_type_period(gtfs_oferta["trips"], gtfs_oferta["calendar_dates"])
#     merged_trips_operacao = compute_trips_per_pattern_day_type_period(gtfs_operacao["trips"], gtfs_operacao["calendar_dates"])

#     resumo_oferta = build_plan_summary(merged_trips_oferta, stops_count_oferta, extension_oferta, "Plano de Oferta")
#     resumo_operacao = build_plan_summary(merged_trips_operacao, stops_count_operacao, extension_operacao, "Plano de Operação")

#     merged_all = build_global_comparison(resumo_oferta, resumo_operacao)

#     grand_total_df = build_contract_summary(
#         gtfs_POferta=gtfs_oferta,
#         gtfs_POperacao=gtfs_operacao,
#         start_date=START_DATE,
#         end_date=END_DATE,
#         vkm_contrato=vkm_contrato,
#         gtfs_offer_name=GTFS_OFFERPLAN_NAME,
#         gtfs_operation_name=GTFS_OPERATIONPLAN_NAME
#     )

#     analysis_period_df = build_analysis_period_table(START_DATE, END_DATE)

#     print(f"✔️ Summaries construídos")
#     print(f"⏱ Tempo summaries: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 1️⃣2️⃣ Circulações por dia
#     # ======================================================================================================================================================================

#     log_step("1️⃣2️⃣ Circulações por dia")
#     start_time = time.time()

#     pivot_dates_oferta, alerts_df = trips_per_date(
#         gtfs_oferta["trips"], gtfs_oferta["calendar_dates"], START_DATE, END_DATE, alerts_df
#     )
#     pivot_dates_operacao, alerts_df = trips_per_date(
#         gtfs_operacao["trips"], gtfs_operacao["calendar_dates"], START_DATE, END_DATE, alerts_df
#     )

#     print(f"✔️ Circulações por dia calculadas")
#     print(f"⏱ Tempo trips per date: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 1️⃣3️⃣ Circulações por hora
#     # ======================================================================================================================================================================

#     log_step("1️⃣3️⃣ Circulações por hora")
#     start_time = time.time()

#     circulacoes_por_hora, alerts_df = compare_circulations_by_hour(
#         gtfs_paths["oferta"],
#         gtfs_paths["operacao"],
#         alerts_df
#     )

#     print(f"✔️ Circulações por hora calculadas")
#     print(f"⏱ Tempo circulações por hora: {time.time() - start_time:.2f}s")

#     # ======================================================================================================================================================================
#     # 1️⃣4️⃣ Exportação 
#     # ======================================================================================================================================================================

#     log_step("1️⃣4️⃣ Exportação")
#     start_time = time.time()

#     save_to_excel(
#         excel_file_path,
#         alerts_df,
#         grand_total_df,
#         analysis_period_df,
#         merged_all,
#         compare_calendars,
#         stops_comparison_detalhada,
#         extension_comparison_df,
#         merged_routes,
#         stop_sequence_oferta,
#         stop_sequence_operacao,
#         resumo_oferta,
#         resumo_operacao,
#         pivot_dates_oferta,
#         pivot_dates_operacao,
#         circulacoes_por_hora
#     )

#     print(f"✔️ Excel principal exportado")
#     print(f"⏱ Tempo exportação principal: {time.time() - start_time:.2f}s")
#     print(f"✅ Análise concluída. Resultados guardados em {excel_file_path}")

#     # ======================================================================================================================================================================
#     # 1️⃣5️⃣ Output extra – Sequência de Paragens (Plano de Oferta)
#     # ======================================================================================================================================================================

#     log_step("1️⃣5️⃣ Output extra – Sequência de Paragens (Plano de Oferta)")
#     start_time = time.time()

#     PLANO_ANALISADO = "A1"

#     export_path_seq = os.path.join(
#         TARGET_FOLDER,
#         f"{EXPORT_STOP_SEQUENCE_FILENAME.format(plan=PLANO_ANALISADO)}.xlsx"
#     )

#     export_stop_sequence(
#         df_seq=stop_sequence_oferta,
#         stops_df=gtfs_oferta["stops"],
#         output_path=export_path_seq
#     )

#     print(f"✔️ Exportado: sequência de paragens")
#     print(f"⏱ Tempo exportação sequência: {time.time() - start_time:.2f}s")
#     print(f"📄 Sequência de paragens exportada: {export_path_seq}")


#     # ========================================================================================================================================================
#     # 1️⃣6️⃣ Output extra – Total Circulações e VKM
#     # ========================================================================================================================================================

#     log_step("1️⃣6️⃣ Output extra – Total Circulações e VKM")
#     start_time = time.time()

#     export_path_total = os.path.join(
#         TARGET_FOLDER,
#         f"{EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME.format(plan=PLANO_ANALISADO)}.xlsx"
#     )

#     export_total_circulacoes_vkm(
#         df=merged_all,
#         output_excel_path=export_path_total
#     )

#     print(f"✔️ Exportado: total circulações e VKM")
#     print(f"⏱ Tempo exportação total: {time.time() - start_time:.2f}s")
#     print(f"📄 Total de Circulações e VKM exportados: {export_path_total}")


# if __name__ == "__main__":
#     main()
