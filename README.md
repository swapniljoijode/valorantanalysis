# Valorant Analysis

A comprehensive data generation and simulation framework for analyzing Valorant gameplay. This project fetches game metadata from the Valorant API, transforms it into structured data, and generates synthetic match timelines with detailed player performance metrics.

---

## Table of Contents

- [Overview](#overview)
- [Project Status](#project-status)
- [Future Use Cases](#future-use-cases)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Core Logic](#core-logic)
- [Installation](#installation)
- [Usage](#usage)
- [Data Output](#data-output)
- [Configuration](#configuration)
- [Logging](#logging)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Status**: 🚧 In Active Development

The Valorant Analysis project serves two primary functions:

1. **API Data Pipeline**: Fetches Valorant game metadata (agents, weapons, maps, competitive tiers) from the official Valorant API and transforms it into structured CSV files.
2. **Match Timeline Simulator**: Generates synthetic match data with realistic round-by-round gameplay, including kill/death events, spike plants/defuses, and individual player performance metrics.

This framework is designed to provide a scalable foundation for:
- Building data warehouses for Valorant analytics
- Training ML models on game state and player behavior
- Analyzing player performance patterns and progression
- Understanding game mechanics at scale
- Developing predictive models for match outcomes and player rankings

### Current Capabilities ✅
- API metadata fetching and transformation
- Synthetic match generation with team assignments
- Round-by-round simulation (25 rounds per match)
- Basic kill/death event simulation
- Spike plant/defuse mechanics
- Per-agent performance statistics
- Comprehensive logging and error handling

### Planned Features 🚀
- Weapon economy system (credits per round)
- Advanced hit-damage mechanics (armor, shields, abilities)
- Weapon selection logic per round based on economy
- Match summary generation
- Player rank progression tracking
- Matchmaking by rank tier
- Advanced game state indicators

---

## Project Status

### Current Development Phase: **Alpha**

The project is actively under development with core simulation mechanics in place. The foundation supports:
- ✅ Match data generation
- ✅ Player performance tracking
- ✅ Round mechanics (planting/defusing spikes)
- ⏳ **In Progress**: Weapon economy and advanced damage mechanics
- ⏳ **Planned**: Rank progression and matchmaking improvements

---

## Future Use Cases

This project is designed to support future machine learning and analytical applications:

### 1. **Predictive Modeling**
- **Win Probability Models**: Predict match outcomes based on player composition, rank distribution, and map selection
- **Player Performance Prediction**: Forecast individual player KDA, round survival rates, and economy management
- **Ranking Systems**: Build models to predict rank progression and tier advancement

### 2. **Anomaly Detection**
- Detect unusual player behavior patterns (e.g., sharp skill changes)
- Identify potential smurfing or account boosting
- Flag suspicious win/loss streaks and match patterns

### 3. **Agent/Meta Analysis**
- Analyze agent win rates across different rank tiers
- Study meta shifts based on balance changes
- Correlate agent selections with team composition outcomes
- Identify optimal team compositions

### 4. **Matchmaking Optimization**
- Develop balanced team creation algorithms
- Optimize rank-based player pairings
- Reduce rank-based imbalance in matches
- Predict competitive fairness metrics

### 5. **Economic System Analysis**
- Model optimal weapon buy patterns per round
- Analyze economy reset strategies
- Predict round outcomes based on economy state
- Study pistol round strategy effectiveness

### 6. **Player Development Tracking**
- Create skill progression models
- Identify learning curves and skill plateaus
- Benchmark player improvements over time
- Recommend practice focus areas

### 7. **Esports Analytics**
- Team composition strength evaluation
- Historical match data analysis and replay systems
- Player talent identification and scouting
- Tournament predictions and simulations

### 8. **Game Design Insights**
- Map balance analysis through gameplay data
- Agent ability effectiveness measurement
- Round economy impact on game dynamics
- Meta evolution tracking

---

## Project Structure

```
ValorantAnalysis/
├── main.py                          # Entry point for API data pipeline
├── requirements.txt                 # Project dependencies
├── setup.py                         # Package installation configuration
│
├── data/                            # Output directory for generated CSVs
│   ├── agents_dim.csv               # Agent metadata (name, role, abilities)
│   ├── weapons_dim.csv              # Weapon specifications
│   ├── maps_dim.csv                 # Map information
│   ├── gamemodes_dim.csv            # Game mode definitions
│   ├── gears_dim.csv                # Equipment/gear data
│   ├── competitive_tiers_dim.csv    # Rank/tier definitions
│   ├── users_dim.csv                # Synthetic user profiles
│   ├── match_status.csv             # Match-level results
│   ├── round_status.csv             # Round-level statistics
│   ├── agent_perf_status.csv        # Per-agent performance metrics
│   └── round_spike_status.csv       # Spike plant/defuse events
│
└── source/                          # Main source code
    ├── __init__.py
    ├── logger.py                    # Logging configuration
    ├── exceptions.py                # Custom exception classes
    ├── utils.py                     # Utility functions
    │
    ├── components/
    │   ├── matchTimeline.py         # Match simulation engine
    │   ├── users.py                 # Synthetic user generation
    │   │
    │   ├── apiClient/
    │   │   └── valorant_api_client.py    # Valorant API integration
    │   │
    │   └── jsonToPdTransformer/
    │       ├── agents.py            # JSON → DataFrame transformers
    │       ├── weapons.py
    │       ├── maps.py
    │       ├── gamemodes.py
    │       ├── gears.py
    │       └── competitivetiers.py
```

---

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────┐
│ Presentation Layer                          │
│ (main.py, matchTimeline.py)                 │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│ Logic Layer                                 │
│ - API Client (valorant_api_client.py)       │
│ - Transformers (jsonToPdTransformer/)       │
│ - Simulation (matchTimeline.py functions)   │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│ Data Layer                                  │
│ - External API (Valorant)                   │
│ - CSV Storage (data/)                       │
└─────────────────────────────────────────────┘
```

### Data Pipeline Flow

```
Valorant API
    ↓
ValorantAPIClient
    ↓
JSON Response
    ↓
Transformers (jsonToPdTransformer)
    ↓
DataFrame Objects
    ↓
CSV Export (data/)
```

### Match Simulation Flow

```
users_df + agents_df + maps_df
    ↓
generate_all_match_details()
    ├─ Generate match base data
    ├─ For each match:
    │   ├─ team_division() - Assign teams
    │   ├─ generating_full_match_details_per_round() - 25 rounds
    │   │   ├─ team_side_assignment() - Set attacker/defender
    │   │   ├─ events_per_round() - Simulate combat
    │   │   │   ├─ kill_death_simulation_by_damage()
    │   │   │   └─ Compute spike plant/defuse
    │   │   ├─ compute_round_duration_seconds()
    │   │   └─ Track player stats/kills/deaths
    │   └─ Aggregate match results
    ↓
match_status, round_status, agent_perf_status, round_spike_status
    ↓
CSV Export
```

---

## Core Logic

### 1. API Data Pipeline (main.py)

Fetches Valorant metadata and transforms into structured dimensions:

```python
# Step 1: Initialize API client
client = ValorantAPIClient()

# Step 2: Fetch raw JSON from Valorant API
agents_json = client.get_agents()
weapons_json = client.get_weapons()
maps_json = client.get_maps()
# ... etc

# Step 3: Transform JSON to DataFrames
df_agents = agents_json_to_df(agents_json)
df_weapons = weapons_json_to_df(weapons_json)
# ... etc

# Step 4: Export to CSV
df_agents.to_csv("data/agents_dim.csv", index=False)
```

**Output Tables:**
- `agents_dim`: Agent UUID, display name, role, abilities
- `weapons_dim`: Weapon specifications, costs, damage
- `maps_dim`: Map identifiers and metadata
- `gamemodes_dim`: Game mode definitions
- `competitive_tiers_dim`: Rank/tier systems
- `users_dim`: Synthetic user profiles with join dates

### 2. Synthetic User Generation (users.py)

Creates synthetic player profiles:
- User ID and join date (distributed over time)
- Associated competitive tier
- Randomized player attributes

### 3. Match Timeline Simulation (matchTimeline.py)

Generates realistic match data through multi-level simulation:

#### **Match Level**
- Creates matches with 10 unique players
- Assigns players to 2 teams (5 per team)
- Selects a map for the match

#### **Round Level (25 rounds per match)**
- **Rounds 1-12**: Team A starts as attackers
- **Round 13**: Teams swap sides
- **Rounds 14-25**: Team B becomes attackers
- Match ends when one team reaches 13 round wins

#### **Event Level (Per Round)**
- **Attacker Role**: Plant spike on the map
- **Defender Role**: Prevent spike plant or defuse planted spike
- **Combat**: Kill/death simulations based on damage calculations
- **Outcome**: Determine round winner (attackers or defenders)

#### **Key Simulation Details**

**Damage Simulation:**
- Each player has 250 HP (base health)
- Random damage values (0-255) per shot
- Damage distributed to body parts: head, body, leg
- Player dies when cumulative damage ≥ max health

**Spike Mechanics:**
- Spike planted: 70% probability if attackers reach site
- Spike defuse time: 40 seconds from plant
- Spike detonation: ~45 seconds from plant
- Defenders have window to defuse before detonation

**Round Duration:**
- **No spike**: 80-100 seconds (timer expires)
- **Spike detonated**: 20-100s (to plant) + 35-45s (fuse) = up to 145s
- **Spike defused**: 20-90s (to plant) + 5-35s (to defuse) = up to 140s

**Round Win Condition:**
- All enemies eliminated, OR
- Spike planted & detonated (attackers win), OR
- Spike defused before detonation (defenders win), OR
- Timer expires (defender win if spike not planted)

---

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ValorantAnalysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create data directory**
   ```bash
   mkdir -p data
   ```

4. **Verify installation**
   ```bash
   python -c "import pandas; import requests; print('All dependencies installed!')"
   ```

---

## Usage

### 1. Fetch Valorant API Data

```bash
python main.py
```

**Output**: Generates CSV files in `data/` directory
- `agents_dim.csv`
- `weapons_dim.csv`
- `maps_dim.csv`
- `gamemodes_dim.csv`
- `gears_dim.csv`
- `competitive_tiers_dim.csv`
- `users_dim.csv`

### 2. Generate Match Timeline Simulations

```bash
python -m source.components.matchTimeline
```

**Configuration** (in `matchTimeline.py`'s `__main__` block):
- Customize date range: `start_date`, `end_date`
- Adjust matches per day: `per_day_match_counter`
- Modify round count: `total_rounds` (default: 25)

**Output**: Generates match analysis CSVs
- `match_status.csv` - Match-level results (wins/losses)
- `round_status.csv` - Per-round statistics and durations
- `agent_perf_status.csv` - Individual player performance metrics
- `round_spike_status.csv` - Spike plant/defuse events

### 3. Python API Usage

```python
from source.components.matchTimeline import generate_all_match_details
import pandas as pd

# Load base data
users_df = pd.read_csv("data/users_dim.csv", parse_dates=["join_date"])
agents_df = pd.read_csv("data/agents_dim.csv")
maps_df = pd.read_csv("data/maps_dim.csv")

# Generate matches
match_status, round_status, agent_perf_status, round_spike_status, match_df = \
    generate_all_match_details(
        users_df=users_df,
        agents_df=agents_df,
        maps_df=maps_df,
        per_day_match_counter=2,  # 2 matches per day
        start_date="2025-01-01",
        end_date="2025-12-31"
    )

# Analyze results
print(f"Generated {len(match_status)} matches")
print(f"Total rounds: {len(round_status)}")
print(f"Agent performances recorded: {len(agent_perf_status)}")
```

---

## Data Output

### match_status.csv
| Column | Description |
|--------|-------------|
| match_id | Unique match identifier |
| attacker_round_wins | Number of rounds won by attackers |
| defender_round_wins | Number of rounds won by defenders |

### round_status.csv
| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| round_id | Unique round identifier (e.g., MATCH_000001-R01) |
| total_round_duration | Duration of round in seconds |

### agent_perf_status.csv
| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| round_id | Parent round identifier |
| agent_name | Player/agent name |
| isAttacker | 1 if agent was attacker, 0 if defender |
| isDefender | 1 if agent was defender, 0 if attacker |
| opponent | Enemy agent name |
| head_hit | Head shots landed |
| body_hit | Body shots landed |
| leg_hit | Leg shots landed |
| head_damage | Head damage dealt |
| body_damage | Body damage dealt |
| leg_damage | Leg damage dealt |

### round_spike_status.csv
| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| round_id | Parent round identifier |
| spike_planted | 1 if spike was planted, 0 otherwise |
| spike_defused | 1 if spike was defused, 0 otherwise |

---

## Future Data Output Tables

The following tables will be generated in upcoming phases:

### weapon_usage.csv (Phase 2) 🚧
Weapon selection and usage statistics per player per round

| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| round_id | Parent round identifier |
| agent_name | Player/agent name |
| primary_weapon | Primary weapon selected for round |
| secondary_weapon | Secondary weapon selected for round |
| armor_level | Armor purchased (0/200/400) |
| weapon_kills | Kills with primary weapon |
| utility_used | Utility abilities used |

### economy_state.csv (Phase 2) 🚧
Round-by-round economy information

| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| round_id | Parent round identifier |
| team | Team identifier |
| total_credits | Total team credits available |
| economy_state | Buy state (full_buy, eco, half_buy, pistol) |
| spent_credits | Total credits spent this round |
| credit_deficit | Credit shortage (if any) |

### match_summary.csv (Phase 3) 🚧
High-level match summary and statistics

| Column | Description |
|--------|-------------|
| match_id | Unique match identifier |
| winning_team | Team that won the match |
| final_score | Final round score (e.g., "13-5") |
| mvp | Most Valuable Player (agent_name) |
| average_match_duration | Total match time in seconds |
| combat_duration | Total combat time (excluding downtime) |
| total_kills | Total elimination count across all players |
| total_plants | Total spike plants in match |

### player_progression.csv (Phase 3) 🚧
Player rank progression and rating changes

| Column | Description |
|--------|-------------|
| match_id | Parent match identifier |
| agent_name | Player/agent name |
| starting_rank | Rank before match |
| ending_rank | Rank after match |
| rr_gain | Rating rating points gained/lost |
| performance_score | Overall performance rating |
| individual_impact | Player's impact on match outcome |

### player_matchup_history.csv (Phase 4) 🚧
Historical head-to-head matchup statistics

| Column | Description |
|--------|-------------|
| player1 | First player identifier |
| player2 | Second player identifier |
| total_encounters | Times these players faced each other |
| player1_wins | Encounters won by player1 |
| player2_wins | Encounters won by player2 |
| average_rating_diff | Average rating difference |

---

## Configuration

### Logging

Logging is configured in `source/logger.py`. Logs capture:
- **INFO**: Major operations (match creation, file generation)
- **DEBUG**: Detailed flow (round processing, team assignments)
- **ERROR**: Exceptions and failures

Check the application logs to debug issues or understand execution flow.

### API Rate Limiting

The Valorant API may have rate limits. If experiencing API errors:
1. Check your internet connection
2. Wait before retrying
3. Consider caching API responses for repeated runs

### Customization

**To modify match generation logic:**
- Edit functions in `source/components/matchTimeline.py`
- Adjust probability distributions in event simulation
- Modify team size, rounds per match, etc.

**To add new data sources:**
- Create new transformer in `source/components/jsonToPdTransformer/`
- Add API client method in `source/components/apiClient/`
- Update `main.py` to include new data

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -e .` to install package in editable mode |
| API connection error | Check internet, verify Valorant API is accessible |
| InvalidIndexError | Occurs with non-aligned DataFrame indices - update to latest version |
| Memory error with large datasets | Process matches in smaller batches, increase available RAM |

---

## Roadmap

### Phase 1: Core Foundation ✅ (Current)
- [x] Valorant API integration
- [x] Match data generation
- [x] Basic round simulation (25 rounds)
- [x] Team assignment and side mechanics
- [x] Kill/death event simulation
- [x] Spike plant/defuse logic
- [x] Player performance metrics
- [x] Comprehensive logging

### Phase 2: Economy & Weapons 🚧 (In Progress)
- [ ] **Weapon Economy System**
  - Implement credit system per round (starting credits: 800)
  - Track team economy state (full buy, eco, half-buy)
  - Implement reset mechanics
  
- [ ] **Weapon Selection Logic**
  - Assign weapons to players based on economy
  - Implement weapon choice algorithms
  - Track weapon usage statistics
  - Generate weapon_usage.csv output
  
- [ ] **Damage Model Enhancement**
  - Implement armor/shield mechanics
  - Body part-specific damage multipliers (head 1.25x, leg 0.75x)
  - Weapon-specific damage profiles
  - Range-based damage falloff

### Phase 3: Advanced Game Mechanics 📋 (Planned)
- [ ] **Match Summary Logic**
  - Aggregate match statistics
  - Calculate impact scores per player
  - Determine MVP (Most Valuable Player)
  - Generate match_summary.csv output

- [ ] **Player Progression System**
  - Track rank progression within matches
  - Implement RR (Rating Rating) gain/loss logic
  - Handle rank tier advancement/demotion
  - Generate player_progression.csv output

- [ ] **Ability & Agent Selection**
  - Integrate agent abilities into damage calculations
  - Implement ability cooldowns and charges
  - Track ability usage per round

### Phase 4: Matchmaking & Ranking 🎯 (Planned)
- [ ] **Rank-Based Matching**
  - Implement matchmaking algorithm by rank tier
  - Balance team compositions by average rank
  - Generate team balance metrics
  
- [ ] **Skill Rating System**
  - Implement true skill or Elo-based ranking
  - Track historical player ratings
  - Generate ranking progression reports

### Phase 5: Analytics & Output 📊 (Planned)
- [ ] **Enhanced Data Output**
  - Economy statistics per team/player
  - Weapon usage heatmaps
  - Position-based kill statistics
  - Round economy decisions and outcomes
  - Rank progression tracking
  - Player matchup history
  
- [ ] **Report Generation**
  - Automated match reports with summaries
  - Performance trend analysis
  - Player comparison reports
  - Meta analysis dashboards

### Phase 6: ML & Modeling 🤖 (Planned)
- [ ] **Training Data Preparation**
  - Feature engineering for ML models
  - Balanced dataset generation
  - Cross-validation split utilities
  
- [ ] **Reference Models**
  - Win probability predictor
  - Player PPA (Performance Per Agent) estimator
  - Rank progression forecaster
  - Economic state impact analyzer

---

## License

This project is provided as-is for educational and analytical purposes.

---

## Contributing

To contribute to the project:

### Getting Started
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/description`
3. Implement your changes following the architecture guidelines
4. Test thoroughly: `python -m pytest`
5. Commit with clear, descriptive messages
6. Push to your branch and create a Pull Request

### Development Areas Seeking Contributions

#### 🎯 Priority Areas
- **Weapon Economy System**: Implement credit tracking and buy state logic
- **Advanced Damage Mechanics**: Add armor effects, damage multipliers per body part
- **Match Summary Generation**: Aggregate statistics and MVP determination
- **Rank Progression**: Build tier advancement and RR calculation

#### 💡 Contribution Guidelines
- Follow the existing code structure and naming conventions
- Add comprehensive logging using `source.logger`
- Include error handling with `CustomException`
- Write unit tests for new functions
- Update the README with new features/data outputs
- Maintain data integrity with `.reset_index(drop=True)` operations

#### 📋 Code Standards
- Use type hints in function signatures
- Document functions with docstrings
- Keep functions focused on single responsibilities
- Add logging at INFO level for major operations, DEBUG for detailed flow
- Handle edge cases (empty DataFrames, missing columns, etc.)

#### 🔄 Testing Before PR
```bash
# Run basic imports
python -c "from source.components.matchTimeline import generate_all_match_details"

# Test end-to-end
python test_reindex_fix.py

# Check for syntax errors
python -m py_compile source/components/matchTimeline.py
```

#### 📝 Documentation
When adding new features, update:
- This README with feature description and usage
- Function docstrings with parameters and return values
- Logging messages to guide debugging
- Data Output section with new CSV schema