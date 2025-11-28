CS Graduation Project

This simple program uses official financial data from Yahoo Finance to elaborate a simple trading strategy based on the Moving Average Crossover method, and commands a demo account on Metatrader5 to buy/sell positions.
Data generated from the MT5 platform are then used to plot charts for study purposes.

Installing Dependencies:

This project uses a requirements.txt file.
You can install all dependencies by running auto_install.py with one command:

    python auto_install.py

Once the required dependencies are installed, You can then run the program by executing main.py:

    python main.py

The program will then:
    1. Check and save in a local .csv the desired symbol data
    2. Generate a signal according to the strategy and send it to the MT5 account
    3. Periodically save data generated
    4. Create and save graphs of the main KPIs

    The program keeps running and does a loop of signal generation every 5 minutes.
    At the end of each day runs a backtest to update results
