"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
var signer_1 = require("@taquito/signer");
var taquito_1 = require("@taquito/taquito");
var Farm_json_1 = __importDefault(require("./ressources/Farm.json"));
var dotenv = __importStar(require("dotenv"));
dotenv.config(({ path: __dirname + '/.env' }));
var rpc = process.env.RPC || "http://127.0.0.1:20000/";
var pk = process.env.PK || "";
var Tezos = new taquito_1.TezosToolkit(rpc);
var signer = new signer_1.InMemorySigner(pk);
Tezos.setProvider({ signer: signer });
var farms = process.env.FARMSDB || "";
var admin = process.env.ADMIN || "";
var reserve = process.env.RESERVE || "";
var creation_time = new Date();
var farm_points = new taquito_1.MichelsonMap();
var lp = process.env.LP || '';
var infoFarm = process.env.INFOFARM || '';
var rate = process.env.RATE || 100;
var reward_at_week = new taquito_1.MichelsonMap();
var smak = process.env.SMAK || '';
var rewards = process.env.REWARDS || 1;
var user_points = new taquito_1.MichelsonMap();
var user_stakes = new taquito_1.MichelsonMap();
var weeks = process.env.WEEKS || 0;
function orig() {
    return __awaiter(this, void 0, void 0, function () {
        var store, originated, farmAddress, op, op2, op3, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    store = {
                        'admin': admin,
                        'creation_time': creation_time,
                        'farm_points': farm_points,
                        'lp_token_address': lp,
                        'rate': rate,
                        'reserve_address': reserve,
                        'reward_at_week': reward_at_week,
                        'smak_address': smak,
                        'total_reward': rewards,
                        'user_points': user_points,
                        'user_stakes': user_stakes,
                        'weeks': weeks,
                    };
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 15, , 16]);
                    return [4 /*yield*/, Tezos.contract.originate({
                            code: Farm_json_1.default,
                            storage: store,
                        })];
                case 2:
                    originated = _a.sent();
                    console.log("Waiting for farm " + originated.contractAddress + " to be confirmed...");
                    return [4 /*yield*/, originated.confirmation(2)];
                case 3:
                    _a.sent();
                    console.log('confirmed farm: ', originated.contractAddress);
                    farmAddress = originated.contractAddress;
                    return [4 /*yield*/, Tezos.contract.at(farmAddress)];
                case 4: return [4 /*yield*/, (_a.sent()).methods.increaseReward(0).send()];
                case 5:
                    op = _a.sent();
                    console.log("Waiting for increaseReward(0) " + op.hash + " to be confirmed...");
                    return [4 /*yield*/, op.confirmation(3)];
                case 6:
                    _a.sent();
                    console.log('confirmed increaseReward(0): ', op.hash);
                    if (!(smak !== lp)) return [3 /*break*/, 10];
                    return [4 /*yield*/, Tezos.contract.at(smak)];
                case 7: return [4 /*yield*/, (_a.sent()).methods.approve(farmAddress, rewards).send()];
                case 8:
                    op2 = _a.sent();
                    console.log("Waiting for approve " + op2.hash + " to be confirmed...");
                    return [4 /*yield*/, op2.confirmation(3)];
                case 9:
                    _a.sent();
                    console.log('confirmed approve: ', op2.hash);
                    _a.label = 10;
                case 10:
                    if (!(farms !== "")) return [3 /*break*/, 14];
                    return [4 /*yield*/, Tezos.contract.at(farms)];
                case 11: return [4 /*yield*/, (_a.sent()).methods.addFarm(farmAddress, infoFarm, lp).send()];
                case 12:
                    op3 = _a.sent();
                    console.log("Waiting for addFarm " + op3.hash + " to be confirmed...");
                    return [4 /*yield*/, op3.confirmation(3)];
                case 13:
                    _a.sent();
                    console.log('confirmed addFarm: ', op3.hash);
                    _a.label = 14;
                case 14: return [3 /*break*/, 16];
                case 15:
                    error_1 = _a.sent();
                    console.log(error_1);
                    return [3 /*break*/, 16];
                case 16: return [2 /*return*/];
            }
        });
    });
}
orig();
