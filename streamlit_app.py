import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.title("Range Breakout Finder (Multi-Symbol, Main Candle, Sliding Window, Counter ≥ N)")

symbol_options = [
    "VBL", "FCL", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "MARUTI", "LT", "HEROMOTOCO"
]

select_all = st.checkbox("Select All Symbols")
if select_all:
    symbols = st.multiselect("Select Company Symbols", options=symbol_options, default=symbol_options, key="symbols")
else:
    symbols = st.multiselect("Select Company Symbols", options=symbol_options, default=["VBL", "FCL"], key="symbols")

start_date = st.date_input("Start Date:", value=datetime.today()-timedelta(days=365*3))
end_date = st.date_input("End Date:", value=datetime.today())
counter = st.number_input("Counter Value (Minimum inside-range candles before breakout):", min_value=2, max_value=50, value=5)
use_wick = st.checkbox("Require >50% inside candles to be 'wicky' (body < wick)?", value=False)

all_charts = []

if st.button("Find Breakouts"):
    for symbol in symbols:
        with st.spinner(f"Fetching data for {symbol}..."):
            data = yf.download(symbol + ".NS", start=start_date, end=end_date, progress=False, interval="1d", multi_level_index=False)
            if data.empty:
                continue
            df = data.reset_index()

        def wick_body_stats(row):
            body = abs(row['Close'] - row['Open'])
            wick = (row['High'] - row['Low']) - body
            return pd.Series({'body': body, 'wick': wick})

        df[['body', 'wick']] = df.apply(wick_body_stats, axis=1)

        breakouts = []
        i = 0
        while i < len(df) - counter - 1:
            main_high = df.loc[i, 'High']
            main_low = df.loc[i, 'Low']
            inside_count = 0
            wicky_count = 0
            for j in range(i+1, len(df)):
                curr_high = df.loc[j, 'High']
                curr_low = df.loc[j, 'Low']
                if curr_high <= main_high and curr_low >= main_low:
                    inside_count += 1
                    if df.loc[j, 'body'] < df.loc[j, 'wick']:
                        wicky_count += 1
                else:
                    breakout = df.loc[j]
                    wick_percent = (wicky_count / inside_count) if inside_count > 0 else 0
                    if inside_count >= counter:
                        if breakout['Close'] > main_high:
                            direction = "UP"
                        elif breakout['Open'] < main_low:
                            direction = "DOWN"
                        else:
                            direction = None
                        if direction and (not use_wick or wick_percent > 0.5):
                            breakouts.append({
                                "Breakout Index": j,
                                "Main Candle": df.loc[i, 'Date'],
                                "Breakout Date": breakout['Date'],
                                "Direction": direction,
                                "Breakout Open": breakout['Open'],
                                "Breakout Close": breakout['Close'],
                                "Range High": main_high,
                                "Range Low": main_low,
                                "Inside Count": inside_count,
                                "Wicky %": round(100 * wick_percent, 1),
                            })
                    break
            i += 1

        if breakouts:
            result_df = pd.DataFrame(breakouts)

            fig = go.Figure(data=[
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Candles"
                )
            ])
            for r in breakouts:
                color = "aqua" if r["Direction"] == "UP" else "purple"
                fig.add_vrect(
                    x0=r["Breakout Date"] - timedelta(hours=12),
                    x1=r["Breakout Date"] + timedelta(hours=12),
                    fillcolor=color, opacity=0.5, line_width=0,
                    annotation_text=f"{r['Direction']} Breakout", annotation_position="top left"
                )
                fig.add_shape(
                    type="line",
                    x0=r["Main Candle"], x1=r["Breakout Date"],
                    y0=r["Range High"], y1=r["Range High"],
                    line=dict(color="green", width=2, dash="solid"),
                )
                fig.add_shape(
                    type="line",
                    x0=r["Main Candle"], x1=r["Breakout Date"],
                    y0=r["Range Low"], y1=r["Range Low"],
                    line=dict(color="red", width=2, dash="solid"),
                )
            fig.update_layout(title=f"{symbol} Range Breakouts (Counter ≥ {counter})", xaxis_title="Date", yaxis_title="Price", height=500)
            all_charts.append((symbol, result_df, fig))

    # Plot charts in rows of 3
    if all_charts:
        st.markdown("### Breakout Charts")
        for i in range(0, len(all_charts), 3):
            cols = st.columns(3)
            for idx, (symbol, result_df, fig) in enumerate(all_charts[i:i+3]):
                with cols[idx]:
                    st.markdown(f"**{symbol}**")
                    st.dataframe(result_df)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No breakouts found for any selected symbols in the given period.")
