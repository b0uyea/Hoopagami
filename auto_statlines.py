import pandas as pd

file_path = "/Users/bouyea/Hoopagami/NBA_PlayerStatistics_Complete.csv"

print("Loading NBA data...")
df = pd.read_csv(file_path, low_memory=False)


stats = ["points", "reboundsTotal", "assists", "steals", "blocks"]

df["gameDateTimeEst"] = pd.to_datetime(df["gameDateTimeEst"])

# The NBA did not officially track steals and blocks before 1973-74.
# The dataset stores those unavailable values as 0, so remember which
# games are from before official steals/blocks tracking began.
df["historical_untracked_defense"] = (
    df["gameDateTimeEst"] < pd.Timestamp("1973-10-01")
)

df[stats] = df[stats].astype(int)
df["statline_key"] = (
    df["points"].astype(str) + "/" +
    df["reboundsTotal"].astype(str) + "/" +
    df["assists"].astype(str) + "/" +
    df["steals"].astype(str) + "/" +
    df["blocks"].astype(str)
)

df.loc[
    df["historical_untracked_defense"],
    "statline_key"
] = (
    df.loc[df["historical_untracked_defense"], "points"].astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "reboundsTotal"].astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "assists"].astype(str) + "/-/-"
)
def format_statline(row):
    if row["historical_untracked_defense"]:
        return (
            f"{int(row['points'])}/"
            f"{int(row['reboundsTotal'])}/"
            f"{int(row['assists'])}/-/-"
        )

    return (
        f"{int(row['points'])}/"
        f"{int(row['reboundsTotal'])}/"
        f"{int(row['assists'])}/"
        f"{int(row['steals'])}/"
        f"{int(row['blocks'])}"
    )

def format_game_context(game):
    if str(game["gameType"]).lower() != "playoffs":
        return "Regular Season"

    label = str(game["gameLabel"])

    playoff_labels = {
        "NBA Finals": "NBA Finals",
        "East - Conf. Finals": "Eastern Conference Finals",
        "East Conf. Finals": "Eastern Conference Finals",
        "West - Conf. Finals": "Western Conference Finals",
        "West Conf. Finals": "Western Conference Finals",
        "East - Conf. Semifinals": "Eastern Conference Semifinals",
        "East Conf. Semifinals": "Eastern Conference Semifinals",
        "West - Conf. Semifinals": "Western Conference Semifinals",
        "West Conf. Semifinals": "Western Conference Semifinals",
        "East - First Round": "Eastern Conference First Round",
        "East First Round": "Eastern Conference First Round",
        "West - First Round": "Western Conference First Round",
        "West First Round": "Western Conference First Round",
    }

    label = playoff_labels.get(label, label)

    game_number = game["seriesGameNumber"]

    if pd.notna(game_number):
        game_number = str(game_number).strip()

        if game_number.lower().startswith("game "):
            return f"{label} — {game_number}"

        try:
            return f"{label} — Game {int(float(game_number))}"
        except (ValueError, TypeError):
            return f"{label} — {game_number}"

    return label
    return (
        f"{int(row['points'])}/"
        f"{int(row['reboundsTotal'])}/"
        f"{int(row['assists'])}/"
        f"{int(row['steals'])}/"
        f"{int(row['blocks'])}"
    )
# Keep only games that belong in our NBA statline database
df = df[
    df["gameType"].isin([
        "Regular Season",
        "Playoffs",
        "NBA Emirates Cup",
        "Emirates NBA Cup",
        "NBA Cup"
    ])
].copy()

# Remove the NBA Cup Championship because it does not count
# toward regular-season statistics.
cup_championship = (
    df["gameType"].isin([
        "NBA Emirates Cup",
        "Emirates NBA Cup",
        "NBA Cup"
    ])
    & df["gameLabel"].astype(str).str.contains(
        "Championship", case=False, na=False
    )
)

df = df[~cup_championship].copy()

all_df = df.copy()

all_df["gameDateTimeEst"] = pd.to_datetime(all_df["gameDateTimeEst"])

def get_season(date):
    if date.month >= 10:
        return f"{date.year}-{str(date.year + 1)[-2:]}"
    else:
        return f"{date.year - 1}-{str(date.year)[-2:]}"

