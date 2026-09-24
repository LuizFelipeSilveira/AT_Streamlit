import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from mplsoccer import Pitch, Radar

PITCH_BG = "#17332A"
LINE = "#D9E6DD"
TEXT = "#F1F5F2"
HOME = "#4EA3E0"
AWAY = "#F07167"
GOLD = "#F2C14E"
MISS = "#E4572E"
OK = "#7BD389"
STROKE = [pe.withStroke(linewidth=3, foreground="#0B1A14")]
HEAT = LinearSegmentedColormap.from_list("heat", [PITCH_BG, "#2F6B4F", GOLD, "#FFF4CC"])

plt.rcParams.update({"font.family": "DejaVu Sans"})


def short(name):
    parts = str(name).split()
    if len(parts) > 2 and parts[-2].lower() in {"de", "di", "da", "van", "von", "dos", "del", "le"}:
        return " ".join(parts[-2:])
    return parts[-1] if parts else ""


def team_colors(home, away):
    return {home: HOME, away: AWAY}


def _pitch():
    return Pitch(pitch_type="statsbomb", pitch_color=PITCH_BG, line_color=LINE,
                 linewidth=1.2, goal_type="box", line_zorder=2)


def _figure(pitch, figsize=(11, 7.4)):
    fig, ax = pitch.draw(figsize=figsize)
    fig.set_facecolor(PITCH_BG)
    return fig, ax


def _title(ax, title, subtitle=None):
    ax.set_title(title, color=TEXT, fontsize=15, fontweight="bold", loc="left", pad=22 if subtitle else 8)
    if subtitle:
        ax.text(0, 1.012, subtitle, transform=ax.transAxes, color=TEXT, alpha=0.75, fontsize=10)


def _legend(ax, handles, loc="upper left", ncol=1):
    leg = ax.legend(handles=handles, loc=loc, ncol=ncol, facecolor=PITCH_BG, edgecolor=LINE,
                    labelcolor=TEXT, fontsize=9, framealpha=0.9)
    return leg


def _empty(fig, ax, text):
    ax.text(60, 40, text, color=TEXT, ha="center", va="center", fontsize=13)
    return fig


def pass_map(events, title, show_complete=True, show_incomplete=True, highlight_key=True):
    pitch = _pitch()
    fig, ax = _figure(pitch)
    passes = events[(events["type"] == "Pass") & events["end_x"].notna()]
    if passes.empty:
        return _empty(fig, ax, "Nenhum passe com os filtros atuais")
    complete = passes[passes["passe_certo"]]
    incomplete = passes[~passes["passe_certo"]]
    key = passes[passes["pass_shot_assist"].eq(True) | passes["pass_goal_assist"].eq(True)]
    handles = []
    if show_complete and not complete.empty:
        pitch.arrows(complete.x, complete.y, complete.end_x, complete.end_y, width=1.6,
                     headwidth=5, headlength=5, color=OK, alpha=0.75, ax=ax, zorder=3)
        handles.append(Line2D([], [], color=OK, lw=2.5, label=f"Certo ({len(complete)})"))
    if show_incomplete and not incomplete.empty:
        pitch.arrows(incomplete.x, incomplete.y, incomplete.end_x, incomplete.end_y, width=1.6,
                     headwidth=5, headlength=5, color=MISS, alpha=0.7, ax=ax, zorder=3)
        handles.append(Line2D([], [], color=MISS, lw=2.5, label=f"Errado ({len(incomplete)})"))
    if highlight_key and not key.empty:
        pitch.arrows(key.x, key.y, key.end_x, key.end_y, width=3, headwidth=4, headlength=4,
                     color=GOLD, ax=ax, zorder=4)
        handles.append(Line2D([], [], color=GOLD, lw=3.5, label=f"Gerou finalização ({len(key)})"))
    pitch.scatter(passes.x, passes.y, s=12, color=TEXT, alpha=0.5, ax=ax, zorder=3)
    acc = len(complete) / len(passes) * 100
    _title(ax, title, f"{len(passes)} passes · {acc:.0f}% de acerto · ataque da esquerda para a direita")
    if handles:
        _legend(ax, handles, loc="lower center", ncol=len(handles)).set_bbox_to_anchor((0.5, -0.07))
    return fig


