import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version as package_version

_EXPECTED_ENGINE_VERSION = '1.32.6'
try:
    _installed_engine_version = package_version("kaggle-environments")
except PackageNotFoundError:
    _installed_engine_version = None

if _installed_engine_version != _EXPECTED_ENGINE_VERSION:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--disable-pip-version-check",
            "--no-deps",
            f"kaggle-environments=={_EXPECTED_ENGINE_VERSION}",
        ],
        check=True,
    )
    _installed_engine_version = package_version("kaggle-environments")

assert _installed_engine_version == _EXPECTED_ENGINE_VERSION
print(f"Using kaggle-environments=={_installed_engine_version}.")

from collections import defaultdict
from io import StringIO
import csv
import json

try:
    from IPython.display import display, Markdown
except ImportError:
    class Markdown(str):
        pass
    def display(value):
        print(str(value))

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

AGENT_SHA256 = 'a7f827b9438885b34b7fd5bf8165458a72f8bb83031a288dd4640f21ade3294b'
ARCHIVE_SHA256 = '47ab26c4ee09eeddcefd5df1de26fb23345a687659c5a94260b7845d21a0aa01'
ENGINE_COMMIT = 'bded87b0d7879078c726a93a4884d044f79c4eed'
ENGINE_VERSION = '1.32.6'

games = list(csv.DictReader(StringIO(r"""panel,target,seed,seat,margin,result,invalid,timeout,unsold
Reproduction vs historical public strong agents,kaito_v23,101,0,2952.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,101,1,2952.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,211,0,2997.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,211,1,2997.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,307,0,2131.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,307,1,2131.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,401,0,2746.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,401,1,2746.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,503,0,2978.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,503,1,2978.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,601,0,2237.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,601,1,2237.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,701,0,2139.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,701,1,2139.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,809,0,3014.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v23,809,1,3014.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,101,0,6498.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,101,1,6498.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,211,0,6268.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,211,1,6268.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,307,0,5295.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,307,1,5295.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,401,0,2248.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,401,1,2248.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,503,0,5192.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,503,1,5192.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,601,0,4895.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,601,1,4895.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,701,0,4997.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,701,1,10071.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,809,0,639.0,win,0,0,0
Reproduction vs historical public strong agents,kaito_v22,809,1,639.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,101,1,6498.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,101,0,6498.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,211,1,6268.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,211,0,6268.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,307,1,5295.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,307,0,5295.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,401,1,2248.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,401,0,2248.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,503,1,5192.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,503,0,5192.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,601,1,4857.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,601,0,4857.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,701,1,9824.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,701,0,4997.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,809,1,639.0,win,0,0,0
Reproduction vs historical public strong agents,andrew_v22_terminal,809,0,639.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,101,0,11055.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,101,1,11055.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,211,0,9715.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,211,1,10408.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,307,0,9715.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,307,1,9715.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,401,0,7756.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,401,1,7660.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,503,0,10408.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,503,1,10408.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,601,0,9129.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,601,1,9129.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,701,0,8943.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,701,1,9788.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,809,0,9432.0,win,0,0,0
Reproduction vs historical public strong agents,v13_r3,809,1,9432.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,101,0,11659.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,101,1,11659.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,211,0,11293.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,211,1,11293.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,307,0,10541.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,307,1,10541.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,401,0,7327.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,401,1,7327.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,503,0,10562.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,503,1,10562.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,601,0,8687.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,601,1,8687.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,701,0,8441.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,701,1,9260.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,809,0,9892.0,win,0,0,0
Reproduction vs historical public strong agents,rayk_v21_impact,809,1,9892.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,101,0,7873.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,101,1,7873.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,211,0,6375.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,211,1,6375.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,307,0,4296.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,307,1,4296.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,401,0,6835.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,401,1,6835.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,503,0,7898.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,503,1,7898.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,601,0,6288.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,601,1,6288.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,701,0,5059.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,701,1,5059.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,809,0,5064.0,win,0,0,0
Reproduction vs historical public strong agents,indar_verified,809,1,5064.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2707,1,5140.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2707,0,5140.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2801,1,4202.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2801,0,4202.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2903,1,2090.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,2903,0,2090.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3001,1,4706.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3001,0,4706.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3109,1,2553.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3109,0,2553.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3203,1,4810.0,win,0,0,0
V14 vs base reproduction and public agents,andrew_v22_terminal,3203,0,4810.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2707,0,563.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2707,1,563.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2801,0,825.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2801,1,825.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2903,0,2184.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,2903,1,2184.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3001,0,2210.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3001,1,2210.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3109,0,3586.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3109,1,3586.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3203,0,3179.0,win,0,0,0
V14 vs base reproduction and public agents,frontier_v1,3203,1,3179.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2707,0,6814.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2707,1,6814.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2801,0,6398.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2801,1,6398.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2903,0,9735.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,2903,1,9735.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3001,0,7867.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3001,1,7867.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3109,0,6477.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3109,1,6477.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3203,0,5923.0,win,0,0,0
V14 vs base reproduction and public agents,indar_verified,3203,1,5923.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2707,0,5140.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2707,1,5140.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2801,0,4202.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2801,1,4202.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2903,0,2090.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,2903,1,2090.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3001,0,4706.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3001,1,4706.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3109,0,2553.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3109,1,2553.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3203,0,4810.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v22,3203,1,4810.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2707,0,2661.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2707,1,2661.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2801,0,3880.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2801,1,3880.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2903,0,6296.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,2903,1,6296.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3001,0,4255.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3001,1,4255.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3109,0,3715.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3109,1,3715.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3203,0,3883.0,win,0,0,0
V14 vs base reproduction and public agents,kaito_v23,3203,1,3883.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2707,0,9982.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2707,1,9982.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2801,0,9028.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2801,1,9028.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2903,0,11381.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,2903,1,11381.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3001,0,9174.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3001,1,9174.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3109,0,8285.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3109,1,8285.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3203,0,9957.0,win,0,0,0
V14 vs base reproduction and public agents,rayk_v21_impact,3203,1,9957.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2707,0,9063.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2707,1,9063.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2801,0,8195.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2801,1,8195.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2903,0,10207.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,2903,1,10207.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3001,0,9236.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3001,1,9126.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3109,0,7972.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3109,1,7972.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3203,0,9830.0,win,0,0,0
V14 vs base reproduction and public agents,v13_r3,3203,1,9830.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2707,0,3225.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2707,1,3225.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2801,0,3638.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2801,1,3638.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2903,0,6181.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,2903,1,6181.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3001,0,3811.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3001,1,3811.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3109,0,4031.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3109,1,4031.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3203,0,3917.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90897351_s1,3203,1,3917.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2707,0,4283.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2707,1,4283.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2801,0,3745.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2801,1,3745.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2903,0,6104.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,2903,1,6104.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3001,0,3840.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3001,1,3840.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3109,0,5460.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3109,1,5460.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3203,0,4502.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90899851_s0,3203,1,4502.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2707,0,5802.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2707,1,5802.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2801,0,4588.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2801,1,4588.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2903,0,7271.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,2903,1,7271.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3001,0,4109.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3001,1,4109.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3109,0,5575.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3109,1,5575.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3203,0,4506.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90900709_s0,3203,1,4506.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2707,0,3440.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2707,1,3440.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2801,0,3207.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2801,1,3207.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2903,0,5495.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,2903,1,5495.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3001,0,3644.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3001,1,3644.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3109,0,4531.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3109,1,4531.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3203,0,3384.0,win,0,0,0
V14 vs untouched Ueddy replay proxies,ueddy_holdout_90916074_s1,3203,1,3384.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3301,1,2200.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3301,0,2200.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3407,1,1400.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3407,0,1400.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3511,1,4572.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3511,0,4572.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3607,1,2556.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3607,0,2556.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3701,1,3061.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3701,0,3061.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3803,1,1778.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90915110_s1,3803,0,1778.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3301,1,2556.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3301,0,2556.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3407,1,1599.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3407,0,1599.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3511,1,5234.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3511,0,5234.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3607,1,2242.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3607,0,2242.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3701,1,2512.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3701,0,2512.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3803,1,1877.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90918455_s0,3803,0,1877.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3301,1,2817.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3301,0,2817.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3407,1,1277.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3407,0,1277.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3511,1,5218.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3511,0,5218.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3607,1,2861.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3607,0,2861.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3701,1,3306.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3701,0,3306.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3803,1,1759.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919309_s0,3803,0,1759.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3301,1,2693.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3301,0,2693.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3407,1,1158.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3407,0,1158.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3511,1,5171.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3511,0,5171.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3607,1,2819.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3607,0,2819.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3701,1,3371.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3701,0,3371.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3803,1,1826.0,win,0,0,0
V14 vs later-sampled current CemBas replay proxies,cem_current_90919334_s1,3803,0,1826.0,win,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2707,0,-10584.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2707,1,-10584.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2801,0,-32486.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2801,1,-32486.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2903,0,-9340.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,2903,1,-9340.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3001,0,-34365.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3001,1,-30175.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3109,0,-4864.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3109,1,-4462.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3203,0,-32596.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90851845_s1,3203,1,-33949.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2707,0,9703.0,win,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2707,1,9703.0,win,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2801,0,11814.0,win,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2801,1,11814.0,win,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2903,0,-5434.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,2903,1,-5434.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3001,0,-25291.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3001,1,-23484.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3109,0,-14242.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3109,1,-14242.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3203,0,-7075.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90893264_s0,3203,1,-8156.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2707,0,-25056.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2707,1,-25056.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2801,0,-45405.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2801,1,-45405.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2903,0,-23112.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,2903,1,-23112.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3001,0,-45656.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3001,1,-45197.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3109,0,-1367.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3109,1,-810.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3203,0,-51651.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90914286_s0,3203,1,-51651.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2707,0,-11824.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2707,1,-11824.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2801,0,-1118.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2801,1,-1118.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2903,0,-46070.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,2903,1,-46070.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3001,0,-45229.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3001,1,-40532.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3109,0,-22758.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3109,1,-22758.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3203,0,-29295.0,loss,0,0,0
V14 vs Seb alternate-route replay proxies,seb_holdout_90915190_s1,3203,1,-28820.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2707,0,-52337.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2707,1,-52337.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2801,0,-46960.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2801,1,-46960.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2903,0,2033.0,win,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,2903,1,2033.0,win,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3001,0,36691.0,win,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3001,1,26194.0,win,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3109,0,-17136.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3109,1,-14819.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3203,0,-1619.0,loss,0,0,0
V14 vs wangtf96 alternate strategy,wangtf96,3203,1,-1619.0,loss,0,0,0""")))
dev_rows = json.loads(r"""[{"variant":"exact_p50_b12","games":12,"wins":12,"losses":0,"mean_margin":1548.3,"worst_margin":498.0,"paired_positive":6},{"variant":"near_p100_b24","games":12,"wins":12,"losses":0,"mean_margin":2368.3,"worst_margin":797.0,"paired_positive":6},{"variant":"near_p200_b30","games":12,"wins":12,"losses":0,"mean_margin":2447.0,"worst_margin":804.0,"paired_positive":6},{"variant":"near_p50_b12","games":12,"wins":12,"losses":0,"mean_margin":1640.3,"worst_margin":498.0,"paired_positive":6},{"variant":"near_price50","games":12,"wins":12,"losses":0,"mean_margin":1842.0,"worst_margin":277.0,"paired_positive":6}]""")