all_df["season"] = all_df["gameDateTimeEst"].apply(get_season)

# Calculate how unusual each individual stat value is.
# Higher percentile = more statistically unusual.
#
# We later transform the percentile into an extremeness score,
# so performances near the historical maximum receive
# disproportionately more weight.

for stat in ["points", "reboundsTotal", "assists"]:
    all_df[f"{stat}_percentile"] = all_df[stat].rank(pct=True)

tracked_defense = ~all_df["historical_untracked_defense"]

all_df["steals_percentile"] = pd.NA
all_df["blocks_percentile"] = pd.NA

all_df.loc[tracked_defense, "steals_percentile"] = (
    all_df.loc[tracked_defense, "steals"].rank(pct=True)
)

all_df.loc[tracked_defense, "blocks_percentile"] = (
    all_df.loc[tracked_defense, "blocks"].rank(pct=True)
)

# Convert percentiles into extremeness scores.
# The closer a percentile is to 100%, the faster the score rises.

for stat in ["points", "reboundsTotal", "assists"]:
    percentile = pd.to_numeric(
        all_df[f"{stat}_percentile"],
        errors="coerce"
    ).clip(upper=0.999999)

    all_df[f"{stat}_extremeness"] = (
    -pd.Series(1 - percentile, index=percentile.index).apply(
        lambda x: __import__("math").log10(x)
    )
)

all_df["steals_extremeness"] = pd.NA
all_df["blocks_extremeness"] = pd.NA

steals_percentile = pd.to_numeric(
    all_df.loc[tracked_defense, "steals_percentile"],
    errors="coerce"
).clip(upper=0.999999)

blocks_percentile = pd.to_numeric(
    all_df.loc[tracked_defense, "blocks_percentile"],
    errors="coerce"
).clip(upper=0.999999)

all_df.loc[tracked_defense, "steals_extremeness"] = (
    -pd.Series(
        1 - steals_percentile,
        index=steals_percentile.index
    ).apply(lambda x: __import__("math").log10(x))
)

all_df.loc[tracked_defense, "blocks_extremeness"] = (
    -pd.Series(
        1 - blocks_percentile,
        index=blocks_percentile.index
    ).apply(lambda x: __import__("math").log10(x))
)

# Steals and blocks were not officially tracked before 1973-74.
# Do not use those historical zeroes when calculating defensive rarity.

tracked_defense = ~all_df["historical_untracked_defense"]

all_df["steals_percentile"] = pd.NA
all_df["blocks_percentile"] = pd.NA

all_df.loc[tracked_defense, "steals_percentile"] = (
    all_df.loc[tracked_defense, "steals"].rank(pct=True)
)

all_df.loc[tracked_defense, "blocks_percentile"] = (
    all_df.loc[tracked_defense, "blocks"].rank(pct=True)
)
# Calculate overall statistical magnitude.
# Historical unavailable steals and blocks contribute 0.

all_df["magnitude_score"] = (
    all_df["points"] +
    all_df["reboundsTotal"] +
    all_df["assists"] +
    all_df["steals"].where(
        ~all_df["historical_untracked_defense"], 0
    ) +
    all_df["blocks"].where(
        ~all_df["historical_untracked_defense"], 0
    )
)
# Combine the individual stat percentiles into an overall
# statistical unusualness score.

all_df["extreme_bonus"] = (
    (all_df["points"] / 100) ** 2 +
    (all_df["reboundsTotal"] / 55) ** 2 +
    (all_df["assists"] / 30) ** 2 +
    (all_df["steals"] / 13) ** 2 +
    (all_df["blocks"] / 17) ** 2
)

all_df["scoring_bonus"] = (
    all_df["points"] / 50
) ** 2.15

all_df["magnitude_percentile"] = (
    all_df["magnitude_score"] / all_df["magnitude_score"].max()
)
sqrt_magnitude = (
    all_df["points"].pow(0.5) +
    all_df["reboundsTotal"].pow(0.5) +
    all_df["assists"].pow(0.5) +
    all_df["steals"].pow(0.5) +
    all_df["blocks"].pow(0.5)
)

