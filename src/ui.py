import itertools

import pandas as pd
import streamlit as st

from src.data import load_competitions, load_events, load_lineups, load_matches, load_players, team_names
from src.state import keep, save
from src.stats import player_stats

DEFAULT = ("FIFA World Cup", "2022", 3869685)

TONES = {
    "green": ("#E3F2E8", "#1F7A4D"),
    "gold": ("#FFF4D1", "#D4A017"),
    "red": ("#FDE7E4", "#D64933"),
    "grey": ("#EEF1EF", "#8A9A90"),
}

_counter = itertools.count()


def inject_css():
    css = "".join(
        f'[class*="st-key-kpi-{name}-"] [data-testid="stMetric"]'
        f"{{background:{bg}; border-left:5px solid {border}; padding:12px 14px; border-radius:8px;}}"
        for name, (bg, border) in TONES.items()
    )
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def kpi(label, value, tone="grey", delta=None, help=None):
    with st.container(key=f"kpi-{tone}-{next(_counter)}"):
        st.metric(label, value, delta=delta, delta_color="off", help=help)


def tone_by(value, good, bad):
    if value >= good:
        return "green"
    if value <= bad:
        return "red"
    return "gold"


def sidebar_filters():
    with st.sidebar:
        st.title("AT Streamlit")
        with st.spinner("Carregando competições..."):
            comps = load_competitions()
        comp_names = sorted(comps["competition_name"].unique())
        comp = st.selectbox("Campeonato", comp_names,
                            key=keep("competition", DEFAULT[0], comp_names),
                            on_change=save, args=("competition",))
        seasons_df = comps[comps["competition_name"] == comp]
        seasons = seasons_df["season_name"].tolist()
        season = st.selectbox("Temporada", seasons, key=keep("season", DEFAULT[1], seasons),
                              on_change=save, args=("season",))
        row = seasons_df[seasons_df["season_name"] == season].iloc[0]
        with st.spinner("Carregando partidas..."):
            matches = load_matches(int(row.competition_id), int(row.season_id))
        labels = dict(zip(matches["match_id"], matches["label"]))
        match_ids = list(labels)
        match_id = st.selectbox("Partida", match_ids, format_func=labels.get,
                                key=keep("match_id", DEFAULT[2], match_ids),
                                on_change=save, args=("match_id",))
        st.caption("Dados: StatsBomb Open Data")
    match = matches[matches["match_id"] == match_id].iloc[0].to_dict()
    st.session_state["context"] = {
        "competition": comp, "season": season, "competition_id": int(row.competition_id),
        "season_id": int(row.season_id), "match": match,
    }


def match_context():
    ctx = st.session_state.get("context")
    if not ctx:
        st.info("Escolha um campeonato, uma temporada e uma partida na barra lateral.")
        st.stop()
    mid = ctx["match"]["match_id"]
    if st.session_state.get("loaded_match") != mid:
        bar = st.progress(0, text="Baixando eventos da partida...")
        load_events(mid)
        bar.progress(55, text="Baixando escalações...")
        load_lineups(mid)
        bar.progress(80, text="Calculando estatísticas...")
        load_players(mid)
        player_stats(mid)
        bar.progress(100, text="Pronto")
        bar.empty()
        st.session_state["loaded_match"] = mid
    match = dict(ctx["match"])
    match["home_team"], match["away_team"] = team_names(
        mid, match["home_team_id"], match["away_team_id"], match["home_team"], match["away_team"])
    return {**ctx, "match": match, "events": load_events(mid), "players": player_stats(mid)}


def match_title(ctx):
    m = ctx["match"]
    return f"{m['home_team']} {m['home_score']} x {m['away_score']} {m['away_team']}"


def match_caption(ctx):
    date = pd.to_datetime(ctx["match"]["match_date"]).strftime("%d/%m/%Y")
    st.caption(f"{ctx['competition']} · {ctx['season']} · {match_title(ctx)} · {date}")


def csv_download(df, name, label="Baixar CSV", key=None):
    st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"), file_name=name,
                       mime="text/csv", key=key)
