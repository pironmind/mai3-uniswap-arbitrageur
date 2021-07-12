// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.7.6;

library Constant {
    address internal constant INVALID_ADDRESS = address(0);
    uint32 internal constant MASK_MARKET_ORDER = 0x40000000;
    uint32 internal constant MASK_USE_TARGET_LEVERAGE = 0x08000000;

    int256 internal constant SIGNED_ONE = 10**18;
    uint256 internal constant UNSIGNED_ONE = 10**18;

    uint256 internal constant PRIVILEGE_DEPOSIT = 0x1;
    uint256 internal constant PRIVILEGE_WITHDRAW = 0x2;
    uint256 internal constant PRIVILEGE_TRADE = 0x4;
    uint256 internal constant PRIVILEGE_GUARD =
        PRIVILEGE_DEPOSIT | PRIVILEGE_WITHDRAW | PRIVILEGE_TRADE;
}
