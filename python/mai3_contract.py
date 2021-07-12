from web3 import Web3
import time

from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad

class Arbitrage(Contract):
    abi = Contract._load_abi(__name__, 'abi/UniswapV3Arbitrage.json')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)
        self.timeout = 120

    def buy_and_short_for_profit(self, amount, min_profit, caller):
        return self.contract.functions.arbitrageProfitBuyAndShort(amount, min_profit).call({'from': caller})

    def sell_and_long_for_profit(self, amount, min_profit, caller):
        return self.contract.functions.arbitrageProfitSellAndLong(amount, min_profit).call({'from': caller})

    def sell_and_long_for_deleverage(self, amount, caller):
        return self.contract.functions.arbitrageDeleverageSellAndLong(amount).call({'from': caller})

    def account_info(self, caller):
        return self.contract.functions.readAccountInfo().call({'from': caller})

    def get_max_leverage(self):
        return self.contract.functions.maxLeverage().call()

