// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.7.6;
pragma abicoder v2;

import "@uniswap/v3-periphery/contracts/libraries/OracleLibrary.sol";
import "@uniswap/v3-periphery/contracts/interfaces/IERC20Metadata.sol";
import "@openzeppelin/contracts/math/SignedSafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";

import "./SwapSingle.sol";
import "./libraries/SafeMathExt.sol";
import "./interfaces/IAccessControl.sol";
import "./interfaces/ILiquidityPool.sol";

contract UniswapV3Arbitrage is SwapSingle {
    using Address for address;
    using SafeMathExt for int256;
    using SignedSafeMath for int256;

    address public underlyingAsset;
    address public collateral;
    uint24 public fee;
    address public pool;
    uint256 public perpetualIndex;
    int256 public targetLeverage;
    uint8 internal underlyingAssetDecimals;
    uint8 internal collateralDecimals;

    constructor(
        address factory_,
        address underlyingAsset_,
        address collateral_,
        uint24 fee_,
        address pool_,
        uint256 perpetualIndex_,
        int256 targetLeverage_
    ) SwapSingle(factory_) {
        require(targetLeverage_ > 0, "invalid target leverage");
        (ILiquidityPool.PerpetualState state, , ) = ILiquidityPool(pool_)
        .getPerpetualInfo(perpetualIndex_);
        require(
            state == ILiquidityPool.PerpetualState.NORMAL,
            "perpetual is not NORMAL"
        );
        underlyingAsset = underlyingAsset_;
        collateral = collateral_;
        fee = fee_;
        pool = pool_;
        perpetualIndex = perpetualIndex_;
        targetLeverage = targetLeverage_;
        address poolAddress = PoolAddress.computeAddress(
            factory,
            PoolAddress.getPoolKey(underlyingAsset, collateral, fee_)
        );
        require(poolAddress.isContract(), "uniswap pool not exists");
        underlyingAssetDecimals = IERC20Metadata(underlyingAsset).decimals();
        collateralDecimals = IERC20Metadata(collateral).decimals();
        require(
            underlyingAssetDecimals <= 18 && collateralDecimals <= 18,
            "decimals exceed 18"
        );
    }

    function profitOpen(uint256 amount, int256 profitLimit)
        public
        returns (int256 profit)
    {
        ILiquidityPool(pool).forceToSyncState();
        (
            ,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            int256 availableMargin,
            ,
            ,

        ) = accountInfo();
        require(position <= 0, "position > 0");
        int256 beforeTotalCollateral = availableCash.add(collateralBalance);
        open(amount, availableMargin);
        bool isReceiveFunding;
        int256 effectiveLeverage;
        (
            ,
            collateralBalance,
            availableCash,
            ,
            ,
            effectiveLeverage,
            ,
            isReceiveFunding
        ) = accountInfo();
        require(isReceiveFunding, "pay funding");
        require(effectiveLeverage <= targetLeverage, "leverage too high");
        profit = availableCash.add(collateralBalance).sub(
            beforeTotalCollateral
        );
        require(profit >= profitLimit, "not enough profit");
    }

    function profitClose(uint256 amount, int256 profitLimit)
        public
        returns (int256 profit)
    {
        ILiquidityPool(pool).forceToSyncState();
        (
            ,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            ,
            ,
            ,

        ) = accountInfo();
        require(position < 0, "position >= 0 when profit close");
        int256 beforeTotalCollateral = availableCash.add(collateralBalance);
        close(amount);
        (, collateralBalance, availableCash, , , , , ) = accountInfo();
        profit = availableCash.add(collateralBalance).sub(
            beforeTotalCollateral
        );
        require(profit >= profitLimit, "not enough profit");
    }

    function deleverageClose(int256 maxLeverage, uint256 amount)
        public
        returns (int256)
    {
        require(
            maxLeverage >= targetLeverage,
            "max leverage < target leverage"
        );
        ILiquidityPool(pool).forceToSyncState();
        (
            ,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            ,
            int256 effectiveLeverage,
            ,

        ) = accountInfo();
        require(position < 0, "position >= 0 when deleverage close");
        require(effectiveLeverage >= maxLeverage, "no need to deleverage");
        int256 beforeTotalCollateral = availableCash.add(collateralBalance);
        close(amount);
        (
            ,
            collateralBalance,
            availableCash,
            ,
            ,
            effectiveLeverage,
            ,

        ) = accountInfo();
        require(effectiveLeverage <= targetLeverage, "deleverage not enough");
        return availableCash.add(collateralBalance).sub(beforeTotalCollateral);
    }

    function allClose(int256 minFundingRate) public returns (int256) {
        require(minFundingRate < 0, "minFundingRate >= 0");
        ILiquidityPool(pool).forceToSyncState();
        (
            ,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            ,
            ,
            int256 fundingRate,

        ) = accountInfo();
        require(position < 0, "position >= 0 when close all");
        require(fundingRate <= minFundingRate, "no need to close position");
        int256 beforeTotalCollateral = availableCash.add(collateralBalance);
        // close all
        close(uint256(position.neg()));
        (, collateralBalance, availableCash, , , , , ) = accountInfo();
        return availableCash.add(collateralBalance).sub(beforeTotalCollateral);
    }

    function open(uint256 amount, int256 availableMargin) internal {
        amount = amount / 10**(18 - underlyingAssetDecimals);
        require(amount > 0, "zero amount");
        int256 mcdexAmount = SafeCast
        .toInt256(amount * 10**(18 - underlyingAssetDecimals))
        .neg();
        if (availableMargin > 0) {
            ILiquidityPool(pool).withdraw(
                perpetualIndex,
                msg.sender,
                availableMargin
            );
        }
        ExactOutputSingleParams memory params = ExactOutputSingleParams({
            tokenIn: collateral,
            tokenOut: underlyingAsset,
            fee: fee,
            recipient: msg.sender,
            deadline: type(uint256).max,
            amountOut: amount,
            amountInMaximum: type(uint256).max,
            sqrtPriceLimitX96: 0
        });
        exactOutputSingle(params);
        int256 collateralBalance = SafeCast.toInt256(
            IERC20Metadata(collateral).balanceOf(msg.sender) *
                10**(18 - collateralDecimals)
        );
        if (collateralBalance > 0) {
            ILiquidityPool(pool).deposit(
                perpetualIndex,
                msg.sender,
                collateralBalance
            );
        }
        ILiquidityPool(pool).trade(
            perpetualIndex,
            msg.sender,
            mcdexAmount,
            0,
            type(uint256).max,
            msg.sender,
            Constant.MASK_MARKET_ORDER
        );
    }

    function close(uint256 amount) internal {
        amount = amount / 10**(18 - underlyingAssetDecimals);
        require(amount > 0, "zero amount");
        ExactInputSingleParams memory params = ExactInputSingleParams({
            tokenIn: underlyingAsset,
            tokenOut: collateral,
            fee: fee,
            recipient: msg.sender,
            deadline: type(uint256).max,
            amountIn: amount,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        });
        exactInputSingle(params);
        int256 mcdexAmount = SafeCast
        .toInt256(amount * 10**(18 - underlyingAssetDecimals))
        .neg();
        int256 collateralBalance = SafeCast.toInt256(
            IERC20Metadata(collateral).balanceOf(msg.sender) *
                10**(18 - collateralDecimals)
        );
        ILiquidityPool(pool).deposit(
            perpetualIndex,
            msg.sender,
            collateralBalance
        );
        ILiquidityPool(pool).trade(
            perpetualIndex,
            msg.sender,
            mcdexAmount,
            type(int256).max,
            type(uint256).max,
            msg.sender,
            Constant.MASK_MARKET_ORDER
        );
    }

    function accountInfo()
        internal
        view
        returns (
            int256 underlyingAssetBalance,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            int256 availableMargin,
            int256 effectiveLeverage,
            int256 fundingRate,
            bool isReceiveFunding
        )
    {
        int256 maxEffectiveLeverage = 9999 * 10**18;
        underlyingAssetBalance = SafeCast.toInt256(
            IERC20Metadata(underlyingAsset).balanceOf(msg.sender) *
                10**(18 - underlyingAssetDecimals)
        );
        collateralBalance = SafeCast.toInt256(
            IERC20Metadata(collateral).balanceOf(msg.sender) *
                10**(18 - collateralDecimals)
        );
        int256 margin;
        (
            availableCash,
            position,
            availableMargin,
            margin,
            ,
            ,
            ,
            ,

        ) = ILiquidityPool(pool).getMarginAccount(perpetualIndex, msg.sender);
        int256[39] memory nums;
        (, , nums) = ILiquidityPool(pool).getPerpetualInfo(perpetualIndex);
        fundingRate = nums[3];
        availableCash = availableCash.sub(position.wmul(nums[4]));
        (, int256 poolPosition, , , , , , , ) = ILiquidityPool(pool)
        .getMarginAccount(perpetualIndex, pool);
        isReceiveFunding = Utils.hasTheSameSign(position, poolPosition);
        if (margin.sub(nums[11]) == 0) {
            effectiveLeverage = position == 0 ? 0 : maxEffectiveLeverage;
        } else {
            effectiveLeverage = position.abs().wfrac(
                nums[1],
                margin.sub(nums[11])
            );
            if (effectiveLeverage < 0) {
                effectiveLeverage = maxEffectiveLeverage;
            }
        }
        require(
            underlyingAssetBalance.add(position) == 0,
            "net position not zero"
        );
    }

    function readAccountInfo()
        public
        returns (
            int256 underlyingAssetBalance,
            int256 collateralBalance,
            int256 availableCash,
            int256 position,
            int256 leverage,
            int256 effectiveLeverage,
            int256 fundingRate,
            bool isReceiveFunding
        )
    {
        leverage = targetLeverage;
        ILiquidityPool(pool).forceToSyncState();
        (
            underlyingAssetBalance,
            collateralBalance,
            availableCash,
            position,
            ,
            effectiveLeverage,
            fundingRate,
            isReceiveFunding
        ) = accountInfo();
    }
}
