import os
from datetime import datetime
from utils.llm import ask_llm
from utils.data_fetcher import get_stock_data, get_nifty_data

def main():
    print("====================================")
    print("Indian Swing Trading Bots Started")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("====================================")

    # 1. Test LLM connection
    print("\n--- Testing LLM ---")
    test_reply = ask_llm("Say only: LLM is working fine")
    print(test_reply)

    # 2. Test data fetch (Nifty)
    print("\n--- Testing Data Fetch ---")
    nifty = get_nifty_data(period="5d")
    if nifty is not None and not nifty.empty:
        print("Nifty data fetched successfully")
        print(nifty.tail(3))
    else:
        print("Failed to fetch Nifty data")

    print("\n====================================")
    print("Basic tests completed")
    print("====================================")

if __name__ == "__main__":
    main()
