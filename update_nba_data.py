import time
import subprocess
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv3, scheduleleaguev2


PROJECT_DIR = Path.home() / "Hoopagami"
CSV_PATH = PROJECT_DIR / "NBA_PlayerStatistics_Complete.csv"

SEASON_TYPES = {
    "Regular Season": "Regular Season",
    "Playoffs": "Playoffs",
}

OUTPUT_COLUMNS = [
    "firstName",
    "lastName",
    "personId",
    "gameId",
    "gameDateTimeEst",
    "playerteamCity",
    "playerteamName",
    "opponentteamCity",
    "opponentteamName",
    "gameType",
    "gameLabel",
    "gameSubLabel",
    "seriesGameNumber",
    "minutes",
    "fieldGoalsMade",
    "fieldGoalsAttempted",
    "fieldGoalsPercentage",
    "threePointersMade",
    "threePointersAttempted",
    "threePointersPercentage",
    "freeThrowsMade",
    "freeThrowsAttempted",
    "freeThrowsPercentage",
    "reboundsOffensive",
    "reboundsDefensive",
    "reboundsTotal",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "foulsPersonal",
    "points",
    "plusMinusPoints",
]


def current_season():
    today = pd.Timestamp.today()

    season_start = pd.Timestamp(year=today.year, month=10, day=20)

    if today >= season_start:
        start_year = today.year
    else:
        start_year = today.year - 1

    return f"{start_year}-{str(start_year + 1)[-2:]}"

def clean_value(value):
    if pd.isna(value):
        return 0
    return value


def get_schedule(season):
    schedule = scheduleleaguev2.ScheduleLeagueV2(season=season).get_data_frames()[0]
    if schedule.empty:
        return {}
    return {
        str(row["gameId"]).lstrip("0"): row
        for _, row in schedule.iterrows()
    }


def get_games(season, season_type):
    result = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable=season_type,
    )

    games = result.get_data_frames()[0]

    if games.empty:
        return []

    return (
        games[["GAME_ID", "GAME_DATE"]]
        .drop_duplicates("GAME_ID")
        .apply(
            lambda row: (
                str(row["GAME_ID"]),
                pd.to_datetime(row["GAME_DATE"]).strftime("%Y-%m-%d"),
            ),
            axis=1,
        )
        .tolist()
    )


def classify_game(game_id, season_type, game_date, schedule):
    info = schedule.get(str(game_id).lstrip("0"))

    if info is not None:
        subtype = str(info.get("gameSubtype", "")).lower()
        sublabel = str(info.get("gameSubLabel", ""))
        label = str(info.get("gameLabel", ""))

        label_lower = label.lower()
        sublabel_lower = sublabel.lower()

        # Never import preseason, play-in, or All-Star games.
        if (
            "preseason" in label_lower
            or "pre-season" in label_lower
            or "play-in" in label_lower
            or "all-star" in label_lower
            or "all star" in label_lower
        ):
            return None

        # NBA Cup qualifying and knockout games.
        if subtype in {"in-season", "in-season-knockout"}:
            if sublabel_lower == "championship":
                return None

            return {
                "gameType": "NBA Cup",
                "gameLabel": label,
                "gameSubLabel": sublabel,
                "seriesGameNumber": info.get("seriesGameNumber", ""),
            }

        # Playoffs.
        if season_type == "Playoffs":
            return {
                "gameType": "Playoffs",
                "gameLabel": label,
                "gameSubLabel": sublabel,
                "seriesGameNumber": info.get("seriesGameNumber", ""),
            }

        # Regular season.
        return {
            "gameType": "Regular Season",
            "gameLabel": label,
            "gameSubLabel": sublabel,
            "seriesGameNumber": info.get("seriesGameNumber", ""),
        }

    # Fallback when schedule metadata is unavailable.
    if season_type == "Playoffs":
        return {
            "gameType": "Playoffs",
            "gameLabel": "",
            "gameSubLabel": "",
            "seriesGameNumber": "",
        }

    return {
        "gameType": "Regular Season",
        "gameLabel": "",
        "gameSubLabel": "",
        "seriesGameNumber": "",
    }


