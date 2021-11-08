# SMAK_Farming
### *The farming tool for Vortex, the Smartlink DEX !*

![Vortex logo](https://gateway.pinata.cloud/ipfs/QmSMzh5JEuPgPNHns9Svk25aPwQn2NtR1TFkd7n3mj2Ktp)



## Summary

###### I. Install the tools

###### II. Tests and compilation

###### III. Deployment



## I. Install the tools

#### I. 1) Install LIGO

OpenTezos offers great documentation so we will use it as a reference:
https://opentezos.com/ligo/installation

_You may simply execute LIGO through Docker to run the ligo CLI:_
`docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 [command without "ligo"]`

_Example:_
_To compile a smart-contract, you may use:_
`docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 compile contract [args]`

The list of ligo CLI is available on LIGOland:
https://ligolang.org/docs/api/cli-commands/

#### I. 2) Install Node
Node 14 or higher is required to run the originate function.

###### Install node on MAC
Go to https://nodejs.org/en/download/ and choose "macOS Installer".
Follow the instructions on the wizard.
Once it is complete, to check that the installation was successful, run:
`node -v`
`npm -v`

###### Install node on Linux
Open your terminal, and run:
sudo apt update
sudo apt install nodejs npm
Once it is complete, to check that the installation was successful, run:
`node -v`
`npm -v`

#### I.3) Install Taquito

_cf._ https://opentezos.com/dapp/taquito

#### I.4) Install Python

You may download from Python (https://wiki.python.org/moin/BeginnersGuide/Download) or install it from the CLI.
You may use python3.

#### I.5) Install Pytezos

_cf._ https://pypi.org/project/pytezos/



## II. Compilation and tests

#### II.1) Compilation du smart contract Farm

Run `ligo compile contract contract/main/main.mligo > contract/test/Farm.tz`
OR
`docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 compile contract contract/main/main.mligo -e main > contract/test/Farm.tz`

#### II.2) Compilation du smart contract Farms

Run `ligo compile contract contract/main/farms.mligo > contract/test/Farms.tz`
OR
`docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 compile contract contract/main/farms.mligo -e main > contract/test/Farms.tz`

#### II.3) Tests

In the contract/test/ repository, run `pytest [-k "filename"] [-s]`


## III. Deployment

#### III.1) Initialisation

* Run `docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 compile contract contract/main/main.mligo --michelson-format json > deploy/ressources/Farm.json`

* Go to the /deploy folder
`cd deploy`

* Install dependencies
Run `npm install`

#### III.2) Update environment variables

Adapt your .env file in the /deploy folder:

PK=[private key]
ADMIN=[admin address]
SMAK=[SMAK token contract address]
RPC=[network]
FARMSDB=[Farms contract address]
LP=[LP token address]
INFOFARM=[name of the LP pair]
RATE=[decreasing rate x10000]
REWARDS=[number of SMAK tokens as rewards for the entire farm lifetime]
WEEKS=[length of the farm lifetime]

#### III.3) [Only once] Originate the smart-contract Farms

From the root, run `docker run --rm -v "$PWD":"$PWD" -w "$PWD" ligolang/ligo:0.27.0 compile contract contract/main/farms.mligo --michelson-format json > deploy/ressources/Farms.json`

This contract reference all farm pools and it is generated only once at the start of the project.
In the folder /deploy, run `tsc deployFarmDb.ts --resolveJsonModule -esModuleInterop` then `node deployFarmDb.js`.

#### III.4) Originate a farm pool

In the folder /deploy, run `chmod +x deploy.sh && ./deploy.sh` or `bash deploy.sh`

It will:
* originate a new farm contract with the storage in the .ts file
* call the entrypoint increaseReward (with 0 as argument)
* approve the newly created farm smart-contract to spend SMAK for the amount in total_reward (will allow to transfer some SMAK tokens to the claiming users)
* call the entrypoint addFarm in the FARMS contract to register the newly created farm


## IV. Staking

The front-end will call the entry point approve on the LP token contract in order to allow the farm contract to use LP tokens owned by the user.

###### Staking mechanism schema (to be updated...)
![Staking schema](https://i.ibb.co/zP9Rxtg/Smartlink-Farm-light.png)
![Staking schema - night mode](https://i.ibb.co/1XdhScd/Smartlink-Farm-dark.png)
