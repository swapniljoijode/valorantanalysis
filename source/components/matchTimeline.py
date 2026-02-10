import pandas as pd
from typing import List, Dict, Any
import numpy as np
import sys
from source.utils import biased_hbl_percentages, divide_number_randomly
from source.exceptions import CustomException
from source.logger import logging
#from src.components.users import synthetic_users

#generating match timeline initial data

def generate_all_match_details(
    users_df: pd.DataFrame,
    agents_df: pd.DataFrame,
    maps_df: pd.DataFrame,
    per_day_match_counter: int = 2,
    start_date: str = "2025-01-01",
    end_date: str = "today",
) -> pd.DataFrame:
    """
    Create a base dataframe of matches:
      - date range from start_date to end_date (daily)
      - per_day_match_counter matches per day
      - each match: 10 unique users, 10 unique agents, 1 map, sides assigned
    """
    try:
        logging.info("Starting generate_all_match_details")
        logging.debug(f"Input shapes - users: {users_df.shape}, agents: {agents_df.shape}, maps: {maps_df.shape}")

        # Date handling
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date).normalize()
        all_rows = []
        match_seq = 1  # incremental match id

    # Pre-filter playable agents
        if "isPlayable" in agents_df.columns:
            playable_agents = agents_df[agents_df["isPlayable"] == True].copy()
        else:
            playable_agents = agents_df.copy()

        N_PLAYERS = 10

        for date in pd.date_range(start=start_dt, end=end_dt):

            # Only players who have joined on or before this date
            eligible_users = users_df[users_df["join_date"] <= date]
            if len(eligible_users) < N_PLAYERS:
                # Not enough players yet, skip this date
                continue

            for _ in range(per_day_match_counter):
                # ----------------------------
                # 1. Sample 10 players
                # ----------------------------
                match_players = eligible_users.sample(
                    n=N_PLAYERS, replace=False
                ).reset_index(drop=True)

                # ----------------------------
                # 2. Sample 10 agents
                # ----------------------------
                if len(playable_agents) < N_PLAYERS:
                    raise ValueError("Not enough playable agents to assign uniquely.")

                agents_sample = playable_agents.sample(
                    n=N_PLAYERS, replace=False
                ).reset_index(drop=True)

                # Use your actual columns: adjust if they differ
                # Common API columns: uuid, displayName
                match_players["agent_id"]   = agents_sample["uuid"]
                match_players["agent_name"] = agents_sample.get(
                    "displayName", agents_sample.get("name", "")
                )

                # ----------------------------
                # 3. Sample a map for the match
                # ----------------------------
                if maps_df.empty:
                    raise ValueError("maps_df is empty.")

                match_map = maps_df.sample(n=1).reset_index(drop=True)
                match_players["map_id"]   = match_map.loc[0, "uuid"]
                match_players["map_name"] = match_map.loc[0, "name"]

                """# ----------------------------
                # 4. Assign sides: 5 attackers, 5 defenders
                # ----------------------------
                attack_indices = np.random.choice(
                    match_players.index, size=5, replace=False
                )
                match_players["is_attacker"] = 0
                match_players.loc[attack_indices, "is_attacker"] = 1
                match_players["is_defender"] = 1 - match_players["is_attacker"]"""

                # ----------------------------
                # 5. Add match metadata
                # ----------------------------
                match_id = f"MATCH_{match_seq:06d}"
                match_players["match_id"]   = match_id
                match_players["match_date"] = date.normalize()

                all_rows.append(match_players)
                logging.info(f"Created match {match_id} on {date.normalize()}")
                match_seq += 1

        if not all_rows:
            logging.warning("No match rows generated. Returning empty DataFrames.")
            # Return 5 empty DataFrames if no data
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        base_matches_df = pd.concat(all_rows, ignore_index=True)
        logging.info(f"Concatenated {len(all_rows)} match rows with shape {base_matches_df.shape}")

        # Optional: enforce column order
        cols_order = [
            "match_id",
            "match_date",
            "user_id",
            "agent_id",
            "agent_name",
            "map_id",
            "map_name",
            "join_date",   # from users_df
            # other user columns (username, etc.) will follow
        ]
        base_matches_df = base_matches_df[
            [c for c in cols_order if c in base_matches_df.columns] +
            [c for c in base_matches_df.columns if c not in cols_order]
        ]
        logging.info(f"Basic Match details generated")

        match_df = pd.DataFrame()
        match_status_list = []
        round_status_list = []
        agent_perf_status_list = []
        round_spike_status_list = []
        
        for m_id in base_matches_df["match_id"].unique():
            logging.debug(f"Processing match {m_id}")
            match_data = base_matches_df[base_matches_df["match_id"] == m_id].reset_index(drop=True)
            match_df = pd.concat([match_df, team_division(match_data)], ignore_index=True)
            match_data_filtered = match_df[match_df["match_id"] == m_id].reset_index(drop=True)
            match_status_per_match, round_status_per_match, agent_perf_status_per_match, round_spike_status_per_match = generating_full_match_details_per_round(
                match_df=match_data_filtered, agents_df=agents_df
            )
            match_status_list.append(match_status_per_match.reset_index(drop=True))
            round_status_list.append(round_status_per_match.reset_index(drop=True))
            agent_perf_status_list.append(agent_perf_status_per_match.reset_index(drop=True))
            round_spike_status_list.append(round_spike_status_per_match.reset_index(drop=True))
        
        # Concatenate all results at once
        match_status = pd.concat(match_status_list, ignore_index=True) if match_status_list else pd.DataFrame()
        round_status = pd.concat(round_status_list, ignore_index=True) if round_status_list else pd.DataFrame()
        agent_perf_status = pd.concat(agent_perf_status_list, ignore_index=True).reset_index(drop=True) if agent_perf_status_list else pd.DataFrame()
        round_spike_status = pd.concat(round_spike_status_list, ignore_index=True) if round_spike_status_list else pd.DataFrame()
        
        logging.info(f"Successfully completed generate_all_match_details")
        return match_status,round_status,agent_perf_status,round_spike_status, match_df
    
    except CustomException as e:
        logging.error(f"CustomException in generate_all_match_details: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error in generate_all_match_details: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)

def team_division (
        match_df: pd.DataFrame,
        rounds_per_match: int = 25)-> pd.DataFrame:
    """
    For each match in match_df, generate round details:
        - rounds_per_match rounds
        - for each round: winning side (attackers/defenders)
    """
    try:
        logging.debug(f"team_division: Dividing teams for {len(match_df)} players")
        match_df = match_df.copy().reset_index(drop=True)
        teamside = np.random.choice(
            match_df.index, size=5, replace=False
            )
        match_df["team A"] = 0
        match_df.loc[teamside, "team A"] = 1
        match_df["team B"] = 1 - match_df["team A"]
        logging.debug(f"team_division: Team A: {match_df['team A'].sum()}, Team B: {match_df['team B'].sum()}")
        return match_df
    except Exception as e:
        error_msg = f"Error in team_division: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)

def team_side_assignment(
        match_df: pd.DataFrame,
        round_number: int
        ) -> pd.DataFrame:
    """
    Assign team sides (Attackers/Defenders) for each match
    """
    try:
        logging.debug(f"team_side_assignment: Assigning sides for round {round_number}")
        match_df = match_df.copy().reset_index(drop=True)
        if round_number == 1:
            
            match_df["isAttacker"] = match_df.apply(
                lambda x: 1 if x["team A"] == 1 else 0, axis=1
                )
            match_df["isDefender"] = 1 - match_df["isAttacker"]
            logging.debug(f"Round 1: Attackers: {match_df['isAttacker'].sum()}, Defenders: {match_df['isDefender'].sum()}")
        elif round_number == 13:
            match_df["isAttacker"] = 1 - match_df["isAttacker"]
            match_df["isDefender"] = 1 - match_df["isAttacker"]
            logging.debug(f"Round 13: Sides swapped. Attackers: {match_df['isAttacker'].sum()}, Defenders: {match_df['isDefender'].sum()}")
        return match_df
    except Exception as e:
        error_msg = f"Error in team_side_assignment: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)

def generating_full_match_details_per_round(
        match_df: pd.DataFrame,
        agents_df: pd.DataFrame,
        total_rounds: int = 25,
        first_round_credit: int = 800,
        attacker_round_wins: int = 0,
        defender_round_wins: int = 0,
        match_duration: int = np.random.randint(1500, 2400) # Match duration between 25 to 40 minutes
        )-> pd.DataFrame:
    """
    For each match in match_df, generate full round details:
        - rounds_per_match rounds
        - for each round: winning side (attackers/defenders)
    """
    try:
        match_id = match_df['match_id'].iloc[0] if len(match_df) > 0 else "UNKNOWN"
        logging.info(f"generating_full_match_details_per_round: Starting for match {match_id} with {total_rounds} rounds")
        match_details = []
        round_details = []
        round_durations = {}
        round_spike_status = pd.DataFrame()
        agent_perf_status = pd.DataFrame()
        for i in range (1, total_rounds + 1):
            round_id = f"{match_df['match_id'].iloc[0]}-R{i:02d}"
            logging.debug(f"Processing round {i}/{total_rounds}: {round_id}")

            if i == 1 or i==13:
                match_df = team_side_assignment(
                    match_df,
                    round_number=i
                    )
            
            for row in match_df.itertuples(index=False):
                row_dict = dict(zip(match_df.columns, row))
                row_dict["round_id"] = round_id
                match_details.append(row_dict)

            round_stats, round_spike_stat, attacker_round_win, defender_round_win, total_duration_round, agent_performance = events_per_round(round_df=pd.DataFrame(match_details)[pd.DataFrame(match_details)["round_id"]==round_id].reset_index(drop=True))
            round_details.extend(round_stats)
            agent_perf_status = pd.concat([agent_perf_status,agent_performance],axis=0, ignore_index=True)
            round_spike_status = pd.concat([round_spike_status,round_spike_stat],axis=0, ignore_index=True)
            attacker_round_wins+= attacker_round_win
            defender_round_wins+= defender_round_win
            round_durations[round_id] = total_duration_round
            logging.debug(f"Round {i} - Attackers: {attacker_round_wins} wins, Defenders: {defender_round_wins} wins")

            if attacker_round_wins == 13 or defender_round_wins == 13:
                logging.info(f"Match {match_id} ended in round {i}. Attackers: {attacker_round_wins}, Defenders: {defender_round_wins}")
                break

        match_status = pd.DataFrame(round_details)["match_id"].drop_duplicates().reset_index(drop=True).to_frame()
        match_status["attacker_round_wins"] = attacker_round_wins
        match_status["defender_round_wins"] = defender_round_wins
        
        round_df = pd.DataFrame(round_details)
        round_status = round_df[["match_id","round_id"]].drop_duplicates().reset_index(drop=True)
        round_status["total_round_duration"] = round_status["round_id"].map(round_durations)

        logging.info(f"Match details completed - {len(round_status)} rounds")
        return match_status, round_status, agent_perf_status, round_spike_status
    
    except Exception as e:
        error_msg = f"Error in generating_full_match_details_per_round: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)




# function to generate kill/death/plant/diffuse/etc events per round for each user.
def events_per_round(
        round_df: pd.DataFrame,
        attackers_alive: int = 5,
        defenders_alive: int = 5,
        ) -> Dict[str, Any]:
    """
    For each round in match_df, generate event details:
        - kills, deaths, plants, defuses, etc.
    """
    try:
        round_id = round_df['round_id'].iloc[0] if len(round_df) > 0 and 'round_id' in round_df.columns else "UNKNOWN"
        logging.debug(f"events_per_round: Processing {round_id}")
        records = []
    
        attacker_team = round_df[round_df["isAttacker"]==1]["agent_name"].tolist()
        defender_team = round_df[round_df["isDefender"]==1]["agent_name"].tolist()


        attacker_dict = {agent:250 for agent in round_df[round_df["isAttacker"]==1]["agent_name"].tolist()}
        defender_dict = {agent:250 for agent in round_df[round_df["isDefender"]==1]["agent_name"].tolist()}

        kill_count_attacker = {agent:0 for agent in round_df[round_df["isAttacker"]==1]["agent_name"].tolist()}
        kill_count_defender = {agent:0 for agent in round_df[round_df["isDefender"]==1]["agent_name"].tolist()}

        
        agents_hit_damage = {agent:{ag: {"hit": {"head":0, "body":0, "leg":0},"damage":{"head":0,"body":0,"leg":0},"outgoing_damage":0, "incoming_damage":0} for ag in attacker_team+defender_team } for agent in attacker_team+defender_team}

        dead_attackers = []
        dead_defenders = []

        round_timer_expired = 0
        total_duration_round = None
        spike_detonated = 0
        team_spike_planted = None
        team_spike_diffused = None
        team_spike_detonated = None


        for row in round_df.itertuples(index=False):
            row_dict = dict(zip(round_df.columns, row))

            row_dict, attacker_dict, defender_dict, team_spike_planted, team_spike_diffused, kill_count_attacker, kill_count_defender, attackers_alive, defenders_alive, agents_hit_damage = kill_death_simulation_by_damage(
                row_dict=row_dict,
                attacker_dict=attacker_dict,
                defender_dict=defender_dict,
                kill_count_attacker=kill_count_attacker,
                kill_count_defender=kill_count_defender,
                attackers_alive=attackers_alive,
                defenders_alive=defenders_alive,
                team_spike_planted=team_spike_planted,
                team_spike_diffused=team_spike_diffused,
                agent_hit_damage=agents_hit_damage
            )        
            records.append(row_dict)


        if team_spike_planted == 1:
            if team_spike_diffused == 1:
                attacker_round_win = 0
                defender_round_win = 1
            else:
                attacker_round_win = 1
                defender_round_win = 0
                round_timer_expired = 1
                spike_detonated = 1
        else: # no spike planted
            if attackers_alive > defenders_alive:
                attacker_round_win = 1
                defender_round_win = 0
            
            else:
                attacker_round_win = 0
                defender_round_win = 1
                round_timer_expired = 1

        total_duration_round = compute_round_duration_seconds(
            spike_planted = team_spike_planted,
            spike_defused = team_spike_diffused,
            spike_detonated = spike_detonated,
            round_timer_expired = round_timer_expired
        )

        #round_per_agent_df = round_df[["match_id","round_id","agent_name","isAttacker","isDefender"]].drop_duplicates().reset_index(drop=True)
        round_summary = round_df[["match_id","round_id","agent_name","isAttacker","isDefender"]].drop_duplicates().reset_index(drop=True)
        # 1. Filter for attackers and create the base summary
        attackers = round_summary[round_summary["isAttacker"] == 1].copy()
        defender = round_summary[round_summary["isDefender"] == 1].copy()
        # 2. Perform a cross join to pair every attacker with every defender
        # Note: how="cross" requires pandas 1.2.0+
        defenders_df = pd.DataFrame({"opponent": defender_team})
        attackers_df = pd.DataFrame({"opponent": attacker_team})
        agent_perf_per_round_attk = attackers.merge(defenders_df, how="cross")
        agent_perf_per_round_def = defender.merge(attackers_df, how="cross")
        agent_perf_per_round = pd.concat([agent_perf_per_round_attk,agent_perf_per_round_def],axis = 0, ignore_index=True)
        # 3. Define a vectorized lookup helper
        def get_stats(row):
            # Navigates your agents_hit_damage[attacker][defender] structure
            stats = agents_hit_damage.get(row["agent_name"], {}).get(row["opponent"], {})
            
            # Return a Series so it expands into multiple columns automatically
            return pd.Series({
                "head_hit": stats.get("hit", {}).get("head", 0),
                "body_hit": stats.get("hit", {}).get("body", 0),
                "leg_hit": stats.get("hit", {}).get("leg", 0),
                "head_damage": stats.get("damage", {}).get("head", 0),
                "body_damage": stats.get("damage", {}).get("body", 0),
                "leg_damage": stats.get("damage", {}).get("leg", 0),
            })

        # 4. Apply the mapping to the whole dataframe
        stat_cols = agent_perf_per_round.apply(get_stats, axis=1)
        # Ensure stat_cols has the same index as agent_perf_per_round
        stat_cols.index = agent_perf_per_round.index
        agent_perf_per_round = pd.concat([agent_perf_per_round.reset_index(drop=True), stat_cols.reset_index(drop=True)], axis=1)

        round_spike_status = round_summary[["match_id","round_id"]].drop_duplicates().reset_index(drop = True)
        round_spike_status["spike_planted"] = team_spike_planted
        round_spike_status["spike_defused"] = team_spike_diffused
        logging.debug(f"Round {round_id} completed - Spike planted: {team_spike_planted}, Spike defused: {team_spike_diffused}")
            
        return records, round_spike_status, attacker_round_win, defender_round_win, total_duration_round, agent_perf_per_round
    
    except Exception as e:
        error_msg = f"Error in events_per_round: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def compute_round_duration_seconds(
    spike_planted: int,
    spike_defused: int,
    spike_detonated: int,
    round_timer_expired: int,
    random_state = np.random,
    min_instant_round: float = 15.0,
) -> float:
    """
    Compute total_duration_round (seconds) given spike/timer outcomes.

    Assumptions (Unrated/Competitive):
    - Base round timer (no spike): up to ~100s.
    - Spike fuse: ~45s from plant to explosion.
    - Full defuse takes ~7s, so last viable full defuse is ~38s after plant.

    Parameters
    ----------
    spike_planted : bool
    spike_detonated : bool
    spike_defused : bool
    round_timer_expired : bool
        True if round ended because timer hit 0 BEFORE a spike plant.
    random_state : np.random.RandomState
    min_instant_round : float
        Hard lower bound to avoid absurdly short rounds.

    Returns
    -------
    float
        total_duration_round in seconds.
    """
    try:
        # ----------------------------
        # Case 1: No spike was planted
        # ----------------------------
        if not spike_planted:
            # If timer expired, the round must reach near the max round time
            if round_timer_expired:
                # End very close to the 100s round clock.
                duration = random_state.uniform(90.0, 100.0)
            else:
                # Team wipe / early push / save – can end anytime from a fast stomp to full time.
                duration = random_state.uniform(min_instant_round, 100.0)
            logging.debug(f"Round duration (no spike): {duration}s")
            return duration

        # ----------------------------
        # Case 2: Spike planted and detonated
        # ----------------------------
        if spike_detonated:
            # Time until plant: attackers need some time to take site.
            # Model plant happening between 20 and 100 seconds.
            time_until_plant = random_state.uniform(20.0, 100.0)

            # Fuse time: up to ~45s, usually close to full when it detonates.
            fuse_time = random_state.uniform(35.0, 45.0)

            total = time_until_plant + fuse_time

            # Hard cap at about 145s (100s round + 45s fuse).
            total = max(min_instant_round, min(total, 145.0))
            logging.debug(f"Round duration (spike detonated): {total}s")
            return total

        # ----------------------------
        # Case 3: Spike planted and defused
        # ----------------------------
        if spike_defused:
            # Time until plant: again between 20 and 100s in most rounds.
            time_until_plant = random_state.uniform(20.0, 90.0)

            # Time from plant to defuse:
            # - Earliest "ninja" defuses can be very fast (few seconds).
            # - Latest successful full defuse is ~38s after plant (45 - 7).
            #
            # We'll model typical successful defuses happening between 5 and 35s after plant.
            time_until_defuse = random_state.uniform(5.0, 35.0)

            total = time_until_plant + time_until_defuse

            # Safety clamps
            if total < min_instant_round:
                total = min_instant_round
            if total > 140.0:
                total = 140.0

        logging.debug(f"Round duration (spike defused): {total}s")
        # ----------------------------
        duration = random_state.uniform(80.0, 100.0)
        return max(min_instant_round, duration)
    
    except Exception as e:
        error_msg = f"Error in events_per_roundround timer generation: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)



