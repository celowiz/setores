"""Universo do projeto: setores dos EUA (ETFs SPDR) e do Brasil (índices setoriais da B3)."""

US_BENCH = "SPY"
US_ORDER = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
BR_BENCH = "IBOV"
BR_ORDER = ["ICON", "IEEX", "IFNC", "IMAT", "IMOB", "INDX", "UTIL"]

# Nomes curtos (pt, en). Os mesmos textos ficam em js/i18n.js para a página.
NAMES = {
    "XLB": ("Materiais", "Materials"),
    "XLC": ("Comunicação", "Communication Services"),
    "XLE": ("Energia", "Energy"),
    "XLF": ("Financeiro", "Financials"),
    "XLI": ("Industrial", "Industrials"),
    "XLK": ("Tecnologia", "Technology"),
    "XLP": ("Consumo básico", "Consumer Staples"),
    "XLRE": ("Imobiliário", "Real Estate"),
    "XLU": ("Utilidades", "Utilities"),
    "XLV": ("Saúde", "Health Care"),
    "XLY": ("Consumo discricionário", "Consumer Discretionary"),
    "SPY": ("S&P 500", "S&P 500"),
    "ICON": ("Consumo", "Consumer"),
    "IEEX": ("Energia elétrica", "Electric Power"),
    "IFNC": ("Financeiro", "Financials"),
    "IMAT": ("Materiais básicos", "Basic Materials"),
    "IMOB": ("Imobiliário", "Real Estate"),
    "INDX": ("Industrial", "Industrials"),
    "UTIL": ("Utilidade pública", "Utilities"),
    "IBOV": ("Ibovespa", "Ibovespa"),
}

SRC = {
    "us": {
        "pt": "Yahoo Finance (yfinance), fechamento ajustado por proventos (retorno total)",
        "en": "Yahoo Finance (yfinance), dividend-adjusted close (total return)",
    },
    "br": {
        "pt": "B3, API pública de estatísticas de índices (pontos de fechamento; índices de preço)",
        "en": "B3 public index statistics API (closing points; price indices)",
    },
}
