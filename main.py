import os
import yfinance as yf
import requests
from datetime import datetime

def analyze_with_ai(stock, current_price, hist_data):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY મિસિંગ છે."
    
    prompt = f"Stock: {stock}, Current Price: {current_price}. Last 5 days close: {hist_data}. Give a strict 1-sentence technical swing trading verdict (Buy/Sell/Hold and why). No fluff."
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    return "AI Analysis નિષ્ફળ."

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

def main():
    stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"] # અહી Nifty 500 ના સ્ટોક્સ ઉમેરી શકો છો
    results = []
    
    for stock in stocks:
        try:
            df = yf.Ticker(stock).history(period="5d")
            if df.empty: continue
            
            close_price = float(df['Close'].iloc[-1])
            hist_prices = [round(x, 2) for x in df['Close'].tolist()]
            
            ai_verdict = analyze_with_ai(stock, close_price, hist_prices)
            results.append(f"🔹 *{stock}* (₹{close_price})\n🤖 *AI:* {ai_verdict}")
        except Exception:
            pass
            
    if results:
        msg = f"🚀 *AI Swing Trading Setup* ({datetime.now().strftime('%d %b %Y')})\n\n" + "\n\n".join(results)
        send_telegram(msg)

if __name__ == "__main__":
    main()
