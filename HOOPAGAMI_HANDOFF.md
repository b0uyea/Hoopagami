# HOOPAGAMI — PROJECT HANDOFF

## 1. What this project is

Hoopagami is a personal NBA Statline Scorigami web application built with Python and Flask.

The idea is to find unusual NBA player statlines and identify "Hoopagamis."

A Hoopagami is a unique player statline combination that occurred exactly once in the database.

The project is designed to let users:
- Explore NBA statlines
- Search for an exact statline
- Search for a player
- Find rare statlines
- View individual statline occurrences
- Navigate between players, statlines, and game/box-score information

The project currently runs locally on the user's Mac.

Project location:

    ~/Hoopagami

---

## 2. Important working preferences

The user strongly prefers:

- Use Terminal commands for edits whenever practical.
- Do not tell the user to manually open files in TextEdit unless necessary.
- Make only 1–2 changes at a time.
- Test after each change.
- Inspect existing code before changing it.
- Do not rewrite large sections when a small edit will work.
- Do not ask the user to re-paste code that is already known or already in the project.
- Preserve working functionality when making UI changes.
- Explain briefly what a change will do before giving the command.
- If something breaks, fix the specific issue rather than redesigning unrelated parts.

The user sometimes provides snippets from commands such as grep/sed output instead of entire files to save conversation space.

---

## 3. Project structure

Important files include:

    app.py

    templates/
        index.html
        player_search.html
        search.html
        rarest.html
        statline_detail.html

There may be additional project/data files in the project directory. Treat the actual project files as the source of truth.

---

## 4. Main Flask functionality

The Flask application is primarily controlled through `app.py`.

Important routes/pages include:

### Homepage

    /

Template:

    templates/index.html

The homepage is the main Hoopagami landing page.

It includes navigation to the major features, including:
- Explore NBA Statlines
- Search Statline
- Rarest Statlines
- Player Search

The homepage also displays overall Hoopagami/statline counts.

---

### Player Search

Route:

    /player

Template:

    templates/player_search.html

This allows the user to search for an NBA player and see that player's games/statlines.

Player Search supports filters including:
- Game type
- Season
- Rarity
- Occurrence
- Sort order

The page also displays player/game statistics.

Current overall player-game counts that have been displayed:
- Regular Season: 661
- Playoffs: 142
- NBA Cup: 13
- Total Games: 816
- Hoopagamis: 747

These numbers should not be assumed to be permanently current if the underlying dataset changes.

---

### Statline Search

Route:

    /search

Template:

    templates/search.html

This allows the user to search for an exact NBA statline and see every occurrence.

The search results include clickable player names.

Player links use:

    /player?player={{ result.player | urlencode }}

The Statline Search page currently uses the same Hoopagami visual header as the homepage.

---

### Rarest Statlines

Route:

    /rarest

Template:

    templates/rarest.html

This page displays rare NBA statlines ranked using the project's rarity system.

Each result includes information such as:
- Rank
- Statline
- Player
- Date
- Teams
- Game type
- Historical occurrences
- Global rarity rank
- Box-score link

Player names on this page are clickable and lead to Player Search.

The player link is:

    /player?player={{ result.player | urlencode }}

The Rarest Statlines page currently uses the same large Hoopagami header as the homepage.

Its statline cards were also made to visually match the Player Search cards.

---

### Individual Statline Detail

Template:

    templates/statline_detail.html

This is used for an individual statline/detail view.

Inspect the existing route in `app.py` before making changes to this functionality.

---

## 5. Hoopagami definition

The key concept is:

A Hoopagami occurs when a player's complete statline combination is unique in the database.

The relevant statistical combination is:

    PTS / REB / AST / STL / BLK

For example, a player's:
- points
- rebounds
- assists
- steals
- blocks

together form their statline.

If that exact combination occurs only once, it is a Hoopagami.

---

## 6. Distinct Statlines

"Distinct Statlines" means the number of different PTS/REB/AST/STL/BLK combinations in the database, regardless of how many times each combination occurred.

This is different from the number of Hoopagamis.

---

## 7. Important Player Search filtering fix

