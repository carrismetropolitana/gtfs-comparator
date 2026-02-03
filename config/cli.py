import click
from pathlib import Path
from datetime import datetime


def validar_data(value):
    """Valida se a data está no formato YYYYMMDD"""
    try:
        datetime.strptime(value, "%Y%m%d")
        return value
    except ValueError:
        raise click.BadParameter("Formato inválido! Use YYYYMMDD.")


def configurar():
    """Recolhe as configurações apenas para esta execução"""

    click.echo("🛠️ Configuração da análise\n")

    target_folder = click.prompt(
        "📂 Caminho para os ficheiros GTFS",
        type=click.Path(exists=True, file_okay=False, path_type=Path)
    )

    gtfs_offerplan_name = click.prompt("📝 Nome do ficheiro GTFS Oferta")
    gtfs_operationplan_name = click.prompt("📝 Nome do ficheiro GTFS Operação")

    while True:
        start_date = click.prompt("📅 Data de início (YYYYMMDD)")
        try:
            start_date = validar_data(start_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    while True:
        end_date = click.prompt("📅 Data de fim (YYYYMMDD)")
        try:
            end_date = validar_data(end_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    result_name = click.prompt("📝 Nome do ficheiro de resultado")

    # ✅ Perguntas de exportação
    export_result = click.confirm(
        "📤 Exportar ficheiro de resultado?", default=True
    )

    export_stop_sequence = click.confirm(
        "📤 Exportar sequência de paragens?", default=False
    )

    export_total_circulations = click.confirm(
        "📤 Exportar Total de Circulações e VKM?", default=False
    )

    export_stop_sequence_filename = None
    export_total_circulations_vkm_filename = None

    if export_stop_sequence:
        export_stop_sequence_filename = click.prompt(
            "📝 Nome do ficheiro da sequência de paragens"
        )

    if export_total_circulations:
        export_total_circulations_vkm_filename = click.prompt(
            "📝 Nome do ficheiro do Total de Circulações e VKM"
        )

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