all_df["sqrt_magnitude_percentile"] = (
    sqrt_magnitude / sqrt_magnitude.max()
)

all_df["component_rarity_score"] = (
    all_df["points_extremeness"] +
    all_df["reboundsTotal_extremeness"] +
    all_df["assists_extremeness"] +
    all_df["steals_extremeness"].fillna(0) +
    all_df["blocks_extremeness"].fillna(0) +
    all_df["extreme_bonus"] * 2
)
all_df["final_rarity_score"] = (
  (all_df["sqrt_magnitude_percentile"] * 10) +
    all_df["component_rarity_score"] +
    all_df["scoring_bonus"]
)

# Count how many times each exact statline has occurred
# throughout NBA history.

statline_history_counts = (
    all_df.groupby("statline_key")
    .size()
    .rename("historical_occurrences")
)

total_unique_statlines = all_df["statline_key"].nunique()

all_df = all_df.join(
    statline_history_counts,
    on="statline_key"
)

statline_ranks = (
    all_df[
        [
            "statline_key",
            "historical_occurrences",
            "final_rarity_score"
        ]
    ]
    .drop_duplicates("statline_key")
    .sort_values(
        [
            "historical_occurrences",
            "final_rarity_score"
        ],
        ascending=[
            True,
            False
        ]
    )
    .reset_index(drop=True)
)

statline_ranks["overall_rarity_rank"] = (
    statline_ranks.index + 1
)

all_df = all_df.drop(
    columns=["overall_rarity_rank"],
    errors="ignore"
)

all_df = all_df.merge(
    statline_ranks[
        ["statline_key", "overall_rarity_rank"]
    ],
    on="statline_key",
    how="left"
)

# Convert exact-statline frequency into a rarity score.
# Fewer historical occurrences = higher rarity.

all_df["exact_rarity_score"] = (
    1 / all_df["historical_occurrences"]
)

# Calculate overall statistical magnitude.
# Historical unavailable steals and blocks contribute 0.

all_df["magnitude_score"] = (
    all_df["points"] +
    all_df["reboundsTotal"] +
    all_df["assists"] +
    all_df["steals"].where(
        ~all_df["historical_untracked_defense"], 0
    ) +
    all_df["blocks"].where(
        ~all_df["historical_untracked_defense"], 0
    )
)
all_df["magnitude_percentile"] = (
    all_df["magnitude_score"].rank(pct=True)
)

