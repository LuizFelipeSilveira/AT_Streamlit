import numpy as np
import pandas as pd
import streamlit as st

from src.data import load_events, load_players

ON_TARGET = ["Goal", "Saved", "Saved To Post"]


def indicators(events):
    t = events["type"]
    return pd.DataFrame({
        "Passes": t == "Pass",
        "Passes certos": events["passe_certo"],
        "Passes-chave": events["pass_shot_assist"].eq(True),
        "Assistências": events["pass_goal_assist"].eq(True),
        "Cruzamentos": events["pass_cross"].eq(True),
        "Finalizações": t == "Shot",
        "No alvo": events["shot_outcome"].isin(ON_TARGET),
        "Gols": events["gol"],
        "xG": events["shot_statsbomb_xg"].fillna(0),
        "Dribles": t == "Dribble",
        "Dribles certos": (t == "Dribble") & (events["dribble_outcome"] == "Complete"),
        "Conduções": t == "Carry",
        "Desarmes": (t == "Duel") & (events["duel_type"] == "Tackle"),
        "Interceptações": t == "Interception",
        "Recuperações": t == "Ball Recovery",
        "Pressões": t == "Pressure",
        "Cortes": t == "Clearance",
        "Faltas": t == "Foul Committed",
        "Escanteios": events["pass_type"] == "Corner",
    }, index=events.index).astype(float)


def add_rates(df):
    df["Precisão (%)"] = np.where(df["Passes"] > 0, df["Passes certos"] / df["Passes"] * 100, 0).round(1)
    df["Conversão (%)"] = np.where(df["Finalizações"] > 0, df["Gols"] / df["Finalizações"] * 100, 0).round(1)
    df["xG"] = df["xG"].round(2)
    return df


@st.cache_data(show_spinner=False, ttl=86400)
def player_stats(match_id):
    events = load_events(match_id)
    ev = events[events["player"].notna()]
    ind = indicators(ev)
    ind["Jogador"] = ev["player"]
    stats = ind.groupby("Jogador").sum()
    players = load_players(match_id).set_index("Jogador")
    stats = players.join(stats, how="left").fillna(0)
    stats = add_rates(stats)
    count_cols = [c for c in stats.columns if c not in ("Time", "Posição", "Titular", "xG",
                                                          "Precisão (%)", "Conversão (%)")]
    stats[count_cols] = stats[count_cols].astype(int)
    return stats.reset_index().sort_values(["Time", "Minutos"], ascending=[True, False])


@st.cache_data(show_spinner=False, ttl=86400)
def team_stats(match_id, home_team, away_team, home_score, away_score):
    events = load_events(match_id)
    ind = indicators(events)
    ind["Time"] = events["team"]
    stats = ind.groupby("Time").sum().reindex([home_team, away_team]).fillna(0)
    stats["Gols"] = [home_score, away_score]
    stats = add_rates(stats)
    total_passes = stats["Passes"].sum()
    stats["Posse aprox. (%)"] = (stats["Passes"] / total_passes * 100).round(1) if total_passes else 0
    cards = events["foul_committed_card"].fillna(events["bad_behaviour_card"])
    stats["Cartões amarelos"] = [int(((events["team"] == t) & cards.isin(["Yellow Card", "Second Yellow"])).sum())
                                 for t in stats.index]
    stats["Cartões vermelhos"] = [int(((events["team"] == t) & cards.isin(["Red Card", "Second Yellow"])).sum())
                                  for t in stats.index]
    order = ["Gols", "xG", "Finalizações", "No alvo", "Conversão (%)", "Posse aprox. (%)", "Passes",
             "Passes certos", "Precisão (%)", "Passes-chave", "Cruzamentos", "Dribles", "Desarmes",
             "Interceptações", "Recuperações", "Pressões", "Faltas", "Escanteios",
             "Cartões amarelos", "Cartões vermelhos"]
    return stats[order].T


@st.cache_data(show_spinner=False, ttl=86400)
def per90(df, cols):
    out = df.copy()
    minutes = out["Minutos"].replace(0, np.nan)
    for c in cols:
        if c not in ("Precisão (%)", "Conversão (%)"):
            out[c] = (out[c] / minutes * 90).round(2)
    return out.fillna(0)
