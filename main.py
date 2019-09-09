import logging
import os
import sys
import json

import requests

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] %(asctime)s (%(name)s) %(message)s', stream=sys.stdout)

# constants
API_ENDPOINT = 'https://api.primedice.com/graphql'
TOKEN = """put token here"""

# default config, you can change this as you like (just make sure they're valid choices)
initialBetAmountDefault = 0.1
winChanceDefault = 50

# setting these to negative means on win/loss you decrease your bet chance, but increase your winnings if you do win (and vice versa)
onWinChangeBetChanceDefault = 0
onLossChangeBetChanceDefault = 5
currencyTypeDefault = 'xrp'

# declerations (don't mess with these)
betAmount = None
currencyType = currencyTypeDefault
currencyTypes = ['btc', 'eth', 'ltc', 'doge', 'bch', 'xrp']

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def getBet(id):
    """ get info on a certain bet (not really used, just built it to learn the api) """
    headers = {
        'x-access-token': TOKEN,
        'Content-Type': "application/json",
        'Host': "api.primedice.com",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }
    json = {'query': """
        {
            bet(iid: "house:%s") {
                id
                iid
                bet {
                    ... on CasinoBet {
                        game
                        payout
                        payoutMultiplier
                        amount
                        createdAt
                        currency
                        user {
                            name
                        }
                        state {
                            ... on CasinoGamePrimedice {
                                result
                                target
                                condition
                            }
                        }
                    }
                }
            }
        } """ % (id)
            }
    try:
        r = requests.post(url=API_ENDPOINT, headers=headers, json=json)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return False
    logging.debug(r.text)
    return r.text

def doBet(amount, target, condition, currency):
    """ do a certain bet """
    headers = {
        'x-access-token': TOKEN,
        'Content-Type': "application/json",
        'Host': "api.primedice.com",
        'Accept': "*/*",
        'Accept-Encoding': "gzip, deflate",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }

    json = {'query': """
        mutation {
            primediceRoll(amount: %s, target: %s, condition: %s, currency: %s) {
                id
                payout
                amountMultiplier
                payoutMultiplier
                createdAt
                nonce
            }
        } """ % (amount, target, condition, currency)
            }

    try:
        r = requests.post(url=API_ENDPOINT, headers=headers, json=json)
    except requests.exceptions.RequestException as e:
        logging.error(e)
        return False
    logging.debug(r.text)
    return r.text

def mainLoop(winChance=50):
    logging.info("betting " + str(betAmount) + " " + str(currencyType) + " at %" + str(winChance))
    winTarget = -winChance + 100 # gotta invert to get the actual dice roll
    betInfo = json.loads(doBet(str(betAmount), str(winTarget), 'above', str(currencyType)))

    # depeonding on our outcome, change our chance
    if betInfo["data"]["primediceRoll"]["payout"] == 0:
        winChance = winChance + onLossChangeBetChance
        logging.info("Loss!")
    else:
        winChance = winChance + onWinChangeBetChance
        logging.info("Win!")

    if winChance > 98:
        winChance = 98

    if winChance < 0.01:
        winChance = 0.01

    mainLoop(winChance=winChance)

### INIT

# generate the user input query
currencyString = "Currency list:"
for i in currencyTypes:
    currencyString = currencyString + "\n[" + str(currencyTypes.index(i)) + "] " + i

# ask for currency choice
print(currencyString)
currencyType = input("Pick a currency [" + str(currencyTypes.index(currencyType)) + "]: ")

# default to xrp if invalid or no selection
if not currencyType.isdigit() or int(currencyType) > 5:
    # make sure that currencyType is a digit, and within the bounds of our currency list
    currencyType = currencyTypeDefault
    print("defaulting to [" + str(currencyTypes.index(currencyType)) + "] " + currencyType + "\n")
else:
    currencyType = currencyTypes[int(currencyType)]

# ask for bet amount
initialBetAmount = input("How much " + currencyType + " would you like to bet initially? [0.1]:")
if not isFloat(initialBetAmount) or float(initialBetAmount) <= 0:
    # make sure that its a float and not negative (you can wager 0 for some reason)
    initialBetAmount = initialBetAmountDefault
    print("defaulting to 0.1\n")
else:
    initialBetAmount = float(initialBetAmount)

# ask for win chance
winChance = input("% win chance [50]:")
if not isFloat(winChance) or float(winChance) >= 100 or float(winChance) <= 0:
    winChance = winChanceDefault
    print("defaulting to 50\n")
else:
    winChance = float(winChance)

# ask for change on win
onWinChangeBetChance = input("% win chance change on win [0]:")
if not isFloat(onWinChangeBetChance) or float(onWinChangeBetChance) >= 100 or float(onWinChangeBetChance) <= -100:
    onWinChangeBetChance = onWinChangeBetChanceDefault
    print("defaulting to 0\n")
else:
    onWinChangeBetChance = float(onWinChangeBetChance)

# ask for change on loss
onLossChangeBetChance = input("% win chance change on loss [5]:")
if not isFloat(onLossChangeBetChance) or float(onLossChangeBetChance) >= 100 or float(onLossChangeBetChance) <= -100:
    onLossChangeBetChance = onLossChangeBetChanceDefault
    print("defaulting to 5\n")
else:
    onLossChangeBetChance = float(onLossChangeBetChance)

betAmount = initialBetAmount

# while True:
#     mainLoop(winChance=winChance)
mainLoop(winChance=winChance)
