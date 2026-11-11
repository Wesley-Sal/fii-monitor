"""Busca cotações e proventos dos FIIs e grava em data.json."""
import json
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


def main() -> None:
    fundos, erros = [], []
    for t in TICKERS:
        try:
            fundos.append(coletar(t))
        except Exception as e:  # um ticker com falha não derruba os outros
            erros.append({"ticker": t, "erro": str(e)})

    saida = {
        "atualizado_em": datetime.now(BRT).strftime("%d/%m/%Y %H:%M"),
        "fundos": fundos,
        "erros": erros,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"{len(fundos)} ok, {len(erros)} com erro")


if __name__ == "__main__":
    main()
