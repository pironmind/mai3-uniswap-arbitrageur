const chalk = require('chalk')

export function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export async function ensureFinished(transation): Promise<any> {
    const result = await transation;
    if (typeof result.deployTransaction != 'undefined') {
        await result.deployTransaction.wait()
    } else {
        await result.wait()
    }
    return result
}

export function printInfo(...message) {
    console.log(chalk.yellow("INFO "), ...message)
}

export function printError(...message) {
    console.log(chalk.red("ERRO "), ...message)
}