# Emulator.py
from games.lbg_silverlioness4x.Model import Model as BaseModel
from games.libs.server.RequestBase import RequestBase


class PlayRequest(RequestBase):
    def __init__(self, play_request):
        """
        When spin is triggered play request is called
        :param play_request:
        """
        super(PlayRequest, self).__init__(play_request)


class Model(BaseModel):
    # Added for only testing purpose
    def __init__(self, system_config, database, rng, controller, logger):
        """
        function to call the parent Model class (BaseModel)
        :param system_config:
        :param database:
        :param rng:
        :param controller:
        :param logger:
        """
        super(Model, self).__init__(system_config, database, rng, controller, logger)

    def get_matrix(self, reels, play_request):
        """
        Emulated matrix from front end is received here and processed
        :param reels: reels used to generate the matrix
        :param play_request:The play request used to emulate the data( matrix), else model class functionality is
        done
        :return:
        """

        # check if play_request emulated matrix has values
        if play_request.emulateMatrix is not None:
            return play_request.emulateMatrix
        else:
            return super(Model, self).get_matrix(reels, play_request)

    def freegame_wild_multiplier(self, matrix, play):

        """
        Emulated freegame_wild_multiplier from front end is received here and processed
        :param matrix: It the matrix for which the emulator is done
        :param play_request: The play request used to emulate the data(freespin multiplier)
        :return:
        """
        if play.emulateMatrix and play.emulateMult:
            matrix_value = play.emulateMatrix['inner']
            freespin_mul_list = []
            freespin_mul_dict = {}
            wild_reel_id = []
            for reel_id, col in enumerate(matrix_value):
                for row, symbol in enumerate(col):
                    if symbol == 13:
                        mul_dict = dict()
                        # for the wild positions the emulated emulateMult is fetched.

                        mul = play.emulateMult[reel_id]
                        mul_dict['reelId'] = reel_id
                        mul_dict['mul'] = mul
                        mul_dict['col'] = row
                        wild_reel_id.append(reel_id)
                        freespin_mul_list.append(mul_dict)
                        freespin_mul_dict[reel_id] = mul_dict
            return freespin_mul_dict, freespin_mul_list, wild_reel_id

        else:
            return super(Model, self).freegame_wild_multiplier(matrix, play)
