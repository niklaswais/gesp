# -*- coding: utf-8 -*-
import os
import warnings

def output(p_msg, p_type = ""):
    if p_type == "err":
        #if __name__ == "__main__":
        print("ERROR: ", p_msg)
        #    os.sys.exit()
        #else:
        #    warnings.warn(p_msg)
    elif p_type == "warn":
        #if __name__ == "__main__":
        print("WARNING: ", p_msg)
        #else:
        #    warnings.warn(p_msg)
    else:
        print(p_msg)