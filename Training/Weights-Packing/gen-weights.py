#BSD 3-Clause License
#=======
#
#Copyright (c) 2017, Xilinx
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#* Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
#* Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#* Neither the name of the copyright holder nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
from finnthesizer import *

if __name__ == "__main__":
    bnnRoot = "."
    npzFile = bnnRoot + "/tiny-yolo.npz"
    targetDirBin = bnnRoot + "/cnvW1A1"
    targetDirHLS = bnnRoot + "/cnvW1A1"

    #topology of convolutional layers (only for config.h defines)
    ifm       = [416, 208,  104,  52,  26,  13,  13,  13,  13]
    ofm       = [416, 208,  104,  52,  26,  13,  13,  13,  13] 
    ifm_ch    = [  3,  16,   64,  64, 128, 256, 512, 512, 512]
    ofm_ch    = [ 16,  64,   64, 128, 256, 512, 512, 512, 125]  
    filterDim = [  3,   3,    3,   3,   3,   3,   3,   3,   1]


    A = 2
    
    if A == 1:
      WeightsPrecisions_fractional =    [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      ActivationPrecisions_fractional = [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      InputPrecisions_fractional =      [7 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      WeightsPrecisions_integer =       [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1]
      ActivationPrecisions_integer =    [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1] 
      InputPrecisions_integer =         [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1]
    elif A == 2:
      WeightsPrecisions_fractional =    [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      ActivationPrecisions_fractional = [0 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      InputPrecisions_fractional =      [7 , 0 , 0 , 0 , 0 , 0 , 0, 0,  0]
      WeightsPrecisions_integer =       [1 , 1 , 1 , 1 , 1 , 1 , 1, 1,  1]
      ActivationPrecisions_integer =    [4 , 4 , 4 , 4 , 4 , 4 , 4, 4,  1]  
      InputPrecisions_integer =         [1 , 4 , 4 , 4 , 4 , 4 , 4, 4,  4]
 


    classes = ['Airplane', 'Automobile', 'Bird', 'Cat', 'Deer', 'Dog', 'Frog', 'Horse', 'Ship', 'Truck']

    #configuration of PE and SIMD counts
    peCounts =    [16, 16, 16, 16, 16, 16, 16, 16, 5]
    simdCounts =  [ 3, 16, 32, 32, 32, 32, 32, 32, 32]
     

    if not os.path.exists(targetDirBin):
      os.mkdir(targetDirBin)
    if not os.path.exists(targetDirHLS):
      os.mkdir(targetDirHLS)    

    #read weights
    rHW = BNNWeightReader(npzFile, True)

    config = "/**\n"
    config+= " * Finnthesizer Config-File Generation\n";
    config+= " *\n **/\n\n"
    config+= "#ifndef __LAYER_CONFIG_H_\n#define __LAYER_CONFIG_H_\n\n"

    # process convolutional layers
    for convl in range(0, 9):
      peCount = peCounts[convl]
      simdCount = simdCounts[convl]
      WPrecision_fractional = WeightsPrecisions_fractional[convl]
      APrecision_fractional = ActivationPrecisions_fractional[convl]
      IPrecision_fractional = InputPrecisions_fractional[convl]
      WPrecision_integer = WeightsPrecisions_integer[convl]
      APrecision_integer = ActivationPrecisions_integer[convl]
      IPrecision_integer = InputPrecisions_integer[convl]
      print "\nUsing peCount = %d simdCount = %d for engine %d" % (peCount, simdCount, convl)
      if convl == 0:
        # use fixed point weights for the first layer
        (w,t) = rHW.readConvBNComplex(WPrecision_fractional, APrecision_fractional, IPrecision_fractional, WPrecision_integer, APrecision_integer, IPrecision_integer, usePopCount=False,    numThresBits=24, numThresIntBits=16)
        # compute the padded width and height
        paddedH = padTo(w.shape[0], peCount)
        paddedW = padTo(w.shape[1], simdCount)
        # compute memory needed for weights and thresholds
        neededWMem = (paddedW * paddedH) / (simdCount * peCount)
        neededTMem = paddedH / peCount
        print "Layer %d: %d x %d" % (convl, paddedH, paddedW)
        print "WMem = %d TMem = %d" % (neededWMem, neededTMem)
        print "IPrecision = %d.%d WPrecision = %d.%d APrecision = %d.%d" % (IPrecision_integer, IPrecision_fractional, WPrecision_integer,WPrecision_fractional, APrecision_integer, APrecision_fractional)

        m = BNNProcElemMem(peCount, simdCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, IPrecision_integer, WPrecision_fractional, APrecision_fractional, IPrecision_fractional, numThresBits=24, numThresIntBits=16)
        m.addMatrix(w,t,paddedW,paddedH)


        config += (printConvDefines("L%d" % convl, filterDim[convl], ifm_ch[convl], ifm[convl], ofm_ch[convl], ofm[convl], simdCount, peCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, WPrecision_fractional, APrecision_fractional)) + "\n" 

        #generate HLS weight and threshold header file to initialize memory directly on bitstream generation       
        #m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(convl) + ".h", str(convl))

        #generate binary weight and threshold files to initialize memory during runtime
        #because HLS might not work for very large header files        
        m.createBinFiles(targetDirBin, str(convl))
 


      else:
        # regular binarized layer
        (w,t) = rHW.readConvBNComplex(WPrecision_fractional, APrecision_fractional, IPrecision_fractional, WPrecision_integer, APrecision_integer, IPrecision_integer)
        # compute the padded width and height
        paddedH = padTo(w.shape[0], peCount)
        paddedW = padTo(w.shape[1], simdCount)
        # compute memory needed for weights and thresholds
        neededWMem = (paddedW * paddedH) / (simdCount * peCount)
        neededTMem = paddedH / peCount
        print "Layer %d: %d x %d" % (convl, paddedH, paddedW)
        print "WMem = %d TMem = %d" % (neededWMem, neededTMem)
        print "IPrecision = %d.%d WPrecision = %d.%d APrecision = %d.%d" % (IPrecision_integer, IPrecision_fractional, WPrecision_integer,WPrecision_fractional, APrecision_integer, APrecision_fractional)
        m = BNNProcElemMem(peCount, simdCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, IPrecision_integer, WPrecision_fractional, APrecision_fractional, IPrecision_fractional)
        m.addMatrix(w,t,paddedW,paddedH)

        config += (printConvDefines("L%d" % convl, filterDim[convl], ifm_ch[convl], ifm[convl], ofm_ch[convl], ofm[convl], simdCount, peCount, neededWMem, neededTMem, WPrecision_integer, APrecision_integer, WPrecision_fractional, APrecision_fractional)) + "\n" 

        #generate HLS weight and threshold header file to initialize memory directly on bitstream generation        
        #m.createHLSInitFiles(targetDirHLS + "/memdata-" + str(convl) + ".h", str(convl))

        #generate binary weight and threshold files to initialize memory during runtime
        #because HLS might not work for very large header files        
        m.createBinFiles(targetDirBin, str(convl))
 

    config+="#endif //__LAYER_CONFIG_H_\n"

    configFile = open(targetDirHLS+"/config.h", "w")
    configFile.write(config)
    configFile.close()

    with open(targetDirBin + "/classes.txt", "w") as f:
        f.write("\n".join(classes))

