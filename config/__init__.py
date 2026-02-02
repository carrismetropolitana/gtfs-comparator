from .cli import configurar

# chama o CLI e guarda os valores
_config = configurar()

# Exporta variáveis individuais como no antigo settings.py
TARGET_FOLDER = _config["TARGET_FOLDER"]
GTFS_OFFERPLAN_NAME = _config["GTFS_OFFERPLAN_NAME"]
GTFS_OPERATIONPLAN_NAME = _config["GTFS_OPERATIONPLAN_NAME"]
START_DATE = _config["START_DATE"]
END_DATE = _config["END_DATE"]
RESULT_NAME = _config["RESULT_NAME"]

EXPORT_STOP_SEQUENCE_FILENAME = _config["EXPORT_STOP_SEQUENCE_FILENAME"]
EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME = _config["EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME"]

# from .cli import configurar

# # Chama o CLI e guarda os valores (force=False para usar config.json se existir)
# _config = configurar(force=False)

# # Variáveis individuais, igual ao antigo settings.py
# TARGET_FOLDER = _config["TARGET_FOLDER"]
# GTFS_OFFERPLAN_NAME = _config["GTFS_OFFERPLAN_NAME"]
# GTFS_OPERATIONPLAN_NAME = _config["GTFS_OPERATIONPLAN_NAME"]
# START_DATE = _config["START_DATE"]
# END_DATE = _config["END_DATE"]
# RESULT_NAME = _config["RESULT_NAME"]

# EXPORT_STOP_SEQUENCE_FILENAME = _config["EXPORT_STOP_SEQUENCE_FILENAME"]
# EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME = _config["EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME"]
