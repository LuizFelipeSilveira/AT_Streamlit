import streamlit as st

from src import viz
from src.state import keep, save, save_many
from src.ui import match_caption, match_context

ctx = match_context()
m, events, players = ctx["match"], ctx["events"], ctx["players"]
home, away = m["home_team"], m["away_team"]
colors = viz.team_colors(home, away)
played = players[players["Minutos"] > 0]
numeric = ["Passes", "Passes certos", "Precisão (%)", "Passes-chave", "Finalizações", "No alvo", "Gols",
           "xG", "Dribles", "Conduções", "Desarmes", "Interceptações", "Recuperações", "Pressões", "Minutos"]

st.title("Estatísticas")
match_caption(ctx)

tab_rel, tab_time = st.tabs(["Relações", "Linha do tempo"])

with tab_rel:
    with st.form("relation_form"):
        a, b = st.columns(2)
        x = a.selectbox("Eixo X", numeric, key=keep("rel_x", "Passes", numeric))
        y = b.selectbox("Eixo Y", numeric, key=keep("rel_y", "xG", numeric))
        scope = st.radio("Time", ["Ambos", home, away], horizontal=True, key=keep("rel_scope", "Ambos"))
        min_minutes = st.number_input("Minutos mínimos em campo", 0, 120, step=5, key=keep("rel_min", 15))
        labels = st.checkbox("Mostrar nomes", key=keep("rel_labels", True))
        st.form_submit_button("Atualizar", on_click=save_many,
                              args=(["rel_x", "rel_y", "rel_scope", "rel_min", "rel_labels"],))
    data = played[played["Minutos"] >= min_minutes]
    if scope != "Ambos":
        data = data[data["Time"] == scope]
    if len(data) < 3:
        st.warning("Poucos jogadores com esses filtros. Diminua os minutos mínimos.")
    else:
        st.pyplot(viz.scatter_relation(data, x, y, colors, labels))
        st.pyplot(viz.correlation_heatmap(data, ["Passes", "Passes-chave", "Finalizações", "xG", "Gols",
                                                 "Dribles", "Desarmes", "Pressões"]))

with tab_time:
    st.pyplot(viz.xg_flow(events, home, away))
    t1, t2 = st.columns(2)
    ev_opts = [e for e in ["Passe", "Finalização", "Pressão", "Recuperação", "Duelo"] if e in events["tipo"].unique()]
    ev_type = t1.selectbox("Evento", ev_opts, key=keep("tl_type", "Passe", ev_opts), on_change=save, args=("tl_type",))
    bin_size = t2.select_slider("Intervalo (min)", [5, 10, 15, 30], key=keep("tl_bin", 15),
                                on_change=save, args=("tl_bin",))
    st.pyplot(viz.events_timeline(events, colors, bin_size, ev_type))
