"""
Este módulo define a interface de linha de comandos para configurar a análise.
Recolhe interativamente os caminhos, ficheiros GTFS, intervalo temporal e opções de exportação, validando os dados introduzidos e devolvendo todas as configurações
num único dicionário para utilização durante a execução.

"""

import click
from pathlib import Path
from datetime import datetime
import pandas as pd

# ========================================================================================================================================================
# 1️⃣ Função para validar se a data está no formato YYYYMMDD
# ========================================================================================================================================================

def validar_data(value):
    """Valida se a data está no formato YYYYMMDD"""
    try:
        datetime.strptime(value, "%Y%m%d")
        return value
    except ValueError:
        raise click.BadParameter("🚨 Formato inválido! Use YYYYMMDD.")

# ========================================================================================================================================================
# 2️⃣ Constroi o nome do ficheiro resultado da comparação por default
# ========================================================================================================================================================

def build_default_result_name(gtfs_operationplan_name: str, start_date: str) -> str:
    """
    Constrói o nome por defeito do ficheiro de resultado do comparador de planos.
    Ex: A2_analise_plano_janeiro_2026
    """
    try:
        second_block = gtfs_operationplan_name.split("_")[1]
        contrato = second_block[1]
    except Exception:
        contrato = "X"

    start_date_dt = pd.to_datetime(start_date, format="%Y%m%d")
    meses = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    mes = meses[start_date_dt.month]
    ano = start_date_dt.year

    return f"A{contrato}_analise_plano_{mes}_{ano}"

# ========================================================================================================================================================
#3️⃣ Constroi o nome do ficheiro da sequencia de paragens por default
# ========================================================================================================================================================

def build_default_stop_sequence_name(gtfs_operationplan_name: str) -> str:
    """
    Constrói o nome default para a análise da sequência de paragens.
    """
    try:
        second_block = gtfs_operationplan_name.split("_")[1]
        contrato = second_block[1]
    except Exception:
        contrato = "X"

    return f"A{contrato}_Sequência_de_Paragens"


# ========================================================================================================================================================
#4️⃣ Constroi o nome do ficheiro do total de circulações e VKM por default
# ========================================================================================================================================================

def build_default_total_circulations_vkm_name(gtfs_operationplan_name: str) -> str:
    """
    Constrói o nome default para a análise do Total de Circulações e VKM.
    """
    try:
        second_block = gtfs_operationplan_name.split("_")[1]
        contrato = second_block[1]
    except Exception:
        contrato = "X"

    return f"A{contrato}_Total_de_Circulações_e_VKM"

# ========================================================================================================================================================
# 5️⃣ Define todas as configurações através de prompts interativos
# ========================================================================================================================================================

def configurar():
    """Recolhe as configurações apenas para esta execução"""

    click.echo("🛠️ Defina as configurações da sua análise\n")

    # -------------------------------------------------------------------------------------------
    # Pasta GTFS
    # -------------------------------------------------------------------------------------------

    target_folder = click.prompt(
        "📂 Adicione o caminho para a pasta onde tem os ficheiros GTFS guardados",
        type=click.Path(exists=True, file_okay=False, path_type=Path)
    )

    # -------------------------------------------------------------------------------------------
    # Identificação dos ficheiros GTFS
    # -------------------------------------------------------------------------------------------

    gtfs_offerplan_name = click.prompt("📝 Coloque o nome do ficheiro GTFS de Oferta")
    gtfs_operationplan_name = click.prompt("📝 Coloque o nome do ficheiro GTFS de Operação")

    # -------------------------------------------------------------------------------------------
    # Datas de análise
    # -------------------------------------------------------------------------------------------

    while True:
        start_date = click.prompt("📅 Adicione a data de início da sua analise no formato YYYYMMDD")
        try:
            start_date = validar_data(start_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    while True:
        end_date = click.prompt("📅 Adicione a data de fim da sua analise no formato YYYYMMDD")
        try:
            end_date = validar_data(end_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    # -------------------------------------------------------------------------------------------
    # Exportação - Comparador de Planos
    # -------------------------------------------------------------------------------------------

    export_result = click.confirm(
        "📤 Pretende exportar o ficheiro que resulta da comparação de planos?",
        default=True
    )

    default_result_name = build_default_result_name(gtfs_operationplan_name, start_date)
    click.echo(f"📝 Adicione o nome que pretende para guardar a comparação de planos: \033[3;90m{default_result_name}\033[0m", nl=False)
    result_name_input = input().strip()
    result_name = result_name_input if result_name_input else default_result_name

    # -------------------------------------------------------------------------------------------
    # Exportação - Sequência de paragens
    # -------------------------------------------------------------------------------------------

    export_stop_sequence = click.confirm(
        "📤 Pretende exportar o ficheiro resultado da análise da sequência de paragens?",
        default=False
    )

    export_stop_sequence_filename = None
    if export_stop_sequence:
        default_stop_sequence_name = build_default_stop_sequence_name(gtfs_operationplan_name)
        click.echo(f"📝 Adicione o nome que pretende para guardar o ficheiro da sequência de paragens: \033[3;90m{default_stop_sequence_name}\033[0m", nl=False)
        stop_sequence_input = input().strip()
        export_stop_sequence_filename = stop_sequence_input if stop_sequence_input else default_stop_sequence_name

    # -------------------------------------------------------------------------------------------
    # Exportação - Total de circulações e VKM
    # -------------------------------------------------------------------------------------------

    export_total_circulations = click.confirm(
        "📤 Pretende exportar o ficheiro resultado da análise do Total de Circulações e VKM?",
        default=False
    )

    export_total_circulations_vkm_filename = None
    if export_total_circulations:
        default_total_circulations_vkm_name = build_default_total_circulations_vkm_name(gtfs_operationplan_name)
        click.echo(f"📝 Adicione o nome que pretende para guardar o ficheiro do Total de Circulações e VKM: \033[3;90m{default_total_circulations_vkm_name}\033[0m", nl=False)
        total_circulations_input = input().strip()
        export_total_circulations_vkm_filename = total_circulations_input if total_circulations_input else default_total_circulations_vkm_name

    # -------------------------------------------------------------------------------------------
    # Output final
    # -------------------------------------------------------------------------------------------

    return {
        "TARGET_FOLDER": str(target_folder),
        "GTFS_OFFERPLAN_NAME": gtfs_offerplan_name,
        "GTFS_OPERATIONPLAN_NAME": gtfs_operationplan_name,
        "START_DATE": start_date,
        "END_DATE": end_date,
        "RESULT_NAME": result_name,
        "EXPORT_RESULT": export_result,
        "EXPORT_STOP_SEQUENCE": export_stop_sequence,
        "EXPORT_TOTAL_CIRCULATIONS_VKM": export_total_circulations,
        "EXPORT_STOP_SEQUENCE_FILENAME": export_stop_sequence_filename,
        "EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME": export_total_circulations_vkm_filename,
    }
