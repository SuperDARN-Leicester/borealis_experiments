#!/usr/bin/python

"""
RocketSoundV2
~~~~~~~~~~~
Rocket chaser!

N beam scan over multiple frequencies

The sequence is
Freq 1 - beam#1, beam#2...beam#N
Freq 2 - beam#1, beam#2...beam#N
Freq 3 - beam#1, beam#2...beam#N
etc.

Integration time: 3.0 sec
Range res: 15 km
NOTE: 15 km range cells need a new filter!
Clear Freq Scan included
Ignore the 1 min scan boundaries

:copyright: 2026 SuperDARN Leicester
"""

import copy

from experiment_prototype.experiment_prototype import ExperimentPrototype
import borealis_experiments.superdarn_common_fields as scf
import experiment_prototype.experiment_utils.decimation_scheme as dm


def filter_15km_mode():
    sample_rate = 5e6  # 5 MHz
    dm_rate = [25, 20]  # downsampling rates after filters
    transition_width = [150e3, 30e3]  # transition from passband to stopband
    cutoff_hz = [10e3, 5e3]  # bandwidth for output of filter
    ripple_db = [115, 50]  # dB between passband and stopband
    scaling_factors = [1000.0, 10000.0]  # multiplicative factors for each filter stage

    dm_rate_so_far = 1
    stages = []

    # First stage Kaiser
    taps = scaling_factors[0] * dm.create_firwin_filter_by_attenuation(
        sample_rate, transition_width[0], cutoff_hz[0], ripple_db[0]
    )
    stages.append(dm.DecimationStage(0, sample_rate, dm_rate[0], taps.tolist()))
    dm_rate_so_far *= dm_rate[0]

    # Second stage Kaiser by num taps
    taps = scaling_factors[1] * dm.create_firwin_filter_by_num_taps(sample_rate / dm_rate_so_far, cutoff_hz[1], 41)
    stages.append(dm.DecimationStage(1, sample_rate / dm_rate_so_far, dm_rate[1], taps.tolist()))
    dm_rate_so_far *= dm_rate[1]

    scheme = dm.DecimationScheme(
        sample_rate, sample_rate / dm_rate_so_far, stages=stages
    )

    return scheme



class Rocket_Sound(ExperimentPrototype):

    def __init__(self, **kwargs):
        cpid = 20666 

        if scf.IS_FORWARD_RADAR:
            beams_to_use = scf.STD_16_FORWARD_BEAM_ORDER
        else:
            beams_to_use = scf.STD_16_REVERSE_BEAM_ORDER
        beams_to_use = [4, 5, 6]
        if scf.options.site_id in ["cly", "rkn", "inv"]:
            num_ranges = scf.POLARDARN_NUM_RANGES
        if scf.options.site_id in ["sas", "pgr", "lab", "han"]:
            num_ranges = scf.STD_NUM_RANGES

        slice_1 = {  # slice_id = 0, the first slice
            "pulse_sequence": scf.SEQUENCE_7P,
            "tau_spacing": scf.TAU_SPACING_7P,
            "pulse_len": scf.PULSE_LEN_15KM,
            "num_ranges": num_ranges,
            "first_range": scf.STD_FIRST_RANGE,
#            "intt": scf.INTT_7P,  # duration of an integration, in ms
            "intt": 3000,  # duration of an integration, in ms
            "beam_angle": scf.STD_16_BEAM_ANGLE,
            "rx_beam_order": beams_to_use,
            "tx_beam_order": beams_to_use,
#            "scanbound": scf.easy_scanbound(scf.INTT_7P, beams_to_use),
            "scanbound": None,
#            "wait_for_first_scanbound": False,
#            "align_sequences": True,
            "cfs_range": [9911, 9983],
#            "txctrfreq": 9500, #centre  frequency in cfs_scan range
#            "rxctrfreq": 9500, #centre  frequency in cfs_scan range
            "decimation_scheme": filter_15km_mode(),
            "acf": True,
            "xcf": True,  # cross-correlation processing
            "acfint": True,  # interferometer acfs
        }

        slice_2 = copy.deepcopy(slice_1)
        slice_3 = copy.deepcopy(slice_1)
        slice_2['cfs_range'] = [11561, 11589]
#        slice_2['txctrfreq']= 11575 #centre  frequency in cfs_scan range
#        slice_2['rxctrfreq']= 11575 #centre  frequency in cfs_scan range

        slice_3['cfs_range'] = [13451, 13499]
#        slice_3['txctrfreq']= 13475 #centre  frequency in cfs_scan range
#        slice_3['rxctrfreq']= 13475 #centre  frequency in cfs_scan range

        super().__init__(cpid, comment_string='Test clear frequency search experiment')

        self.add_slice(slice_1)
        self.add_slice(slice_2, interfacing_dict={0: 'SCAN'})
        self.add_slice(slice_3, interfacing_dict={0: 'SCAN', 1: 'SCAN'})

