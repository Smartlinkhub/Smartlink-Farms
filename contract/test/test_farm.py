from unittest import TestCase
from contextlib import contextmanager
from copy import deepcopy
from pytezos import ContractInterface, MichelsonRuntimeError, pytezos
from pytezos.michelson.types.big_map import big_map_diff_to_lazy_diff
import time
import json 

alice = 'tz1hNVs94TTjZh6BZ1PM5HL83A7aiZXkQ8ur'
admin = 'tz1fABJ97CJMSP2DKrQx2HAFazh6GgahQ7ZK'
bob = 'tz1c6PPijJnZYjKiSQND4pMtGMg6csGeAiiF'
oscar = 'tz1Phy92c2n817D17dUGzxNgw1qCkNSTWZY2'
fox = 'tz1XH5UyhRCUmCdUUbqD4tZaaqRTgGaFXt7q'

sec_week = 604800
farm_address = "KT1BEqzn5Wx8uJrZNvuS9DVHmLvG9td3fDLi" # Hardcoded farm address for tests
compiled_contract_path = "Farm.tz"

initial_storage = ContractInterface.from_file(compiled_contract_path).storage.dummy()
initial_storage["admin"] = admin
initial_storage["total_reward"] = 10000000
initial_storage["weeks"] = 5
initial_storage["rate"] = 7500
initial_storage["smak_address"] = "KT1TwzD6zV3WeJ39ukuqxcfK2fJCnhvrdN1X"
initial_storage["lp_token_address"] ="KT1XtQeSap9wvJGY1Lmek84NU6PK6cjzC9Qd"
initial_storage["reserve_address"] = "tz1fABJ97CJMSP2DKrQx2HAFazh6GgahQ7ZK"

