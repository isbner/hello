# based off of rules from
# http://bigpicture.typepad.com/comments/files/turtlerules.pdf

# uses ETFs:
# http://etfdb.com/type/commodity/exposure/futures-based/no-leveraged/

# this is just a start, there additional rules that haven't yet been implemented
import math
from talib import ATR
import numpy as np

def initialize(context):
    
    # you can find other tickers at that ETF page above
    context.security_list = [
                              sid(21448), # sina
                              # sid(37732), # euro
                              #sid(40365), # uranium
                              #sid(36468), # coffee
                              # sid(41309), # ..
                              # sid(35691), # ethanol
                         ]
    # set to True if only longs are wanted, not shorts
    context.long_only = False
    
    context.past_high_max = {}
    context.past_low_min = {}
    
    for sec in context.security_list:
        context.past_high_max[sec] = 0
        context.past_low_min[sec] = float('inf')
    
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())

def rebalance(context, data):
    context.total_price = 0 # to be used later as a sort of benchmark
    
    # for each security in the list
    context.total_price = sum(data.current(context.security_list, 'price'))
    hist = data.history(context.security_list, ['high', 'low', 'close'], 30, '1d')
    for security in context.security_list:
        highs = hist['high'][security][:-1]
        lows = hist['low'][security][:-1]
        closes = hist['close'][security][:-1]
        N = ATR(highs, lows, closes, timeperiod=20)[-1]
        if np.isnan(N):
            continue
            
        # count how many shares we have in open orders and own
        shares = 0
        for o in get_open_orders(security):
            shares += o.amount
        shares += context.portfolio.positions[security].amount
        
        # determine account size
        current_value = context.portfolio.cash + context.portfolio.positions_value
        if current_value < context.portfolio.starting_cash:
            account_size = -context.portfolio.starting_cash + 2*current_value
        else:
            account_size = current_value
        
        # compute how many units to buy or sell
        trade_amt = math.floor(account_size*.01/N)
        
        # 20-day high?
        h_20 = True if data.current(security, 'price') > context.past_high_max[security] else False
        
        # 20-day low?
        l_20 = True if data.current(security, 'price') < context.past_low_min[security] else False
        
        goal_shares = shares
        if h_20:
            # long
            goal_shares = trade_amt
        elif l_20:
            # sell or short
            if context.long_only:
                goal_shares = 0
            else:
                goal_shares = -trade_amt
            
        # goal_shares = shares + (amount to buy or sell)
        amt_to_buy = goal_shares - shares
        if amt_to_buy != 0:
            if amt_to_buy > 0:
                log.info("buying %s shares of %s" % (amt_to_buy, security.symbol))
            if amt_to_buy < 0:
                log.info("selling %s shares of %s" % (-amt_to_buy, security.symbol))
            order(security, amt_to_buy)
        
        # keep deques updated
        context.past_high_max[security] = max(context.past_high_max[security], data.current(security, 'high'))
        context.past_low_min[security] = min(context.past_low_min[security], data.current(security, 'low'))
 
def record_vars(context, data):
    # record the total price of all stocks. just a sort of benchmark.
    record(total_price=context.total_price)
