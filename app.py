from pathlib import Path
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "NBA_PlayerStatistics_Complete.csv"
RANKS_PATH = BASE_DIR / "statline_ranks.csv"

df = pd.read_csv(CSV_PATH)
ranks_df = pd.read_csv(RANKS_PATH)

@app.context_processor
def inject_site_stats():
    return {"hoopagami_count": int((ranks_df["historical_occurrences"] == 1).sum()), "distinct_statline_count": int(len(ranks_df))}

def format_game_type(row):
    game_type = str(row["gameType"])

    if game_type.lower() != "playoffs":
        return game_type

    label = str(row.get("gameLabel", "")).strip()

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

    game_number = row.get("seriesGameNumber")

    if pd.notna(game_number):
        game_number = str(game_number).strip()

        if game_number.lower().startswith("game "):
            return f"{label} — {game_number}"

        try:
            return f"{label} — Game {int(float(game_number))}"
        except (ValueError, TypeError):
            if game_number:
                return f"{label} — {game_number}"

    return label or "Playoffs"


def format_game_date(value):
    return pd.to_datetime(value).strftime("%B %-d, %Y")


def box_score_url(game_id):
    padded_id = str(int(float(game_id))).zfill(10)
    return f"https://www.nba.com/game/{padded_id}/box-score"


def normalize_statline_key(key):
    parts = str(key).split("/")
    normalized = []

    for part in parts:
        if part in {"-", "nan", "None"}:
            normalized.append("-")
        else:
            normalized.append(str(int(float(part))))

    return "/".join(normalized)

ranks_df["statline_key"] = ranks_df["statline_key"].apply(normalize_statline_key)

df["gameDateTimeEst"] = pd.to_datetime(df["gameDateTimeEst"])
df["historical_untracked_defense"] = (
    df["gameDateTimeEst"] < pd.Timestamp("1973-10-01")
)

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
    df.loc[df["historical_untracked_defense"], "points"].astype(int).astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "reboundsTotal"].astype(int).astype(str) + "/" +
    df.loc[df["historical_untracked_defense"], "assists"].astype(int).astype(str) + "/-/-"
)

statline_counts = df.groupby(["points", "reboundsTotal", "assists", "steals", "blocks"]).size().to_dict()

STAT_COLUMNS = ["points", "reboundsTotal", "assists", "steals", "blocks"]


def get_historical_hoopagami_activity():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()

    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )

    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    occurrence = eligible_df.groupby("statline_key").cumcount()

    new_df = eligible_df[occurrence == 0].tail(100)
    broken_df = eligible_df[occurrence == 1].tail(100)

    new_hoopagamis = []

    for _, row in new_df.iterrows():
        new_hoopagamis.append({
            "statline": row["statline_key"],
            "player": f"{row['firstName']} {row['lastName']}",
            "player_id": str(row["personId"]).replace(".0", ""),
            "date": format_game_date(row["gameDateTimeEst"]),
            "team": f"{row['playerteamCity']} {row['playerteamName']}",
            "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
            "game_type": format_game_type(row),
            "box_score_url": box_score_url(row["gameId"]),
        })

    broken_hoopagamis = []

    for _, row in broken_df.iterrows():
        statline = row["statline_key"]

        previous_match = eligible_df[
            (eligible_df["statline_key"] == statline)
            & (eligible_df["gameDateTimeEst"] < row["gameDateTimeEst"])
        ].tail(1)

        if previous_match.empty:
            continue

        previous_row = previous_match.iloc[0]

        broken_hoopagamis.append({
            "statline": statline,
            "player": f"{row['firstName']} {row['lastName']}",
            "player_id": str(row["personId"]).replace(".0", ""),
            "date": format_game_date(row["gameDateTimeEst"]),
            "team": f"{row['playerteamCity']} {row['playerteamName']}",
            "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
            "game_type": format_game_type(row),
            "box_score_url": box_score_url(row["gameId"]),
            "previous_player": f"{previous_row['firstName']} {previous_row['lastName']}",
            "previous_player_id": str(previous_row["personId"]).replace(".0", ""),
            "previous_date": format_game_date(previous_row["gameDateTimeEst"]),
            "previous_box_score_url": box_score_url(previous_row["gameId"]),
        })

    new_hoopagamis = list(reversed(new_hoopagamis))
    broken_hoopagamis = list(reversed(broken_hoopagamis))

    return new_hoopagamis, broken_hoopagamis


HISTORICAL_NEW_HOOPAGAMIS, HISTORICAL_BROKEN_HOOPAGAMIS = get_historical_hoopagami_activity()


def get_all_time_hoopagami_leaderboard():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()

    hoopagami_df = eligible_df[
        eligible_df["statline_key"].map(
            eligible_df["statline_key"].value_counts()
        ) == 1
    ].copy()

    leaderboard = (
        hoopagami_df
        .groupby(["personId", "firstName", "lastName"])
        .size()
        .reset_index(name="hoopagamis")
        .sort_values(
            ["hoopagamis", "lastName", "firstName"],
            ascending=[False, True, True]
        )
        .head(100)
    )

    return leaderboard.to_dict("records")


ALL_TIME_HOOPAGAMI_LEADERBOARD = get_all_time_hoopagami_leaderboard()


def get_current_nba_players():
    import requests

    team_ids = ["atl", "bos", "bkn", "cha", "chi", "cle", "dal", "den", "det", "gs", "hou", "ind", "lac", "lal", "mem", "mia", "mil", "min", "no", "ny", "okc", "orl", "phi", "phx", "por", "sac", "sa", "tor", "utah", "wsh"]
    players = set()

    for team_id in team_ids:
        response = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster",
            timeout=20,
        )
        response.raise_for_status()
        for player in response.json().get("athletes", []):
            name = f"{player.get('firstName', '')} {player.get('lastName', '')}".strip()
            if name:
                players.add(name)

    return players


CURRENT_NBA_PLAYERS = get_current_nba_players()


