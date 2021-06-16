import time
import os
import math
import sys
import xlsxwriter
import json

game_path = os.path.dirname(os.path.abspath(__file__)) + "/"  # Path to game
game_name = "lbg_silverlioness4x"  # Game name with no spaces, used for generating the name of the csv file


# User Defined Helper Functions for Sim ------------------------------------------------
def log_play_data(worker_results, play_data):
    """
    User defined function for properly logging data returned from each play call.
    :param worker_results: {dict} current combined data from play calls. Initialized to win: 0, cost:0.
    :param play_data: {dict} data returned from play call.
    :return: None.
    """
    if play_data.get("error") is not None:
        sys.exit()

    game_type = play_data["state"]

    if worker_results.get("bet") is None:
        worker_results["bet"] = play_data["cost"]

    if worker_results.get(game_type) is None:
        worker_results[game_type] = {"win": 0, "trials": 0, "winAmountCount": {}}

    worker_results["win"] += play_data["win"]  # Required for sim to calculate and log RTP
    worker_results["cost"] += play_data["cost"]  # Required for sim to calculate and log RTP

    if is_cycle_win(play_data):
        worker_results["connectorWin"] += play_data["finalBalance"]
        cycle_win = play_data["win"]

        if play_data["state"] == "freespin":
            cycle_win = play_data["totalWin"]

        if worker_results["winAmountCount"].get(cycle_win) is None:
            worker_results["winAmountCount"][cycle_win] = 1
        else:
            worker_results["winAmountCount"][cycle_win] += 1

    if worker_results[game_type]["winAmountCount"].get(play_data["win"]) is None:
        worker_results[game_type]["winAmountCount"][play_data["win"]] = 1

    else:
        worker_results[game_type]["winAmountCount"][play_data["win"]] += 1

    worker_results[game_type]["win"] += play_data["win"]
    worker_results[game_type]["trials"] += 1

    if play_data.get("state") == "base":
        worker_results["connectorCost"] += play_data["preWinBalance"]

    if play_data.get("ways") is not None:
        if worker_results[game_type].get("wins") is None:
            worker_results[game_type]["wins"] = {}

        add_wins(worker_results[game_type], play_data["ways"])

    if play_data.get("scatters") is not None:
        if worker_results[game_type].get("scatters") is None:
            worker_results[game_type]["scatters"] = {}

        if game_type == "base":
            add_scatters(worker_results[game_type], play_data["scatters"], 3)
        else:
            add_scatters(worker_results[game_type], play_data["scatters"], 2)

    if game_type == "freespin":
        if worker_results[game_type].get("reelid_n_mul") is None:
            worker_results[game_type]["reelid_n_mul"] = {}
        if worker_results[game_type].get("two_reel_mult") is None:
            worker_results[game_type]["two_reel_mult"] = {}
        if worker_results[game_type].get("three_reel_mult") is None:
            worker_results[game_type]["three_reel_mult"] = {}
        if worker_results[game_type].get("four_reel_mult") is None:
            worker_results[game_type]["four_reel_mult"] = {}

        for win in play_data.get("freespinWildMultiplierLst"):
            multiplier = win['mul']

            if multiplier == 2 and play_data.get("freespinWildMultiplierLst") is not None:
                if worker_results[game_type]["two_reel_mult"].get(str(multiplier)) is None:
                    worker_results[game_type]["two_reel_mult"][str(multiplier)] = {}
                if worker_results[game_type]["two_reel_mult"][str(multiplier)].get(str(multiplier)) is None:
                    worker_results[game_type]["two_reel_mult"][str(multiplier)][str(multiplier)] = 1
                else:
                    worker_results[game_type]["two_reel_mult"][str(multiplier)][str(multiplier)] += 1

            if multiplier == 3 and play_data.get("freespinWildMultiplierLst") is not None:
                if worker_results[game_type]["three_reel_mult"].get(str(multiplier)) is None:
                    worker_results[game_type]["three_reel_mult"][str(multiplier)] = {}
                if worker_results[game_type]["three_reel_mult"][str(multiplier)].get(str(multiplier)) is None:
                    worker_results[game_type]["three_reel_mult"][str(multiplier)][str(multiplier)] = 1
                else:
                    worker_results[game_type]["three_reel_mult"][str(multiplier)][str(multiplier)] += 1

            if multiplier == 4 and play_data.get("freespinWildMultiplierLst") is not None:
                if worker_results[game_type]["four_reel_mult"].get(str(multiplier)) is None:
                    worker_results[game_type]["four_reel_mult"][str(multiplier)] = {}
                if worker_results[game_type]["four_reel_mult"][str(multiplier)].get(str(multiplier)) is None:
                    worker_results[game_type]["four_reel_mult"][str(multiplier)][str(multiplier)] = 1
                else:
                    worker_results[game_type]["four_reel_mult"][str(multiplier)][str(multiplier)] += 1

        if play_data.get("freespinWildMultiplierLst") is not None:
            for win in play_data.get("freespinWildMultiplierLst"):
                multiplier = win['mul']
                reel_id = win['reelId']

                reelid_n_mul = 'reel_id_' + str(reel_id) + '_mult_' + str(multiplier)

                if worker_results[game_type]["reelid_n_mul"].get(str(reelid_n_mul)) is None:
                    worker_results[game_type]["reelid_n_mul"][str(reelid_n_mul)] = {}

                if worker_results[game_type]["reelid_n_mul"][str(reelid_n_mul)].get(str(reelid_n_mul)) is None:
                    worker_results[game_type]["reelid_n_mul"][str(reelid_n_mul)][str(reelid_n_mul)] = 1
                else:
                    worker_results[game_type]["reelid_n_mul"][str(reelid_n_mul)][str(reelid_n_mul)] += 1

    if game_type == "freespin" and play_data["freespins"] == 0:
        if worker_results[game_type].get("spins") is None:
            worker_results[game_type]["spins"] = {}

        if worker_results[game_type]["spins"].get(play_data["totalFreespins"]) is None:
            worker_results[game_type]["spins"][play_data["totalFreespins"]] = 1

        else:
            worker_results[game_type]["spins"][play_data["totalFreespins"]] += 1


