import pandas as pd
import streamlit as st

from src import viz
from src.data import event_display
from src.state import keep, save, save_many
from src.stats import per90
from src.ui import csv_download, kpi, match_caption, match_context, tone_by

ctx = match_context()
events, players = ctx["events"], ctx["players"]
played = players[players["Minutos"] > 0]
names = played["Jogador"].tolist()
label = dict(zip(played["Jogador"], played["Jogador"] + " (" + played["Time"] + ")"))

st.title("Jogadores")
match_caption(ctx)

player = st.selectbox("Jogador", names, format_func=label.get,
                      key=keep("pl_player", names[0], names), on_change=save, args=("pl_player",))
p = played.set_index("Jogador").loc[player]
pev = events[events["player"] == player]

c = st.columns(4)
with c[0]:
    kpi("Passes certos", int(p["Passes certos"]), "green", delta=f"de {int(p['Passes'])}")
with c[1]:
    kpi("Precisão", f"{p['Precisão (%)']:.0f}%", tone_by(p["Precisão (%)"], 85, 70) if p["Passes"] else "grey")
with c[2]:
    kpi("Gols", int(p["Gols"]), "gold" if p["Gols"] else "grey", delta=f"{int(p['Finalizações'])} chutes")
with c[3]:
    kpi("Conversão", f"{p['Conversão (%)']:.0f}%", tone_by(p["Conversão (%)"], 20, 5) if p["Finalizações"] else "grey")

tab_ev, tab_maps, tab_cmp = st.tabs(["Eventos", "Mapas", "Comparação"])

with tab_ev:
    type_opts = pev["tipo"].value_counts().index.tolist()
    chosen = st.pills("Filtrar por tipo", type_opts, selection_mode="multi",
                      key=keep("pl_types", [], type_opts), on_change=save, args=("pl_types",))
    filt = pev[pev["tipo"].isin(chosen)] if chosen else pev
    st.dataframe(event_display(filt), hide_index=True, height=420)
    csv_download(event_display(filt), f"eventos_{player.replace(' ', '_')}.csv", key="dl_player")

with tab_maps:
    st.pyplot(viz.pass_map(pev, f"Passes · {player}"))
    st.pyplot(viz.heatmap(pev, f"Mapa de calor · {player}", "Densidade (KDE)"))

with tab_cmp:
    groups = {
        "Ataque": ["Finalizações", "No alvo", "Gols", "xG", "Dribles certos", "Passes-chave"],
        "Passe": ["Passes", "Passes certos", "Precisão (%)", "Passes-chave", "Conduções", "Cruzamentos"],
        "Defesa": ["Desarmes", "Interceptações", "Recuperações", "Pressões", "Cortes", "Faltas"],
    }
    with st.form("compare_form"):
        f1, f2 = st.columns(2)
        p1 = f1.selectbox("Jogador A", names, format_func=label.get, key=keep("cmp_a", names[0], names))
        p2 = f2.selectbox("Jogador B", names, format_func=label.get,
                          key=keep("cmp_b", names[min(1, len(names) - 1)], names))
        group = st.radio("Comparar", list(groups), horizontal=True, key=keep("cmp_group", "Passe", list(groups)))
        norm = st.checkbox("Por 90 minutos", key=keep("cmp_norm", False))
        submitted = st.form_submit_button("Comparar", on_click=save_many,
                                          args=(["cmp_a", "cmp_b", "cmp_group", "cmp_norm"],))
    if submitted:
        st.session_state["cmp_done"] = True
    if st.session_state.get("cmp_done"):
        params = groups[group]
        base = per90(played, params) if norm else played
        pool = base[base["Minutos"] >= 20] if norm else base
        high = [100.0 if c == "Precisão (%)" else float(pool[c].max()) for c in params]
        v1 = [min(v, h) for v, h in zip(base.set_index("Jogador").loc[p1, params].astype(float), high)]
        v2 = [min(v, h) for v, h in zip(base.set_index("Jogador").loc[p2, params].astype(float), high)]
        st.pyplot(viz.radar_compare(v1, v2, params, [0.0] * len(params), high, p1, p2))
        st.dataframe(pd.DataFrame({p1: v1, p2: v2}, index=params).round(2))