def get_all_time_hoopagami_ranks():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()

    hoopagami_df = eligible_df[
        eligible_df["statline_key"].map(
            eligible_df["statline_key"].value_counts()
        ) == 1
    ].copy()

    leaderboard = (
        hoopagami_df
        .groupby(["personId", "firstName", "lastName"])
        .size()
        .reset_index(name="hoopagamis")
        .sort_values(
            ["hoopagamis", "lastName", "firstName"],
            ascending=[False, True, True]
        )
        .reset_index(drop=True)
    )

    ranks = leaderboard["hoopagamis"].rank(method="min", ascending=False).astype(int)

    return {
        str(row["personId"]).replace(".0", ""): int(rank)
        for (_, row), rank in zip(leaderboard.iterrows(), ranks)
    }


ALL_TIME_HOOPAGAMI_RANKS = get_all_time_hoopagami_ranks()

def get_available_seasons():
    dates = pd.to_datetime(df["gameDateTimeEst"], errors="coerce").dropna()
    years = sorted(
        {
            year if month >= 8 else year - 1
            for year, month in zip(dates.dt.year, dates.dt.month)
        },
        reverse=True,
    )
    return [f"{year}-{str(year + 1)[-2:]}" for year in years]


def get_current_season_hoopagami_leaderboard(selected_season=None):
    today = pd.Timestamp.now()

    if selected_season:
        season_start_year = int(selected_season[:4])
    else:
        season_start_year = today.year if today.month >= 8 else today.year - 1

    season_opening_dates = {
        2026: pd.Timestamp("2026-10-20"),
    }

    opening_date = season_opening_dates.get(
        season_start_year,
        pd.Timestamp(f"{season_start_year}-10-01")
    )

    if today < opening_date:
        season_start_year -= 1
        opening_date = season_opening_dates.get(
            season_start_year,
            pd.Timestamp(f"{season_start_year}-10-01")
        )

    season_end = pd.Timestamp(f"{season_start_year + 1}-08-01")

    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    historical_df = eligible_df[
        eligible_df["gameDateTimeEst"] < opening_date
    ]

    season_df = eligible_df[
        (eligible_df["gameDateTimeEst"] >= opening_date)
        & (eligible_df["gameDateTimeEst"] < season_end)
    ].copy()

    seen_counts = historical_df["statline_key"].value_counts().to_dict()
    hoopagami_rows = []

    for _, row in season_df.iterrows():
        statline = row["statline_key"]
        if seen_counts.get(statline, 0) == 0:
            hoopagami_rows.append(row)
        seen_counts[statline] = seen_counts.get(statline, 0) + 1

    season_total = len(hoopagami_rows)

    if not hoopagami_rows:
        return [], season_total

    hoopagami_df = pd.DataFrame(hoopagami_rows)

    leaderboard = (
        hoopagami_df
        .groupby(["personId", "firstName", "lastName"])
        .size()
        .reset_index(name="hoopagamis")
        .sort_values(
            ["hoopagamis", "lastName", "firstName"],
            ascending=[False, True, True]
        )
    )

    return leaderboard.head(100).to_dict("records"), season_total


def get_most_broken_leaderboard():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    occurrence = eligible_df.groupby("statline_key").cumcount()
    broken_df = eligible_df[occurrence == 1].copy()

    first_occurrences = eligible_df[occurrence == 0][
        ["statline_key", "personId", "firstName", "lastName"]
    ].rename(
        columns={
            "personId": "original_personId",
            "firstName": "original_firstName",
            "lastName": "original_lastName",
        }
    )

    broken_df = broken_df.merge(
        first_occurrences,
        on="statline_key",
        how="left",
    )

    leaderboard = (
        broken_df
        .groupby(
            [
                "original_personId",
                "original_firstName",
                "original_lastName",
            ]
        )
        .size()
        .reset_index(name="broken_hoopagamis")
        .sort_values(
            ["broken_hoopagamis", "original_lastName", "original_firstName"],
            ascending=[False, True, True],
        )
        .head(100)
    )

    return leaderboard.to_dict("records")


MOST_BROKEN_LEADERBOARD = get_most_broken_leaderboard()


