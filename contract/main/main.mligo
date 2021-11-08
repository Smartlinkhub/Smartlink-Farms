#include "../partials/FarmMethods.mligo"

let main (action, s : entrypoint * storage_farm) : return =
    match action with
    | SetAdmin(admin) -> setAdmin(admin, s)
    | Stake(value) -> stakeSome(value, s)
    | Unstake(value) -> unstakeSome(value, s)
    | ClaimAll() -> claimAll(s)
    | IncreaseReward(value) -> increaseReward(value, s)