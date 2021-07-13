from web3 import Web3, HTTPProvider
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware


from mai3_contract import ERC20, AccessControl
from lib.address import Address

def approve(w3, erc20_address, spender_address, account):
    erc20 = ERC20(w3, Address(erc20_address))
    erc20.approve(spender_address, account.address)

def grant_privilege(w3, pool_creator_address, grantee_address, account):
    access_control = AccessControl(w3, Address(pool_creator_address))
    access_control.grant_privilege(grantee_address, account.address)

if __name__ == "__main__":
    node_uri = "https://rinkeby.arbitrum.io/rpc"
    wallet_key = ""
    arbitrage_address = "0xa56f1AD41976fbBcA8E256bF1ddD26A293693f9c"
    collateral_address = "0x705ed5a688Ce3234644B2004Fafc08e77ED01575"
    underlying_asset_address = "0x443b8225BEc07E1039e13A4162Ee3628d04B4c3b"
    pool_creator_address = "0x0A1334aCea4E38a746daC7DCf7C3E61F0AB3D834"
    w3 = Web3(HTTPProvider(endpoint_uri=node_uri))
    account = Account().from_key(wallet_key)
    w3.middleware_onion.add(
        construct_sign_and_send_raw_middleware(account))
    approve(w3, collateral_address, arbitrage_address, account)
    approve(w3, underlying_asset_address, arbitrage_address, account)
    grant_privilege(w3, pool_creator_address, arbitrage_address, account)