def _shot_scatter(pitch, ax, shots, color, flip=False):
    x = 120 - shots.x if flip else shots.x
    y = 80 - shots.y if flip else shots.y
    size = shots["shot_statsbomb_xg"].fillna(0.02) * 1400 + 60
    goal = shots["gol"].values
    on_target = shots["shot_outcome"].isin(["Saved", "Saved To Post"]).values
    off = ~(goal | on_target)
    pitch.scatter(x[off], y[off], s=size[off], facecolors="none", edgecolors=color, lw=2, alpha=0.9, ax=ax, zorder=4)
    pitch.scatter(x[on_target], y[on_target], s=size[on_target], color=color, edgecolors=TEXT, lw=1, alpha=0.85, ax=ax, zorder=4)
    pitch.scatter(x[goal], y[goal], s=size[goal] * 1.2, marker="football", ax=ax, zorder=5)
    spots = {}
    for (_, s), gx, gy in zip(shots[goal].iterrows(), x[goal], y[goal]):
        spot = spots.setdefault((round(gx / 3), round(gy / 3)), {"xy": (gx, gy), "names": {}})
        spot["names"].setdefault(short(s["player"]), []).append(f"{s['minute']}'")
    for i, spot in enumerate(spots.values()):
        text = "\n".join(f"{n} {' '.join(m)}" for n, m in spot["names"].items())
        pitch.annotate(text, spot["xy"], xytext=(0, 16 if i % 2 == 0 else -22), textcoords="offset points",
                       ha="center", va="bottom" if i % 2 == 0 else "top", color=TEXT, fontsize=9,
                       fontweight="bold", path_effects=STROKE, ax=ax, zorder=6)


def _shot_legend(ax, color):
    return [
        Line2D([], [], marker="o", ls="", markersize=11, markerfacecolor="white", markeredgecolor="black", label="Gol"),
        Line2D([], [], marker="o", ls="", markersize=10, color=color, markeredgecolor=TEXT, label="No alvo (defendido)"),
        Line2D([], [], marker="o", ls="", markersize=10, markerfacecolor="none", markeredgecolor=color, mew=2, label="Fora / bloqueado"),
    ]


def shot_map(events, home, away):
    shots = events[events["type"] == "Shot"]
    colors = team_colors(home, away)
    pitch = _pitch()
    fig, ax = _figure(pitch)
    for t, flip in ((home, False), (away, True)):
        _shot_scatter(pitch, ax, shots[shots["team"] == t], colors[t], flip=flip)
    for t, xpos, ha in ((away, 2, "left"), (home, 118, "right")):
        s = shots[shots["team"] == t]
        ax.text(xpos, 83.5, f"{t}: {len(s)} chutes · xG {s['shot_statsbomb_xg'].sum():.2f}",
                color=colors[t], ha=ha, va="top", fontsize=11, fontweight="bold")
    _title(ax, "Mapa de finalizações", f"{home} ataca para a direita · {away} para a esquerda · tamanho = xG")
    handles = _shot_legend(ax, LINE)
    _legend(ax, handles, loc="lower center", ncol=3).set_bbox_to_anchor((0.5, -0.13))
    return fig