A major recent bug was fixed in Player Search.

Problem:

When filtering by Hoopagamis, the page was still displaying the total number of games, such as all 816 games, instead of the number of games remaining after the Hoopagami filter.

The working logic now applies the Hoopagami filter before calculating the filtered game count.

The relevant logic in `app.py` includes:

    # Apply sorting.
    matches["gameDateTimeEst"] = pd.to_datetime(
        matches["gameDateTimeEst"],
        errors="coerce"
    )

    if sort_filter == "hoopagamis":
        matches = matches[matches["player_statline_occurrences"] == 1]
        matches = matches.sort_values(
            ["global_rarity_rank", "gameDateTimeEst"],
            ascending=[True, True]
        )

There are additional sorting branches for other sort options.

After filtering/sorting:

    filtered_games = len(matches)

The page then determines the displayed game count with logic equivalent to:

    filters_active = (
        game_filter != "all"
        or season_filter != "all"
        or rarity_filter != "all"
        or occurrence_filter != "all"
        or sort_filter != "rarity_rarest"
    )

    games_showing = (
        len(results)
        if sort_filter == "hoopagamis"
        else (filtered_games if filters_active else games_played)
    )

This was tested by the user and confirmed working.

DO NOT casually replace this logic.

---

## 8. Player Search data filtering

Player Search uses the player's name to filter the underlying dataframe.

The search logic includes:

    search_mask = (
        df["firstName"].astype(str) + " " + df["lastName"].astype(str)
    ).str.contains(player_query, case=False, na=False)

    matches = df[search_mask].copy()

NBA Cup Championship games that are excluded from Hoopagami are also filtered out using logic equivalent to:

    matches = matches[
        matches["gameType"].astype(str) != "Excluded"
    ].copy()

Do not remove this exclusion without understanding why it exists.

---

## 9. Current visual design

The visual identity is important.

Primary colors:

    Deep navy: #252A34
    Burnt orange: #B94A2C
    Muted cream: #EFE2CF
    Warm brown: #765548
    Charcoal: #1E1B19

Fonts:

    "Bebas Neue", sans-serif
    "DM Sans", sans-serif

The Hoopagami logo/header uses Bebas Neue.

Body text uses DM Sans.

---

## 10. Homepage hero/header

