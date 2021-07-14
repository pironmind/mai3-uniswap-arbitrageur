import { Deployer } from './deployer'
import { printError } from './utils'

export async function restorableEnviron(ethers, options, job, ...args) {
    // detect network
    const deployer = new Deployer(ethers, options)
    await deployer.initialize();
    // main logic
    try {
        await job(ethers, deployer, ...args)
    } catch (err) {
        printError("Error occurs when deploying contracts:", err)
    }
    // save deployed
    deployer.finalize()
}

export async function readOnlyEnviron(ethers, options, job, ...args) {
    // detect network
    const deployer = new Deployer(ethers, options)
    await deployer.initialize();
    // main logic
    await job(ethers, deployer, ...args)
}
