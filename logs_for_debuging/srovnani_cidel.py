"""Univerzalni skript pro porovnani cidel (teplota, vlhkost) z exportu Home Assistantu.

Vstup:  CSV se sloupci entity_id, state, last_changed.
Vystup: slozka 'output' (nebo --vystup): grafy (PNG, PDF), souhrny (CSV)
        a tabulky pro LaTeX. Statistiky jsou dvoje: z celeho okna a jen
        z "klidnych" minut (bez rychlych zmen, napr. vetrani).

Pouziti:
  python srovnani_cidel.py                       (final_comparison.csv vedle skriptu)
  python srovnani_cidel.py data.csv
  python srovnani_cidel.py data.csv --od "2026-10-26 08:00" --do "2026-10-27 08:00" --ustaleni 2
  python srovnani_cidel.py data.csv --vystup output_krabice --ref S --vsechny-dvojice

Volby:
  --od, --do         okno mereni (mistni cas); bez nich cely spolecny zaznam
  --ustaleni HODIN   prvnich N hodin okna se do statistik nepocita (v grafu sede)
  --ref KOD          referencni cidlo (vychozi S = SHT40)
  --vsechny-dvojice  porovnat vsechny dvojice, ne jen cidla proti reference
  --vystup SLOZKA    vystupni slozka (vychozi 'output' vedle skriptu)

Pridani cidla = jeden radek v seznamu 'sensors' dane veliciny.
Zavislosti: pip install pandas numpy matplotlib
"""
import argparse
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
TZ = "Europe/Prague"

QUANTITIES = {
    "teplota": {
        "unit": "°C", "unit_tex": r"\si{\celsius}", "tol": 0.7,
        "calm_max_change": 0.15,   # max. zmena za 10 min v "klidnych" minutach
        "sensors": [   # (kod, text v entity_id, popisek)
            ("S", "teplota_6", "SHT40"),
            ("A", "alpstuga_air_quality_monitor_teplota", "ALPSTUGA (SEN63C)"),
            ("B", "teplota_1", "BMP180"),
            ("D", "teplota_5", "DHT11"),
            ("F", "timmerflotte_temp_hmd_sensor_teplota", "TIMMERFLOTTE"),
        ],
    },
    "vlhkost": {
        "unit": "%RH", "unit_tex": r"\%RH", "tol": 3.0,
        "calm_max_change": 1.0,
        "sensors": [
            ("S", "vlhkost_vzduchu_7", "SHT40"),
            ("A", "alpstuga_air_quality_monitor_vlhkost", "ALPSTUGA (SEN63C)"),
            ("D", "vlhkost_vzduchu_8", "DHT11"),
            ("F", "timmerflotte_temp_hmd_sensor_vlhkost", "TIMMERFLOTTE"),
        ],
    },
}


def read_csv(path):
    df = pd.read_csv(path)
    # naivni mistni cas (bez tz) - obchazi problemy pandas na Windows
    t = (pd.to_datetime(df["last_changed"], utc=True)
         .dt.tz_convert(TZ).dt.tz_localize(None))
    v = pd.to_numeric(df["state"], errors="coerce")
    return t, v, df["entity_id"].astype(str).str.lower()


def load(t, v, ent, sensors):
    out = {}
    for code, key, _ in sensors:
        m = (ent.str.contains(key.lower()) & v.notna()).to_numpy()
        if not m.any():
            sys.exit(f"V CSV nenalezena entita obsahujici '{key}' "
                     f"(upravte QUANTITIES).")
        s = pd.Series(v.to_numpy()[m], index=pd.DatetimeIndex(t.to_numpy()[m]))
        out[code] = s[~s.index.duplicated()]
    return out


def align(series, start, end, freq="1min"):
    # HA uklada jen zmeny -> mezi zmenami plati posledni zname hodnota (ffill)
    lo = max(s.index.min() for s in series.values())
    hi = min(s.index.max() for s in series.values())
    if start is not None:
        lo = max(lo, start)
    if end is not None:
        hi = min(hi, end)
    idx = pd.date_range(lo.ceil(freq), hi, freq=freq)
    cols = {k: s.reindex(s.index.union(idx)).ffill().reindex(idx)
            for k, s in series.items()}
    return pd.DataFrame(cols).dropna()


