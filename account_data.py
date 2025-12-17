#VARIOUS CONFIGURATION DATA

#Strategy parameters with profiles: [0]= high risk, [1] = medium, [2] = low, [3] = PAC
PROFILES        = ["high", "medium", "low", "pac"]
SHORT_MA        = [50,  50, 50, None]   # high, medium, low, PAC (N/A)
LONG_MA         = [120,  120, 200, None]
RSI_PERIOD      = [10,   10,  14, None]
RSI_OVERBOUGHT  = [65,  65,  60, None]
RSI_OVERSOLD    = [35,  35,  40, None]

#Account parameters
SYMBOLS         = ["^NDX"]
INITIAL_DEPOSIT = 5000
COMMISSION      = 0.0005 #spread commissions fixed for simplicity, for every trade
STOP_LOSS       = 0.02 #2% SL fixed
TAKE_PROFIT     = 0.04 #4% TP fixed (when used)
TRAIL_PERCENT   = 0.02 #2% trailing stop loss

#PAC (Piano Accumulo Capitale) parameters
PAC_MONTHLY_INVESTMENT = 100  # Amount to invest each month

#Italy Tax parameters
ITALY_CAPITAL_GAINS_TAX = 0.26  # 26% tax on capital gains

#Metatrader5 Config
MT5_ACCOUNT     = "77777777"
MT5_PASSWORD    = "password"
MT5_SERVER      = "FirstPrudentialMarkets-Demo"
MAGIC_NUMBER    = "09031994"
LOT_SIZE        = 1.0
SLIPPAGE        = 20

#Output directory for saving data
OUTPUT_DIR      = "./output"

#Yfinance Config
START_DATE      = "2018-01-01"

#Robo Advisor Config (cost and returns based on risk profiles)
ROBO_COMMISSION = 0.0128 #1.28% annual total commission
ROBO_LOW_RISK   = 0.023 #Total returns from 01-01-2018, From MoneyFarm website (low)
ROBO_MEDIUM_RISK = 0.463 #Total returns from 01-01-2018, From MoneyFarm website (medium)    
ROBO_HIGH_RISK  = 1.189 #Total returns from 01-01-2018, From MoneyFarm website (high)