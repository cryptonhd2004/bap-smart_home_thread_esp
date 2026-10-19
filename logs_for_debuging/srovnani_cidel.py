"""Porovnani teplotnich cidel: ALPSTUGA (SEN63C) vs BMP180 vs DHT11.

Vstup:  CSV z Home Assistantu se sloupci entity_id, state, last_changed.
Vystup: grafy (PNG, PDF), tabulka pro LaTeX a souhrn statistik ve slozce
        'output' umistene vedle tohoto skriptu.

Pouziti: python srovnani_cidel.py [cesta_k_csv]
Zavislosti: pip install pandas numpy matplotlib
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "alpstuga_vs_bmp180_vs_dht11.csv"
OUT = HERE / "output"
TZ = "Europe/Prague"
STATS_FROM = "2026-10-10 00:00"   # statistiky bez prechodoveho deje (vetrani)
TOL = 0.7                         # tolerance SEN63C (max.) v C
NAMES = {"A": "ALPSTUGA (SEN63C)", "B": "BMP180", "D": "DHT11"}
MAP = {"alpstuga": "A", "teplota_1": "B", "teplota_5": "D"}
PAIRS = (("B", "A"), ("D", "A"), ("D", "B"))


def load(path):
    df = pd.read_csv(path)
    # cas jako naivni mistni cas (bez tz sloupce) - obchazi pad pandas na Windows
    t = (pd.to_datetime(df["last_changed"], utc=True)
         .dt.tz_convert(TZ).dt.tz_localize(None))
    v = pd.to_numeric(df["state"], errors="coerce")
    ent = df["entity_id"].astype(str)
    series = {}
    for key, code in MAP.items():
        mask = (ent.str.contains(key) & v.notna()).to_numpy()
        if not mask.any():
            sys.exit(f"V CSV nenalezena entita obsahujici '{key}' (upravte MAP).")
        s = pd.Series(v.to_numpy()[mask],
                      index=pd.DatetimeIndex(t.to_numpy()[mask]))
        series[code] = s[~s.index.duplicated()]
    return series


def align(series, freq="1min"):
    start = max(s.index.min() for s in series.values()).ceil(freq)
    end = min(s.index.max() for s in series.values())
    idx = pd.date_range(start, end, freq=freq)
    cols = {k: s.reindex(s.index.union(idx)).ffill().reindex(idx)
            for k, s in series.items()}
    return pd.DataFrame(cols).dropna()


def stats_row(x, y):
    d = (x - y).dropna()
    m, s = d.mean(), d.std(ddof=1)
    return {"n": len(d), "mean": m, "median": d.median(), "std": s,
            "loa_lo": m - 1.96 * s, "loa_hi": m + 1.96 * s,
            "rmse": float(np.sqrt((d ** 2).mean())),
            "within": (d.abs() <= TOL).mean() * 100,
            "r": x.corr(y)}


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=200)
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)


def plot_timeseries(R):
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for c in "ABD":
        ax[0].plot(R.index, R[c], label=NAMES[c], lw=1)
    ax[0].set_ylabel("Teplota [°C]")
    ax[0].set_title("Časový průběh teploty")
    ax[0].legend()
    ax[0].grid(alpha=.3)
    for x, y in PAIRS:
        ax[1].plot(R.index, R[x] - R[y], lw=1,
                   label=f"{NAMES[x]} − {NAMES[y]}")
    ax[1].axhline(0, color="k", lw=.5)
    ax[1].set_ylabel("Rozdíl [°C]")
    ax[1].set_xlabel("Čas (místní)")
    ax[1].legend()
    ax[1].grid(alpha=.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    save(fig, "casovy_prubeh")


def plot_diurnal(R):
    fig, ax = plt.subplots(figsize=(8, 4))
    for x, y in (("B", "A"), ("D", "A")):
        med = (R[x] - R[y]).groupby(R.index.hour).median()
        ax.plot(med.index, med.values, marker="o",
                label=f"{NAMES[x]} − {NAMES[y]}")
    ax.axhline(0, color="k", lw=.5)
    ax.set_xlabel("Hodina dne")
    ax.set_ylabel("Medián rozdílu [°C]")
    ax.set_title("Denní chod rozdílu")
    ax.legend()
    ax.grid(alpha=.3)
    fig.tight_layout()
    save(fig, "denni_chod")


def plot_bland_altman(Q):
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, (x, y) in zip(axs, PAIRS):
        mean = (Q[x] + Q[y]) / 2
        d = Q[x] - Q[y]
        m, s = d.mean(), d.std(ddof=1)
        ax.scatter(mean, d, s=4, alpha=.35)
        ax.axhline(m, color="r", label=f"průměr {m:+.2f} °C")
        ax.axhline(m + 1.96 * s, color="gray", ls="--", label="±1,96 s")
        ax.axhline(m - 1.96 * s, color="gray", ls="--")
        ax.set_title(f"{NAMES[x]} − {NAMES[y]}")
        ax.set_xlabel("Průměr obou čidel [°C]")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    axs[0].set_ylabel("Rozdíl [°C]")
    fig.tight_layout()
    save(fig, "bland_altman")


def latex_table(rows):
    f = lambda v, p=2: f"{v:.{p}f}".replace(".", ",")
    lines = [
        r"\begin{table}[ht]",
        r"\centering",
        r"\caption{Porovnání teplotních čidel (rozdíl prvního a druhého čidla)}",
        r"\label{tab:porovnani-cidel}",
        r"\begin{tabular}{lrrrrrr}",
        r"\hline",
        r"Dvojice & $n$ & $\bar{d}$ [\si{\celsius}] & $s_d$ [\si{\celsius}] "
        r"& LoA [\si{\celsius}] & RMSE [\si{\celsius}] "
        r"& $|d|\le 0{,}7$ [\%] \\",
        r"\hline",
    ]
    for name, r in rows:
        loa = f"{f(r['loa_lo'])} až {f(r['loa_hi'])}"
        lines.append(f"{name} & {r['n']} & {f(r['mean'])} & {f(r['std'])} & "
                     f"{loa} & {f(r['rmse'])} & {f(r['within'], 1)} \\\\")
    lines += [r"\hline", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def main():
    if not CSV.exists():
        sys.exit(f"CSV nenalezeno: {CSV}")
    OUT.mkdir(exist_ok=True)

    R = align(load(CSV))
    if R.empty:
        sys.exit("Zadna spolecna data pro vsechna tri cidla.")
    Q = R[STATS_FROM:]
    if Q.empty:
        print("STATS_FROM je mimo rozsah dat, pouzivam cely zaznam.")
        Q = R

    plot_timeseries(R)
    plot_diurnal(R)
    plot_bland_altman(Q)

    rows = [(f"{NAMES[x]} − {NAMES[y]}", stats_row(Q[x], Q[y]))
            for x, y in PAIRS]
    (OUT / "tabulka_porovnani.tex").write_text(latex_table(rows),
                                               encoding="utf-8")
    pd.DataFrame({n: r for n, r in rows}).T.round(3).to_csv(
        OUT / "souhrn_statistik.csv")

    print(latex_table(rows))
    print("\nHotovo, vystup je v:", OUT)


if __name__ == "__main__":
    import traceback
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        print("Spoustim, CSV:", CSV)
        main()
    except SystemExit as e:
        print("KONEC:", e)
        raise
    except Exception:
        err = traceback.format_exc()
        (HERE / "chyba.log").write_text(err, encoding="utf-8")
        print(err)
        raise