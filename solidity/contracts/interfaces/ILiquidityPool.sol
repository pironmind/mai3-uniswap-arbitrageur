// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma experimental ABIEncoderV2;

interface ILiquidityPool {
    enum PerpetualState {
        INVALID,
        INITIALIZING,
        NORMAL,
        EMERGENCY,
        CLEARED
    }

    function forceToSyncState() external;

    function getPerpetualInfo(uint256 perpetualIndex)
        external
        view
        returns (
            PerpetualState state,
            address oracle,
            int256[39] memory nums
        );

    function getMarginAccount(uint256 perpetualIndex, address trader)
        external
        view
        returns (
            int256 cash,
            int256 position,
            int256 availableMargin,
            int256 margin,
            int256 settleableMargin,
            bool isInitialMarginSafe,
            bool isMaintenanceMarginSafe,
            bool isMarginSafe,
            int256 targetLeverage
        );

    function trade(
        uint256 perpetualIndex,
        address trader,
        int256 amount,
        int256 limitPrice,
        uint256 deadline,
        address referrer,
        uint32 flags
    ) external returns (int256);

    function setTargetLeverage(
        uint256 perpetualIndex,
        address trader,
        int256 targetLeverage
    ) external;

    function deposit(
        uint256 perpetualIndex,
        address trader,
        int256 amount
    ) external;

    function withdraw(
        uint256 perpetualIndex,
        address trader,
        int256 amount
    ) external;
}