only_admin = "Only the contract admin can change the contract administrator or increase reward"
unknown_lp_contract = "This farm works with a different LP token"
unknown_smak_contract  = "Cannot connect to the SMAK contract"
unknown_user_unstake = "You do not have any LP token to unstake"
unknown_user_claim = "You do not have any reward to claim"
farm_empty_week = "Farm has no cumulated stake for one week"
amount_is_null = "The staking amount must be greater than zero"
amount_must_be_zero_tez = "You must not send Tezos to the smart contract"
time_too_early ="Please try again in few seconds"
no_stakes  = "You did not stake any token yet"
unstake_more_than_stake  = "You cannot unstake more than your staking"
user_no_points = "You do not have or no longer have any rewards"
rewards_sent_but_missing_points = "You do not have any reward to claim"
no_week_left = "There are no more weeks left for staking"

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

    ######################
    # Tests for setAdmin #
    ######################

    def test_setAdmin_should_work(self):
        init_storage = deepcopy(initial_storage)
        res = self.farms.setAdmin(bob).interpret(storage=init_storage, sender=admin, now=int(sec_week + sec_week/2))
        self.assertEqual(bob, res.storage["admin"])
        self.assertEqual([], res.operations)

    def test_setAdmin_user_sets_new_admin_should_fail(self):
        init_storage = deepcopy(initial_storage)
        with self.raisesMichelsonError(only_admin):
            self.farms.setAdmin(bob).interpret(storage=init_storage, sender=alice, now=int(sec_week + sec_week/2))

    def test_setAdmin_sending_XTZ_should_fail(self):
        init_storage = deepcopy(initial_storage)
        with self.raisesMichelsonError(amount_must_be_zero_tez):
            self.farms.setAdmin(bob).interpret(storage=init_storage, sender=admin, now=int(sec_week + sec_week/2), amount=1)

    ############################
    # Test rewards computation #
    ############################

    def test_initializeReward_5week_20Kreward_75rate_initialization_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["weeks"] = 5
        init_storage["rate"] = 7500
        res = self.farms.increaseReward(0).interpret(storage=init_storage, sender=admin)

        reward_week_1 = int(res.storage["reward_at_week"][1])
        reward_week_2 = int(res.storage["reward_at_week"][2])
        reward_week_3 = int(res.storage["reward_at_week"][3])
        reward_week_4 = int(res.storage["reward_at_week"][4])
        reward_week_5 = int(res.storage["reward_at_week"][5])
        self.assertEqual(reward_week_1, 6555697)
        self.assertEqual(reward_week_2, 4916773)
        self.assertEqual(reward_week_3, 3687580)
        self.assertEqual(reward_week_4, 2765685)
        self.assertEqual(reward_week_5, 2074263)

    def test_initializeReward_5week_30Kreward_80rate_initialization_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 30_000_000
        init_storage["weeks"] = 5
        init_storage["rate"] = 8000
        res = self.farms.increaseReward(0).interpret(storage=init_storage, sender=admin)

        reward_week_1 = int(res.storage["reward_at_week"][1])
        reward_week_2 = int(res.storage["reward_at_week"][2])
        reward_week_3 = int(res.storage["reward_at_week"][3])
        reward_week_4 = int(res.storage["reward_at_week"][4])
        reward_week_5 = int(res.storage["reward_at_week"][5])
        self.assertEqual(reward_week_1, 8924321)
        self.assertEqual(reward_week_2, 7139457)
        self.assertEqual(reward_week_3, 5711565)
        self.assertEqual(reward_week_4, 4569252)
        self.assertEqual(reward_week_5, 3655402)

    def test_initializeReward_3week_40Kreward_60rate_initialization_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 40_000_000
        init_storage["weeks"] = 3
        init_storage["rate"] = 6000
        res = self.farms.increaseReward(0).interpret(storage=init_storage, sender=admin)

        reward_week_1 = int(res.storage["reward_at_week"][1])
        reward_week_2 = int(res.storage["reward_at_week"][2])
        reward_week_3 = int(res.storage["reward_at_week"][3])
        self.assertEqual(reward_week_1, 20408163)
        self.assertEqual(reward_week_2, 12244897)
        self.assertEqual(reward_week_3, 7346938)

    #########################
    # Test rewards increase #
    #########################

    def test_increaseReward_reward_50k_on_week_3_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["weeks"] = 5
        init_storage["rate"] = 7500
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        res = self.farms.increaseReward(50_000_000).interpret(storage=init_storage, sender=admin, now=int(sec_week * 2 + sec_week/2))

        self.assertEqual(res.storage["total_reward"], 70000000)
        self.assertEqual(res.storage["weeks"], 5)
        reward_week_1 = int(res.storage["reward_at_week"][1])
        reward_week_2 = int(res.storage["reward_at_week"][2])
        reward_week_3 = int(res.storage["reward_at_week"][3])
        reward_week_4 = int(res.storage["reward_at_week"][4])
        reward_week_5 = int(res.storage["reward_at_week"][5])
        self.assertEqual(reward_week_1, 6555697)
        self.assertEqual(reward_week_2, 4916773)
        self.assertEqual(reward_week_3, 25309202)
        self.assertEqual(reward_week_4, 18981901)
        self.assertEqual(reward_week_5, 14236426)

    def test_increaseReward_reward_20k_on_week_2_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 10_000_000
        init_storage["weeks"] = 3
        init_storage["rate"] = 7500
        init_storage["reward_at_week"] = {
            1: 4324324,
            2: 3243243,
            3: 2432432,
        }
        res = self.farms.increaseReward(20_000_000).interpret(storage=init_storage, sender=admin, now=int(sec_week + sec_week/2))

        self.assertEqual(res.storage["total_reward"], 30000000)
        self.assertEqual(res.storage["weeks"], 3)
        reward_week_1 = int(res.storage["reward_at_week"][1])
        reward_week_2 = int(res.storage["reward_at_week"][2])
        reward_week_3 = int(res.storage["reward_at_week"][3])
        self.assertEqual(reward_week_1, 4324324)
        self.assertEqual(reward_week_2, 14671814)
        self.assertEqual(reward_week_3, 11003861)

    def test_increaseReward_if_not_admin_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 10_000_000
        init_storage["weeks"] = 3
        init_storage["rate"] = 7500
        init_storage["reward_at_week"] = {
            1: 4324324,
            2: 3243243,
            3: 2432432,
        }
        with self.raisesMichelsonError(only_admin):
            res = self.farms.increaseReward(20_000_000).interpret(storage=init_storage, sender=fox, now=int(sec_week + sec_week/2))

    def test_increaseReward_after_end_of_pool_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 10_000_000
        init_storage["weeks"] = 3
        init_storage["rate"] = 7500
        init_storage["reward_at_week"] = {
            1: 4324324,
            2: 3243243,
            3: 2432432,
        }
        with self.raisesMichelsonError(no_week_left):
            res = self.farms.increaseReward(20_000_000).interpret(storage=init_storage, sender=admin, now=int(sec_week * 20 + sec_week/2))


    ######################
    # Tests for Staking #
    ######################

    def test_stake_one_time_on_second_week_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {}
        init_storage["user_points"] = {}
        init_storage["farm_points"] = {}
        init_storage["creation_time"] = 0
        staking_time = int(sec_week + sec_week/2)
        locked_amount = 20

        res = self.farms.stake(locked_amount).interpret(storage=init_storage, sender=bob, now=staking_time)

        self.assertEqual(admin, res.storage["admin"])
        transfer_tx = res.operations[0]
        transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
        self.assertEqual(bob, transfer_tx_params[0]['string'])
        self.assertEqual(farm_address, transfer_tx_params[1]['string'])
        self.assertEqual(locked_amount, int(transfer_tx_params[2]['int']))

        user_stakes = res.storage["user_stakes"]
        self.assertEqual(locked_amount, user_stakes[bob])
        self.assertEqual(1, len(user_stakes.keys()))

        farm_points = res.storage["farm_points"]
        self.assertEqual(sec_week * locked_amount / 2, farm_points[2])
        self.assertEqual(sec_week * locked_amount, farm_points[3])
        self.assertEqual(sec_week * locked_amount, farm_points[4])
        self.assertEqual(sec_week * locked_amount, farm_points[5])

        user_points = res.storage["user_points"]
        user_points_keys = user_points.keys()
        self.assertEqual(1, len(user_points_keys))
        self.assertEqual(bob, list(user_points_keys)[0])
        self.assertEqual(sec_week * locked_amount / 2, user_points[bob][2])
        self.assertEqual(sec_week * locked_amount, user_points[bob][3])
        self.assertEqual(sec_week * locked_amount, user_points[bob][4])
        self.assertEqual(sec_week * locked_amount, user_points[bob][5])

    def test_stake_with_XTZ_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {}
        init_storage["user_points"] = {}
        init_storage["farm_points"] = {}
        init_storage["creation_time"] = 0
        staking_time = int(sec_week + sec_week/2)
        locked_amount = 20

        with self.raisesMichelsonError(amount_must_be_zero_tez):
            self.farms.stake(locked_amount).interpret(storage=init_storage, sender=bob, now=staking_time, amount=1)


    def test_stake_multiple_times_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {}
        init_storage["user_points"] = {}
        init_storage["farm_points"] = {}
        init_storage["creation_time"] = 0
        staking_time_1 = int(2*sec_week + sec_week/2)
        locked_amount_1 = 300

        res1 = self.farms.stake(locked_amount_1).interpret(storage=init_storage, sender=bob, now=staking_time_1)

        self.assertEqual(admin, res1.storage["admin"])
        transfer_tx = res1.operations[0]
        transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
        self.assertEqual(bob, transfer_tx_params[0]['string'])
        self.assertEqual(farm_address, transfer_tx_params[1]['string'])
        self.assertEqual(locked_amount_1, int(transfer_tx_params[2]['int']))

        user_stakes = res1.storage["user_stakes"]
        self.assertEqual(locked_amount_1, user_stakes[bob])
        self.assertEqual(1, len(user_stakes.keys()))

        farm_points = res1.storage["farm_points"]
        self.assertEqual(sec_week * locked_amount_1 / 2, farm_points[3])
        self.assertEqual(sec_week * locked_amount_1, farm_points[4])
        self.assertEqual(sec_week * locked_amount_1, farm_points[5])

        user_points = res1.storage["user_points"]
        user_points_keys = user_points.keys()
        self.assertEqual(1, len(user_points_keys))
        self.assertEqual(bob, list(user_points_keys)[0])
        self.assertEqual(sec_week * locked_amount_1 / 2, user_points[bob][3])
        self.assertEqual(sec_week * locked_amount_1, user_points[bob][4])
        self.assertEqual(sec_week * locked_amount_1, user_points[bob][5])

        new_storage = deepcopy(initial_storage)
        new_storage["user_stakes"][bob] = 300
        new_storage["user_points"] = {
            bob: {
                1: 0,
                2: 0,
                3: int(300 * sec_week / 2),
                4: 300 * sec_week,
                5: 300 * sec_week
            }
        }
        new_storage["farm_points"] = {
            1: 0,
            2: 0,
            3: int(300 * sec_week / 2),
            4: 300 * sec_week,
            5: 300 * sec_week
        }
        new_storage["creation_time"] = 0
        staking_time_2 = int(3*sec_week + sec_week*2/3)
        locked_amount_2 = 500

        res2 = self.farms.stake(locked_amount_2).interpret(storage=new_storage, sender=bob, now=staking_time_2)

        self.assertEqual(admin, res2.storage["admin"])
        transfer_tx = res2.operations[0]
        transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
        self.assertEqual(bob, transfer_tx_params[0]['string'])

        self.assertEqual(farm_address, transfer_tx_params[1]['string'])
        self.assertEqual(locked_amount_2, int(transfer_tx_params[2]['int']))

        user_stakes = res2.storage["user_stakes"]
        self.assertEqual(locked_amount_1 + locked_amount_2, user_stakes[bob])
        self.assertEqual(1, len(user_stakes.keys()))

        farm_points = res2.storage["farm_points"]
        self.assertEqual(sec_week * locked_amount_1 / 2, farm_points[3])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2 / 3, farm_points[4])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2 , farm_points[5])

        user_points = res2.storage["user_points"]
        user_points_keys = user_points.keys()
        self.assertEqual(1, len(user_points_keys))
        self.assertEqual(bob, list(user_points_keys)[0])
        self.assertEqual(sec_week * locked_amount_1 / 2, user_points[bob][3])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2 / 3, user_points[bob][4])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2 , user_points[bob][5])

    def test_stake_with_two_users_should_work(self):
        new_storage = deepcopy(initial_storage)
        new_storage["user_stakes"][bob] = 300
        new_storage["user_points"] = {
            bob: {
                1: 0,
                2: 0,
                3: int(300 * sec_week / 2),
                4: 300 * sec_week,
                5: 300 * sec_week
            }
        }
        new_storage["farm_points"] = {
            1: 0,
            2: 0,
            3: int(300 * sec_week / 2),
            4: 300 * sec_week,
            5: 300 * sec_week
        }
        new_storage["creation_time"] = 0
        locked_amount_1 = 300
        staking_time_2 = int(2*sec_week + sec_week*2/3)
        locked_amount_2 = 400

        res2 = self.farms.stake(locked_amount_2).interpret(storage=new_storage, sender=alice, now=staking_time_2)

        self.assertEqual(admin, res2.storage["admin"])
        transfer_tx = res2.operations[0]
        transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
        self.assertEqual(alice, transfer_tx_params[0]['string'])
        self.assertEqual(farm_address, transfer_tx_params[1]['string'])
        self.assertEqual(locked_amount_2, int(transfer_tx_params[2]['int']))

        user_stakes = res2.storage["user_stakes"]
        self.assertEqual(locked_amount_2, user_stakes[alice])
        self.assertEqual(2, len(user_stakes.keys()))

        farm_points = res2.storage["farm_points"]
        self.assertEqual(sec_week * locked_amount_1 / 2 + sec_week * locked_amount_2 / 3, farm_points[3])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2, farm_points[4])
        self.assertEqual(sec_week * locked_amount_1 + sec_week * locked_amount_2, farm_points[5])

        user_points = res2.storage["user_points"]
        user_points_keys = user_points.keys()
        self.assertEqual(2, len(user_points_keys))
        self.assertEqual(alice, list(user_points_keys)[1])
        self.assertEqual(sec_week * locked_amount_2 / 3, user_points[alice][3])
        self.assertEqual(sec_week * locked_amount_2, user_points[alice][4])
        self.assertEqual(sec_week * locked_amount_2, user_points[alice][5])

    def test_stake_0_LP_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {}
        init_storage["user_points"] = {}
        init_storage["farm_points"] = {}
        init_storage["creation_time"] = 0
        locked_amount = 0

        with self.raisesMichelsonError(amount_is_null):
            res = self.farms.stake(locked_amount).interpret(storage=init_storage, sender=alice, now=int(sec_week + sec_week/2))
    
    def test_stake_after_end_of_pool_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {}
        init_storage["user_points"] = {}
        init_storage["farm_points"] = {}
        init_storage["creation_time"] = 0
        locked_amount = 10

        with self.raisesMichelsonError(no_week_left):
            self.farms.stake(locked_amount).interpret(storage=init_storage, sender=alice, now=int(5 * sec_week + sec_week/2))

    def test_stake_after_increasing_reward_should_work(self):
            init_storage = deepcopy(initial_storage)
            init_storage["total_reward"] = 10_000_000
            init_storage["weeks"] = 3
            init_storage["rate"] = 7500
            init_storage["reward_at_week"] = {
                1: 4324324,
                2: 3243243,
                3: 2432432,
            }
            locked_amount = 10000
            res = self.farms.increaseReward(20_000_000).interpret(storage=init_storage, sender=admin, now=int(sec_week + sec_week/2))
            res2 = self.farms.stake(locked_amount).interpret(storage=res.storage, sender=alice, now=int(2 * sec_week + sec_week/2))

            self.assertEqual(res.storage["total_reward"], 30000000)
            self.assertEqual(res.storage["weeks"], 3)
            
            self.assertEqual(admin, res.storage["admin"])
            transfer_tx = res2.operations[0]
            transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
            self.assertEqual(alice, transfer_tx_params[0]['string'])

            self.assertEqual(farm_address, transfer_tx_params[1]['string'])
            self.assertEqual(locked_amount, int(transfer_tx_params[2]['int']))

            user_stakes = res2.storage["user_stakes"]
            self.assertEqual(locked_amount, user_stakes[alice])
            self.assertEqual(1, len(user_stakes.keys()))

            farm_points = res2.storage["farm_points"]
            
            self.assertEqual(sec_week/2 * 10000, farm_points[3])

            user_points = res2.storage["user_points"]
            user_points_keys = user_points.keys()
            self.assertEqual(1, len(user_points_keys))
            self.assertEqual(alice, list(user_points_keys)[0])
            
            self.assertEqual(sec_week/2 * 10000, user_points[alice][3])


    #####################
    # Tests for Unstake #
    #####################

    def test_unstake_basic_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: int((500+250) * sec_week/2),
                3: 250 * sec_week,
                4: 250 * sec_week,
                5: 250 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: int((500+250) * sec_week/2),
            3: 250 * sec_week,
            4: 250 * sec_week,
            5: 250 * sec_week
        }
        res = self.farms.unstake(250).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week/2))
        self.assertDictEqual(res.storage["user_points"], final_userpoint)
        self.assertDictEqual(res.storage["farm_points"], final_farmpoint)
        self.assertEqual(res.storage["user_stakes"][alice], 250)


    def test_unstake_same_week_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2) - int(499 * sec_week/4),
                2: sec_week,
                3: sec_week,
                4: sec_week,
                5: sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week/2) - int(499 * sec_week/4),
            2: sec_week,
            3: sec_week,
            4: sec_week,
            5: sec_week
        }
        res = self.farms.unstake(499).interpret(sender=alice, storage=init_storage, now=int(sec_week*3/4))
        self.assertDictEqual(res.storage["user_points"], final_userpoint)
        self.assertDictEqual(res.storage["farm_points"], final_farmpoint)
        self.assertEqual(res.storage["user_stakes"][alice], 1)


    def test_unstake_total_stake_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week/2),
                3: 0,
                4: 0,
                5: 0
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week / 2),
            3: 0,
            4: 0,
            5: 0
        }
        res = self.farms.unstake(500).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week/2))
        self.assertDictEqual(res.storage["user_points"], final_userpoint)
        self.assertDictEqual(res.storage["farm_points"], final_farmpoint)
        self.assertEqual(res.storage["user_stakes"][alice], 0)

    def test_unstake_more_than_staked_should_fail(self):

        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: int((500+250) * sec_week/2),
                3: 250 * sec_week,
                4: 250 * sec_week,
                5: 250 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: int((500+250) * sec_week/2),
            3: 250 * sec_week,
            4: 250 * sec_week,
            5: 250 * sec_week
        }

        with self.raisesMichelsonError(unstake_more_than_stake):
            self.farms.unstake(501).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week / 2))


    def test_unstake_with_0_staked_should_fail(self):

        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        with self.raisesMichelsonError(no_stakes):
            self.farms.unstake(10).interpret(storage=init_storage, sender=bob)

    def test_unstake_with_two_users_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"][bob] = 600
        init_storage["user_points"] = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: 600 * sec_week,
                5: 600 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: 600 * sec_week + 500 * sec_week,
            5: 600 * sec_week + 500 * sec_week
        }

        final_userpoint = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: int((600 * (6 / 7) + 500 / 7) * sec_week),
                5: 500 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: int(500 * sec_week + (600 * (6 / 7) + 500 / 7) * sec_week),
            5: 500 * sec_week + 500 * sec_week
        }
        res2 = self.farms.unstake(100).interpret(storage=init_storage, sender=bob, now=int(3 * sec_week + sec_week * 6 / 7))
        self.assertDictEqual(res2.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res2.storage["user_points"], final_userpoint)
        self.assertEqual(res2.storage["user_stakes"][bob], 500)

    def test_unstake_should_work_after_pool_end(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }
        res = self.farms.unstake(250).interpret(sender=alice, storage=init_storage, now=sec_week * 1000)
        self.assertDictEqual(res.storage["user_points"], final_userpoint)
        self.assertDictEqual(res.storage["farm_points"], final_farmpoint)
        self.assertEqual(res.storage["user_stakes"][alice], 250)

    def test_unstake_all_with_two_users_at_the_pool_end_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"][bob] = 600
        init_storage["user_stakes"][alice] = 500
        init_storage["user_points"] = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: 600 * sec_week,
                5: 600 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: 600 * sec_week + 500 * sec_week,
            5: 600 * sec_week + 500 * sec_week
        }

        final_userpoint = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: 600 * sec_week,
                5: 600 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: 600 * sec_week + 500 * sec_week,
            5: 600 * sec_week + 500 * sec_week,
        }
        res2 = self.farms.unstake(600).interpret(storage=init_storage, sender=bob, now=int(30 * sec_week + sec_week * 6 / 7))
        self.assertDictEqual(res2.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res2.storage["user_points"], final_userpoint)
        self.assertEqual(res2.storage["user_stakes"][bob], 0)


    def test_unstake_after_staking_two_times_in_a_row_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        second_storage = deepcopy(init_storage)
        second_storage["user_stakes"] = {alice: 1000}
        second_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
                3: 1000 * sec_week,
                4: 1000 * sec_week,
                5: 1000 * sec_week
            }
        }
        second_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
            3: 1000 * sec_week,
            4: 1000 * sec_week,
            5: 1000 * sec_week
        }


        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
                3: 0,
                4: 0,
                5: 0
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
            3: 0,
            4: 0,
            5: 0
        }

        res2 = self.farms.stake(500).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week/2))
        self.assertEqual(res2.storage["user_stakes"][alice], 1000)
        self.assertDictEqual(res2.storage["farm_points"], second_storage["farm_points"])
        self.assertDictEqual(res2.storage["user_points"], second_storage["user_points"])
        res3 = self.farms.unstake(1000).interpret(sender=alice, storage=second_storage, now=int(sec_week + sec_week*2/3))
        self.assertEqual(res3.storage["user_stakes"][alice], 0)
        self.assertDictEqual(res3.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res3.storage["user_points"], final_userpoint)



    def test_unstake_everything_with_two_users_at_the_pool_end_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"][bob] = 600
        init_storage["user_stakes"][alice] = 500
        init_storage["user_points"] = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: 600 * sec_week,
                5: 600 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: 600 * sec_week + 500 * sec_week,
            5: 600 * sec_week + 500 * sec_week
        }

        final_userpoint = {
            bob: {
                1: 0,
                2: 0,
                3: int(600 * sec_week / 3),
                4: 600 * sec_week,
                5: 600 * sec_week
            },
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: int(600 * sec_week / 3) + 500 * sec_week,
            4: 600 * sec_week + 500 * sec_week,
            5: 600 * sec_week + 500 * sec_week,
        }
        res2 = self.farms.unstake(600).interpret(storage=init_storage, sender=bob, now=int(30 * sec_week + sec_week * 6 / 7))
        self.assertDictEqual(res2.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res2.storage["user_points"], final_userpoint)
        self.assertEqual(res2.storage["user_stakes"][bob], 0)


        res3 = self.farms.unstake(500).interpret(storage=init_storage, sender=alice, now=int(30 * sec_week + sec_week * 6 / 7))
        self.assertDictEqual(res3.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res3.storage["user_points"], final_userpoint)
        self.assertEqual(res3.storage["user_stakes"][alice], 0)


    def test_unstake_after_increasing_reward_should_work(self):
            init_storage = deepcopy(initial_storage)
            init_storage["total_reward"] = 10_000_000
            init_storage["weeks"] = 3
            init_storage["rate"] = 7500
            init_storage["reward_at_week"] = {
                1: 4324324,
                2: 3243243,
                3: 2432432,
            }
            locked_amount = 10000
            res = self.farms.increaseReward(20_000_000).interpret(storage=init_storage, sender=admin, now=int(sec_week + sec_week/2))
            res2 = self.farms.stake(locked_amount).interpret(storage=res.storage, sender=alice, now=int(2 * sec_week + sec_week/2))

            self.assertEqual(res.storage["total_reward"], 30000000)
            self.assertEqual(res.storage["weeks"], 3)
            
            self.assertEqual(admin, res.storage["admin"])
            transfer_tx = res2.operations[0]
            transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
            self.assertEqual(alice, transfer_tx_params[0]['string'])

            self.assertEqual(farm_address, transfer_tx_params[1]['string'])
            self.assertEqual(locked_amount, int(transfer_tx_params[2]['int']))

            user_stakes = res2.storage["user_stakes"]
            self.assertEqual(locked_amount, user_stakes[alice])
            self.assertEqual(1, len(user_stakes.keys()))

            farm_points = res2.storage["farm_points"]
            
            self.assertEqual(sec_week/2 * locked_amount, farm_points[3])

            user_points = res2.storage["user_points"]
            user_points_keys = user_points.keys()
            self.assertEqual(1, len(user_points_keys))
            self.assertEqual(alice, list(user_points_keys)[0])
            
            self.assertEqual(sec_week/2 * locked_amount, user_points[alice][3])

            res3 = self.farms.unstake(locked_amount).interpret(sender=alice, storage=res2.storage, now=int(2 * sec_week + sec_week*2/3))
            transfer_txs = res3.operations
            self.assertEqual(1, len(transfer_txs))

            self.assertEqual('transaction', transfer_txs[0]["kind"])
 


            transfer_tx_params = transfer_tx["parameters"]["value"]['args'][0]['args'][0]['args']
            self.assertEqual(alice, transfer_tx_params[0]['string'])

            self.assertEqual('KT1BEqzn5Wx8uJrZNvuS9DVHmLvG9td3fDLi', transfer_tx_params[1]['string'])
            self.assertEqual(locked_amount, int(transfer_tx_params[2]['int']))


    def test_unstake_after_staking_two_times_in_a_row_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        second_storage = deepcopy(init_storage)
        second_storage["user_stakes"] = {alice: 1000}
        second_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
                3: 1000 * sec_week,
                4: 1000 * sec_week,
                5: 1000 * sec_week
            }
        }
        second_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
            3: 1000 * sec_week,
            4: 1000 * sec_week,
            5: 1000 * sec_week
        }


        final_userpoint = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
                3: 0,
                4: 0,
                5: 0
            }
        }

        final_farmpoint = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
            3: 0,
            4: 0,
            5: 0
        }

        res2 = self.farms.stake(500).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week/2))
        self.assertEqual(res2.storage["user_stakes"][alice], 1000)
        self.assertDictEqual(res2.storage["farm_points"], second_storage["farm_points"])
        self.assertDictEqual(res2.storage["user_points"], second_storage["user_points"])
        res3 = self.farms.unstake(1000).interpret(sender=alice, storage=second_storage, now=int(sec_week + sec_week*2/3))
        self.assertEqual(res3.storage["user_stakes"][alice], 0)
        self.assertDictEqual(res3.storage["farm_points"], final_farmpoint)
        self.assertDictEqual(res3.storage["user_points"], final_userpoint)


    ######################
    # Tests for ClaimAll #
    ######################

    def test_claimall_basic_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=int(sec_week + sec_week/2))

        self.assertEqual(admin, res.storage["admin"])
        transfer_txs = res.operations

        self.assertEqual(1, len(transfer_txs))
        self.assertEqual('transaction', transfer_txs[0]["kind"])
        transfer_tx_params = transfer_txs[0]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_params[0]['string'])
        self.assertEqual(alice, transfer_tx_params[1]['string'])
        self.assertEqual(str(init_storage["reward_at_week"][1]), transfer_tx_params[2]['int'])

        alice_points = res.storage["user_points"][alice]
        self.assertEqual(alice_points[1], 0)
        self.assertEqual(alice_points[2], 500 * sec_week)
        self.assertEqual(alice_points[3], 500 * sec_week)
        self.assertEqual(alice_points[4], 500 * sec_week)
        self.assertEqual(alice_points[5], 500 * sec_week)


    def test_claimall_with_0_points_should_fail(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        with self.raisesMichelsonError(unknown_user_claim):
            self.farms.claimAll().interpret(storage=init_storage, sender=bob, now=int(sec_week * 7 + sec_week/2))

    def test_claimall_3rd_week_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=int(sec_week * 2 + sec_week/2))

        self.assertEqual(admin, res.storage["admin"])
        transfer_txs = res.operations
        
        self.assertEqual(2, len(transfer_txs))

        self.assertEqual('transaction', transfer_txs[1]["kind"])
        transfer_tx_2_params = transfer_txs[1]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_2_params[0]['string'])
        self.assertEqual(alice, transfer_tx_2_params[1]['string'])
        self.assertEqual(str(init_storage["reward_at_week"][1]), transfer_tx_2_params[2]['int'])

        self.assertEqual('transaction', transfer_txs[0]["kind"])
        transfer_tx_1_params = transfer_txs[0]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_1_params[0]['string'])
        self.assertEqual(alice, transfer_tx_1_params[1]['string'])
        self.assertEqual(str(init_storage["reward_at_week"][2]), transfer_tx_1_params[2]['int'])

        alice_points = res.storage["user_points"][alice]
        self.assertEqual(alice_points[1], 0)
        self.assertEqual(alice_points[2], 0)
        self.assertEqual(alice_points[3], 500 * sec_week)
        self.assertEqual(alice_points[4], 500 * sec_week)
        self.assertEqual(alice_points[5], 500 * sec_week)



    def test_claimall_with_2_stakers_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500,
            bob: 100
        }
        init_storage["user_points"] = {
            alice: {
                1: 0,
                2: int(500 * sec_week * (1 - 2/3)),
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            },
            bob : {
                1: 0,
                2: int(100 * sec_week * (1 - 1/2)),
                3: 100 * sec_week,
                4: 100 * sec_week,
                5: 100 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: 0,
            2: int(500 * sec_week * (1 - 2/3) + 100 * sec_week * (1 - 1/2)),
            3: (500 + 100) * sec_week,
            4: (500 + 100) * sec_week,
            5: (500 + 100) * sec_week
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=int(sec_week * 3 + sec_week / 2))

        self.assertEqual(admin, res.storage["admin"])
        transfer_txs = res.operations
        self.assertEqual(2, len(transfer_txs))

        self.assertEqual('transaction', transfer_txs[0]["kind"]) # week 3
        transfer_tx_3_params = transfer_txs[0]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_3_params[0]['string'])
        self.assertEqual(alice, transfer_tx_3_params[1]['string'])
        expected_value_3 = int(init_storage["reward_at_week"][3] *  init_storage["user_points"][alice][3] / init_storage["farm_points"][3])
        self.assertEqual(str(expected_value_3), transfer_tx_3_params[2]['int'])

        self.assertEqual('transaction', transfer_txs[1]["kind"]) # week 2
        transfer_tx_2_params = transfer_txs[1]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_2_params[0]['string'])
        self.assertEqual(alice, transfer_tx_2_params[1]['string'])
        expected_value_2 = int(init_storage["reward_at_week"][2] * (500 * sec_week * 1/3) / init_storage["farm_points"][2])
        self.assertEqual(str(expected_value_2), transfer_tx_2_params[2]['int'])

        alice_points = res.storage["user_points"][alice]
        self.assertEqual(alice_points[1], 0)
        self.assertEqual(alice_points[2], 0)
        self.assertEqual(alice_points[3], 0)
        self.assertEqual(alice_points[4], 500 * sec_week)
        self.assertEqual(alice_points[5], 500 * sec_week)

    def test_claimall_with_2_stakers_not_staking_middle_week_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500,
            bob: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: 500 * sec_week,
                2: 0,
                3: int(500 * sec_week * (1 - 2/3)),
                4: 500 * sec_week,
                5: 500 * sec_week
            },
            bob : {
                1: 500 * sec_week,
                2: 0,
                3: int(100 * sec_week * (1 - 1/2)),
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: (500 + 500) * sec_week,
            2: 0,
            3: int(500 * sec_week * (1 - 2/3) + 100 * sec_week * (1 - 1/2)),
            4: (500 + 500) * sec_week,
            5: (500 + 500) * sec_week
        }

        reward_sent = {
            1: int(6555697/2),
            3: int((int(500 * sec_week * (1 - 2/3)) / int(500 * sec_week * (1 - 2/3) + 100 * sec_week * (1 - 1/2)) )* 3687580) - 1
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=int(sec_week * 3 + sec_week / 2))
        transfer_txs = res.operations
        self.assertEqual(2, len(transfer_txs))
        for tx, week in zip(transfer_txs, list(reward_sent.keys())[::-2]):
            self.assertEqual('transaction', tx["kind"])
            transfer_tx_params = tx["parameters"]["value"]['args']
            self.assertEqual(initial_storage["reserve_address"], transfer_tx_params[0]['string'])
            self.assertEqual(alice, transfer_tx_params[1]['string'])
            self.assertEqual(str(int(reward_sent[week])), transfer_tx_params[2]['int'])

    def test_claimall_with_2_stakers_not_staking_last_week_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500,
            bob: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: 500 * sec_week,
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 0
            },
            bob : {
                1: 500 * sec_week,
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 0
            }
        }
        init_storage["farm_points"] = {
            1: (500 + 500) * sec_week,
            2: (500 + 500) * sec_week,
            3: (500 + 500) * sec_week,
            4: (500 + 500) * sec_week,
            5: 0,
        }

        reward_sent = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=int(sec_week * 6 + sec_week / 2))
        transfer_txs = res.operations
        self.assertEqual(4, len(transfer_txs))
        for tx, week in zip(transfer_txs, list(reward_sent.keys())[::-1]):
            self.assertEqual('transaction', tx["kind"])
            transfer_tx_params = tx["parameters"]["value"]['args']
            self.assertEqual(initial_storage["reserve_address"], transfer_tx_params[0]['string'])
            self.assertEqual(alice, transfer_tx_params[1]['string'])
            self.assertEqual(str(int(reward_sent[week]/2)), transfer_tx_params[2]['int'])

    def test_claimall_after_pool_end_should_work(self):

        init_storage = deepcopy(initial_storage)
        init_storage["total_reward"] = 20_000_000
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["creation_time"] = 0
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week / 2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        res = self.farms.claimAll().interpret(storage=init_storage, sender=alice, now=sec_week * 100)

        self.assertEqual(admin, res.storage["admin"])
        transfer_txs = res.operations

        self.assertEqual(5, len(transfer_txs))

        for tx, week in zip(transfer_txs, list(init_storage["reward_at_week"].keys())[::-1]):
            self.assertEqual('transaction', tx["kind"])
            transfer_tx_params = tx["parameters"]["value"]['args']
            self.assertEqual(initial_storage["reserve_address"], transfer_tx_params[0]['string'])
            self.assertEqual(alice, transfer_tx_params[1]['string'])
            self.assertEqual(str(init_storage["reward_at_week"][week]), transfer_tx_params[2]['int'])

        alice_points = res.storage["user_points"][alice]
        self.assertEqual(alice_points[1], 0)
        self.assertEqual(alice_points[2], 0)
        self.assertEqual(alice_points[3], 0)
        self.assertEqual(alice_points[4], 0)
        self.assertEqual(alice_points[5], 0)

    def test_claimall_with_XTZ_should_fail(self):
        init_storage = deepcopy(initial_storage)
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        with self.raisesMichelsonError(amount_must_be_zero_tez):
            self.farms.claimAll().interpret(storage=init_storage, sender=bob, now=sec_week * 12, amount=1)


    def test_claimall_two_times_after_unstake_and_staking_two_times_should_work(self):
        init_storage = deepcopy(initial_storage)
        init_storage["reward_at_week"] = {
            1: 6555697,
            2: 4916773,
            3: 3687580,
            4: 2765685,
            5: 2074263
        }
        init_storage["user_stakes"] = {
            alice: 500
        }
        init_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: 500 * sec_week,
                3: 500 * sec_week,
                4: 500 * sec_week,
                5: 500 * sec_week
            }
        }
        init_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: 500 * sec_week,
            3: 500 * sec_week,
            4: 500 * sec_week,
            5: 500 * sec_week
        }

        second_storage = deepcopy(init_storage)
        second_storage["user_stakes"] = {alice: 1000}
        second_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
                3: 1000 * sec_week,
                4: 1000 * sec_week,
                5: 1000 * sec_week
            }
        }
        second_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ),
            3: 1000 * sec_week,
            4: 1000 * sec_week,
            5: 1000 * sec_week
        }

        third_storage = deepcopy(second_storage)
        third_storage["user_stakes"] = {alice: 0}
        third_storage["user_points"] = {
            alice: {
                1: int(500 * sec_week/2),
                2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
                3: 0,
                4: 0,
                5: 0
            }
        }
        third_storage["farm_points"] = {
            1: int(500 * sec_week / 2),
            2: int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ),
            3: 0,
            4: 0,
            5: 0
        }

        self.farms.stake(500).interpret(sender=alice, storage=init_storage, now=int(sec_week + sec_week/2))
        self.farms.unstake(1000).interpret(sender=alice, storage=second_storage, now=int(sec_week + sec_week*2/3))
        res4 = self.farms.claimAll().interpret(sender=alice, storage=third_storage, now=int(sec_week + sec_week*3/4))

        self.assertEqual(admin, res4.storage["admin"])
        transfer_txs = res4.operations
        self.assertEqual(1, len(transfer_txs))

        self.assertEqual('transaction', transfer_txs[0]["kind"])
        transfer_tx_params = transfer_txs[0]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_params[0]['string'])
        self.assertEqual(alice, transfer_tx_params[1]['string'])
        self.assertEqual(str(int(res4.storage["reward_at_week"][1])), transfer_tx_params[2]['int'])

        self.assertEqual(res4.storage["user_points"][alice][1], 0)
        self.assertEqual(res4.storage["user_points"][alice][2], int(500 * sec_week) +  int(500 * sec_week / 2 ) - int(1000 * sec_week / 3 ))
        self.assertEqual(res4.storage["user_points"][alice][3], 0)
        self.assertEqual(res4.storage["user_points"][alice][4], 0)
        self.assertEqual(res4.storage["user_points"][alice][5], 0)

        res5 = self.farms.claimAll().interpret(sender=alice, storage=res4.storage, now=int(sec_week * 2 + sec_week*3/4))
        transfer_txs2 = res5.operations
        self.assertEqual(1, len(transfer_txs2))

        self.assertEqual('transaction', transfer_txs2[0]["kind"])
        transfer_tx_params2 = transfer_txs2[0]["parameters"]["value"]['args']
        self.assertEqual(initial_storage["reserve_address"], transfer_tx_params2[0]['string'])
        self.assertEqual(alice, transfer_tx_params2[1]['string'])
        self.assertEqual(str(int(res5.storage["reward_at_week"][2])), transfer_tx_params2[2]['int'])