for row in games:
    row["seed"] = int(row["seed"])
    row["seat"] = int(row["seat"])
    row["margin"] = float(row["margin"])
    for key in ("invalid", "timeout", "unsold"):
        row[key] = int(row[key])

def markdown_table(rows, columns=None):
    rows = list(rows)
    if not rows:
        return "_No data._"
    columns = columns or list(rows[0])
    header = "| " + " | ".join(columns) + " |"
    rule = "|" + "|".join("---" for _ in columns) + "|"
    body = ["| " + " | ".join(str(row.get(column, "")) for column in columns) + " |" for row in rows]
    return "\n".join([header, rule, *body])

def summarize(rows, key="panel"):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    output = []
    for name, panel_rows in grouped.items():
        output.append({
            key: name,
            "games": len(panel_rows),
            "W-D-L": f"{sum(r['result']=='win' for r in panel_rows)}-{sum(r['result']=='draw' for r in panel_rows)}-{sum(r['result']=='loss' for r in panel_rows)}",
        })
    return output

assert len(games) == 336
assert sum(row["invalid"] + row["timeout"] + row["unsold"] for row in games) == 0
print(f"Loaded {len(games)} evaluation games.")

display(Markdown("### Development-Set Parameter Sweep\n" + markdown_table(dev_rows)))

selected = next(row for row in dev_rows if row["variant"] == "near_p200_b30")
assert selected["wins"] == 12 and selected["losses"] == 0 and selected["paired_positive"] == 6

gates = [
    {"Parameter": "clone distance", "V14": "<= 6"},
    {"Parameter": "active steps", "V14": "120–679"},
    {"Parameter": "premium products", "V14": "STRAWBERRY / MELON / MILK / WOOL"},
    {"Parameter": "minimum next-turn SELL", "V14": ">= 4"},
    {"Parameter": "maximum shift per product", "V14": "30"},
    {"Parameter": "selected variant", "V14": "near_p200_b30"},
]
display(Markdown("### Final Activation Gates\n" + markdown_table(gates)))

if HAS_MATPLOTLIB:
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    boxes = [
        (0.3, 2.35, "Base action"),
        (2.2, 2.35, "Repay t-1"),
        (4.1, 2.35, "Rank base SELL"),
        (6.25, 2.35, "Clone gate"),
        (8.05, 2.35, "Append shift"),
    ]
    for x, y, label in boxes:
        patch = FancyBboxPatch((x, y), 1.45, 0.7, boxstyle="round,pad=0.08", facecolor="#CCFBF1", edgecolor="#0F766E")
        ax.add_patch(patch); ax.text(x+0.725, y+0.35, label, ha="center", va="center", fontsize=9)
    for left, right in zip(boxes, boxes[1:]):
        ax.add_patch(FancyArrowPatch((left[0]+1.45, 2.7), (right[0], 2.7), arrowstyle="->", mutation_scale=14, color="#475569"))
    ax.text(5, 1.15, "turn t: append SELL s   →   turn t+1: scheduled SELL q-s", ha="center", fontsize=11, fontweight="bold")
    ax.text(5, 0.55, "quantity conserved; timing changed", ha="center", color="#64748B")
    plt.tight_layout(); plt.show()
else:
    print("Base action → repay → rank base SELL → clone gate → append shift → next-turn repayment")

panel_summary = summarize(games)
display(Markdown(markdown_table(panel_summary, columns=["panel", "games", "W-D-L"])))

