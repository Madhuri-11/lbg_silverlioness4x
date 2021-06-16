# Model.py
# Description : This file in the game play the major role in backend process by Initializing the game
# (getting ready with Math configs), handling the play request and performs the reel spinning and calculates
# the win amount.Also handles recall and recovery requests
# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created date : 07/04/21
# author: Anish Sharma

import json
import time
import re
import itertools
from functools import reduce
from connector.Connector import ConnectorError
from games.lbg_silverlioness4x.lib.GameMath import GameMath
from games.libs.server.BaseModel import BaseModel
from games.libs.server.WaysMath import WaysMath
from games.libs.server.MatrixGenerator import MatrixGenerator
from games.libs.server.Replace import Replace
from games.libs.server.RequestBase import RequestBase
from games.libs.server.CustomErrors import RequestError
from games.libs.server.CustomErrors import RecoveryError
from games.libs.server.ScattersMath import ScattersMath
from server.libs.Database import DatabaseError
from server.libs.schema.Cycle import Cycle
import copy


class Bet:
    """
    Bet class is to getting [cost, bet, denoms] and setting bet levels
    """

    def __init__(self):
        """
        initializing bets and denoms and this will be set in default for first load of the game
        """
        self.bets = [1, 2, 3, 4, 5, 8, 10, 20, 50]
        self.denoms = [1]

    def get_cost(self, bet_index, base_cost):

        if bet_index < 0 or bet_index >= len(self.bets):
            raise RequestError("Invalid Bet Index")

        return self.get_bet(bet_index) * base_cost

    def get_bet(self, bet_index):
        """
        function to get the bet index
        :param bet_index:
        :return:
        """
        if bet_index < 0 or bet_index >= len(self.bets):
            raise RequestError("Invalid Bet Index")

        return self.bets[bet_index]

    def get_denoms(self, denom_index):
        """
        function to get the denom index
        :param denom_index:
        :return:
        """
        if denom_index < 0 or denom_index >= len(self.denoms):
            raise RequestError("Invalid Denom Index")

        return self.denoms[denom_index]

    def set_bet_levels(self, bets, denoms):
        """
        function to set bet levels and denom levels
        :param bets:
        :param denoms:
        :return:
        """
        self.bets = bets
        self.denoms = denoms


class InitializeRequest(RequestBase):
    def __init__(self, initialize_request):
        """
        Initialize request - game loads for 1st time
        :param initialize_request:
        """
        super(InitializeRequest, self).__init__(initialize_request)


class PlayRequest(RequestBase):
    def __init__(self, play_request):
        """
        When spin is triggered play request is called
        :param play_request:
        """
        super(PlayRequest, self).__init__(play_request)


class RecallRequest(RequestBase):
    def __init__(self, recall_request):
        """
        recall request is made to check when previous wins are made and plays the selected previous game
        :param recall_request:
        """
        super(RecallRequest, self).__init__(recall_request)


class RecoveryRequest(RequestBase):
    def __init__(self, recovery_request):
        """
        When game reloads/network disconnect in halfway of game - recovery request is made to get the state of game where it has left
        :param recovery_request:
        """
        super(RecoveryRequest, self).__init__(recovery_request)