def get_current_players_most_broken_leaderboard():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    occurrence = eligible_df.groupby("statline_key").cumcount()
    broken_df = eligible_df[occurrence == 1].copy()

    first_occurrences = eligible_df[occurrence == 0][
        ["statline_key", "personId", "firstName", "lastName"]
    ].rename(
        columns={
            "personId": "original_personId",
            "firstName": "original_firstName",
            "lastName": "original_lastName",
        }
    )

    broken_df = broken_df.merge(
        first_occurrences,
        on="statline_key",
        how="left",
    )

    leaderboard = (
        broken_df
        .groupby(
            [
                "original_personId",
                "original_firstName",
                "original_lastName",
            ]
        )
        .size()
        .reset_index(name="broken_hoopagamis")
        .sort_values(
            ["broken_hoopagamis", "original_lastName", "original_firstName"],
            ascending=[False, True, True],
        )
    )

    current_players = {name.lower() for name in CURRENT_NBA_PLAYERS}
    current_player_ids = set()

    for name in current_players:
        name_parts = name.split(" ", 1)
        if len(name_parts) != 2:
            continue

        first_name, last_name = name_parts

        matches = eligible_df[
            (eligible_df["firstName"].astype(str).str.lower() == first_name)
            & (eligible_df["lastName"].astype(str).str.lower() == last_name)
        ]

        if not matches.empty:
            latest = matches.sort_values("gameDateTimeEst").iloc[-1]
            current_player_ids.add(str(latest["personId"]).replace(".0", ""))

    leaderboard = leaderboard[
        leaderboard["original_personId"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .isin(current_player_ids)
    ]

    return leaderboard.head(100).to_dict("records")


def get_season_most_broken_leaderboard(selected_season=None):
    today = pd.Timestamp.now()

    if selected_season:
        season_start_year = int(selected_season[:4])
    else:
        season_start_year = today.year if today.month >= 8 else today.year - 1

    season_opening_dates = {
        2026: pd.Timestamp("2026-10-20"),
    }

    opening_date = season_opening_dates.get(
        season_start_year,
        pd.Timestamp(f"{season_start_year}-10-01")
    )

    if today < opening_date:
        season_start_year -= 1
        opening_date = season_opening_dates.get(
            season_start_year,
            pd.Timestamp(f"{season_start_year}-10-01")
        )

    season_end = pd.Timestamp(f"{season_start_year + 1}-08-01")

    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    occurrence = eligible_df.groupby("statline_key").cumcount()

    broken_df = eligible_df[
        (occurrence == 1)
        & (eligible_df["gameDateTimeEst"] >= opening_date)
        & (eligible_df["gameDateTimeEst"] < season_end)
    ].copy()

    season_total = len(broken_df)

    leaderboard = (
        broken_df
        .groupby(["personId", "firstName", "lastName"])
        .size()
        .reset_index(name="broken_hoopagamis")
        .rename(
            columns={
                "personId": "original_personId",
                "firstName": "original_firstName",
                "lastName": "original_lastName",
            }
        )
        .sort_values(
            ["broken_hoopagamis", "original_lastName", "original_firstName"],
            ascending=[False, True, True],
        )
    )

    return leaderboard.head(100).to_dict("records"), season_total


@app.route("/most-broken")
def most_broken():
    view = request.args.get("view", "all-time")
    selected_season = request.args.get("season", "2025-26")
    season_total = None

    if view == "current-players":
        leaderboard_data = get_current_players_most_broken_leaderboard()
    elif view == "season":
        leaderboard_data, season_total = get_season_most_broken_leaderboard(selected_season)
    else:
        view = "all-time"
        leaderboard_data = MOST_BROKEN_LEADERBOARD

    return render_template(
        "most_broken.html",
        leaderboard=leaderboard_data,
        leaderboard_view=view,
        available_seasons=get_available_seasons(),
        selected_season=selected_season,
        season_total=season_total,
    )


def get_season_hoopagami_trends():
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    occurrence = eligible_df.groupby("statline_key").cumcount()

    eligible_df["season_start_year"] = (
        eligible_df["gameDateTimeEst"].dt.year
        - (eligible_df["gameDateTimeEst"].dt.month < 8).astype(int)
    )

    eligible_df["season"] = (
        eligible_df["season_start_year"].astype(str)
        + "-"
        + (eligible_df["season_start_year"] + 1).astype(str).str[-2:]
    )

    eligible_df["occurrence"] = occurrence

    created = (
        eligible_df[eligible_df["occurrence"] == 0]
        .groupby("season")
        .size()
        .to_dict()
    )

    broken = (
        eligible_df[eligible_df["occurrence"] == 1]
        .groupby("season")
        .size()
        .to_dict()
    )

    games = (
        eligible_df.groupby("season")["gameId"]
        .nunique()
        .to_dict()
    )

    seasons = sorted(
        set(created) | set(broken) | set(games),
        key=lambda x: int(x[:4])
    )

    return [
        {
            "season": season,
            "created": int(created.get(season, 0)),
            "broken": int(broken.get(season, 0)),
            "games": int(games.get(season, 0)),
            "created_per_100_games": round(
                (created.get(season, 0) / games[season]) * 100,
                2
            ) if games.get(season, 0) else 0,
            "broken_per_100_games": round(
                (broken.get(season, 0) / games[season]) * 100,
                2
            ) if games.get(season, 0) else 0,
        }
        for season in seasons
    ]

@app.route("/trends")
def trends():
    trend_data = get_season_hoopagami_trends()
    return render_template(
        "trends.html",
        trend_data=trend_data,
    )


@app.route("/leaderboard")
def leaderboard():
    view = request.args.get("view", "all-time")
    selected_season = request.args.get("season", "2025-26")

    season_total = None

    if view == "current-players":
        leaderboard_data = get_current_players_hoopagami_leaderboard()
    elif view == "season":
        leaderboard_data, season_total = get_current_season_hoopagami_leaderboard(selected_season)
    else:
        view = "all-time"
        leaderboard_data = ALL_TIME_HOOPAGAMI_LEADERBOARD

    return render_template(
        "leaderboard.html",
        leaderboard=leaderboard_data,
        leaderboard_view=view,
        available_seasons=get_available_seasons(),
        selected_season=selected_season,
        season_total=season_total,
    )


@app.route("/")
def home():
    today = pd.Timestamp.now()

    # Automatically use the current NBA season
    season_start_year = today.year if today.month >= 8 else today.year - 1

    season_start = pd.Timestamp(f"{season_start_year}-08-01")
    season_end = pd.Timestamp(f"{season_start_year + 1}-08-01")

    season_dates = pd.to_datetime(
        df["gameDateTimeEst"],
        errors="coerce"
    )
    regular_season_dates = df[
        (df["gameType"].astype(str) == "Regular Season")
        & (season_dates >= season_start)
        & (season_dates < season_end)
    ]["gameDateTimeEst"]

    opening_date = (
        pd.to_datetime(regular_season_dates, errors="coerce").min()
        if not regular_season_dates.empty
        else season_start
    )

    eligible_df = df[
        (df["gameType"].astype(str) != "Excluded")
        & (pd.to_datetime(df["gameDateTimeEst"], errors="coerce") >= season_start)
        & (pd.to_datetime(df["gameDateTimeEst"], errors="coerce") < season_end)
        & (pd.to_datetime(df["gameDateTimeEst"], errors="coerce") >= opening_date)
    ].copy()

    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )

    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    historical_df = df[
        (df["gameType"].astype(str) != "Excluded")
        & (pd.to_datetime(df["gameDateTimeEst"], errors="coerce") < opening_date)
    ].copy()

    seen_counts = historical_df["statline_key"].value_counts().to_dict()

    new_hoopagamis = []
    broken_hoopagamis = []

    for _, row in eligible_df.iterrows():
        statline = row["statline_key"]
        previous_count = seen_counts.get(statline, 0)

        game = {
            "statline": statline,
            "player": f"{row['firstName']} {row['lastName']}",
            "player_id": str(row["personId"]).replace(".0", ""),
            "date": format_game_date(row["gameDateTimeEst"]),
            "team": f"{row['playerteamCity']} {row['playerteamName']}",
            "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
            "game_type": format_game_type(row),
            "box_score_url": box_score_url(row["gameId"]),
        }

        if previous_count == 0:
            new_hoopagamis.append(game)

        elif previous_count == 1:
            broken_hoopagamis.append(game)

        seen_counts[statline] = previous_count + 1

    new_hoopagamis.reverse()
    broken_hoopagamis.reverse()

    return render_template(
        "index.html",
        new_hoopagamis=new_hoopagamis[:5],
        broken_hoopagamis=broken_hoopagamis[:5],
        season_start_date=opening_date.strftime("%B %-d, %Y"),
    )


