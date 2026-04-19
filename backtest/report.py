import matplotlib.pyplot as plt

def plot_equity(equity):
    plt.plot(equity)
    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Capital")
    plt.show()