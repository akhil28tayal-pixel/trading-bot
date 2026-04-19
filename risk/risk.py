import config

daily_pnl = 0

def update_pnl(pnl):
    global daily_pnl
    daily_pnl += pnl


def check_limit():
    if daily_pnl <= -config.CAPITAL * config.DAILY_LOSS_LIMIT:
        return False
    return True