@app.route("/search")
def search():
    statline = request.args.get("statline", "").strip()
    game_filter = request.args.get("game_type", "all")
    season_filter = request.args.get("season", "all")
    sort_filter = request.args.get("sort", "newest")
    from_player = request.args.get("from_player", "").strip()
    from_player_game_type = request.args.get("from_player_game_type", "all")
    from_player_season = request.args.get("from_player_season", "all")
    from_player_rarity = request.args.get("from_player_rarity", "all")
    from_player_occurrences = request.args.get("from_player_occurrences", "all")
    from_player_sort = request.args.get("from_player_sort", "rarity_rarest")
    from_new = request.args.get("from_new", "").strip()
    from_leaderboard = request.args.get("from_leaderboard", "").strip()
    from_broken_leaderboard = request.args.get("from_broken_leaderboard", "").strip()
    broken_leaderboard_view = request.args.get("broken_leaderboard_view", "").strip()
    broken_leaderboard_season = request.args.get("broken_leaderboard_season", "").strip()
    from_common = request.args.get("from_common", "").strip()
    from_rarest = request.args.get("from_rarest", "").strip()
    from_broken = request.args.get("from_broken", "").strip()

    search_mode = request.args.get("mode", "exact")

    if not statline:
        return render_template(
            "search.html",
            results=[],
            statline="",
            game_filter=game_filter,
            season_filter=season_filter,
            sort_filter=sort_filter,
            search_mode=search_mode,
            seasons=[]
        )

    try:
        normalized = statline.replace("-", "/")
        raw_parts = [x.strip() for x in normalized.split("/")]

        if len(raw_parts) > 5:
            raise ValueError

        raw_parts += [""] * (5 - len(raw_parts))

        parts = [
            None if x == "" else int(x)
            for x in raw_parts
        ]

        if any(x is not None and x < 0 for x in parts):
            raise ValueError

    except ValueError:
        return render_template(
            "search.html",
            results=[],
            statline=statline,
            error="Enter stats in PTS / REB / AST / STL / BLK order. Leave stats blank to ignore them.",
            game_filter=game_filter,
            season_filter=season_filter,
            sort_filter=sort_filter,
            search_mode=search_mode,
            seasons=[]
        )

    stat_columns = [
        "points",
        "reboundsTotal",
        "assists",
        "steals",
        "blocks"
    ]

    stat_labels = ["PTS", "REB", "AST", "STL", "BLK"]
    display_parts = []

    for label, value in zip(stat_labels, parts):
        if value is None:
            display_parts.append("—")
        elif search_mode == "minimum":
            display_parts.append(f"{value}+")
        else:
            display_parts.append(str(value))

    search_display = " / ".join(display_parts)

    matches = df.copy()

    for column, value in zip(stat_columns, parts):
        if value is None:
            continue

        if search_mode == "minimum":
            matches = matches[matches[column] >= value]
        else:
            matches = matches[matches[column] == value]

    matches = matches[matches["gameType"].astype(str) != "Excluded"].copy()

    match_dates = pd.to_datetime(matches["gameDateTimeEst"], errors="coerce")
    seasons = sorted({f"{d.year}-{str(d.year + 1)[-2:]}" if d.month >= 8 else f"{d.year - 1}-{str(d.year)[-2:]}" for d in match_dates.dropna()}, reverse=True)

    if season_filter != "all":
        season_start = int(season_filter.split("-")[0])
        start = pd.Timestamp(f"{season_start}-08-01")
        end = pd.Timestamp(f"{season_start + 1}-08-01")
        matches = matches[(match_dates >= start) & (match_dates < end)]

    if game_filter == "regular":
        matches = matches[matches["gameType"].astype(str).str.lower() == "regular season"]
    elif game_filter == "playoffs":
        matches = matches[matches["gameType"].astype(str).str.lower() == "playoffs"]
    elif game_filter == "cup":
        matches = matches[matches["gameType"].astype(str).str.lower() == "nba cup"]

    matches["gameDateTimeEst"] = pd.to_datetime(matches["gameDateTimeEst"], errors="coerce")
    matches = matches.sort_values("gameDateTimeEst", ascending=(sort_filter == "oldest"))

    # Partial/minimum searches are not single exact statlines,
    # so rarity metadata does not apply to them.
    is_full_exact_search = (
        search_mode == "exact"
        and all(x is not None for x in parts)
    )

    rarity_rank = None
    historical_occurrences = None

    if is_full_exact_search:
        lookup_parts = tuple(parts)
        rank_key = "/".join(str(x) for x in parts)
        rank_match = ranks_df[ranks_df["statline_key"] == rank_key]
        rarity_rank = (
            int(rank_match.iloc[0]["global_rarity_rank"])
            if not rank_match.empty else None
        )
        occurrence_matches = df[
            df["gameType"].astype(str) != "Excluded"
        ].copy()

        if game_filter == "regular":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "regular season"
            ]
        elif game_filter == "playoffs":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "playoffs"
            ]
        elif game_filter == "cup":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "nba cup"
            ]

        for column, value in zip(stat_columns, parts):
            if value is not None:
                occurrence_matches = occurrence_matches[
                    occurrence_matches[column] == value
                ]

        historical_occurrences = len(occurrence_matches)
    else:
        occurrence_matches = df[
            df["gameType"].astype(str) != "Excluded"
        ].copy()

        if game_filter == "regular":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "regular season"
            ]
        elif game_filter == "playoffs":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "playoffs"
            ]
        elif game_filter == "cup":
            occurrence_matches = occurrence_matches[
                occurrence_matches["gameType"].astype(str).str.lower() == "nba cup"
            ]

        for column, value in zip(stat_columns, parts):
            if value is None:
                continue

            if search_mode == "minimum":
                occurrence_matches = occurrence_matches[
                    occurrence_matches[column] >= value
                ]
            else:
                occurrence_matches = occurrence_matches[
                    occurrence_matches[column] == value
                ]

        historical_occurrences = len(occurrence_matches)

    first_match = df[df["gameType"].astype(str) != "Excluded"].copy()

    for column, value in zip(stat_columns, parts):
        if value is None:
            continue

        if search_mode == "minimum":
            first_match = first_match[first_match[column] >= value]
        else:
            first_match = first_match[first_match[column] == value]

    first_match["gameDateTimeEst"] = pd.to_datetime(
        first_match["gameDateTimeEst"],
        errors="coerce"
    )
    first_match = first_match.sort_values("gameDateTimeEst")

    first_record = None

    if not first_match.empty:
        first_row = first_match.iloc[0]
        first_record = {
            "player": f"{first_row["firstName"]} {first_row["lastName"]}",
            "date": format_game_date(first_row["gameDateTimeEst"]),
            "team": f"{first_row["playerteamCity"]} {first_row["playerteamName"]}",
            "opponent": f"{first_row["opponentteamCity"]} {first_row["opponentteamName"]}",
            "game_type": format_game_type(first_row),
            "game_id": str(first_row["gameId"]),
            "box_score_url": box_score_url(first_row["gameId"]),
        }

    results = []
    for _, row in matches.iterrows():
        results.append({
            "player": f"{row["firstName"]} {row["lastName"]}",
            "player_id": str(row["personId"]).replace(".0", ""),
            "date": format_game_date(row["gameDateTimeEst"]),
            "team": f"{row["playerteamCity"]} {row["playerteamName"]}",
            "opponent": f"{row["opponentteamCity"]} {row["opponentteamName"]}",
            "game_type": format_game_type(row),
            "game_id": str(row["gameId"]),
            "is_first": (
                is_full_exact_search
                and str(row["gameId"]) == str(first_record["game_id"])
                if first_record else False
            ),
            "box_score_url": box_score_url(row["gameId"]),
            "actual_statline": f"{int(row['points'])}/{int(row['reboundsTotal'])}/{int(row['assists'])}/{int(row['steals'])}/{int(row['blocks'])}",
            "historical_occurrences": historical_occurrences,
            "rarity_rank": rarity_rank,
        })

    page = max(int(request.args.get("page", 1)), 1)
    page_size = 100
    total_results = len(results)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_results = results[start_index:end_index]
    has_more = end_index < total_results

    return render_template(
        "search.html",
        results=paginated_results,
        statline=statline,
        search_display=search_display,
        show_actual_statline=not is_full_exact_search,
        error=None,
        game_filter=game_filter,
        season_filter=season_filter,
        sort_filter=sort_filter,
        search_mode=search_mode,
        seasons=seasons,
        first_record=first_record,
        from_player=from_player,
        from_player_game_type=from_player_game_type,
        from_player_season=from_player_season,
        from_player_rarity=from_player_rarity,
        from_player_occurrences=from_player_occurrences,
        from_player_sort=from_player_sort,
        from_common=from_common,
        from_rarest=from_rarest,
        from_broken=from_broken,
        from_new=from_new,
        page=page,
        has_more=has_more,
        total_results=total_results
    )