current_game_type = "All Games"
current_start_date = "All Dates"
current_end_date = "All Dates"
while True:
    print(
        f"\nActive Filters: {current_game_type} | "
        f"{current_start_date} to {current_end_date}"
    )
    print("\n===== HOOPAGAMI =====")
    print(f"Total Distinct NBA Statlines: {total_unique_statlines:,}")

    unique_history = all_df[
        all_df["historical_occurrences"] == 1
    ]

    print(f"Unique Statlines: {len(unique_history):,}")

    regular_unique_count = unique_history.loc[
        unique_history["gameType"].str.lower() == "regular season",
        "statline_key"
    ].nunique()

    playoff_unique_count = unique_history.loc[
        unique_history["gameType"].str.lower() == "playoffs",
        "statline_key"
    ].nunique()

    cup_unique_count = unique_history.loc[
        unique_history["gameType"].isin(
            ["NBA Cup", "NBA Emirates Cup", "Emirates NBA Cup"]
        ),
        "statline_key"
    ].nunique()

    print(
        f"Regular Season Unique: {regular_unique_count:,} | "
        f"Playoffs Unique: {playoff_unique_count:,} | "
        f"NBA Cup Unique: {cup_unique_count:,}"
    )

    print()
    print("1. Search statline")
    print("2. Find rarest statlines")
    print("3. Find most common statlines")
    print("4. Search player")
    print("5. Set filters")
    print("6. Test rarity analysis")
    print("7. Exit")

    choice = input("\nChoose an option: ")

    if choice == "1":
        statline = input(
            "Enter statline (PTS-REB-AST-STL-BLK): "
        )

        parts = statline.split("-")

        if len(parts) != 5:
            print("Invalid statline format.")
            continue

        points = parts[0]
        rebounds = parts[1]
        assists = parts[2]
        steals = parts[3]
        blocks = parts[4]

        if not points.isdigit() or not rebounds.isdigit() or not assists.isdigit():
            print("Invalid statline format.")
            continue

        if steals == "" and blocks == "":
            search_key = (
                f"{int(points)}/"
                f"{int(rebounds)}/"
                f"{int(assists)}/-/-"
            )

        elif steals.isdigit() and blocks.isdigit():
            search_key = (
                f"{int(points)}/"
                f"{int(rebounds)}/"
                f"{int(assists)}/"
                f"{int(steals)}/"
                f"{int(blocks)}"
            )

        else:
            print("Invalid statline format.")
            continue

        matches = df[
            df["statline_key"] == search_key
        ]

        print("\n===== STATLINE SEARCH =====")
        print(f"Statline: {search_key}")

        if len(matches) == 0:
            historical_matches = all_df[
                all_df["statline_key"] == search_key
            ]

            if len(historical_matches) == 0:
                print("\nThis statline has never occurred in the database.")
            else:
                print(
                    "\nThis statline has occurred in NBA history, "
                    "but not within the current filters."
                )

            continue

        total_occurrences = len(matches)
        status = "UNIQUE" if total_occurrences == 1 else "REPEATED"

        print(f"Occurrences: {total_occurrences}")
        print(f"Status: {status}")

        if search_key in all_df["statline_key"].values:
            rank = all_df.loc[
                all_df["statline_key"] == search_key,
                "overall_rarity_rank"
            ].iloc[0]

            print(f"Overall Rarity Rank: #{int(rank)}")

        print("\n===== OCCURRENCES =====")

        for _, game in matches.sort_values(
            "gameDateTimeEst"
        ).iterrows():

            date = game["gameDateTimeEst"].strftime("%b %d, %Y")

            print(
                f"\n{game['firstName']} {game['lastName']} | {date}"
            )

            print(
                f"   Opponent: "
                f"{game['opponentteamCity']} "
                f"{game['opponentteamName']}"
            )

            print(
                f"   Game Type: "
                f"{format_game_context(game)}"
            )

    elif choice == "2":
        counts = df.groupby("statline_key").size().reset_index(name="occurrences")

        limit = int(input("How many results? (20, 50, 100, 500, or 1000): "))

        print(
            f"\nFilters: {current_game_type} | "
            f"{current_start_date} to {current_end_date}"
        )

        total_counts = all_df.groupby("statline_key").size().reset_index(
    name="total_occurrences"
        )
        overall_ranks = (
            all_df[["statline_key", "overall_rarity_rank"]]
            .drop_duplicates("statline_key")
        )
        rare = counts.merge(total_counts, on="statline_key")
        rare = rare.merge(
            overall_ranks,
            on="statline_key"
        )
        rare = rare.merge(
            all_df[
                ["statline_key", "final_rarity_score"]
            ].drop_duplicates("statline_key"),
            on="statline_key"
        )
        rare = rare.sort_values(
            "overall_rarity_rank",
            ascending=True
        ).head(limit)

        print("\n===== RAREST STATLINES =====")

        for rank, (_, row) in enumerate(rare.iterrows(), start=1):

            matches = df[
                df["statline_key"] == row["statline_key"]
            ]

            for _, game in matches.iterrows():

                date = game["gameDateTimeEst"].strftime("%b %d, %Y")

                print(
                   f"\nOverall Rarity Rank: #{int(row['overall_rarity_rank'])}  "
                    f"{format_statline(game)}"
                )

                print(
                    f"    Filtered Occurrences: {int(row['occurrences'])} | "
                    f"NBA History: {int(row['total_occurrences'])}"
                )

                print(
                    f"    {game['firstName']} {game['lastName']} | {date}"
                )

                print(
                    f"    Opponent: "
                    f"{game['opponentteamCity']} "
                    f"{game['opponentteamName']}"
                )

                print(
                    f"    Game Type: "
                    f"{format_game_context(game)}"
                )
    elif choice == "3":
        counts = df.groupby("statline_key").size().reset_index(
            name="occurrences"
        )

        limit = int(input("How many results? (20, 50, or 100): "))

        print(
            f"\nFilters: {current_game_type} | "
            f"{current_start_date} to {current_end_date}"
        )

        common = counts.sort_values(
            "occurrences",
            ascending=False
        ).head(limit)

        print("\n===== MOST COMMON STATLINES =====")

        for _, row in common.iterrows():

            matches = df[
                df["statline_key"] == row["statline_key"]
            ]

            if len(matches) > 0:

                game = matches.iloc[0]

                print(
                    f"{format_statline(game)} | "
                    f"Occurrences: {int(row['occurrences'])}"
                )
    elif choice == "4":
        player = input("Enter player name: ").strip().lower()

        matches = df[
            (df["firstName"].str.lower() + " " +
             df["lastName"].str.lower()).str.contains(
                player, na=False
            )
        ]

        if len(matches) == 0:
            print("\nNo player found.")
            continue

        player_name = (
            matches.iloc[0]["firstName"] + " " +
            matches.iloc[0]["lastName"]
        )

        unique_statline_keys = set(
            all_df.loc[
                all_df["historical_occurrences"] == 1,
                "statline_key"
            ]
        )

        unique_statlines = matches[
            matches["statline_key"].isin(unique_statline_keys)
        ].copy()

        print(f"\n===== {player_name.upper()} =====")
        print(f"Games Played: {len(matches):,}")
        print(f"Unique Statline Games: {len(unique_statlines):,}")

        regular_unique = unique_statlines[
            unique_statlines["gameType"].str.lower() == "regular season"
        ]

        playoff_unique = unique_statlines[
            unique_statlines["gameType"].str.lower() == "playoffs"
        ]

        print(
            f"Regular Season Unique: {len(regular_unique):,} | "
            f"Playoff Unique: {len(playoff_unique):,}"
        )

        if len(unique_statlines) == 0:
            print("\nNo unique statlines found.")
            continue

        unique_statlines = unique_statlines.sort_values(
            "overall_rarity_rank",
            ascending=True
        )

        print("\n===== UNIQUE STATLINES =====")

        for rank, (_, game) in enumerate(
            unique_statlines.iterrows(),
            start=1
        ):
            print(
                f"\n{rank}. {format_statline(game)}"
            )
            print(
                f"   Date: "
                f"{game['gameDateTimeEst'].strftime('%b %d, %Y')}"
            )
            print(
                f"   Opponent: "
                f"{game['opponentteamCity']} "
                f"{game['opponentteamName']}"
            )
            print(
                f"   Game Type: "
                f"{format_game_context(game)}"
            )
            print(
                f"   Overall Rarity Rank: "
                f"#{game['overall_rarity_rank']}"
            )

    elif choice == "5":
        print("\n===== SET FILTERS =====")
        print("1. Regular Season")
        print("2. Playoffs")
        print("3. Regular Season + Playoffs")

        game_choice = input("Choose game type (1-3): ")

        if game_choice == "1":
            current_game_type = "Regular Season"
        elif game_choice == "2":
            current_game_type = "Playoffs"
        elif game_choice == "3":
            current_game_type = "Regular Season + Playoffs"
        else:
            print("Invalid choice.")
            continue

        print("\n===== SELECT SEASON =====")

        seasons = sorted(all_df["season"].dropna().unique(), reverse=True)

        for i, season in enumerate(seasons, start=1):
            season_games = all_df[all_df["season"] == season]

            if game_choice == "1":
                season_games = season_games[
                    season_games["gameType"].isin([
                        "Regular Season",
                        "NBA Emirates Cup",
                        "Emirates NBA Cup"
                    ])
                ]

            elif game_choice == "2":
                season_games = season_games[
                    season_games["gameType"] == "Playoffs"
                ]

            elif game_choice == "3":
                season_games = season_games[
                    season_games["gameType"].isin([
                        "Regular Season",
                        "Playoffs",
                        "NBA Emirates Cup",
                        "Emirates NBA Cup"
                    ])
                ]

            if len(season_games) > 0:
                min_date = season_games["gameDateTimeEst"].min().strftime("%b %d, %Y")
                max_date = season_games["gameDateTimeEst"].max().strftime("%b %d, %Y")

                print(
                    f"{i}. {season} "
                    f"({min_date} - {max_date})"
                )

        season_choice = input("\nChoose season: ")

        try:
            selected_season = seasons[int(season_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid season.")
            continue

        df = all_df[all_df["season"] == selected_season].copy()

        if game_choice == "1":
            df = df[
                df["gameType"].isin([
                    "Regular Season",
                    "NBA Emirates Cup",
                    "Emirates NBA Cup"
                ])
            ]

        elif game_choice == "2":
            df = df[
                df["gameType"] == "Playoffs"
            ]

        elif game_choice == "3":
            df = df[
                df["gameType"].isin([
                    "Regular Season",
                    "Playoffs",
                    "NBA Emirates Cup",
                    "Emirates NBA Cup"
                ])
            ]

        current_start_date = df["gameDateTimeEst"].min().strftime("%Y-%m-%d")
        current_end_date = df["gameDateTimeEst"].max().strftime("%Y-%m-%d")

        print(
            f"\nFilters updated! "
            f"{current_game_type} | {selected_season}"
        )

        print(f"Games available: {df['gameId'].nunique():,}")
    elif choice == "6":
        statline = input("Enter statline to analyze (PTS-REB-AST-STL-BLK): ")

        parts = statline.split("-")

        if len(parts) != 5:
            print("Invalid statline format.")
            continue
        points = parts[0]
        rebounds = parts[1]
        assists = parts[2]
        steals = parts[3]
        blocks = parts[4]
        if not points.isdigit() or not rebounds.isdigit() or not assists.isdigit():
            print("Invalid statline format.")
            continue
        if steals == "" and blocks == "":
            search_key = (
                f"{int(points)}/"
                f"{int(rebounds)}/"
                f"{int(assists)}/-/-"
            )

        elif steals.isdigit() and blocks.isdigit():
            search_key = (
                f"{int(points)}/"
                f"{int(rebounds)}/"
                f"{int(assists)}/"
                f"{int(steals)}/"
                f"{int(blocks)}"
            )

        else:
            print("Invalid statline format.")
            continue
        matches = df[
            df["statline_key"] == search_key
        ]

        if len(matches) == 0:
            print("\nNo matching statline found.")
            continue
        game = matches.iloc[0]
        historical_game = all_df[
            all_df["statline_key"] == search_key
        ].iloc[0]

        print("\n===== STATLINE RARITY ANALYSIS =====")
        print(f"Statline: {format_statline(game)}")
        print(
            f"Historical occurrences: "
            f"{int(historical_game['historical_occurrences'])}"
        )
        print(
            f"Points percentile: "
            f"{historical_game['points_percentile']:.6f}"
        )

        print(
            f"Rebounds percentile: "
            f"{historical_game['reboundsTotal_percentile']:.6f}"
        )

        print(
            f"Assists percentile: "
            f"{historical_game['assists_percentile']:.6f}"
        )

        if pd.isna(historical_game["steals_percentile"]):
            print("Steals percentile: unavailable")
        else:
            print(
                f"Steals percentile: "
                f"{historical_game['steals_percentile']:.6f}"
            )

        if pd.isna(historical_game["blocks_percentile"]):
            print("Blocks percentile: unavailable")
        else:
            print(
                f"Blocks percentile: "
                f"{historical_game['blocks_percentile']:.6f}"
            )

        print(
            f"Component rarity score: "
            f"{historical_game['component_rarity_score']:.6f}"
        )

        print(
            f"Exact rarity score: "
            f"{historical_game['exact_rarity_score']:.6f}"
        )

        print(
            f"Magnitude score: "
            f"{historical_game['magnitude_score']}"
        )

        print(
            f"Sqrt magnitude percentile: "
            f"{historical_game['sqrt_magnitude_percentile']:.6f}"
        )

        print(
            f"Scoring bonus: "
            f"{historical_game['scoring_bonus']:.6f}"
        )

        print(
            f"Final rarity score: "
            f"{historical_game['final_rarity_score']:.6f}"
        )

    elif choice == "7":
        print("Goodbye!")
        break
    else:
        print("Invalid option.")