expected = {
    "Reproduction vs historical public strong agents": (96, "96-0-0"),
    "V14 vs base reproduction and public agents": (84, "84-0-0"),
    "V14 vs untouched Ueddy replay proxies": (48, "48-0-0"),
    "V14 vs later-sampled current CemBas replay proxies": (48, "48-0-0"),
    "V14 vs Seb alternate-route replay proxies": (48, "4-0-44"),
    "V14 vs wangtf96 alternate strategy": (12, "4-0-8"),
}
for row in panel_summary:
    games_expected, record_expected = expected[row["panel"]]
    assert (row["games"], row["W-D-L"]) == (games_expected, record_expected)

import base64
import contextlib
import gzip
import hashlib
import importlib.util
import io
import tarfile
import zlib
from pathlib import Path

_AGENT_B85_PARTS = [
    'c-',
    'qZ<XP2T()A0BG6*`6oble+IL@#r|j5+UF5fKqZK!RC+`%5rR*lX`Mob%3y9i^+PtE;Q3D>SojZ*N^V@Q+PqB%a#)ri{#On5q7i76nC>HCp9F!6',
    'xyVViOoj_R+j3Fg8hMR-Cpnelsh{0QvdjM~-',
    '9osf`k*HlCV@vW+rv6&o$C7~4!1S2lId*c6qT@Qh6sHC6vIr(}J$$=)0)Q%n8fk~3)hSjnu+DRY4nl!;9hC7(izGAFP$MVqWRMKMVKwAq@PpmI',
    '8WUSv7i;74KP4WpR!ByGa$54(u}ht7*A`*@M2c-xjS7bsDjY;r4z0?!$X)6qGa@o_6j2e-BGO2sD1hC~GR-4cOL^@qyHD^AeqD07_-',
    '%`=psNj7m}PCT`7f;qRoUY#*Uz6w_P`Qz>F?T1cUlvUe=QkY=i_Kg;${q6HY5ry056{XH^pAS4Y`SIfinaZ?_wQ9>2Ga-NSA~jV2WANux-',
    '?5dkeg&|||D1$S<KdJ6{)hI-%V;e=Av~yi(gh}1;9S6KAVSrcqg3~g6|54PwBc+vp8<q)slcCR{$f*$@)!F#&(&KVrbln!+9F&U9r-',
    '|f5K9H!=c4SJtPgt_;fIGcT41tM?<E2BvlLz82k?nFSC1v1m)Va3xw&IJs`ny{%B3Pv5m1it`4B5}p1emTPrLS3xkOIqI)|MT!*Qk2XA{l2{YZ',
    '!4NwNW}sralum*T!I6C6i8b_k&T2~a~j^N}mE-',
    'E?OGh3SwRduW*8Jir{yphXXf#FPvvIJJi88}s`FBhvK58IB!Pg_~TGAyn>cTcL=(t9lmRW|BTtWwOb;hLp#L#^>V+R7ov`HL3P;JD=CtZH1Hb1',
    'cjCc!nsV>j)Q`|r7;t%oR96X6Kg+Z%XL39NzpBS?HeB$dFPlUSNlo!kTW!njIQb7cq^RoRNuXy?_y$sLN{ogspfX=Hr4YwsdB#P8dE_Jc#tva9',
    '4Yk5-pVGi_3b>fS)Kv>h0A(Q=JsI@Q3YbIaMeBB_eI0UHYB3KUYjTfS`?dbvwL4Vh8KsG*{F0JClj^QKrTS`Wj2WO8_q`tq@q_0Gp=mH-',
    'h<fA&{<SA=PVKjBOsTa5+PsEhj!YTwcDLt9YBXN8fVaXdwiNkn@PXWY}MPjO4WJr^%lDxxq``wcfSA?Z%^}T&H?QWCGx(QV>DfW^_Yu3rXZ)cz',
    'MDg(LXmT%7rk`_#%moX+8&$;`Y<GWYFCI8n|VcbXtdJbw%a@mHO7)Vl3imv$Ec!>kO?uW1{4>EAV6{J?HqxGZ>&h5zi>=P>KF%PNQ}!v<rPGS`',
    'AEf?-Ymy#q7ggA2CI0z#N$jVrbS}eOTkSCj;Ta`R?2RV;p`k5cz{!(>Ju=hUEo897+h-',
    '3(_ku0`y+VuH~}$?&A8X)QZeJs1CCurc1qehM7bloqg>xEln6Y@H%i+;FO=XnI}bCP@LN|qy7&3!E><Rok<q%A9=Enh>_RbPe`%_LNFY8e0f|G',
    'fJ4Q0a!Opu8qq4Ty>}Fs#+*6bJv{%C~olgBEwEda9e`m*=@x99A;!R>iV*TZKh_9H_d@PcQXbnjoRH-',
    'fx22LNB#YxR^9IYz*-b7RK=~j?N`P70H$QsN#cSsk)YIbs-Xu0W(d$>ui)i8Rj$0lAppn4T=A}^d*D4HTtoRp*6jnpDMWHMB)SLLIAU|;190lP',
    'XlVM4b=j#avdFNJ({=oxQf?Z!D+a_1cQVHn)QC3LaF8h`^@DGuKeaPL`yOtfLebD%FuTs^?UQm!P-T5fc`MQ9!*C-',
    'kLXcaZ(<TGMrtTe?b7H&yV>8{??J1{Dg}6DwNFpJ(yTsE@iJ*-v6&8HbW9@~|d@$vGc@NA-R;Jj?eN>1HI@iyU{=P-',
    'u|zjMA%U9#Ip6e#5&cfXOu$^adNLRv#}rczfJC^z}CTxHo+CX@kn593<HxdR`q;Whyclud>W|%r?P7Jhu0wAR@DH#KYlLcsJ@cy3RQ^&A}PBlN',
    '!j}2)@*zK?lhZp0dBH`m_UltghK4M`c~Ey%1X}jaE1^JT+X0_|8WL>qs$44TigdzZ`QegfcQMjP;X(Z?B@8ZISfHu?o9VJJlEyt8^j&f?ROTr}',
    '_8+Rm=s;7cQ1O_W)_-rf0|DC6dDvYkt;&N8NTEp%0^du5xN-GKH!Wn{tE<h`q9S@UA@0xxURHR+2JNdW+A<w3;eZPpR$9v*z~VI$BHlYxNx&5m',
    'M)~v|k*ze72H{q}H&S3@@5Kj&uN<VU6obBDVx|V~vCov+k5zU<IY&_P3{Qb#q}oc{$qZmKI%gq$bg1*u$*V7^~Hjmo%GCwHU28+IMpMdT&)(c1',
    'aBPvnMddj}iAi<kKpdkp~pAwPJ1s2%Cvdi)nSP-',
    '5EgkGgj;`5o}lqAW>pC0wSqZAxcKT9oBcl@EFPV*j=mvoE(kuPCNH^@v&=<DZ5HASgWo=n9G}-',
    '!QFE@qRl0A=viS~U?86x1>rP2u~e;*P{Va720A^Wx7NsFhd#T7?NK3EJPPT>9&&YRmGrjcKcpD6%9a`u)A!qbZPH&Di)=^1b&GQqdq>(4+@BJx',
    '>*!B*ocodB!P4$lu}AC>@)&3c%_F@TsmB>A<SKD~yWn7^Nvggb$}*X8rCvuii+XYh)w5nQ7>5CrIp@37?6mZj9qvKvG<PycWuH%aoKlaNdtE*_',
    'ud_gJFhV$c$7;L0>C`D|+p2UGySsoFsgsu8F+-',
    'ny5CR1X)%DKdE%0H~6AbkE+DhiV>*jinX!@SUz4SZ~!;g!^w9+1>JPWFtZgTO=>KLM(L+mv5Nmys(4+fk2um&8O!Fps--G&j>V^5D6EvU8l>1s',
    't}*-9-',
    'EPI(W#%@jk0I2jCrlydac@NzGUUdEZK!YHd~F*+)rC284HOT>^HgnNVSC|cl`&RMvZojDaLd`hInGN~3oFI+uAm2m(^9BYX$m)ret+K(>^!Cfv',
    'rY)2eRRMy-DFA$(w+dj3A*VD7s0L9L^1L%hQ5SGBu{gx0GmqxmEIL1TCT2F}7i28DM>|fAKTgb;#EqgHC@P)f6rz<?T3^){I7o%p=&)SCz_Hb-',
    'hmBv=p+ME6&>KuhGb7)$nH#6d}NA~OBS&x5IxCCZner{B%FA6|Mh4<X1k!(qHCfo$0!J2D`!o^^>pk!boQi8U<B|MXa{?h9SksU~q#DR9aNMpg',
    '3Y+j^PxETxB+dzPccn4@CFLzKeL=FM5bu1@R9+a4)hhuG=CD!Bhfb)9OtHNMJ<PSkli38M>w%^l@9<&Y6u>UA+3&SMhs~$Y{b%FNp+CER3Zq}k',
    'w-',
    'Z|^%AbaF6CcDGJR!(;)eAlHfe#I?;^IALAoderY0O}{BUb@xqQ_^J7^fv}5OgGM}pz8Aka(i($wD*aeV;q&lb|rUqK_LdrPRB}YIY$HQ5mEF{O',
    'MO?_lgzfp9)D~VaEGaut5zc1wLVZuUMiE;IKQxm+L$W&$4q|B=7VdgnQNBMZaZ>r^)u6<Xm=?L4>*o&K9cECT_D$#pe4}tO4SoP+^q(?(=HuwE',
    'qZ<XqHk|_Sub&jxic$!dUrVSm%NHk`1E`f3S<HV7CV(_XSdRGL5`6}=rXgq)1H|XiW#n_E(%nsMzFrin9H(@SRhv4C{TOdScq*WL!^QJYC|tNN',
    '+8<@SbMpgP@J*o21Mh7NDEyl1zZxaQZE>-Fi7UY(-',
    'MK90o^!Q+7)1T%*e4P!_`#<M8ZqS4vD+jI$v_+SC9y$r@U*Dk%SyAOB1xv!7GT%vq=S}G3gRL$lH}%U%E?`M07)}_C74q@g2Pl1sTk^{j{?#c~',
    '5hR6vu5lwmHlt7g$QpB(kvf1eSI$YIn4c5Odsbd=u}Em`9ju)Q-',
    'f8T07WN`teQ*vTJb01xvZqwy@BuXfgmcYjxar#JP?hC<@z2PDnGvdCqhLo=$ocDduZfu-',
    '}+xdS{2Ytx8ypa40KvlZepKB_ywF9jaW2&4b87U3D70HR3#9_}CnYr+|K_i#FDa)dIVu<%@j=rP_z7!%;~PhitIOtz~GqSqETco8kAtOJ2__Co',
    'S}d3KzOjb{B{>DZ5nBhYWh1Sxj8O_FZR^h9j3ALAv99M_zQDBgMhsGJ(qeculQF3#Y6wVbWVJ(wm0^(bf<VBZtGv?>GbknRW|m&q=bnb{^n(?=',
    '(uNNZTJv!(|N)3JSggMFDY$m2-*OQ?01$WDghW{e3&rj-$iCwB}C_<uR)T%AsbnotdPx)c{`|Y5$_0O#oibUXLoAGZ-',
    'd{JlCu#u9`ME*8R9&rQ&X<%SqSg*-6uN;n(YW&Q&NUTK+)x>`UwCe7wBg7Wxw$WQ(qL3>lSz!%;Qta8T#;A|2U{gVWPt1+I%OdQR?>aTs-PTJU',
    '@vMmTiI`_e8FW^k`F+Hq~L7<ysj(kkogxVOVZE5se#^Pz-',
    'w=^YlW&nNlSf;n#1(^Elk2)WJ#&?LpdxEyf@CN02*$De1AAuzr4vg5Smld^$xxjYp60~Dk;xibjJ3brrCH*Ah@d;AJ)PY$L5MlP<LJ~lJ<WIW^',
    'MWWrC#WG|3TH@dZi9WT-?1)Spwu$+@rF)VpzEHm^c=SRG>gU=#NE;739rX#7clX3dimq>ZoIaGsU%)eCDT0-',
    '#!#h%c`{Sj?&_SDXv`G(!^$kHlOSjNxWYE`W-7yE<iMf3Ufse@$2(}vZpvNvo?=U9?!BsvJNu`At(F!1<GD_;~oCXc7yqJJ1|8~8d{@t-',
    '8VU996cb`U!l(inT#T?SN6t9CsGyHcLqR?PQTjh4T+;cL@GyV7$mOQFil%NM#17md0ysrfFgE!4aW$+e8o2`?*iqJ~mTR45hwU;`TtoJXy-',
    '3rb+F7}?Q<0#El($3ex%R*r`VJUqDY{beSMbJ+g0n>P!S<1FiIcG~;&<&Z^Ttx~CF$#5zO$KaM2)z&i%j6=Rfbsp(d`d)m$;DO4r5%CTkgQUyT',
    'V#jd`Cm3kv5JFC8<$PRq%ZPv3s4^lKOYaMsW{+0W>5Dd8PP|ZTaN2d25T8hUdv15ZaYTB}aeLiM4l0R>M=G~f*Qhhec<s=6lxeIYSTuR22Sgny',
    'px`hoDr+PVCH8?W6Xl#;Lb!BFq)^oy7dDncp$w<TITFP&4(~ATE_VaRM!B<0AQ0*&we%Dl&QXTuBeTibU+<rpDO$wx(E}!?8pr4bs$tIfj80dP',
    'va2F3V{AGL`K$ACXN5X7@7_-',
    'kR4TM~2BOt|G41k%wm@&Ibdge60^o*bcP`J+GA|I#fd4RT^io)W%K&(JZnukGs=L_o1C^{To9APtB|BACnXeb3Ymf`Cm?p;b^O+*L>K3HSaub$',
    'vdc+#eAY^v1+&G&aaRb1Cte=mhkkh)L3Xxt1W3>(G3U=}+;J0Vs@hRV!^?Qdkt(FFQUKgql=Kjp$>|mlZcXI&6_DOX-pOzxS-YGIUUJi1(z(wG',
    'Gucj*wK)VvINGI*1*cjEA4hLNX3Jg8F5_fRLl=ZB!9L9U+W-',
    '?M85Q${cJIJS?z|IlKw#(<Eer_p;V0;vF0psyN%`2H>9xggal4@{ETByhQ%gB?9=i1OL9b2@Vr)p*;HoF<0i}m*1xy>=&CFeAbW;AG?29jQ6)u',
    'cvf250Jr2ITFzq)e%hK1}1ei;AwCmte9m-!qL!xfxi@m^I`8Ix>_@<<`xR=1ufc-jz2|ZMv&UJ>3D~v((VHSpdT^w%KJ$zA`v>G)Fw-',
    '%48zvg?l#CjT3<p{Q!(l58bGS*j=6~;^$%SC<n(+Q6=ik*L#KjkY`~$of*V^g%Xp<i_zMFWXe-1AXQiW{e{dEX)w9>$*5RciiJ(Aw3HpAgu-',
    '74FB~h6HY=<gqB>#Dv8hcv^tm5_Q(K}vuZdegPue@txvy-;5LdgfsmJrqq`K-',
    '+RBZ<N7hDf<uA_LNk9M%|K*{EX?3x(2nPNQNaH`FmTdqXV`qT|hys!`PRzhkPOz!exvT>APAd`#E2i<KiJn5x7Xd>XrkWmGK55X~ip=0Bzqa5A',
    'Jh#;&oCFmqqVx5Ycp|BW&JIMKEP)!%(`2dw6xoLL^fR|(+$)a)Ro~W?nb3B9M+sY27d%fkk%}=t9eZn0P=ct0S9ir32lKujlj+ON|Z|!VD<i=O',
    'zo1R4@nc-',
    '8#3pEMTDImC6q1i@q&<^)BW;LtmxisC%FEr;FwWr3zuDw($b~BkRQKP~XFG<lzD(NRKp5`RLRmg@5o#kAY3OUao)VkfV9X8JPj(hAJAb8ZZWYb',
    'i*leGt8Jh+!@lxoN2u70dc(!*jD?R6=*=pUfPM!~*DC)2zSBpSm8i?n*dB|2xkqi|AP29T5-%=Xv2t#-',
    'x+1@Sll8Y?`_rYo`*Lv!8&N1TLm+My)6^QdFV_0BEt9#4zD8Lvis{&l{IEfOr#Ij|nTJv%DtoJn$IpNn9*q_*C=8^JBiPDOsUqVjzL^K6JlP%C',
    'D_S~`AVcdgVZpUy1{BQ4OfA5TFsR1uU=b?0^zRnWT!I7O@pfn_*QZL?Utn)fJ&so<*Tb)MNF?)0t-',
    'E{ym01O%H@iQysD+e!PZo3qzYSFns!kPI<69qLZ$JnquP02yY+0irt%H;!CKlM8-URs+i<7swTh+v*xC;Dl64%uA=1wrW-',
    'ug<}Kq9jJjAa+F5FP}QlH-ToLH2#o91&Zvj^Xdjxc&!rjG_J*c~U2~Q6wp1Ursd~G+VmFkvA9vXd7xu?vs5_16sZB?Z>NY?rr4%Nyj7CqHb|#j',
    'KrJ*Aobvpa)aXL{2$o`61Rp}KW!ZUbuR<gl~Lm{0_x!kDbrmQLt3NE<A=4Q>JZW*<O6hU2*zcVk#4{(M?(`kINC6hsh@i>D>Zs)EHAWt-',
    '$AxBCefp5e`X4+B``+f)*+E<fhvsa1uLR%_oZ*{}DqRdIzECdcuT;fO}_Gz(_&2PNj1FvR7JihYmV$)K0Gh6I)r%Mlxgm!)i&&s1}qvG+OsbHQ',
    'jq+*xuiB0mOHpZ)D)we_v>oB`LxTJ)b>l}8BTJMh~EmZ}M4&Op+CdzOJP%u(0<E;#x%(4+Mx<x=P4b=oRljj{<sp6N{!=;+bYGrqnh@Cw#<}yA',
    'hlBgufP%(4Lvo#;PB<PavWbgqz+%ssYCLQ&df!RdKW8>7T4%-',
    '{zlnpixt@35ZhiKiZoz7Z2sCrZTNy9%0ZatmaurRH7FiL7dkkZP#yiND4am?=B{lQlB4KISDKJF_8(NV82l>y^D@%X_t+0hx7HbHy6OUpUUMa!',
    'Eb<eBY|9apyJu_NV?9Y9rRM1zZ{w05|2<wXc`Rl{5;*95T{NEcoHT4_Z$LwjgiK}XfeVGzp}c23!;^)w>0D4w?VwKO^;q+Vh&DM`*<Za;TKGR<',
    'bp9f|-',
    'U49_&HRY#CX!`dD=;nk^sxf!mOnrFbHtCLb6`#tM%FS7*%V&&@ATFV0M6*jE2$`3E~${bk63gt1j?3K?<gFDRRhRjlpPTr+DSlpZEVQg~BkLme',
    '_UW?jFm?X>RazF)_!lV{r!SF1hweqzQRF=x#@GQB5C1>1|_oqRO&A_o{b&&xvYOqpc_85{Bm_{5f*J-3XEn*@Z-xL~Nw?w0nt)t0RoRwj9a-',
    '67z=91}2@kTF{JGVqRkjkzTIG!&Ja+KU4gTeWpuGDJUpxoI<vduUVnVsP!5>0Ot6FxrSmhE+XvaMA@VK`sTOx@K;L<*IfBYVC~&PR=KC=4}ACs',
    '!%QtfD9HC^V`pw>tuCqpgvi#^s?b7aet5*>Ynb&Po6p4R-gEw=z}eYVIOsSCT_5X%VSiPeR(TT<?sP3Z#yQtypu2HyGX1Op$h{qQ{QJ6j|5-',
    'F5d`YsEF*vy`;>lefN&T4jeLP9I5OwF`AaVC_djU8xogY3dm-|`a!~3<l)E}+@BKOnk&9sXX~TXAYtze@_1a1gs~}-',
    '>d#W`(5azk{Z*G%LyOL7(MP)Nu>;mWI(o`n$%d7zN<*#jG&Awg_yve0z<JrN#uGH<+Odr-awzw`Bg2g0V4#tY2lJI^(Sy2M2aw#m=;JWH3AbG6',
    'd0ZRTrXqs$O4|^MPdv3w)syjNd(K9<$-C>Z12?VU2Pe2n5QCX_nr~|E%<kYG!0koQ-',
    'U!KObswnAl1Ep!wd&2|9Gm90q!V3aH*tQ>d06zaje{M`UkwfS%WN<0OQMtqAI@jhd=m-a^+DRB1ihI88ND1}U@MHPjYgow*b8-',
    'DE)>N*LutyCox%k@e@V8AC7(}<aDh=k544W8i&V(>a<y8F>=yPF9P6bk^W>2r*ygs_m6%0qJuFF8B30Su5ap7tsFkDQYgE?TiqI)=LOd0j3a4>',
    'hrs__iqV!j=fCYW-wmSk4j3b<*-5X$?6Vn7;17~70gw_GMwL6bIAwQCH@RQ{_R&uvW;rb*mtQ?ayR-',
    'y{6NU<~t4;zh2Ne$HId!EQ3XY`nlbf&JMzbyF|Gdo;8ROVXD9oU~Yt4gNP*yyKut+Hhf=U8ORiy3Ngawv;4v*`qzVIGwmwZ@soaJj!L`*r|Tbu',
    'r7*B~=YHo!;dl4EtIb-QI7(wR;Pk9ISeDgM(RTqU6ugW+c~3<JP#cYR*f0wNk3NgAMW2+{)5v;ygE<F6`2zm&b#D=d!2vX=Nkg!9rk4W&;bjl5',
    '4fVUWD*UKn~OPRU!~Z!I{RKd$Cf#)9@%*nG1*-',
    'm4)~H!cyo4HYIzhl^>Q|psyHZ<r+a86N$WsTXuSh8jtmc)pc{#@6(4Wb!vAdG%$@o>6WKm_ifH@C%i494h&=R7+=pdwzXI<u+8gBtTyaEWhR0}',
    '&%(D(p1B3MXyY?i<K)YGLNFh<uR`uVo>b+`V5=h1lB@Q@?J^x9+|ebbZjf1TQKfoX_yScYc9wAL_j4)JEqcxij|+kv=@ajpaYsq?xB%y_k`cSd',
    'Ld0EBYpv7RcLFmPA;?xdy{%OAY=adAS@R1;ISsN)33Kh6jVR*ZWTIZ?P+Ub@&a*q#Zzux<Z52XU{|L)(Bf)rTEb21g?VbGA52T$$YO7nTdpVIe',
    'zTH07rzd9*7Cwm1acw^5eA{^WGQne|d7>BDrr}7+iB2M1Jsl!u0@ymv9X(vo(59VfpX~84ydOEL>8LWw#0L$|7wwF>gSX)F%i%yHGIa#0#F&h7',
    '2&6fRa=eEUyIP<#n&gztWkEIKhw#cHM%4Z&*Dr+fSrvEX6>l+$DS|MlZY$hjsVp`Z6-',
    'zOBzPyIFMBtK8g?1+2^VU1|W*sZh_1L*c*xOK3nqy&oTLVzKQ%xbAR?D8WpHm(0;y6NJK9~*cn{0r{*VF0Uwm){SkE)g@JypRjNa@J2T4+S-',
    'z6G-',
    '=NVWP@Nk!efZ&K=pX4`0FQtu#SLy+dHL`lmd?$Jp<d+78&mGSF=)ufOe?bEf)Xjp8ecP_7xO2lKk1eR8!3X_H7(=s<ILe6{(tfuQ@qFS0Ri*r6',
    '-xo``imi9MXk<v_450PE3vJ}_S(vEiFSch)a>f9J~7P_8#a9K{(!6Qg7c9PWdl>DfDUFfdY)I8`ynw@f>x_5Cvf!gpmAp7%VjH7e>R!Q^+@wT`',
    'mnGG+|!j9IIw3`}DKu#u4Q>eF3g`!>n@&<P+)eaQqWj=pA2arx6R5%_xM?cWr`cJe^9J9q#sF}csz<3jN%v7g;n+=`@xge&=EszLR_Ob46qxnm',
    '8E*bMU<!L%DjAP?UG9Syy%|79cyGBicpBBQCc5NBSri-ATmjfN3QH5&B_z0u(8?}`#2lIX<IN|FuvdL+wN?0B`QeZJau<|~WTB!c0JvBPbLkp<',
    '|)Ti?h*{keowb^7gZnbmN;h1O!R|-3Kw}El2u3@1X2l`n?X)l{Wk=Q1i47?sVFBR7+!H<h1d&W3z-',
    'jC}6AbidgQu1=xTm*)FpMRMvAKg<lP%Dqvi#MprN4Zdm7BXpv>&#Bb-PG?N5_Sr}U9A0xAmIZU4h7unNYE!ZFU=N`9c&<W+MX^oV&wJ^k!HGa;',
    'u<@F&k*^3Rdo*PAnwoD)y*&*=+YO-J`99By{R+M+Hi;S5nK4lr7$H}_q4@0h7qv{;95L}iFGay(1BXAbxPR#<!0C=@}~w65F#---',
    'VCfOUTAai6?UPy+*duvuu`Jea5{lji`D5~N%w{%J04a18Ez!5iw$3NE202aO5~EOkgBBp-T8Xjl;<4AUdC~;=k--nwQX=Cv+ZLsa0y}Uq*^K@G',
    '5aia?(FLmI}QL_QJwD7@o+&I3T^B{Bil7ZH^SXij!tC)VHnk2xEBr+{=u9R8o6aFhx(PgdmB?F$EaPiS6#s_z5^%Yc?O*Vxx!ZPU)TZb1&L^U0',
    '~8OP&?XS^y4G=f$C2kFEFg$r*6o(uP3}nTb_8}H;N_4Vj~Ns|O7XE5O6&@q0~*@ri_6uLr7(Ms7*DcwkDo~9aIV&$<H@WRiXo1A;nd|eV0#8bJ',
    '83%4jbyM_9f2u5MDDr5o~(pR>1Fg-',
    'A|@#p#D_B#s!q#+O8%I#vq;dPjD{_@uvc=MSUJ*}RC$<UGeo~V$efZ1J^0VF&TbnmFqK?{k|E!Gdt3{C1eq^^A=gMd9oc=qnj{YWRezdnXkL4R',
    'Xio_wE_5!(ZI?K8zz7h>t5_<I?2urLbvoFn8a+^ZG7CAQBT=j*Q!6=&B^=cQQiZ5vZ5(9XX~b7gwvI>E<4yMTptmFV<`;J@KBy!|Orq1x_#^)V',
    'f<Ld9i{3PK<_o=n;181AFtTwmizIC^n{lt~?Z*$Y-YjNtGN%W^P5mkSgUsSYs+uKJm3kqiKY@NC=ns-eHOqLLtf!hO!noda{9)67-',
    'g*T*)qeZO1|aCW4TkiecU!>t=S^A5>f5`H9n!z>B5Qs|z;_ETlWI0=CZhid5rv*%pNU{M#CDBHwQB}q5V|8G=8V=QF%vxSj2pb+w%W~9FO4^w0',
    '|OsM9t7Z5ma%7Q@Phz>S87#jwGUiB^qFh@qyK@1=ko^AGmanm%<v~65yeW`<n(E&F!Cao;5VH1YPE{VDD=EY^lL`%6Xx({yI3g>@uoQ~^e+;A{',
    ';HEW{~%k1T3uJDTDFsEKWRxiRmLr$o3ePn>CJ84dT}^RnaC!Lx$gJ-UVj2lH#=25jBnK~4SJ>d{<6<EltHRlC0p%U6E`tT@x0##4gJqF@f7i3;',
    'fch%?at5#u629Jq;eL;t3uytwuoA-T`1yzBzc#6s!8C@*44-?4sVOO5q=iO>jDkA<CRJ(UBPvctD3|!z^lFLre7&GI>l_txSdGWnpxbib>PJo-',
    ')%QRKB>X`P3iAa_+(07Y}ETz0pEY<Gxu;jtBXF>Hn=-N|JaUaU9F5?=j&h-uUAq79R{x(N)s~lsF-',
    'U%kjyy^%r~A=R8mnHNf(k2*5{dO%*XF<CT)vR_`gLu8x9f2iF%vFtA<FkIs<K4V;;|QP3xAYK7jm$9?ywXpG>FPnSwsx|L{Dc%Md5CMSV%tjIp',
    'NR(|ECZb;3<!e@vGPy$<I(?M@RX8=X|OU2G3@kiY{#r`c>9t{Z`#AJ*!|G$HF5QS1=Lj(^m`*S)=N8~EeLk0~>=ku0ME8;aMMciWQLzuWYOl*X',
    '&EswgnvKc;}WnT=C8K~X7zW^TY!j#jVZ#*fUXnk?AN!Jh`rXJViUrax5~S?5syK&h&Hqx7bK*ZDFhyv;{bJa61l1}vn{6Isu{nB_74JjW~Cb?L',
    '^XU(&iE4OqXf^H^VWP7MhCjAbO_!xhFR%DNi8Om@6;_co*C6(j4K#&e2##W3Y@8vzacUvKqPtM&H#>KshWIVDUL9r2fmX<mAM0kzFU*}4mD+;4',
    's%ZJ}C}e}liDh^{DksY~~T>YpfG;XjZ%-z26mlul%#T;+6KK5S};paP~c>BIV-',
    '8W*k^^V~3L>Ho%b?X@wy!q}i2IYT5Cyg~R%)Oe`qvNsuiqG&$X3F>TJxqIfp9Q|dG`E77xe6U4rJR<<+2x!fGysw1fIaVM|!CeLLZhI{3t^i-',
    '@hzY^$B!*U*slli|iOJ{FdLEJj-)~#{iFNbwZKdDu=glUJdCU<|U)gQ`hhdmQKbf7%2vgwKO>NA*CXIcTDS>5xJKw%1df;^ui-',
    '%v=`G4!I{hczJ@W1}K(f<AWd1ox5cMX~|Q(d04aYtU^4mTGwr}&vZo$<u>pa0m9udNF(!F)E|pWi;|;x(T>Klu*+6&C!U+mb9UO!iG4t!;eq3d',
    'ZglD)Hqmn-',
    'G%BZ77v7fSxSDdZ=%|?lmmuaRt84cR&4%AKg*?V_Q)>K##=?lQR96WkKK_$Pm8i(X3H@2Mlj)DdBZGBl6Ri@jNT|lT(?M0)W?bn`$L&7(o?fj(',
    'Ih?2bCv?&l)U=3TM4wqN|FDXb9*1?gn)PeI1bQ=WLz_@hi+{tFZJ&6F8N;y||*&{lba9KY7qA<v;jCld8(`AJ%wf!yNd$G)qT~t$bEl!)8nb6B',
    'dRnSYtmpVan{@pP4uIg%LEJUtN;G^QxYXGt+bGn6|j(NbV9fCwLip+KDFu#t&`0=OXCw%k9C9iq8I>;4hQd@8_8XQGGtyZ=kxF7*cw-',
    ';!M!w<e4|a{~-Uufi8-@KD(j9H?&`-9=tq(e}m8b00tIlu_fGgK%d-',
    'r06?~AOs8o%_3IuOuMU~dchAp%?SF&+CZU@!4JMC&GP>`K?P)izlKo(1=jW9@tA)Yz(|27g#@YCmZ5m0$3)fS|l$2r$^2+av5t}Cw|9ABD_&bB',
    'YS?`AFl6ryw4GsISp~fuww9j<l-!Bk`sEu6YD)C>t*J10$HBB~Pj&GS-PY*&2n>B)5GruX|c>Tk(e67|pQY{@^m&MsMW`hy%m9^Ouabr18Dr|6',
    'bjZMuV<GbY(mii{WnNi3qvY}fKC`#Z~6#w=?d%n~lQwH+>Go;L{HAb-<yP-|bGDLJIb3MvGZh+qkQQ#MP%#LOxUHRL4iNR%Al;3S#Lk-',
    'Q(f6L{Q8Udy}-)$>S0ImvuXV)~&o0i=~Zv=394D+mR3iB_vWx7KXcdb$Sn7TKu=E}t@vMh>*o?Ur?AxJ;26>SCFPsg98+35-',
    'ozG?xr5;Z|JP#;S%q<x>#GT(P|hEED)VSkq2ecE5f0*nag!N{{nY~Cx0=RoBSdJiegmmf(*4>c)6;mjlFx@)>iQSSNqQ=RSK%K?v^?tyFA*WIY',
    '@mh}E&U8YeP`JbMTUvVwD(8fZPyCZ~dF3;FCgU$2(kdwu&nKJzO{QT!d6HGs0#GeN4OD3s5c{k7FYjplgfAIUCk6ZQOkb1K4zf^yNiJAFctik#',
    'lEsK&NhO4RTpDfq#nVRMBO@{&8U4%(VM|uOnpPD4;IVkuEQRn)8SXjdSO#C7EUncBtn>Y5s_-{WGnW2`?iuO>Nd+zaVO!fXPtS0axz0_kH-DIY',
    'EcA$QTXqB6;%<2m9`&mI0QPws7Itqd}y}G5?#;eNYl)G-',
    ';Bg6VHv%IU%yykK*;m0irg*=|{4{Mz>J$8{fc5b+buZ>W#f|2hA;n(EyA#ZA8#DFu^I8=Ss90sNPxL0@Mo(B~CfP!D33>RlWQTq7AiZQ5n+r$v',
    ')fs-',
    's`<o9(I#;F0m%2k<jGo#*RM3z<ptuoS8v}W!bdrD5Mr|LB`d8)fv`SOqZp~^_c`3M<;H@`$pk7{CC$K#{Q_HOgR&q3CW{A(r7`1Pk++#UThSEk',
    '+RG#||WdLnHNGt%=eS>RUz8Sj?wEipZ(axa3qI+u^dz)z}m&0t@o`1J<d%Vn=(yRYApn$2!8{~-',
    '(bBTDoG#*<X;pugXr9+@ICq<uX9VLemR!5xib?Ii-foub$H_lwiqh=E`EeFMLYfUS~}k;wgioFmlMits;Go}MiKu~@6naCH_s?n}~O_=Rg-',
    '%Z#Fopw9e$3w({jxfS<LueC{Q82)XZ<Z&DHW$1eY`te<C_arV0_HL#R=&5$ABpG4K9sAv2#R@UNZ|M7C5A@e)?uPk2h%S`}Aw4^S{_>=}EyEUj',
    ';NJnP4f;vxXPz*<O8lj2blt(<rf7_hKmKba{jy{<(+tn7yEC3wfLHT1y_DAm-%{k;-)8t+FTPKpXuP3}$MZ*Jyd(d*QT_d8P4u6S%4aC#L-',
    'q7;pB2w|sGkM;EVn}ahbY)&>z4&)iQjl&&Tl=u2AxkjXFR`a+;x=}+M}Xn{$-',
    'H=Jui6AyFc_GqOsfA@Y06>|1WsWuiVL35rl5Ce`vh?i4jYc%p%?=rFs^IHTow?cdz!T`1C<tp2HVw$W#^>`V)1TSy7x|{H2xH9}ANob=aEVztq',
    'q#y`QCZAC&aU)IB$P*2df5Yno)0{(WER?Y(45n{_#>g8m2u@8`k2ereTGX*1b)Ev1@jWff8%W^FFyON+bi{rxz5S%@|G#VTG7osT4*tl^7Z-',
    'oNC_#@~t|&86wA%y>}`+g^LSmcU;EO@jvu@>;Id<??R(Aou7qX^-',
    'u@ZsfnPr&2P@+%oMK(7)XOr&Qt#@xKm!?zFytni9TFsiz!M;Nwm_E%VmI1)n*15#e=d(QDBA2OIrTGOtJCFUy>6yI|3N+Oq!>`>}{UXk9h_PRS',
    'a-J5p=(!Tq;K^sj$l==YCr1IlZZZ5)PQ09oVKT;CtxM&?XXx2*GCL$;WEDWLuLHRD@;_UC%UQ+4uIPb(S~+iOAX-)d{uN!}{8Oc~F<-',
    'Pa{kG((zy)auqCw9*~((S3cCY1Q}G;#RG)!hQYNF}C^rHFz<*SihhAn^CYbh?+k8)?xn0pLr0O^ZlXU{L*)P0{&Dt`0<gl)#EeS`2Aog`rMVYi',
    'a7VFu5vQ|)E8;}sjr)yz6(VjZP)MGvwui%S!!iU`f(TK-_u(I=gZ9YA>Aw4FY{W1v(2Ye_9FwvjR&2`oyl+W*v}0{vn~EtowolEI&79SuB-',
    'iZ6VC4+_Y>JvnRi3&1m)2pyVKq<x5V)|#x^@(#;$#31eVGfwqzOIi=+D3TKlF0_h9{}Buc=Q$;WM!Z@oXoGB^L|dtTJ9H{C_bx|e<C#01ull-G',
    'HmS-N$RVs}e^5Y$(wpD@hy?e~Yi4`Q5M2JNVEyTWVxeA()6Cj8EqS*>$Rw0~#-',
    'd?&q+z0s!z<849UYm?Ndecd(vrJ1TcE5%h09%^vkYSX^2N@0BWz3PL7c&$8am|KqXR9?O@b}LNZAg+)9t*bb@LmDCWwUG(Dr8~t+mVBzk>-',
    '$q}zx`X2^4eni?g;(yS5<P`wFdvv2D8VmeSm-Az>?F=?Hg{;((Stoyldw5#?yUc9}e+ro%{8cE#`0D;il);{rvsfc{GZ(ADXDj>tXZF?UffA@I',
    'Nny+V@Ayy~IjM3?S&f?ArRh?$)g<U<PkL_3+J#!!3|U7HJ+EvHJzuuW!nIf>zewK<aVrcNoTYe8e&SZskv7=*rh;wnX+DEPVu){(uHUe?Wu)_$',
    'Q?Mp(k{i;`E(*L{_Fq?^3qHP%A~bhQ0SD<W=BC4)bnf)*8oi6PeR=5QU};{hlzqxYbj6fxdmV;$YopO~egz9kD*&vzV_^t4H1Tb}JzIJmHh)Sx',
    'G#nYEwf2o@dmz$6(X;pPSx1vu1Mpu-',
    '03qXCio?NP50PequxSW)Io?`0R_HnR{9EN9LZT^C#wfUorQL{E(OLnbDV;lwl{&FCaW8Z{}=9Dd4INoMKjFuGPhVzV5+1xj7T=<8_sXJg!$Ao~',
    'pwyW1p+UUkqQ%b}vfv+KaLNRxN4#ZQN^B>zVyqdF`vEJ>Oq6oyePy6J~E$v$F~@M)UE;3HUi@`nrhmp&tFWw+ODh7*~^DYFvLT%l!CwoyLT=;G',
    'XV}?Z3DH_gwn9BYacip*30736ak;-S3><AKsF0^Oc5c`uu{v)<pHG%<{Q-',
    '@|8#WG&lH6n%5&2`6J=Kp`siAqtEi=lQP`LblbZhHm~dOJx_jD$SJeZ^_P_Nfho1OHcmg;XB?~PQI-',
    '{d8MkV#DXO>?Uia8|@<okJlwKRQ2H0~O*@XDqx;0j$+?aXZv=1!3nSgah&QgZ1AOVw#{_8$HX#^LtezaVb{aOe5nwZX9OUG&HHdnl&=~OMEfvd',
    'PJL0vE7--1<RCbO|^Ea#sm$0!=D7R73zKD`2C##IKe?uTBBgtrRh4fW&YE^~5k%m%!Q=s&NEHMSo>Zl&BCt>^pH@T2c&%xJ`R&u{tMXQdf~<bN',
    'y0jEVI@j*s1WtoX5@kL&p`@w2L1NH@(j{noQ5{lL((^E9E1-T2P`-V=Wl@K)pd8)s}{{MiZrmEZk;>_GnyUE*E)E$3pq-S^k7<8iK-cVs`gr>}',
    'gRk&Kx<STzVeG7;$gwX6&q$iS7}f3B>7`X^W?`{Em|-PBFO3N&BeWc1v~-hH8-MK8_0CKX;(mDkeK%gX-x>i>V&`jN%0Sz~!zO8-',
    'kOf4BLrdGph&8?Sf3ujBW7_>V;TTE%|$Mjw>k9Qys-oiaH6`fkm0XG#b9Y25h%WX5>Yl!+NHPTeAXVQJlZG+xcoA&pk@)3q^kg6~?!zXWDyG=~',
    'fl;1~Q_uFhKO%gYBAjX%6{aQn{!NS@O})G77H66CE=7`0(=@K1vHcRexxZ-UQ_tuNjO_~Np@6(RAIAXt4Z>xKsO+S$6j68LC(-',
    'KFx~)rx=qpc1d=({=J+FTT&brS`qUd*SZW>xfU8%7)_1_q$%*Cutp}M)l>p-kYu@GG*j9cM7*1)5CiV4q0k)rTGBz-Iw#>(uIy~k-',
    'Q}fA63(^h>wk+k1*eKfK0-#H_2W!lhR$)^XpVEfxT6({&>6fNsq3@>PM69izdQ{29TkR-',
    '<9KE)cEBpgi!&0bjV++{rQ^JR|tRd$FD`#2hzV?WcUK*FOB}Af&aPjaLuD|^OrvK)KdP}cZ0rsq3QLN!CN)!wd47CG4S&{UH?|?|3K;SHsI69{',
    'ROBc#j-p@KK^ePQdduTFNvJ+#Y=w=<^A!$0C4OntN',
]
agent_bytes = zlib.decompress(base64.b85decode("".join(_AGENT_B85_PARTS).encode("ascii")))
assert len(agent_bytes) == 26304
assert hashlib.sha256(agent_bytes).hexdigest() == AGENT_SHA256

