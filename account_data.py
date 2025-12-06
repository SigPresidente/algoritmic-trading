#VARIOUS CONFIGURATION DATA

#Strategy parameters with profiles: [0]= high risk, [1] = medium, [2] = low
PROFILES        = ["high", "medium", "low"]
SHORT_MA        = [50,  100, 150]   # high, medium, low
LONG_MA         = [70,  150, 200]
RSI_PERIOD      = [7,   10,  14]
RSI_OVERBOUGHT  = [70,  65,  60]    # tighter = higher risk
RSI_OVERSOLD    = [30,  35,  40]

#Account parameters
SYMBOLS         = ["^NDX"]
INITIAL_DEPOSIT = 5000
COMMISSION      = 0.000 #no commissions on "manual" trading
STOP_LOSS       = 0.02 #2% SL fixed
TAKE_PROFIT     = 0.04 #4% TP when used
TRAIL_PERCENT   = 0.02 #2% trailing stop loss

#Metatrader5 Config
MT5_ACCOUNT     = "77777777"
MT5_PASSWORD    = "password"
MT5_SERVER      = "FirstPrudentialMarkets-Demo"
MAGIC_NUMBER    = "09031994"
LOT_SIZE        = 1.0
SLIPPAGE        = 20

#Output directory
OUTPUT_DIR      = "./output"

#Yfinance Config
START_DATE      = "2018-01-01"

#Robo Advisor Config (cost and returns based on risk profiles)
ROBO_COMMISSION = 0.015 #1.5% commission
ROBO_LOW_RISK   = 0.023 
ROBO_MEDIUM_RISK = 0.463
ROBO_HIGH_RISK  = 1.189 #Total returns from 01-01-2018, From MoneyFarm website