from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
import math
import emoji
import time
import re
import ccxt
import requests
import cryptocompare
from forex_python.bitcoin import BtcConverter
from forex_python.converter import CurrencyRates, CurrencyCodes
from .fetch import get_news_previous_day

bitmex = ccxt.bitmex()
coinbase = ccxt.coinbase()
kraken = ccxt.kraken()


# Create your views here.
def hilow():
    bitmex_price = f"bitmex for $ {bitmex.fetch_ticker('BTC/USDT')['close']}"
    coinbase_price = f"coinbase for $ {coinbase.fetch_ticker('BTC/USDT')['close']}"
    kraken_price = f"Kraken for $ {kraken.fetch_ticker('BTC/USDT')['close']}"
    
    # Extract the numeric values from the strings and convert them to floats
    bitmex_value = float(bitmex_price.split()[3])
    coinbase_value = float(coinbase_price.split()[3])
    kraken_value = float(kraken_price.split()[3])

    # Create a list of float prices for comparison
    all_prices = [bitmex_value, coinbase_value, kraken_value]
    minimum_price = min(all_prices)
    maximum_price = max(all_prices)

    # Calculate the arbitrage value
    arbitrage = maximum_price - minimum_price

    # Return a formatted string showing where to buy/sell and the arbitrage opportunity
    return (f"Buy bitcoin on {'bitmex' if minimum_price == bitmex_value else 'coinbase' if minimum_price == coinbase_value else 'kraken'} "
            f"for ${minimum_price:.2f} and sell on {'bitmex' if maximum_price == bitmex_value else 'coinbase' if maximum_price == coinbase_value else 'kraken'} "
            f"for ${maximum_price:.2f}. Arbitrage opportunity: ${arbitrage:.2f}")

def rates():
    latest_price = BtcConverter()
    converted_amount_USD = latest_price.get_latest_price('USD')
    converted_amount_EUR = latest_price.get_latest_price('EUR')
    converted_amount_GBP = latest_price.get_latest_price('GBP')
    return (
        f"Bitcoin prices of top 3 global currencies \n"
        f"\n"
        f"USD - ${converted_amount_USD:.2f} \n"
        f"EUR - €{converted_amount_EUR:.2f} \n"
        f"GBP - £{converted_amount_GBP:.2f} \n"
    )

def check_usd_bitcoin_value(amount):
    validate = requests.get(f"https://www.blockchain.com/tobtc?currency=USD&value={amount}")
    data = validate.json()
    return data


@csrf_exempt
def index(request):
    if request.method == 'POST':
        incoming_msg = request.POST['Body'].lower()
        message = incoming_msg.split()

        resp = MessagingResponse()
        msg = resp.message()
        responded = False

        if 'hi' in incoming_msg:
            reply = emoji.emojize("""Welcome to Bitbot. For everything bitcoin. Select number like 1 or type a word like 'bitcoin'\n
*arbitrage:* Check the arbitrage opportunity. eg: 'arbitrage'\n
*Top currencies:* Check the latest Bitcoin price of top 3 global currencies. eg: 'Top currencies'\n
*Convert:* Convert usd to bitcoin.eg: 'convert 5000 usd to bitcoin'.\n
*check date:* Check date for bitcoins value. eg: 'usd check date 2 bitcoins on 12.12.2015'. \n
*latest news:* Get a latest news related to bitcoin investments , just type 'Latest news'.\n
*Buy Bitcoin* : Just type buy bitcoin , eg: 'buy bitcoin' """)
            msg.body(reply)
            responded = True
        
        elif 'arbitrage' in incoming_msg and 'latest' not in incoming_msg and 'check date' not in incoming_msg: 
            reply = hilow()
            msg.body(reply)
            responded = True

        elif 'top' in incoming_msg and 'latest' not in incoming_msg and 'check date' not in incoming_msg: 
            reply = rates()
            msg.body(reply)
            responded = True

        elif 'latest' in incoming_msg and 'news' not in incoming_msg:
            currency = incoming_msg.split()[4].upper()
            amount = float(re.search(r'\d+(\.\d+)?', incoming_msg).group(0))
            symbols = CurrencyCodes()
            symbol = symbols.get_symbol(currency)
            
            latest_price = BtcConverter()
            converted_amount = latest_price.convert_btc_to_cur(amount, currency)
            reply = f"The latest price of B {amount} to {currency} is {symbol}{round(converted_amount, 2)}"
            msg.body(reply)
            responded = True

        elif 'check date' in incoming_msg:
            match_date = re.search(r'\d{2}.\d{2}.\d{4}', incoming_msg)
            if match_date:
                date = datetime.strptime(match_date.group(), '%d.%m.%Y').date()
                currency = incoming_msg[:3].upper()
                symbols = CurrencyCodes()
                amount = float(re.search(r'\d+(\.\d+)?', incoming_msg).group(0))
                past_date = BtcConverter()
                try:
                    reply = past_date.convert_btc_to_cur_on(amount, currency, date)
                    msg.body(f"{amount} Bitcoin was worth {symbols.get_symbol(currency)}{str(round(reply))} on that date.")
                except Exception as e:
                    msg.body("Rates are not available for the specified date.")
                responded = True


        elif 'convert' in incoming_msg:
            amount = float(re.search(r'\d+', incoming_msg).group(0))
            reply = check_usd_bitcoin_value(amount)
            msg.body(f"USD {amount} converted to bitcoin is B{str(reply)}")
            responded = True

        
        elif 'latest news' in incoming_msg:
            api_key = '9d1945a8c6df4ded9f10cf2bf6afb062'
            query='bitcoin AND ("buy" OR "sell" OR "investment" OR "sentiment" OR "analysis")'
            news_message = get_news_previous_day(api_key, query)
            msg.body(news_message)
            responded = True

        elif 'buy bitcoin' in incoming_msg:
            link = 'https://ln.run/O7PEV'  
            msg.body(
            'Click on the link below to buy some bitcoin.\n'
            f'{link}'
            )
            responded = True  

        if not responded:
            msg.body("Please send 'hi' for a menu")

        return HttpResponse(str(resp), content_type='text/xml')