work_dir = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd() / "output"
work_dir.mkdir(parents=True, exist_ok=True)
main_path = work_dir / "main.py"
archive_path = work_dir / "submission.tar.gz"
main_path.write_bytes(agent_bytes)

with archive_path.open("wb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            info = tarfile.TarInfo("main.py")
            info.size = len(agent_bytes)
            info.mode = 0o644
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(agent_bytes))

assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == ARCHIVE_SHA256
with tarfile.open(archive_path, "r:gz") as archive:
    assert archive.getnames() == ["main.py"]
    assert hashlib.sha256(archive.extractfile("main.py").read()).hexdigest() == AGENT_SHA256

# Self-play validates runtime and packaging contracts only; it is not win-rate evidence.
from importlib.metadata import version as package_version
engine_version = package_version("kaggle-environments")
assert engine_version == ENGINE_VERSION, (
    f"Expected kaggle-environments=={ENGINE_VERSION}, found {engine_version}"
)
captured = io.StringIO()
with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
    from kaggle_environments import make
    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "townCenterSellInterval": 24,
            "farmHandCostMult": 1,
            "seed": 93001,
        },
        debug=False,
    )
    env.run([str(main_path), str(main_path)])

final = env.steps[-1]
statuses = [str(player.status) for player in final]
rewards = [float(player.reward) for player in final]
assert len(env.steps) == 720
assert statuses == ["DONE", "DONE"]
assert all(reward > 0 for reward in rewards)
assert int(env.configuration.townCenterSellInterval) == 24

artifact_check = [{
    "engine version": engine_version,
    "engine commit": ENGINE_COMMIT[:8],
    "main.py bytes": len(agent_bytes),
    "main.py SHA-256": hashlib.sha256(agent_bytes).hexdigest(),
    "archive SHA-256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
    "archive members": "main.py",
    "self-play frames": len(env.steps),
    "self-play status": "/".join(statuses),
    "self-play rewards": f"{rewards[0]:,.0f} / {rewards[1]:,.0f}",
}]
display(Markdown(markdown_table(artifact_check)))
print("Generated: main.py")
print("Generated: submission.tar.gz")