# Author: Ulysses 0. Andulte
# Date Created: November 2022

import json
from datetime import datetime

global message


# this class process message directly from the web socket, and parse it internally to obtain OLHC data internally
class Price_Action():
    # OHLC Variables
    _candleBodyHigh = 0.0
    _candleBodyLow = 0.0
    _candleWickHigh = 0.0
    _candleWickLow = 0.0
    _candleDirection = False

    # Range Variables
    _rangeBodyHigh = 0.0
    _rangeBodyLow = 0.0
    _rangeWickHigh = 0.0
    _rangeWickLow = 0.0

    # Counters
    _resistance_candle_count = 0
    _support_candle_count = 0
    _reset_resistance_candle_count = False
    _reset_support_candle_count = False

    # flags
    _long_position_flag = False
    _short_position_flag = False
    _trade_today = False
    _second_candle_flag = False

    # public variables
    candle_composition = 0
    trades_per_day = 0

    #
    _timeCurrent = datetime

    # functions
    def __init__(self):
        print('initialize')
        global message

    def _getCandleInfo(self, message):

        json_message = json.loads(message)

        # captures the OHLC of the streamed message
        candle = json_message['k']

        # captures timestamp and convert to datetime
        self._timeCurrent = datetime.utcfromtimestamp(candle['t'] / 1000)

        # captures "close" flag
        is_candle_closed = candle['x']

        # captures the closing price
        close = candle['c']
        open = candle['o']

        # previous candle is bullish
        if close > open:
            self._candleClose = candle['c']
            self._candleOpen = candle['o']
            self._candleHigh = candle['h']
            self._candleLow = candle['l']
            self._candleDirection = True

        # previous candle is bearish
        elif close < open:
            self._candleClose = candle['c']
            self._candleOpen = candle['o']
            self._candleHigh = candle['h']
            self._candleLow = candle['l']
            self._candleDirection = False

        # incase of doji candle
        else:
            self._candleClose = candle['c']
            self._candleOpen = candle['o']
            self._candleHigh = candle['h']
            self._candleLow = candle['l']
            self._candleDirection = True

    def _resetVariables(self):
        print('Reset Variables')
        self._candleBodyHigh = 0.0
        self._candleBodyLow = 0.0
        self_candleWickHigh = 0.0
        self_candleWickLow = 0.0
        self_candleDirection = False
        self._rangeBodyHigh = 0.0
        self._rangeBodyLow = 0.0
        self._rangeWickHigh = 0.0
        self._rangeWickLow = 0.0
        self._resistance_candle_count = 0
        self._support_candle_count = 0
        self._reset_resistance_candle_count = False
        self._reset_support_candle_count = False
        self._long_position_flag = False
        self._short_position_flag = False
        self._trade_today = False

    def _firstCandleUpdateSNR(self):
        self._rangeBodyHigh = self._candleBodyHigh
        self._rangeBodyLow = self._candleBodyLow
        self._rangeWickHigh = self._candleWickHigh
        self._rangeWickLow = self._candleWickLow
        print('FirstCandleUpdate')

    def _candleUpdateSNR(self):

        # RESISTANCE:
        # update range.wick_high and range.body_high from the incoming candles
        if (self._rangeWickHigh > 0 and self._rangeWickLow > 0 and
                self._resistance_candle_count <= self.candle_composition and self._resistance_candle_count > 0):

            # //this will update new resistance given that new candle establishes new high AND significant change (>1) difference AND bullish candle
            if (self._candleWickHigh > self._rangeWickHigh and self._candleBodyHigh > self._rangeBodyHigh and
                    abs(self._candleWickHigh > self._rangeWickHigh) > 0.1 and abs(self._candleBodyHigh > self._rangeBodyHigh) > 0.1):
                self._rangeBodyHigh = self._candleBodyHigh
                self._rangeWickHigh = self._candleWickHigh

                self._resistance_candle_count = 1
                self._reset_resistance_candle_count = True

        # SUPPORT:
        # update range.wick_low and range.body_low from the incoming candles
        if (self._rangeWickHigh > 0 and self._rangeWickLow > 0 and
                self._support_candle_count <= self.candle_composition and self._support_candle_count > 0):

            # //this will update new support given that new candle establishes new low AND significant change (>1) difference AND bearish candle
            if (self._candleWickLow > self._rangeWickLow and self._candleBodyLow > self._rangeBodyLow and
                    abs(self._candleWickLow > self._rangeWickLow) > 0.1 and abs(self._candleBodyLow > self._rangeBodyLow) > 0.1):
                self._rangeBodyLow = self._candleBodyLow
                self._rangeWickLow = self._candleWickLow

                self._support_candle_count = 1
                self._reset_support_candle_count = True

    def _getBuySellSignals(self):

        # Generate buy signal for long position
        # Bullish Signal 1st Condition:  Resistance_candle_counter greater than candle_composition (box range) and previous candle is bullish
        if (self._resistance_candle_count > self.candle_composition and self._candleDirection == True):

            # 2nd Condition: a breakout from the range resistance (wick_high)
            if self._rangeWickHigh < self._candleBodyHigh:

                # 3rd condition is to ensure that EA will only open position once/twice per day depending on user setting..
                if (self._trade_today == True and self._long_position_flag == False):

                    # update flags
                    if (self.trades_per_day == 2):
                        self._long_position_flag = True
                    if (self.trades_per_day == 1):
                        self._trade_today = False
                    return (11)  # return "11" BuyLong Signal

        # Generate sell signal for short position
        # Sell order 1st condition: Support_candle_counter greater than candle_composition (box range) and previous candle is bearish
        if (self._support_candle_count > self.candle_composition and self._candleDirection == False):

            # 2nd Condition: a breakout from the range resistance (wick_high)
            if self._rangeWickLow > self._candleBodyLow:

                # 3rd condition is to ensure that EA will only open position once/twice per day depending on user setting..
                if (self._trade_today == True and self._short_position_flag == False):

                    # update flags
                    if (self.trades_per_day == 2):
                        self._short_position_flag = True
                    if (self.trades_per_day == 1):
                        self._trade_today = False
                    return (10)  # return "10" Sell Short Signal

        return (0)  # return "0" if no signal was generated..

    def _updateFlags(self):

        if self._long_position_flag == True and self._short_position_flag == True:
            self._trade_today = False

        # resistance flags
        if self._reset_resistance_candle_count:
            self._resistance_candle_count = 1
            self._reset_resistance_candle_count = False
        else:
            self._reset_resistance_candle_count = self._reset_resistance_candle_count + 1  # increment resistance counter

        # support flags
        if self._reset_support_candle_count:
            self._support_candle_count = 1
            self._reset_support_candle_count = False
        else:
            self._reset_support_candle_count = self._reset_support_candle_count + 1  # increment support counter

    # main function
    def open_range_breakout(self, message):

        message = message
        output = 0

        # get latest candle closed info
        self._getCandleInfo(message)

        # Open of 1st candle of the day, this will only execute at candle open during the  first hour of the trading day
        if self._timeCurrent.hour == 0 and self._timeCurrent.minute == 0:  # start of new trading day, opening candle UTC 12am
            self._resetVariables()  # //reset all flags/variables: counters and range high and range low values at new trading day
            first_candle_flag = False
            self._second_candle_flag = True

        # Open of 2nd candle of the day..
        elif self._second_candle_flag == True:
            self._firstCandleUpdateSNR()
            self._updateFlags()
            self._second_candle_flag == False

        else:
            self._candleUpdateSNR()
            self._updateFlags()

        output = self._getBuySellSignals()
        return (output)
