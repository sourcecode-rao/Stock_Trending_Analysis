import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Optional imports for LSTM
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    LSTM_AVAILABLE = True
except Exception:
    LSTM_AVAILABLE = False

# Import ARIMA for time series forecasting
from statsmodels.tsa.arima.model import ARIMA


def arima_forecast(series: pd.Series, steps=30, order=(5, 1, 0)) -> pd.DataFrame:
    """Forecast future values using ARIMA."""
    series = series.dropna()
    model = ARIMA(series, order=order)
    model_fit = model.fit()
    forecast_res = model_fit.get_forecast(steps=steps)
    forecast = forecast_res.predicted_mean

    # Use inclusive='right' instead of closed='right' (new pandas versions)
    idx = pd.date_range(start=series.index[-1], periods=steps + 1, inclusive='right', freq='D')
    return pd.DataFrame({'forecast': forecast.values}, index=idx)


def lstm_forecast(series: pd.Series, steps=30):
    """Forecast future values using an LSTM neural network."""
    if not LSTM_AVAILABLE:
        raise RuntimeError('LSTM dependencies not available. Install tensorflow to use LSTM forecast.')

    # Scale the data
    scaler = MinMaxScaler()
    vals = series.values.reshape(-1, 1)
    scaled = scaler.fit_transform(vals)

    # Prepare sequences
    seq_len = 60
    X, y = [], []
    for i in range(seq_len, len(scaled)):
        X.append(scaled[i - seq_len:i, 0])
        y.append(scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    # Build LSTM model
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')

    # Train briefly for demonstration
    model.fit(X, y, epochs=5, batch_size=16, verbose=0)

    # Forecast next steps
    last_seq = scaled[-seq_len:]
    preds = []
    cur_seq = last_seq.copy()
    for _ in range(steps):
        x = cur_seq.reshape((1, seq_len, 1))
        p = model.predict(x, verbose=0)[0, 0]
        preds.append(p)
        cur_seq = np.vstack([cur_seq[1:], [[p]]])

    preds = scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()
    idx = pd.date_range(start=series.index[-1], periods=steps + 1, inclusive='right', freq='D')

    return pd.DataFrame({'forecast': preds}, index=idx)
