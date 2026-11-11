"""Busca cotações e proventos dos FIIs e grava em data.json."""
import json
import sys
from datetime import datetime, timedelta, timezone

import yfinance as yf

TICKERS = [
    "GARE11", "FGAA11", "RZAG11", "CPTS11",
    "SNAG11", "SNEL11", "TRXF11", "BODB11",
]
BRT = timezone(timedelta(hours=-3))


def pct(atual: float, base: float) -> float | None:
    return round((atual / base - 1) * 100, 2) if base else None


def coletar(ticker: str) -> dict:
    ativo = yf.Ticker(f"{ticker}.SA")
    hist = ativo.history(period="1y", auto_adjust=False)
    if hist.empty:
        raise ValueError("sem histórico")

    fechamentos = hist["Close"]
    preco = float(fechamentos.iloc[-1])
    ontem = float(fechamentos.iloc[-2]) if len(fechamentos) > 1 else preco
    mes = float(fechamentos.iloc[-22]) if len(fechamentos) > 22 else float(fechamentos.iloc[0])

    divs = ativo.dividends
    ultimo_prov = float(divs.iloc[-1]) if len(divs) else None
    soma_12m = float(divs.tail(12).sum()) if len(divs) else 0.0

    return {
        "ticker": ticker,
        "preco": round(preco, 2),
        "dia_pct": pct(preco, ontem),
        "mes_pct": pct(preco, mes),
        "min_52s": round(float(fechamentos.min()), 2),
        "max_52s": round(float(fechamentos.max()), 2),
        "ultimo_provento": round(ultimo_prov, 4) if ultimo_prov else None,
        "dy_12m_pct": round(soma_12m / preco * 100, 2) if preco else None,
    }


CONFIG = "config.json"
FOLGA_MIN = 7  # o agendador do GitHub costuma atrasar alguns minutos


def ler_json(caminho: str, padrao: dict) -> dict:
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def deve_atualizar(intervalo_min: int) -> bool:
    """Nas execuções agendadas, só atualiza se já passou o intervalo escolhido."""
    ultimo = ler_json("data.json", {}).get("atualizado_ts")
    if not ultimo:
        return True
    passados = (datetime.now(timezone.utc).timestamp() - ultimo) / 60
    return passados >= intervalo_min - FOLGA_MIN


def main() -> None:
    args = sys.argv[1:]
    config = ler_json(CONFIG, {"intervalo_min": 60})

    # --intervalo N  grava o novo intervalo escolhido
    if "--intervalo" in args:
        valor = args[args.index("--intervalo") + 1]
        if valor.isdigit():
            config["intervalo_min"] = int(valor)
            with open(CONFIG, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"Intervalo alterado para {valor} min")

    intervalo = int(config.get("intervalo_min", 60))
    if "--agendado" in args and not deve_atualizar(intervalo):
        print(f"Ainda não deu {intervalo} min desde a última atualização; pulando.")
        return

    fundos, erros = [], []
    for t in TICKERS:
        try:
            fundos.append(coletar(t))
        except Exception as e:  # um ticker com falha não derruba os outros
            erros.append({"ticker": t, "erro": str(e)})

    saida = {
        "atualizado_em": datetime.now(BRT).strftime("%d/%m/%Y %H:%M"),
        "atualizado_ts": int(datetime.now(timezone.utc).timestamp()),
        "intervalo_min": intervalo,
        "fundos": fundos,
        "erros": erros,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"{len(fundos)} ok, {len(erros)} com erro")


if __name__ == "__main__":
    main()
