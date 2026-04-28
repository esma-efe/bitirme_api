from fastapi.responses import FileResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

def get_portfolio(risk_level):

    data = yf.download(stocks, start="2020-01-01")["Close"]
    returns = data.pct_change().dropna()

    mean_returns = returns.mean()
    volatility = returns.std()
    sharpe = mean_returns / volatility

    risk_df = pd.DataFrame({
        "Return": mean_returns,
        "Volatility": volatility,
        "Sharpe": sharpe
    })

    def risk_label(vol):
        if vol < volatility.quantile(0.33):
            return "Low"
        elif vol < volatility.quantile(0.66):
            return "Medium"
        else:
            return "High"

    risk_df["Risk_Level"] = risk_df["Volatility"].apply(risk_label)

    if risk_level == "Low":
        result = risk_df[risk_df["Risk_Level"] == "Low"]
    elif risk_level == "Medium":
        result = risk_df[risk_df["Risk_Level"].isin(["Low","Medium"])]
    else:
        result = risk_df

    return result.to_dict()

@app.get("/portfolio")
def portfolio(risk: str):
    return get_portfolio(risk)

@app.get("/stocks")
def get_stocks():
    try:
        data = yf.download(stocks, period="1d", interval="1m")["Close"]

        latest = data.iloc[-1]   # son fiyat
        first = data.iloc[0]     # günün ilk fiyatı

        result = {}

        for stock in stocks:
            price = float(latest[stock])
            start = float(first[stock])

            change = ((price - start) / start) * 100 if start != 0 else 0

            result[stock] = {
                "price": round(price, 2),
                "change": round(change, 2)
            }

        return result

    except Exception as e:
        return {"error": str(e)}