The homepage header currently uses the following visual structure:

    .hero {
        background: var(--deep-navy);
        color: var(--muted-cream);
        padding: 70px 24px 65px;
        text-align: center;
        border-top: 7px solid var(--burnt-orange);
        border-bottom: 10px solid var(--burnt-orange);
    }

    .logo {
        font-family: "Bebas Neue", sans-serif;
        font-size: 82px;
        font-weight: 400;
        letter-spacing: 4px;
        line-height: 0.95;
        margin: 0;
        color: var(--muted-cream);
        text-shadow: 3px 3px 0 var(--burnt-orange);
    }

    .tagline {
        margin: 14px 0 0;
        color: var(--muted-cream);
        opacity: 0.75;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

The homepage logo is:

    Hoopagami

The tagline is:

    NBA Statline Scorigami

Keep other pages visually consistent with this header.

---

## 11. Player Search cards

Player Search statline cards use this general style:

    .statline-card {
        background: #fffaf2;
        padding: 18px 20px;
        margin: 14px 0;
        border: 3px solid var(--deep-navy);
        box-shadow: 5px 5px 0 var(--warm-brown);
    }

    .statline-card:hover {
        box-shadow: 5px 5px 0 var(--burnt-orange);
    }

    .statline {
        color: var(--deep-navy);
        font-family: "Bebas Neue", sans-serif;
        font-size: 29px;
        letter-spacing: .8px;
        margin-bottom: 3px;
    }

    .rank {
        color: #555;
        font-size: 15px;
        margin-bottom: 10px;
    }

    .game-info {
        color: #444;
        line-height: 1.6;
    }

    .rarity-info {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #eee;
        color: #555;
    }

These styles are the visual reference for similar result cards elsewhere.

---

## 12. Rarest Statlines cards

The Rarest Statlines page was recently updated so its cards match the Player Search cards.

Important current styling:

    .statline-card {
        background: #fffaf2;
        padding: 18px 20px;
        margin: 14px 0;
        border: 3px solid var(--deep-navy);
        box-shadow: 5px 5px 0 var(--warm-brown);
    }

    .statline-card:hover {
        box-shadow: 5px 5px 0 var(--burnt-orange);
    }

    .statline {
        color: var(--deep-navy);
        font-family: "Bebas Neue", sans-serif;
        font-size: 29px;
        letter-spacing: .8px;
        margin-bottom: 3px;
    }

    .player {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .player a {
        color: var(--deep-navy);
        text-decoration: none;
    }

    .player a:hover {
        color: var(--burnt-orange);
    }

    .game-info {
        color: #444;
        line-height: 1.6;
    }

    .rarity-info {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #eee;
        color: #555;
    }

    .box-score {
        display: inline-block;
        margin-top: 16px;
        padding: 10px 16px;
        background: var(--deep-navy);
        color: var(--muted-cream);
        text-decoration: none;
        border-radius: 6px;
        font-weight: 700;
    }

    .box-score:hover {
        background: var(--burnt-orange);
    }

---

## 13. Player links

Player names should generally be clickable when the relevant page supports Player Search.

The standard destination is:

    /player?player={{ result.player | urlencode }}

Do not remove player links when modifying result-card styling.

---

## 14. Search page fonts

The correct Google Fonts import is:

    @import url("https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap");

Do not accidentally create malformed CSS/font import syntax.

---

## 15. Recent UI fixes

### Player Search autocomplete

There was an issue where player autocomplete suggestions became white/invisible against the white background.

The suggestion text was fixed with:

    .player-suggestion {
        display: block;
        width: 100%;
        color: var(--deep-navy);
        ...
    }

Keep the text color explicit so suggestions remain visible.

### Player Search header

The Player Search page was changed to use the large Hoopagami hero/header matching the homepage.

### Statline Search header

The Statline Search page was also changed to use the same large Hoopagami hero/header.

### Rarest Statlines header

The Rarest Statlines page was changed to use the same large Hoopagami hero/header.

One earlier CSS edit accidentally replaced part of the Rarest page header styling, but that was restored.

The current header should remain intact.

---

## 16. Current Rarest Statlines status

The Rarest Statlines page currently works and visually matches the rest of the site.

It has:
- Large Hoopagami hero/header
- Rarest Statlines page content
- Styled statline cards
- Clickable player names
- Box Score links
- Rarity information

The next likely development area is adding more functionality to the Rarest Statlines page.

Possible future functionality could include:
- More filtering
- Different rarity/sorting options
- Pagination
- Search within rare statlines
- Statline category filters
- More detailed rarity information
- Navigation between related statlines
- Better exploration tools

Do not add these automatically. Ask the user what functionality they want or suggest a few options first.

---

## 17. Development philosophy

The project is already functional.

Prioritize:
1. Preserve existing functionality.
2. Make small changes.
3. Test immediately.
4. Keep the visual language consistent.
5. Avoid unnecessary refactoring.
6. Avoid changing backend logic just to accomplish a frontend change.
7. Avoid replacing working templates wholesale.
8. Use existing variables/routes/data structures whenever possible.

If a change requires a larger modification, explain why before doing it.

---

## 18. When debugging

When the user reports a bug:

1. Identify the specific page/route.
2. Inspect the relevant existing code.
3. Find the smallest section responsible.
4. Change only that section.
5. Restart the Flask app if necessary.
6. Test the exact behavior that was broken.
7. Tell the user what changed.

Do not assume a bug is caused by CSS if it could be route/data logic, and vice versa.

---

## 19. Important conversation context

The user has spent significant time building this project and wants continuity.

If another AI is taking over:
- Read this file first.
- Read `HOOPAGAMI_CURRENT_STATE.md` next.
- Then inspect the actual project files.
- Do not make the user reconstruct the project history from scratch.
- Do not ask the user to paste huge files unless the actual project files are genuinely unavailable.

The actual code/data in the project directory should always take precedence over this handoff document if they disagree.

EOFcd ~/Hoopagami

cat > HOOPAGAMI_HANDOFF.md <<'EOF'
# HOOPAGAMI — PROJECT HANDOFF

## 1. What this project is

Hoopagami is a personal NBA Statline Scorigami web application built with Python and Flask.

The idea is to find unusual NBA player statlines and identify "Hoopagamis."

A Hoopagami is a unique player statline combination that occurred exactly once in the database.

The project is designed to let users:
- Explore NBA statlines
- Search for an exact statline
- Search for a player
- Find rare statlines
- View individual statline occurrences
- Navigate between players, statlines, and game/box-score information

The project currently runs locally on the user's Mac.

Project location:

    ~/Hoopagami

---

## 2. Important working preferences

The user strongly prefers:

- Use Terminal commands for edits whenever practical.
- Do not tell the user to manually open files in TextEdit unless necessary.
- Make only 1–2 changes at a time.
- Test after each change.
- Inspect existing code before changing it.
- Do not rewrite large sections when a small edit will work.
- Do not ask the user to re-paste code that is already known or already in the project.
- Preserve working functionality when making UI changes.
- Explain briefly what a change will do before giving the command.
- If something breaks, fix the specific issue rather than redesigning unrelated parts.

The user sometimes provides snippets from commands such as grep/sed output instead of entire files to save conversation space.

---

## 3. Project structure

Important files include:

    app.py

    templates/
        index.html
        player_search.html
        search.html
        rarest.html
        statline_detail.html

There may be additional project/data files in the project directory. Treat the actual project files as the source of truth.

---

## 4. Main Flask functionality

The Flask application is primarily controlled through `app.py`.

Important routes/pages include:

### Homepage

    /

Template:

    templates/index.html

The homepage is the main Hoopagami landing page.

It includes navigation to the major features, including:
- Explore NBA Statlines
- Search Statline
- Rarest Statlines
- Player Search

The homepage also displays overall Hoopagami/statline counts.

---

### Player Search

Route:

    /player

Template:

    templates/player_search.html

This allows the user to search for an NBA player and see that player's games/statlines.

Player Search supports filters including:
- Game type
- Season
- Rarity
- Occurrence
- Sort order

The page also displays player/game statistics.

Current overall player-game counts that have been displayed:
- Regular Season: 661
- Playoffs: 142
- NBA Cup: 13
- Total Games: 816
- Hoopagamis: 747

These numbers should not be assumed to be permanently current if the underlying dataset changes.

---

### Statline Search

Route:

    /search

Template:

    templates/search.html

This allows the user to search for an exact NBA statline and see every occurrence.

The search results include clickable player names.

Player links use:

    /player?player={{ result.player | urlencode }}

The Statline Search page currently uses the same Hoopagami visual header as the homepage.

---

### Rarest Statlines

Route:

    /rarest

Template:

    templates/rarest.html

This page displays rare NBA statlines ranked using the project's rarity system.

Each result includes information such as:
- Rank
- Statline
- Player
- Date
- Teams
- Game type
- Historical occurrences
- Global rarity rank
- Box-score link

Player names on this page are clickable and lead to Player Search.

The player link is:

    /player?player={{ result.player | urlencode }}

The Rarest Statlines page currently uses the same large Hoopagami header as the homepage.

Its statline cards were also made to visually match the Player Search cards.

---

### Individual Statline Detail

Template:

    templates/statline_detail.html

This is used for an individual statline/detail view.

Inspect the existing route in `app.py` before making changes to this functionality.

---

## 5. Hoopagami definition

The key concept is:

A Hoopagami occurs when a player's complete statline combination is unique in the database.

The relevant statistical combination is:

    PTS / REB / AST / STL / BLK

For example, a player's:
- points
- rebounds
- assists
- steals
- blocks

together form their statline.

If that exact combination occurs only once, it is a Hoopagami.

---

## 6. Distinct Statlines

"Distinct Statlines" means the number of different PTS/REB/AST/STL/BLK combinations in the database, regardless of how many times each combination occurred.

This is different from the number of Hoopagamis.

---

## 7. Important Player Search filtering fix

A major recent bug was fixed in Player Search.

Problem:

When filtering by Hoopagamis, the page was still displaying the total number of games, such as all 816 games, instead of the number of games remaining after the Hoopagami filter.

The working logic now applies the Hoopagami filter before calculating the filtered game count.

The relevant logic in `app.py` includes:

    # Apply sorting.
    matches["gameDateTimeEst"] = pd.to_datetime(
        matches["gameDateTimeEst"],
        errors="coerce"
    )

    if sort_filter == "hoopagamis":
        matches = matches[matches["player_statline_occurrences"] == 1]
        matches = matches.sort_values(
            ["global_rarity_rank", "gameDateTimeEst"],
            ascending=[True, True]
        )

There are additional sorting branches for other sort options.

After filtering/sorting:

    filtered_games = len(matches)

The page then determines the displayed game count with logic equivalent to:

    filters_active = (
        game_filter != "all"
        or season_filter != "all"
        or rarity_filter != "all"
        or occurrence_filter != "all"
        or sort_filter != "rarity_rarest"
    )

    games_showing = (
        len(results)
        if sort_filter == "hoopagamis"
        else (filtered_games if filters_active else games_played)
    )

This was tested by the user and confirmed working.

DO NOT casually replace this logic.

---

## 8. Player Search data filtering

Player Search uses the player's name to filter the underlying dataframe.

The search logic includes:

    search_mask = (
        df["firstName"].astype(str) + " " + df["lastName"].astype(str)
    ).str.contains(player_query, case=False, na=False)

    matches = df[search_mask].copy()

NBA Cup Championship games that are excluded from Hoopagami are also filtered out using logic equivalent to:

    matches = matches[
        matches["gameType"].astype(str) != "Excluded"
    ].copy()

Do not remove this exclusion without understanding why it exists.

---

## 9. Current visual design

The visual identity is important.

Primary colors:

    Deep navy: #252A34
    Burnt orange: #B94A2C
    Muted cream: #EFE2CF
    Warm brown: #765548
    Charcoal: #1E1B19

Fonts:

    "Bebas Neue", sans-serif
    "DM Sans", sans-serif

The Hoopagami logo/header uses Bebas Neue.

Body text uses DM Sans.

---

## 10. Homepage hero/header

The homepage header currently uses the following visual structure:

    .hero {
        background: var(--deep-navy);
        color: var(--muted-cream);
        padding: 70px 24px 65px;
        text-align: center;
        border-top: 7px solid var(--burnt-orange);
        border-bottom: 10px solid var(--burnt-orange);
    }

    .logo {
        font-family: "Bebas Neue", sans-serif;
        font-size: 82px;
        font-weight: 400;
        letter-spacing: 4px;
        line-height: 0.95;
        margin: 0;
        color: var(--muted-cream);
        text-shadow: 3px 3px 0 var(--burnt-orange);
    }

    .tagline {
        margin: 14px 0 0;
        color: var(--muted-cream);
        opacity: 0.75;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 3px;
        text-transform: uppercase;
    }

The homepage logo is:

    Hoopagami

The tagline is:

    NBA Statline Scorigami

Keep other pages visually consistent with this header.

---

## 11. Player Search cards

Player Search statline cards use this general style:

    .statline-card {
        background: #fffaf2;
        padding: 18px 20px;
        margin: 14px 0;
        border: 3px solid var(--deep-navy);
        box-shadow: 5px 5px 0 var(--warm-brown);
    }

    .statline-card:hover {
        box-shadow: 5px 5px 0 var(--burnt-orange);
    }

    .statline {
        color: var(--deep-navy);
        font-family: "Bebas Neue", sans-serif;
        font-size: 29px;
        letter-spacing: .8px;
        margin-bottom: 3px;
    }

    .rank {
        color: #555;
        font-size: 15px;
        margin-bottom: 10px;
    }

    .game-info {
        color: #444;
        line-height: 1.6;
    }

    .rarity-info {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #eee;
        color: #555;
    }

These styles are the visual reference for similar result cards elsewhere.

---

## 12. Rarest Statlines cards

The Rarest Statlines page was recently updated so its cards match the Player Search cards.

Important current styling:

    .statline-card {
        background: #fffaf2;
        padding: 18px 20px;
        margin: 14px 0;
        border: 3px solid var(--deep-navy);
        box-shadow: 5px 5px 0 var(--warm-brown);
    }

    .statline-card:hover {
        box-shadow: 5px 5px 0 var(--burnt-orange);
    }

    .statline {
        color: var(--deep-navy);
        font-family: "Bebas Neue", sans-serif;
        font-size: 29px;
        letter-spacing: .8px;
        margin-bottom: 3px;
    }

    .player {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .player a {
        color: var(--deep-navy);
        text-decoration: none;
    }

    .player a:hover {
        color: var(--burnt-orange);
    }

    .game-info {
        color: #444;
        line-height: 1.6;
    }

    .rarity-info {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid #eee;
        color: #555;
    }

    .box-score {
        display: inline-block;
        margin-top: 16px;
        padding: 10px 16px;
        background: var(--deep-navy);
        color: var(--muted-cream);
        text-decoration: none;
        border-radius: 6px;
        font-weight: 700;
    }

    .box-score:hover {
        background: var(--burnt-orange);
    }

---

## 13. Player links

Player names should generally be clickable when the relevant page supports Player Search.

The standard destination is:

    /player?player={{ result.player | urlencode }}

Do not remove player links when modifying result-card styling.

---

## 14. Search page fonts

The correct Google Fonts import is:

    @import url("https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;600;700&display=swap");

Do not accidentally create malformed CSS/font import syntax.

---

## 15. Recent UI fixes

### Player Search autocomplete

There was an issue where player autocomplete suggestions became white/invisible against the white background.

The suggestion text was fixed with:

    .player-suggestion {
        display: block;
        width: 100%;
        color: var(--deep-navy);
        ...
    }

Keep the text color explicit so suggestions remain visible.

### Player Search header

The Player Search page was changed to use the large Hoopagami hero/header matching the homepage.

### Statline Search header

The Statline Search page was also changed to use the same large Hoopagami hero/header.

### Rarest Statlines header

The Rarest Statlines page was changed to use the same large Hoopagami hero/header.

One earlier CSS edit accidentally replaced part of the Rarest page header styling, but that was restored.

The current header should remain intact.

---

## 16. Current Rarest Statlines status

The Rarest Statlines page currently works and visually matches the rest of the site.

It has:
- Large Hoopagami hero/header
- Rarest Statlines page content
- Styled statline cards
- Clickable player names
- Box Score links
- Rarity information

The next likely development area is adding more functionality to the Rarest Statlines page.

Possible future functionality could include:
- More filtering
- Different rarity/sorting options
- Pagination
- Search within rare statlines
- Statline category filters
- More detailed rarity information
- Navigation between related statlines
- Better exploration tools

Do not add these automatically. Ask the user what functionality they want or suggest a few options first.

---

## 17. Development philosophy

The project is already functional.

Prioritize:
1. Preserve existing functionality.
2. Make small changes.
3. Test immediately.
4. Keep the visual language consistent.
5. Avoid unnecessary refactoring.
6. Avoid changing backend logic just to accomplish a frontend change.
7. Avoid replacing working templates wholesale.
8. Use existing variables/routes/data structures whenever possible.

If a change requires a larger modification, explain why before doing it.

---

## 18. When debugging

When the user reports a bug:

1. Identify the specific page/route.
2. Inspect the relevant existing code.
3. Find the smallest section responsible.
4. Change only that section.
5. Restart the Flask app if necessary.
6. Test the exact behavior that was broken.
7. Tell the user what changed.

Do not assume a bug is caused by CSS if it could be route/data logic, and vice versa.

---

## 19. Important conversation context

The user has spent significant time building this project and wants continuity.

If another AI is taking over:
- Read this file first.
- Read `HOOPAGAMI_CURRENT_STATE.md` next.
- Then inspect the actual project files.
- Do not make the user reconstruct the project history from scratch.
- Do not ask the user to paste huge files unless the actual project files are genuinely unavailable.

The actual code/data in the project directory should always take precedence over this handoff document if they disagree.