def build_play_request(last_play_data, model, playerid, variant, denom, bet, pick):
    """
    User defined function for properly generating play request to simulate the front end
    :param last_play_data: {dict} return from last play call. Empty if no play call has been made.
    :param model: {module} module of the model file for the game, used to instantiate classes
    :param playerid: {string} name of the worker
    :return: {class} User defined request to simulate front end
    """
    if variant is not None:
        request = model.PlayRequest(
            {"playerid": playerid, "gameid": game_name, "variant": variant, "bet": bet, "denom": denom,
             "event": "spin",
             # emulating at the time of freespin request
             # freegame has 13 symbol as wild, for it the multiplier is fetched
             # 'emulateMatrix': {
            # 'inner': [[11, 6, 7, 11], [13, 11, 11, 11], [13, 10, 5, 8], [13, 11, 5, 5], [6, 11, 11, 2]],
            # 'outer': [[10, 3], [11, 8], [11, 10], [3, 7], [7, 6]], 'index': [6, 64, 64, 73, 37]},
            # 'emulateMult': {1: 4, 2: 3, 3: 3}
        })


        # if last_play_data == {}:
            # added  below data for emulator purpose only --- Base Game
            # request.emulateMatrix= {'inner': [[12, 6, 7, 12], [0, 11, 12, 11], [0, 10, 5, 8], [0, 12, 5, 5], [6, 12, 11, 2]],
            #                    'outer': [[10, 3], [11, 8], [11, 10], [3, 7], [7, 6]], 'index': [6, 64, 64, 73, 37]}


    else:
        request = model.PlayRequest(
            {"playerid": playerid, "gameid": game_name, "variant": "90", "bet": bet, "denom": denom, "event": "spin"})

    return request


def is_cycle_win(play_data):
    if play_data.get("scatters") is not None:
        for scatter in play_data["scatters"]:
            if play_data["scatters"][scatter].get("trigger") is not None:
                return False

    if play_data["state"] == "base":
        play_data["endCycle"] = True
        return True
    elif play_data["state"] == "freespin" and play_data["freespins"] == 0:
        play_data["endCycle"] = True
        return True

    return False


def add_wins(worker_results, wins):
    for win in wins:

        length = str(wins[win]["length"])
        symbol = str(win)
        mult = wins[win].get("multiplier")

        if mult is None:
            mult = 1
        else:
            mult = int(mult)

        if worker_results["wins"].get(symbol) is None:
            worker_results["wins"][symbol] = {}

        if worker_results["wins"][symbol].get(mult) is None:
            worker_results["wins"][symbol][mult] = {}

        if worker_results["wins"][symbol][mult].get(length) is None:
            worker_results["wins"][symbol][mult][length] = 1

        else:
            worker_results["wins"][symbol][mult][length] += 1


