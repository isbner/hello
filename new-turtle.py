import math
from talib import ATR
import numpy as np


def initialize(context):
    set_slippage(slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
    set_commission(commission.PerShare(cost=0.0075, min_trade_cost=1))
    
    # Reference to SINA
    context.sina = sid(21448)
    context.security = context.sina
    
    # trading parameters
    context.atr_window = 10
    context.limit_unit = 2
    context.unit = 0
    context.MIN_ORDER_CASH_AMOUNT = 0
    context.MIN_ORDER_QUANTITY = 0
    
    schedule_function(rebalance, 
                      date_rules.every_day(), 
                      time_rules.market_open(hours=1))
    
    schedule_function(record_vars,                  
                      date_rules.every_day(),                  
                      time_rules.market_close())
    

# Record things helpful for our analysis and review.
# Now only check how many long and short positions we have.
def record_vars(context, data):
    longs = shorts = 0
    for position in context.portfolio.positions.itervalues():
        if position.amount > 0:
          longs += 1
        elif position.amount < 0:
          shorts += 1
    # Record our variables.
    record(leverage=context.account.leverage, 
           long_count=longs, 
           short_count=shorts)
    
    
def handle_data(context, data):
    if data.can_trade(context.security) is False:
        log.error("%s cannot be traded now" % context.security)
        pass
    
    # 获取历史数据 this should be done daily before market start
    hist = data.history(context.security, 'price', context.atr_window + 1, '1m')
#    if len(hist.index) < (context.user_data.T + 1):
#        context.log.warn("bar的数量不足, 等待下一根bar...")
#        return
    # hist = data.history(context.sina, 'close', 10, '1d')
    # print hist.mean()
    # 1 计算ATR
    atr = calc_atr(hist.iloc[:len(hist)-1])
    
    # 获取当前行情数据
    price = data.current(context.security, 'price')

    
    if context.hold_flag is True: # and context.account.huobi_cny_eth > 0:  # 先判断是否持仓
        # 2 判断加仓或止损
        long_short_position(context, data, price, atr)
    else:
        # 3 判断入场离场
        out = in_or_out(context, hist.iloc[:len(hist) - 1], price, context.user_data.T)
        if out is 1:
            open_position(context, data, price, atr)
        elif out is -1:
            close_position(context, data, price, atr)
        else:
            log.info("尚未入场或已经离场，不产生离场信号")    
        
def rebalance(context, data):
    # print "rebalance..."
    pass


def long_short_position(context, data, price, atr):
        temp = add_or_stop(price, context.last_buy_price, atr, context)
        if temp == 1:  # 判断加仓
            if context.add_time < context.limit_unit:  # 判断加仓次数是否超过上限
                log.info("产生加仓信号")
                cash_amount = min(context.portfolio.cash, context.unit * price)  # 不够1 unit时买入剩下全部
                context.last_buy_price = price
                if cash_amount >= context.MIN_ORDER_CASH_AMOUNT:
                    context.add_time += 1
                    log.info("正在买入 %s" % context.security)
                    log.info("下单金额为 %s 元" % cash_amount)
                    order(context.security, context.unit, style=LimitOrder(price))
                else:
                    log.info("订单无效，下单金额小于交易所最小交易金额")
            else:
                log.info("加仓次数已经达到上限，不会加仓")
        elif temp == -1:  # 判断止损
            # 重新初始化参数！重新初始化参数！重新初始化参数！非常重要！
            init_local_context(context)
            # 卖出止损
            log.info("产生止损信号")
            log.info("正在卖出 %s" % context.security)
            log.info("卖出数量为 %s" % context.portfolio.positions[context.security].amount)
            order(context.security, (-1)*context.portfolio.positions[context.security].amount)
            
            
def open_position(context, data, price, atr):
    if context.hold_flag is False:
        value = context.portfolio.portfolio_value * 0.01
        context.unit = calc_unit(value, atr)
        context.add_time = 1
        context.hold_flag = True
        context.last_buy_price = price
        cash_amount = min(context.portfolio.cash, context.unit * price)
        # 有买入信号，执行买入
        log.info("产生入场信号")
        log.info("正在买入 %s" % context.security)
        log.info("下单金额为 %s 元" % cash_amount)
        order(context.security, context.unit, style=LimitOrder(price))
    else:
        log.info("已经入场，不产生入场信号")
   

def close_position(context, data, price, atr):
    if context.hold_flag is False:
        log.info("尚未入场或已经离场，不产生离场信号") 
        return
    
    if context.portfolio.portfolio_value >= context.MIN_ORDER_QUANTITY:
        log.info("产生止盈离场信号")
        # 重新初始化参数！重新初始化参数！重新初始化参数！非常重要！
        init_local_context(context)
        # 有卖出信号，且持有仓位，则市价单全仓卖出
        log.info("正在卖出 %s" % context.security)
        log.info("卖出数量为 %s" % context.portfolio.positions[context.security].amount)
        order(context.security, context.portfolio.positions[context.security].amount)
   
    
# 用户自定义的函数，可以被handle_data调用：ATR值计算
def calc_atr(data):  # data是日线级别的历史数据
    atr = 0.0
    return atr

# 用户自定义的函数，可以被handle_data调用
# 判断是否加仓或止损:当价格相对上个买入价上涨 0.5ATR时，再买入一个unit; 当价格相对上个买入价下跌 2ATR时，清仓
def add_or_stop(price, lastprice, atr, context):
    if price >= lastprice + 0.5 * atr:
        context.log.info("当前价格比上一个购买价格上涨超过0.5个ATR")
        return 1
    elif price <= lastprice - 2 * atr:
        context.log.info("当前价格比上一个购买价格下跌超过2个ATR")
        return -1
    else:
        return 0
    

# 用户自定义的函数，可以被handle_data调用:用于初始化一些用户数据
def init_local_context(context):
    # 上一次买入价
    context.last_buy_price = 0
    # 是否持有头寸标志
    context.hold_flag = False
    # 限制最多买入的单元数
    context.limit_unit = 4
    # 现在买入1单元的security数目
    context.unit = 0
    # 买入次数
    context.add_time = 0
    

# 用户自定义的函数，可以被handle_data调用: 唐奇安通道计算及判断入场离场
# data是日线级别的历史数据，price是当前分钟线数据（用来获取当前行情），T代表需要多少根日线
def in_or_out(context, data, price, T):
    up = np.max(data["high"].iloc[-T:])
    # 这里是T/2唐奇安下沿，在向下突破T/2唐奇安下沿卖出而不是在向下突破T唐奇安下沿卖出，这是为了及时止损
 #   down = np.min(data["low"].iloc[-int(T / 2):])
    context.log.info("当前价格为: %s, 唐奇安上轨为: %s, 唐奇安下轨为: %s" % (price, up, down))
    # 当前价格升破唐奇安上沿，产生入场信号
    if price > up:
        context.log.info("价格突破唐奇安上轨")
        return 1
    # 当前价格跌破唐奇安下沿，产生出场信号
    elif price < down:
        context.log.info("价格跌破唐奇安下轨")
        return -1
    # 未产生有效信号
    else:
        return 0

#
# Utility
#

# 用户自定义的函数，可以被handle_data调用
# 计算unit
def calc_unit(per_value, atr):
    return per_value / atr
