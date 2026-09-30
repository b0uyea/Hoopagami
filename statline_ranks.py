import pandas as pd
import math

CSV_PATH = "/Users/bouyea/Hoopagami/NBA_PlayerStatistics_Complete.csv"

df = pd.read_csv(CSV_PATH)

df = df[df["gameType"].astype(str) != "Excluded"].copy()

stats = ["points", "reboundsTotal", "assists", "steals", "blocks"]

df["gameDateTimeEst"] = pd.to_datetime(df["gameDateTimeEst"])

df["historical_untracked_defense"] = (
    df["gameDateTimeEst"] < pd.Timestamp("1973-10-01")
)

# Match Hoopagami's exact statline identity.
df["statline_key"] = (
    df["points"].astype(int).astype(str) + "/" +
    df["reboundsTotal"].astype(int).astype(str) + "/" +
    df["assists"].astype(int).astype(str) + "/" +
    df["steals"].astype(int).astype(str) + "/" +
    df["blocks"].astype(int).astype(str)
)

df.loc[
    df["historical_untracked_defense"],
    "statline_key"
] = (
    df.loc[df["historical_untracked_defense"], "points"].astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "reboundsTotal"].astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "assists"].astype(str) + "/-/-"
)

# Exact historical frequency.
statline_history_counts = (
    df.groupby("statline_key")
    .size()
    .rename("historical_occurrences")
)

df = df.join(statline_history_counts, on="statline_key")

# Magnitude
magnitude = (
    df["points"]
    + df["reboundsTotal"]
    + df["assists"]
    + df["steals"].where(~df["historical_untracked_defense"], 0)
    + df["blocks"].where(~df["historical_untracked_defense"], 0)
)

df["magnitude_percentile"] = magnitude / magnitude.max()

sqrt_magnitude = (
    df["points"].pow(0.5)
    + df["reboundsTotal"].pow(0.5)
    + df["assists"].pow(0.5)
    + df["steals"].pow(0.5)
    + df["blocks"].pow(0.5)
)

df["sqrt_magnitude_percentile"] = (
    sqrt_magnitude / sqrt_magnitude.max()
)

# Percentiles
for stat in ["points", "reboundsTotal", "assists"]:
    df[f"{stat}_percentile"] = df[stat].rank(pct=True)

tracked = ~df["historical_untracked_defense"]

df["steals_percentile"] = pd.NA
df["blocks_percentile"] = pd.NA

df.loc[tracked, "steals_percentile"] = (
    df.loc[tracked, "steals"].rank(pct=True)
)

df.loc[tracked, "blocks_percentile"] = (
    df.loc[tracked, "blocks"].rank(pct=True)
)

# Extremeness
for stat in ["points", "reboundsTotal", "assists"]:
    percentile = pd.to_numeric(
        df[f"{stat}_percentile"],
        errors="coerce"
    ).clip(upper=0.999999)

    df[f"{stat}_extremeness"] = (
        -pd.Series(
            1 - percentile,
            index=percentile.index
        ).apply(lambda x: math.log10(x))
    )

steals_percentile = pd.to_numeric(
    df.loc[tracked, "steals_percentile"],
    errors="coerce"
).clip(upper=0.999999)

df.loc[tracked, "steals_extremeness"] = (
    -pd.Series(
        1 - steals_percentile,
        index=steals_percentile.index
    ).apply(lambda x: math.log10(x))
)

blocks_percentile = pd.to_numeric(
    df.loc[tracked, "blocks_percentile"],
    errors="coerce"
).clip(upper=0.999999)

df.loc[tracked, "blocks_extremeness"] = (
    -pd.Series(
        1 - blocks_percentile,
        index=blocks_percentile.index
    ).apply(lambda x: math.log10(x))
)

# Extreme bonus
df["extreme_bonus"] = (
    (df["points"] / 100) ** 2
    + (df["reboundsTotal"] / 55) ** 2
    + (df["assists"] / 30) ** 2
    + (df["steals"] / 13) ** 2
    + (df["blocks"] / 17) ** 2
)

# Component rarity
df["component_rarity_score"] = (
    df["points_extremeness"]
    + df["reboundsTotal_extremeness"]
    + df["assists_extremeness"]
    + df["steals_extremeness"].fillna(0)
    + df["blocks_extremeness"].fillna(0)
    + df["extreme_bonus"] * 2
)

# Scoring bonus
df["scoring_bonus"] = (
    (df["points"] / 50) ** 2.15
)

# Final rarity score
df["final_rarity_score"] = (
    (df["sqrt_magnitude_percentile"] * 10)
    + df["component_rarity_score"]
    + df["scoring_bonus"]
)

# One row per distinct statline
ranked = (
    df.groupby("statline_key", as_index=False)
    .agg(
        historical_occurrences=("historical_occurrences", "first"),
        final_rarity_score=("final_rarity_score", "first")
    )
)

# Exact rarity first, then rarity score within each frequency group
ranked = ranked.sort_values(
    ["historical_occurrences", "final_rarity_score"],
    ascending=[True, False]
).reset_index(drop=True)

ranked["global_rarity_rank"] = ranked.index + 1

ranked.to_csv(
    "/Users/bouyea/Hoopagami/statline_ranks.csv",
    index=False
)

print(f"Distinct statlines ranked: {len(ranked):,}")
print("Saved to statline_ranks.csv")
