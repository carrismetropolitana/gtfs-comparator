# analysis/vkm.py

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def calculate_trip_distance_km(trips, shapes):
    """
    Calcula a distância real (km) de cada trip com base na shape.
    Assume shape_dist_traveled em metros ou km.
    """

    logger.info("📏 A calcular distância real das viagens")

    shape_dist = (shapes.groupby("shape_id", as_index=False)["shape_dist_traveled"].max())

    # Normalização para km
    shape_dist["distance_km"] = shape_dist["shape_dist_traveled"].apply(lambda x: x / 1000 if x > 1000 else x)

    return (trips.merge(shape_dist[["shape_id", "distance_km"]], on="shape_id", how="left") [["trip_id", "service_id", "pattern_id", "distance_km"]])


def calculate_service_days(calendar_dates, start_date, end_date):
    """
    Calcula o número de dias ativos de cada service_id e período.
    """

    logger.info("📅 A calcular dias ativos por serviço")

    df = calendar_dates.copy()
    df["date"] = pd.to_datetime(df["date"])

    mask = ((df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date)))

    return (df[mask].groupby("service_id", as_index=False)["date"].nunique().rename(columns={"date": "n_days"}))


def calculate_vkm(gtfs, start_date, end_date):
    """
    Calcula VKM por viagem:
    VKM = distância da viagem (km) × nº de dias ativos do serviço
    """

    logger.info("🧮 A calcular VKM")

    trips_dist = calculate_trip_distance_km(gtfs["trips"], gtfs["shapes"])

    service_days = calculate_service_days(gtfs["calendar_dates"], start_date, end_date)

    if trips_dist.empty or service_days.empty:
        logger.warning("⚠️ VKM não calculado: dados insuficientes")
        return pd.DataFrame(columns=["trip_id", "service_id", "vkm"])

    merged = trips_dist.merge(service_days, on="service_id", how="inner")

    merged["distance_km"] = pd.to_numeric(merged["distance_km"], errors="coerce").fillna(0)
    merged["n_days"] = pd.to_numeric(merged["n_days"], errors="coerce").fillna(0)

    merged["vkm"] = merged["distance_km"] * merged["n_days"]

    logger.info(f"✅ VKM calculado ({merged['vkm'].sum():,.0f} km)")

    return merged[["trip_id", "service_id", "pattern_id", "vkm"]]