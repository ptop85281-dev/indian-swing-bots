import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

print("=== Script Execution Started ===")

def analyze_with_ai(stock, current_price, hist_data):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY is missing in GitHub Secrets!")
        return "API Key Error"

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
            print(f"Groq API Error: {response.status_code} - {response.text}")
            return f"Error: {response.status_code}"
    except Exception as e:
        print(f"AI Exception: {e}")
        return f"AI Error"

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Error: Telegram credentials missing!")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    if response.status_code == 200:
        print("Telegram message sent successfully!")
    else:
        print("Telegram sending failed:", response.text)

def main():
    print("Fetching Nifty 50 Stocks...")
    try:
        url = 'https://en.wikipedia.org/wiki/NIFTY_50'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        html = pd.read_html(StringIO(response.text))
        stocks = html[2]['Symbol'].apply(lambda x: x + ".NS").tolist()
        print(f"Found {len(stocks)} stocks.")
    except Exception as e:
        print(f"Wikipedia fetch error, using Top 10 fallback stocks. Error: {e}")
        stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "BAJFINANCE.NS"]
        
    results = []
    
    for stock in stocks:
        try:
            df = yf.Ticker(stock).history(period="1mo")
            if df.empty or len(df) < 20: continue
            
            close_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            
            # 20 દિવસની વોલ્યુમ એવરેજ
            df['Vol_20_Avg'] = df['Volume'].rolling(window=20).mean()
            current_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Vol_20_Avg'].iloc[-1])
            
            # બ્રેકઆઉટ કન્ડિશન (વોલ્યુમ એવરેજ કરતા 20% વધુ અને ભાવ વધેલો હોવો જોઈએ)
            if current_vol > (1.2 * avg_vol) and close_price > prev_close:
                print(f"Breakout detected in {stock}! Asking AI...")
                hist_prices = [round(x, 2) for x in df['Close'].tail(5).tolist()]
                ai_verdict = analyze_with_ai(stock, close_price, hist_prices)
                results.append(f"🔹 *{stock}* (₹{close_price:.2f})\n🤖 *AI:* {ai_verdict}")
                
        except Exception as e:
            print(f"Error processing {stock}: {e}")
            
    date_str = datetime.now().strftime('%d %b %Y')
    if results:
        msg = f"🚀 *Smart AI Setup - Nifty 50* ({date_str})\n\n" + "\n\n".join(results)
    else:
        msg = f"📊 *Smart AI Setup* ({date_str})\n\nઆજે Nifty 50 માં કોઈ સ્પેશિયલ વોલ્યુમ બ્રેકઆઉટ મળ્યો નથી."
        
    send_telegram(msg)
    print("Done! Check your Telegram.")

if __name__ == "__main__":
    main()