def add_scatters(worker_results, scatters, min_count):
    for scatter in scatters:
        count = str(scatters[scatter]["count"])

        if int(count) < min_count:
            continue

        if worker_results["scatters"].get(scatter) is None:
            worker_results['scatters'][scatter] = {}

        if worker_results["scatters"][scatter].get(count) is None:
            worker_results["scatters"][scatter][count] = 1

        else:
            worker_results["scatters"][scatter][count] += 1


def add_mult(worker_results, mult):
    if worker_results.get("multipliers") is None:
        worker_results["multipliers"] = {}

    if worker_results["multipliers"].get(mult) is None:
        worker_results["multipliers"][mult] = 1

    else:
        worker_results["multipliers"][mult] += 1


def add_progressives(worker_results, progressives):
    if worker_results.get("progressives") is None:
        worker_results["progressives"] = {}

    for tier in progressives:
        if worker_results["progressives"].get(tier) is None:
            worker_results["progressives"][tier] = {}

        if worker_results["progressives"][tier].get(progressives[tier]) is None:
            worker_results["progressives"][tier][progressives[tier]] = 1

        else:
            worker_results["progressives"][tier][progressives[tier]] += 1


# Pre defined Helper Functions for Sim ------------------------------------------------
def calc_remaining_time(elapsed_time, percent_complete):
    """
    Calculates the estimated remaining time based on the elapsed time and the percent complete
    :param elapsed_time: {float} elapsed time in seconds.
    :param percent_complete: {float} decimal value representing the percent complete
    :return: {string} time represented in the format days-hours:minutes:seconds
    """
    estimated_total_time = elapsed_time / percent_complete
    estimated_time_remaining = estimated_total_time - elapsed_time

    return format_time(estimated_time_remaining)


def format_time(unformatted_time):
    """
    Converts a given time in seconds to a string representation in days-hours:minutes:seconds
    :param unformatted_time: {float} time in seconds
    :return: {string} time represented in the format days-hours:minutes:seconds
    """
    time_struct = time.gmtime(unformatted_time)

    return "%d-%d:%d:%d" % (time_struct.tm_yday - 1, time_struct.tm_hour, time_struct.tm_min, time_struct.tm_sec)


def calculate_error(expected_rtp, sd, observed_rtp, trials):
    """
    Calculates the percent error of the observed rtp compared to the expected rtp,
    using the standard deviation and number of trials to specify accuracy
    :param expected_rtp: {float} The expected rtp value of the math model
    :param sd: {float} The standard deviation of the math model
    :param observed_rtp: {float} The observed rtp of the sim
    :param trials: {int} The number of trials the sim ran
    :return: {string} The percent error of the sim results with 2 decimal accuracy
    """
    denominator = observed_rtp - expected_rtp
    divisor = (1.96 * sd) / math.sqrt(trials)
    error = denominator / divisor

    return error


def calculate_sd(wins, bet):
    """
    Calculate the standard deviation of each worker from the sim
    :param wins: {dict} All wins amounts recorded with the count of the number of times the win occurred
    :return: {string} calculated standard deviation of all of the workers from the sim
    """
    mean = 0
    sd = 0
    count = 0

    for win in wins:
        mean += (int(win) / bet) * wins[win]
        count += wins[win]

    mean /= count

    for win in wins:
        sd += wins[win] * ((int(win) / bet) - mean) ** 2

    sd = math.sqrt(sd / count)

    return "%.2f" % sd


def combine_worker_results(raw_worker_results, combined_data, trials):
    """
    Takes the raw input from a group of workers and combines them,
    excluding the expected rtp and standard deviation. Also adds the percent
    error and the standard deviation of the sim.
    :param raw_worker_results: {list} results returned by each worker
    :param combined_data: {dict} combination of all of the worker results
    :return: None
    """
    game_rtp = raw_worker_results[0]["expected_rtp"]
    worker_rtps = []

    for result in raw_worker_results:
        worker_rtps.append(result["win"] / result["cost"])

        for data in result:
            if data != "expected_rtp" and data != "sd" and data != "bet":
                add_data_item(data, result[data], combined_data)

    observed_rtp = combined_data["win"] / combined_data["cost"]
    combined_data["bet"] = raw_worker_results[0]["bet"]
    combined_data["sd"] = calculate_sd(combined_data["winAmountCount"], combined_data["bet"])
    combined_data["error"] = calculate_error(game_rtp, float(combined_data["sd"]), observed_rtp, trials)


def add_data_item(data_tag, new_data, location):
    """
    Recursively adds data to a dict, creating labels as needed
    :param data_tag: {string} the reference name of the data item
    :param new_data: the actual data to be added to the dict, can be a dict or number
    :param location: {dict} the current location within the dictionary where the data should be placed
    :return: None
    """
    if isinstance(new_data, dict):
        if location.get(data_tag) is None:
            location[data_tag] = {}

        for item in new_data:
            add_data_item(item, new_data[item], location[data_tag])

    else:

        if location.get(data_tag) is None:
            location[data_tag] = new_data

        else:
            location[data_tag] += new_data


def print_sim_results(sim_results):
    """
    Prints out the sim results to the console
    :param sim_results: {dict} combined results from the sim
    :return: None
    """
    rtp = "%.2f" % ((sim_results["win"] / sim_results["cost"]) * 100)
    error = "%.2f" % (sim_results["error"] * 100)
    print("Cost: %d \nBet: %d \nWin: %d \nSD: %s \nRTP: %s%% \nError: %s%%" %
          (sim_results["cost"], sim_results["bet"], sim_results["win"], sim_results["sd"], rtp, error))

    if sim_results.get("base") is not None:
        base_rtp = sim_results["base"]["win"] / sim_results["cost"]
        base_rtp = "%.2f" % (base_rtp * 100)
        print("\nBase Game RTP: %s" % base_rtp)

    if sim_results.get("freespin") is not None:
        freespin_rtp = sim_results["freespin"]["win"] / sim_results["cost"]
        freespin_rtp = "%.2f" % (freespin_rtp * 100)
        print("\nFree Spin RTP: %s\n" % freespin_rtp)


def print_result(data_tag, data_item, location, indent_level):
    """
    Recursively print objects in a dictionary
    :param data_tag: {str} Name of the object
    :param data_item: data object to be printed
    :param location: {dict}location of the data object within the dictionary
    :param indent_level: specifies how far the item should be indented
    :return: None
    """
    indent = ""

    for _ in range(indent_level):
        indent += "\t"

    if data_tag == "winAmountCount":
        return

    if isinstance(data_item, dict):
        print("\n%s%s:" % (indent, data_tag))

        for item in location[data_tag]:
            print_result(item, data_item[item], location[data_tag], indent_level + 1)

    else:
        print("%s%s: %d" % (indent, data_tag, data_item))


def results_to_csv(sim_results, variant, trials):
    """
    Writes the results of the sim to a CSV file
    :param sim_results: {dict} Combined results of the Sim
    :param trials: Number of trials ran by the sim
    :return: None
    """
    scientific_trials = '%.0E' % trials
    time_stamp = time.strftime("%b_%d_%Y_%H-%M-%S")
    file_path = "SimResults/%s/" % game_name
    sim_type = get_sim_type(sim_results.get("bet", 1))
    file_name = "%s_%s_%s_%s_%s_%s.xlsx" % (
        game_name, "v" + get_version(), scientific_trials, variant, sim_type, time_stamp)

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    workbook = xlsxwriter.Workbook(file_path + file_name)

    formats = {
        "percent": workbook.add_format({"num_format": 0x0a}),
        "bold": workbook.add_format({"bold": True})
    }

    write_summary_sheet(sim_results, trials, workbook, formats)
    write_base_sheet(sim_results["base"], sim_results["cost"], workbook, formats)

    if sim_results.get("pick") is not None:
        write_pick_sheet(sim_results["pick"], workbook, formats)

    if sim_results.get("freespin") is not None:
        write_freespin_sheet(sim_results["freespin"], sim_results["cost"], workbook, formats)

    workbook.close()


