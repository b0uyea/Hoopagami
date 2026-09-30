# HOOPAGAMI — CURRENT STATE

Last updated: September 2026

## Current status

Hoopagami is currently working locally.

The Flask app is functional and the major recent bugs have been fixed.

The project is located at:

    ~/Hoopagami

## Pages currently working

### Homepage
Route:

    /

Working with the main Hoopagami visual identity and navigation.

### Player Search
Route:

    /player

Working.

Current functionality includes:
- Player search
- Autocomplete
- Player profile/statistics
- Game type filtering
- Season filtering
- Rarity filtering
- Occurrence filtering
- Sorting
- Hoopagami filtering
- Statline/game results
- Clickable navigation where applicable

The recent "games showing" bug is fixed.

### Statline Search
Route:

    /search

Working.

It allows exact statline searches and displays occurrences.

Player names in results are clickable and lead to:

    /player?player=PLAYER_NAME

The page now has the large Hoopagami header matching the homepage.

### Rarest Statlines
Route:

    /rarest

Working.

Current functionality includes:
- Rare statline ranking
- Player information
- Date/game information
- Historical occurrence count
- Global rarity rank
- Box Score links
- Clickable player names

The page now has:
- Large Hoopagami header
- Matching Player Search-style statline cards
- Matching colors/fonts
- Clickable player names

## Recent major fix

Player Search previously showed the wrong "games showing" number when filtering by Hoopagamis.

For example, the Hoopagami filter could be active while the page still displayed all 816 games.

This was fixed by applying the Hoopagami filter before calculating the filtered game count.

The user tested the fix and confirmed:

    "Ok everything is finally working."

Do not undo this logic.

## Current Player Search totals

At the time of the recent testing, Player Search displayed:

    Regular Season: 661
    Playoffs: 142
    NBA Cup: 13
    Total Games: 816
    Hoopagamis: 747

These numbers depend on the underlying dataset and may change if the data changes.

## Current visual identity

Colors:

    #252A34  deep navy
    #B94A2C  burnt orange
    #EFE2CF  muted cream
    #765548  warm brown
    #1E1B19  charcoal

Fonts:

    Bebas Neue
    DM Sans

The Hoopagami logo is large, cream-colored, uses Bebas Neue, and has a burnt-orange shadow.

Tagline:

    NBA Statline Scorigami

## Most recent work

The latest work focused on:
1. Fixing Player Search Hoopagami filtering.
2. Fixing the games-showing count.
3. Making Player Search autocomplete text visible.
4. Making Player Search use the homepage-style header.
5. Making Statline Search use the homepage-style header.
6. Making Rarest Statlines use the homepage-style header.
7. Making Rarest Statlines cards match Player Search cards.
8. Making Rarest Statlines player names clickable.

All of these were tested during development.

## Immediate next task

The next task is to improve the functionality of the Rarest Statlines page.

The user has not yet decided exactly which functionality to add.

Possible directions include:
- More filters
- Better sorting
- Pagination
- Search
- Statline category filters
- More rarity information
- Better exploration/navigation
- Related statlines

Do NOT automatically implement one of these.

First ask the user what functionality they want, or present a small list of options.

## Important development rule

The user wants changes made incrementally.

For each new feature:
1. Explain what will change.
2. Make the smallest practical edit.
3. Test it.
4. Only then move to the next change.

Prefer Terminal commands.

Do not ask the user to paste entire files if the needed code can be inspected directly from the project.

## If another AI takes over

Tell it:

"Read HOOPAGAMI_HANDOFF.md and this file first. The actual Hoopagami project files are the source of truth. The app is currently working. Do not rewrite working functionality. The next task is to improve Rarest Statlines functionality, but wait for the user to choose what functionality they want."

