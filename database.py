import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
from pymongo import MongoClient
from bson.objectid import ObjectId
stored_trades = []

def get_previous_day():

    date_str = datetime.now().strftime("%d-%m-%Y")
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    previous_day = date_obj - timedelta(days=1)
    
    return previous_day.strftime("%d-%m-%Y")

def get_data_function(access_token, f_date, s_date, f_year, page_num):
    url = 'https://api.upstox.com/v2/trade/profit-loss/data'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'from_date': f_date,
        'to_date': s_date,
        'segment': 'FO',
        'financial_year': f_year,
        'page_number': page_num, # which number you need 
        'page_size': '500' # in one page how many trade count  you need 
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    return response.json()

def get_page_count(access_token, f_date, s_date, f_year) :

    url = 'https://api.upstox.com/v2/trade/profit-loss/metadata'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'from_date': f_date,
        'to_date': s_date,
        'segment': 'FO',
        'financial_year': f_year
    }
    
    response = requests.get(url, headers=headers, params=params)
    return (response.json()['data']['trades_count'])

def calculate_trade_pl(data):
    trades = data['data']
    trade_pl_summary = {}
    
    for trade in trades:
        date = trade['buy_date']
        
        buy_amount = trade['buy_amount']
        sell_amount = trade['sell_amount']
        trade_pl = sell_amount - buy_amount
        quantity = trade['quantity']
        
        if date not in trade_pl_summary:
            trade_pl_summary[date] = {
                'total_buy_amount': 0,
                'total_sell_amount': 0,
                'total_pl': 0,
                'total_quantity': 0,
                'trades': []
            }
        
        trade_pl_summary[date]['total_buy_amount'] += buy_amount
        trade_pl_summary[date]['total_sell_amount'] += sell_amount
        trade_pl_summary[date]['total_pl'] += trade_pl
        trade_pl_summary[date]['total_quantity'] += quantity
        trade_pl_summary[date]['trades'].append({
            'scrip_name': trade['scrip_name'],
            'quantity': quantity,
            'buy_average': trade['buy_average'],
            'sell_average': trade['sell_average'],
            'trade_pl': trade_pl
        })
    
    return trade_pl_summary

def get_financial_year_details(date_str):
    # Convert string to datetime object
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    year = date_obj.year
    month = date_obj.month
    
    # Determine financial year
    if month < 4:
        start_year = year - 1
        end_year = year
    else:
        start_year = year
        end_year = year + 1
    
    start_date = f"01-04-{start_year}"
    end_date = f"31-03-{end_year}"
    financial_year = f"{str(start_year)[-2:]}{str(end_year)[-2:]}"
    
    return start_date, end_date, financial_year

def aggregate_trade_data(trade_list):
    result = defaultdict(lambda: {"total_buy_amount": 0, "total_sell_amount": 0, "total_pl": 0, "total_quantity": 0})

    for trade in trade_list:
        buy_date = trade["buy_date"]
        result[buy_date]["total_buy_amount"] += trade["buy_amount"]
        result[buy_date]["total_sell_amount"] += trade["sell_amount"]
        result[buy_date]["total_quantity"] += trade["quantity"]
        result[buy_date]["total_pl"] = result[buy_date]["total_sell_amount"] - result[buy_date]["total_buy_amount"]

    return dict(result)

def extract_trade_data(data):
    global stored_trades
    extracted_data = [
        { 
            'buy_date': trade['buy_date'], 
            'quantity': trade['quantity'], 
            'buy_amount': trade['buy_amount'], 
            'sell_amount': trade['sell_amount']
        }
        for trade in data.get('data', [])
    ]
    
    # Append new data to the global list
    stored_trades.extend(extracted_data)

def stored_data(doc_id, aggregated_data) :

    client = MongoClient("mongodb+srv://test-yt:DYYAQ8YZ2d1XrdTb@test.ced18.mongodb.net/")
    db = client["user_database"]
    collection = db["users"]
    # Assuming aggregated_data is a dictionary with dates as keys and trade details as values
    trade_summary_object = {date: details for date, details in aggregated_data.items()}

    collection.update_one(
        {
            "_id": ObjectId(doc_id)
            # "upstox.trade_summary": {"$exists": True}
        },
        {
            "$set": {
                "upstox.$[].trade_summary": trade_summary_object
            }
        }
    )


def get_all_financial_year_data(access_token ,starting_trading_date) :

    current_date = get_previous_day()
    start_date, end_date, fy = get_financial_year_details(starting_trading_date)
    current_date_obj = datetime.strptime(current_date, "%d-%m-%Y")
    end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")

    while current_date_obj > end_date_obj:
    
            trade_count = get_page_count(access_token ,start_date, end_date, fy)
            page_number = trade_count / 500
            count = 0 
    
            while count <= page_number :
                count += 1
                stored_data = get_data_function(access_token ,start_date, end_date, fy, count)
                extract_trade_data(stored_data)
    
            date_obj = datetime.strptime(start_date, "%d-%m-%Y")
            start_date = date_obj.replace(year=date_obj.year + 1)
            start_date = start_date.strftime("%d-%m-%Y")
    
            date_obj = datetime.strptime(end_date, "%d-%m-%Y")
            end_date = date_obj.replace(year=date_obj.year + 1)
            end_date = end_date.strftime("%d-%m-%Y")
    
            first_part = int(fy[:2])  # "24" -> 24
            second_part = int(fy[2:])  # "25" -> 25
            new_first_part = first_part + 1  # 24 -> 25
            new_second_part = second_part + 1  # 25 -> 26
            fy = f"{new_first_part}{new_second_part}"
    
            end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")

    trade_count = get_page_count(access_token ,start_date, end_date, fy)
    page_number = trade_count / 500
    count = 0 

    while count <= page_number :
        count += 1
        stored_data = get_data_function(access_token ,start_date, end_date, fy, count)
        extract_trade_data(stored_data)
    
def stored_datas(user_id, access_token) :
    starting_trading_date = "01-01-2025"
    get_all_financial_year_data(access_token, starting_trading_date) 
    aggregated_data = aggregate_trade_data(stored_trades)
    stored_data(user_id,aggregated_data)
    
#stored_datas("eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIyM0NGOFQiLCJqdGkiOiI2N2E5YmJjNWZlNWFjYTI2MDg2MTBlZDAiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzM5MTc2OTAxLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3MzkyMjQ4MDB9.GZn8Uq31ndSRVCHeHoKFRcTkTZuWsfVKqr3zaqZVNic")