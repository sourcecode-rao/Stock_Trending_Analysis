import pandas as pd


def compute_moving_averages(df: pd.DataFrame, windows=[7, 21, 50]):
    """Return DataFrame with moving averages added."""
    res = df[['Close']].copy()
    for w in windows:
        res[f'SMA_{w}'] = df['Close'].rolling(window=w).mean()
        res[f'EMA_{w}'] = df['Close'].ewm(span=w, adjust=False).mean()
    return res.dropna()


def compute_price_stats(df: pd.DataFrame):
    """Return basic price stats for display."""
    return {
        'open': float(df['Open'].iloc[-1]),
        'close': float(df['Close'].iloc[-1]),
        'high': float(df['High'].max()),
        'low': float(df['Low'].min()),
        'volume': int(df['Volume'].iloc[-1])
    }


def prepare_candlestick_data(df: pd.DataFrame):
    """Return simplified structure for candlestick chart."""
    cs = df[['Open', 'High', 'Low', 'Close']].copy()
    cs.index = cs.index.astype(str)
    return cs
