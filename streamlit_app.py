import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Range Breakout Finder", layout="wide")

symbol_options = [
    "VBL", "FCL", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "MARUTI", "LT", 
    "360ONE", "AARTIIND", "ABB", "ABCAPITAL", "ABFRL", "ACC", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", 
    "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APLAPOLLO", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", "ASTRAL",
    "ATGL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BALKRISIND",
    "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHARTIARTL", "BHEL", 
    "BIOCON", "BLUESTARCO", "BOSCHLTD", "BPCL", "BRITANNIA", "BSE", "BSOFT", "CAMS", "CANBK", "CDSL", "CESC",
    "CGPOWER", "CHAMBLFERT", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR", "CROMPTON",
    "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DMART", 
    "DRREDDY", "EICHERMOT", "ETERNAL", "EXIDEIND", "FEDERALBNK", "FORTIS", "GAIL", "GLENMARK",
    "GMRAIRPORT", "GODREJCP", "GODREJPROP", "GRANULES", "GRASIM", "HAL", "HAVELLS", "HCLTECH", 
    "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HFCL", "HINDALCO", "HINDCOPPER", "HINDPETRO",
    "HINDUNILVR", "HINDZINC", "HUDCO", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "IDFCFIRSTB", 
    "IEX", "IGL", "IIFL", "INDHOTEL", "INDIANB", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", 
    "INOXWIND", "IOC", "IRB", "IRCTC", "IREDA", "IRFC", "ITC", "JINDALSTEL", "JIOFIN", "JSL",
    "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KALYANKJIL", "KAYNES", "KEI", "KFINTECH", "KOTAKBANK", "KPITTECH",
    "LAURUSLABS", "LICHSGFIN", "LICI", "LODHA", "LT", "LTF", "LTIM", "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", 
    "MANKIND", "MARICO", "MARUTI", "MAXHEALTH", "MAZDOCK", "MCX", "MFSL", "MGL", "MOTHERSON", 
    "MPHASIS", "MUTHOOTFIN", "NATIONALUM", "NAUKRI", "NBCC", "NCC", "NESTLEIND", "NHPC", 
    "NMDC", "NTPC", "NYKAA", "OBEROIRLTY", "OFSS", "OIL", "ONGC", "PAGEIND", "PATANJALI", "PAYTM", "PEL", 
    "PERSISTENT", "PETRONET", "PFC", "PGEL", "PHOENIXLTD", "PIDILITIND", "PIIND", "PNB", "PNBHOUSING", "POLICYBZR", 
    "POLYCAB", "POONAWALLA", "POWERGRID", "PPLPHARMA", "PRESTIGE", "RBLBANK", "RECLTD", "RELIANCE", "RVNL", "SAIL", 
    "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SJVN", "SOLARINDS", "SONACOMS", "SRF", 
    "SUNPHARMA", "SUPREMEIND", "SYNGENE", "TATACHEM", "TATACOMM", "TATACONSUM", "TATAELXSI", "TATAMOTORS", 
    "TATAPOWER", "TATASTEEL", "TATATECH", "TCS", "TECHM", "TIINDIA", "TITAGARH", "TITAN", "TORNTPHARM", 
    "TORNTPOWER", "TRENT", "TVSMOTOR", "ULTRACEMCO", "UNIONBANK", "UNITDSPR", "UNOMINDA", "UPL", "VBL", "VEDL", 
    "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
]


select_all = st.checkbox("Select All Symbols", value=True)
if select_all:
    symbols = st.multiselect("Select Company Symbols", options=symbol_options, default=symbol_options, key="symbols")
else:
    symbols = st.multiselect("Select Company Symbols", options=symbol_options, default=["VBL", "FCL"], key="symbols")

interval_map = {
    "15 min": "15m",
    "1 day": "1d",
    "1 week": "1wk",
    "1 month": "1mo"
}
interval_label = st.selectbox("Select Interval", list(interval_map.keys()), index=1)
interval = interval_map[interval_label]

start_date = st.date_input("Start Date:", value=datetime.today()-timedelta(days=365))
end_date = st.date_input("End Date (and Breakout Date):", value=datetime.today())
counter = st.number_input("Counter Value (Minimum inside-range candles before breakout):", min_value=2, max_value=50, value=5)
use_wick = st.checkbox("Require >50% inside candles to be 'wicky' (body < wick)?", value=True)

if st.button("Find Breakouts"):
    found_any = False
    for symbol in symbols:
        with st.spinner(f"Fetching data for {symbol}..."):
            try:
                data = yf.download(
                    symbol + ".NS",
                    start=start_date,
                    end=end_date + timedelta(days=1) if interval == "1d" else end_date,
                    progress=False,
                    interval=interval,
                    multi_level_index=False
                )
            except Exception:
                continue

            if data.empty:
                continue
            df = data.reset_index()

        def wick_body_stats(row):
            body = abs(row['Close'] - row['Open'])
            wick = (row['High'] - row['Low']) - body
            return pd.Series({'body': body, 'wick': wick})

        df[['body', 'wick']] = df.apply(wick_body_stats, axis=1)

        i = 0
        breakout_found = False
        while i < len(df) - counter - 1 and not breakout_found:
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
                    breakout_dt = pd.to_datetime(breakout['Date']).date()
                    if inside_count >= counter:
                        if breakout['Close'] > main_high:
                            direction = "UP"
                        elif breakout['Open'] < main_low:
                            direction = "DOWN"
                        else:
                            direction = None
                        if (direction and (not use_wick or wick_percent > 0.5)
                            and breakout_dt == end_date):
                            st.write(f"**{symbol}** | Breakout Date: {breakout_dt} | Counter: {inside_count} | Direction: {direction}")
                            found_any = True
                            breakout_found = True  # Only first breakout per symbol
                    break
            i += 1

    if not found_any:
        st.warning(f"No breakouts found for any selected symbols **on {end_date}**.")
