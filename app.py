import urllib
import json
import os

from flask import Flask
from flask import request
from flask import make_response
from predictStocks import predictStocks
from twitter_analyze import twitter_analyze
from yahoo_finance import Share
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    print r
    return r

def processRequest(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if req.get("result").get("action") == "CurrentPrice.price":   
        res = makeWebhookResult(getStockCurrentPrice(req), req, stock_symbol)
        return res
    elif req.get("result").get("action") == "Prediction.stockForecast":
        res = makeWebhookResult(getStockPrediction(req), req, stock_symbol)
        return res 
    elif req.get("result").get("action") == "Feelings.analyze":
        res = makeWebhookResult(getTwitterFeelings(req), req, stock_symbol)
        return res
    elif req.get("result").get("action") == "DividendDate.Date":
        res = makeWebhookResult(getStockDividendPayDate(req), req, stock_symbol)
        return res
    elif req.get("result").get("action") == "Stock.info":
        res = makeWebhookResult(getStockInfo(req), req, stock_symbol)
        return res
    elif req.get("result").get("action") == "Stock.historical":
        res = makeWebhookResult(getHistoricalData(req), req, stock_symbol)
        return res
    elif req.get("result").get("action") == "Decision.Classification":
        res = makeWebhookResult(getStockClassification(req), req, stock_symbol)
        return res 
    elif req.get("result").get("action") == "input.welcome":
        res = makeWebhookResult(getWelcome(req), req, stock_symbol)
        return res
    else:
        return {}

def getWelcome(req):
    response = 'Hi! I am here to help predict financial markets. My predictions are not 100% accurate!'
    return response

# analyze feelings intent
def getTwitterFeelings(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    twitter_analyzer = twitter_analyze()
    twitter_data = twitter_analyzer.analyze_feelings(stock_symbol)
    print 'Twitter data:'
    print twitter_data

    data = {}
    data['positive'] = twitter_data[0]
    data['negative'] = twitter_data[1]
    data['neutral'] = twitter_data[2]

    total = data['positive'] + data['negative'] + data['neutral']

    positive_percent = percentage(data['positive'], total)
    negative_percent = percentage(data['negative'], total)
    neutral_percent = percentage(data['neutral'], total)

    data_string = 'positive: ' + str(positive_percent) + '% negative: ' + str(negative_percent) + '% neutral: ' + str(neutral_percent) + '%'

    return data_string

# make percentage and round
def percentage(part, whole):
    return round(100 * float(part)/float(whole), 2)

# for intent prediction
def getStockPrediction(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")

    time = parameters.get("date-period")

    if stock_symbol is None:
        return None

    num_of_days = 3
    if time != '' and time is not None:
        num_of_days = extract_days(time)

    prediction = predictStocks()
    
    predicted_values = prediction.stocksRegression(stock_symbol, int(num_of_days))
    predicted_list = predicted_values.tolist()
    return ''.join(str(v) for v in predicted_list)

# invest or not
def getStockClassification(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")

    time = parameters.get("date-period")

    if stock_symbol is None:
        return None

    num_of_days = 14
    if time != '' and time is not None:
        num_of_days = extract_days(time)

    prediction = predictStocks()
    
    predicted_values = prediction.stocksNeuralNet(stock_symbol, int(num_of_days))
    predicted_decision = predicted_values.tolist()[-1][0]
    if time != '' and time is not None:
        return predicted_decision.lower() + ' (decision for next ' + str(num_of_days-1) + ' days)' 

    return predicted_decision.lower() + ' (decision for next two weeks)'

def extract_days(time):
    num_days = 3

    dates = time.split('/')

    first = datetime.strptime(dates[0], "%Y-%m-%d").date()
    second = datetime.strptime(dates[1], "%Y-%m-%d").date()

    num_days = (second - first).days+1

    return num_days

# intent current price
def getStockCurrentPrice(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    prediction = predictStocks()
    current_price = prediction.getCurrentPrice(stock_symbol)
    return str(current_price)

# intent dividend date
def getStockDividendPayDate(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    stock = Share(stock_symbol)
    pay_date = stock.get_dividend_pay_date()
    if pay_date is None:
        return 'No Dividend Date Avaliable'
    return str(pay_date)

def getStockInfo(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    stock = Share(stock_symbol)
    info = stock.get_info()
    return str(info)

# last 5 days data
def getHistoricalData(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    last_days = 5

    past_days_ago = datetime.now() - timedelta(days=last_days)
    past_days_ago_str = past_days_ago.strftime('%Y-%m-%d')

    now = datetime.now().date()
    now_str = now.strftime('%Y-%m-%d')

    stock = Share(stock_symbol)
    return str(stock.get_historical(past_days_ago_str, now_str))

# return to API.AI
def makeWebhookResult(data, req, stock_symbol):
    action = req.get("result").get("action")
    originalRequest1 = req.get("originalRequest")
    source = ''
    if originalRequest1 != None:
        source = originalRequest1.get("source")
    if action == "CurrentPrice.price":
        speech = "Current Price for the stock is $" + str(data)
        next_speech = "Predict " + stock_symbol
        # news_speech = "News for " + stock_symbol
        # news_url = "http://finance.yahoo.com/quote/" + stock_symbol
        chart_speech = "Chart for " + stock_symbol
        chart_url = "https://www.etoro.com/markets/" + stock_symbol + "/chart"
        feelings_speech = 'Feelings ' + stock_symbol
        if source == 'facebook':
            return {
                "speech": speech,
                "displayText": speech,
                "source": "apiai-wallstreetbot-webhook", 
                "data": {
                    "facebook": {
                      "attachment": {
                        "type": "template",
                        "payload": {
                                "template_type":"button",
                                "text":speech,
                                "buttons":[
                                  {
                                    "type":"web_url",
                                    "url":chart_url,
                                    "title":chart_speech,
                                    "webview_height_ratio": "compact"
                                  },
                                  {
                                    "type":"postback",
                                    "title":next_speech,
                                    "payload":next_speech
                                  },
                                  {
                                    "type":"postback",
                                    "title":feelings_speech,
                                    "payload":feelings_speech
                                  }
                                ]
                            }
                         }
                    }
                }
            }

    elif action == "Prediction.stockForecast":
        speech = "Predicted price for next few days: " + str(data)
    elif action == "Feelings.analyze":
        speech = "Feelings for " + stock_symbol + ": " + str(data)
    elif action == "Decision.Classification":
        speech = "I think we should " + str(data) + " " + stock_symbol 
    elif action == "input.welcome":
        speech = str(data)
    else:
        speech = str(data)

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "apiai-wallstreetbot-webhook"
    }

    #gif example

    # Image example
    # "data": {
    #     "facebook": {
    #       "attachment": {
    #         "type": "image",
    #         "payload": {
    #         "url": "https://www.testclan.com/images/testbot/siege/weapons/assault-rifles.jpg"
    #          }
    #         }
    #       }
    #     }

    # quick reply template
  #   "message":{
  #   "text":"Pick a color:",
  #   "quick_replies":[
  #     {
  #       "content_type":"text",
  #       "title":"Red",
  #       "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_RED"
  #     },
  #     {
  #       "content_type":"text",
  #       "title":"Green",
  #       "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GREEN"
  #     }
  #   ]
  # }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
