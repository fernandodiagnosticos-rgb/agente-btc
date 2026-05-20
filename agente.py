import time,numpy as np,pandas as pd,pandas_ta as ta,yfinance as yf,anthropic,requests
CLAUDE_API_KEY="SUA_CHAVE_AQUI"
TELEGRAM_TOKEN="8702123117:AAHf4B1hjek7UqFklvX6lclGQ40FrKw6QGM"
TELEGRAM_CHAT_ID="8962699675"
def enviar_telegram(msg):
    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url,data={"chat_id":TELEGRAM_CHAT_ID,"text":msg})
def buscar_dados(intervalo="15m",periodo="5d"):
    btc=yf.download("BTC-USD",interval=intervalo,period=periodo,progress=False)
    df=btc[["Open","High","Low","Close","Volume"]].copy()
    df.columns=["abertura","maxima","minima","fechamento","volume"]
    df=df.dropna()
    df=pd.concat([df,ta.macd(df["fechamento"])],axis=1)
    df["RSI"]=ta.rsi(df["fechamento"],length=14)
    df=pd.concat([df,ta.stochrsi(df["fechamento"])],axis=1)
    df["EMA9"]=ta.ema(df["fechamento"],length=9)
    df["EMA21"]=ta.ema(df["fechamento"],length=21)
    df["EMA50"]=ta.ema(df["fechamento"],length=50)
    df["EMA200"]=ta.ema(df["fechamento"],length=200)
    df=pd.concat([df,ta.bbands(df["fechamento"],length=20)],axis=1)
    df["ATR"]=ta.atr(df["maxima"],df["minima"],df["fechamento"],length=14)
    hlc3=(df["maxima"]+df["minima"]+df["fechamento"])/3
    esa=hlc3.ewm(span=10,adjust=False).mean()
    d=(hlc3-esa).abs().ewm(span=10,adjust=False).mean()
    ci=(hlc3-esa)/(0.015*d)
    wt1=ci.ewm(span=21,adjust=False).mean()
    wt2=wt1.rolling(4).mean()
    df=df.copy()
    df["WT1"]=wt1
    df["WT2"]=wt2
    raw=hlc3-hlc3.rolling(14).mean()
    df["MFI"]=(raw/(0.015*hlc3.rolling(14).std())).ewm(span=14,adjust=False).mean()
    df["CUP"]=(df["WT1"]>df["WT2"])&(df["WT1"].shift(1)<=df["WT2"].shift(1))
    df["CDN"]=(df["WT1"]<df["WT2"])&(df["WT1"].shift(1)>=df["WT2"].shift(1))
    df["BUY"]=df["CUP"]&(df["WT2"]<=-53)
    df["SELL"]=df["CDN"]&(df["WT2"]>=53)
    df["SBUY"]=df["CUP"]&(df["WT2"]<=-60)
    df["SSELL"]=df["CDN"]&(df["WT2"]>=60)
    return df
