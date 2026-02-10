import pandas as pd
from typing import List, Dict, Any, Tuple
import numpy as np
import sys
from source.utils import biased_hbl_percentages, divide_number_randomly
from source.exceptions import CustomException
from source.logger import logging


def generate_all_match_details(
        users_df: pd.DataFrame,
        agents_df: pd.DataFrame,
        maps_df: pd.DataFrame,
        num_matches: int = 5,
        start_date: str = "2023-01-01",
        end_date: str = "2024-12-31"
        ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate match timelines and all associated data.
    
    Returns: (match_status, round_status, agent_perf_status, round_spike_status, base_matches_df)
    """
    try:
        logging.info("generate_all_match_details: Starting")
        logging.debug(f"Input shapes - users: {users_df.shape}, agents: {agents_df.shape}, maps: {maps_df.shape}")
        
        # Prepare data
        playable_agents = agents_df.copy()
        logging.debug(f"Number of playable agents: {len(playable_agents)}")
        
        start_pd = pd.to_datetime(start_date)
        end_pd = pd.to_datetime(end_date)
        logging.info(f"Date range: {start_pd} to {end_pd}")
        
        all_rows = []
        match_seq = 1
        
        # Generate matches across date range
        for date in pd.date_range(start=start_pd, end=end_pd, freq='D'):
            daily_users = users_df[users_df["join_date"] <= date]
            if len(daily_users) < 10:
                logging.debug(f"Skipping {date.date()}: insufficient users ({len(daily_users)})")
                continue
            
            daily_users = daily_users.sample(n=min(len(daily_users), 10), replace=False)
            
            for _ in range(num_matches):
                match_id = f"MATCH-{match_seq:06d}"
                
                # Select 10 random players
                match_players = daily_users.sample(n=min(len(daily_users), 10), replace=False).reset_index(drop=True)
                
                # Select agents and map
                selected_agents = playable_agents.sample(n=len(match_players), replace=True).reset_index(drop=True)
                selected_map = maps_df.sample(n=1).iloc[0] if len(maps_df) > 0 else None
                
                if selected_map is None:
                    logging.warning(f"No maps available for match {match_id}")
                    continue
                
                # Merge data
                match_players["match_id"] = match_id
                match_players["match_date"] = date.normalize()
                match_players["agent_id"] = selected_agents["uuid"].values if "uuid" in selected_agents.columns else selected_agents.index
                match_players["agent_name"] = selected_agents.get("displayName", selected_agents.get("name", "")).values
                match_players["map_id"] = selected_map["uuid"]
                match_players["map_name"] = selected_map["name"]
                
                all_rows.append(match_players)
                logging.info(f"Created match {match_id} on {date.normalize()}")
                match_seq += 1
        
        logging.info(f"Generated {len(all_rows)} total matches")
        
        if not all_rows:
            logging.warning("No match rows generated. Returning empty DataFrames.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        base_matches_df = pd.concat(all_rows, ignore_index=True)
        logging.info(f"Concatenated {len(all_rows)} match rows into base_matches_df with shape {base_matches_df.shape}")
        
        # Enforce column order
        cols_order = [
            "match_id", "match_date", "user_id", "agent_id", "agent_name", "map_id", "map_name", "join_date"
        ]
        base_matches_df = base_matches_df[
            [c for c in cols_order if c in base_matches_df.columns] +
            [c for c in base_matches_df.columns if c not in cols_order]
        ]
        logging.info(f"Basic match details generated")
        logging.debug(f"Columns: {list(base_matches_df.columns)}")
        
        # Process matches
        match_status_list = []
        round_status_list = []
        agent_perf_status_list = []
        round_spike_status_list = []
        
        total_matches = len(base_matches_df["match_id"].unique())
        logging.info(f"Processing {total_matches} unique matches")
        
        match_df = pd.DataFrame()
        for idx, m_id in enumerate(base_matches_df["match_id"].unique(), 1):
            logging.debug(f"Processing match {idx}/{total_matches}: {m_id}")
            match_data = base_matches_df[base_matches_df["match_id"] == m_id].reset_index(drop=True)
            match_df = pd.concat([match_df, team_division(match_data)], ignore_index=True)
            
            match_status_per_match, round_status_per_match, agent_perf_status_per_match, round_spike_status_per_match = generating_full_match_details_per_round(
                match_df=match_df[match_df["match_id"] == m_id].reset_index(drop=True),
                agents_df=agents_df
            )
            
            match_status_list.append(match_status_per_match.reset_index(drop=True))
            round_status_list.append(round_status_per_match.reset_index(drop=True))
            agent_perf_status_list.append(agent_perf_status_per_match.reset_index(drop=True))
            round_spike_status_list.append(round_spike_status_per_match.reset_index(drop=True))
        
        # Concatenate all results at once
        match_status = pd.concat(match_status_list, ignore_index=True) if match_status_list else pd.DataFrame()
        round_status = pd.concat(round_status_list, ignore_index=True) if round_status_list else pd.DataFrame()
        agent_perf_status = pd.concat(agent_perf_status_list, ignore_index=True) if agent_perf_status_list else pd.DataFrame()
        round_spike_status = pd.concat(round_spike_status_list, ignore_index=True) if round_spike_status_list else pd.DataFrame()
        
        logging.info(f"Final output shapes - match_status: {match_status.shape}, round_status: {round_status.shape}, agent_perf_status: {agent_perf_status.shape}, round_spike_status: {round_spike_status.shape}")
        logging.info(f"Successfully completed generate_all_match_details")
        
        return match_status, round_status, agent_perf_status, round_spike_status, match_df
    
    except CustomException as e:
        logging.error(f"CustomException in generate_all_match_details: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error in generate_all_match_details: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def team_division(match_df: pd.DataFrame, rounds_per_match: int = 25) -> pd.DataFrame:
    """
    For each match in match_df, divide players into Team A and Team B.
    """
    try:
        logging.debug(f"team_division: Dividing teams for {len(match_df)} players")
        match_df = match_df.copy()
        
        if len(match_df) < 5:
            error_msg = f"team_division: Need at least 5 players for team division, got {len(match_df)}"
            logging.error(error_msg)
            raise CustomException(error_msg, sys)
        
        teamside = np.random.choice(match_df.index, size=5, replace=False)
        match_df["team A"] = 0
        match_df.loc[teamside, "team A"] = 1
        match_df["team B"] = 1 - match_df["team A"]
        
        logging.debug(f"team_division: Team A: {match_df['team A'].sum()}, Team B: {match_df['team B'].sum()}")
        return match_df
    
    except CustomException as e:
        logging.error(f"CustomException in team_division: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error in team_division: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def team_side_assignment(match_df: pd.DataFrame, round_number: int) -> pd.DataFrame:
    """
    Assign team sides (Attackers/Defenders) for each match
    """
    try:
        logging.debug(f"team_side_assignment: Assigning sides for round {round_number}")
        match_df = match_df.copy()
        
        if round_number == 1:
            side_assignment = np.random.choice([0, 1], p=[0.5, 0.5])
            match_df["isAttacker"] = match_df.apply(
                lambda x: side_assignment if x["team A"] == 1 else 1 - side_assignment, axis=1
            )
            match_df["isDefender"] = 1 - match_df["isAttacker"]
            logging.debug(f"Round 1: Initial side assignment. Attackers: {match_df['isAttacker'].sum()}, Defenders: {match_df['isDefender'].sum()}")
        
        elif round_number == 13:
            match_df["isAttacker"] = 1 - match_df["isAttacker"]
            match_df["isDefender"] = 1 - match_df["isDefender"]
            logging.debug(f"Round 13: Sides swapped. Attackers: {match_df['isAttacker'].sum()}, Defenders: {match_df['isDefender'].sum()}")
        
        return match_df
    
    except Exception as e:
        error_msg = f"Error in team_side_assignment for round {round_number}: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def generating_full_match_details_per_round(
        match_df: pd.DataFrame,
        agents_df: pd.DataFrame,
        total_rounds: int = 25,
        first_round_credit: int = 800
        ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    For each match in match_df, generate full round details across 25 rounds.
    """
    try:
        match_id = match_df['match_id'].iloc[0] if len(match_df) > 0 else "UNKNOWN"
        logging.info(f"generating_full_match_details_per_round: Starting for match {match_id} with {total_rounds} rounds")
        
        match_details = []
        round_details = []
        round_durations = {}
        round_spike_status = pd.DataFrame()
        agent_perf_status = pd.DataFrame()
        
        attacker_round_wins = 0
        defender_round_wins = 0
        
        for i in range(1, total_rounds + 1):
            round_id = f"{match_df['match_id'].iloc[0]}-R{i:02d}"
            logging.debug(f"Processing round {i}/{total_rounds}: {round_id}")
            
            # Assign sides at round 1 and 13
            if i == 1 or i == 13:
                match_df = team_side_assignment(match_df, round_number=i)
            
            # Add round_id to match data
            for row in match_df.itertuples(index=False):
                row_dict = dict(zip(match_df.columns, row))
                row_dict["round_id"] = round_id
                match_details.append(row_dict)
            
            # Get round data
            round_df = pd.DataFrame(match_details)
            round_df = round_df[round_df["round_id"] == round_id].reset_index(drop=True)
            
            # Generate events for this round
            round_stats, round_spike_stat, attacker_round_win, defender_round_win, total_duration_round, agent_performance = events_per_round(round_df=round_df)
            
            round_details.extend(round_stats)
            agent_perf_status = pd.concat([agent_perf_status, agent_performance], axis=0, ignore_index=True)
            round_spike_status = pd.concat([round_spike_status, round_spike_stat], axis=0, ignore_index=True)
            
            attacker_round_wins += attacker_round_win
            defender_round_wins += defender_round_win
            round_durations[round_id] = total_duration_round
            
            logging.debug(f"Round {i} stats - Attackers: {attacker_round_wins} wins, Defenders: {defender_round_wins} wins, Duration: {total_duration_round}s")
            
            # Check if match is over (first to 13 wins)
            if attacker_round_wins == 13 or defender_round_wins == 13:
                logging.info(f"Match {match_id} ended in round {i}. Attackers: {attacker_round_wins} wins, Defenders: {defender_round_wins} wins")
                break
        
        match_status = pd.DataFrame(round_details)["match_id"].drop_duplicates().reset_index(drop=True).to_frame()
        match_status["attacker_round_wins"] = attacker_round_wins
        match_status["defender_round_wins"] = defender_round_wins
        
        round_df = pd.DataFrame(round_details)
        round_status = round_df[["match_id", "round_id"]].drop_duplicates().reset_index(drop=True)
        round_status["total_round_duration"] = round_status["round_id"].map(round_durations)
        
        logging.info(f"Match details completed - {len(round_status)} rounds, Attacker wins: {attacker_round_wins}, Defender wins: {defender_round_wins}")
        
        return match_status, round_status, agent_perf_status, round_spike_status
    
    except Exception as e:
        error_msg = f"Error in generating_full_match_details_per_round: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def events_per_round(round_df: pd.DataFrame, attackers_alive: int = 5, defenders_alive: int = 5) -> Tuple[List, pd.DataFrame, int, int, float, pd.DataFrame]:
    """
    For each round, generate event details: kills, deaths, plants, defuses, etc.
    """
    try:
        if len(round_df) == 0:
            logging.warning("events_per_round: Empty round_df provided")
            return [], pd.DataFrame(), 0, 0, 0, pd.DataFrame()
        
        round_id = round_df['round_id'].iloc[0] if 'round_id' in round_df.columns else "UNKNOWN"
        logging.debug(f"events_per_round: Processing {round_id}")
        
        records = []
        
        # Get team composition
        attacker_team = round_df[round_df["isAttacker"] == 1]["agent_name"].tolist()
        defender_team = round_df[round_df["isDefender"] == 1]["agent_name"].tolist()
        
        if len(attacker_team) == 0 or len(defender_team) == 0:
            error_msg = f"events_per_round: Invalid team composition. Attackers: {len(attacker_team)}, Defenders: {len(defender_team)}"
            logging.error(error_msg)
            raise CustomException(error_msg, sys)
        
        logging.debug(f"events_per_round: Attackers: {len(attacker_team)}, Defenders: {len(defender_team)}")
        
        # Initialize damage tracking
        agents_hit_damage = {
            agent: {op: {"hit": {"head": 0, "body": 0, "leg": 0}, "damage": {"head": 0, "body": 0, "leg": 0}, 
                         "outgoing_damage": 0, "incoming_damage": 0} 
                    for op in attacker_team + defender_team}
            for agent in attacker_team + defender_team
        }
        
        # Initialize team dictionaries with agent health (100 HP each)
        attacker_dict = {agent: 100 for agent in attacker_team}
        defender_dict = {agent: 100 for agent in defender_team}
        
        kill_count_attacker = {agent: 0 for agent in attacker_team}
        kill_count_defender = {agent: 0 for agent in defender_team}
        
        # Initialize round outcomes
        team_spike_planted = None
        team_spike_diffused = None
        spike_detonated = 0
        round_timer_expired = 0
        
        # Process each player's actions
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
        
        # Determine round winner
        if team_spike_planted == 1:
            if team_spike_diffused == 1:
                attacker_round_win = 0
                defender_round_win = 1
            else:
                attacker_round_win = 1
                defender_round_win = 0
                spike_detonated = 1
                round_timer_expired = 1
        else:  # no spike planted
            if attackers_alive > defenders_alive:
                attacker_round_win = 1
                defender_round_win = 0
            else:
                attacker_round_win = 0
                defender_round_win = 1
                round_timer_expired = 1
        
        # Compute duration
        total_duration_round = compute_round_duration_seconds(
            spike_planted=team_spike_planted,
            spike_defused=team_spike_diffused,
            spike_detonated=spike_detonated,
            round_timer_expired=round_timer_expired
        )
        
        # Create agent performance data
        round_summary = round_df[["match_id", "round_id", "agent_name", "isAttacker", "isDefender"]].drop_duplicates().reset_index(drop=True)
        attackers = round_summary[round_summary["isAttacker"] == 1].copy()
        defenders = round_summary[round_summary["isDefender"] == 1].copy()
        
        defenders_df = pd.DataFrame({"opponent": defender_team})
        attackers_df = pd.DataFrame({"opponent": attacker_team})
        agent_perf_per_round_attk = attackers.merge(defenders_df, how="cross")
        agent_perf_per_round_def = defenders.merge(attackers_df, how="cross")
        agent_perf_per_round = pd.concat([agent_perf_per_round_attk, agent_perf_per_round_def], axis=0, ignore_index=True)
        
        # Add stats
        def get_stats(row):
            stats = agents_hit_damage.get(row["agent_name"], {}).get(row["opponent"], {})
            return pd.Series({
                "head_hit": stats.get("hit", {}).get("head", 0),
                "body_hit": stats.get("hit", {}).get("body", 0),
                "leg_hit": stats.get("hit", {}).get("leg", 0),
                "head_damage": stats.get("damage", {}).get("head", 0),
                "body_damage": stats.get("damage", {}).get("body", 0),
                "leg_damage": stats.get("damage", {}).get("leg", 0),
            })
        
        stat_cols = agent_perf_per_round.apply(get_stats, axis=1)
        stat_cols.index = agent_perf_per_round.index
        agent_perf_per_round = pd.concat([agent_perf_per_round.reset_index(drop=True), stat_cols.reset_index(drop=True)], axis=1)
        
        # Create spike status data
        round_spike_status_df = round_summary[["match_id", "round_id"]].drop_duplicates().reset_index(drop=True)
        round_spike_status_df["spike_planted"] = team_spike_planted if team_spike_planted is not None else 0
        round_spike_status_df["spike_defused"] = team_spike_diffused if team_spike_diffused is not None else 0
        
        logging.debug(f"Round {round_id} completed - Spike planted: {team_spike_planted}, Spike defused: {team_spike_diffused}, Attacker win: {attacker_round_win}, Defender win: {defender_round_win}")
        
        return records, round_spike_status_df, attacker_round_win, defender_round_win, total_duration_round, agent_perf_per_round
    
    except CustomException as e:
        logging.error(f"CustomException in events_per_round: {str(e)}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error in events_per_round: {str(e)}"
        logging.error(error_msg)
        raise CustomException(error_msg, sys)


def compute_round_duration_seconds(
    spike_planted: int,
    spike_defused: int,
    spike_detonated: int,
    round_timer_expired: int,
    random_state=np.random,
    min_instant_round: float = 15.0,
) -> float:
    """
    Compute total_duration_round (seconds) given spike/timer outcomes.
    """
    try:
        # Case 1: No spike was planted
        if not spike_planted:
            if round_timer_expired:
                duration = random_state.uniform(90.0, 100.0)
            else:
                duration = random_state.uniform(min_instant_round, 100.0)
            logging.debug(f"Round duration (no spike): {duration}s")
            return duration
        
        # Case 2: Spike planted and detonated
        if spike_detonated:
            time_until_plant = random_state.uniform(20.0, 100.0)
            fuse_time = random_state.uniform(35.0, 45.0)
            total = time_until_plant + fuse_time
            total = max(min_instant_round, min(total, 145.0))
            logging.debug(f"Round duration (spike detonated): {total}s")
            return total
        
        # Case 3: Spike planted and defused
        if spike_defused:
            time_until_plant = random_state.uniform(20.0, 90.0)
            time_until_defuse = random_state.uniform(5.0, 35.0)
            total = time_until_plant + time_until_defuse
            if total < min_instant_round:
                total = min_instant_round
            if total > 140.0:
                total = 140.0
            logging.debug(f"Round duration (spike defused): {total}s")
            return total
        
        # Fallback
        duration = random_state.uniform(80.0, 100.0)
        return max(min_instant_round, duration)
    
    except Exception as e:
        error_msg = f"Error in compute_round_duration_seconds: {str(e)}"
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
) -> Tuple[Dict, Dict, Dict, int, int, Dict, Dict, int, int, Dict]:
    """
    Simulate kill/death/damage interactions for a player in a round.
    """
    try:
        agent_name = row_dict.get('agent_name', 'UNKNOWN')
        logging.debug(f"kill_death_simulation_by_damage: Processing {agent_name}")
        
        kill = 0
        death = 0
        
        if row_dict.get("isAttacker") == 1:
            # Attacker action
            spike_planted = np.random.choice([0, 1], p=[0.3, 0.7]) if team_spike_planted is None or team_spike_planted == 0 else 0
            row_dict["plants"] = spike_planted
            team_spike_planted = spike_planted if team_spike_planted is None or team_spike_planted == 0 else team_spike_planted
            
            if spike_planted:
                logging.debug(f"Attacker {agent_name}: spike_planted")
            
            # Get attacker health and simulate damage with first defender
            attacker_health = attacker_dict.get(agent_name, 100)
            if len(defender_dict) > 0:
                first_defender = list(defender_dict.keys())[0]
                defender_health = defender_dict.get(first_defender, 100)
                
                hit_value = np.random.randint(0, defender_health + 1)
                damage_value = np.random.randint(0, attacker_health + 1)
                
                head_hit_pct, body_hit_pct, leg_hit_pct = biased_hbl_percentages(value=hit_value)
                head_damage_pct, body_damage_pct, leg_damage_pct = biased_hbl_percentages(value=damage_value)
                
                # Record damage stats
                agent_hit_damage[agent_name][first_defender]["hit"]["head"] = head_hit_pct
                agent_hit_damage[agent_name][first_defender]["hit"]["body"] = body_hit_pct
                agent_hit_damage[agent_name][first_defender]["hit"]["leg"] = leg_hit_pct
                agent_hit_damage[agent_name][first_defender]["damage"]["head"] = head_damage_pct
                agent_hit_damage[agent_name][first_defender]["damage"]["body"] = body_damage_pct
                agent_hit_damage[agent_name][first_defender]["damage"]["leg"] = leg_damage_pct
                agent_hit_damage[agent_name][first_defender]["outgoing_damage"] = hit_value
                agent_hit_damage[agent_name][first_defender]["incoming_damage"] = damage_value
                
                logging.debug(f"Attacker {agent_name} vs Defender {first_defender}: hit={hit_value}, damage={damage_value}")
                
                # Apply damage
                if damage_value >= attacker_health and attacker_health > 0:
                    attacker_dict[agent_name] = 0
                    death = 1
                    kill_count_defender[first_defender] += 1
                    attackers_alive -= 1
                    logging.debug(f"Attacker {agent_name} eliminated")
                else:
                    attacker_dict[agent_name] = attacker_health - damage_value
                
                if hit_value >= defender_health and defender_health > 0:
                    defender_dict[first_defender] = 0
                    kill_count_attacker[agent_name] += 1
                    kill = kill_count_attacker[agent_name]
                    defenders_alive -= 1
                    logging.debug(f"Defender {first_defender} eliminated by {agent_name}")
                else:
                    defender_dict[first_defender] = defender_health - hit_value
        
        elif row_dict.get("isDefender") == 1:
            # Defender action
            spike_diffused = np.random.choice([0, 1], p=[0.8, 0.2]) if team_spike_planted == 1 and (team_spike_diffused is None or team_spike_diffused == 0) else 0
            row_dict["diffused"] = spike_diffused
            team_spike_diffused = spike_diffused if team_spike_diffused is None or team_spike_diffused == 0 else team_spike_diffused
            
            if spike_diffused:
                logging.debug(f"Defender {agent_name}: spike_diffused")
            
            # Defender interacts with attackers
            defender_health = defender_dict.get(agent_name, 100)
            if len(attacker_dict) > 0:
                first_attacker = list(attacker_dict.keys())[0]
                attacker_health = attacker_dict.get(first_attacker, 100)
                
                hit_value = np.random.randint(0, attacker_health + 1)
                damage_value = np.random.randint(0, defender_health + 1)
                
                head_hit_pct, body_hit_pct, leg_hit_pct = biased_hbl_percentages(value=hit_value)
                head_damage_pct, body_damage_pct, leg_damage_pct = biased_hbl_percentages(value=damage_value)
                
                agent_hit_damage[agent_name][first_attacker]["hit"]["head"] = head_hit_pct
                agent_hit_damage[agent_name][first_attacker]["hit"]["body"] = body_hit_pct
                agent_hit_damage[agent_name][first_attacker]["hit"]["leg"] = leg_hit_pct
                agent_hit_damage[agent_name][first_attacker]["damage"]["head"] = head_damage_pct
                agent_hit_damage[agent_name][first_attacker]["damage"]["body"] = body_damage_pct
                agent_hit_damage[agent_name][first_attacker]["damage"]["leg"] = leg_damage_pct
                agent_hit_damage[agent_name][first_attacker]["outgoing_damage"] = hit_value
                agent_hit_damage[agent_name][first_attacker]["incoming_damage"] = damage_value
                
                logging.debug(f"Defender {agent_name} vs Attacker {first_attacker}: hit={hit_value}, damage={damage_value}")
                
                # Apply damage
                if damage_value >= defender_health and defender_health > 0:
                    defender_dict[agent_name] = 0
                    death = 1
                    kill_count_attacker[first_attacker] += 1
                    defenders_alive -= 1
                    logging.debug(f"Defender {agent_name} eliminated")
                else:
                    defender_dict[agent_name] = defender_health - damage_value
                
                if hit_value >= attacker_health and attacker_health > 0:
                    attacker_dict[first_attacker] = 0
                    kill_count_defender[agent_name] += 1
                    kill = kill_count_defender[agent_name]
                    attackers_alive -= 1
                    logging.debug(f"Attacker {first_attacker} eliminated by {agent_name}")
                else:
                    attacker_dict[first_attacker] = attacker_health - hit_value
        
        row_dict["kills"] = kill
        row_dict["death"] = death
        
        return row_dict, attacker_dict, defender_dict, team_spike_planted, team_spike_diffused, kill_count_attacker, kill_count_defender, attackers_alive, defenders_alive, agent_hit_damage
    
    except Exception as e:
        error_msg = f"Error in kill_death_simulation_by_damage for agent {agent_name}: {str(e)}"
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
