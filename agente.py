import time,numpy as np,pandas as pd,pandas_ta as ta,yfinance as yf,anthropic
CLAUDE_API_KEY="SUA_CHAVE_AQUI"
def buscar_dados():
 btc=yf.download("BTC-USD",interval="15m",period="5d",progress=False)
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
 print(f"SCORE:{score}")
 if score<=-60:print("SINAL:SHORT")
 elif score>=60:print("SINAL:LONG")
 else:print("SINAL:AGUARDAR")
 return score
def analisar_com_claude(df,score):
 p=df["fechamento"].iloc[-1]
 prompt=f"Trader BTC 15min. Preco:{p:.2f} Score:{score} RSI:{df['RSI'].iloc[-1]:.2f} MACD:{df['MACDh_12_26_9'].iloc[-1]:.2f} WT1:{df['WT1'].iloc[-1]:.2f} ATR:{df['ATR'].iloc[-1]:.2f} BBSup:{df['BBU_20_2.0_2.0'].iloc[-1]:.2f} BBInf:{df['BBL_20_2.0_2.0'].iloc[-1]:.2f}. Capital 1234 USDT 1x risco 1pct. Responda em portugues: 1.DECISAO 2.JUSTIFICATIVA 3.ENTRADA 4.STOP 5.ALVO1 6.ALVO2 7.RR"
 c=anthropic.Anthropic(api_key=CLAUDE_API_KEY)
 m=c.messages.create(model="claude-sonnet-4-6",max_tokens=1024,messages=[{"role":"user","content":prompt}])
 print(m.content[0].text)
def rodar_agente(ciclos=3,mins=1):
 print("AGENTE INICIADO")
 for i in range(ciclos):
  print(f"CICLO {i+1}/{ciclos} - {time.strftime('%H:%M:%S')}")
  df=buscar_dados()
  score=calcular_score(df)
  if abs(score)>=60:
   analisar_com_claude(df,score)
  if i<ciclos-1:
   time.sleep(mins*60)
 print("AGENTE FINALIZADO")
rodar_agente(ciclos=3,mins=1)
