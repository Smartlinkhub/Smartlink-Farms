import { InMemorySigner } from '@taquito/signer';
import { TezosToolkit, MichelsonMap } from '@taquito/taquito';
import farms from './ressources/Farms.json';
import * as dotenv from 'dotenv'

dotenv.config(({path:__dirname+'/.env'}))
const rpc = process.env.RPC || "http://127.0.0.1:20000/"
const pk: string = process.env.PK || "";
const Tezos = new TezosToolkit(rpc);
const signer = new InMemorySigner(pk);
Tezos.setProvider({ signer: signer })

const admin = process.env.ADMIN || "";
let all_farms = new Array();
let all_farms_data = new MichelsonMap();
let inverse_farms = new MichelsonMap();

async function orig() {

    const store = {
        'admin': admin,
        'all_farms': all_farms,
        'all_farms_data': all_farms_data,
        'inverse_farms': inverse_farms
    }
    const originated = await Tezos.contract.originate({
        code: farms,
        storage: store,
    })
    await originated.confirmation(2);
    console.log("FARMS=", originated.contractAddress);
}


orig();
