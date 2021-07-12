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

    def execute_profit_open(self, amount, profit_limit, caller):
        tx_hash = self.contract.functions.profitOpen(
            amount,
            profit_limit).transact({
                'from': caller,
                'gasPrice': 1 * 10**9,
                'gas': 3000 * 1000,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout*2)
        return 2**256 - int(tx_receipt["returnData"], 16)

    def profit_close(self, amount, profit_limit, caller):
        return self.contract.functions.profitClose(amount, profit_limit).call({'from': caller})

    def execute_profit_close(self, amount, profit_limit, caller):
        tx_hash = self.contract.functions.profitClose(
            amount,
            profit_limit).transact({
                'from': caller,
                'gasPrice': 1 * 10**9,
                'gas': 3000 * 1000,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout*2)
        return 2**256 - int(tx_receipt["returnData"], 16)

    def deleverage_close(self, amount, max_leverage, caller):
        return self.contract.functions.deleverageClose(amount, max_leverage).call({'from': caller})

    def execute_deleverage_close(self, amount, max_leverage, caller):
        tx_hash = self.contract.functions.deleverageClose(
            amount,
            max_leverage).transact({
                'from': caller,
                'gasPrice': 1 * 10**9,
                'gas': 3000 * 1000,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout*2)
        return 2**256 - int(tx_receipt["returnData"], 16)

    def execute_all_close(self, min_funding_rate, caller):
        tx_hash = self.contract.functions.allClose(
            min_funding_rate).transact({
                'from': caller,
                'gasPrice': 1 * 10**9,
                'gas': 3000 * 1000,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout*2)
        return 2**256 - int(tx_receipt["returnData"], 16)

    def account_info(self, caller):
        return self.contract.functions.readAccountInfo().call({'from': caller})
