// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;

interface IAccessControl {
    function isGranted(
        address owner,
        address trader,
        uint256 privilege
    ) external view returns (bool);
}