@app.route("/player/autocomplete")
def player_autocomplete():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return {"players": []}

    player_names = (
        df["firstName"].astype(str).str.strip()
        + " "
        + df["lastName"].astype(str).str.strip()
    ).drop_duplicates()

    lower_names = player_names.str.lower()
    first_names = lower_names.str.split().str[0]
    last_names = lower_names.str.split().str[-1]

    first_matches = player_names[
        first_names.str.startswith(query)
        | lower_names.str.startswith(query)
    ].sort_values()

    last_matches = player_names[
        last_names.str.startswith(query)
        & ~first_names.str.startswith(query)
    ].sort_values()

    matches = list(first_matches) + list(last_matches)

    return {"players": matches[:10]}


def get_player_hoopagami_trends(player_name):
    eligible_df = df[df["gameType"].astype(str) != "Excluded"].copy()
    eligible_df["gameDateTimeEst"] = pd.to_datetime(
        eligible_df["gameDateTimeEst"],
        errors="coerce"
    )
    eligible_df = eligible_df.sort_values("gameDateTimeEst")

    eligible_df["season_start_year"] = (
        eligible_df["gameDateTimeEst"].dt.year
        - (eligible_df["gameDateTimeEst"].dt.month < 8).astype(int)
    )

    eligible_df["season"] = (
        eligible_df["season_start_year"].astype(str)
        + "-"
        + (eligible_df["season_start_year"] + 1).astype(str).str[-2:]
    )

    occurrence = eligible_df.groupby("statline_key").cumcount()

    created_df = eligible_df[occurrence == 0].copy()
    broken_df = eligible_df[occurrence == 1].copy()

    player_mask_created = (
        created_df["firstName"].astype(str) + " " +
        created_df["lastName"].astype(str)
    ).str.lower() == player_name.lower()

    player_mask_broken = (
        broken_df["firstName"].astype(str) + " " +
        broken_df["lastName"].astype(str)
    ).str.lower() == player_name.lower()

    created_counts = (
        created_df[player_mask_created]
        .groupby("season")
        .size()
        .to_dict()
    )

    broken_counts = (
        broken_df[player_mask_broken]
        .groupby("season")
        .size()
        .to_dict()
    )

    seasons = sorted(
        set(created_counts) | set(broken_counts),
        key=lambda x: int(x[:4])
    )

    return [
        {
            "season": season,
            "created": int(created_counts.get(season, 0)),
            "broken": int(broken_counts.get(season, 0)),
        }
        for season in seasons
    ]


