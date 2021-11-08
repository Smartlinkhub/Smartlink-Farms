#include "Error.mligo"
#include "FarmTypes.mligo"
#include "../main/fa12.mligo"

// Should update the admin
// Params : admin (address) 
let setAdmin(admin, s : address * storage_farm) : return =
    let _check_if_no_tez : bool = if Tezos.amount = 0tez then true else (failwith(amount_must_be_zero_tez) : bool) in
    let new_admin = if Tezos.sender = s.admin then admin
    else (failwith(only_admin) : address) in 
    (noOperations, { s with admin = new_admin })

let get_current_week(s : storage_farm) : nat = 
    let delay : nat = abs(Tezos.now - s.creation_time) in
    delay / week_in_seconds + 1n

let get_weeks_indices(first, last : nat * nat) : nat list =
    let rec append ( acc, elt, last: nat list * nat * nat) : nat list = if elt <= last then append (elt :: acc, elt + 1n, last) else acc in
    append(([]:nat list), first, last)

    
let get_weeks_indices_as_set(first, last : nat * nat) : nat set =
    let rec append ( acc, elt, last: nat set * nat * nat) : nat set = if elt <= last then append (Set.add elt acc, elt + 1n, last) else acc in
    append((Set.empty : nat set), first, last)


let stakeSome(lp_amount, s : nat * storage_farm) : return =
    let _check_if_no_tez : bool = if Tezos.amount = 0tez then true else (failwith(amount_must_be_zero_tez) : bool) in
    let _check_amount_positive : bool = 
        if (lp_amount > 0n) 
        then true 
        else (failwith(amount_is_null) : bool)
    in 
    let _check_current_week : bool = 
        if (Tezos.now < s.creation_time + int(s.weeks * week_in_seconds))
        then true
        else (failwith(no_week_left) : bool)
    in
    let lp_contract_opt : parameter contract option = Tezos.get_contract_opt(s.lp_token_address) in
    let lp_contract : parameter contract = match lp_contract_opt with
        | None -> (failwith(unknown_lp_contract) : parameter contract)
        | Some(x) -> x
    in
    // create a transfer transaction (for LP token contract)
    let transfer_param : transfer = { address_from = Tezos.sender; address_to = Tezos.self_address; value = lp_amount } in 
    let op : operation = Tezos.transaction (Transfer(transfer_param)) 0mutez lp_contract in
    let ops : operation list = [ op; ] in
    // update current storage with updated user_stakes map
    let existing_bal_opt : nat option = Big_map.find_opt Tezos.sender s.user_stakes in
    let new_user_stakes : (address, nat) big_map = match existing_bal_opt with
        | None -> Big_map.add Tezos.sender lp_amount s.user_stakes
        | Some(v) -> Big_map.update Tezos.sender (Some(lp_amount + v)) s.user_stakes
    in
    let current_week : nat = get_current_week(s) in
    let endofweek_in_seconds : timestamp = s.creation_time + int(current_week * week_in_seconds) in
    
    //assert_some (Tezos.now - endofweek_in_seconds < 0)
    let _check_negative : bool = 
        if (Tezos.now - endofweek_in_seconds < 0) 
        then true 
        else (failwith(time_too_early) : bool)
    in
    let before_end_week : nat = abs(Tezos.now - endofweek_in_seconds) in 
    let points_current_week : nat = before_end_week * lp_amount in
    let points_next_weeks : nat = week_in_seconds * lp_amount in
    
    //user_points[user_address][current_week] += before_end_week * lp_amount
    let user_weeks_opt : (nat, nat) map option = Big_map.find_opt Tezos.sender s.user_points in
    let new_user_points : (address, (nat, nat) map ) big_map = match user_weeks_opt with
    | None -> Big_map.add Tezos.sender (Map.literal [(current_week, points_current_week)] : (nat, nat) map) s.user_points
    | Some(m) -> 
        let modified_current_week : (nat, nat) map = match (Map.find_opt current_week m) with
        | None -> (Map.literal [(current_week, points_current_week)] : (nat, nat) map)
        | Some(wpts) -> (Map.update current_week (Some(points_current_week + wpts)) m)
        in
        Big_map.update Tezos.sender (Some(modified_current_week)) s.user_points
    in 
    //farm_points[current_week] += before_end_week * lp_amount
    let new_farm_points = match Map.find_opt current_week s.farm_points with
    | None -> Map.add current_week points_current_week s.farm_points
    | Some(val_) -> Map.update current_week (Some(val_ + points_current_week)) s.farm_points
    in
    //for (i = current_week + 1; i <= s.weeks; i++) 
    //    user_points[user_address][i] += week_in_seconds * lp_amount
    let future_weeks : nat list = get_weeks_indices(current_week + 1n, s.weeks) in
    let update_user_points_func = fun (a, v, i, m : address * nat * nat * (address, (nat, nat) map ) big_map) -> 
        match Big_map.find_opt a m with
        | None -> Big_map.add Tezos.sender (Map.literal [(i, v)] : (nat, nat) map) m
        | Some(weeks_map) ->
            let new_weeks_map : (nat, nat) map = match Map.find_opt i weeks_map with
            | None -> Map.add i v weeks_map
            | Some(value) -> Map.update i (Some(value +v)) weeks_map
            in
            Big_map.update a (Some(new_weeks_map)) m
    in
    let rec modify_user_points_func(resulting_acc, modificateur, weeks_indices : (address, (nat, nat) map ) big_map * nat * nat list) : (address, (nat, nat) map ) big_map =
        let week_indice_opt : nat option = List.head_opt weeks_indices in
        match week_indice_opt with
        | None -> resulting_acc
        | Some(week_indice) -> 
            let modified : (address, (nat, nat) map ) big_map = update_user_points_func(Tezos.sender, modificateur, week_indice, resulting_acc) in
            let remaining_weeks_opt : nat list option = List.tail_opt weeks_indices in
            let remaining_weeks : nat list = match remaining_weeks_opt with
            | None -> ([] : nat list)
            | Some(l) -> l
            in
            modify_user_points_func(modified, modificateur, remaining_weeks)
    in
    let final_user_points : (address, (nat, nat) map ) big_map  = modify_user_points_func(new_user_points, points_next_weeks, future_weeks)
    in

    //for (i = current_week + 1; i <= s.weeks; i++) 
    //    farm_points[i] += week_in_seconds * lp_amount 
    let update_farm_points_func = fun (v, i, m : nat * nat * (nat, nat) map) ->
        match (Map.find_opt i m) with
        | None -> Map.add i v m
        | Some(entry) -> Map.update i (Some(entry+v)) m
    in
    let rec modify_farm_points_func(farm_result, delta, weeks_indices : (nat, nat) map * nat * nat list) : (nat, nat) map =
        let week_indice_opt : nat option = List.head_opt weeks_indices in
        match week_indice_opt with
        | None -> farm_result
        | Some(week_indice) -> 
            let modified : (nat, nat) map = update_farm_points_func(delta, week_indice, farm_result) in
            let remaining_weeks_opt : nat list option = List.tail_opt weeks_indices in
            let remaining_weeks : nat list = match remaining_weeks_opt with
            | None -> ([] : nat list)
            | Some(l) -> l
            in
            modify_farm_points_func(modified, delta, remaining_weeks)
    in
    let final_farm_points : (nat, nat) map = modify_farm_points_func(new_farm_points, points_next_weeks, future_weeks) in

    (ops, { s with user_stakes = new_user_stakes; user_points = final_user_points; farm_points = final_farm_points } )


