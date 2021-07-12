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

    def profit_open(self, amount, profit_limit, caller):
        return self.contract.functions.profitOpen(amount, profit_limit).call({'from': caller})

    def profit_close(self, amount, profit_limit, caller):
        return self.contract.functions.profitClose(amount, profit_limit).call({'from': caller})

    def deleverage_close(self, amount, max_leverage, caller):
        return self.contract.functions.deleverageClose(amount, max_leverage).call({'from': caller})

    def all_close(self, min_funding_rate, caller):
        return self.contract.functions.allClose(min_funding_rate).call({'from': caller})

    def account_info(self, caller):
        return self.contract.functions.readAccountInfo().call({'from': caller})
