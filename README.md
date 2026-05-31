# Valorant Game Data Pipeline

An end-to-end **ELT data engineering project** built around Valorant gameplay data. It fetches game metadata from the Valorant API, simulates realistic match timelines and rank progression in Python, loads everything into a **PostgreSQL** warehouse, and models it into clean, tested analytics tables with **dbt**.

The result is a dimensional (star-schema) warehouse with analytical marts for player performance, agent pick rates, map win rates, rank distribution, and credit economy — the kind of stack you'd run in production, scaled down to a laptop.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Analytical Marts](#analytical-marts)
- [Quickstart](#quickstart)
- [Pipeline Details](#pipeline-details)
- [Simulation Logic](#simulation-logic)
- [Testing](#testing)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Architecture

This is a classic **ELT** pipeline: extract + load raw data first, then transform inside the warehouse with dbt.

```
┌──────────────┐   extract/    ┌──────────────┐   load     ┌─────────────────────────────────────┐
│ Valorant API │──transform──▶ │ Python (CSV) │──to_sql──▶ │           PostgreSQL                │
└──────────────┘   + simulate  └──────────────┘            │                                     │
                                                           │  raw  ──▶  staging  ──▶  marts      │
                                                           │ (tables)   (views)      (tables)    │
                                                           │            └────────── dbt ─────────┘
                                                           └─────────────────────────────────────┘
```

| Stage | What happens | Where |
|-------|--------------|-------|
| **Extract** | Pull agents, weapons, maps, gamemodes, gears, tiers from the Valorant API | `source/components/apiClient` |
| **Transform (Python)** | JSON → DataFrames; generate synthetic users, match timelines, and rank progression | `source/components/jsonToPdTransformer`, `matchTimeline.py` |
| **Load** | Write DataFrames to the Postgres `raw` schema (also persisted as CSVs) | `source/components/warehouse/postgres_loader.py` |
| **Transform (dbt)** | `raw` → `staging` (clean, typed views) → `marts` (star schema + analytics tables) | `valorant_dbt/` |

---

## Tech Stack

- **Python 3.13** — extraction, simulation, loading (`pandas`, `requests`, `SQLAlchemy`, `psycopg2`)
- **PostgreSQL 16** — warehouse, run locally via **Docker** (`docker-compose`)
- **dbt** (`dbt-core` + `dbt-postgres`) — in-warehouse transformations, testing, and docs
- **pytest** — integration tests for the warehouse loader
- **python-dotenv** — environment-based configuration

> **Note on dbt:** this project pins `dbt-core` + `dbt-postgres` inside an isolated `dbt_venv`. A globally installed `dbt` may be **dbt-fusion**, which does not support a Postgres adapter — hence the dedicated venv. See [Quickstart](#quickstart).

---

## Project Structure

```
Game Data Pipeline/
├── main.py                           # Pipeline entry point (extract → simulate → load)
├── docker-compose.yml                # PostgreSQL 16 service
├── requirements.txt
├── .env.example                      # Template for warehouse credentials
│
├── data/                             # CSV landing zone — GENERATED, NOT tracked in git
│   │                                 # (gitignored; recreated by `python main.py`)
│   ├── agents_dim.csv  weapons_dim.csv  maps_dim.csv  gamemodes_dim.csv
│   ├── gears_dim.csv   competitive_tiers_dim.csv  users_dim.csv
│   ├── match_df.csv    match_status.csv  round_status.csv
│   ├── agent_perf_status.csv  round_spike_status.csv
│   ├── match_summary.csv  rank_history.csv  weapon_economy.csv
│
├── source/                           # Python source
│   ├── logger.py  exceptions.py  utils.py
│   └── components/
│       ├── matchTimeline.py          # Match + rank-progression simulation engine
│       ├── users.py                  # Synthetic player generation
│       ├── apiClient/                # Valorant API client
│       ├── jsonToPdTransformer/      # JSON → DataFrame transformers
│       └── warehouse/
│           └── postgres_loader.py    # DataFrame → Postgres loader
│
├── tests/
│   └── test_postgres_loader.py       # pytest integration tests
│
└── valorant_dbt/                     # dbt project
    ├── dbt_project.yml  profiles.yml
    ├── macros/generate_schema_name.sql
    └── models/
        ├── staging/                  # 15 staging views (stg_*) + sources/tests
        └── marts/                    # 9 marts (dims, fact, analytics) + tests
```

> **Generated artifacts are not version-controlled.** The `data/` CSV outputs and any local virtual environment (`dbt_venv/`, conda envs) are gitignored — they're reproducible by running the pipeline, and some CSVs exceed git/GitHub size limits. Only source code, dbt models, and config live in the repo. Run `python main.py` to regenerate the `data/` folder from scratch.

---

## Data Model

Data flows through three schemas in Postgres, each a transformation layer.

### `raw` (loaded by Python)
15 tables landed verbatim from the pipeline — API dimensions, synthetic users, and simulated facts (including `weapon_economy`, one row per player per round). This is the immutable source of truth dbt builds on.

### `staging` (dbt views — `stg_*`)
One view per raw table. Light, non-destructive cleanup only: renaming to `snake_case`, casting types, fixing booleans (`col = 1`), and standardizing keys. Quoted mixed-case source columns (e.g. `"isAttacker"`, `"ACV"`) are normalized here.

### `marts` (dbt tables — star schema + analytics)

**Dimensions & fact:**

| Model | Grain | Notes |
|-------|-------|-------|
| `dim_players` | one row per player (1,000) | `riot_id = username \|\| tagline`; rank lives in the fact, not here |
| `dim_agents` | one row per agent | |
| `dim_maps` | one row per map | |
| `fct_player_match` | **one row per player per match** (~10,220) | joins participation + per-agent combat stats + rank movement; `is_win`, KDA, combat score, `rank_before`/`rank_after` |

`fct_player_match` is the central fact: `match_player_id = match_id || '-' || user_id`, combining `stg_matches` (participation), `stg_match_summary` (combat stats, joined on `match_id + agent_name`), and `stg_rank_history` (rank movement, joined on `match_id + user_id`).

---

## Analytical Marts

Five analytics tables sit on top of the fact, ready for BI / dashboards:

| Mart | Question it answers |
|------|---------------------|
| `mart_player_performance` | Per-player career stats: matches, win rate, K/D, total kills/deaths/assists, first bloods, avg combat score, and **current rank** (rank after most recent match) |
| `mart_agent_pickrate` | How often each agent is picked (pick rate), and how well they perform (win rate, K/D, avg combat score) |
| `mart_map_winrate` | Per-map activity, player win rate, and attacker vs. defender round-win balance |
| `mart_rank_distribution` | Current rank distribution across the player base (players per rank, share, avg points) |
| `mart_player_economy` | Per-player credit economy: rounds played, avg credits banked/spent, total earned/spent, full-buy rate, and pistol-round win rate |

Every model carries dbt tests — `unique`, `not_null`, `relationships`, and `accepted_values` (e.g. `result ∈ {win, loss}`, `is_win ∈ {0,1}`, `side ∈ {attacker, defender}`). A full `dbt build` runs **24 models and 63 tests (87 nodes)**, all passing.

---

## Quickstart

### Prerequisites
- Python 3.10+ and `pip`
- Docker Desktop (for PostgreSQL)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env      # adjust credentials if you like; defaults work out of the box
```

### 3. Start PostgreSQL
```bash
docker compose up -d
```
This launches PostgreSQL 16 (`valorant_postgres`) on `localhost:5432` with a persistent named volume.

### 4. Run the pipeline (extract → simulate → load into `raw`)
```bash
python main.py
```

### 5. Set up dbt in an isolated venv
```bash
python -m venv dbt_venv
dbt_venv/Scripts/pip install dbt-core dbt-postgres   # Windows
# dbt_venv/bin/pip install dbt-core dbt-postgres     # macOS/Linux
```

### 6. Build the warehouse models
```bash
cd valorant_dbt
../dbt_venv/Scripts/dbt.exe build --profiles-dir .   # Windows
# ../dbt_venv/bin/dbt build --profiles-dir .         # macOS/Linux
```

### 7. (Optional) Generate & serve docs
```bash
../dbt_venv/Scripts/dbt.exe docs generate --profiles-dir .
../dbt_venv/Scripts/dbt.exe docs serve --profiles-dir .
```

After step 6 you'll have `raw` (15 tables), `staging` (15 views), and `marts` (9 tables) populated and tested.

---

## Pipeline Details

`main.py` orchestrates the run in three functions:

- **`build_dimension_data()`** — calls the Valorant API client, transforms each JSON response to a DataFrame, generates synthetic users, and writes 7 dimension CSVs.
- **`build_fact_data()`** — reads the dimension CSVs and runs `generate_all_match_details()`, which simulates matches chronologically: it matchmakes by each player's live rank, simulates the match, then updates ranks before forming the next lobby. Writes 8 fact CSVs (including `match_summary`, `rank_history`, and `weapon_economy`).
- **`main()`** — runs both, then `load_all({**dimensions, **facts})` to push every DataFrame into the Postgres `raw` schema.

The loader (`postgres_loader.py`) builds a SQLAlchemy engine from env vars, ensures the target schema exists, and uses `pandas.to_sql(method="multi")` with a dynamic chunk size that respects Postgres' 65,535 bind-parameter limit. NaNs land as SQL `NULL`.

---

## Simulation Logic

Since the Valorant API exposes only metadata (not real match telemetry), match data is **synthetically simulated** to be statistically realistic.

### Match level
- 10 unique players per match, split into 2 teams of 5, on a randomly selected map.

### Round level (up to 25 rounds)
- **Rounds 1–12:** Team A attacks; **Round 13:** sides swap; **Rounds 14+:** Team B attacks.
- Match ends when a team reaches 13 round wins.

### Event level (per round)
- **Damage model:** each player has 250 HP; per-shot damage (0–255) is split across head / body / leg; a player dies when cumulative damage ≥ max health.
- **Spike mechanics:** ~70% plant probability when attackers reach a site; ~40s defuse window, ~45s detonation timer.
- **Round duration:** no spike → 80–100s (timer); detonated → up to ~145s; defused → up to ~140s.
- **Win condition:** all enemies eliminated, spike detonated (attackers), spike defused (defenders), or timer expiry (defenders if no plant).

### Matchmaking
Lobbies are formed by each player's **live rank tier**, so matches stay competitive as players climb. Players are grouped by *rank family* (IRON, BRONZE, SILVER, …, ignoring the 1/2/3 sub-rank). All 10 players in a lobby must fall within **3 consecutive rank families**; a 4-family span is allowed only when the lowest family present is **UNRANKED** (new players act as a wildcard floor). Early in a player's history everyone is UNRANKED, so the constraint is unbound until ranks diverge.

### Rank progression
Rank movement is interleaved with simulation: after each match, every player's rank and rating points are updated from the match outcome (result, round margin, and combat score relative to team average), producing `rank_history` (per player, per match: `rank_before/after`, `points_before/after`, `radiant_delta`, `result`). Each tier holds 100 points — crossing 100 promotes, dropping below 0 demotes. Every player starts **UNRANKED** and climbs from there, and the updated rank immediately feeds the next match's matchmaking.

### Credit economy & loadouts
Each round, every player runs a sequential **buy → settle** credit cycle, producing `weapon_economy` (one row per player per round, 24 columns: starting/ending credits, sidearm/secondary/gear choices and their costs, total spend, kills, survival, round outcome, credits earned, and the loss-bonus streak).

- **Loadout:** one **sidearm** + one **secondary** (a non-sidearm gun: SMG / Shotgun / Rifle / Sniper / Heavy) + one **gear** (armor). Buys are constrained to what the player can afford — spend never exceeds the wallet.
- **Buy phase:** the free **Classic** is the default sidearm; players probabilistically upgrade their sidearm, buy a secondary, and buy armor when affordable.
- **Pistol & reset rounds:** round 1 and the halftime round (round 13) reset every player to **800** credits — the classic pistol-round economy. *(Overtime's 5,000-credit reset is not yet modeled — see Roadmap.)*
- **Round earnings:** round win **+3000**; loss bonus escalates on a streak (**1900 → 2400 → 2900**); a save penalty caps a surviving loss at **1000**; **+200 per kill**; **+300 spike-plant bonus** to attackers. Wallet is capped at **6500**.
- **Weapon costs** live in `weapons_dim` (`category`, `cost`) and gear costs in `gears_dim`, both sourced from the Valorant API's `shopData` and normalized to a canonical buy-menu spec in the transformer:

  | Category | Weapons (cost) |
  |----------|----------------|
  | Sidearm  | Classic 0 · Shorty 300 · Frenzy 450 · Ghost 500 · Bandit 600 · Sheriff 800 |
  | SMG      | Stinger 1100 · Spectre 1600 |
  | Shotgun  | Bucky 850 · Judge 1850 |
  | Rifle    | Bulldog 2050 · Guardian 2250 · Phantom 2900 · Vandal 2900 |
  | Sniper   | Marshal 950 · Outlaw 2400 · Operator 4700 |
  | Heavy    | Ares 1550 · Odin 3250 |
  | Gear     | Light Armor 400 · Regen Shield 650 · Heavy Armor 1000 |

---

## Testing

The warehouse loader has a pytest integration suite (`tests/test_postgres_loader.py`):

```bash
python -m pytest
```

It uses a throwaway `loader_test` schema and **skips gracefully** if Postgres is unreachable, so it never fails on a machine without the container running. Coverage includes connectivity, schema idempotency, load round-trips, NaN→NULL handling, `replace` idempotency, and per-dimension row-count checks.

dbt provides the warehouse-side tests — run `dbt test` (or `dbt build`) to validate keys, referential integrity, and accepted values across all models.

---

## Configuration

All warehouse settings come from environment variables (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | `valorant` | DB user |
| `POSTGRES_PASSWORD` | `valorant` | DB password (dev only) |
| `POSTGRES_DB` | `valorant` | Database name |
| `POSTGRES_HOST` | `localhost` | Host |
| `POSTGRES_PORT` | `5432` | Port |
| `RAW_SCHEMA` | `raw` | Target schema for the loader |

`.env` is gitignored — only the example template is committed. The defaults are throwaway credentials for a local Docker instance; change them for any non-local use. dbt reads the same variables via `env_var(...)` in `valorant_dbt/profiles.yml`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` on `source.*` | Run `pip install -e .` to install the package in editable mode |
| Loader / dbt can't connect to Postgres | Ensure `docker compose up -d` is running and `.env` matches `docker-compose.yml` |
| dbt error: *adapter "postgres" not found* | You're using **dbt-fusion**. Install `dbt-postgres` in an isolated venv and invoke that binary (see [Quickstart](#quickstart)) |
| dbt: `column "..." does not exist` | Postgres folds unquoted identifiers to lowercase — mixed-case source columns must be double-quoted in staging models |
| dbt: `function round(double precision, integer) does not exist` | Cast the expression to `::numeric` before `round()` |
| dbt: `cannot cast type integer to boolean` | Use `(col = 1)` instead of `cast(col as boolean)` |
| pytest skips all tests | Expected when Postgres is down — start the container to run them |

---

## Roadmap

### ✅ Done
- **Simulation engine** — match timelines, damage/spike mechanics, per-agent performance, match summaries, and rank progression
- **Phase 1 — Data Warehouse** — Dockerized PostgreSQL + Python loader, integrated into `main.py`, with a pytest integration suite
- **Phase 2 — dbt** — sources, 15 staging views, star-schema marts (dims + `fct_player_match`), 5 analytical marts, and 87 passing nodes
- **Credit economy** — per-round buy/settle credit cycle, weapon & gear costs, loadout selection, loss-bonus streaks, and the `weapon_economy` fact + `mart_player_economy`

### 🚧 Next
- **BI / serving layer** — dashboards on the marts (Metabase, Streamlit, or similar)
- **Orchestration** — schedule the end-to-end run (e.g. with Airflow / Dagster / cron)
- **Economy & damage model extensions** — overtime (5,000-credit) reset, in-round weapon switches, armor/shield and body-part damage multipliers
- **ML** — win-probability and rank-progression models built on the marts

---

## License

Provided as-is for educational and portfolio purposes.
