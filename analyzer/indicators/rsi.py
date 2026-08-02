import pandas as pd
from scipy.signal import find_peaks


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates standard Wilder's RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
    return 100 - (100 / (1 + rs))


def detect_rsi_divergences(
    df: pd.DataFrame, rsi_period: int = 14, order: int = 5
) -> pd.DataFrame:
    """
    Programmatically detects Regular and Hidden RSI Divergences.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'High', 'Low', 'Close' columns.
    rsi_period : int
        Lookback window for RSI calculation.
    order : int
        Distance parameter for local peak/trough confirmation.
        Higher values filter out market noise.
    """
    data = df.copy()
    data["RSI"] = calculate_rsi(data["Close"], period=rsi_period)

    # Initialize output signal columns (0 = None, 1 = Signal Detected)
    data["Reg_Bullish_Div"] = 0
    data["Reg_Bearish_Div"] = 0
    data["Hid_Bullish_Div"] = 0
    data["Hid_Bearish_Div"] = 0

    # 1. Identify local extrema using scipy find_peaks
    # Troughs are identified by inverting the series (-series)
    price_troughs, _ = find_peaks(-data["Low"].values, distance=order)
    price_peaks, _ = find_peaks(data["High"].values, distance=order)

    rsi_troughs, _ = find_peaks(-data["RSI"].values, distance=order)
    rsi_peaks, _ = find_peaks(data["RSI"].values, distance=order)

    # 2. Evaluate Bullish Divergences (Trough Comparisons)
    for i in range(1, len(price_troughs)):
        curr_p_idx = price_troughs[i]
        prev_p_idx = price_troughs[i - 1]

        # Locate closest RSI troughs corresponding to price troughs
        curr_rsi_idx = min(rsi_troughs, key=lambda x: abs(x - curr_p_idx))
        prev_rsi_idx = min(rsi_troughs, key=lambda x: abs(x - prev_p_idx))

        # Ensure RSI troughs temporally align with price troughs (within tolerance)
        if (
            abs(curr_rsi_idx - curr_p_idx) <= order
            and abs(prev_rsi_idx - prev_p_idx) <= order
        ):
            p_curr, p_prev = (
                data["Low"].iloc[curr_p_idx],
                data["Low"].iloc[prev_p_idx],
            )
            rsi_curr, rsi_prev = (
                data["RSI"].iloc[curr_rsi_idx],
                data["RSI"].iloc[prev_rsi_idx],
            )

            # Regular Bullish: Price Lower Low + RSI Higher Low
            if p_curr < p_prev and rsi_curr > rsi_prev:
                data.iloc[
                    curr_p_idx, data.columns.get_loc("Reg_Bullish_Div")
                ] = 1

            # Hidden Bullish: Price Higher Low + RSI Lower Low
            elif p_curr > p_prev and rsi_curr < rsi_prev:
                data.iloc[
                    curr_p_idx, data.columns.get_loc("Hid_Bullish_Div")
                ] = 1

    # 3. Evaluate Bearish Divergences (Peak Comparisons)
    for i in range(1, len(price_peaks)):
        curr_p_idx = price_peaks[i]
        prev_p_idx = price_peaks[i - 1]

        curr_rsi_idx = min(rsi_peaks, key=lambda x: abs(x - curr_p_idx))
        prev_rsi_idx = min(rsi_peaks, key=lambda x: abs(x - prev_p_idx))

        if (
            abs(curr_rsi_idx - curr_p_idx) <= order
            and abs(prev_rsi_idx - prev_p_idx) <= order
        ):
            p_curr, p_prev = (
                data["High"].iloc[curr_p_idx],
                data["High"].iloc[prev_p_idx],
            )
            rsi_curr, rsi_prev = (
                data["RSI"].iloc[curr_rsi_idx],
                data["RSI"].iloc[prev_rsi_idx],
            )

            # Regular Bearish: Price Higher High + RSI Lower High
            if p_curr > p_prev and rsi_curr < rsi_prev:
                data.iloc[
                    curr_p_idx, data.columns.get_loc("Reg_Bearish_Div")
                ] = 1

            # Hidden Bearish: Price Lower High + RSI Higher High
            elif p_curr < p_prev and rsi_curr > rsi_prev:
                data.iloc[
                    curr_p_idx, data.columns.get_loc("Hid_Bearish_Div")
                ] = 1

    return data