def kill_death_simulation_by_damage(
        row_dict: Dict[str, Any],
        attacker_dict: Dict[str, int],
        defender_dict: Dict[str, int],
        kill_count_attacker: Dict[str, int],
        kill_count_defender: Dict[str, int],
        team_spike_planted: int,
        team_spike_diffused: int,
        attackers_alive: int,
        defenders_alive: int,
        agent_hit_damage: Dict
)->Dict[str, Any]:
    
    try:
        kill = 0
        death = 0
        
        if row_dict["isAttacker"] == 1:
            spike_planted = np.random.choice([0,1], p=[0.3,0.7]) if team_spike_planted != 1 else 0
            row_dict["plants"] = spike_planted
            team_spike_planted = spike_planted if team_spike_planted is None or team_spike_planted == 0 else team_spike_planted
            for agent,health in defender_dict.items():
                attacker_agent_health = attacker_dict.get(row_dict["agent_name"])
                hit_value = np.random.randint(0,health+1)
                damage_value = np.random.randint(0,attacker_agent_health+1)
                head_hit_pct, body_hit_pct, leg_hit_pct = biased_hbl_percentages(value = hit_value)
                head_damage_pct, body_damage_pct, leg_damage_pct = biased_hbl_percentages(value = damage_value)
                
                #attacker hit and damage pct per agent
                
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["head"] = head_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["body"] = body_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["leg"] = leg_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["head"] = head_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["body"] = body_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["leg"] = leg_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["outgoing_damage"] = hit_value
                agent_hit_damage[(row_dict["agent_name"])][agent]["incoming_damage"] = damage_value

                
                if damage_value >= attacker_agent_health and attacker_agent_health >0:
                    attacker_dict[row_dict["agent_name"]] = 0
                    death = 1
                    kill_count_defender[agent] +=1
                    defenders_alive -= 1
                    
                else:
                    attacker_dict[row_dict["agent_name"]] = attacker_agent_health - damage_value

                if hit_value >= health and health >0:
                    defender_dict[agent] = 0
                    kill_count_attacker[row_dict["agent_name"]] +=1
                    kill = kill_count_attacker[row_dict["agent_name"]]
                    attackers_alive -= 1
                else:
                    defender_dict[agent] = health - hit_value

        elif row_dict["isDefender"] == 1:
            spike_diffused = np.random.choice([0,1], p=[0.8,0.2]) if team_spike_planted == 1 and (team_spike_diffused is None or team_spike_diffused == 0) else 0
            row_dict["defussed"] = spike_diffused
            team_spike_diffused = spike_diffused if team_spike_diffused is None or team_spike_diffused == 0 else team_spike_diffused
            for agent,health in attacker_dict.items():
                defender_agent_health = defender_dict.get(row_dict["agent_name"])
                hit_value = np.random.randint(0,health+1)
                damage_value = np.random.randint(0,defender_agent_health+1)
                head_hit_pct, body_hit_pct, leg_hit_pct = biased_hbl_percentages(value = hit_value)
                head_damage_pct, body_damage_pct, leg_damage_pct = biased_hbl_percentages(value = damage_value)
                
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["head"] = head_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["body"] = body_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["hit"]["leg"] = leg_hit_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["head"] = head_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["body"] = body_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["damage"]["leg"] = leg_damage_pct
                agent_hit_damage[(row_dict["agent_name"])][agent]["outgoing_damage"] = hit_value
                agent_hit_damage[(row_dict["agent_name"])][agent]["incoming_damage"] = damage_value
                
                if damage_value >= defender_agent_health and defender_agent_health >0:
                    defender_dict[row_dict["agent_name"]] = 0
                    death = 1
                    kill_count_attacker[agent] +=1
                    attackers_alive -= 1
                    
                else:
                    defender_dict[row_dict["agent_name"]] = defender_agent_health - damage_value

                if hit_value >= health and health:
                    attacker_dict[agent] = 0
                    kill_count_defender[row_dict["agent_name"]] +=1
                    kill = kill_count_defender[row_dict["agent_name"]]
                    defenders_alive -= 1
                else:
                    attacker_dict[agent] = health - hit_value
        row_dict["kills"] = kill
        row_dict["death"] = death

        return row_dict, attacker_dict, defender_dict, team_spike_planted, team_spike_diffused, kill_count_attacker, kill_count_defender, attackers_alive, defenders_alive, agent_hit_damage

    except Exception as e:
        error_msg = f"Error in kill_deat_simulation: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


