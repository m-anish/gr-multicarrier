#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Anish Mangal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#



from gnuradio import gr

class multicarrier_wbfm_pfs(gr.hier_block2):
    """
    docstring for block multicarrier_wbfm_pfs
    """
    def __init__(self, num_carriers=4,audio_rate=48000,bband_rate=200000,amplitude=[0.25]*4,start_freq=88.0e6,end_freq=108.0e6,frequency=[92.0e6,96.0e6,100.0e6,104.0e6],lpf_taps=None):
        gr.hier_block2.__init__(self,
            "multicarrier_wbfm_pfs",
            gr.io_signature(<+MIN_IN+>, <+MAX_IN+>, gr.sizeof_<+ITYPE+>),  # Input signature
            gr.io_signature(<+MIN_OUT+>, <+MAX_OUT+>, gr.sizeof_<+OTYPE+>)) # Output signature

        # Define blocks and connect them
        self.connect()
