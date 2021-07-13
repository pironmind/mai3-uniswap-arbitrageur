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
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        return self.parse_int256(tx_receipt["returnData"])

    def profit_close(self, amount, profit_limit, caller):
        return self.contract.functions.profitClose(amount, profit_limit).call({'from': caller})

    def execute_profit_close(self, amount, profit_limit, caller):
        tx_hash = self.contract.functions.profitClose(
            amount,
            profit_limit).transact({
                'from': caller,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        return self.parse_int256(tx_receipt["returnData"])

    def deleverage_close(self, amount, max_leverage, caller):
        return self.contract.functions.deleverageClose(amount, max_leverage).call({'from': caller})

    def execute_deleverage_close(self, amount, max_leverage, caller):
        tx_hash = self.contract.functions.deleverageClose(
            amount,
            max_leverage).transact({
                'from': caller,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        return self.parse_int256(tx_receipt["returnData"])

    def execute_all_close(self, min_funding_rate, caller):
        tx_hash = self.contract.functions.allClose(
            min_funding_rate).transact({
                'from': caller,
            })
        tx_receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        return self.parse_int256(tx_receipt["returnData"])

    def account_info(self, caller):
        return self.contract.functions.readAccountInfo().call({'from': caller})

    def parse_int256(self, x):
        x = int(x, 16)
        if x & 2**255 != 0:
            return -(2**256 - x)
        else:
            return x

class ERC20(Contract):
    abi = Contract._load_abi(__name__, 'abi/ERC20.json')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)
        self.timeout = 120

    def approve(self, spender, caller):
        amount = 2 ** 255
        tx_hash = self.contract.functions.approve(spender,
            amount).transact({
                'from': caller,
            })
        receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        print(receipt)

class AccessControl(Contract):
    abi = Contract._load_abi(__name__, 'abi/AccessControl.json')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)
        self.timeout = 120

    def grant_privilege(self, grantee, caller):
        privilege = 7
        tx_hash = self.contract.functions.grantPrivilege(grantee,
            privilege).transact({
                'from': caller,
            })
        receipt = self.web3.eth.waitForTransactionReceipt(
            tx_hash, timeout=self.timeout)
        print(receipt)

