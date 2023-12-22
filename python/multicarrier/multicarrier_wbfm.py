#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Anish Mangal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#



from gnuradio import gr

class multicarrier_wbfm(gr.hier_block2):
    """
    docstring for block multicarrier_wbfm
    """
    def __init__(self, num_carriers=4,audio_rate=48000,bband_samp_rate=4800000,amplitude=[0.25, 0.25, 0.25, 0.25]):
        gr.hier_block2.__init__(self,
            "multicarrier_wbfm",
            gr.io_signature(<+MIN_IN+>, <+MAX_IN+>, gr.sizeof_<+ITYPE+>),  # Input signature
            gr.io_signature(<+MIN_OUT+>, <+MAX_OUT+>, gr.sizeof_<+OTYPE+>)) # Output signature

        # Define blocks and connect them
        self.connect()
