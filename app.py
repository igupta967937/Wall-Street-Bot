import urllib
import json
import os

from flask import Flask
from flask import request
from flask import make_response
from predictStocks import predictStocks
from twitter_analyze import twitter_analyze

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
    if req.get("result").get("action") == "CurrentPrice.price":   
        # data = json.loads(getStockCurrentPrice(req))
        res = makeWebhookResult(getStockCurrentPrice(req))
        return res
    elif req.get("result").get("action") == "Prediction.stockForecast":
        # data = json.loads(getStockPrediction(req))
        res = makeWebhookResult(getStockPrediction(req))
        return res 
    elif req.get("result").get("action") == "Feelings.analyze":
        # data = json.loads(getTwitterFeelings(req))
        res = makeWebhookResult(getTwitterFeelings(req))
        return res
    else:
        return {}

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

    data_string = ''
    for key, value in d.iteritems():
        data_string += key + ' ' + str(value) + '\n'

    return str(data['positive'])

def getStockPrediction(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    prediction = predictStocks()
    num_of_days = 3
    predicted_values = prediction.stocksRegression(stock_symbol, int(num_of_days))
    predicted_list = predicted_values.tolist()
    return ''.join(str(v) for v in predicted_list)

def getStockCurrentPrice(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    prediction = predictStocks()
    current_price = prediction.getCurrentPrice(stock_symbol)
    return str(current_price)

def makeWebhookResult(data):
    if req.get("result").get("action") == "CurrentPrice.price":
        speech = "Current Price for the stock is $" + str(data)
    elif req.get("result").get("action") == "Prediction.stockForecast":
        speech = "Predicted price for next few days: " + str(data):
    elif req.get("result").get("action") == "Feelings.analyze":
        speech = "Feelings about stock: " + str(data)
    else:
        return {}

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "apiai-wallstreetbot-webhook"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