def write_summary_sheet(results, trials, workbook, formats):
    rtp = results["win"] / results["cost"]

    worksheet = workbook.add_worksheet("Summary")

    worksheet.write(0, 0, "Trials")
    worksheet.write(0, 1, int(trials))
    worksheet.write(1, 0, "Cost")
    worksheet.write(1, 1, int(results["cost"]))
    worksheet.write(2, 0, "Bet")
    worksheet.write(2, 1, int(results["bet"]))
    worksheet.write(3, 0, "Total Won")
    worksheet.write(3, 1, int(results["win"]))
    worksheet.write(4, 0, "SD")
    worksheet.write(4, 1, float(results["sd"]))
    worksheet.write(5, 0, "RTP")
    worksheet.write(5, 1, rtp, formats["percent"])
    worksheet.write(6, 0, "Error")
    worksheet.write(6, 1, results["error"], formats["percent"])

    worksheet.write(8, 0, "Connector Cost")
    worksheet.write(8, 2, int(results["connectorCost"]))
    worksheet.write(9, 0, "Connector Win")
    worksheet.write(9, 2, int(results["connectorWin"]))
    worksheet.write(10, 0, "Connector RTP")
    worksheet.write(10, 2, float(results["connectorWin"] / results["connectorCost"]), formats["percent"])

    write_win_results(results["winAmountCount"], 13, worksheet, formats)


def write_base_sheet(results, cost, workbook, formats):
    row = 0
    worksheet = workbook.add_worksheet("Base Game")
    rtp = results["win"] / cost

    worksheet.write(row, 0, "Count")
    worksheet.write(row, 1, int(results["trials"]))
    row += 1

    worksheet.write(row, 0, "Total Won")
    worksheet.write(row, 1, int(results["win"]))
    row += 1

    worksheet.write(row, 0, "RTP")
    worksheet.write(row, 1, rtp, formats["percent"])
    row += 3

    row = write_scatter_results(results["scatters"], row, worksheet, formats)
    row = write_symbol_results(results["wins"], row, worksheet, formats)
    write_win_results(results["winAmountCount"], row, worksheet, formats)


def write_freespin_sheet(results, cost, workbook, formats):
    row = 0
    worksheet = workbook.add_worksheet("Free Spins")
    rtp = results["win"] / cost

    worksheet.write(row, 0, "Count")
    worksheet.write(row, 1, int(results["trials"]))
    row += 1

    worksheet.write(row, 0, "Total Won")
    worksheet.write(row, 1, int(results["win"]))
    row += 1

    worksheet.write(row, 0, "RTP")
    worksheet.write(row, 1, rtp, formats["percent"])
    row += 3
    row = write_spins_results(results["spins"], row, worksheet, formats)
    row = write_multiplier_reelid_n_mul(results["reelid_n_mul"], row, worksheet, formats)
    row = write_two_reels_selected_mul(results["two_reel_mult"], row, worksheet, formats)
    row = write_three_reels_selected_mul(results["three_reel_mult"], row, worksheet, formats)
    row = write_four_reels_selected_mul(results["four_reel_mult"], row, worksheet, formats)
    row = write_scatter_results(results["scatters"], row, worksheet, formats)
    row = write_symbol_results(results["wins"], row, worksheet, formats)
    write_win_results(results["winAmountCount"], row, worksheet, formats)


def write_pick_sheet(results, workbook, formats):
    row = 0
    worksheet = workbook.add_worksheet("Pick")

    worksheet.write(row, 0, "Count")
    worksheet.write(row, 1, int(results["trials"]))
    row += 3

    row = write_pick_info_results(results["freespinType"], row, worksheet, formats, "Free Spins Type")
    write_pick_info_results(results["multType"], row, worksheet, formats, "Multiplier Type")


def write_win_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Win")
    worksheet.write(row, col + 1, "Count")

    for win in sorted(results):
        row += 1

        worksheet.write(row, col, win)
        worksheet.write(row, col + 1, results[win])
    return row + 3


def write_multiplier_reelid_n_mul(results, row, worksheet, formats):
    col = 0
    worksheet.write(row, col, "Selected_reels", formats["bold"])
    row += 2
    worksheet.write(row, col, "reeld_n_mul", formats["bold"])
    worksheet.write(row, col + 1, "Count", formats["bold"])
    total = 0

    for reel in sorted(results):
        total += results[reel][reel]
        row += 1
        worksheet.write(row, col, reel)
        worksheet.write(row, col + 1, results[reel][reel])

    worksheet.write(row + 1, col, "Total", formats["bold"])
    worksheet.write(row + 1, col + 1, total)

    return row + 3


