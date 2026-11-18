import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

def analyze_with_ai(stock, current_price, hist_data):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "API Key મળતી નથી. (GitHub Secrets ચેક કરો)"
    
    prompt = f"Stock: {stock}, Price: {current_price}. Last 5 days: {hist_data}. Give a strict 1-sentence technical swing trading verdict (Buy/Sell/Hold and why). No fluff."
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "mixtral-8x7b-32768",  
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"AI Error: {e}"

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

def main():
    print("Fetching Nifty 50 Stocks...")
    
    # Wikipedia 403 Forbidden Error સોલ્વ કરવા માટે User-Agent ઉમેર્યો છે
    url = 'https://en.wikipedia.org/wiki/NIFTY_50'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    # HTML ને વાંચવા માટે
    html = pd.read_html(StringIO(response.text))
    df_nifty = html[2]
    stocks = df_nifty['Symbol'].apply(lambda x: x + ".NS").tolist()
    
    results = []
    
    for stock in stocks:
        try:
            df = yf.Ticker(stock).history(period="1mo")
            if df.empty or len(df) < 20: continue
            
            close_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            
            # વોલ્યુમ બ્રેકઆઉટ ચેક 
            df['Vol_20_Avg'] = df['Volume'].rolling(window=20).mean()
            current_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Vol_20_Avg'].iloc[-1])
            
            if current_vol > (1.2 * avg_vol) and close_price > prev_close:
                hist_prices = [round(x, 2) for x in df['Close'].tail(5).tolist()]
                ai_verdict = analyze_with_ai(stock, close_price, hist_prices)
                results.append(f"🔹 *{stock}* (₹{close_price:.2f})\n🤖 *AI:* {ai_verdict}")
                
        except Exception as e:
            pass
            
    # ટેલિગ્રામ પર મેસેજ
    date_str = datetime.now
