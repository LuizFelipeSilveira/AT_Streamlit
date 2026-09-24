import warnings

import numpy as np
import pandas as pd
import streamlit as st
from statsbombpy import sb

warnings.filterwarnings("ignore")

EVENT_PT = {
    "Pass": "Passe",
    "Shot": "Finalização",
    "Carry": "Condução",
    "Ball Receipt*": "Recepção",
    "Pressure": "Pressão",
    "Ball Recovery": "Recuperação",
    "Duel": "Duelo",
    "Clearance": "Corte",
    "Dribble": "Drible",
    "Dribbled Past": "Driblado",
    "Interception": "Interceptação",
    "Block": "Bloqueio",
    "Foul Committed": "Falta cometida",
    "Foul Won": "Falta sofrida",
    "Miscontrol": "Erro de domínio",
    "Dispossessed": "Perda de posse",
    "Goal Keeper": "Goleiro",
    "Substitution": "Substituição",
    "Tactical Shift": "Mudança tática",
    "Half Start": "Início de tempo",
    "Half End": "Fim de tempo",
    "Starting XI": "Escalação inicial",
    "Injury Stoppage": "Parada por lesão",
    "Referee Ball-Drop": "Bola ao chão",
    "Shield": "Proteção de bola",
    "50/50": "Dividida",
    "Error": "Erro",
    "Offside": "Impedimento",
    "Own Goal For": "Gol contra (a favor)",
    "Own Goal Against": "Gol contra",
    "Bad Behaviour": "Conduta antidesportiva",
    "Player Off": "Jogador sai",
    "Player On": "Jogador volta",
}

OPTIONAL_COLUMNS = [
    "location", "pass_end_location", "carry_end_location", "shot_end_location",
    "pass_outcome", "pass_recipient", "pass_length", "pass_type", "pass_height",
    "pass_shot_assist", "pass_goal_assist", "pass_cross", "shot_outcome",
    "shot_statsbomb_xg", "shot_body_part", "shot_technique", "shot_type",
    "dribble_outcome", "duel_type", "duel_outcome", "under_pressure",
    "foul_committed_card", "bad_behaviour_card", "position", "play_pattern",
]


@st.cache_data(show_spinner=False, ttl=86400)
def load_competitions():
    df = sb.competitions()
    cols = ["competition_id", "season_id", "competition_name", "season_name",
            "country_name", "competition_gender"]
    return df[cols].sort_values(["competition_name", "season_name"],
                                ascending=[True, False]).reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=86400)
def load_matches(competition_id, season_id):
    df = sb.matches(competition_id=competition_id, season_id=season_id)
    df = df.sort_values(["match_date", "kick_off"]).reset_index(drop=True)
    df["label"] = (
        df["match_date"].astype(str) + "  ·  " + df["home_team"] + " "
        + df["home_score"].astype(str) + " x " + df["away_score"].astype(str)
        + " " + df["away_team"]
    )
    return df


def _coord(series, i):
    return series.apply(lambda v: v[i] if isinstance(v, (list, tuple)) and len(v) > i else np.nan)


@st.cache_data(show_spinner=False, ttl=86400)
def load_events(match_id):
    df = sb.events(match_id=match_id)
    df = df[df["period"] <= 4].copy()
    names = display_names(match_id)
    for col in ("player", "pass_recipient", "substitution_replacement"):
        if col in df.columns:
            df[col] = df[col].map(lambda v: names.get(v, v))
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    df = df.sort_values("index").reset_index(drop=True)
    df["x"] = _coord(df["location"], 0)
    df["y"] = _coord(df["location"], 1)
    end = df["pass_end_location"].where(df["pass_end_location"].notna(), df["carry_end_location"])
    end = end.where(end.notna(), df["shot_end_location"])
    df["end_x"] = _coord(end, 0)
    df["end_y"] = _coord(end, 1)
    df["tempo"] = df["minute"] + df["second"] / 60
    df["tipo"] = df["type"].map(EVENT_PT).fillna(df["type"])
    df["passe_certo"] = (df["type"] == "Pass") & df["pass_outcome"].isna()
    df["gol"] = df["shot_outcome"] == "Goal"
    df["shot_statsbomb_xg"] = pd.to_numeric(df["shot_statsbomb_xg"], errors="coerce")
    return df


@st.cache_data(show_spinner=False, ttl=86400)
def load_lineups(match_id):
    return sb.lineups(match_id=match_id)


def display_names(match_id):
    names = {}
    for df in load_lineups(match_id).values():
        for full, nick in zip(df["player_name"], df["player_nickname"]):
            names[full] = nick if isinstance(nick, str) and nick.strip() else full
    return names


def team_names(match_id, home_id, away_id, home, away):
    events = load_events(match_id)
    names = events.drop_duplicates("team_id").set_index("team_id")["team"]
    return names.get(home_id, home), names.get(away_id, away)


def _clock(text):
    if not isinstance(text, str) or ":" not in text:
        return None
    m, s = text.split(":")
    return int(m) + int(s) / 60


def _minutes(positions, match_end):
    spans = []
    for p in positions:
        if (p.get("from_period") or 1) > 4:
            continue
        start = _clock(p.get("from")) or 0
        stop = _clock(p.get("to"))
        if stop is None or (p.get("to_period") or 0) < (p.get("from_period") or 0) or stop < start:
            stop = match_end
        spans.append((min(start, match_end), min(stop, match_end)))
    total, cursor = 0.0, 0.0
    for a, b in sorted(spans):
        a = max(a, cursor)
        if b > a:
            total += b - a
            cursor = b
    return total


@st.cache_data(show_spinner=False, ttl=86400)
def load_players(match_id):
    events = load_events(match_id)
    lineups = load_lineups(match_id)
    match_end = events.loc[events["period"] <= 4, "tempo"].max()
    rows = []
    for team, df in lineups.items():
        for _, r in df.iterrows():
            positions = r["positions"] if isinstance(r["positions"], list) else []
            minutes = _minutes(positions, match_end)
            rows.append({
                "Jogador": r["player_nickname"] if isinstance(r["player_nickname"], str) and r["player_nickname"].strip() else r["player_name"],
                "Time": team,
                "Camisa": r["jersey_number"],
                "Posição": positions[0]["position"] if positions else "Não entrou",
                "Titular": bool(positions) and positions[0].get("start_reason") == "Starting XI",
                "Minutos": round(minutes),
            })
    return pd.DataFrame(rows)


def event_display(df):
    cols = {
        "period": "Tempo", "minute": "Min", "second": "Seg", "team": "Time",
        "player": "Jogador", "tipo": "Evento", "position": "Posição",
        "play_pattern": "Origem da jogada", "x": "x", "y": "y", "end_x": "x final",
        "end_y": "y final", "pass_recipient": "Receptor", "pass_outcome": "Resultado do passe",
        "shot_outcome": "Resultado do chute", "shot_statsbomb_xg": "xG",
        "under_pressure": "Sob pressão",
    }
    out = df[list(cols)].rename(columns=cols).copy()
    out["Sob pressão"] = out["Sob pressão"].fillna(False).astype(bool)
    out["Resultado do passe"] = np.where(
        df["type"] == "Pass", df["pass_outcome"].fillna("Completo"), None)
    return out