@app.route("/player")
def player_search():
    player_query = request.args.get("player", "").strip()
    game_filter = request.args.get("game_type", "all")
    from_statline = request.args.get("from_statline", "").strip()
    from_common = request.args.get("from_common", "").strip()
    from_new = request.args.get("from_new", "").strip()
    from_leaderboard = request.args.get("from_leaderboard", "").strip()
    leaderboard_view = request.args.get("leaderboard_view", "").strip()
    leaderboard_season = request.args.get("leaderboard_season", "").strip()

    from_broken_leaderboard = request.args.get("from_broken_leaderboard", "").strip()
    broken_leaderboard_view = request.args.get("broken_leaderboard_view", "").strip()
    broken_leaderboard_season = request.args.get("broken_leaderboard_season", "").strip()
    from_rarest = request.args.get("from_rarest", "").strip()
    from_broken = request.args.get("from_broken", "").strip()
    statline_game_filter = request.args.get("statline_game_type", "all")
    statline_season_filter = request.args.get("statline_season", "all")
    statline_sort_filter = request.args.get("statline_sort", "newest")
    rarity_filter = request.args.get("rarity", "all")
    occurrence_filter = request.args.get("occurrences", "all")
    sort_filter = request.args.get("sort", "rarity_rarest")
    season_filter = request.args.get("season", "all")

    results = []

    games_played = 0
    regular_season_games = 0
    playoff_games = 0
    nba_cup_games = 0
    unique_statlines = 0
    all_time_hoopagami_rank = None
    filtered_games = 0
    player_name = ""
    player_id = ""
    player_team = ""
    is_hall_of_fame = False
    player_trend_data = []

    if player_query:
        search_mask = (
            df["firstName"].astype(str) + " " + df["lastName"].astype(str)
        ).str.contains(player_query, case=False, na=False)

        matches = df[search_mask].copy()

        # Exclude NBA Cup Championship games from Hoopagami.
        matches = matches[
            matches["gameType"].astype(str) != "Excluded"
        ].copy()

        # Build the season list from this player's actual games.
        player_dates = pd.to_datetime(matches["gameDateTimeEst"], errors="coerce")
        player_seasons = sorted(
            {
                f"{d.year}-{str(d.year + 1)[-2:]}" if d.month >= 8
                else f"{d.year - 1}-{str(d.year)[-2:]}"
                for d in player_dates.dropna()
            },
            reverse=True
        )

        if not matches.empty:
            player_name = f"{matches.iloc[0]['firstName']} {matches.iloc[0]['lastName']}"
            player_id = str(matches.iloc[0]["personId"]).replace(".0", "")
            all_time_hoopagami_rank = ALL_TIME_HOOPAGAMI_RANKS.get(player_id)
            player_team = f"{matches.iloc[0]['playerteamCity']} {matches.iloc[0]['playerteamName']}"
            hof_path = Path(__file__).resolve().parent / "hall_of_fame.txt"
            if hof_path.exists():
                hall_of_fame_names = {line.strip() for line in hof_path.read_text(encoding="utf-8").splitlines() if line.strip()}
                is_hall_of_fame = player_name in hall_of_fame_names
            player_trend_data = get_player_hoopagami_trends(player_name)

            games_played = len(matches)

            regular_season_games = int(
                (matches["gameType"].astype(str).str.lower() == "regular season").sum()
            )

            playoff_games = int(
                (matches["gameType"].astype(str).str.lower() == "playoffs").sum()
            )

            nba_cup_games = int(
                (matches["gameType"].astype(str).str.lower() == "nba cup").sum()
            )

            unique_statlines = int(
                matches["statline_key"]
                .map(ranks_df.set_index("statline_key")["historical_occurrences"])
                .eq(1)
                .sum()
            )

        # Apply season filter.
        if season_filter != "all":
            season_start = int(season_filter.split("-")[0])
            season_start_date = pd.Timestamp(f"{season_start}-08-01")
            season_end_date = pd.Timestamp(f"{season_start + 1}-08-01")

            match_dates = pd.to_datetime(
                matches["gameDateTimeEst"],
                errors="coerce"
            )

            matches = matches[
                (match_dates >= season_start_date)
                & (match_dates < season_end_date)
            ]

        # Apply game type filter.
        if game_filter == "regular":
            matches = matches[
                matches["gameType"].astype(str).str.lower() == "regular season"
            ]
        elif game_filter == "playoffs":
            matches = matches[
                matches["gameType"].astype(str).str.lower() == "playoffs"
            ]
        elif game_filter == "cup":
            matches = matches[
                matches["gameType"].astype(str).str.lower() == "nba cup"
            ]

        matches = matches.merge(
            ranks_df[
                ["statline_key", "global_rarity_rank", "historical_occurrences"]
            ],
            on="statline_key",
            how="left"
        )

        # Count how many times this player recorded each statline.
        player_statline_counts = matches.groupby("statline_key").size()
        matches["player_statline_occurrences"] = matches["statline_key"].map(player_statline_counts)

    # Apply player occurrence filter.
        if occurrence_filter == "once":
            matches = matches[matches["player_statline_occurrences"] == 1]
        elif occurrence_filter == "twice":
            matches = matches[matches["player_statline_occurrences"] == 2]
        elif occurrence_filter == "three":
            matches = matches[matches["player_statline_occurrences"] == 3]
        elif occurrence_filter == "four_plus":
            matches = matches[matches["player_statline_occurrences"] >= 4]

        # Apply rarity filter.
        if rarity_filter == "unique":
            matches = matches[matches["historical_occurrences"] == 1]
        elif rarity_filter == "twice":
            matches = matches[matches["historical_occurrences"] == 2]
        elif rarity_filter == "three_plus":
            matches = matches[matches["historical_occurrences"] >= 3]

        # Apply sorting.
        matches["gameDateTimeEst"] = pd.to_datetime(
            matches["gameDateTimeEst"],
            errors="coerce"
        )

        if sort_filter == "hoopagamis":
            matches = matches[matches["historical_occurrences"] == 1]
            matches = matches.sort_values(
                ["global_rarity_rank", "gameDateTimeEst"],
                ascending=[True, True]
            )
        elif sort_filter == "player_most_common":
            matches = matches.sort_values(
                ["player_statline_occurrences", "global_rarity_rank", "gameDateTimeEst"],
                ascending=[False, True, False]
            )
        elif sort_filter == "player_least_common":
            matches = matches.sort_values(
                ["player_statline_occurrences", "global_rarity_rank", "gameDateTimeEst"],
                ascending=[True, True, False]
            )
        elif sort_filter == "rarity_rarest":
            matches = matches.sort_values(
                ["global_rarity_rank", "gameDateTimeEst"],
                ascending=[True, True]
            )
        elif sort_filter == "rarity_common":
            matches = matches.sort_values(
                ["global_rarity_rank", "gameDateTimeEst"],
                ascending=[False, True]
            )
        elif sort_filter == "highest_scoring":
            matches["statline_magnitude"] = (
                pd.to_numeric(matches["points"], errors="coerce").fillna(0)
                + pd.to_numeric(matches["reboundsTotal"], errors="coerce").fillna(0)
                + pd.to_numeric(matches["assists"], errors="coerce").fillna(0)
                + pd.to_numeric(matches["steals"], errors="coerce").fillna(0)
                + pd.to_numeric(matches["blocks"], errors="coerce").fillna(0)
            )
            matches = matches.sort_values(
                ["statline_magnitude", "gameDateTimeEst"],
                ascending=[False, False]
            )
        elif sort_filter == "newest":
            matches = matches.sort_values(
                "gameDateTimeEst",
                ascending=False
            )
        elif sort_filter == "oldest":
            matches = matches.sort_values(
                "gameDateTimeEst",
                ascending=True
            )
        else:
            matches = matches.sort_values(
                ["global_rarity_rank", "gameDateTimeEst"],
                ascending=[True, True]
            )

        # Count games after all filters and sorting.
        filtered_games = len(matches)

        # Group identical statlines together while preserving every game.
        grouped_results = {}

        for _, row in matches.iterrows():
            key = row["statline_key"]

            if key not in grouped_results:
                grouped_results[key] = {
                    "player": f"{row['firstName']} {row['lastName']}",
                    "statline": key,
                    "historical_occurrences": int(row["historical_occurrences"]),
                    "rarity_rank": int(row["global_rarity_rank"]),
                    "games": [],
                }

            grouped_results[key]["games"].append({
                "date": format_game_date(row["gameDateTimeEst"]),
                "team": f"{row['playerteamCity']} {row['playerteamName']}",
                "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
                "game_type": format_game_type(row),
                "box_score_url": box_score_url(row["gameId"]),
            })

        if sort_filter == "most_common":
            grouped_results = dict(sorted(
                grouped_results.items(),
                key=lambda item: (-len(item[1]["games"]), item[1]["rarity_rank"])
            ))

        for result in grouped_results.values():
            result["player_games"] = len(result["games"])

            # Most recent game first.
            result["games"].sort(
                key=lambda game: pd.to_datetime(game["date"]),
                reverse=True
            )

            # Use the most recent game for the compact summary.
            latest = result["games"][0]

            results.append({
                "player": result["player"],
                "statline": result["statline"],
                "historical_occurrences": result["historical_occurrences"],
                "rarity_rank": result["rarity_rank"],
                "player_games": result["player_games"],
                "date": latest["date"],
                "team": latest["team"],
                "opponent": latest["opponent"],
                "game_type": latest["game_type"],
                "box_score_url": latest["box_score_url"],
                "games": result["games"],
            })


    filters_active = (
        game_filter != "all"
        or season_filter != "all"
        or rarity_filter != "all"
        or occurrence_filter != "all"
        or sort_filter != "rarity_rarest"
    )

    games_showing = sum(result["player_games"] for result in results) if filters_active else games_played

    return render_template(
        "player_search.html",
        player_query=player_query,
        player_name=player_name,
        player_id=player_id,
        player_team=player_team,
        is_hall_of_fame=is_hall_of_fame, from_broken=from_broken, from_new=from_new,
        from_leaderboard=from_leaderboard,
        leaderboard_view=leaderboard_view,
        leaderboard_season=leaderboard_season,
        from_broken_leaderboard=from_broken_leaderboard,
        broken_leaderboard_view=broken_leaderboard_view,
        broken_leaderboard_season=broken_leaderboard_season,
        from_statline=from_statline,
        from_common=from_common,
        from_rarest=from_rarest,
        statline_game_filter=statline_game_filter,
        statline_season_filter=statline_season_filter,
        statline_sort_filter=statline_sort_filter,
        games_played=games_played,
        filtered_games=filtered_games,
        games_showing=games_showing,
        filters_active=filters_active,
        regular_season_games=regular_season_games,
        playoff_games=playoff_games,
        nba_cup_games=nba_cup_games,
        unique_statlines=unique_statlines,
        all_time_hoopagami_rank=all_time_hoopagami_rank,
        game_filter=game_filter,
        occurrence_filter=occurrence_filter,
        rarity_filter=rarity_filter,
        sort_filter=sort_filter,
        season_filter=season_filter,
        seasons=player_seasons if player_query else [],
        results=results,
        player_trend_data=player_trend_data,
    )


