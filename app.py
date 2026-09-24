import streamlit as st

from src.ui import inject_css, sidebar_filters

st.set_page_config(page_title="AT Streamlit", layout="centered")
inject_css()

pages = st.navigation([
    st.Page("views/partida.py", title="Partida", default=True),
    st.Page("views/mapas.py", title="Mapas"),
    st.Page("views/jogadores.py", title="Jogadores"),
    st.Page("views/estatisticas.py", title="Estatísticas"),
])
sidebar_filters()
pages.run()
