import click
from pathlib import Path
import json

CONFIG_FILE = "config.json"

def configurar():
    """
    Recolhe as configurações do utilizador. Se existir config.json, lê de lá.
    Caso contrário, pergunta no terminal e guarda em JSON.
    """
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        pass  # ficheiro não existe, vamos perguntar

    click.echo("🔧 Configuração da análise GTFS\n")

    target_folder = click.prompt(
        "📂 Caminho para os ficheiros GTFS",
        type=click.Path(exists=True, file_okay=False, path_type=Path)
    )

    gtfs_offerplan_name = click.prompt(
        "📝 Nome do ficheiro GTFS Oferta",
        default="GTFS_44_REF_v29_202512181606"
    )

    gtfs_operationplan_name = click.prompt(
        "📝 Nome do ficheiro GTFS Operação",
        default="20251218_44_YEAR_04_27"
    )

    start_date = click.prompt("📅 Data de início (YYYYMMDD)", default="20251220")
    end_date = click.prompt("📅 Data de fim (YYYYMMDD)", default="20260115")

    result_name = click.prompt(
        "📝 Nome do ficheiro de resultado",
        default="A4_analise_plano_anual_dezembro_2026_testes"
    )

    export_stop_sequence_filename = click.prompt(
        "📝 Nome do ficheiro de exportação da sequência de paragens",
        default="Paragens_Sequência_A4"
    )

    export_total_circulations_vkm_filename = click.prompt(
        "📝 Nome do ficheiro de exportação do Total de Circulações e VKM",
        default="Total de Circulações e VKM"
    )

    config = {
        "TARGET_FOLDER": str(target_folder),
        "GTFS_OFFERPLAN_NAME": gtfs_offerplan_name,
        "GTFS_OPERATIONPLAN_NAME": gtfs_operationplan_name,
        "START_DATE": start_date,
        "END_DATE": end_date,
        "RESULT_NAME": result_name,
        "EXPORT_STOP_SEQUENCE_FILENAME": export_stop_sequence_filename,
        "EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME": export_total_circulations_vkm_filename,
    }

    # guardar config para reutilização
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    click.echo("\n✅ Configuração concluída! As configurações foram guardadas em config.json")
    return config
