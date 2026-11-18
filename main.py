import os
import yfinance as yf
import requests

def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Error: Telegram credentials missing in GitHub Secrets!")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Telegram message successfully sent!")
    else:
        print("Failed to send Telegram message:", response.text)

def main():
    print("Starting Swing Bot Scan...")
    
    # ઉદાહરણ માટે 3 સ્ટોક્સ ચેક કરીએ છીએ જેથી 0 સેકન્ડમાં કોડ પૂરો ન થઈ જાય
    stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
    message = "🚀 Nifty Swing Bot Test Results:\n\n"
    
    for stock in stocks:
        try:
            data = yf.download(stock, period="2d", progress=False)
            if not data.empty:
                # લેટેસ્ટ ક્લોઝિંગ પ્રાઇસ કાઢવા માટે
                close_price = float(data['Close'].iloc[-1])
                message += f"✅ {stock}: ₹{close_price:.2f}\n"
        except Exception as e:
            print(f"Error fetching {stock}: {e}")
            
    # ટેલિગ્રામ પર મેસેજ મોકલવાનું ફંક્શન કોલ થશે
    send_telegram(message)
    print("Bot execution completed.")

if __name__ == "__main__":
    main()