let unstakeSome(lp_amount, s : nat * storage_farm) : return =
    let _check_if_no_tez : bool = if Tezos.amount = 0tez then true else (failwith(amount_must_be_zero_tez) : bool) in
    // update current storage with updated user_stakes map
    let existing_bal_opt : nat option = Big_map.find_opt Tezos.sender s.user_stakes in
    let new_user_stakes : (address, nat) big_map = match existing_bal_opt with
        | None -> (failwith(no_stakes): (address, nat) big_map)
        | Some(v) -> if (v >= lp_amount) 
        then Big_map.update Tezos.sender (Some(abs(v - lp_amount))) s.user_stakes
        else (failwith(unstake_more_than_stake): (address, nat) big_map)
    in
    let lp_contract_opt : parameter contract option = Tezos.get_contract_opt(s.lp_token_address) in
    let lp_contract : parameter contract = match lp_contract_opt with
        | None -> (failwith(unknown_lp_contract) : parameter contract)
        | Some(x) -> x
    in
    // create a transfer transaction (for LP token contract)
    let transfer_param : transfer = { address_from = Tezos.self_address; address_to = Tezos.sender; value = lp_amount } in 
    let op : operation = Tezos.transaction (Transfer(transfer_param)) 0mutez lp_contract in
    let ops : operation list = [ op; ] in
    if ((Tezos.now - s.creation_time - (s.weeks *  week_in_seconds)) < 0 ) then  
        let current_week : nat = get_current_week(s) in
        let endofweek_in_seconds : timestamp = s.creation_time + int(current_week * week_in_seconds) in
        

        //assert_some (Tezos.now - endofweek_in_seconds < 0)
        let _check_negative : bool = 
            if (Tezos.now - endofweek_in_seconds < 0) 
            then true 
            else (failwith(time_too_early) : bool)
        in
        let before_end_week : nat = abs(Tezos.now - endofweek_in_seconds) in 
        let points_current_week : nat = before_end_week * lp_amount in
        let points_next_weeks : nat = week_in_seconds * lp_amount in
        
        //user_points[user_address][current_week] += before_end_week * lp_amount
        let user_weeks_opt : (nat, nat) map option = Big_map.find_opt Tezos.sender s.user_points in
        let new_user_points : (address, (nat, nat) map ) big_map = match user_weeks_opt with
        | None -> (failwith(user_no_points): (address, (nat, nat) map ) big_map)
        | Some(m) -> 
            let modified_current_week : (nat, nat) map = match (Map.find_opt current_week m) with
            | None -> (failwith(user_no_points):  (nat, nat) map)
            | Some(wpts) -> (Map.update current_week (Some(abs(wpts - points_current_week))) m)
            in
            Big_map.update Tezos.sender (Some(modified_current_week)) s.user_points
        in 
        //farm_points[current_week] += before_end_week * lp_amount
        let new_farm_points = match Map.find_opt current_week s.farm_points with
        | None -> (failwith(user_no_points):  (nat, nat) map)
        | Some(val_) -> Map.update current_week (Some(abs(val_ - points_current_week))) s.farm_points
        in
        //for (i = current_week + 1; i <= s.weeks; i++) 
        //    user_points[user_address][i] += week_in_seconds * lp_amount
        let future_weeks : nat list = get_weeks_indices(current_week + 1n, s.weeks) in
        let update_user_points_func = fun (a, v, i, m : address * nat * nat * (address, (nat, nat) map ) big_map) -> 
            match Big_map.find_opt a m with
            | None -> (failwith(unknown_user_unstake):  (address, (nat , nat) map)big_map)
            | Some(weeks_map) ->
                let new_weeks_map : (nat, nat) map = match Map.find_opt i weeks_map with
                | None -> (failwith(unknown_user_unstake): (nat , nat) map)
                | Some(value) -> Map.update i (Some(abs(value - v))) weeks_map
                in
                Big_map.update a (Some(new_weeks_map)) m
        in
        let rec modify_user_points_func(resulting_acc, modificateur, weeks_indices : (address, (nat, nat) map ) big_map * nat * nat list) : (address, (nat, nat) map ) big_map =
            let week_indice_opt : nat option = List.head_opt weeks_indices in
            match week_indice_opt with
            | None -> resulting_acc
            | Some(week_indice) -> 
                let modified : (address, (nat, nat) map ) big_map = update_user_points_func(Tezos.sender, modificateur, week_indice, resulting_acc) in
                let remaining_weeks_opt : nat list option = List.tail_opt weeks_indices in
                let remaining_weeks : nat list = match remaining_weeks_opt with
                | None -> ([] : nat list)        
                | Some(l) -> l
                in
                modify_user_points_func(modified, modificateur, remaining_weeks)
        in
        let final_user_points : (address, (nat, nat) map ) big_map  = modify_user_points_func(new_user_points, points_next_weeks, future_weeks)
        in

        //for (i = current_week + 1; i <= s.weeks; i++) 
        //    farm_points[i] += week_in_seconds * lp_amount 
        let update_farm_points_func = fun (v, i, m : nat * nat * (nat, nat) map) ->
            match (Map.find_opt i m) with
            | None -> (failwith(user_no_points):  (nat, nat) map)
            | Some(entry) -> Map.update i (Some(abs(entry-v))) m
        in
        let rec modify_farm_points_func(farm_result, delta, weeks_indices : (nat, nat) map * nat * nat list) : (nat, nat) map =
            let week_indice_opt : nat option = List.head_opt weeks_indices in
            match week_indice_opt with
            | None -> farm_result
            | Some(week_indice) -> 
                let modified : (nat, nat) map = update_farm_points_func(delta, week_indice, farm_result) in
                let remaining_weeks_opt : nat list option = List.tail_opt weeks_indices in
                let remaining_weeks : nat list = match remaining_weeks_opt with
                | None -> ([] : nat list)
                | Some(l) -> l
                in
                modify_farm_points_func(modified, delta, remaining_weeks)
        in
        let final_farm_points : (nat, nat) map = modify_farm_points_func(new_farm_points, points_next_weeks, future_weeks) in 
        (ops, { s with user_stakes = new_user_stakes; user_points = final_user_points; farm_points = final_farm_points } )
    else
        (ops, { s with user_stakes = new_user_stakes} )


    let sendReward(token_amount, user_address, s : nat * address * storage_farm) : operation = 
        let smak_contract_otp : smak_transfer contract option = Tezos.get_entrypoint_opt "%transfer" s.smak_address in
        let transfer_smak : smak_transfer contract = match smak_contract_otp with
            | Some c -> c
            | None -> (failwith unknown_smak_contract:  smak_transfer contract)
        in
        // create a transfer transaction (for LP token contract)
        let transfer_param : smak_transfer = s.reserve_address,  (user_address , token_amount ) in 
        let op : operation = Tezos.transaction (transfer_param) 0mutez transfer_smak in
        op

    let power(x, y: nat * nat) : nat = 
        let rec multiply(acc, elt, last: nat * nat * nat ) : nat = if last = 0n then acc else multiply(acc * elt, elt, abs(last - 1n)) in
        multiply(1n, x, y)

    let computeReward(offset, s : nat * storage_farm) : storage_farm =
        let weeks : nat list = get_weeks_indices(1n, s.weeks) in
        let update_reward_per_week_func(week_indice, rate, weeks_max, reward_total, map_accumulator : nat * nat * nat * nat * (nat, nat) map): (nat, nat) map =
            let t_before : nat = power(rate, abs(week_indice - 1n)) in  
            let t_before_divisor : nat = power(10_000n, abs(week_indice - 1n)) in
            let un_moins_rate : nat = abs(10_000n - rate) in 
            let m_10000_4 : nat = power(10_000n, abs(weeks_max - 1n)) in
            let numerator : nat = un_moins_rate * m_10000_4 in 
            let t_I_max : nat = power(rate, weeks_max) in 
            let m_10000_5 : nat = power(10_000n, weeks_max) in
            let denominator : nat = abs(m_10000_5 - t_I_max) in
            let final_denominator : nat = t_before_divisor * denominator in 
            let final_numerator : nat = numerator * reward_total * t_before in 
            let result : nat =  final_numerator / final_denominator in 
            let value_opt : nat option = Map.find_opt (week_indice+offset) map_accumulator in
            let new_map : (nat, nat) map = match value_opt with
            | None -> Map.add (week_indice+offset) result map_accumulator
            | Some(_v) -> Map.update (week_indice+offset) (Some(result)) map_accumulator
            in
            new_map
        in
        let rec modify_rewards_func(resulting_acc, weeks_indices : (nat, nat) map * nat list) : (nat, nat) map =
            let week_indice_opt : nat option = List.head_opt weeks_indices in
            match week_indice_opt with
            | None -> resulting_acc
            | Some(week_indice) -> 
                let modified : (nat, nat) map = update_reward_per_week_func(week_indice, s.rate, s.weeks, s.total_reward, resulting_acc) in
                let remaining_weeks_opt : nat list option = List.tail_opt weeks_indices in
                let remaining_weeks : nat list = match remaining_weeks_opt with
                | None -> ([] : nat list)
                | Some(l) -> l
                in
                modify_rewards_func(modified, remaining_weeks)
        in
        let final_rewards : (nat, nat) map = modify_rewards_func(s.reward_at_week, weeks) in
        { s with reward_at_week = final_rewards }


    let increaseReward(value, s : nat * storage_farm) : return = 
        let _check_if_admin : bool = if Tezos.sender = s.admin then true else (failwith(only_admin) : bool) in
        let _check_if_no_tez : bool = if Tezos.amount = 0tez then true else (failwith(amount_must_be_zero_tez) : bool) in
        let current_week : nat = get_current_week(s) in
        let _check_current_week : bool = 
        if (Tezos.now < s.creation_time + int(s.weeks * week_in_seconds))
        then true
        else (failwith(no_week_left) : bool)
        in
        let delta : nat = value in
        //sum (current_week , s.weeks) reward_at_week
        let weeks_set : nat set = get_weeks_indices_as_set(current_week, s.weeks) in
        let initialized_creation_time: timestamp =
        if (delta = 0n)
        then Tezos.now 
        else s.creation_time
        in
        let folded (acc, elt: nat * (nat * nat) ) : nat = if Set.mem elt.0 weeks_set then acc  else acc + elt.1 in
        let sum_R : nat = Map.fold folded s.reward_at_week 0n in
        let new_r_total : nat = delta + abs(s.total_reward - sum_R) in
        let new_i_max : nat = abs(s.weeks - current_week + 1n) in
        let new_storage : storage_farm = { s with weeks = new_i_max; total_reward = new_r_total; creation_time = initialized_creation_time } in
        let new_reward_storage : storage_farm = computeReward(abs(current_week - 1n), new_storage) in
        let final_reward : nat = s.total_reward + value in
        let final_weeks : nat = s.weeks in
        (noOperations, { new_reward_storage with total_reward = final_reward; weeks = final_weeks })



   let claimAll(s : storage_farm) : return = 
        let _check_if_no_tez : bool = if Tezos.amount = 0tez then true else (failwith(amount_must_be_zero_tez) : bool) in
        let current_week : nat = get_current_week(s) in
        let precision : nat = 100_000_000n in
        let weeks : nat list =
            if (current_week > s.weeks) 
            then get_weeks_indices(1n, s.weeks) 
            else get_weeks_indices(1n, abs(current_week - 1n))
        in
        let compute_percentage_func(week_indice, map_accumulator : nat * (address, (nat, nat) map) map) : (address, (nat, nat) map) map =
            let points : nat = match (Big_map.find_opt Tezos.sender s.user_points) with
                | None -> (failwith(unknown_user_claim) : nat)
                | Some(week_points_map) -> 
                    let val_opt : nat option = Map.find_opt week_indice week_points_map in
                    let computed_value : nat = match val_opt with
                    | None -> 0n
                    | Some(v) -> v
                    in
                    computed_value
            in
            let farm_points : nat = match Big_map.find_opt week_indice s.farm_points with
            | None -> 0n
            | Some(val_) -> val_
            in
            if farm_points = 0n then map_accumulator else
            let perc : nat = if points = 0n then 0n else points * precision / farm_points in
            if perc = 0n then map_accumulator else
            match Map.find_opt Tezos.sender map_accumulator with
            | None ->
                let modified_wks : (nat, nat) map = Map.add week_indice perc (Map.empty : (nat, nat) map) in
                Map.add Tezos.sender modified_wks map_accumulator
            | Some(wks) ->  
                let modified_wks : (nat, nat) map = Map.add week_indice perc wks in
                Map.update Tezos.sender (Some(modified_wks)) map_accumulator
        in 
        let rec compute_func(acc, indices : (address, (nat, nat) map) map * nat list) : (address, (nat, nat) map) map = 
            let indice_opt : nat option = List.head_opt indices in
            match indice_opt with
            | None -> acc
            | Some(week_indice) -> 
                let modified_acc : (address, (nat, nat) map) map = compute_percentage_func(week_indice, acc) in
                let remaining_indices_opt : nat list option = List.tail_opt indices in
                let remaining_indices : nat list = match remaining_indices_opt with
                | None -> ([] : nat list)
                | Some(l) -> l
                in
                compute_func(modified_acc, remaining_indices)
        in
        let percentages : (address, (nat, nat) map) map = compute_func((Map.empty : (address, (nat, nat) map) map), weeks) in
        let compute_and_send_func(ops, i : operation list * (address * (nat, nat) map) ): operation list =
            let send_reward_func(acc, elt : operation list * (nat * nat)) : operation list =
                let (week_indice, percent) : nat * nat = elt in 
                let reward_for_week : nat = match Map.find_opt week_indice s.reward_at_week with
                | None -> 0n
                | Some(rwwk) -> rwwk
                in
                let amount_to_send : nat = reward_for_week * percent / precision in
                sendReward(amount_to_send, Tezos.sender, s) :: acc
            in
            Map.fold send_reward_func i.1 ops
        in
        let operations : operation list = Map.fold compute_and_send_func percentages ([] : operation list) in
        let remove_points (acc, percentages_i : (address, (nat, nat) map) big_map * (address * (nat, nat) map) ) : (address, (nat, nat) map) big_map = 
            let user : address = percentages_i.0 in
            let percs : (nat, nat) map = percentages_i.1 in 
            let rem(week_points, j : (nat, nat) map * (nat * nat)) : (nat, nat) map = 
                let week_indice : nat = j.0 in
                match Map.find_opt week_indice week_points with
                | None -> week_points
                | Some(_pts) -> Map.update week_indice (Some(0n)) week_points
            in
            // acc[user]
            let week_points_for_user : (nat, nat) map = match Big_map.find_opt user acc with
            | None -> (failwith(rewards_sent_but_missing_points) : (nat, nat) map)
            | Some(wk_pts) -> wk_pts
            in
            let new_week_points : (nat, nat) map = Map.fold rem percs week_points_for_user in 
            let modified_map : (address, (nat, nat) map) big_map = Map.update user (Some(new_week_points)) acc in 
            modified_map
        in
        let remove_points_map : (address, (nat, nat) map) big_map = Map.fold remove_points percentages s.user_points in 
        (operations, { s with user_points = remove_points_map })