@app.route("/new")
def newest_hoopagamis():
    new_hoopagamis = HISTORICAL_NEW_HOOPAGAMIS

    return render_template(
        "newest_hoopagamis.html",
        season_label="NBA History",
        season_start_date="",
        season_games=0,
        new_hoopagamis=new_hoopagamis,
        broken_hoopagamis=[],
    )


@app.route("/broken")
def broken_hoopagamis():
    broken_hoopagamis = HISTORICAL_BROKEN_HOOPAGAMIS

    return render_template(
        "broken_hoopagamis.html",
        season_label="NBA History",
        season_start_date="",
        season_games=0,
        new_hoopagamis=[],
        broken_hoopagamis=broken_hoopagamis,
    )



@app.route("/broken-history")
def broken_hoopagamis_history():
    broken_hoopagamis = HISTORICAL_BROKEN_HOOPAGAMIS

    return render_template(
        "broken_hoopagamis.html",
        season_label="NBA History",
        season_start_date="",
        season_games=0,
        new_hoopagamis=[],
        broken_hoopagamis=broken_hoopagamis,
    )


@app.route("/statline/<path:statline>")
def statline_detail(statline):
    normalized = normalize_statline_key(statline)

    rank_match = ranks_df[ranks_df["statline_key"] == normalized]

    if rank_match.empty:
        return "Statline not found", 404

    rank = rank_match.iloc[0]

    matches = df[df["statline_key"] == normalized].copy()

    results = []

    for _, row in matches.iterrows():
        results.append({
            "player": f"{row['firstName']} {row['lastName']}",
            "date": format_game_date(row["gameDateTimeEst"]),
            "team": f"{row['playerteamCity']} {row['playerteamName']}",
            "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
            "game_type": format_game_type(row),
            "box_score_url": box_score_url(row["gameId"]),
        })

    return render_template(
        "statline_detail.html",
        statline=normalized,
        rank=int(rank["global_rarity_rank"]),
        occurrences=int(rank["historical_occurrences"]),
        results=results,
    )


