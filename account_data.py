#CONFIGURATION DATA

#Strategy parameters with profiles: [0]= high risk, [1] = medium, [2] = low, [3] = PAC
PROFILES        = ["high", "medium", "low", "pac"]
SHORT_MA        = [10,  20, 50, None]   # high, medium, low, PAC (N/A)
LONG_MA         = [50,  100, 120, None]
RSI_PERIOD      = [9,   14,  14, None]
RSI_OVERBOUGHT  = [40,  50,  65, None]
RSI_OVERSOLD    = [60,  50,  35, None]
STOP_LOSS       = [0.03, 0.025, 0.02]    # 3%, 2.5%, 2% initial stop loss
TRAIL_PERCENT   = [0.03, 0.02,  0.015]   # 3%, 2%, 1,5% trailing stop
TAKE_PROFIT     = [0.08, 0.05,  0.03]    # 8%, 5%, 3% take profit (if used)

#Account parameters
SYMBOLS         = ["^NDX", "^SPX", "^GDAXI"]
INITIAL_DEPOSIT = 5000 #USD for simplicity
COMMISSION      = 0.0005 #spread commissions fixed for simplicity, for every trade

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