from web3 import Web3, HTTPProvider
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware
import time
from scipy import optimize
import logging
from logging.handlers import TimedRotatingFileHandler

from lib.address import Address
from lib.wad import Wad
from contract import Arbitrage

_logger = None
_debug_logger = None


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
        # absolute tolerance
        self.trade_amount_atol = Wad.from_number(trade_amount_atol)
        self.max_leverage = Wad.from_number(max_leverage)
        self.min_funding_rate = Wad.from_number(min_funding_rate)
        _, _, _, _, leverage, _, _, _ = self.read_account()
        assert self.max_leverage >= leverage, "invalid max leverage"

        self.last_print_time = 0

    @classmethod
    def logger(cls):
        global _logger
        if _logger is None:
            _logger = logging.getLogger(__name__)
            _logger.setLevel(logging.INFO)
            handler = TimedRotatingFileHandler("main.log", 'D')
            formatter = logging.Formatter(
                fmt='%(levelname)s %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
        return _logger

    @classmethod
    def debug_logger(cls):
        global _debug_logger
        if _debug_logger is None:
            _debug_logger = logging.getLogger(__name__ + 'debug')
            _debug_logger.setLevel(logging.DEBUG)
            handler = TimedRotatingFileHandler("debug.log", 'D')
            formatter = logging.Formatter(
                fmt='%(levelname)s %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            _debug_logger.addHandler(handler)
        return _debug_logger

    def profit_open_check(self):
        best_amount, min_cost = self.find_best_answer(
            self.profit_open_cost, 0, self.max_trade_amount.value, self.trade_amount_atol.value)
        best_amount = Wad(int(best_amount))
        max_profit = Wad(int(-min_cost))
        self.logger().info(
            f"[profit open] best amount:{round(float(best_amount), 4)}, max profit:{round(float(max_profit), 4)}")
        if max_profit >= self.profit_limit:
            try:
                status, profit = self.arb.execute_profit_open(
                    best_amount.value, self.profit_limit.value, self.account.address)
                if status == 1:
                    self.logger().info(
                        f"[profit open] [action] success open {round(float(best_amount), 4)} and profit {round(float(Wad(profit)), 4)}")
                else:
                    self.logger().info(
                        f"[profit open] [action] fail open {round(float(best_amount), 4)}")
                self.print_account_info()
            except Exception as e:
                self.logger().error(f"[profit open] [action] error:{e}")

    def profit_open_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.profit_open(
                amount, (Wad(0) - self.big_number).value, self.account.address)
            self.debug_logger().debug(
                f"[profit open] amount:{round(amount / 10**18, 4)} profit:{round(profit / 10**18, 4)}")
        except Exception as e:
            self.debug_logger().debug(f"[profit open] {e}")
            self.debug_logger().debug(
                f"[profit open] amount:{round(amount / 10**18, 4)} profit:{round(-(self.big_number.value + amount) / 10**18, 4)}")
            return float((self.big_number + Wad(amount)).value)
        return float(-profit)

    def profit_close_check(self, position, funding_rate):
        best_amount, min_cost = self.find_best_answer(
            self.profit_close_cost, 0, -position.value, self.trade_amount_atol.value)
        best_amount = Wad(int(best_amount))
        max_profit = Wad(int(-min_cost))
        self.logger().info(
            f"[profit close] best amount:{round(float(best_amount), 4)}, max profit:{round(float(max_profit), 4)}")
        if funding_rate <= Wad(0):
            # paying funding
            close_profit_limit = Wad.from_number(1)
        else:
            # receiving funding
            close_profit_limit = self.profit_limit
        if max_profit >= close_profit_limit:
            try:
                status, profit = self.arb.execute_profit_close(
                    best_amount.value, close_profit_limit.value, self.account.address)
                if status == 1:
                    self.logger().info(
                        f"[profit close] [action] success close {round(float(best_amount), 4)} and profit {round(float(Wad(profit)), 4)}")
                else:
                    self.logger().info(
                        f"[profit close] [action] fail close {round(float(best_amount), 4)}")
                self.print_account_info()
            except Exception as e:
                self.logger().error(f"[profit close] [action] error:{e}")

    def profit_close_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.profit_close(
                amount, (Wad(0)-self.big_number).value, self.account.address)
            self.debug_logger().debug(
                f"[profit close] amount:{round(amount / 10**18, 4)} profit:{round(profit / 10**18, 4)}")
        except Exception as e:
            self.debug_logger().debug(f"[profit close] {e}")
            self.debug_logger().debug(
                f"[profit close] amount:{round(amount / 10**18, 4)} profit:{round(-(self.big_number.value + amount) / 10**18, 4)}")
            return float((self.big_number + Wad(amount)).value)
        return float(-profit)

    def deleverage_close_check(self, effective_leverage, position):
        if effective_leverage >= self.max_leverage:
            best_amount, min_cost = self.find_best_answer(
                self.deleverage_close_cost, 0, -position.value, self.trade_amount_atol.value)
            best_amount = Wad(int(best_amount))
            max_profit = Wad(int(-min_cost))
            self.logger().info(
                f"[deleverage close] best amount:{round(float(best_amount), 4)} max profit:{round(float(max_profit), 4)}")
            try:
                status, profit = self.arb.execute_deleverage_close(
                    best_amount.value, self.max_leverage.value, self.account.address)
                if status == 1:
                    self.logger().info(
                        f"[deleverage close] [action] success close {round(float(best_amount), 4)} and profit {round(float(Wad(profit)), 4)}")
                else:
                    self.logger().info(
                        f"[deleverage close] [action] fail close {round(float(best_amount), 4)}")
                self.print_account_info()
            except Exception as e:
                self.logger().error(f"[deleverage close] [action] error:{e}")
        else:
            self.logger().info(
                f"[deleverage close] no need to deleverage, effective lev:{round(float(effective_leverage), 4)} max lev:{round(float(self.max_leverage), 4)}")

    def deleverage_close_cost(self, amount):
        amount = int(amount)
        try:
            profit = self.arb.deleverage_close(
                amount, self.max_leverage.value, self.account.address)
            self.debug_logger().debug(
                f"[deleverage close] amount:{round(amount / 10**18, 4)} profit:{round(profit / 10**18, 4)}")
        except Exception as e:
            self.debug_logger().debug(f"[deleverage close] {e}")
            self.debug_logger().debug(
                f"[deleverage close] amount:{round(amount / 10**18, 4)} profit:{round(-(self.big_number.value - amount) / 10**18, 4)}")
            return float((self.big_number - Wad(amount)).value)
        return float(-profit)

    def all_close_check(self, funding_rate, position):
        if funding_rate <= self.min_funding_rate:
            try:
                status, profit = self.arb.execute_all_close(
                    self.min_funding_rate.value, self.account.address)
                if status == 1:
                    self.logger().info(
                        f"[all close] [action] success close {round(float(Wad(0) - position), 4)} and profit {round(float(Wad(profit)), 4)}")
                else:
                    self.logger().info(
                        f"[all close] [action] fail close {round(float(Wad(0) - position), 4)}")
                self.print_account_info()
            except Exception as e:
                self.logger().error(f"[all close] [action] error:{e}")
        else:
            self.logger().info(
                f"[all close] no need to close all, fr:{round(float(funding_rate) * 100, 4)}% min fr:{round(float(self.min_funding_rate) * 100, 4)}%")

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
            self.logger().info(
                f"[read account] position: {round(float(underlying_asset_balance), 4)} vs {round(float(position), 4)}")
            self.logger().info(
                f"[read account] collateral: {round(float(collateral_balance), 4)} vs {round(float(available_cash), 4)}, total:{round(float(collateral_balance + available_cash), 4)}")
            self.logger().info(
                f"[read account] leverage set:{round(float(leverage), 4)}, now:{round(float(effective_leverage), 4)}")
            self.logger().info(
                f"[read account] {'receiving funding' if is_receive_funding else 'paying funding'}, funding rate:{round(float(funding_rate) * 100, 4)}%")
        except Exception as e:
            self.logger().error(f"[read account] error:{e}")


if __name__ == "__main__":
    arb_address = ""
    wallet_key = ""
    arbitrage = MyArbitrage(arb_address, wallet_key, 50, 100, 0.01, 5, -0.004)
    while True:
        if time.time() - arbitrage.last_print_time >= 60 * 5:
            arbitrage.print_account_info()
            arbitrage.last_print_time = time.time()
        arbitrage.profit_open_check()
        try:
            _, _, _, position, _, effective_leverage, funding_rate, _ = arbitrage.read_account()
        except Exception as e:
            arbitrage.logger().error(f"[read account] error:{e}")
            continue
        position = Wad(position)
        if not position.is_zero():
            arbitrage.profit_close_check(position, funding_rate)
            arbitrage.deleverage_close_check(effective_leverage, position)
            arbitrage.all_close_check(funding_rate, position)