def _plotly_pitch(fig):
    line = dict(color=LINE, width=1.5)
    shapes = [
        dict(type="rect", x0=0, y0=0, x1=120, y1=80),
        dict(type="line", x0=60, y0=0, x1=60, y1=80),
        dict(type="circle", x0=50, y0=30, x1=70, y1=50),
        dict(type="rect", x0=0, y0=18, x1=18, y1=62),
        dict(type="rect", x0=102, y0=18, x1=120, y1=62),
        dict(type="rect", x0=0, y0=30, x1=6, y1=50),
        dict(type="rect", x0=114, y0=30, x1=120, y1=50),
        dict(type="rect", x0=-2, y0=36, x1=0, y1=44),
        dict(type="rect", x0=120, y0=36, x1=122, y1=44),
    ]
    for s in shapes:
        s.update(line=line, layer="below")
    fig.update_layout(shapes=shapes, plot_bgcolor=PITCH_BG, paper_bgcolor=PITCH_BG,
                      font=dict(color=TEXT), height=560, margin=dict(l=10, r=10, t=60, b=10),
                      legend=dict(orientation="h", y=-0.02, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(range=[-4, 124], visible=False)
    fig.update_yaxes(range=[84, -4], visible=False, scaleanchor="x", scaleratio=1)
    return fig


def shot_map_interactive(events, home, away):
    shots = events[events["type"] == "Shot"].copy()
    colors = team_colors(home, away)
    fig = go.Figure()
    for t in (home, away):
        s = shots[shots["team"] == t].copy()
        if t == away:
            s["x"], s["y"] = 120 - s["x"], 80 - s["y"]
        for is_goal, symbol, suffix in ((False, "circle", "chutes"), (True, "star", "gols")):
            d = s[s["gol"] == is_goal]
            if d.empty:
                continue
            fig.add_trace(go.Scatter(
                x=d["x"], y=d["y"], mode="markers", name=f"{t} · {suffix}",
                marker=dict(size=d["shot_statsbomb_xg"].fillna(0.02) * 60 + 8, color=colors[t],
                            symbol=symbol, line=dict(color=TEXT, width=1.5 if is_goal else 0.5),
                            opacity=0.9),
                customdata=np.stack([d["player"], d["minute"], d["shot_statsbomb_xg"].round(3),
                                     d["shot_outcome"], d["shot_body_part"].fillna("-"),
                                     d["shot_type"].fillna("-")], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b><br>Minuto %{customdata[1]}'<br>xG %{customdata[2]}"
                              "<br>Resultado: %{customdata[3]}<br>Parte do corpo: %{customdata[4]}"
                              "<br>Tipo: %{customdata[5]}<extra></extra>",
            ))
    fig.update_layout(title=f"Passe o mouse sobre cada chute · {home} → direita, {away} ← esquerda")
    return _plotly_pitch(fig)


def pass_network(events, team, jerseys, min_passes=3, color=HOME):
    team_ev = events[events["team"] == team]
    subs = team_ev[team_ev["type"] == "Substitution"]
    cutoff = subs["tempo"].min() if not subs.empty else team_ev["tempo"].max() + 1
    passes = team_ev[(team_ev["type"] == "Pass") & team_ev["passe_certo"]
                     & team_ev["pass_recipient"].notna() & (team_ev["tempo"] < cutoff)]
    pitch = _pitch()
    fig, ax = _figure(pitch)
    if passes.empty:
        return _empty(fig, ax, "Sem passes suficientes"), pd.DataFrame()
    locs = pd.concat([
        passes[["player", "x", "y"]],
        passes[["pass_recipient", "end_x", "end_y"]].set_axis(["player", "x", "y"], axis=1),
    ])
    avg = locs.groupby("player").agg(x=("x", "mean"), y=("y", "mean"))
    avg["passes"] = passes.groupby("player").size().reindex(avg.index).fillna(0)
    pairs = passes.assign(a=passes[["player", "pass_recipient"]].min(axis=1),
                          b=passes[["player", "pass_recipient"]].max(axis=1))
    pairs = pairs.groupby(["a", "b"]).size().reset_index(name="n")
    pairs = pairs[pairs["n"] >= min_passes]
    if not pairs.empty:
        width = pairs["n"] / pairs["n"].max() * 9
        alpha = (pairs["n"] / pairs["n"].max()).clip(0.25, 1).values
        rgba = np.array([plt.matplotlib.colors.to_rgba(LINE, a) for a in alpha])
        pitch.lines(avg.loc[pairs.a, "x"], avg.loc[pairs.a, "y"], avg.loc[pairs.b, "x"],
                    avg.loc[pairs.b, "y"], lw=width, color=rgba, ax=ax, zorder=3)
    sizes = avg["passes"] / max(avg["passes"].max(), 1) * 1300 + 250
    pitch.scatter(avg.x, avg.y, s=sizes, color=color, edgecolors=TEXT, lw=1.5, ax=ax, zorder=4)
    for name, row in avg.iterrows():
        pitch.annotate(str(jerseys.get(name, "?")), (row.x, row.y), ha="center", va="center",
                       color="black", fontsize=11, fontweight="bold", ax=ax, zorder=5)
    _title(ax, f"Rede de passes · {team}",
           f"Até a 1ª substituição ({cutoff:.0f}') · nós = posição média · linhas = ≥ {min_passes} passes entre a dupla")
    table = avg.reset_index().rename(columns={"player": "Jogador", "passes": "Passes"})
    table.insert(0, "Nº", table["Jogador"].map(jerseys))
    return fig, table[["Nº", "Jogador", "Passes"]].sort_values("Nº")


def heatmap(events, title, method="Grade"):
    pitch = _pitch()
    fig, ax = _figure(pitch)
    pts = events.dropna(subset=["x", "y"])
    if len(pts) < 3:
        return _empty(fig, ax, "Poucos eventos para gerar o mapa")
    if method == "Grade":
        bs = pitch.bin_statistic(pts.x, pts.y, statistic="count", bins=(6, 5), normalize=True)
        pitch.heatmap(bs, ax=ax, cmap=HEAT, edgecolors=PITCH_BG)
        pitch.label_heatmap(bs, color=TEXT, fontsize=12, ax=ax, ha="center", va="center",
                            str_format="{:.0%}", path_effects=STROKE)
    elif method == "Juego de Posición":
        bs = pitch.bin_statistic_positional(pts.x, pts.y, statistic="count", positional="full", normalize=True)
        pitch.heatmap_positional(bs, ax=ax, cmap=HEAT, edgecolors=PITCH_BG)
        pitch.label_heatmap(bs, color=TEXT, fontsize=11, ax=ax, ha="center", va="center",
                            str_format="{:.0%}", exclude_zeros=True, path_effects=STROKE)
    else:
        pitch.kdeplot(pts.x, pts.y, ax=ax, fill=True, levels=80, thresh=0, cut=4, cmap=HEAT)
    _title(ax, title, f"{len(pts)} eventos · ataque da esquerda para a direita")
    return fig


def pass_flow(events, title, bins=(6, 4)):
    pitch = _pitch()
    fig, ax = _figure(pitch)
    passes = events[(events["type"] == "Pass") & events["end_x"].notna()]
    if len(passes) < 5:
        return _empty(fig, ax, "Poucos passes para gerar o fluxo")
    bs = pitch.bin_statistic(passes.x, passes.y, statistic="count", bins=bins)
    pitch.heatmap(bs, ax=ax, cmap=HEAT, edgecolors=PITCH_BG, alpha=0.9)
    pitch.flow(passes.x, passes.y, passes.end_x, passes.end_y, color=TEXT, arrow_type="scale",
               arrow_length=14, bins=bins, ax=ax, zorder=3)
    _title(ax, title, "Cor = volume de passes na zona · seta = direção média · comprimento = distância média")
    return fig


def radar_compare(p1, p2, params, low, high, name1, name2):
    high = [h if h > l else l + 1 for l, h in zip(low, high)]
    radar = Radar(params, low, high, num_rings=4, ring_width=1, center_circle_radius=1)
    fig, ax = radar.setup_axis(figsize=(8, 8), facecolor=PITCH_BG)
    fig.set_facecolor(PITCH_BG)
    radar.draw_circles(ax=ax, facecolor="#244A3B", edgecolor="#3C6B57")
    radar.draw_radar_compare(p1, p2, ax=ax,
                             kwargs_radar={"facecolor": HOME, "alpha": 0.6},
                             kwargs_compare={"facecolor": AWAY, "alpha": 0.6})
    radar.draw_range_labels(ax=ax, fontsize=9, color=TEXT, path_effects=STROKE)
    radar.draw_param_labels(ax=ax, fontsize=12, color=TEXT, fontweight="bold")
    ax.text(0.02, 1.02, name1, color=HOME, fontsize=14, fontweight="bold", transform=ax.transAxes)
    ax.text(0.98, 1.02, name2, color=AWAY, fontsize=14, fontweight="bold", ha="right", transform=ax.transAxes)
    return fig


def xg_flow(events, home, away):
    colors = team_colors(home, away)
    shots = events[events["type"] == "Shot"]
    end = max(events["tempo"].max(), 90)
    fig, ax = plt.subplots(figsize=(11, 4.6))
    for t in (home, away):
        s = shots[shots["team"] == t].sort_values("tempo")
        x = np.concatenate([[0], s["tempo"].values, [end]])
        y = np.concatenate([[0], s["shot_statsbomb_xg"].fillna(0).cumsum().values,
                            [s["shot_statsbomb_xg"].sum()]])
        ax.step(x, y, where="post", color=colors[t], lw=2.6, label=f"{t} (xG {y[-1]:.2f})")
        goals = s[s["gol"]]
        gy = s["shot_statsbomb_xg"].fillna(0).cumsum()[s["gol"]]
        ax.scatter(goals["tempo"], gy, s=110, color=colors[t], edgecolor="black", zorder=5)
        for i, ((_, g), yy) in enumerate(zip(goals.iterrows(), gy)):
            ax.annotate(f"{short(g['player'])} {g['minute']}'", (g["tempo"], yy),
                        xytext=(-6, 8 if i % 2 == 0 else -14), textcoords="offset points",
                        fontsize=9, ha="right", color=colors[t], fontweight="bold")
    ax.axvline(45, color="grey", ls=":", lw=1)
    ax.axvline(90, color="grey", ls=":", lw=1)
    ax.set_xlabel("Minuto")
    ax.set_ylabel("xG acumulado")
    ax.set_title("Evolução do xG ao longo da partida (círculos = gols)", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def scatter_relation(df, x, y, hue_colors, labels=True, regression=True):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    if regression and len(df) > 2 and df[x].nunique() > 1:
        sns.regplot(data=df, x=x, y=y, scatter=False, color="#6B7F72", ax=ax,
                    line_kws={"lw": 1.5, "ls": "--"})
    sns.scatterplot(data=df, x=x, y=y, hue="Time", palette=hue_colors, s=110,
                    edgecolor="black", alpha=0.85, ax=ax)
    if labels:
        top = df.nlargest(8, y) if df[y].sum() else df.nlargest(8, x)
        for _, r in top.iterrows():
            ax.annotate(short(r["Jogador"]), (r[x], r[y]), xytext=(5, 4),
                        textcoords="offset points", fontsize=8)
    corr = df[[x, y]].corr().iloc[0, 1] if len(df) > 2 else np.nan
    ax.set_title(f"{y} × {x}  ·  correlação de Pearson r = {corr:.2f}" if pd.notna(corr) else f"{y} × {x}",
                 loc="left", fontweight="bold")
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


def correlation_heatmap(df, cols):
    fig, ax = plt.subplots(figsize=(9, 7))
    corr = df[cols].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, mask=mask, cmap="RdYlGn", vmin=-1, vmax=1, annot=True, fmt=".2f",
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.7}, ax=ax, annot_kws={"size": 8})
    ax.set_title("Correlação entre estatísticas dos jogadores", loc="left", fontweight="bold")
    fig.tight_layout()
    return fig


def events_timeline(events, hue_colors, bin_size=15, event_type="Passe"):
    ev = events[events["tipo"] == event_type].copy()
    ev["Faixa"] = (ev["minute"] // bin_size * bin_size).astype(int)
    ev["Faixa"] = ev["Faixa"].astype(str) + "–" + (ev["Faixa"] + bin_size).astype(str) + "'"
    order = sorted(ev["Faixa"].unique(), key=lambda s: int(s.split("–")[0]))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    sns.countplot(data=ev, x="Faixa", hue="team", order=order, palette=hue_colors, ax=ax)
    ax.set_xlabel("Intervalo de minutos")
    ax.set_ylabel(f"{event_type} (qtd.)")
    ax.set_title(f"{event_type} por intervalo de {bin_size} minutos", loc="left", fontweight="bold")
    ax.legend(title=None, frameon=False)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig
