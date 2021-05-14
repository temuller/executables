#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np

def main():
    files = input('Enter file name or space separated list:')
    
    if len(files.split())==1:
        x, y = np.loadtxt(files).T
        plt.plot(x, y)
        plt.title(files)
        plt.show()
  
    else:
        for file in files.split():
            x, y = np.loadtxt(file).T
            plt.plot(x, y)
        plt.title(files)
        plt.show()
    
main()