if __name__ == "__main__":
    try:
        logging.info("=" * 80)
        logging.info("Starting Valorant Match Timeline Generation")
        logging.info("=" * 80)
        
        logging.info("Loading input CSV files...")
        users_df = pd.read_csv("data/users_dim.csv", parse_dates=["join_date"])
        agents_df = pd.read_csv("data/agents_dim.csv")
        maps_df = pd.read_csv("data/maps_dim.csv")
        logging.info(f"Successfully loaded input files - users: {users_df.shape}, agents: {agents_df.shape}, maps: {maps_df.shape}")
        
        logging.info("Generating match timeline...")
        match_status, round_status, agent_perf_status, round_spike_status, match_df = generate_all_match_details(
            users_df,
            agents_df,
            maps_df
        )
        
        logging.info("Writing output CSV files...")
        match_status.to_csv("data/match_status.csv", index=False)
        logging.info(f"Saved match_status to data/match_status.csv (shape: {match_status.shape})")
        
        round_status.to_csv("data/round_status.csv", index=False)
        logging.info(f"Saved round_status to data/round_status.csv (shape: {round_status.shape})")
        
        agent_perf_status.to_csv("data/agent_perf_status.csv", index=False)
        logging.info(f"Saved agent_perf_status to data/agent_perf_status.csv (shape: {agent_perf_status.shape})")
        
        round_spike_status.to_csv("data/round_spike_status.csv", index=False)
        logging.info(f"Saved round_spike_status to data/round_spike_status.csv (shape: {round_spike_status.shape})")
        
        logging.info("=" * 80)
        logging.info("Match Timeline Generation Completed Successfully!")
        logging.info("=" * 80)
        
    except CustomException as e:
        logging.error(f"CustomException occurred: {str(e)}")
        logging.error("=" * 80)
        raise
    except Exception as e:
        error_msg = f"Unexpected error in main execution: {str(e)}"
        logging.error(error_msg)
        logging.error("=" * 80)
        raise