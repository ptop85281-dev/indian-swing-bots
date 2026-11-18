import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

def analyze_with_ai(stock, current_price, hist_data):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "API Key મળતી નથી. (GitHub Secrets ચેક કરો)"
    
    prompt = f"Stock: {stock}, Price: {current_price}. Last 5 days: {hist_data}. Give a strict 1-sentence technical swing trading verdict (Buy/Sell/Hold and why). No fluff."
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "mixtral-8x7b-32768",  # ફ્રી એકાઉન્ટ માટે સૌથી બેસ્ટ અને ફાસ્ટ મોડેલ 
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
    # Nifty 50 ના લેટેસ્ટ 50 સ્ટોક્સ ડાયરેક્ટ ઇન્ટરનેટ પરથી લેશે 
    url = 'https://en.wikipedia.org/wiki/NIFTY_50'
    html = pd.read_html(url)
    df_nifty = html[2]
    stocks = df_nifty['Symbol'].apply(lambda x: x + ".NS").tolist()
    
    results = []
    
    for stock in stocks:
        try:
            df = yf.Ticker(stock).history(period="1mo")
            if df.empty or len(df) < 20: continue
            
            close_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            
            # વોલ્યુમ બ્રેકઆઉટ ચેક (એવરેજ કરતા 20% વધારે વોલ્યુમ)
            df['Vol_20_Avg'] = df['Volume'].rolling(window=20).mean()
            current_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Vol_20_Avg'].iloc[-1])
            
            # જો સ્ટોકમાં બ્રેકઆઉટ હોય તો જ AI પાસે લઈ જાવ!
            if current_vol > (1.2 * avg_vol) and close_price > prev_close:
                hist_prices = [round(x, 2) for x in df['Close'].tail(5).tolist()]
                ai_verdict = analyze_with_ai(stock, close_price, hist_prices)
                results.append(f"🔹 *{stock}* (₹{close_price:.2f})\n🤖 *AI:* {ai_verdict}")
                
        except Exception as e:
            pass
            
    # ટેલિગ્રામ પર મેસેજ
    date_str = datetime.now().strftime('%d %b %Y')
    if results:
        msg = f"🚀 *Smart AI Setup - Nifty 50* ({date_str})\n\n" + "\n\n".join(results)
    else:
        msg = f"📊 *Smart AI Setup* ({date_str})\n\nઆજે Nifty 50 માં કોઈ સ્પેશિયલ વોલ્યુમ બ્રેકઆઉટ મળ્યો નથી."
        
    send_telegram(msg)
    print("Done!")

if __name__ == "__main__":
    main()
