import pandas as pd
import streamlit as st

from src.data import event_display
from src.state import keep, save, save_many
from src.stats import team_stats
from src.ui import csv_download, kpi, match_context, match_title, tone_by

ctx = match_context()
m, events = ctx["match"], ctx["events"]
home, away = m["home_team"], m["away_team"]

st.title(match_title(ctx))
info = st.columns(3)
info[0].markdown(f"**Competição**  \n{ctx['competition']}")
info[1].markdown(f"**Temporada**  \n{ctx['season']}")
info[2].markdown(f"**Data**  \n{pd.to_datetime(m['match_date']).strftime('%d/%m/%Y')}")

ts = team_stats(m["match_id"], home, away, m["home_score"], m["away_score"])
total = ts.sum(axis=1)
conv = total["Gols"] / total["Finalizações"] * 100 if total["Finalizações"] else 0
acc = total["Passes certos"] / total["Passes"] * 100 if total["Passes"] else 0

c = st.columns(4)
with c[0]:
    kpi("Gols", int(total["Gols"]), "gold")
with c[1]:
    kpi("Finalizações", int(total["Finalizações"]), delta=f"{int(total['No alvo'])} no alvo")
with c[2]:
    kpi("Passes certos", int(total["Passes certos"]), tone_by(acc, 82, 70), delta=f"{acc:.0f}% de acerto")
with c[3]:
    kpi("Conversão de chutes", f"{conv:.1f}%", tone_by(conv, 15, 7), help="Gols divididos por finalizações")

tab_stats, tab_events = st.tabs(["Estatísticas", "Eventos"])

with tab_stats:
    st.dataframe(ts.style.format("{:g}"), height=740)

with tab_events:
    teams = ["Ambos", home, away]
    team = st.radio("Time", teams, horizontal=True, key=keep("ev_team", "Ambos", teams),
                    on_change=save, args=("ev_team",))
    pool = events if team == "Ambos" else events[events["team"] == team]
    player_opts = ["Todos"] + sorted(pool["player"].dropna().unique())
    player = st.selectbox("Jogador", player_opts, key=keep("ev_player", "Todos", player_opts),
                          on_change=save, args=("ev_player",))
    type_opts = pool["tipo"].value_counts().index.tolist()
    main_types = [t for t in ["Passe", "Finalização", "Duelo", "Interceptação"] if t in type_opts]
    types = st.pills("Tipos de evento", type_opts, selection_mode="multi",
                     key=keep("ev_types", main_types, type_opts), on_change=save, args=("ev_types",))

    max_min = int(events["minute"].max()) + 1
    with st.form("event_form"):
        n_events = st.number_input("Quantidade de eventos", 10, 5000, step=50, key=keep("ev_n", 200))
        minute_range = st.slider("Intervalo de tempo (minutos)", 0, max_min,
                                 key=keep("ev_minutes", (0, max_min), bounds=(0, max_min)))
        search = st.text_input("Buscar jogador pelo nome", key=keep("ev_search", ""))
        pressure = st.checkbox("Apenas eventos sob pressão", key=keep("ev_press", False))
        st.form_submit_button("Aplicar", on_click=save_many,
                              args=(["ev_n", "ev_minutes", "ev_search", "ev_press"],))

    filt = pool
    if player != "Todos":
        filt = filt[filt["player"] == player]
    if types:
        filt = filt[filt["tipo"].isin(types)]
    filt = filt[filt["minute"].between(*minute_range)]
    if search:
        filt = filt[filt["player"].fillna("").str.contains(search, case=False)]
    if pressure:
        filt = filt[filt["under_pressure"].eq(True)]

    st.caption(f"{min(len(filt), int(n_events))} de {len(filt)} eventos filtrados")
    st.dataframe(event_display(filt.head(int(n_events))), hide_index=True, height=460)
    csv_download(event_display(filt), f"eventos_{m['match_id']}.csv", "Baixar eventos filtrados (CSV)")