def make_pairs(codes, ref, all_pairs):
    if all_pairs:
        return [(x, y) for i, x in enumerate(codes) for y in codes[:i]]
    return [(c, ref) for c in codes if c != ref]


def stats_row(x, y, tol):
    d = x - y
    m, s = d.mean(), d.std(ddof=1)
    slope, icpt = np.polyfit(y, x, 1) if y.std() > 0 else (np.nan, np.nan)
    return {"n": len(d), "mean": m, "median": d.median(), "std": s,
            "loa_lo": m - 1.96 * s, "loa_hi": m + 1.96 * s,
            "rmse": float(np.sqrt((d ** 2).mean())),
            "within": (d.abs() <= tol).mean() * 100,
            "r": x.corr(y), "slope": slope, "intercept": icpt}


def grid(n):
    cols = 2 if n == 4 else min(n, 3)
    return int(np.ceil(n / cols)), cols


def save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=200)
    fig.savefig(out / f"{name}.pdf")
    plt.close(fig)


def plot_timeseries(R, settle_end, q, cfg, names, pairs, out):
    u = cfg["unit"]
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for c in R.columns:
        ax[0].plot(R.index, R[c], lw=1, label=names[c])
    ax[0].set_ylabel(f"{q.capitalize()} [{u}]")
    ax[0].set_title(f"Časový průběh: {q}")
    for x, y in pairs:
        ax[1].plot(R.index, R[x] - R[y], lw=1,
                   label=f"{names[x]} − {names[y]}")
    ax[1].axhline(0, color="k", lw=.5)
    ax[1].set_ylabel(f"Rozdíl [{u}]")
    ax[1].set_xlabel("Čas (místní)")
    for a in ax:
        if settle_end > R.index.min():
            a.axvspan(R.index.min(), settle_end, color="gray", alpha=.2,
                      label="ustalování" if a is ax[0] else None)
        a.grid(alpha=.3)
        a.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    save(fig, out, f"casovy_prubeh_{q}")


def plot_diurnal(Q, q, cfg, names, pairs, out):
    fig, ax = plt.subplots(figsize=(8, 4))
    for x, y in pairs:
        med = (Q[x] - Q[y]).groupby(Q.index.hour).median()
        ax.plot(med.index, med.values, marker="o",
                label=f"{names[x]} − {names[y]}")
    ax.axhline(0, color="k", lw=.5)
    ax.set_xlabel("Hodina dne")
    ax.set_ylabel(f"Medián rozdílu [{cfg['unit']}]")
    ax.set_title(f"Denní chod rozdílu: {q}")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.tight_layout()
    save(fig, out, f"denni_chod_{q}")


def plot_box(Q, q, cfg, names, pairs, suffix, out):
    fig, ax = plt.subplots(figsize=(max(6, 1.6 * len(pairs) + 2), 4.5))
    ax.boxplot([Q[x] - Q[y] for x, y in pairs], showfliers=False)
    ax.set_xticks(range(1, len(pairs) + 1))
    ax.set_xticklabels([f"{names[x]}\n− {names[y]}" for x, y in pairs],
                       fontsize=8)
    ax.axhline(0, color="k", lw=.5)
    ax.set_ylabel(f"Rozdíl [{cfg['unit']}]")
    ax.set_title(f"Rozdělení rozdílů: {q}")
    ax.grid(alpha=.3, axis="y")
    fig.tight_layout()
    save(fig, out, f"boxplot_{q}{suffix}")


def plot_regression(Q, q, cfg, names, pairs, suffix, out):
    u = cfg["unit"]
    rows, cols = grid(len(pairs))
    fig, axs = plt.subplots(rows, cols, figsize=(4.7 * cols, 4.4 * rows),
                            squeeze=False)
    flat = axs.ravel()
    for ax, (x, y) in zip(flat, pairs):
        ax.scatter(Q[y], Q[x], s=4, alpha=.35)
        lo, hi = min(Q[y].min(), Q[x].min()), max(Q[y].max(), Q[x].max())
        ax.plot([lo, hi], [lo, hi], "k--", lw=.8, label="y = x")
        if Q[y].std() > 0:
            k, b = np.polyfit(Q[y], Q[x], 1)
            xs = np.array([Q[y].min(), Q[y].max()])
            ax.plot(xs, k * xs + b, "r", lw=1.2,
                    label=f"fit: y = {k:.2f}x {b:+.2f}")
        ax.set_xlabel(f"{names[y]} [{u}]")
        ax.set_ylabel(f"{names[x]} [{u}]")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    for ax in flat[len(pairs):]:
        ax.axis("off")
    fig.tight_layout()
    save(fig, out, f"regrese_{q}{suffix}")


