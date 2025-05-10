import pandas

# --- tune these once ---
BBOXES = {
    "I5_UW":   {"lat_min": 47.587, "lat_max": 47.675,
                "lon_min": -122.340, "lon_max": -122.300},
    "SR520":   {"lat_min": 47.635, "lat_max": 47.676,
                "lon_min": -122.320, "lon_max": -122.100},
}

def bbox_mask(df, box):
    return (
        (df["lat"].between(box["lat_min"], box["lat_max"])) &
        (df["lon"].between(box["lon_min"], box["lon_max"]))
    )

def slice_corridor(csv_in: str, csv_out: str):
    df = pandas.read_csv(csv_in)
    corridor_df = pandas.concat(
        [df[bbox_mask(df, box)] for box in BBOXES.values()]
    ).drop_duplicates(subset="station_id")
    corridor_df.to_csv(csv_out, index=False)
    print(f"✔  Saved {len(corridor_df)} detectors to {csv_out}")

# usage
slice_corridor("wsdot_raw.csv", "wsdot_corridor.csv")