def build_rows(game_id, game_info, game_date):
    box = boxscoretraditionalv3.BoxScoreTraditionalV3(
        game_id=game_id
    ).get_data_frames()[0]

    if box.empty:
        return []

    rows = []

    teams = box[
        ["teamId", "teamCity", "teamName", "teamTricode"]
    ].drop_duplicates()

    if len(teams) != 2:
        return []

    team_lookup = {
        row["teamId"]: row
        for _, row in teams.iterrows()
    }


    for _, player in box.iterrows():
        team_id = player["teamId"]

        opponent_rows = teams[teams["teamId"] != team_id]

        if opponent_rows.empty:
            continue

        opponent = opponent_rows.iloc[0]


        row = {
            "firstName": player["firstName"],
            "lastName": player["familyName"],
            "personId": player["personId"],
            "gameId": str(int(game_id)),
            "gameDateTimeEst": game_date,
            "playerteamCity": player["teamCity"],
            "playerteamName": player["teamName"],
            "opponentteamCity": opponent["teamCity"],
            "opponentteamName": opponent["teamName"],
            "gameType": game_info["gameType"],
            "gameLabel": game_info["gameLabel"],
            "gameSubLabel": game_info["gameSubLabel"],
            "seriesGameNumber": game_info["seriesGameNumber"],
            "minutes": clean_value(player["minutes"]),
            "fieldGoalsMade": clean_value(player["fieldGoalsMade"]),
            "fieldGoalsAttempted": clean_value(
                player["fieldGoalsAttempted"]
            ),
            "fieldGoalsPercentage": clean_value(
                player["fieldGoalsPercentage"]
            ),
            "threePointersMade": clean_value(
                player["threePointersMade"]
            ),
            "threePointersAttempted": clean_value(
                player["threePointersAttempted"]
            ),
            "threePointersPercentage": clean_value(
                player["threePointersPercentage"]
            ),
            "freeThrowsMade": clean_value(player["freeThrowsMade"]),
            "freeThrowsAttempted": clean_value(
                player["freeThrowsAttempted"]
            ),
            "freeThrowsPercentage": clean_value(
                player["freeThrowsPercentage"]
            ),
            "reboundsOffensive": clean_value(
                player["reboundsOffensive"]
            ),
            "reboundsDefensive": clean_value(
                player["reboundsDefensive"]
            ),
            "reboundsTotal": clean_value(player["reboundsTotal"]),
            "assists": clean_value(player["assists"]),
            "steals": clean_value(player["steals"]),
            "blocks": clean_value(player["blocks"]),
            "turnovers": clean_value(player["turnovers"]),
            "foulsPersonal": clean_value(player["foulsPersonal"]),
            "points": clean_value(player["points"]),
            "plusMinusPoints": clean_value(
                player["plusMinusPoints"]
            ),
        }

        rows.append(row)

    return rows


def main():
    print("Hoopagami NBA data updater")
    print()

    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found: {CSV_PATH}")
        return

    existing = pd.read_csv(CSV_PATH, low_memory=False)

    existing_game_ids = set(
        existing["gameId"].astype(str).str.lstrip("0")
    )

    season = current_season()
    schedule = get_schedule(season)

    print(f"Checking season: {season}")
    print(f"Existing games: {len(existing_game_ids):,}")
    print()

    new_rows = []

    for season_type in SEASON_TYPES:
        print(f"Checking {season_type}...")

        try:
            game_ids = get_games(
                season,
                season_type,
            )
        except Exception as exc:
            print(f"  Could not retrieve games: {exc}")
            continue

        new_games = [
            (game_id, game_date)
            for game_id, game_date in game_ids
            if str(game_id).lstrip("0") not in existing_game_ids
        ]

        print(f"  Games found: {len(game_ids):,}")
        print(f"  New games: {len(new_games):,}")

        for index, (game_id, game_date) in enumerate(new_games, start=1):
            try:
                game_info = classify_game(game_id, season_type, game_date, schedule)
                if game_info is None:
                    continue
                rows = build_rows(
                    game_id,
                    game_info,
                    game_date,
                )

                new_rows.extend(rows)

                print(
                    f"  [{index}/{len(new_games)}] "
                    f"{game_id}: {len(rows)} player rows"
                )

            except Exception as exc:
                print(
                    f"  ERROR {game_id}: {exc}"
                )

            time.sleep(1)

    if not new_rows:
        print()
        print("No new games found.")
        return

    new_df = pd.DataFrame(new_rows)

    for column in OUTPUT_COLUMNS:
        if column not in new_df.columns:
            new_df[column] = ""

    new_df = new_df[OUTPUT_COLUMNS]

    combined = pd.concat(
        [existing, new_df],
        ignore_index=True,
    )

    combined = combined.drop_duplicates(
        subset=["gameId", "personId"],
        keep="first",
    )

    combined.to_csv(
        CSV_PATH,
        index=False,
    )

    print()
    print(
        f"Added {len(new_df):,} player rows."
    )
    print(
        f"Total rows: {len(combined):,}"
    )
    print("Hoopagami data update complete.")
    print("Rebuilding statline rankings...")
    subprocess.run(["python3", str(PROJECT_DIR / "statline_ranks.py")], check=True)


if __name__ == "__main__":
    main()