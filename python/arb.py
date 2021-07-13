from web3 import Web3, HTTPProvider
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware
import time
from datetime import datetime
from scipy import optimize

from lib.address import Address
from lib.wad import Wad
from mai3_contract import Arbitrage


class MyArbitrage():

    big_number = Wad.from_number(9999999)

    def __init__(self, arb_address, wallet_key, profit_limit, max_trade_amount, trade_amount_atol, max_leverage, min_funding_rate):
        node_uri = "https://rinkeby.arbitrum.io/rpc"
        w3 = Web3(HTTPProvider(endpoint_uri=node_uri))
        self.arb = Arbitrage(w3, Address(arb_address))

        account = Account()
        self.account = account.from_key(wallet_key)
        w3.middleware_onion.add(
            construct_sign_and_send_raw_middleware(self.account))

        self.profit_limit = Wad.from_number(profit_limit)
        self.max_trade_amount = Wad.from_number(max_trade_amount)
        self.trade_amount_atol = Wad.from_number(trade_amount_atol)
        self.max_leverage = Wad.from_number(max_leverage)
        self.min_funding_rate = Wad.from_number(min_funding_rate)
        _, _, _, _, leverage, _, _, _ = self.read_account()
        assert self.max_leverage >= leverage, "invalid max leverage"

        self.last_print_time = 0

    def my_print(self, message):
        print(f"{str(datetime.now()).split('.')[0]} {message}")

    def profit_open_check(self):
        best_amount, min_cost = self.find_best_answer(
            self.profit_open_cost, 0, self.max_trade_amount.value, self.trade_amount_atol.value)
        best_amount = Wad(int(best_amount))
        max_profit = Wad(int(-min_cost))
        self.my_print(
            f"[profit open] best amount:{best_amount}, max profit:{max_profit}")
        if max_profit >= self.profit_limit:
            try:
                profit = self.arb.execute_profit_open(
                    best_amount.value, self.profit_limit.value, self.account.address)
                self.my_print(
                    f"[profit open] [action] open {best_amount} and profit {profit}")
                self.print_account_info()
            except Exception as e:
                self.my_print(f"[profit open] [action] error:{e}")

    def profit_open_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.profit_open(
                amount, (Wad(0) - self.big_number).value, self.account.address)
            self.my_print(f"amount:{amount / 10**18} profit:{profit / 10**18}")
        except Exception as e:
            self.my_print(e)
            self.my_print(
                f"amount:{amount / 10**18} profit:{int(self.big_number) * (amount + 1) / 10**18}")
            return float((self.big_number * (Wad(amount) + Wad.from_number(1))).value)
        return float(-profit)

    def profit_close_check(self, position):
        best_amount, min_cost = self.find_best_answer(
            self.profit_close_cost, 0, -position.value, self.trade_amount_atol.value)
        best_amount = Wad(int(best_amount))
        max_profit = Wad(int(-min_cost))
        self.my_print(
            f"[profit close] best amount:{best_amount}, max profit:{max_profit}")
        if max_profit >= self.profit_limit:
            try:
                profit = self.arb.execute_profit_close(
                    best_amount.value, self.profit_limit.value, self.account.address)
                self.my_print(
                    f"[profit close] [action] close {best_amount} and profit {profit}")
                self.print_account_info()
            except Exception as e:
                self.my_print(f"[profit close] [action] error:{e}")

    def profit_close_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.profit_close(
                amount, (Wad(0)-self.big_number).value, self.account.address)
            self.my_print(f"amount:{amount / 10**18} profit:{profit / 10**18}")
        except Exception as e:
            self.my_print(e)
            self.my_print(
                f"amount:{amount / 10**18} profit:{int(self.big_number) * (amount + 1) / 10**18}")
            return float((self.big_number * (Wad(amount) + Wad.from_number(1))).value)
        return float(-profit)

    def deleverage_close_check(self, effective_leverage, position):
        if effective_leverage >= self.max_leverage:
            best_amount, min_cost = self.find_best_answer(
                self.deleverage_close_cost, 0, -position.value, self.trade_amount_atol.value)
            best_amount = Wad(int(best_amount))
            max_profit = Wad(int(-min_cost))
            self.my_print(
                f"[deleverage close] best amount:{best_amount} max profit:{max_profit}")
            try:
                profit = self.arb.execute_deleverage_close(
                    best_amount.value, self.max_leverage.value, self.account.address)
                self.my_print(
                    f"[deleverage close] [action] close {best_amount} and profit {profit}")
                self.print_account_info()
            except Exception as e:
                self.my_print(f"[deleverage close] [action] error:{e}")

    def deleverage_close_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.deleverage_close(
                amount, self.max_leverage.value, self.account.address)
            self.my_print(f"amount:{amount / 10**18} profit:{profit / 10**18}")
        except Exception as e:
            self.my_print(e)
            self.my_print(
                f"amount:{amount / 10**18} profit:{int(self.big_number) * 10**18 / amount}")
            return float((self.big_number / Wad(amount)).value)
        return float(-profit)

    def all_close_check(self, funding_rate, position):
        if funding_rate <= self.min_funding_rate:
            try:
                profit = self.arb.execute_all_close(
                    self.min_funding_rate.value, self.account.address)
                self.my_print(
                    f"[all close] [action] close {Wad(0) - position} and profit {profit}")
                self.print_account_info()
            except Exception as e:
                self.my_print(f"[all close] [action] error:{e}")

    def read_account(self):
        underlying_asset_balance, collateral_balance, available_cash, position, leverage, effective_leverage, funding_rate, is_receive_funding = self.arb.account_info(
            self.account.address)
        return Wad(underlying_asset_balance), Wad(collateral_balance), Wad(available_cash), Wad(position), Wad(leverage), Wad(effective_leverage), Wad(funding_rate), is_receive_funding

    def find_best_answer(self, func, begin, end, xatol):
        sol = optimize.minimize_scalar(
            func, method='Bounded', bounds=[begin, end], options={'xatol': xatol})
        return sol.x, func(sol.x)

    def print_account_info(self):
        try:
            underlying_asset_balance, collateral_balance, available_cash, position, leverage, effective_leverage, funding_rate, is_receive_funding = self.read_account()
            self.my_print(
                f"[read account] position: {underlying_asset_balance} vs {position}")
            self.my_print(
                f"[read account] collateral: {collateral_balance} vs {available_cash}, total:{collateral_balance + available_cash}")
            self.my_print(
                f"[read account] leverage set:{leverage}, now:{effective_leverage}")
            self.my_print(
                f"[read account] {'receiving funding' if is_receive_funding else 'paying funding'}, funding rate:{funding_rate}")
        except Exception as e:
            self.my_print(f"[read account] error:{e}")


if __name__ == "__main__":
    arb_address = "0x4618dF3679B7cE1ba4Fc4Fa8Da1F17B7c46D7d02"
    wallet_key = "dc1dfb1ba0850f1e808eb53e4c83f6a340cc7545e044f0a0f88c0e38dd3fa40d"
    arbitrage = MyArbitrage(arb_address, wallet_key, 100, 100, 0.01, 5, -0.01)
    while True:
        if time.time() - arbitrage.last_print_time >= 60:
            arbitrage.print_account_info()
            arbitrage.last_print_time = time.time()
        arbitrage.profit_open_check()
        try:
            _, _, _, position, _, effective_leverage, funding_rate, _ = arbitrage.read_account()
        except Exception as e:
            arbitrage.my_print(f"[read account] error:{e}")
            continue
        position = Wad(position)
        if not position.is_zero():
            arbitrage.profit_close_check(position)
            arbitrage.deleverage_close_check(effective_leverage, position)
            arbitrage.all_close_check(funding_rate, position)
