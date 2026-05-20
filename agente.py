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
    def calcular_score(df):
    score=0
    p=df["fechamento"].iloc[-1]
    ab=sum([p<df["EMA9"].iloc[-1],p<df["EMA21"].iloc[-1],p<df["EMA50"].iloc[-1],p<df["EMA200"].iloc[-1]])
    score+=25-(ab*12.5)
    h=df["MACDh_12_26_9"].iloc[-1]
    ha=df["MACDh_12_26_9"].iloc[-2]
    if h<0 and h<ha:score-=20
    elif h<0 and h>ha:score-=10
    elif h>0 and h>ha:score+=20
    else:score+=10
    r=df["RSI"].iloc[-1]
    if r>70:score-=15
    elif r<30:score+=15
    elif r>55:score+=10
    elif r<45:score-=10
    k=df["STOCHRSIk_14_14_3_3"].iloc[-1]
    d=df["STOCHRSId_14_14_3_3"].iloc[-1]
    if k<20:score-=10
    elif k>80:score+=10
    elif k>d:score+=5
    else:score-=5
    if p<df["BBL_20_2.0_2.0"].iloc[-1]:score+=10
    elif p>df["BBU_20_2.0_2.0"].iloc[-1]:score-=10
    elif p<df["BBM_20_2.0_2.0"].iloc[-1]:score-=5
    else:score+=5
    w=df["WT1"].iloc[-1]
    u=df.tail(10)
    if u["SBUY"].any():score+=20
    elif u["BUY"].any():score+=12
    elif u["SSELL"].any():score-=20
    elif u["SELL"].any():score-=12
    elif w>53:score-=8
    elif w<-53:score+=8
    return score
def analisar_multi_timeframe():
    timeframes={"15m":("15m","5d"),"1h":("1h","15d"),"4h":("1d","30d"),"1d":("1d","60d")}
    scores={}
    dados={}
    for nome,(intervalo,periodo) in timeframes.items():
        df=buscar_dados(intervalo,periodo)
        scores[nome]=calcular_score(df)
        dados[nome]=df
    score_final=int(scores["15m"]*0.3+scores["1h"]*0.3+scores["4h"]*0.2+scores["1d"]*0.2)
    alinhados=sum(1 for s in scores.values() if s<-40)
    alinhados_long=sum(1 for s in scores.values() if s>40)
    print(f"15m:{scores['15m']} | 1h:{scores['1h']} | 4h:{scores['4h']} | 1d:{scores['1d']}")
    print(f"SCORE FINAL:{score_final}")
    if score_final<=-60 and alinhados>=3:
        print("SINAL:SHORT FORTE")
    elif score_final>=60 and alinhados_long>=3:
        print("SINAL:LONG FORTE")
    elif score_final<=-60:
        print("SINAL:SHORT")
    elif score_final>=60:
        print("SINAL:LONG")
    else:
        print("SINAL:AGUARDAR")
    return score_final,scores,dados
    def analisar_com_claude(scores,dados,score_final):
    df=dados["15m"]
    p=df["fechamento"].iloc[-1]
    prompt=f"Trader BTC multi-timeframe. Preco:{p:.2f} Score15m:{scores['15m']} Score1h:{scores['1h']} Score4h:{scores['4h']} Score1d:{scores['1d']} ScoreFinal:{score_final} RSI:{df['RSI'].iloc[-1]:.2f} MACD:{df['MACDh_12_26_9'].iloc[-1]:.2f} WT1:{df['WT1'].iloc[-1]:.2f} ATR:{df['ATR'].iloc[-1]:.2f} BBSup:{df['BBU_20_2.0_2.0'].iloc[-1]:.2f} BBInf:{df['BBL_20_2.0_2.0'].iloc[-1]:.2f}. Capital 1234 USDT 1x risco 1pct. Analise todos os timeframes e responda em portugues: 1.DECISAO 2.JUSTIFICATIVA 3.ENTRADA 4.STOP 5.ALVO1 6.ALVO2 7.RR"
    c=anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    m=c.messages.create(model="claude-sonnet-4-6",max_tokens=1024,messages=[{"role":"user","content":prompt}])
    resposta=m.content[0].text
    print(resposta)
    msg=f"SINAL BTC MULTI-TIMEFRAME\n15m:{scores['15m']} | 1h:{scores['1h']} | 4h:{scores['4h']} | 1d:{scores['1d']}\nFINAL:{score_final}\n\n{resposta[:3000]}"
    enviar_telegram(msg)
    return resposta
def rodar_agente(ciclos=3,mins=1):
    print("AGENTE INICIADO")
    enviar_telegram("AGENTE BTC MULTI-TIMEFRAME INICIADO")
    for i in range(ciclos):
        print(f"CICLO {i+1}/{ciclos} - {time.strftime('%H:%M:%S')}")
        score_final,scores,dados=analisar_multi_timeframe()
        if abs(score_final)>=60:
            analisar_com_claude(scores,dados,score_final)
        else:
            enviar_telegram(f"15m:{scores['15m']} | 1h:{scores['1h']} | 4h:{scores['4h']} | 1d:{scores['1d']}\nFinal:{score_final} - Aguardando...")
        if i<ciclos-1:
            time.sleep(mins*60)
    print("AGENTE FINALIZADO")
    enviar_telegram("AGENTE FINALIZADO")
rodar_agente(ciclos=3,mins=1)