def plot_bland_altman(Q, q, cfg, names, pairs, suffix, out):
    u = cfg["unit"]
    rows, cols = grid(len(pairs))
    fig, axs = plt.subplots(rows, cols, figsize=(4.7 * cols, 4.2 * rows),
                            sharey=True, squeeze=False)
    flat = axs.ravel()
    for ax, (x, y) in zip(flat, pairs):
        mean, d = (Q[x] + Q[y]) / 2, Q[x] - Q[y]
        m, s = d.mean(), d.std(ddof=1)
        ax.scatter(mean, d, s=4, alpha=.35)
        ax.axhline(m, color="r", label=f"průměr {m:+.2f} {u}")
        ax.axhline(m + 1.96 * s, color="gray", ls="--", label="±1,96 s")
        ax.axhline(m - 1.96 * s, color="gray", ls="--")
        ax.set_title(f"{names[x]} − {names[y]}", fontsize=10)
        ax.set_xlabel(f"Průměr obou čidel [{u}]")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    for ax in flat[len(pairs):]:
        ax.axis("off")
    for r in range(rows):
        axs[r, 0].set_ylabel(f"Rozdíl [{u}]")
    fig.tight_layout()
    save(fig, out, f"bland_altman_{q}{suffix}")


def latex_table(rows, q, cfg, suffix, extra):
    f = lambda v, p=2: f"{v:.{p}f}".replace(".", ",")
    ut, tol = cfg["unit_tex"], str(cfg["tol"]).replace(".", "{,}")
    L = [r"\begin{table}[ht]", r"\centering",
         rf"\caption{{Porovnání čidel ({q}), rozdíl prvního a druhého čidla"
         rf"{extra}}}",
         rf"\label{{tab:porovnani-{q}{suffix}}}",
         r"\begin{tabular}{lrrrrrrr}", r"\hline",
         rf"Dvojice & $n$ & $\bar{{d}}$ [{ut}] & $s_d$ [{ut}] & LoA [{ut}] "
         rf"& RMSE [{ut}] & $|d|\le {tol}$ [\%] & směrnice \\", r"\hline"]
    for name, r in rows:
        loa = f"{f(r['loa_lo'])} až {f(r['loa_hi'])}"
        L.append(f"{name} & {r['n']} & {f(r['mean'])} & {f(r['std'])} & {loa} "
                 f"& {f(r['rmse'])} & {f(r['within'], 1)} & {f(r['slope'])} \\\\")
    L += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(L)


def process(q, cfg, t, v, ent, a, out):
    names = {c: n for c, _, n in cfg["sensors"]}
    codes = [c for c, _, _ in cfg["sensors"]]
    if a.ref not in codes:
        sys.exit(f"Referencni cidlo '{a.ref}' neni v seznamu: {codes}")
    pairs = make_pairs(codes, a.ref, a.vsechny_dvojice)
    start = pd.Timestamp(a.od) if a.od else None
    end = pd.Timestamp(a.do) if a.do else None
    R = align(load(t, v, ent, cfg["sensors"]), start, end)
    if R.empty:
        sys.exit(f"Ve zvolenem okne nejsou spolecna data ({q}).")
    settle_end = R.index.min() + pd.Timedelta(hours=a.ustaleni)
    calm = R.diff(10).abs().max(axis=1) < cfg["calm_max_change"]
    Qall = R[R.index >= settle_end]
    if Qall.empty:
        sys.exit(f"Po ustalovani nezbyla data ({q}); zkratte --ustaleni.")
    Qcalm = Qall[calm.reindex(Qall.index)]
    print(f"[{q}] okno {R.index.min()} az {R.index.max()}, ve sta