class Model(BaseModel):
    """
    Model for  Silver lioness 4x -contains important  flow of game such as [initialize, play, recovery, recall]
    """

    def __init__(self, system_config, database, rng, connector, logger):
        """
        initializing all
        :param system_config:
        :param database:
        :param rng:
        :param connector:
        :param logger:
        """
        # calls the parent class and initializes with config,db,random num gen,etc..
        super(Model, self).__init__(system_config, database, rng, connector, logger)

        # generates random reel matrix[3x5] for each spin
        self.matrix = MatrixGenerator(self.rng)

        # after triggering spin until the reel stops - entire cycle is recorded/saved and finally closes
        self.cycle = Cycle()

        # Contains the Math logic behind each spin - calculates the win patterns and feature wins
        self.math = GameMath()
        # check for default symbols/wilds and pays accordingly
        self.ways = WaysMath(self.math.get_paytable(), self.math.get_wilds())

        # look for any scatter symbol that appears on reel matrix and triggers free spin accordingly
        self.scatters = ScattersMath(self.math.get_scatter("base"))
        # import the wild multiplier module using dynamic import module

        # calculates bet,cost,denoms and setting up the bet levels are done here
        self.bet = Bet()

    def initialize(self, initialize):
        """
        After game loads initialize method is called
        :param initialize:
        :return:
        """
        # setting recovery to empty [first time]/ replaces recovery with prev values after [nth time]
        recovery_cycle = None

        try:
            # after sending request - an initialize response is received and assigned to response
            response = initialize
            # getting player info from the current response object
            player_info = self.connector.get_player(initialize.session)

            # getting and assigning all player_info values to response dict
            response.balance = player_info["balance"]
            response.bet_levels = player_info["bets"]
            response.denoms = player_info["denoms"]
            response.currency = player_info["currency"]
            response.lang = player_info["lang"]
            response.cashSymbol = player_info["symbol"]
            response.baseURL = player_info["baseURL"]
            response.config = player_info.get("config")
            response.numberOfRecalls = player_info.get("numberOfRecalls", 5)

            # check whether config info from response has no values
            if response.config is None:
                response.config = {}
                self.logger.info("Missing Front End Game Configuration Info")

            # check whether disableButtons from response.config has no values
            if response.config.get("disableButtons") is None:
                response.config["disableButtons"] = []

            # check whether inCredits from player info has values
            if player_info.get("inCredits") is not None:
                response.inCredits = player_info["inCredits"]
            else:
                response.inCredits = True

            # calls the variant function from GameMath to set the variant inputted by the user [88,90,92,94,96]
            self.math.set_variant(player_info["variant"])
            # calls recovery from cycle to assign/check the previous recovery values
            recovery_cycle = self.cycle.recovery(player_info["playerid"], initialize.gameid, self.db)

            response.recovery = self.get_recovery(recovery_cycle, player_info["playerid"], initialize.gameid,
                                                  initialize.session, player_info.get("cycleWaitDuration",
                                                                                      self.default_cycle_wait_duration))
            # getting number of ways from GameMath and assigned to response property get_num_ways
            response.numWays = self.math.get_num_ways()

            # getting the reel strips to be displayed on first game load and assigned to response property reel_strips
            response.reel_strips = self.get_reels(response.recovery)

            # base reel strips
            response.base_reel_strips = self.math.get_reels("base")

            # freespin reel strips
            response.free_reel_strips = self.math.get_reels("freespin")

            # calling full_start_matrix from basemodel
            fullStartMatrix = self.get_full_start_matrix(response.recovery)

            # calling start_matrix from basemodel which calls get_start_matrix from GameMath which has fullStartMatrix
            # and those properties are assigned to following response properties startMatrix,outerStart,startIndices
            response.startMatrix = fullStartMatrix["inner"]
            response.outerStartMatrix = fullStartMatrix["outer"]
            response.startIndices = fullStartMatrix["index"]

            # calls rtp from gameMath and assigning to response dict
            response.rtp = self.math.get_rtp(player_info["variant"])[0]

            # check if recovery length is 0 and bets,denom values are set
            # which helps in loading bets and denom values for next game recovery
            if len(response.recovery) == 0 or player_info.get("forceDefaultBet"):
                default_bet_settings = player_info.get("defaultBetConfig", {})
                # check if default_bet_settings has values
                if default_bet_settings is not None:
                    response.recovery["denom"] = default_bet_settings.get("defaultDenomIndex", 0)
                    response.recovery["betMultiplier"] = default_bet_settings.get("defaultBetIndex", 0)
                else:
                    response.recovery["denom"] = 0
                    response.recovery["betMultiplier"] = 0

            # when game loads for nth time check_bet_index fn is called to revive the prev cycle
            # bet mult,values and denoms
            self.check_bet_index(response.recovery, response.bet_levels, response.denoms)

            # getting the game compatibility
            with open("games/lbg_silverlioness4x/package.json") as package:
                game_json = json.load(package)
                response.version = game_json["version"]
                self.check_game_lib_compatibility(game_json.get("game_libs_compatibility"))

            # check whether new balance has values
            if response.recovery.get("newBalance") is not None:
                response.balance = response.recovery["newBalance"]

            # For recovery, most games are using the final balance which does not get updated from the connector
            # so we overwrite the balance to display correctly
            if response.recovery.get("finalBalance"):
                response.recovery["finalBalance"] = response.balance
                response.recovery["preWinBalance"] = response.balance

            self.adjust_for_large_numbers(response)
            response = dict(response)
            return response

        # except in case of Connection,database,request,recovery error
        except (ConnectorError, DatabaseError, RequestError, RecoveryError) as err:
            if recovery_cycle is not None and recovery_cycle.state == "pendingResolve":
                self.logger.critical("Critical Error: Unable to resolve cycle - {}".format(str(recovery_cycle._id)))
                recovery_cycle.errorCode = err.lookup
                recovery_cycle.save(self.db)
                err.lookup = -1

            self.logger.exception(err, exc_info=True)
            return {"error": err.message, "lookup": err.lookup}

        except Exception as err:
            self.logger.exception(err, exc_info=True)
            return {"error": "Game Error", "lookup": 0}

    def play(self, play):
        cycle = None
        try:
            player_info = self.connector.get_player(play.session)
            play.playerid = player_info["playerid"]
            balance = player_info["balance"]

            self.bet.set_bet_levels(player_info["bets"], player_info["denoms"])

            cycle = self.cycle.find_or_create(play.playerid, play.gameid, self.db)

            self.set_variant(cycle, player_info["variant"])

            cycle.session = play.session
            cycle.site = player_info["site"]

            cycle.balance = balance

            if cycle.get("state") is not None and cycle.state != "complete":
                delta_time = int(time.time()) - cycle.get("lastUpdated", 0)
                # check if delta time is less than cycle wait duration
                if delta_time < player_info.get("cycleWaitDuration", self.default_cycle_wait_duration):
                    cycle = None
                    raise RecoveryError("Cycle Still Processing")
                elif cycle.state == "pendingResolve":
                    error = RecoveryError("Recovered Pending Resolve")
                    error.lookup = -1
                    raise error
                else:
                    raise RecoveryError("Invalid Recovery State")

            response = self.initialize_response(play, cycle.actions, balance)
            denom = response["denomValue"]
            cycle.create_action(play.event, response["cost"], dict(play), response)

            if response["cost"] != 0:
                cycle.state = "pendingWager"
                cycle.cost = response["cost"] * denom
                response["startingBalance"] = player_info["balance"]
                response["denomValue"] = denom
                cycle.save(self.db)
                response["preWinBalance"] = self.connector.place_wager(play.session, cycle, cycle.actions[-1]._id,
                                                                       cycle.cost)
                cycle.save(self.db)

            cycle.state = "pendingCalculations"

            reels = self.math.get_reels(response["state"])
            response["matrix_info"] = self.get_matrix(reels, play)
            response["outer_matrix"] = response["matrix_info"]["outer"]
            response["matrix"] = response["matrix_info"]["inner"]
            response["reelStartIndex"] = response["matrix_info"]["index"]

            response["ways"] = self.ways.find_wins(response["matrix"], response["betMultiplierValue"] * 40)
            response["win"] = self.ways.calc_win_amount(response["ways"])

            if response["state"] == "freespin":
                response["freespins"] -= 1
                matrix = response["matrix"]

                freespin_mul_dict, freespin_mul_list, wild_reel_id = self.freegame_wild_multiplier(matrix, play)

                total_acc_win = 0
                for win, win_node in list(response['ways'].items()):
                    symbol_positions = win_node['positions']
                    sym_ways_combinations = list(itertools.product(*symbol_positions))

                    accumulated_win = 0
                    win_break_up = []
                    base_pay = win_node['basePay']
                    for way_com_tup in sym_ways_combinations:
                        win_mul = 1
                        win_mul_lst = []
                        win_com_lst = list(way_com_tup)
                        for id in range(len(win_com_lst)):
                            if id in wild_reel_id:
                                sym_pos = win_com_lst[id]
                                if freespin_mul_dict[id]['col'] == sym_pos:
                                    multiplier = freespin_mul_dict[id]['mul']
                                    win_mul *= multiplier
                                    win_mul_lst.append(multiplier)
                        win_factor = base_pay * win_mul
                        accumulated_win += win_factor
                        node = {
                            'wildMuliplier': win_mul,
                            'base_pay': base_pay,
                            'wayPositions': win_com_lst,
                            'wildMultiplierList': win_mul_lst,
                            'individualWaysWin': win_factor,
                            'wildMultiplierDict': freespin_mul_dict
                        }
                        win_break_up.append(node)

                        win_node['breakup'] = win_break_up

                    win_node['symbolWin'] = accumulated_win
                    total_acc_win += accumulated_win
                response['win'] = total_acc_win
                response['freespinWildMultiplierLst'] = freespin_mul_list
                response["totalWin"] += response["win"]

                if freespin_mul_list:
                    temp_matrix = copy.deepcopy(response["matrix"])
                    for reel_id, col in enumerate(temp_matrix):
                        for row, symbol in enumerate(col):
                            if symbol == 13:
                                wild_mul = freespin_mul_dict[reel_id]['mul']
                                wild_symbol_id = self.math.wild_sym_lst[wild_mul]
                                temp_matrix[reel_id][row] = wild_symbol_id
                    response["matrix"] = temp_matrix

                    temp_inner_matrix = copy.deepcopy(response["matrix_info"]["inner"])
                    for reel_id, col in enumerate(temp_inner_matrix):
                        for row, symbol in enumerate(col):
                            if symbol == 13:
                                wild_mul = freespin_mul_dict[reel_id]['mul']
                                wild_symbol_id = self.math.wild_sym_lst[wild_mul]
                                temp_inner_matrix[reel_id][row] = wild_symbol_id
                    response["matrix_info"]["inner"] = temp_inner_matrix

            self.scatters.set_scatters(self.math.get_scatter(response["state"]))
            response["scatters"] = self.scatters.find_scatters(response["matrix"], self.get_scatter_cost(response))
            scatterWins = self.scatters.get_scatter_pays(response["scatters"])
            response["win"] += scatterWins

            feature_triggered = self.scatters.check_for_triggers(response["scatters"])
            if feature_triggered and response["state"] == "freespin":
                feature_triggered = False
                response["totalWin"] += self.scatters.get_scatter_pays(response["scatters"])
                response["freespins"] += self.math.get_spins(response["state"], response["scatters"]["12"]["count"])
                response["totalFreespins"] += self.math.get_spins(response["state"],
                                                                  response["scatters"]["12"]["count"])

            elif feature_triggered:
                response["startMatrix"] = self.math.get_start_matrix()
                response["totalFreespins"] = self.math.get_spins(response["state"], response["scatters"]["12"]["count"])
                response["freespins"] = response["totalFreespins"]
                response["totalWin"] = response["win"]

            if feature_triggered or self.feature_not_finished(response):
                response["finalBalance"] = response["preWinBalance"]
                cycle.state = "complete"
                cycle.save(self.db)

            else:

                if response["state"] != "base":
                    cycle.win = response["totalWin"] * denom
                else:
                    cycle.win = response["win"] * denom

                cycle.state = "pendingResolve"
                cycle.save(self.db)
                response["finalBalance"] = self.connector.resolve_wager(play.session, cycle, cycle.actions[-1]._id,
                                                                        cycle.win)
                cycle.state = "complete"
                cycle.close_and_save(self.db)

            self.check_bet_index(response, player_info["bets"], player_info["denoms"])

            return response

        except (ConnectorError, DatabaseError, RequestError, RecoveryError) as err:
            if cycle is not None:
                if cycle.state == "pendingResolve":
                    cycle.errorCode = err.lookup
                    cycle.save(self.db)
                elif hasattr(err, "valid_error") and err.valid_error is not False:
                    cycle.state = "ERROR"
                    cycle.errorCode = err.lookup
                    cycle.close_and_save(self.db)
                else:
                    self.refund_wager(cycle, play.session)

            self.logger.exception(err, exc_info=True)
            return {"error": err.message, "lookup": err.lookup}

        except Exception as err:
            if cycle is not None:
                self.refund_wager(cycle, play.session)

            self.logger.exception(err, exc_info=True)
            return {"error": "Game Error", "lookup": 0}

    def freegame_wild_multiplier(self, matrix, play):
        freespin_mul_list = []
        freespin_mul_dict = {}
        wild_reel_id = []
        for reel_id, col in enumerate(matrix):
            for row, symbol in enumerate(col):
                if symbol == 13:
                    mul_dict = dict()
                    mul = self.get_free_reel_multiplier(
                        self.math.get_freespin_reel_multiplier(reel_id))

                    mul_dict['reelId'] = reel_id
                    mul_dict['mul'] = mul
                    mul_dict['col'] = row
                    wild_reel_id.append(reel_id)
                    freespin_mul_list.append(mul_dict)  # added for client purpose only
                    freespin_mul_dict[reel_id] = mul_dict
        return freespin_mul_dict, freespin_mul_list, wild_reel_id

    def feature_not_finished(self, response):
        """
        function to check if any freespin is pending to complete
        :param response:
        :return:
        """
        if response.get("freespins") is not None and response["freespins"] > 0:
            return True

        return False

    def get_scatter_cost(self, response):

        if response["state"] == "base":
            return response["cost"]
        else:
            return response["triggerResponse"]["cost"]

    def initialize_response(self, play_request, actions, balance):
        """
        fucntion to maintain/record actions of the game
        :param play_request:
        :param actions:
        :param balance:
        :return:game
        """
        if len(actions) == 0:
            response = {
                "state": "base",
                "preWinBalance": balance,
                "version": self.math.version,
                "numWays": self.math.get_num_ways(),
                "cost": self.bet.get_cost(play_request.bet, self.math.get_base_cost()),
                "denom": play_request.denom,
                "denomValue": self.bet.get_denoms(play_request.denom),
                "betMultiplier": play_request.bet,
                "betMultiplierValue": self.bet.get_bet(play_request.bet)
            }
        elif actions[-1].response["state"] == "base":
            prev_response = actions[-1].response
            response = {
                "state": "freespin",
                "preWinBalance": balance,
                "version": self.math.version,
                "numWays": actions[-1].response["numWays"],
                "cost": 0,
                "denom": prev_response["denom"],
                "denomValue": prev_response["denomValue"],
                "betMultiplier": prev_response["betMultiplier"],
                "betMultiplierValue": prev_response["betMultiplierValue"],
                "totalWin": prev_response["totalWin"],
                "triggerResponse": prev_response,
                "totalFreespins": prev_response["totalFreespins"],
                "freespins": prev_response["totalFreespins"]
            }
        elif actions[-1].response["freespins"] > 0:
            prev_response = actions[-1].response
            response = {
                "state": "freespin",
                "preWinBalance": balance,
                "version": self.math.version,
                "numWays": actions[-1].response["numWays"],
                "cost": 0,
                "denom": prev_response["denom"],
                "denomValue": prev_response["denomValue"],
                "betMultiplier": prev_response["betMultiplier"],
                "betMultiplierValue": prev_response["betMultiplierValue"],
                "triggerResponse": prev_response["triggerResponse"],
                "totalWin": prev_response["totalWin"],
                "totalFreespins": prev_response["totalFreespins"],
                "freespins": prev_response["freespins"],
                "freespinWildMultiplierLst": prev_response['freespinWildMultiplierLst'],
            }
        else:
            raise RequestError("Invalid Play Request Sent")

        self.adjust_for_large_numbers(response)
        return response

    def get_free_reel_multiplier(self, multiplier_dist):
        """
        fucntion to  get the  multiplier for two reels
        :param multiplier_dist:
        :return:

        """

        return self.rng.distribution(multiplier_dist)

    def adjust_recovery_response(self, response, cycle):
        """
        function to adjust recovery respone
        :param response:
        :param cycle:
        :return:
        """
        if response["state"] == "freespin" and response["freespins"] == 0:
            response = cycle["actions"][0]["response"]
            del response["scatters"]  # ["12"]["trigger"]
        return None

    def get_matrix(self, reels, play_request):
        """
        function to get matrix
        :param reels:
        :param play_request:
        :return:
        """
        return self.matrix.generate_full_matrix(reels, self.math.get_reel_layout())

    def get_reels(self, recovery):
        """
        function to get reels based on the game state
        :param recovery:
        :return:
        """
        if recovery.get("state") is None:
            return self.math.get_reels("base")

        elif recovery["state"] == "base":
            return self.math.get_reels("base")
        elif recovery["state"] == "freespin":
            return self.math.get_reels("freespin")

    def check_bet_index(self, recovery, bets, denoms):
        """
        function to check bet index
        :param recovery:
        :param bets:
        :param denoms:
        :return:
        """
        if recovery.get("betMultiplier") is not None and recovery["betMultiplier"] >= len(bets):
            recovery["betMultiplier"] = len(bets) - 1

            if recovery.get("triggerResponse") is not None:
                recovery["triggerResponse"]["betMultiplier"] = len(bets) - 1

        if recovery.get("denom") is not None and recovery["denom"] >= len(denoms):
            recovery["denom"] = len(denoms) - 1

            if recovery.get("triggerResponse") is not None:
                recovery["triggerResponse"]["denom"] = len(denoms) - 1
        return None

    def get_select_reel(self, reel, play_request):
        """
        function to get reel while emulating for multiplietr
        :param reel, play_request :
        :return:
        """

        return reel

    def get_select_multiplier(self, multiplier, play_request):
        """
        function to get the multiplier  while emulating
        :param multiplier, play_request :
        :return:
        """
        return multiplier
