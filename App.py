import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import feedparser

DEFAULT_SUFFIX = ".JK"

def normalize_ticker(t):
    t = t.strip().upper()
    if "." not in t:
        t += DEFAULT_SUFFIX
    return t

@st.cache_data(ttl=60)
def load_data(ticker):
    df = yf.Ticker(ticker).history(period="2y")
    if df is None or df.empty:
        raise ValueError("Data harga tidak ditemukan. Coba kode seperti BBNI / BBCA / TLKM.")
    df["EMA20"] = ta.ema(df["Close"], 20)
    df["EMA50"] = ta.ema(df["Close"], 50)
    df["EMA200"] = ta.ema(df["Close"], 200)
    df["RSI14"] = ta.rsi(df["Close"], 14)
    df["ATR14"] = ta.atr(df["High"], df["Low"], df["Close"], 14)
    return df.dropna()

def trade_plan(df):
    last = df.iloc[-1]
    close = float(last.Close)
    atr = float(last.ATR14)
    support = float(df.Low.tail(60).min())
    resistance = float(df.High.tail(60).max())

    if close > float(last.EMA50):
        entry = float(last.EMA20)
        cl = min(entry - 1.2 * atr, support * 0.995)
        tp1 = entry + 1.5 * atr
        tp2 = min(resistance, entry + 3 * atr)
        reco = "BUY / ACCUMULATE (terukur)"
        why = "Uptrend (di atas EMA50). Entry ideal saat pullback dekat EMA20."
    else:
        entry = support * 1.01
        cl = support * 0.985
        tp1 = min(resistance, entry + 1.2 * atr)
        tp2 = resistance
        reco = "WAIT (tunggu setup)"
        why = "Belum kuat di atas EMA50. Jika entry, lakukan dekat support dengan cutloss ketat."

    return {
        "close": close,
        "entry": entry,
        "tp1": tp1,
        "tp2": tp2,
        "cutloss": cl,
        "support": support,
        "resistance": resistance,
        "reco": reco,
        "why": why
    }

def get_news(ticker, n=8):
    q = ticker.replace(".JK","")
    url = f"https://news.google.com/rss/search?q={q}+saham+OR+stock&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(url)
    return [{"title": e.get("title",""), "link": e.get("link","")} for e in feed.entries[:n]]

st.set_page_config(page_title="IDX Stock Advisor", layout="centered")
st.title("📈 IDX Stock Advisor (HP Friendly)")

kode = st.text_input("Masukkan Kode Saham (contoh: BBNI, BBCA, TLKM)", "BBNI")
if st.button("Analyze"):
    t = normalize_ticker(kode)
    try:
        df = load_data(t)
        plan = trade_plan(df)

        st.subheader(f"Hasil untuk {t}")
        st.metric("Harga Terakhir", f"{plan['close']:,.0f}")
        st.success(plan["reco"])
        st.caption(plan["why"])

        st.write("### 🎯 Trade Plan")
        st.write(f"**Entry:** {plan['entry']:,.0f}")
        st.write(f"**Target 1:** {plan['tp1']:,.0f}")
        st.write(f"**Target 2:** {plan['tp2']:,.0f}")
        st.write(f"**Cutloss:** {plan['cutloss']:,.0f}")
        st.write(f"Support/Resistance (60D): **{plan['support']:,.0f} / {plan['resistance']:,.0f}**")

        st.write("### 📰 News Terkini")
        for item in get_news(t, 8):
            st.markdown(f"- [{item['title']}]({item['link']})")

    except Exception as e:
        st.error(str(e))
