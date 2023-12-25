#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Anish Mangal.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#



from gnuradio import gr
from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal

import logging

#FIXME: Logging!!


class multicarrier_wbfm(gr.hier_block2):
    """
    Multicarrier WBFM Block

    Generates N independent baseband WFM signals from N audio streams.
    By default the baseband signals are 200kHz wide. They can be passed
    onto a polyphase synthesis block to spread them over a wider bandwidth.

    Developed as part of the parallelcast project.

    Args:
        num_carriers: 'N' or the number of independent carriers (int)
        audio_rate: Audio sample rate of each carrier (float)
        bband_rate: Baseband sample rate of each independent WFM carrier (float)
        amplitude: A num_carriers-wide list of floating point integers to multiply 
                    each generated carrier. Helps with normalization of peak power. 
    """

    def __init__(self, num_carriers=4,audio_rate=48000,bband_rate=200000,
                 amplitude=[0.25]*4):
        gr.hier_block2.__init__(self,
            "multicarrier_wbfm",
            gr.io_signature.makev(num_carriers, num_carriers,
                                  [gr.sizeof_float*1]*num_carriers),
            gr.io_signature.makev(num_carriers, num_carriers,
                                  [gr.sizeof_gr_complex*1]*num_carriers),)
        
        ##################################################
        # Parameters
        ##################################################
        
        self.audio_rate = audio_rate
        self.bband_rate = bband_rate
        self.amplitude = amplitude
        self.carriers = num_carriers

        ##################################################
        # Blocks
        ##################################################
        
        # Make empty lists of the blocks we shall later connect
        self.rational_resampler = []
        self.multiply_const = []
        self.wfm_tx = []

        # Populate the lists created above by iterating over them
        for i in range(num_carriers):
            self.rational_resampler.append(
                filter.rational_resampler_fff(
                interpolation=int(bband_rate),
                decimation=int(audio_rate),
                taps=[],
                fractional_bw=0)
            )
            self.multiply_const.append(
                blocks.multiply_const_cc(amplitude[i])
            )
            self.wfm_tx.append(
                analog.wfm_tx(
                audio_rate=int(bband_rate),
                quad_rate=int(bband_rate),
                tau=(75e-6),
                max_dev=75e3,
                fh=(-1.0),)
            )

        ##################################################
        # Connections
        ##################################################
        for i in range(num_carriers):
            self.connect((self, i), (self.rational_resampler[i], 0))
            self.connect((self.rational_resampler[i], 0), (self.wfm_tx[i], 0))
            self.connect((self.wfm_tx[i], 0), (self.multiply_const[i], 0))
            self.connect((self.multiply_const[i], 0), (self, i))

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude

        if len(amplitude) != self.carriers:
            logging.warn("Number of items in the amplitude list do not match num_carriers")
            
        for i in range(len(amplitude)):
            self.multiply_const.set_k(self.amplitude[i])

    def get_audio_rate(self):
        return self.audio_rate
    
    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate

    def get_bband_rate(self):
        return self.bband_rate
    
    def set_bband_rate(self,bband_rate):
        self.bband_rate = bband_rate
