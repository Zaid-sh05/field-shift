import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


NASA_GRID_ELEVATION_M = 148.86
LAPSE_RATE_C_PER_KM = 6.5

FIELDS = {
    "maru_1": 530.2153449700978,
    "maru_2": 502.39055108798453,
    "maru_3": 499.2592188215408,
}


def number(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        result = float(value)
        if not math.isfinite(result) or result == -999:
            return None
        return result
    except (ValueError, TypeError):
        return None


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main():
    parser = argparse.ArgumentParser(
        description="Prepare corrected NASA POWER climate data for Field Shift."
    )
    parser.add_argument("--source-dir", required=True,
                        help="Folder containing the professor's NASA POWER CSV files.")
    args = parser.parse_args()

    source = Path(args.source_dir)
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / "data" / "climate_monthly.csv"

    daily_path = source / "01_climate_daily.csv"
    monthly_path = source / "02_climate_monthly.csv"

    if not daily_path.exists() or not monthly_path.exists():
        raise FileNotFoundError("Required daily or monthly NASA POWER CSV is missing.")

    daily_rows = read_csv(daily_path)
    monthly_rows = read_csv(monthly_path)

    # Calculate daily heat and frost counts after elevation correction.
    daily_counts = defaultdict(lambda: {
        "heat_days": 0,
        "frost_days": 0,
        "valid_max": 0,
        "valid_min": 0,
    })

    for row in daily_rows:
        month = row["date"][:7]
        tmax = number(row.get("T2M_MAX"))
        tmin = number(row.get("T2M_MIN"))

        for field_id, elevation in FIELDS.items():
            correction = (
                (elevation - NASA_GRID_ELEVATION_M)
                * LAPSE_RATE_C_PER_KM / 1000
            )
            key = (field_id, month)
            counts = daily_counts[key]

            if tmax is not None:
                counts["valid_max"] += 1
                if tmax - correction > 35:
                    counts["heat_days"] += 1

            if tmin is not None:
                counts["valid_min"] += 1
                if tmin - correction < 0:
                    counts["frost_days"] += 1

    # Build long-format climate records.
    records = []

    source_variables = {
        "T2M_mean": "tmean_c",
        "T2M_MIN_mean": "tmin_c",
        "T2M_MAX_mean": "tmax_c",
        "PRECTOTCORR_total_mm": "precip_mm",
        "RH2M_mean": "rh_pct",
        "WS2M_mean": "wind_m_s",
        "ALLSKY_SFC_SW_DWN_mean": "solar_mj_m2_day",
        "GWETROOT_mean": "gwetroot",
        "GWETTOP_mean": "gwettop",
        "longest_run_precip_lt_1mm_within_month_days": "dry_spell_days",
    }

    for row in monthly_rows:
        month = row["month"]

        for field_id, elevation in FIELDS.items():
            correction = (
                (elevation - NASA_GRID_ELEVATION_M)
                * LAPSE_RATE_C_PER_KM / 1000
            )

            for source_name, variable in source_variables.items():
                value = number(row.get(source_name))

                if value is not None and variable in {
                    "tmean_c", "tmin_c", "tmax_c"
                }:
                    value -= correction

                records.append({
                    "field_id": field_id,
                    "month": month,
                    "variable": variable,
                    "value": value,
                })

            counts = daily_counts[(field_id, month)]

            heat = (
                counts["heat_days"] if counts["valid_max"] > 0 else None
            )
            frost = (
                counts["frost_days"] if counts["valid_min"] > 0 else None
            )

            records.append({
                "field_id": field_id,
                "month": month,
                "variable": "heat_days",
                "value": heat,
            })
            records.append({
                "field_id": field_id,
                "month": month,
                "variable": "frost_days",
                "value": frost,
            })

    # Calculate z-score against the same calendar month across years.
    groups = defaultdict(list)
    for record in records:
        if record["value"] is not None:
            calendar_month = record["month"][5:7]
            key = (
                record["field_id"],
                record["variable"],
                calendar_month,
            )
            groups[key].append(record)

    for key, values in groups.items():
        numbers = [item["value"] for item in values]

        if len(numbers) < 3:
            for item in values:
                item["anomaly"] = None
            continue

        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        std = math.sqrt(variance)

       
        for item in values:
            item["anomaly"] = (
                (item["value"] - mean) / std if std > 0 else None
            )

    for record in records:
        record.setdefault("anomaly", None)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["field_id", "month", "variable", "value", "anomaly"],
        )
        writer.writeheader()

        for record in records:
            writer.writerow({
                "field_id": record["field_id"],
                "month": record["month"],
                "variable": record["variable"],
                "value": (
                    "" if record["value"] is None
                    else round(record["value"], 6)
                ),
                "anomaly": (
                    "" if record["anomaly"] is None
                    else round(record["anomaly"], 6)
                ),
            })

    print(f"Created: {output_path}")
    print(f"Fields: {len(FIELDS)}")
    print(f"Monthly source rows: {len(monthly_rows)}")
    print(f"Output rows: {len(records)}")
    print(f"Elevation correction rate: {LAPSE_RATE_C_PER_KM} C/km")


if __name__ == "__main__":
    main()
