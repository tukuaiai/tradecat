"""Symbol 格式处理"""


def normalize_symbol(symbol: str) -> str:
    """
    标准化 symbol 格式
    BTC -> BTCUSDT
    BTCUSDT -> BTCUSDT
    """
    symbol = symbol.upper().strip()
    if not symbol.endswith("USDT"):
        symbol = f"{symbol}USDT"
    return symbol


def to_base_symbol(symbol: str) -> str:
    """
    转换为基础 symbol (CoinGlass 格式)
    BTCUSDT -> BTC
    """
    symbol = symbol.upper().strip()
    if symbol.endswith("USDT"):
        return symbol[:-4]
    return symbol
