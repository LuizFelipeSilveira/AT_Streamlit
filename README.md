# Painel StatsBomb com Streamlit

Dashboard interativo para explorar os dados abertos da StatsBomb: competições, temporadas, partidas e jogadores, com mapas táticos (mplsoccer), gráficos estatísticos (Matplotlib/Seaborn) e filtros interativos.

**App publicado:** https://SEU-APP.streamlit.app
**Repositório:** https://github.com/SEU-USUARIO/statsbomb-dashboard

## Páginas

| Página | Conteúdo |
|---|---|
| Partida | Placar, competição e temporada, métricas coloridas, comparativo entre times, tabela de eventos com filtros por jogador/tipo/tempo, download CSV, escalações |
| Mapas do jogo | Mapa de passes, mapa de chutes (estático e interativo), rede de passes, mapa de calor (grade, Juego de Posición, KDE, hexbin), fluxo de passes e direção dos passes |
| Jogadores | Métricas individuais, eventos filtráveis, mapas do jogador e comparação entre dois jogadores em radar |
| Estatísticas | Relações entre estatísticas (dispersão com regressão, ranking, matriz de correlação), evolução do xG, eventos por intervalo, distribuição de passes e análise da temporada inteira |

## Estrutura

```
statsbomb-dashboard/
├── app.py                 navegação e barra lateral
├── requirements.txt
├── .streamlit/config.toml tema
├── src/
│   ├── data.py            carregamento dos dados (com cache)
│   ├── stats.py           cálculo de estatísticas
│   ├── viz.py             visualizações
│   ├── state.py           persistência do Session State
│   └── ui.py              componentes de interface
└── views/
    ├── partida.py
    ├── mapas.py
    ├── jogadores.py
    └── estatisticas.py
```

## Como rodar localmente

```bash
git clone https://github.com/SEU-USUARIO/statsbomb-dashboard.git
cd statsbomb-dashboard
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Recursos do Streamlit utilizados

`st.navigation`, `st.sidebar`, `st.columns`, `st.tabs`, `st.container`, `st.expander`, `st.form`, `st.metric`, `st.pills`, `st.radio`, `st.selectbox`, `st.multiselect`, `st.slider`, `st.number_input`, `st.text_input`, `st.checkbox`, `st.download_button`, `st.progress`, `st.spinner`, `st.toast`, `st.cache_data` e `st.session_state`.

## Dados

[StatsBomb Open Data](https://github.com/statsbomb/open-data), acessados pela biblioteca `statsbombpy`.
