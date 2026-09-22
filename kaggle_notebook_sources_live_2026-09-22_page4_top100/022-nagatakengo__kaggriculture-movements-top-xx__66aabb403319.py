#!unzip -qo /content/archive.zip -d /data
import sys
sys.path.append("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx")

import pandas as pd
from split_zip_file import Split_zip_file      
from kaggriculture_df import Kaggriculture_df  
from dir_to_strong import DirToStrong          
from dirtobeginner import DirToBeginner

#Split_zip_file("/kaggle/input/datasets/nagatakengo/kaggriculture-movements-in-the-top-xx/Kaggriculture_Movements in the top xx%", 30)
"""
This class
wasn't necessary on Kaggle.
The model performed so well that there was no need for cross-validation.
It's used when running the code in Colab.
"""

DirToStrong(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir="/kaggle/working/st_data",
    top_percent=0.01
        )

DirToBeginner(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir = "/kaggle/working/be_data_5",
    top_percent = 0.5
)

DirToBeginner(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir = "/kaggle/working/be_data_4",
    top_percent = 0.4
)

DirToBeginner(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir = "/kaggle/working/be_data_3",
    top_percent = 0.3
)

DirToBeginner(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir = "/kaggle/working/be_data_2",
    top_percent = 0.2
)

DirToBeginner(
    target_dir="/kaggle/input/datasets/organizations/kaggle/kaggriculture-episodes-2026-08-08",
    output_dir = "/kaggle/working/be_data_1",
    top_percent = 0.1
)