def write_two_reels_selected_mul(two_reel_mul, row, worksheet, formats):
    col = 0
    worksheet.write(row, col, "2 Reels selected", formats["bold"])
    row += 2

    worksheet.write(row, col, "Multipliers", formats["bold"])
    worksheet.write(row, col + 1, "Count", formats["bold"])
    total = 0

    for mul in sorted(two_reel_mul):
        row += 1
        total += two_reel_mul[mul][mul]

        worksheet.write(row, col, mul)
        worksheet.write(row, col + 1, two_reel_mul[mul][mul])
    worksheet.write(row + 1, col, "Total", formats["bold"])
    worksheet.write(row + 1, col + 1, total)
    return row + 3


def write_three_reels_selected_mul(three_reel_mul, row, worksheet, formats):
    col = 0
    worksheet.write(row, col, "3 Reels selected", formats["bold"])
    row += 2

    worksheet.write(row, col, "Multipliers", formats["bold"])
    worksheet.write(row, col + 1, "Count", formats["bold"])
    total = 0
    for mul in sorted(three_reel_mul):
        row += 1
        total += three_reel_mul[mul][mul]

        worksheet.write(row, col, mul)
        worksheet.write(row, col + 1, three_reel_mul[mul][mul])
    worksheet.write(row + 1, col, "Total", formats["bold"])
    worksheet.write(row + 1, col + 1, total)
    return row + 3


def write_four_reels_selected_mul(three_reel_mul, row, worksheet, formats):
    col = 0
    worksheet.write(row, col, "4 Reels selected", formats["bold"])
    row += 2

    worksheet.write(row, col, "Multipliers", formats["bold"])
    worksheet.write(row, col + 1, "Count", formats["bold"])
    total = 0
    for mul in sorted(three_reel_mul):
        row += 1
        total += three_reel_mul[mul][mul]

        worksheet.write(row, col, mul)
        worksheet.write(row, col + 1, three_reel_mul[mul][mul])
    worksheet.write(row + 1, col, "Total", formats["bold"])
    worksheet.write(row + 1, col + 1, total)
    return row + 3


def write_scatter_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Scatters", formats["bold"])
    row += 1

    for scatter in results:
        worksheet.write(row, col, "Symbol " + str(scatter))
        worksheet.write(row + 1, col, "Count")

        for count in sorted(results[scatter]):
            col += 1
            worksheet.write(row, col, int(count))
            worksheet.write(row + 1, col, int(results[scatter][count]))

    return row + 4


def write_replace_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Replace", formats["bold"])

    for replace in sorted(results):
        row += 1
        worksheet.write(row, col, int(replace))
        worksheet.write(row, col + 1, int(results[replace]))

    return row + 3


def write_mult_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Multipliers", formats["bold"])

    for reel in sorted(results):
        row += 1
        worksheet.write(row, col, "Reel " + str(reel))
        worksheet.write(row + 1, col, "Count")
        col += 1

        for mult in sorted(results[reel]):
            col += 1
            worksheet.write(row, col, int(mult))
            worksheet.write(row + 1, col, int(results[reel][mult]))

        row += 1
        col = 0

    return row + 3


def write_spins_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Free Spins Played", formats["bold"])

    for spins in sorted(results):
        row += 1
        worksheet.write(row, col, int(spins))
        worksheet.write(row, col + 1, int(results[spins]))

    return row + 3


def write_symbol_results(results, row, worksheet, formats):
    col = 0

    worksheet.write(row, col, "Symbol Wins", formats["bold"])

    for symbol in sorted(results):
        for mult in sorted(results[symbol]):
            row += 1
            worksheet.write(row, col, "Symbol " + str(symbol) + "  - X" + str(mult))
            worksheet.write(row + 1, col, "Count")
            col += 1

            for win in sorted(results[symbol][mult]):
                col += 1
                worksheet.write(row, col, int(win))
                worksheet.write(row + 1, col, int(results[symbol][mult][win]))

            row += 2
            col = 0

    return row + 3


def write_pick_info_results(results, row, worksheet, formats, label):
    col = 0

    worksheet.write(row, col, label, formats["bold"])

    for pick in sorted(results):
        row += 1
        worksheet.write(row, col, str(pick))
        worksheet.write(row, col + 1, int(results[pick]))

    return row + 3


def get_version():
    """
    Returns the current version of the game
    :return: int
    """
    with open(game_path + "package.json") as package:
        version = json.load(package)["backend_version"]
    return version


def get_sim_type(bet):
    with open("configs/connector/ConnectorConfig.json") as connector_config:
        is_social = json.load(connector_config).get("social", False)

        if is_social or bet > 10000:
            return "Social"
        else:
            return "For_Wager"
