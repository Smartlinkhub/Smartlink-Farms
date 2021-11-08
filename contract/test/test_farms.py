from unittest import TestCase
from contextlib import contextmanager
from copy import deepcopy
from pytezos import ContractInterface, MichelsonRuntimeError, pytezos
from pytezos.michelson.types.big_map import big_map_diff_to_lazy_diff
import time

alice = 'tz1hNVs94TTjZh6BZ1PM5HL83A7aiZXkQ8ur'
admin = 'tz1fABJ97CJMSP2DKrQx2HAFazh6GgahQ7ZK'
bob = 'tz1c6PPijJnZYjKiSQND4pMtGMg6csGeAiiF'
oscar = 'tz1Phy92c2n817D17dUGzxNgw1qCkNSTWZY2'
fox = 'tz1XH5UyhRCUmCdUUbqD4tZaaqRTgGaFXt7q'

compiled_contract_path = "Farms.tz"
# Permet de charger le smart contract zvec Pytest de le simuler avec un faux storage
initial_storage = ContractInterface.from_file(compiled_contract_path).storage.dummy()
initial_storage["admin"] = admin
initial_storage["all_farms"] = []
initial_storage["all_farms_data"] = {}

farm_address = "KT1TwzD6zV3WeJ39ukuqxcfK2fJCnhvrdN1X"
lp_address ="KT1XtQeSap9wvJGY1Lmek84NU6PK6cjzC9Qd"
farm_lp_info = "pair colibri-pouet"

only_admin = "Only admin"
amount_zero = "This smart contract does not accept tez"

class FarmsContractTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.farms = ContractInterface.from_file(compiled_contract_path)
        cls.maxDiff = None

    @contextmanager
    def raisesMichelsonError(self, error_message):
        with self.assertRaises(MichelsonRuntimeError) as r:
            yield r

        error_msg = r.exception.format_stdout()
        if "FAILWITH" in error_msg:
            self.assertEqual(f"FAILWITH: '{error_message}'", r.exception.format_stdout())
        else:
            self.assertEqual(f"'{error_message}': ", r.exception.format_stdout())

    ######################################
    # Admin add a new farm (works) #
    ######################################
    def test_addFarm(self):
        init_storage = deepcopy(initial_storage)
        input = {}
        input["farm_address"] = farm_address
        input["lp_address"] = lp_address
        input["farm_lp_info"] = farm_lp_info

        res = self.farms.addFarm(input).interpret(storage=init_storage, sender=admin, amount=0)
        self.assertEqual(admin, res.storage["admin"])
        self.assertEqual([], res.operations)
        self.assertEqual(res.storage["all_farms"], [ farm_address ])
        self.assertEqual(res.storage["all_farms_data"][farm_address]["lp_address"], lp_address)
        self.assertEqual(res.storage["all_farms_data"][farm_address]["farm_lp_info"], farm_lp_info)
        
    ######################################
    # random user add a new farm (fails) #
    ######################################
    def test_addFarm_not_admin_fails(self):
        init_storage = deepcopy(initial_storage)
        input = {}
        input["farm_address"] = farm_address
        input["lp_address"] = lp_address
        input["farm_lp_info"] = farm_lp_info

        with self.raisesMichelsonError(only_admin):
            self.farms.addFarm(input).interpret(storage=init_storage, sender=alice)

    ######################################
    # Admin add a new farm with some tez (fails) #
    ######################################
    def test_addFarm_with_amount_fails(self):
        init_storage = deepcopy(initial_storage)
        input = {}
        input["farm_address"] = farm_address
        input["lp_address"] = lp_address
        input["farm_lp_info"] = farm_lp_info

        with self.raisesMichelsonError(amount_zero):
            self.farms.addFarm(input).interpret(storage=init_storage, sender=admin, amount=1)

