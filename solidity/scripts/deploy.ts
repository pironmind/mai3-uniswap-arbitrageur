const hre = require("hardhat")
const ethers = hre.ethers

import { DeploymentOptions } from './deployer/deployer'
import { restorableEnviron } from './deployer/environ'
import { printError } from './deployer/utils'

const ENV: DeploymentOptions = {
    network: hre.network.name,
    artifactDirectory: './artifacts/contracts',
    addressOverride: {}
}

function toWei(n) { return hre.ethers.utils.parseEther(n) };
function fromWei(n) { return hre.ethers.utils.formatEther(n); }

async function main(_, deployer, accounts) {
    await deployer.deployOrSkip("UniswapV3Arbitrage", "0x1F98431c8aD98523631AE4a59f267346ea31F984", "0x443b8225BEc07E1039e13A4162Ee3628d04B4c3b", "0x705ed5a688Ce3234644B2004Fafc08e77ED01575", 3000, "0x87a1e1C5D2f90Ba97c96DEA386E94d1e8A634087", 0, toWei("2"))
}

ethers.getSigners()
    .then(accounts => restorableEnviron(ethers, ENV, main, accounts))
    .then(() => process.exit(0))
    .catch(error => {
        printError(error);
        process.exit(1);
    });


