import { task } from "hardhat/config";
import "@nomiclabs/hardhat-waffle";
import "solidity-coverage"

const pk = process.env["PK"]

task("accounts", "Prints the list of accounts", async (args, hre) => {
    const accounts = await hre.ethers.getSigners();

    for (const account of accounts) {
        console.log(account.address);
    }
});

task("encode", "Encode calldata")
    .addPositionalParam("sig", "Signature of contract to deploy")
    .addOptionalPositionalParam("args", "Args of function call, seprated by common ','")
    .setAction(async (args, hre) => {
        if (typeof args.args != 'undefined') {
            args.args = args.args.split(',')
        }
        args.sig = args.sig.replace('function ', '')
        var iface = new hre.ethers.utils.Interface(["function " + args.sig])
        var selector = args.sig.slice(0, args.sig.indexOf('('))
        // console.log(args.sig, args.args, selector)
        var calldata = iface.encodeFunctionData(selector, args.args)
        console.log("encoded calldata", calldata)
    })


task("deploy", "Deploy a single contract")
    .addPositionalParam("name", "Name of contract to deploy")
    .addOptionalPositionalParam("args", "Args of contract constructor, seprated by common ','")
    .setAction(async (args, hre) => {
        if (typeof args.args != 'undefined') {
            args.args = args.args.split('|')
        }
        const factory = await hre.ethers.getContractFactory(args.name);
        const contract = await factory.deploy(...args.args);
        console.log(args.name, "has been deployed to", contract.address);
    })

task("send", "Call contract function")
    .addPositionalParam("address", "Address of contract")
    .addPositionalParam("sig", "Signature of contract")
    .addOptionalPositionalParam("args", "Args of function call, seprated by common ','")
    .setAction(async (args, hre) => {
        if (typeof args.args != 'undefined') {
            args.args = args.args.split('|')
        }
        args.sig = args.sig.replace('function ', '')
        var iface = new hre.ethers.utils.Interface(["function " + args.sig])
        var selector = args.sig.slice(0, args.sig.indexOf('('))
        // console.log(args.sig, args.args, selector)
        var calldata = iface.encodeFunctionData(selector, args.args)
        // console.log("encoded calldata", calldata)
        const signer = hre.ethers.provider.getSigner(0);

        const tx = await signer.sendTransaction({
            to: args.address,
            from: signer._address,
            data: calldata,
        });
        console.log(tx);
        console.log(await tx.wait());
    })

task("call", "Call contract function")
    .addPositionalParam("address", "Address of contract")
    .addPositionalParam("sig", "Signature of contract")
    .addOptionalPositionalParam("args", "Args of function call, seprated by common ','")
    .setAction(async (args, hre) => {
        if (typeof args.args != 'undefined') {
            args.args = args.args.split('|')
        }
        args.sig = args.sig.replace('function ', '')
        var iface = new hre.ethers.utils.Interface(["function " + args.sig])
        var selector = args.sig.slice(0, args.sig.indexOf('('))
        console.log(args.sig, args.args, selector)
        var calldata = iface.encodeFunctionData(selector, args.args)
        //       console.log("encoded calldata", calldata)
        const signer = hre.ethers.provider.getSigner(0);
        const result = await signer.call({
            to: args.address,
            data: calldata,
        })
        console.log("result", result);
    })

module.exports = {
    defaultNetwork: "hardhat",
    networks: {
        hardhat: {
            allowUnlimitedContractSize: true
        },
        arb1: {
            url: "https://arb1.arbitrum.io/rpc",
            gasPrice: 2e8,
            accounts: [pk],
            timeout: 300000,
            confirmations: 1,
        },
        arbRinkeby: {
            url: "https://rinkeby.arbitrum.io/rpc",
            gasPrice: 1e9,
            accounts: [pk],
            timeout: 300000,
            confirmations: 1,
        },
    },
    solidity: {
        compilers: [
            {
                version: "0.7.4",
                settings: {
                    optimizer: {
                        enabled: true,
                        runs: 200
                    }
                }
            },
            {
                version: "0.7.6",
                settings: {
                    optimizer: {
                        enabled: true,
                        runs: 200
                    }
                }
            }
        ],
    },
    paths: {
        sources: "./contracts",
        tests: "./test",
        cache: "./cache",
        artifacts: "./artifacts"
    },
    contractSizer: {
        alphaSort: true,
        runOnCompile: false,
        disambiguatePaths: false,
    },
    abiExporter: {
        path: './abi',
        clear: false,
        flat: true,
        only: ['PoolCreator', 'LiquidityPool'],
    },
    mocha: {
        timeout: 60000
    }
};
