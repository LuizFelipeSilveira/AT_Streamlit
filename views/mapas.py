import streamlit as st

from src import viz
from src.state import keep, save
from src.ui import match_caption, match_context

ctx = match_context()
m, events, players = ctx["match"], ctx["events"], ctx["players"]
home, away = m["home_team"], m["away_team"]
colors = viz.team_colors(home, away)
jerseys = dict(zip(players["Jogador"], players["Camisa"]))

st.title("Mapas")
match_caption(ctx)

c1, c2 = st.columns(2)
team = c1.selectbox("Time", [home, away], key=keep("map_team", home, [home, away]),
                    on_change=save, args=("map_team",))
team_players = ["Time inteiro"] + players.loc[(players["Time"] == team) & (players["Minutos"] > 0), "Jogador"].tolist()
player = c2.selectbox("Jogador", team_players, key=keep("map_player", "Time inteiro", team_players),
                      on_change=save, args=("map_player",))
max_min = int(events["minute"].max()) + 1
minutes = st.slider("Intervalo de tempo (minutos)", 0, max_min,
                    key=keep("map_minutes", (0, max_min), bounds=(0, max_min)),
                    on_change=save, args=("map_minutes",))

period = events[events["minute"].between(*minutes)]
sel = period[period["team"] == team]
if player != "Time inteiro":
    sel = sel[sel["player"] == player]
who = team if player == "Time inteiro" else player

tabs = st.tabs(["Passes", "Finalizações", "Rede de passes", "Mapa de calor", "Fluxo de passes"])

with tabs[0]:
    o1, o2, o3 = st.columns(3)
    show_ok = o1.checkbox("Certos", key=keep("pm_ok", True), on_change=save, args=("pm_ok",))
    show_bad = o2.checkbox("Errados", key=keep("pm_bad", True), on_change=save, args=("pm_bad",))
    show_key = o3.checkbox("Geraram chute", key=keep("pm_key", True), on_change=save, args=("pm_key",))
    with st.spinner("Gerando mapa..."):
        st.pyplot(viz.pass_map(sel, f"Passes · {who}", show_ok, show_bad, show_key))

with tabs[1]:
    mode = st.radio("Tipo de mapa", ["Estático", "Interativo"], horizontal=True,
                    key=keep("shot_mode", "Estático"), on_change=save, args=("shot_mode",))
    shots_ev = period if player == "Time inteiro" else period[(period["player"] == player) | (period["team"] != team)]
    if mode == "Estático":
        st.pyplot(viz.shot_map(shots_ev, home, away))
    else:
        st.plotly_chart(viz.shot_map_interactive(shots_ev, home, away))

with tabs[2]:
    min_passes = st.slider("Mínimo de passes entre dois jogadores", 1, 10,
                           key=keep("net_min", 3), on_change=save, args=("net_min",))
    fig, table = viz.pass_network(period, team, jerseys, min_passes, colors[team])
    st.pyplot(fig)
    st.dataframe(table, hide_index=True)

with tabs[3]:
    type_opts = sel["tipo"].value_counts().index.tolist()
    heat_types = st.multiselect("Eventos", type_opts,
                                key=keep("heat_types", [t for t in ["Passe", "Recepção", "Condução"] if t in type_opts], type_opts),
                                on_change=save, args=("heat_types",))
    method = st.radio("Estilo", ["Grade", "Juego de Posición", "Densidade (KDE)"], horizontal=True,
                      key=keep("heat_method", "Grade"), on_change=save, args=("heat_method",))
    data = sel[sel["tipo"].isin(heat_types)] if heat_types else sel
    st.pyplot(viz.heatmap(data, f"Mapa de calor · {who}", method))

with tabs[4]:
    st.pyplot(viz.pass_flow(sel, f"Fluxo de passes · {who}"))