@app.route("/common")
def common():
    common_df = ranks_df.sort_values(
        ["historical_occurrences", "global_rarity_rank"],
        ascending=[False, True]
    ).head(100)

    results = []

    for _, rank in common_df.iterrows():
        statline = rank["statline_key"]

        matches = df[
            (df["statline_key"] == statline)
            & (df["gameType"].astype(str) != "Excluded")
        ].copy()

        most_recent = None

        if not matches.empty:
            matches["gameDateTimeEst"] = pd.to_datetime(
                matches["gameDateTimeEst"],
                errors="coerce"
            )
            matches = matches.sort_values("gameDateTimeEst")

            row = matches.iloc[-1]

            most_recent = {
                "player": f"{row['firstName']} {row['lastName']}",
                "player_id": str(row["personId"]).replace(".0", ""),
                "date": format_game_date(row["gameDateTimeEst"]),
                "team": f"{row['playerteamCity']} {row['playerteamName']}",
                "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
                "game_type": format_game_type(row),
                "box_score_url": box_score_url(row["gameId"]),
            }

        results.append({
            "statline": statline,
            "occurrences": int(rank["historical_occurrences"]),
            "rarity_rank": int(rank["global_rarity_rank"]),
            "most_recent": most_recent,
        })

    return render_template("common.html", results=results)


@app.route("/rarest")
def rarest():
    search_query = request.args.get("query", "").strip()
    occurrence_filter = request.args.get("occurrences", "all")

    rarest_df = ranks_df.sort_values("global_rarity_rank")

    if search_query:
        rarest_df = rarest_df[
            rarest_df["statline_key"].astype(str).str.contains(
                search_query,
                case=False,
                na=False
            )
        ]

    if occurrence_filter == "1":
        rarest_df = rarest_df[rarest_df["historical_occurrences"] == 1]
    elif occurrence_filter == "2":
        rarest_df = rarest_df[rarest_df["historical_occurrences"] == 2]
    elif occurrence_filter == "3":
        rarest_df = rarest_df[rarest_df["historical_occurrences"] == 3]
    elif occurrence_filter == "4+":
        rarest_df = rarest_df[rarest_df["historical_occurrences"] >= 4]

    page = max(int(request.args.get("page", 1)), 1)
    page_size = 100
    total_results = len(rarest_df)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    rarest_df = rarest_df.iloc[start_index:end_index]
    has_more = end_index < total_results

    results = []

    for _, rank in rarest_df.iterrows():
        statline = rank["statline_key"]
        parts = statline.split("/")

        matches = df[df["statline_key"] == statline] if "statline_key" in df.columns else pd.DataFrame()

        if not matches.empty:
            games = []

            for _, row in matches.iterrows():
                games.append({
                    "player": f"{row['firstName']} {row['lastName']}",
                    "player_id": str(row["personId"]).replace(".0", ""),
                    "date": format_game_date(row["gameDateTimeEst"]),
                    "team": f"{row['playerteamCity']} {row['playerteamName']}",
                    "opponent": f"{row['opponentteamCity']} {row['opponentteamName']}",
                    "game_type": format_game_type(row),
                    "game_id": str(row["gameId"]),
                    "box_score_url": box_score_url(row["gameId"]),
                })

            results.append({
                "statline": statline,
                "rank": int(rank["global_rarity_rank"]),
                "occurrences": int(rank["historical_occurrences"]),
                "games": games,
            })
        else:
            results.append({
                "statline": statline,
                "rank": int(rank["global_rarity_rank"]),
                "occurrences": int(rank["historical_occurrences"]),
                "player": "Unknown",
                "date": "",
            })

    return render_template(
        "rarest.html",
        results=results,
        page=page,
        has_more=has_more,
        query=search_query,
        occurrence_filter=occurrence_filter
    )


if __name__ == "__main__":
    app.run(debug=True)
