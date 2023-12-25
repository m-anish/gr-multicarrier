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

class multicarrier_wbfm_pfs(gr.hier_block2):
    """
    Multicarrier Polyphase WBFM Block

    Generates a SINGLE multicarrier baseband stream from N audio streams.
    By default the baseband signals are 200kHz wide. This block does three stages
    of signal processing:
      * Generates multiple WFM signals from a multiple audio streams
      * Takes as input, a starting frequency, and ending frequency, and
        a list of frequencies for each WFM carrier
      * Places all the generated WFM carriers onto a baseband from the given set
        of frequencies using polyphases synthesis
      * Note that the final bandwidth of the generated signal will be 
        (end_freq - start_freq) wide 

    Developed as part of the parallelcast project.

    Args:
        num_carriers: 'N' or the number of independent carriers (int)
        audio_rate: Audio sample rate of each carrier (float)
        bband_rate: Baseband sample rate of each independent WFM carrier (float)
        amplitude: A num_carriers-wide list of floating point integers to multiply 
                    each generated carrier. Helps with normalization of peak power.
        start_freq: Start Frequency of the generated multicarrier signal (float)
        end_freq: End frequency of the generated multicarrier signal (float)
        frequency: List of frequencies to put all the carriers onto (float_vector)
        lpf_taps: Low Pass Filter taps to pass onto the Polyphase Synthesis block
                  (real_vector)
    """


    def __init__(self, num_carriers=4,audio_rate=48000,bband_rate=200000,
                 amplitude=[0.25]*4,start_freq=88.0e6,end_freq=108.0e6,
                 frequency=[92.0e6,96.0e6,100.0e6,104.0e6],lpf_taps=None):
        
        gr.hier_block2.__init__(
            self,
            "multicarrier_wbfm_pfs",
            gr.io_signature.makev(num_carriers, num_carriers,
                                    [gr.sizeof_float*1]*num_carriers),
            gr.io_signature(1,1,gr.sizeof_gr_complex*1),)

        self.my_log = gr.logger(self.alias())

        ##################################################
        # Parameters
        ##################################################
        
        self.audio_rate = audio_rate
        self.bband_rate = bband_rate
        self.amplitude = amplitude
        self.carriers = num_carriers
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.frequency = frequency
        self.lpf_taps = lpf_taps

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

        self.my_log.trace("Before pfs declaration")
        self.my_log.debug("int(bband_rate):%d" % bband_rate)
        self.my_log.trace("len(lpf_taps):%d"%len(lpf_taps))

        ch_map = self.chmap(frequency, start_freq, end_freq, bband_rate)
        num_pfs_channels = int((end_freq - start_freq)/bband_rate)
        self.pfs = filter.pfb_synthesizer_ccf(num_pfs_channels, lpf_taps, False)
        self.pfs.set_channel_map(ch_map)
        self.pfs.declare_sample_delay(0)

        ##################################################
        # Connections
        ##################################################
        for i in range(num_carriers):
            self.connect((self, i), (self.rational_resampler[i], 0))
            self.connect((self.rational_resampler[i], 0), (self.wfm_tx[i], 0))
            self.connect((self.wfm_tx[i], 0), (self.multiply_const[i], 0))
            self.connect((self.multiply_const[i], 0), (self.pfs, i))
        
        self.connect((self.pfs, 0), (self, 0))

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude

        if len(amplitude) != self.carriers:
            self.my_log.warn(("Number of items in the amplitude",
                         " list do not match num_carriers"))

        for i in range(len(amplitude)):
            self.multiply_const[i].set_k(self.amplitude[i])

    def get_audio_rate(self):
        return self.audio_rate
    
    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate

    def get_bband_rate(self):
        return self.bband_rate
    
    def set_bband_rate(self,bband_rate):
        self.bband_rate = bband_rate
    
    def get_start_freq(self):
        return self.start_freq
    
    def set_start_freq(self, start_freq):
        self.start_freq = start_freq

    def get_end_freq(self):
        return self.end_freq
    
    def set_end_freq(self, end_freq):
        self.end_freq = end_freq

    def get_frequency(self):
        return self.frequency
    
    def set_frequency(self, frequency):
        self.frequency = frequency
        ch_map = self.chmap(frequency, self.start_freq, self.end_freq, self.bband_rate)
        self.pfs.set_channel_map(ch_map)
        self.my_log.trace("set_frequency called")
        
    def get_lpf_taps(self):
        return self.lpf_taps
    
    def set_lpf_taps(self, lpf_taps):
        self.lpf_taps = lpf_taps

    # TBD: Make function compatible with handling Hz instead of MHz
    # This function returns a dictionary mapping of FM frequency v/s a channel map
    # to be compared with a list of frequencies passed to chmap() function
    def make_channel_dict(self, start_freq, end_freq, bband_rate):
        try:
            if (int(start_freq)  % int(bband_rate) == 0
            and int(end_freq) % int(bband_rate) == 0
            and (end_freq > start_freq)):

                freq_range = end_freq - start_freq

                # Each tap is bband_rate wide
                num_taps = int(freq_range/bband_rate)
                self.my_log.debug("make_channel_dict: Number of Taps: %d" % num_taps)

                unsorted_channel_dict = {}
                
                for tap in range(0, num_taps):
                    if tap < num_taps/2:
                        index = int(
                            start_freq + freq_range/2 + (tap * bband_rate))
                        unsorted_channel_dict[index] = tap
                    else:
                        index = int(
                            start_freq + ((tap - num_taps/2) * bband_rate))
                        unsorted_channel_dict[index] = tap

                sorted_channel_dict = dict(sorted(unsorted_channel_dict.items()))
                string_channel_dict = {}
                
                # We convert from float to string to make comparison with supplied
                # frequency values easier
                for i, j in sorted_channel_dict.items():
                    string_channel_dict[str(i)] = j

                [self.my_log.trace("%s : %s" % (i, j))
                for i, j in string_channel_dict.items()]

                return string_channel_dict
            else:
                raise ValueError
        except ValueError:
            self.my_log.error("Incorrect values of start_freq and/or end_freq")           

    def chmap(self, dirty_freq_list, start_freq, end_freq, bband_rate):
        chmap = []
        channel_dict = self.make_channel_dict(start_freq, end_freq, bband_rate)
        
        # Each tap is bband_rate wide
        num_taps = int((end_freq - start_freq)/bband_rate)
        self.my_log.debug("Number of taps:%d" % num_taps)

        freq_list = []
        # Sanitize the freq_list
        for dirty_freq in dirty_freq_list:
            freq_list.append(str(int(dirty_freq)))

        self.my_log.trace("Done sanitizing freq_list")

        for index in range(len(freq_list)):
            freq = freq_list[index]
            #self.my_log.debug("chmap: number of instances of freq %s in list: %d" % (freq, freq_list.count(freq)))
            #self.my_log.debug("chmap: appending to chmap tap:%s" % channel_dict[freq])
            chmap.append(channel_dict[freq])
            if(freq_list[index:].count(freq) == 1):
                #self.my_log.debug("chmap: popping from channel_dict freq in list: {'%s':'%s'}" %
                #        (freq, channel_dict[freq]))
                channel_dict.pop(freq)

        self.my_log.trace("Done adding useful taps")

        for freq in channel_dict.copy():
            #self.my_log.debug("chmap: appending to chmap tap:%s" % channel_dict[freq])
            chmap.append(channel_dict[freq])
            #self.my_log.debug("chmap: popping from channel_dict freq NOT in list: {'%s':'%s'}" % 
            #            (freq, channel_dict[freq]))
            channel_dict.pop(freq)

        self.my_log.trace("chmap: generated channel map")
        #self.my_log.info(str(chmap))
        self.my_log.trace("chmap: length of generated channel map: %d" % len(chmap))
        self.my_log.debug("channel_map: %s" % str(chmap[:num_taps]))

        return chmap[:num_taps]