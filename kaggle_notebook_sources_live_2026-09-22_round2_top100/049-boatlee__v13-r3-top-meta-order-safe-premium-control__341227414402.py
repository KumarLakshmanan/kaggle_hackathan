from io import StringIO
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

plt.rcParams["figure.dpi"] = 125
plt.rcParams["axes.unicode_minus"] = False

TEAL = "#0F766E"
TEAL_LIGHT = "#5EEAD4"
ORANGE = "#EA580C"
SLATE = "#64748B"
LIGHT = "#E2E8F0"
DARK = "#0F172A"

AGENT_SHA256 = "6f52902081fed08bb5da08d575b796437e645c5320662b448b81eb079f185cfb"
V21_SHA256 = "d9dc24ce5429ec628ead0621a160bee90725350683d7dfcc4686fcaf511f3aab"
ENGINE_VERSION = "1.32.4"

gold_games = pd.read_csv(StringIO(r"""candidate,margin,my_reward,my_status,opp_reward,opp_status,opponent,result,seat,seed
v13r3_order_safe,11922.0,134478.0,DONE,122556.0,DONE,Top-route replay proxy A,win,0,87703
v13r3_order_safe,11922.0,134478.0,DONE,122556.0,DONE,Top-route replay proxy A,win,1,87703
v13r3_order_safe,1509.0,86257.0,DONE,84748.0,DONE,Top-route replay proxy A,win,0,87721
v13r3_order_safe,803.0,85882.0,DONE,85079.0,DONE,Top-route replay proxy A,win,1,87721
v13r3_order_safe,98.0,91400.0,DONE,91302.0,DONE,Top-route replay proxy A,win,0,87739
v13r3_order_safe,-995.0,90954.0,DONE,91949.0,DONE,Top-route replay proxy A,loss,1,87739
v13r3_order_safe,10651.0,153454.0,DONE,142803.0,DONE,Top-route replay proxy A,win,0,87763
v13r3_order_safe,9735.0,152546.0,DONE,142811.0,DONE,Top-route replay proxy A,win,1,87763
v13r3_order_safe,8028.0,138166.0,DONE,130138.0,DONE,Top-route replay proxy A,win,0,87781
v13r3_order_safe,8028.0,138166.0,DONE,130138.0,DONE,Top-route replay proxy A,win,1,87781
v13r3_order_safe,10355.0,153589.0,DONE,143234.0,DONE,Top-route replay proxy A,win,0,87809
v13r3_order_safe,10355.0,153589.0,DONE,143234.0,DONE,Top-route replay proxy A,win,1,87809
v13r3_order_safe,10646.0,153423.0,DONE,142777.0,DONE,Top-route replay proxy A,win,0,87827
v13r3_order_safe,11740.0,153631.0,DONE,141891.0,DONE,Top-route replay proxy A,win,1,87827
v13r3_order_safe,120.0,137586.0,DONE,137466.0,DONE,Top-route replay proxy A,win,0,87851
v13r3_order_safe,120.0,137586.0,DONE,137466.0,DONE,Top-route replay proxy A,win,1,87851
v13r3_order_safe,9308.0,130810.0,DONE,121502.0,DONE,Top-route replay proxy B,win,0,87703
v13r3_order_safe,9308.0,130810.0,DONE,121502.0,DONE,Top-route replay proxy B,win,1,87703
v13r3_order_safe,4497.0,103681.0,DONE,99184.0,DONE,Top-route replay proxy B,win,0,87721
v13r3_order_safe,4497.0,103681.0,DONE,99184.0,DONE,Top-route replay proxy B,win,1,87721
v13r3_order_safe,-267.0,81311.0,DONE,81578.0,DONE,Top-route replay proxy B,loss,0,87739
v13r3_order_safe,-549.0,81207.0,DONE,81756.0,DONE,Top-route replay proxy B,loss,1,87739
v13r3_order_safe,5799.0,147357.0,DONE,141558.0,DONE,Top-route replay proxy B,win,0,87763
v13r3_order_safe,6551.0,147808.0,DONE,141257.0,DONE,Top-route replay proxy B,win,1,87763
v13r3_order_safe,7548.0,140366.0,DONE,132818.0,DONE,Top-route replay proxy B,win,0,87781
v13r3_order_safe,7548.0,140366.0,DONE,132818.0,DONE,Top-route replay proxy B,win,1,87781
v13r3_order_safe,9709.0,150590.0,DONE,140881.0,DONE,Top-route replay proxy B,win,0,87809
v13r3_order_safe,9709.0,150590.0,DONE,140881.0,DONE,Top-route replay proxy B,win,1,87809
v13r3_order_safe,4454.0,154844.0,DONE,150390.0,DONE,Top-route replay proxy B,win,0,87827
v13r3_order_safe,6467.0,155731.0,DONE,149264.0,DONE,Top-route replay proxy B,win,1,87827
v13r3_order_safe,2125.0,130285.0,DONE,128160.0,DONE,Top-route replay proxy B,win,0,87851
v13r3_order_safe,2330.0,130293.0,DONE,127963.0,DONE,Top-route replay proxy B,win,1,87851
v13r3_order_safe,2487.0,117477.0,DONE,114990.0,DONE,Top-route replay proxy C,win,0,87703
v13r3_order_safe,2487.0,117477.0,DONE,114990.0,DONE,Top-route replay proxy C,win,1,87703
v13r3_order_safe,698.0,82791.0,DONE,82093.0,DONE,Top-route replay proxy C,win,0,87721
v13r3_order_safe,-389.0,83191.0,DONE,83580.0,DONE,Top-route replay proxy C,loss,1,87721
v13r3_order_safe,861.0,91128.0,DONE,90267.0,DONE,Top-route replay proxy C,win,0,87739
v13r3_order_safe,-188.0,90685.0,DONE,90873.0,DONE,Top-route replay proxy C,loss,1,87739
v13r3_order_safe,1446.0,161856.0,DONE,160410.0,DONE,Top-route replay proxy C,win,0,87763
v13r3_order_safe,2492.0,162018.0,DONE,159526.0,DONE,Top-route replay proxy C,win,1,87763
v13r3_order_safe,4679.0,145750.0,DONE,141071.0,DONE,Top-route replay proxy C,win,0,87781
v13r3_order_safe,4287.0,145596.0,DONE,141309.0,DONE,Top-route replay proxy C,win,1,87781
v13r3_order_safe,5770.0,146690.0,DONE,140920.0,DONE,Top-route replay proxy C,win,0,87809
v13r3_order_safe,5770.0,146690.0,DONE,140920.0,DONE,Top-route replay proxy C,win,1,87809
v13r3_order_safe,2199.0,132653.0,DONE,130454.0,DONE,Top-route replay proxy C,win,0,87827
v13r3_order_safe,3758.0,133394.0,DONE,129636.0,DONE,Top-route replay proxy C,win,1,87827
v13r3_order_safe,1344.0,137986.0,DONE,136642.0,DONE,Top-route replay proxy C,win,0,87851
v13r3_order_safe,1344.0,137986.0,DONE,136642.0,DONE,Top-route replay proxy C,win,1,87851
v13r3_order_safe,7515.0,128314.0,DONE,120799.0,DONE,Top-route replay proxy D,win,0,87703
v13r3_order_safe,7515.0,128314.0,DONE,120799.0,DONE,Top-route replay proxy D,win,1,87703
v13r3_order_safe,4895.0,100483.0,DONE,95588.0,DONE,Top-route replay proxy D,win,0,87721
v13r3_order_safe,3954.0,100014.0,DONE,96060.0,DONE,Top-route replay proxy D,win,1,87721
v13r3_order_safe,1555.0,82940.0,DONE,81385.0,DONE,Top-route replay proxy D,win,0,87739
v13r3_order_safe,1141.0,82733.0,DONE,81592.0,DONE,Top-route replay proxy D,win,1,87739
v13r3_order_safe,5927.0,164323.0,DONE,158396.0,DONE,Top-route replay proxy D,win,0,87763
v13r3_order_safe,6077.0,164473.0,DONE,158396.0,DONE,Top-route replay proxy D,win,1,87763
v13r3_order_safe,6328.0,160484.0,DONE,154156.0,DONE,Top-route replay proxy D,win,0,87781
v13r3_order_safe,6328.0,160484.0,DONE,154156.0,DONE,Top-route replay proxy D,win,1,87781
v13r3_order_safe,6824.0,147340.0,DONE,140516.0,DONE,Top-route replay proxy D,win,0,87809
v13r3_order_safe,6824.0,147340.0,DONE,140516.0,DONE,Top-route replay proxy D,win,1,87809
v13r3_order_safe,6817.0,138755.0,DONE,131938.0,DONE,Top-route replay proxy D,win,0,87827
v13r3_order_safe,8539.0,139616.0,DONE,131077.0,DONE,Top-route replay proxy D,win,1,87827
v13r3_order_safe,1993.0,127724.0,DONE,125731.0,DONE,Top-route replay proxy D,win,0,87851
v13r3_order_safe,1993.0,127724.0,DONE,125731.0,DONE,Top-route replay proxy D,win,1,87851
v13r3_order_safe,2516.0,126713.0,DONE,124197.0,DONE,Top-route replay proxy E,win,0,87703
v13r3_order_safe,2516.0,126713.0,DONE,124197.0,DONE,Top-route replay proxy E,win,1,87703
v13r3_order_safe,1592.0,83988.0,DONE,82396.0,DONE,Top-route replay proxy E,win,0,87721
v13r3_order_safe,388.0,83869.0,DONE,83481.0,DONE,Top-route replay proxy E,win,1,87721
v13r3_order_safe,2756.0,92360.0,DONE,89604.0,DONE,Top-route replay proxy E,win,0,87739
v13r3_order_safe,1746.0,91987.0,DONE,90241.0,DONE,Top-route replay proxy E,win,1,87739
v13r3_order_safe,4859.0,162601.0,DONE,157742.0,DONE,Top-route replay proxy E,win,0,87763
v13r3_order_safe,5009.0,162751.0,DONE,157742.0,DONE,Top-route replay proxy E,win,1,87763
v13r3_order_safe,1880.0,131599.0,DONE,129719.0,DONE,Top-route replay proxy E,win,0,87781
v13r3_order_safe,1880.0,131599.0,DONE,129719.0,DONE,Top-route replay proxy E,win,1,87781
v13r3_order_safe,4678.0,137384.0,DONE,132706.0,DONE,Top-route replay proxy E,win,0,87809
v13r3_order_safe,4678.0,137384.0,DONE,132706.0,DONE,Top-route replay proxy E,win,1,87809
v13r3_order_safe,620.0,152197.0,DONE,151577.0,DONE,Top-route replay proxy E,win,0,87827
v13r3_order_safe,3562.0,153502.0,DONE,149940.0,DONE,Top-route replay proxy E,win,1,87827
v13r3_order_safe,3218.0,138895.0,DONE,135677.0,DONE,Top-route replay proxy E,win,0,87851
v13r3_order_safe,3218.0,138895.0,DONE,135677.0,DONE,Top-route replay proxy E,win,1,87851
v13r3_order_safe,4997.0,111699.0,DONE,106702.0,DONE,Top-route replay proxy F,win,0,87703
v13r3_order_safe,4997.0,111699.0,DONE,106702.0,DONE,Top-route replay proxy F,win,1,87703
v13r3_order_safe,4705.0,100522.0,DONE,95817.0,DONE,Top-route replay proxy F,win,0,87721
v13r3_order_safe,3609.0,100088.0,DONE,96479.0,DONE,Top-route replay proxy F,win,1,87721
v13r3_order_safe,4187.0,84321.0,DONE,80134.0,DONE,Top-route replay proxy F,win,0,87739
v13r3_order_safe,3850.0,84152.0,DONE,80302.0,DONE,Top-route replay proxy F,win,1,87739
v13r3_order_safe,2668.0,158731.0,DONE,156063.0,DONE,Top-route replay proxy F,win,0,87763
v13r3_order_safe,2980.0,158887.0,DONE,155907.0,DONE,Top-route replay proxy F,win,1,87763
v13r3_order_safe,4017.0,147202.0,DONE,143185.0,DONE,Top-route replay proxy F,win,0,87781
v13r3_order_safe,3821.0,147104.0,DONE,143283.0,DONE,Top-route replay proxy F,win,1,87781
v13r3_order_safe,4306.0,146028.0,DONE,141722.0,DONE,Top-route replay proxy F,win,0,87809
v13r3_order_safe,4306.0,146028.0,DONE,141722.0,DONE,Top-route replay proxy F,win,1,87809
v13r3_order_safe,1616.0,149199.0,DONE,147583.0,DONE,Top-route replay proxy F,win,0,87827
v13r3_order_safe,3660.0,150221.0,DONE,146561.0,DONE,Top-route replay proxy F,win,1,87827
v13r3_order_safe,2924.0,128538.0,DONE,125614.0,DONE,Top-route replay proxy F,win,0,87851
v13r3_order_safe,2924.0,128538.0,DONE,125614.0,DONE,Top-route replay proxy F,win,1,87851
"""))
public_games = pd.read_csv(StringIO(r"""candidate,margin,my_reward,my_status,opp_reward,opp_status,opponent,result,seat,seed
v13r3_order_safe,11867.0,153232.0,DONE,141365.0,DONE,Public strong-route control A,win,0,87703
v13r3_order_safe,11867.0,153232.0,DONE,141365.0,DONE,Public strong-route control A,win,1,87703
v13r3_order_safe,6964.0,126001.0,DONE,119037.0,DONE,Public strong-route control A,win,0,87721
v13r3_order_safe,5730.0,105138.0,DONE,99408.0,DONE,Public strong-route control A,win,1,87721
v13r3_order_safe,8423.0,144970.0,DONE,136547.0,DONE,Public strong-route control A,win,0,87739
v13r3_order_safe,7141.0,138109.0,DONE,130968.0,DONE,Public strong-route control A,win,1,87739
v13r3_order_safe,10117.0,106745.0,DONE,96628.0,DONE,Public strong-route control A,win,0,87763
v13r3_order_safe,10278.0,106901.0,DONE,96623.0,DONE,Public strong-route control A,win,1,87763
v13r3_order_safe,6371.0,103181.0,DONE,96810.0,DONE,Public strong-route control A,win,0,87781
v13r3_order_safe,6278.0,103174.0,DONE,96896.0,DONE,Public strong-route control A,win,1,87781
v13r3_order_safe,13354.0,135665.0,DONE,122311.0,DONE,Public strong-route control A,win,0,87809
v13r3_order_safe,13354.0,135665.0,DONE,122311.0,DONE,Public strong-route control A,win,1,87809
v13r3_order_safe,4930.0,106040.0,DONE,101110.0,DONE,Public strong-route control A,win,0,87827
v13r3_order_safe,7551.0,103218.0,DONE,95667.0,DONE,Public strong-route control A,win,1,87827
v13r3_order_safe,6065.0,113352.0,DONE,107287.0,DONE,Public strong-route control A,win,0,87851
v13r3_order_safe,6065.0,113352.0,DONE,107287.0,DONE,Public strong-route control A,win,1,87851
v13r3_order_safe,14804.0,155224.0,DONE,140420.0,DONE,Public strong-route control B,win,0,87703
v13r3_order_safe,14804.0,155224.0,DONE,140420.0,DONE,Public strong-route control B,win,1,87703
v13r3_order_safe,11100.0,130002.0,DONE,118902.0,DONE,Public strong-route control B,win,0,87721
v13r3_order_safe,8980.0,106969.0,DONE,97989.0,DONE,Public strong-route control B,win,1,87721
v13r3_order_safe,14344.0,147560.0,DONE,133216.0,DONE,Public strong-route control B,win,0,87739
v13r3_order_safe,12975.0,140382.0,DONE,127407.0,DONE,Public strong-route control B,win,1,87739
v13r3_order_safe,9680.0,108323.0,DONE,98643.0,DONE,Public strong-route control B,win,0,87763
v13r3_order_safe,10017.0,108476.0,DONE,98459.0,DONE,Public strong-route control B,win,1,87763
v13r3_order_safe,7712.0,103813.0,DONE,96101.0,DONE,Public strong-route control B,win,0,87781
v13r3_order_safe,7712.0,103813.0,DONE,96101.0,DONE,Public strong-route control B,win,1,87781
v13r3_order_safe,12459.0,137691.0,DONE,125232.0,DONE,Public strong-route control B,win,0,87809
v13r3_order_safe,12459.0,137691.0,DONE,125232.0,DONE,Public strong-route control B,win,1,87809
v13r3_order_safe,8891.0,109864.0,DONE,100973.0,DONE,Public strong-route control B,win,0,87827
v13r3_order_safe,10477.0,104725.0,DONE,94248.0,DONE,Public strong-route control B,win,1,87827
v13r3_order_safe,7824.0,115780.0,DONE,107956.0,DONE,Public strong-route control B,win,0,87851
v13r3_order_safe,7947.0,115775.0,DONE,107828.0,DONE,Public strong-route control B,win,1,87851
v13r3_order_safe,13053.0,151006.0,DONE,137953.0,DONE,Public strong-route control C,win,0,87703
v13r3_order_safe,13053.0,151006.0,DONE,137953.0,DONE,Public strong-route control C,win,1,87703
v13r3_order_safe,18873.0,132442.0,DONE,113569.0,DONE,Public strong-route control C,win,0,87721
v13r3_order_safe,16075.0,143237.0,DONE,127162.0,DONE,Public strong-route control C,win,1,87721
v13r3_order_safe,11836.0,126495.0,DONE,114659.0,DONE,Public strong-route control C,win,0,87739
v13r3_order_safe,11629.0,126395.0,DONE,114766.0,DONE,Public strong-route control C,win,1,87739
v13r3_order_safe,11136.0,81866.0,DONE,70730.0,DONE,Public strong-route control C,win,0,87763
v13r3_order_safe,10143.0,81408.0,DONE,71265.0,DONE,Public strong-route control C,win,1,87763
v13r3_order_safe,11584.0,97510.0,DONE,85926.0,DONE,Public strong-route control C,win,0,87781
v13r3_order_safe,11584.0,97510.0,DONE,85926.0,DONE,Public strong-route control C,win,1,87781
v13r3_order_safe,13842.0,119652.0,DONE,105810.0,DONE,Public strong-route control C,win,0,87809
v13r3_order_safe,13842.0,119652.0,DONE,105810.0,DONE,Public strong-route control C,win,1,87809
v13r3_order_safe,7001.0,97828.0,DONE,90827.0,DONE,Public strong-route control C,win,0,87827
v13r3_order_safe,14136.0,110515.0,DONE,96379.0,DONE,Public strong-route control C,win,1,87827
v13r3_order_safe,14748.0,153517.0,DONE,138769.0,DONE,Public strong-route control C,win,0,87851
v13r3_order_safe,14989.0,153518.0,DONE,138529.0,DONE,Public strong-route control C,win,1,87851
v13r3_order_safe,14804.0,155224.0,DONE,140420.0,DONE,Public strong-route control D,win,0,87703
v13r3_order_safe,14804.0,155224.0,DONE,140420.0,DONE,Public strong-route control D,win,1,87703
v13r3_order_safe,11100.0,130002.0,DONE,118902.0,DONE,Public strong-route control D,win,0,87721
v13r3_order_safe,8980.0,106969.0,DONE,97989.0,DONE,Public strong-route control D,win,1,87721
v13r3_order_safe,14344.0,147560.0,DONE,133216.0,DONE,Public strong-route control D,win,0,87739
v13r3_order_safe,12975.0,140382.0,DONE,127407.0,DONE,Public strong-route control D,win,1,87739
v13r3_order_safe,9680.0,108323.0,DONE,98643.0,DONE,Public strong-route control D,win,0,87763
v13r3_order_safe,10017.0,108476.0,DONE,98459.0,DONE,Public strong-route control D,win,1,87763
v13r3_order_safe,7712.0,103813.0,DONE,96101.0,DONE,Public strong-route control D,win,0,87781
v13r3_order_safe,7712.0,103813.0,DONE,96101.0,DONE,Public strong-route control D,win,1,87781
v13r3_order_safe,12459.0,137691.0,DONE,125232.0,DONE,Public strong-route control D,win,0,87809
v13r3_order_safe,12459.0,137691.0,DONE,125232.0,DONE,Public strong-route control D,win,1,87809
v13r3_order_safe,8891.0,109864.0,DONE,100973.0,DONE,Public strong-route control D,win,0,87827
v13r3_order_safe,10477.0,104725.0,DONE,94248.0,DONE,Public strong-route control D,win,1,87827
v13r3_order_safe,7824.0,115780.0,DONE,107956.0,DONE,Public strong-route control D,win,0,87851
v13r3_order_safe,7947.0,115775.0,DONE,107828.0,DONE,Public strong-route control D,win,1,87851
v13r3_order_safe,10292.0,149604.0,DONE,139312.0,DONE,Public strong-route control E,win,0,87703
v13r3_order_safe,10292.0,149604.0,DONE,139312.0,DONE,Public strong-route control E,win,1,87703
v13r3_order_safe,16052.0,131143.0,DONE,115091.0,DONE,Public strong-route control E,win,0,87721
v13r3_order_safe,13226.0,141935.0,DONE,128709.0,DONE,Public strong-route control E,win,1,87721
v13r3_order_safe,9004.0,125062.0,DONE,116058.0,DONE,Public strong-route control E,win,0,87739
v13r3_order_safe,8799.0,124963.0,DONE,116164.0,DONE,Public strong-route control E,win,1,87739
v13r3_order_safe,6821.0,79693.0,DONE,72872.0,DONE,Public strong-route control E,win,0,87763
v13r3_order_safe,5740.0,79172.0,DONE,73432.0,DONE,Public strong-route control E,win,1,87763
v13r3_order_safe,6735.0,95051.0,DONE,88316.0,DONE,Public strong-route control E,win,0,87781
v13r3_order_safe,6735.0,95051.0,DONE,88316.0,DONE,Public strong-route control E,win,1,87781
v13r3_order_safe,9098.0,117286.0,DONE,108188.0,DONE,Public strong-route control E,win,0,87809
v13r3_order_safe,9098.0,117286.0,DONE,108188.0,DONE,Public strong-route control E,win,1,87809
v13r3_order_safe,5948.0,97227.0,DONE,91279.0,DONE,Public strong-route control E,win,0,87827
v13r3_order_safe,9797.0,108291.0,DONE,98494.0,DONE,Public strong-route control E,win,1,87827
v13r3_order_safe,11780.0,152049.0,DONE,140269.0,DONE,Public strong-route control E,win,0,87851
v13r3_order_safe,12021.0,152050.0,DONE,140029.0,DONE,Public strong-route control E,win,1,87851
v13r3_order_safe,8568.0,149708.0,DONE,141140.0,DONE,Public strong-route control F,win,0,87703
v13r3_order_safe,8568.0,149708.0,DONE,141140.0,DONE,Public strong-route control F,win,1,87703
v13r3_order_safe,13934.0,131018.0,DONE,117084.0,DONE,Public strong-route control F,win,0,87721
v13r3_order_safe,13236.0,143248.0,DONE,130012.0,DONE,Public strong-route control F,win,1,87721
v13r3_order_safe,6524.0,124844.0,DONE,118320.0,DONE,Public strong-route control F,win,0,87739
v13r3_order_safe,6719.0,125101.0,DONE,118382.0,DONE,Public strong-route control F,win,1,87739
v13r3_order_safe,4697.0,79829.0,DONE,75132.0,DONE,Public strong-route control F,win,0,87763
v13r3_order_safe,4187.0,79277.0,DONE,75090.0,DONE,Public strong-route control F,win,1,87763
v13r3_order_safe,4711.0,95108.0,DONE,90397.0,DONE,Public strong-route control F,win,0,87781
v13r3_order_safe,4430.0,95060.0,DONE,90630.0,DONE,Public strong-route control F,win,1,87781
v13r3_order_safe,7233.0,117319.0,DONE,110086.0,DONE,Public strong-route control F,win,0,87809
v13r3_order_safe,7233.0,117319.0,DONE,110086.0,DONE,Public strong-route control F,win,1,87809
v13r3_order_safe,3837.0,97341.0,DONE,93504.0,DONE,Public strong-route control F,win,0,87827
v13r3_order_safe,6383.0,105561.0,DONE,99178.0,DONE,Public strong-route control F,win,1,87827
v13r3_order_safe,9695.0,152128.0,DONE,142433.0,DONE,Public strong-route control F,win,0,87851
v13r3_order_safe,9830.0,152129.0,DONE,142299.0,DONE,Public strong-route control F,win,1,87851
"""))
v21_games = pd.read_csv(StringIO(r"""candidate,margin,my_reward,my_status,opp_reward,opp_status,opponent,result,seat,seed
v13r3_order_safe,4620.0,110062.0,DONE,105442.0,DONE,Exact public V21.1 artifact,win,0,93001
v13r3_order_safe,2058.0,107829.0,DONE,105771.0,DONE,Exact public V21.1 artifact,win,1,93001
v13r3_order_safe,406.0,120536.0,DONE,120130.0,DONE,Exact public V21.1 artifact,win,0,93019
v13r3_order_safe,406.0,120536.0,DONE,120130.0,DONE,Exact public V21.1 artifact,win,1,93019
v13r3_order_safe,2541.0,126920.0,DONE,124379.0,DONE,Exact public V21.1 artifact,win,0,93037
v13r3_order_safe,2541.0,126920.0,DONE,124379.0,DONE,Exact public V21.1 artifact,win,1,93037
v13r3_order_safe,3010.0,108400.0,DONE,105390.0,DONE,Exact public V21.1 artifact,win,0,93055
v13r3_order_safe,3010.0,108400.0,DONE,105390.0,DONE,Exact public V21.1 artifact,win,1,93055
v13r3_order_safe,2478.0,130567.0,DONE,128089.0,DONE,Exact public V21.1 artifact,win,0,93073
v13r3_order_safe,3388.0,130845.0,DONE,127457.0,DONE,Exact public V21.1 artifact,win,1,93073
v13r3_order_safe,5040.0,103182.0,DONE,98142.0,DONE,Exact public V21.1 artifact,win,0,93091
v13r3_order_safe,4938.0,103080.0,DONE,98142.0,DONE,Exact public V21.1 artifact,win,1,93091
v13r3_order_safe,4510.0,129291.0,DONE,124781.0,DONE,Exact public V21.1 artifact,win,0,93109
v13r3_order_safe,4643.0,129393.0,DONE,124750.0,DONE,Exact public V21.1 artifact,win,1,93109
v13r3_order_safe,618.0,125489.0,DONE,124871.0,DONE,Exact public V21.1 artifact,win,0,93127
v13r3_order_safe,618.0,125489.0,DONE,124871.0,DONE,Exact public V21.1 artifact,win,1,93127
v13r3_order_safe,1921.0,123983.0,DONE,122062.0,DONE,Exact public V21.1 artifact,win,0,93145
v13r3_order_safe,1921.0,123983.0,DONE,122062.0,DONE,Exact public V21.1 artifact,win,1,93145
v13r3_order_safe,2380.0,130670.0,DONE,128290.0,DONE,Exact public V21.1 artifact,win,0,93163
v13r3_order_safe,2380.0,130670.0,DONE,128290.0,DONE,Exact public V21.1 artifact,win,1,93163
v13r3_order_safe,1593.0,155008.0,DONE,153415.0,DONE,Exact public V21.1 artifact,win,0,93181
v13r3_order_safe,1593.0,155008.0,DONE,153415.0,DONE,Exact public V21.1 artifact,win,1,93181
v13r3_order_safe,4324.0,112136.0,DONE,107812.0,DONE,Exact public V21.1 artifact,win,0,93199
v13r3_order_safe,4324.0,112136.0,DONE,107812.0,DONE,Exact public V21.1 artifact,win,1,93199
v13r3_order_safe,954.0,85707.0,DONE,84753.0,DONE,Exact public V21.1 artifact,win,0,93217
v13r3_order_safe,954.0,85707.0,DONE,84753.0,DONE,Exact public V21.1 artifact,win,1,93217
v13r3_order_safe,2649.0,120217.0,DONE,117568.0,DONE,Exact public V21.1 artifact,win,0,93235
v13r3_order_safe,2649.0,120217.0,DONE,117568.0,DONE,Exact public V21.1 artifact,win,1,93235
v13r3_order_safe,595.0,123922.0,DONE,123327.0,DONE,Exact public V21.1 artifact,win,0,93253
v13r3_order_safe,-176.0,106642.0,DONE,106818.0,DONE,Exact public V21.1 artifact,loss,1,93253
v13r3_order_safe,416.0,132707.0,DONE,132291.0,DONE,Exact public V21.1 artifact,win,0,93271
v13r3_order_safe,416.0,132707.0,DONE,132291.0,DONE,Exact public V21.1 artifact,win,1,93271
"""))
shift_windows = pd.DataFrame(json.loads(r"""[{"step":167,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":213,"item":"MILK","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":215,"item":"MILK","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":235,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":4.0,"support":6,"next_base_quantity":4,"static_shift_cap":4},{"step":258,"item":"MELON","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":258,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":4.0,"support":6,"next_base_quantity":4,"static_shift_cap":4},{"step":260,"item":"MELON","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":260,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":261,"item":"MELON","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":263,"item":"MELON","sell_probability":1.0,"median_requested_quantity":30.0,"support":6,"next_base_quantity":30,"static_shift_cap":30},{"step":281,"item":"MELON","sell_probability":0.8333333333333334,"median_requested_quantity":6.0,"support":5,"next_base_quantity":6,"static_shift_cap":6},{"step":283,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":287,"item":"MELON","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":287,"item":"MILK","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":308,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":310,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":310,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":8.0,"support":6,"next_base_quantity":8,"static_shift_cap":8},{"step":335,"item":"MILK","sell_probability":1.0,"median_requested_quantity":9.0,"support":6,"next_base_quantity":9,"static_shift_cap":9},{"step":335,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":356,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":375,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":378,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":382,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":383,"item":"MILK","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":383,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":388,"item":"MILK","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":404,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":404,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":406,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":407,"item":"WOOL","sell_probability":0.6666666666666666,"median_requested_quantity":4.0,"support":4,"next_base_quantity":4,"static_shift_cap":4},{"step":425,"item":"MILK","sell_probability":0.5,"median_requested_quantity":3.0,"support":3,"next_base_quantity":3,"static_shift_cap":3},{"step":427,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":7.0,"support":4,"next_base_quantity":8,"static_shift_cap":8},{"step":428,"item":"MILK","sell_probability":0.5,"median_requested_quantity":6.0,"support":3,"next_base_quantity":6,"static_shift_cap":6},{"step":431,"item":"STRAWBERRY","sell_probability":0.8333333333333334,"median_requested_quantity":6.0,"support":5,"next_base_quantity":6,"static_shift_cap":6},{"step":431,"item":"MILK","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":9,"static_shift_cap":9},{"step":431,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":450,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":452,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":453,"item":"STRAWBERRY","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":454,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":455,"item":"STRAWBERRY","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":455,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":460,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":6.0,"support":5,"next_base_quantity":6,"static_shift_cap":6},{"step":472,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":6.0,"support":4,"next_base_quantity":6,"static_shift_cap":6},{"step":473,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":473,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":475,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":478,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":6.0,"support":4,"next_base_quantity":6,"static_shift_cap":6},{"step":479,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":16.0,"support":6,"next_base_quantity":16,"static_shift_cap":16},{"step":479,"item":"MILK","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":479,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":503,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":7.0,"support":4,"next_base_quantity":8,"static_shift_cap":8},{"step":503,"item":"MILK","sell_probability":1.0,"median_requested_quantity":4.5,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":520,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":522,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":8.0,"support":6,"next_base_quantity":8,"static_shift_cap":8},{"step":522,"item":"MELON","sell_probability":0.8333333333333334,"median_requested_quantity":6.0,"support":5,"next_base_quantity":6,"static_shift_cap":6},{"step":522,"item":"MILK","sell_probability":1.0,"median_requested_quantity":6.0,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":522,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":523,"item":"STRAWBERRY","sell_probability":0.8333333333333334,"median_requested_quantity":31.0,"support":5,"next_base_quantity":31,"static_shift_cap":30},{"step":524,"item":"MELON","sell_probability":0.8333333333333334,"median_requested_quantity":24.0,"support":5,"next_base_quantity":24,"static_shift_cap":24},{"step":524,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":526,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":527,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":4.0,"support":6,"next_base_quantity":4,"static_shift_cap":4},{"step":527,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":527,"item":"WOOL","sell_probability":0.6666666666666666,"median_requested_quantity":4.0,"support":4,"next_base_quantity":4,"static_shift_cap":4},{"step":551,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":20.0,"support":6,"next_base_quantity":20,"static_shift_cap":20},{"step":551,"item":"MELON","sell_probability":1.0,"median_requested_quantity":34.5,"support":6,"next_base_quantity":33,"static_shift_cap":30},{"step":551,"item":"MILK","sell_probability":1.0,"median_requested_quantity":7.5,"support":6,"next_base_quantity":9,"static_shift_cap":9},{"step":551,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":8.0,"support":5,"next_base_quantity":8,"static_shift_cap":8},{"step":571,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":572,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":19.0,"support":4,"next_base_quantity":19,"static_shift_cap":19},{"step":572,"item":"MILK","sell_probability":0.5,"median_requested_quantity":3.0,"support":3,"next_base_quantity":3,"static_shift_cap":3},{"step":572,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":574,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":575,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":43.5,"support":6,"next_base_quantity":47,"static_shift_cap":30},{"step":575,"item":"MILK","sell_probability":1.0,"median_requested_quantity":9.0,"support":6,"next_base_quantity":9,"static_shift_cap":9},{"step":596,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":598,"item":"MILK","sell_probability":1.0,"median_requested_quantity":4.5,"support":6,"next_base_quantity":6,"static_shift_cap":6},{"step":599,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":14.5,"support":6,"next_base_quantity":14,"static_shift_cap":14},{"step":599,"item":"MILK","sell_probability":0.8333333333333334,"median_requested_quantity":6.0,"support":5,"next_base_quantity":6,"static_shift_cap":6},{"step":599,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":8.0,"support":6,"next_base_quantity":8,"static_shift_cap":8},{"step":619,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":7.5,"support":4,"next_base_quantity":9,"static_shift_cap":9},{"step":620,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":6.0,"support":4,"next_base_quantity":6,"static_shift_cap":6},{"step":621,"item":"MILK","sell_probability":1.0,"median_requested_quantity":3.0,"support":6,"next_base_quantity":3,"static_shift_cap":3},{"step":622,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":14.0,"support":4,"next_base_quantity":14,"static_shift_cap":14},{"step":623,"item":"STRAWBERRY","sell_probability":0.8333333333333334,"median_requested_quantity":38.0,"support":5,"next_base_quantity":42,"static_shift_cap":30},{"step":623,"item":"WOOL","sell_probability":0.8333333333333334,"median_requested_quantity":4.0,"support":5,"next_base_quantity":4,"static_shift_cap":4},{"step":645,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":647,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":7.5,"support":4,"next_base_quantity":9,"static_shift_cap":9},{"step":647,"item":"MILK","sell_probability":0.6666666666666666,"median_requested_quantity":3.0,"support":4,"next_base_quantity":3,"static_shift_cap":3},{"step":647,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":8.0,"support":6,"next_base_quantity":8,"static_shift_cap":8},{"step":667,"item":"STRAWBERRY","sell_probability":0.6666666666666666,"median_requested_quantity":4.0,"support":4,"next_base_quantity":4,"static_shift_cap":4},{"step":669,"item":"MILK","sell_probability":0.8333333333333334,"median_requested_quantity":3.0,"support":5,"next_base_quantity":3,"static_shift_cap":3},{"step":670,"item":"MILK","sell_probability":0.5,"median_requested_quantity":3.0,"support":3,"next_base_quantity":3,"static_shift_cap":3},{"step":670,"item":"WOOL","sell_probability":0.5,"median_requested_quantity":4.0,"support":3,"next_base_quantity":4,"static_shift_cap":4},{"step":671,"item":"STRAWBERRY","sell_probability":1.0,"median_requested_quantity":32.0,"support":6,"next_base_quantity":31,"static_shift_cap":30},{"step":671,"item":"MILK","sell_probability":1.0,"median_requested_quantity":12.0,"support":6,"next_base_quantity":12,"static_shift_cap":12},{"step":671,"item":"WOOL","sell_probability":1.0,"median_requested_quantity":8.0,"support":6,"next_base_quantity":8,"static_shift_cap":8}]"""))

for frame in (gold_games, public_games, v21_games):
    for column in ["seed", "seat"]:
        frame[column] = frame[column].astype(int)
    for column in ["margin", "my_reward", "opp_reward"]:
        frame[column] = frame[column].astype(float)

assert len(gold_games) == 96
assert len(public_games) == 96
assert len(v21_games) == 32 and v21_games["seed"].nunique() == 16
assert set(v21_games.groupby("seed")["seat"].apply(frozenset)) == {frozenset({0, 1})}
assert v21_games[["my_status", "opp_status"]].eq("DONE").all().all()
assert len(shift_windows) == 98 and shift_windows["step"].nunique() == 64

print(
    "Validated frozen evidence: 224 local games; "
    "the V21.1 panel contains 16 seeds x 2 seats; "
    "98 static premium-shift candidates span 64 steps."
)

# Mechanism diagram. The quantities are illustrative; the invariant is exact.
from matplotlib.patches import FancyArrowPatch

planned_next = 30
shifted_now = 12
repaid_next = planned_next - shifted_now

fig, ax = plt.subplots(figsize=(10.5, 3.5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(-0.28, 1.22)
ax.set_ylim(-0.28, 1.55)
ax.axis("off")

# Quiet time anchors.
for x, label in [(0, "turn t"), (1, "turn t+1")]:
    ax.plot([x, x], [0.03, 1.12], color=LIGHT, lw=1.2, zorder=0)
    ax.text(x, -0.08, label, ha="center", va="top", color=SLATE, fontsize=10)

ax.text(-0.22, 1.04, "Base schedule", ha="left", va="center", color=SLATE, weight="bold")
ax.text(-0.22, 0.27, "V13-R3", ha="left", va="center", color=DARK, weight="bold")

card = dict(boxstyle="round,pad=0.65", edgecolor="none")
ax.text(
    1, 1.04, f"SELL q = {planned_next}", ha="center", va="center", color="white", weight="bold",
    bbox={**card, "facecolor": SLATE}, zorder=3,
)
ax.text(
    0, 0.27, f"SELL s = {shifted_now}", ha="center", va="center", color="white", weight="bold",
    bbox={**card, "facecolor": ORANGE}, zorder=3,
)
ax.text(
    1, 0.27, f"SELL q - s = {repaid_next}", ha="center", va="center", color="white", weight="bold",
    bbox={**card, "facecolor": TEAL}, zorder=3,
)

ax.add_patch(FancyArrowPatch(
    (0.94, 0.91), (0.12, 0.39),
    connectionstyle="arc3,rad=0.18", arrowstyle="-|>", mutation_scale=13,
    lw=2, color=ORANGE,
))
ax.text(0.50, 0.76, "12 units shift earlier", ha="center", va="center",
        color=ORANGE, weight="bold", fontsize=10)
ax.add_patch(FancyArrowPatch(
    (1.00, 0.87), (1.00, 0.43),
    arrowstyle="-|>", mutation_scale=12, lw=1.8, color=TEAL,
))
ax.text(1.06, 0.66, "18 remain", ha="left", va="center", color=TEAL, weight="bold", fontsize=9)

ax.text(
    0.5, 1.40, "Planned quantity is split across two turns",
    ha="center", va="center", color=DARK, fontsize=12, weight="bold",
)
ax.text(
    0.5, 1.24, f"Quantity conserved: {planned_next} = {shifted_now} + {repaid_next}",
    ha="center", va="center", color=SLATE, fontsize=10,
)
plt.tight_layout()
plt.show()

item_order = ["WOOL", "MILK", "MELON", "STRAWBERRY"]
item_y = {item: index for index, item in enumerate(item_order)}

fig, ax = plt.subplots(figsize=(11, 4.6))
scatter = ax.scatter(
    shift_windows["step"],
    shift_windows["item"].map(item_y),
    s=25 + shift_windows["static_shift_cap"] * 6,
    c=shift_windows["sell_probability"],
    cmap="viridis",
    vmin=0.5,
    vmax=1.0,
    alpha=0.82,
    edgecolor="white",
    linewidth=0.4,
)
ax.set_yticks(range(len(item_order)), item_order)
ax.set_xlim(120, 680)
ax.set_xlabel("step used for one-turn preemption")
ax.set_title("Static premium-shift candidate windows", loc="left", color=DARK, weight="bold", pad=24)
ax.text(
    0,
    1.02,
    "Marker size = static quantity cap; color = sale support across six representative replays",
    transform=ax.transAxes,
    color=SLATE,
)
ax.grid(axis="x", alpha=0.14)
ax.spines[["top", "right", "left"]].set_visible(False)
colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
colorbar.set_label("sell probability")
plt.tight_layout()
plt.show()

window_summary = (
    shift_windows.groupby("item")
    .agg(
        candidate_rows=("step", "size"),
        distinct_steps=("step", "nunique"),
        first_step=("step", "min"),
        last_step=("step", "max"),
    )
    .reindex(item_order)
    .reset_index()
)
window_summary.columns = [
    "Item", "Candidate windows", "Distinct steps", "First step", "Last step"
]
from IPython.display import Markdown

table_lines = [
    "**Static premium-shift coverage by item**",
    "",
    "| Item | Candidate windows | Distinct steps | First step | Last step |",
    "|:---|---:|---:|---:|---:|",
]
for row in window_summary.itertuples(index=False):
    table_lines.append(
        f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |"
    )
display(Markdown("\n".join(table_lines)))

# Queue comparison: the same three orders are shown in two execution sequences.
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

base_market = [
    ["SELL", "STRAWBERRY", 24],
    ["HIRE"],
]
shifted_order = ["SELL", "MILK", 6]
queues = {
    "Front insertion": [shifted_order] + base_market,
    "R3 append": base_market + [shifted_order],
}

def order_label(order):
    if order[0] == "HIRE":
        return "HIRE"
    return f"SELL {order[1]} {order[2]}"

def order_color(order):
    if order[0] == "HIRE":
        return SLATE
    return TEAL if order[1] == "STRAWBERRY" else ORANGE

fig, ax = plt.subplots(figsize=(11, 3.8))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.set_xlim(-0.12, 2.92)
ax.set_ylim(-0.22, 1.68)
ax.axis("off")

row_specs = [
    (0.96, "Prototype — front insertion", queues["Front insertion"]),
    (0.18, "V13-R3 — append", queues["R3 append"]),
]
x_positions = [0.08, 1.08, 2.08]
box_width, box_height = 0.72, 0.30

for y, row_title, queue in row_specs:
    ax.text(0.08, y + 0.25, row_title, ha="left", va="center", color=DARK, weight="bold")
    for index, (x, order) in enumerate(zip(x_positions, queue), start=1):
        color = order_color(order)
        ax.add_patch(FancyBboxPatch(
            (x, y - box_height / 2), box_width, box_height,
            boxstyle="round,pad=0.035,rounding_size=0.04",
            linewidth=0, facecolor=color,
        ))
        ax.text(x + 0.10, y, str(index), ha="center", va="center", color="white",
                weight="bold", fontsize=9,
                bbox=dict(boxstyle="circle,pad=0.20", facecolor=DARK, edgecolor="none"))
        ax.text(x + 0.47, y, order_label(order), ha="center", va="center",
                color="white", weight="bold", fontsize=9)
        if index < 3:
            ax.add_patch(FancyArrowPatch(
                (x + box_width + 0.05, y), (x_positions[index] - 0.05, y),
                arrowstyle="-|>", mutation_scale=11, lw=1.4, color=SLATE,
            ))

ax.text(-0.08, 1.58, "Same three market orders, two execution queues",
        ha="left", va="center", color=DARK, fontsize=13, weight="bold")
ax.text(-0.08, 1.39, "Each row contains the same orders. Execution runs left to right.",
        ha="left", va="center", color=SLATE, fontsize=10)
plt.tight_layout()
plt.show()

assert queues["R3 append"][0] == ["SELL", "STRAWBERRY", 24]

def summarize_panel(label, frame):
    paired = frame.groupby(["opponent", "seed"], as_index=False)["margin"].sum()
    return {
        "panel": label,
        "games": len(frame),
        "wins": int((frame["margin"] > 0).sum()),
        "losses": int((frame["margin"] < 0).sum()),
        "win_rate": float((frame["margin"] > 0).mean()),
        "mean_margin": float(frame["margin"].mean()),
        "worst_game": float(frame["margin"].min()),
        "paired": len(paired),
        "paired_positive": int((paired["margin"] > 0).sum()),
        "paired_negative": int((paired["margin"] < 0).sum()),
        "paired_positive_rate": float((paired["margin"] > 0).mean()),
        "worst_paired": float(paired["margin"].min()),
    }

panel_summary = pd.DataFrame([
    summarize_panel("Top-route replay proxies", gold_games),
    summarize_panel("Public strong-route controls", public_games),
    summarize_panel("Exact public V21.1", v21_games),
])

summary_view = panel_summary.copy()
summary_view["record"] = summary_view["wins"].astype(str) + "-" + summary_view["losses"].astype(str)
summary_view["win_rate"] = summary_view["win_rate"].map(lambda value: f"{value:.1%}")
summary_view["paired_record"] = (
    summary_view["paired_positive"].astype(str)
    + "/"
    + summary_view["paired"].astype(str)
    + " positive"
)
summary_view["mean_margin"] = summary_view["mean_margin"].map(lambda value: f"{value:+,.1f}")
summary_view["worst_game"] = summary_view["worst_game"].map(lambda value: f"{value:+,.0f}")
summary_view["worst_paired"] = summary_view["worst_paired"].map(lambda value: f"{value:+,.0f}")
display(summary_view[[
    "panel", "games", "record", "win_rate", "paired_record",
    "mean_margin", "worst_game", "worst_paired"
]])

exact = panel_summary.loc[panel_summary["panel"].eq("Exact public V21.1")].iloc[0]
top_route = panel_summary.loc[panel_summary["panel"].eq("Top-route replay proxies")].iloc[0]
public_controls = panel_summary.loc[
    panel_summary["panel"].eq("Public strong-route controls")
].iloc[0]
assert (exact["wins"], exact["losses"]) == (31, 1)
assert (exact["paired_positive"], exact["paired_negative"]) == (16, 0)
assert exact["worst_game"] == -176 and exact["worst_paired"] == 419
assert (top_route["wins"], top_route["losses"]) == (91, 5)
assert (top_route["paired_positive"], top_route["paired_negative"]) == (46, 2)
assert (public_controls["wins"], public_controls["losses"]) == (96, 0)
assert (public_controls["paired_positive"], public_controls["paired_negative"]) == (48, 0)

v21_paired = (
    v21_games.pivot(index="seed", columns="seat", values="margin")
    .rename(columns={0: "seat 0", 1: "seat 1"})
)
v21_paired["paired total"] = v21_paired.sum(axis=1)
v21_paired = v21_paired.sort_index()

fig, (ax_left, ax_right) = plt.subplots(
    1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.45, 1]}
)

x = range(len(v21_paired))
ax_left.plot(x, v21_paired["seat 0"], marker="o", color=TEAL, label="V13-R3 as seat 0")
ax_left.plot(x, v21_paired["seat 1"], marker="s", color=ORANGE, label="V13-R3 as seat 1")
ax_left.axhline(0, color=SLATE, linewidth=1)
ax_left.set_xticks(list(x), [str(seed) for seed in v21_paired.index], rotation=55, ha="right", fontsize=8)
ax_left.set_ylabel("V13-R3 final margin (coins)")
ax_left.set_title("Per-seat margins: 31 wins / 1 loss", loc="left", color=DARK, weight="bold")
ax_left.legend(frameon=False)
ax_left.grid(axis="y", alpha=0.14)
ax_left.spines[["top", "right"]].set_visible(False)

colors = [TEAL if value > 0 else ORANGE for value in v21_paired["paired total"]]
ax_right.barh([str(seed) for seed in v21_paired.index], v21_paired["paired total"], color=colors)
ax_right.axvline(0, color=SLATE, linewidth=1)
ax_right.set_xlabel("seat 0 + seat 1 margin")
ax_right.set_title("Paired seeds: 16 / 16 positive", loc="left", color=DARK, weight="bold")
ax_right.invert_yaxis()
ax_right.grid(axis="x", alpha=0.14)
ax_right.spines[["top", "right", "left"]].set_visible(False)

plt.tight_layout()
plt.show()

display(v21_paired.apply(lambda column: column.map(lambda value: f"{value:+,.0f}")))

chart = panel_summary.set_index("panel")
fig, axes = plt.subplots(1, 2, figsize=(12.5, 3.9))

axes[0].barh(chart.index, chart["win_rate"], color=[TEAL_LIGHT, TEAL, "#115E59"])
axes[0].axvline(0.5, color=SLATE, linestyle="--", linewidth=1)
axes[0].set_xlim(0, 1.04)
axes[0].set_xlabel("per-game win rate")
axes[0].set_title("Frozen regression panels", loc="left", color=DARK, weight="bold")
for index, value in enumerate(chart["win_rate"]):
    axes[0].text(value + 0.012, index, f"{value:.1%}", va="center", color=DARK)

axes[1].barh(chart.index, chart["paired_positive_rate"], color=[TEAL_LIGHT, TEAL, "#115E59"])
axes[1].axvline(0.5, color=SLATE, linestyle="--", linewidth=1)
axes[1].set_xlim(0, 1.04)
axes[1].set_xlabel("paired-seed positive rate")
axes[1].set_title("Seat-swapped aggregate", loc="left", color=DARK, weight="bold")
for index, value in enumerate(chart["paired_positive_rate"]):
    axes[1].text(value + 0.012, index, f"{value:.1%}", va="center", color=DARK)

for ax in axes:
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.14)
    ax.spines[["top", "right", "left"]].set_visible(False)

plt.tight_layout()
plt.show()

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
    'c-qZ<XSbqQv+(!+71}Bnw4Ezv#~ct8vlx4|NK#Oe1QpY7e?jFO&*?Dp+<QN~XU$qIJ5<%KU3qVqFJHfY9dN2hSz(sbggwW47?Gpo',
    'u%;-I2dCC+O<+vXFg4DjaXLq74DVqmnH5;d;QspZh2S}lswu3=7=j{u42@zq&w<jNU$V|<0&Rm_X*MwGK0^2G1zn&;&LhYkMYboK',
    'v?wq(aEFM$zH}6iu9%t)gi%<|qi7z@lnp`Ro+E5945#ZJLHC$C$NuH<I20T-N>w?{L$R!GLlrF#Z`1gN5{0!aakBBvLo24t+N9W2',
    'C|X!l7)taUIJ?0HO9|RHk4~*P&k$*~Yz9!0D#+_^9vg;dCCK(ro#)suqOdcab=%AM>x<2}FM^~hn&F`-olC~uCq_{%_xDCuWcT+;',
    '6zDHszL4cA(dc%Dp8UP{FHxab9dtVXVmU^URGZB@_yGAAolZE7EC+&LJoevzF=1_+>lWtG(st1zmy6y$m1(bxGZ1P?)k^g|nQtux',
    'ZZ;yFX`@j>fJXNaKzG;8?2s0QXck(PZ!Iji;qXl|Tv1iHU!|CRwopEm7_kQoxL}8c{_BB?lR$;(2`C`qGx4M;!yqt{vRra=$rvGD',
    'o{H|rxqMPYLRQ)zKesL;nVFsr^re{`VkK&><VFE+CXj3I4#Kjh2d~zo(_SwIrFpvm&1Vrn8c$|VR9JpjIjrIvqJj_Tk-EG_3r8hY',
    'JP3If?zKxyct7bYvZCjSOr0IvPOWGGE>#;$fp4bB9WfctOQ8cpWc`<H|B5aQs+m7t*IrdXm*@SYv<z5W^oh!6K-MkX*5&<TJm@Vr',
    '8ZSfyBN$F>I$pCyD#A@2mMchz6^5kuOq-ZL*K4;<GTH0O?Z~>^>Q1|r3A6Gqh!KAXhcB44>p>H1Kw?HWuxu{5$<akMS_U*`>P>IY',
    '9nF#(JW_%~bi11gR?K6PW)j$C+rYwHe>Rf=!NTAXmkuA($I7LX#rJ@)pX7*Pkfz4F6AL8=Yb+!7Bf8i^t@Li$+0I+rdgO@;qVUo6',
    'fD4$K5-<^^!+S72JEjA;-njS)njde*bj};Et_MufG}pt!spl;ed}ddN^@_R9wHnzS##42LTon&JJnZ*xGt5H0TtnSTsm?9uL4kdu',
    '3MYne_;~FwR>o{;<V;`Ya%LAercZm8LF@4~1=p{8fZnKKtx|x-rCWGlT+j;|JxbiACx|#TMGSFS8=TMbMBJT4e>%m8fpA>AG}`ri',
    '^=v6mRF&plfe<;^6Jq5udk9NQ9+E5jzACcW{2JSvh5#N``%KFSp#H(WIG^VG*X$^eEz}ml9x~f>QoBrcM8+aR5CnQ1lw3@%5vc&3',
    'OTC)Z4dUV+aTz!*sYo|@X=>FCdeuAi$Ud6nCm}fiY}xn_&uooAYd*U%T=;-(uY>CzJGHk+DRxOWBz3J2OL*e%pAF$AkAg-BwRUw(',
    'F#N!|Sc8{?5gDo7!cSBexF(eH7@BCF$w6R0FJXr2lck`4uNC&$%`N4RZi<=s?ikr8_Iwcyj%MS-p<3wV$uM+G<;oIWuBLjH!h{3p',
    '9-@vh1!&iTO9f^^>-CAT_}t`)Dv@n67FjRv^{sRiNbiv3n*x!7rm=3~)(qiQZQW`KoVtvy3Pcm(R#ZM&j!dbp+{@JFeP003f^_>B',
    '=FR!UcgTeE-R!7-f$>RT?XUaGx!8zxRrpZJ+>$<~Xv<Q*A6BbvqQxnzBDl1y<qACxsqVf4ucD{yel4Qe%P|6P2l>+tUsex3i4Ju)',
    '_=UkcMK0J2=tyYX^Rr5xw=GSgpqE)?8y=zl<P#N*UubXq6y3y-8iHN*0G3fQiBxf1=9k5d)}_`eeXOwYZ4VDDWYF{{!&J%;mZQ@w',
    'n7HD4JfV-fiG8DalvncXaGjS3RI8$VeOkzN2LRh(Cz&Uz;ANPj*anIe{ITdLnc6b&c08w(wX%L(N2vqF7b2Nl(5D${I1L4kqouAT',
    '#?^FdkCe84O(Y3@o=h$ylNAq`1dit;J$lzwn8Li!2ZzNim~6S`RshP;VIK_!dF{O0rpf`^?skr+_4Q!Qu#Lp==z66TkE2?08k1&h',
    '1|ef%fDn=GB~MJ)Xvq)q*UtC=mnKxOdn!rfDs`Bj>1k<k2otegyJ?MGu^?CTb-4!?)#+T+m%wPzj8zH=yp)51(GE{%5+WS#)Wkv)',
    'SI3bZmh;wu#8qFU+wpN^Wuzmt*r}drx-#i_x7aAKtEpM0xY#7O#eHTi!farg(4VN}j#3P!q2;+dN+YVc-0xE-Xn-;aeYHx@DYKct',
    'kFioenbxglQ9JNRdQh>w#?k~z*gSL&q=8!ac4d#93l28BYTRh^-tB33o+M1Dwxt66?U;X}THbVjta$Nmlp`-@=QJTER(J)ac+%Vz',
    'o25Xq1k@$jUxLz-w|=SBM_8=Iic@5?0gC>-*$~%-cCJjC`D(J&igVqr7#{oMMRUlq9g_z9>S(!qqMB0dL5W7Ix^A0TfKM#LwFR5A',
    'l`=_LNE7kxwO(wSiwuO-v7Zg@u}jF>+}1f_v9kSFG-~0AESX*rg=C<|HZT13Kt$0^f%Fa4aXunIK>`rCCn_}6xMf<E=4v0pDFrlg',
    'iBMx0Xb!z$vFOLs$zGYF1Hl0YwUw|gmRjVwTrV+%0sB`zhUx4=TTmPZ#YUZDpykxN$A<-ijkmigayq7$O*ur!rzfg*K@9l>Yt-!O',
    '+VC7(My9}c8b9o3NSE~S*&bRWeP|BbYTzy|kisZ&fHpZx0OP4CQ^;g%;bXEfpG+g+88%vMdibg{5vYnf&J@#~NJ^5u+M@GBm4oJ{',
    'jC8;pIF1XODYD>3g*+|wCQT+6PNzf(Esp@EahXUKPi0dOlc1<_wX|8T=J9SL&!-l#LXeA6T3qT6#{C{2^Y%_hj$h=)8LQd_=L?Q`',
    'qGI97pjFAW`{L1TT!)T%qnn&q^>=DmVijq_%H?#O^+x9rmfGZln{d^D1{$#Nm*i0;rL!UCI838upv>3vdas}I5>c<N(4~p!@0QFa',
    'Aj50vi7JF^{C3=}nd=xk?RAEi(8BN*r7S`=Za!asXhFUCzAH-A9@L%Yt71rpt1M7!9A~)#cd40vbIY_l-DIrM0CPq$io;gf>JRb=',
    '+OaJ(2B)>U{6w|hq2hq^MlR}nv1P(A5}c|;HSXn?!n!c#TD#ujcwAiv%1tVE>!<a)?>hw5RgBJBN}@SBD5t{Mm)!zWxP|QUqk1HB',
    'tn91Y*%~iY$~*1cpcv|^uqo}4zPD-(O*x(;$1RR0QlnEkU=*=_Wt_?~QjF@JT4+zmb~}w$F-T>50bd`Xxt7S)GPktp%L9G33xF|f',
    '8O<jTT6y807o`aoMG7&r?nA4tWf%R}YH}IvLJ7niYG`@iVvQ!ZFP6LO7%IwmM#3`m5J8LM))m{|46&|BbTobSB4*Q9Qt-TGtNdOw',
    '(CfI)REF#81&K}8ZDE+ak-{y>%D%u86`nKZgh+y=g(Y&LzuytYfjyy0&BSqbxxjp9n#;9gE&s3@nlw!!CNC8r-)Wq#Rc<}ff<CN2',
    'HCYB^Xm2FtO-qYxJboDGkF8+@Fnt>ze+W(RC#uM}6tyP99CF_EX0aI_fdajHf8AZ3Quwu(NW_+8ULFfJQ=;akZ~1vy>cP|4p}*Vb',
    'Q@%0<PmI7$HZPG2)9muasmu@OqeH1HSM@VfjHx>qb@d8a$k~K0r3#ZA(x-T@hygM(kV}zHNw4R`*=3gT2B3p7%C{D$pt>m~=;(T7',
    'k)s1&3&hI!e%(v>Qe+92h)|4~FAhH5<i?#)aXXLn=Oe9>5QHbHVFJL?`}QqkN~{&^L<_S;MU6)xe7A!z-!LHcww8INjwz+0aa!aW',
    'm><C~KAgvD>|l^$E}M7;Iuj*uv?J*q-s*?X%}#om$aJea)X1^hQYw3WqAHDm>}u}C*A2Y^9+h)pmx<NZBpQrjc&^|LS1_<O5<=Q)',
    '+^?dUZ5VD02iJ1)wAT)ZmcEJ6nE+mB<$RIocz@H!=F@XDCk#sdbY~Vug$hk!ZgAF$R*natS8NYbAu*q7UlIbg*Us(C0o^o33#^rL',
    'kQXoZI^3buYLCyp;jxpD3eAPmJ{5(i%A6YfKm^TY!dJ7PON>I#@F_B=EXgFin^g5`X6$An%M%w!x5~lekU30!z~scArh&v+=#12&',
    'dfT1$vE<4-E-+?fzY^j}tTM=jsfC{11z5feYzFnnFc^*-6j9{#a)z7w@gy*S$>IuX`3guWmr4(sPgLc3h{vZ|02tPJ->E$l7jzPy',
    'a0hKtR1+CYByX!$W`#DkLt_x@ho)BvlW?t84lG-TL#tCgEuu7|!H}XcF)|HRS7d+I4S{nKtQTsbLl3aFpc`9E15_SZRa0JolE<Sc',
    'P#X*mfniZjt|+h8g0jgSQr+n!7L8@SgQE~#R@2jN7&&tRRj`Il1fZJRk+#lh0JO^EC2@3xV|r_~^+VCoGF^;Jrw7+x!SN!jHm5>0',
    '17`+R+@G|3iWUHM<Qh$c6)t^)+oxWCqNyvCJWMja1h`jbdaZW2p_ZOk(fG8T6`H|{08u@zY$baf&E&bjc2-;$!D@2ILhuvSBC6#0',
    'jC2}QK-hNTQh&l9DjmpLSH}BeezhqI6`};oIvUcpK#TPs&SN|E0B59~C#Oq>fMMQ4Zh<Rdv(qJR#Z~Vl$lYL28H~N1X`M^dg^6pJ',
    'Cbjhpo~0sQZC$U)2|KsNQv;)B6479?W@S^pWi#2*q#?d6(5HA9mv829510#mY=sJYYEta>yLoSCxJaExjVidE57wMd-|n{ua+~IE',
    'NDhs;`PIHp=cYYFGuZZ;53YJ%aSHB@B~o3U3|}p4KwjD!?`AO(_njuIPOYD<iAlV6maUy>d1L(%xu!}CB`WF>Kb}zFY#Y@9n$0iv',
    'tt6pi0e?5`u8LUed0ku&%Nl237&WWwmr$%1I$suWQ7<m=5nml)L%LUn&TJ}z)zjoTuMF`mHod`gvfiAjj9*zzOGz+LndI@dHmseP',
    'Gf#IrbJE|*ly*?jjcyn4Wk<pYF~m3R(Ct=c+NMM`y|YHf3Nkq#Wa`C4@w7{m5pW}dokSl$)lVcqP?yaa9!taEuC?O3h01a4-JFrs',
    'G9O&rC@`=hh?zHnljo9Oa;=3Dm^HVnWvfi=dK05%yJ~xi+)Fiz3xo{iPt(<56Qr<O@d_WUbc!s-$B20>S^UX5S#~;AOyo<)U<oi3',
    'Qz}J|e(Ab5(sZmDYfYJRaWo2Chb{v*m2MzAhdLd>V)MmVB!4o>!_~w*iS&War*mGq!F4kiD894Qsd=+))FBQ}>Vs;mf7w{Vh-(%0',
    'd>&b3JIc~d{uj{FtTftKFQ=xgIZ&Au`)|dB{Yc26la!C4D`&ovGEO}*Z6^VJY#qhK5*(6JNGIOQp>jwKYDlb_SXc3COj(q26cNl8',
    'E+Jno>ZSITjUSk0CY7*o!*WpzEckMJ4Wp_NO+OT#sPxz^S;>MesU6!K8q$0y*Oc>WLv0%%&0no%+&3A~GpS0O6iyCi=R>m*632%|',
    'IKQ=`Z96yxHo1(sUqnp++V{&!=UD4Qd_2D$6o<{)F*@e^<`Y$+zy@wxIcpJ#RQsrEhFK6|5u!DRl#$$9m*Im*3x_xm$zF&Cax6jd',
    'bpSkGyvx36@u3(2&-{g@<X<&IXfi5o%EzVJ0J`PMVF?-i9#)>f``Q!L$(xyT=xW&>au9qtQvwfgt1#9;@oLVyvGN+x+7Gxgf7o9w',
    'jSa!$4B-XTWp~U4Dqs!p4M~553Ke;LHabgI6c9us){2#4i%TZEt@g#Ow00BJ0ophRTj~;9)kd9W+`pxXP4XgO$)>Mh9V=)QNU~K(',
    'Sg}}RCuxaRN)_4!k?)_Ia=y?x?K6=`Y(yYuyc$R_?ZnD^ZL8fDyp9JAix}x6bGLE}KOJ0)9Fcr8TddwVNLg`mra0XpKC&J3A7e}o',
    'PRxkTEx`IZSClZg$r?T$56S$h+9m^jQ(4oAG<UtFtWid!1E#X0uWbZG*h03T&=kJVB!9H>L^TFi)f~L{$2-yEDVWYjtu)+M0S3%e',
    'N_8MK>Vqvmd7*{+neeeF&7v5zT?IF-{bH%D=~bCTyNy*}G#M$gwbrFH6YWj-rQC!i?G)Y&8x-AfV~eUSIQ}lzS#9dmzBVtxQlK0&',
    '6%*{W1KWkRGreA_+gmHgk_>JSA-TNd86lJ@G>kRvjcym`UN<QQ4p?1{@TsuKD*IkfWPH;duMpOL0q6^B{6ytF*0k<CcvECvAg1uf',
    'H2EqL*-tZllPZ)q+AJJPCbdEtNjH;=)-+#&`RtXG$nK$b+bql?vbX%T3S6~w)7?-La>-*<_ksz+pvtswIuV0P#f>fcoL53K%<&>H',
    'eyTI5FOe+_7mvZn!MD+3gF>pD&J=P~1C)Zz375UZvjaTV%J1_vSf_%a${;#MQ(~||F}X#k17GZXjJJb(a*H%6*<A19`dD*ox7b;P',
    ';=bG@Z(UBITdSYC(S<&|El;7CZyXB|q8aJx(+aSW1H+PS@sY^1jY!hOU#@I~oi=BB!E}Xa0pnqMUPC&KbUCx@&iDgo;pf2IcQnwn',
    'n;ww8cB#wlC&O?a>=gt7@2@3#bn9iS7FgmY8)OypFAl8WCk9(SQVgHwf!qksHw@Tp4ll{nh+Q)y)EB62qbgv^<7R8tJ`{;GlkS+)',
    'Vh#k;u3>6!*z_tz1Vb&HD(5@0okWadd;W|p5VN@2UrJ3MJzo;Nkx3qs?X41uG@$mr++D<Ofl940ELw_1QQ5h#TG8o5E5Vh{)3wme',
    'riFt)RI8%WxJo}!sq&@6Voayv-JU1Y^Pz{U+cl?vz;PN$mLwpWZGfrbavSk;R%y3tcg(6}6tAbsp}Nbp>ro&fC`z5@rX5+$w@|FR',
    '?<{r)|FAo)99a!YoU@hf6IJ%sAd3+RmNDOP2q38oJV8RacEd02>}0dSKtaa4K9?esdNU6s;$bX05P`tHB_s$i9m|!l;As<E?sH7A',
    '8C&iS@g#Gt^npZ~05jIDbljnO#Vsa;cU*81D7AytLTjPs^YMip@|nUo=-o;CTtQ31i{RYy?IoStZn!Sm$Y_`0XhiAT>?twmkAbLP',
    '7!FQht6H0M1Gz|}o}SA(?@cDONNE~Asr|I&MohR4W3{2Ui#N{7AV82qeS%jiZDLrt2!&3&crjvlbZ>&O^I9K7)<CXWD=#FP?4|@M',
    'U8qO<c0M76NHCVJNnA_E&x^>iJxO=ix;!mR(Cikbo~Tkotl85}W8N6n&{RE9B~u9k$%aO`d3WC23d$)S=?scxn8$6z+h*J9=4MM4',
    '_Mz?K6jHh3cx|VAq-FFni;{l`G;iY&pKL6*vuL}wTn?*xC-FpOl&P6|^1|l?vXn7Bg^$j`cw#%Aly?yX8FadPpiU~$G7@i&XHf}H',
    'T*+Qp8{>&uZSK!yP8ExdSEHf!VPR+O$fVFI+Uvy91K-GyS2AT~NZL*1s?8M!B=q&c0G7Ana4ql%v(;N2d@SdDqCc9|<4QKWiuxxa',
    'pj9pf{Lqy)iN&!29)u`9>K_FftJ<EVk5qXx5C%u*h%f<e!{$EOk8}>{CO7T55fhXtSJ>(Cu!iSL83(rAaI-U$(E~`Aj4^+!Dy1TI',
    '<%-$kEqQCiwpo2YC|8f8h&Q-VCsS}eN7tuT)V~adgi|l!&m+ZKKwXqlTzVNeL@|WTyVV$--?srg46VI-FlWjF=2g(>oTy#%b8{aW',
    '`jGsD0+`KGDGaV&N$FMdQCJaHBX}ZJ;YOjvrE`;pP}(!pNf-PDeP*kEE}<atZTmba&XY=OxpC`(6(&W^)?p^bR|=CPS_rRVK_%fY',
    'l;~Wx2;*dD+0dmlUQ5|1xYKeu*er2;-ii2WJOS*wmsFuTTAl!0@q(LmVK`bSGk^bR>Wtn7x_$r)a>FMoxH~A@34BdTom!{ke!!FK',
    'RY-)7%i}EH<#{^|NXOcz*t`|?<#Ie4E!F)i7!9a{EwU(AQWbP{8iB36Vu!QUR8c6e&E4Xv`s*usXyzwYM$07KI1n6*IXNCwn^9sc',
    'qzJj@Bf14ZPc^_yHn{=f&4stYNA~e4P2_`}Si!puCHZWbl6z_h+nC#IljTc9aIap_aQtY7R+DoaI<=T4YX*ipq7`Fhz(uu4D%PAl',
    '$<nYlMQ6Lbk{Hs&5H6j(p(DNb_f8#)@a88>zZiwLh!JMgLuVL?di}9DqSeCuvdFf<-UL{0{n37lmi(v8AkE}9tMt5C!&}Lsnth@=',
    'pH`Cso>2W|I%mz>xl414joQ~`E@yR@-~x?|S8%#VcBFN1lbMm->5#Z>%y6#S=t{{D8b{cAeY1-t;M&<ZX=j1$mWX{LTif7s7EGpF',
    '>5|uVBG7sqzRkqrqO+|9QM{i-Ru`zP)tgYUTp>Cm20*hyqamDpaH}MZW)YL)z#KBF?)E}w*A;5>UfwsuZ$KUj0xdcatQy|%)VQ3&',
    'hPfC}(dbxr>+B&0D^HIzD7+cm^zg~{-Aw$b&pK7U6_?w5tr%QRqG;%(O)hNQ$Sy}lHaI?x0ZwkD&3&|GKw4~5vD$T8MXc<g4y{?^',
    '##cI#qY)?^TLRP|7Vfz)y&Dw^>ll%O2Ss912uad@TyD&~v1Gx^Px{GzK&VXu-qh;E?>DV;^33IPjEY`~BRc^@ZErQ*TrO8+-n(5$',
    'fj~YpO(oPx)~YVaP_Ed-Z*=diL~<*fVn`~nXAWDqkcvm3M)d4UnEh&by0hbdm^mGbv6;-P>1!aez&ZkRF^A_GUNT1ExHU8JARbDu',
    'Z0*!&-ES4_q|8XgaSHYO<ce}mPSJ~7q$`iSx8i15V}TwS<!ygkYb=bu?=nu&G66LGHGChRj35re?5s6{?FI=zzy))5YGNi4ipD3f',
    'W)gK}SB@6(U@)oHd8~XrZbJ<zSl+^my_Ko&o~ZbsPAkFV2=do)EV@{XrM-f%x$RLg4s>R6?GtF~f>sfzT4oBh`bwKsljcAOr08}f',
    'C935UHmLyl&}<swv1>I@VKZa18jIE=ad|*@&%q=&b_=S<zAw@Cn!Y&%udbuzWGCw&V}j|S8i4}ogiz1k#0hJlevYN<MrYCYAIzN~',
    '^D<LdlbJ!WyP8wERQ$wcq1c44f~3|AQ7APDq5%{ub(9GlUc176wbOeQjI88!gKSC)XsU}Oc`fw4W;%SRGL7|os+O+@wVGl5yLD5V',
    '$Ce~;5w7V0xT4JtGbkoUn@J^AUGwNIaGK)rCW17pTo!F6&Mje7<;zc0)Q&%eqlwnCU`)(#M;fw`F=l2v={S6Z2F3#Rtq03%t=Xf}',
    '6RLG;T>{-G*As!m0$0~o5s!Bn?@|n{cFXB@35>~NZ#~#{#Ra2s2tzahn7_EkFS7vRRjDmdN0U2HE&wI(t=rp|eY_G}_XcsrqN|D8',
    '5XA7gH6Ng3@)-2i=W?D2RckuM?!=-U)Rt;e%geN|EOrjo57(yYJB%0+Tn_lg0*RF3PgIR8Vg*N+7O`TL8M4_hna!{r0Nb>_3RlYJ',
    'Ww-5Or=U_;Sc=!bTxikc7~a7-K5#we<W6wZ)ki*G!XH~3!a2U!q}42fb6Aqe7X}+LqT@t|b@Qv0Kwffof`Sf5lTi)C)7Qp?hoi;Q',
    'O6i}X?bUUh$!)He4ehm)@71AwsQTu>u|d+!{yraP&3HL+Ue`+t{Y1j^R(`!lQk&z-VA~Am%cM3cRT%W$;&(Q>+!7nkWD$QmF<F|c',
    'qQ#bgT_(r$8kvsR+^*F~D-#R!&I84JREsU9Jkv)=REgC$lR|$Vp*nW@j3pQX-6Fow@De?2BI!m`+(j41M4<-(ZhFw<(#WYhAHjT-',
    '@zR$DN*w|)a=TrFw=q&Q1XkVZu-sZ=HSOw6^h%H(gf8Cpp^zwe6I}PiDM*MZ$3p!Su`lGivB<Wn5#vOtE>wY3#HcS)7uPlV_=UeX',
    'J{xRvt2Gm|w33pdsW~6)jg~&GP+Rib30n7Sz)Hww8cHMtrm9pX!BpjnKRNc&H2_7rWq2>2&2jaX9yN;ke0||zxpS%3kMf~W#)9rG',
    'l6b$@wMzbcRV@$+qc>{B`0V76rY&zWCkVcj0Ax3I0@0P_@ZeHw`^jamM$p8HnZ~z~+A<AEIkjsweEg^YX>EFws@_7BKLi>f9>kli',
    'brHuzS1jTNvyN80uy?g)EOq3&oD<k-Bh=G_1GAX}_49SItFqp@1kG@t7(=}hC#9)rqmd3I=<WG*@V2}aC?{34xe}eRhB+(OT2;P?',
    '#Wqp=%3b<?*Dzt%RxMG1xK?YpT0@0EuZIr8rA%aX+%7p7IxQ1z(AMZ-oy-Q(n;9@|N}c*ulTNXbUksP7vSMNNZX&-49*AozOSU?-',
    '5thjCY^a_)EtTzn3^m*`aWaYmDX*dXT3MPVOa0cafCe-GZ6NEk5Y1FB6e5;`yUJ|bj}MRzRjCyseQJ|LuAI6r5ayD%l|Q+owK)+9',
    'k*9Q4@tb>05@S7o6QojXHZgZgB-8EU)Mz9iO6XN*{={_<?IU<Upupvm2J(YrdghOxNxGhFUUg0`0^L|%3}@BWsd1GA;7ZLdExj%l',
    '+vs2wIG1lN{C4QHa@DI<k52Gr7Lgime${Li#6`cwW-eufqvG);a6K&#;mWa(nq6^CE)ggS1_m`mqqFol)zzkDE>J5`!BaFV<JbJT',
    'S4q{4v%bkL{E$z<BDv0-(9UwDG20qjS{HWG)II4*Mdzlr4SR+CWs<JKN{hhsqnh=%7j-gOiJykXcA_WYdIZI@sq1wi&|^7-@HkkP',
    'eVIb1XJOK2Um2{EfpKHB?<6>C*g^*bj>(V60E6=2$gSP#We_UIlYvAM$q1J~0`;elB4!8$ywqdjQAyqgPQlypTq_#Q%9>W<(cF2z',
    'oiGvQvdo3VGJ0GA?N&6JMEY1UiPaB&c?cyM39X-v&9y6jyDbK8APrN|p;B5~<z#n|S&}HYO7;(d+BwM!=q#I5d`nENt0}9PnJSW=',
    'XaUDzbk~?_oLWx>$4sQkqy{}YwM!4<TN<qRn1Ze!2|I43Cl~^wXoL1XQPn}Af$D{Mus*`VdZ9C`CoV|8hy~Dav%Vra3KU2zdiVzL',
    'a&7t`=1mbQF_kPg*bmwhsJgWp-k7p0GP@cpoOXd$?4WW-fWW)8rjR|7<GPP<i*y{drWg5TAm1y@^NUuJAT#N7hh8D^qSa{XQdZ`h',
    'QwFX>-cF-ityK{-+8#uet#{>37PfsK6{w{vwT>T64slR1QPH22a<q1pCVG3yY*w4x#T5%O0_sb-Q@6v=U^g2d=PppJ4kz<85pRQf',
    'YsMtcWIrn{5k4?tYwJb_&+JNA5mT=fEF8*~XZ&eXFcVgs)comit2~l2LM9OJEyFqgrF5<D*FD#=CsTDaU&s#@hT2t_Tk*ne1!8$S',
    'TA8+9V{-ImbY9CBVB9`+dNo0$ZzvXH5qj710@SQuz-Qf3XO*LihsAZCj46i@UJ8{ct9L2H7L96|wNA~mdkrUV8#*ivM62QyMY+T!',
    '+KP=0^@b@4DeH@`RsR|Awkr+)u+j-lWJTVYZIC+PNxsyZ@HKTxM<B4b<uc0vTHmWDc2%TvqXNA+O|E->*<SX_`zNYVyH`?CCq+!^',
    '-NslPrR$Z}H5`r4LNP3Nsz>JO<D#cq^X_DqInS6{f4ugsFsWZ`M^n*EnNGLrmDL`i*7-`Jq^m-C)#9yUp$P}9+My!*>x!H7WI8ev',
    'gmbGf(UAkG-E269x+j&337Kmw2Q-EaDurQ1Ez8c7HH^>p7q&v@%8VHCA}JXRuqJGaI1GVoIMbBPu}M+WnfIW<esQx49mbYFHzC{;',
    ')SNLBSSVk}OsjEpzYC<i%iOS%1yd;GWn0ZEq*rs}i8x4&+nlbQ!08~_v8s9~w~hyApej{w)p~7yTW`;$jg&JbO`h7(7z9CoJ+H!k',
    'HH}p`{S|_~kZ8A6BeC+lJgEIo@6)Q?R7g-NRvak^>Ne6J?^KaIU-azSKkqB4zBWQ5SL3Y3b+XQcx0Kkupsg{V8+HS%0gc%>5k5g>',
    'Uw?99Rl+>)LNT!vO$$}ubVnX6Uv1@DfpTLT7)#ixe$ev0QxKu)@=)zSjXg~GtszO7I9W*0fmMIAWs4%aCuG+0Mlcz@G*J<rK=FOD',
    '<_D?`3mT!dP&^h8VxvmhO91*rS&WH&_ArXM*K5|3X8#ya=jE(#q6R0NutS1mq*AE(Q(i%2P~QwKPpW$1a_cd}sTx`b^8SEaJ*JpM',
    'EqU{I&Csb8t#s5jp0%_7Y!=PR?O|mYxW@T%Gs-40&OL-p)`(+o%B4$Jv8#^O2`1XCi~@=g#=EVi6<jus+nAk2`Wj+@+vY}#z|f0D',
    'Viom(dz0l_N*om??Q4HS;M#dAMAKe%6W9jz%oI8Gj1jn4r7hlgqUuG0ja_hFiZ!w;j5WfERR0#u_;w4tkSL$0sm|`!SWQBG#!mNk',
    'Ib}_cVpH6oWCRGsmtGyZ%xl>ayYPach7jCwhYUa2HL{CP-yhGWCj0QLpt(hDe+!NwFtErcid|n1?)2lqMOrnoYQIyjW7G8^yxvyk',
    '8z8U1D^wy<AkmP;b=hjHZ=LRDyI^d49VNn%#DGp!Lfd{VvfOlqz8&$Jd&B3?>zU%nb>tVK6xmdXseddc0kyGC>^iajDvc^_*78%!',
    'dVAsPrPfeC(JYrkiK2yu`&^6-Yx~T&2?|A7?&s;|&Nj|F^pXRItdwaT;&qIOj6#H_Sfp}nxv{u3*fX$?=7DNn?a~4|Dj-PA%fqog',
    '-P3@gv<456AS8h^FDQ=>vAi%|8vPqEY*ToBj|V`io(OL(?Piq$qOW$x=&{bmeUUO46ffu?C^Sc|u%E61UQHCkfe=~gY87TrHfiFp',
    '3v}r{Hpy5*8)Vw>oV$)Lq6&|hw34sQIe2YKOLodiR!XSM=_-lfKs-WIm~h;L0559P3+-w?TN4wf#y0HMBeGd?(uLw!CN)l87?A<n',
    'kwIiZG!a^gEWLItT&jae!Pg(R`qRkBSamIOfG%r+QBluk_u6Kj8etlC?DzFSZqby-RsjV&ei_J<>m}J=C4(`IcVlrMAgj9Vzq5X6',
    '8Ls1vZ12)yrp4oN(U$6<DL@8a9F2Xch1Di&xmB%2i9T^w;nVxTK55wj2O0HWwD?fTmC`#i$^}p=Va>Q?OC{@Lk~&V7ZrG1eExq6A',
    'NV9q977%=1pLXqKxAjeBh8-|Ghb=W0Xql~iBbA1(>Cxug#?}HcpY{f!K`tBImeVUBlcJl;(CpAWb$h+^D3z2BZ8_NP2#a!YNg!^O',
    'r7*g+F&~rMWS~l3UTJzba!vzVnVoJra82J3N^)GNa9JOL=8KEaZZ_^ox74Dx(!{=Yp{kbL886D>W{k!98aCXZkqlKPN1@oNpFHP=',
    '-c)<zUdFRS`evmug>6GnRx6`47LRAB{KgigO#Qf)la2nCDy^BWu`QQ|xoSwhg}1#%-Ztsu2F8cO=~7lFPQ_zX3mwW^VW5tgR^(DE',
    'a>R6?o2l+dBv$SXxrlyISdl8Gd0~hZvnh+;YU6TGi5;P2en@06Y8GXJ!NU%zrnAL%sXXalP*gmmn**j!u-o!Ae4C(vRrM}vr`t3i',
    'r@Yv(-7eviBq~u@YW8;PDqa=n!x%!dW4Sc0k8%ZITda#KIm1ojp;E4^t+`IM)SG6K3(^8X;GoT^c6z*=jtYI+Tiq-QLwcK-Wc4%H',
    'B;<rtiENK}E<dgp$Mqdj@8nOpi)#bbZAIDhIzPZ9HU)_N?lL$=%_XqhNQXREDqhuCdLQ8@Ru-1|T%%kcpyN@;nCn@VjrA^!(8=Xv',
    'QVF9d1Pxcu!<yAEEE<X1ywe0P2$yM{-HO;UU#W7V&?Q@L^FCD%dgT=oYJhuC7LvnY3l4N5Ynj%2-NnS)*EZOKE@0D{8p60^jO&JP',
    '3Nk+T2l4)N5!?@=Qy~<)qKcFrHS5iJ2w2OhS^nmpb!>%OSl%_;OV$^OH9DaMIpX^Lkx#($%C*-B#cO0zUdP+jz8Xph?Q~-fUydaM',
    'E^3njrsHFAGdK)})7zO6bAkT3J8ZS=@T*}KM)kf}#CjO)9>RudkWY@bF3mLAEwKKIp*1>99xRi4i#nzPn@g%UPw51Fw$|IAc5DcI',
    '<03MfF%_85tul57BNB!WsU<wmRH8+p)Us%9wo2(fzPBv&QUyCkcCXg}YOKGO^j1zB0XeTw>UHc$-CM-B)4-Mkf)`c+E2FS1$KdsC',
    '0YN26N5dRn9g{TzfoF$R3NNb&+bJns%*bxzt+r%`=5lH?*jBulS<J@cwCdWxQbG~fU7L)~dl4uYEOz5KJMHJ|Qke-$WKZh!Ln6N8',
    '$0<$B#u<zbwWx)x5`M04O!Kk2H{K?Ievg~iFVyk24yTE*nOpV){T;fW(jdA&M=-ZYaBB*9<hDyzVrA(VY|phI!CVlO0oj$F9r%D?',
    'r(|2m)l@I$Yl$jZ-eA$waY_U-jg<o9LpXXd$2<ZhQ?bbarcU^zJHDPWmowBH@!noc;%2VDIu{q&j&EP83)P%DV*EJ>3B*&~!VRm`',
    'V{zEmCDn94blR-BNy_Moy1|mo;!G+e)|p|T#vIW@vjm{kWLZv=rKmXABM=zTcgJC|Ef&MI?zk~^EjzGC_l~(zrCdGh-o+R$nAgyp',
    'l{Q=D(B4dDmgK{j6}pYWiEWx25xH4w!;Ho`atGG(MSm(+KE_YnCaj=Jq84sig3ybny$hTZxBK{dk(ivvC)Y5=sdGR-9(GH(eNL68',
    'C3Fno;yy@U!SuPvPZzo=aLcwH+Sj_M+3uecbUI&^d19KW64nw{@YP&ImGB@kFP_hlalED_d%ug1CkRp_2S~3~o{>WW={awmMW4+>',
    'qD&z6^EvXj=loTqbc56lPW}3~Ck%h{e05&e+jI8Q`Fj24f&X#L^$R(~8g=3w?tQtx2F{w?=jS^V`{#YE9kg?jYTUac!C>b4?G6n7',
    'zXE0x+Z!NAyGM{nr(9_vPWnJ-CimV>U;|``+4+Ut6ZtFg-ccVs-r#ds`B&t<y<MJ?l`>Jq?2gz=d$nr==}w&S@W;{BR=0zYwT8{H',
    'PSs&q^1a_~8xYQvXymoA+jEAcA8qZ%sBJ%jUx&n?JgFdq!R)KO=r&@*z5i&maOdBNO~F@N8l1Nqoy9tH?)>~$6P<rCq)dE$?7`PM',
    'G9VhQ#vB<qT?mRg{}A1Fndmyds^!6;>kNjzeEGt1D-XHm3{asr-#lB+`sT5lC{r}@9YyA#zwaQ0l}FG8SvM$|;T}U-fia%F&Y#8^',
    'rY3vruD={;uYjO0F9YmO$}qH_(Y+Dl2#VdUKY{Nl(d2A?Jc-op1>8mHo99lSOWtFcpnGJ+xc9u1W@y&?!wV^rAcGQh1S8)(f^2|y',
    '2oUtmBXTn6z5@z*!X6lUo6Q{=PBlCrVW}LVX^QsEGj^uke?uR!sFbeX8(7M+>32}Ptif)ymk@!R_h%yy1iWHuKM!<TKac!*0S=C!',
    'CmQ#J?qGhsiYJ4e*I&uUyT0J#pC{#y2b%<Egl(%h)%o!p<DfrZKj1&Vt@rDS(j-o^6<8E><2mCl2yV}v{O@0T<>Bz_59r(bOy@OV',
    '-JbaUK2y<HPWv#_vr?P}r&*9aA3#5*J|O>qe!KvcC~eCbAEEvU(sTSLP*;~@&Kh1sQs*ecQT)4FeB3SP1!(SdzdU(oASddaCvu<c',
    'z|!s6cfwv~-rMboHu@(OudH@ZetXRQ?)?7Y;J(w5yYKY92YTQ+ztMevyPCYS>ABo*p7&+EZTGJv;y!|WN9zoGW5bt+E~p%1aICWy',
    'N7kIBI3vEfd-~H_?#=Gff4`BgN;^>RJ&?Uf7u&mz-Mjwcjs_>Q;CEME?wd?H8>~_Cngidc48OpGo=6@ve1GEqVUzanr0_oe``<3?',
    'A3t8V>H*Z<0z(ivl5#ntD!TBZa33tw@teoB6Yj9@5nEM0w!lB2&o=i1>m7U_S^wSo@%{MY%d7cn$Sik!+OK~yWltnuTiq&-)V{v0',
    '%lV7|d4E^ml^n+`e|x;X|F%BoTLZS_JnhhT*J3$Ka)v{WqWsEM{dkxgR}}6*9aVZWG@t3a@7o>UAI#1NDSR3Hle~WU4EeF+cQSsw',
    '6O?<E(Yx-wqk8hm`GNuY_=17Ur@Owp>UihEV>RxF9&DCT9$HkGtu3~dQKMD+Z#z8f5T1iz@Sa)&{pOISSsuaGO@rrT4?`IY?=e-6',
    'aS-e^IUhdwsNlad1aIc-cS^pdr27WG$D<GP<8F*YzOye8hi~_X++ALsc@N&c2ZP`2=ni_3tS9V`@!~^>KE$nW6Mmw?p6vj6qxAa=',
    'D5ul;aqo21$JzJquj=B8$v02%-5~$gianNX%7Q_<-^#Gz{leRQdvSG7$bWELZ=1E}o-6w9GT_IThtse}-bL=)<EtIdofYJFTe|1|',
    '5)4k#!B-Xwj-or^@h_F=A+pYPJ(SiC9^m(>tLN;(!@j?+`ctIyM6W6;_$2Z@G;{wLMK%Q4<lY*oHTT>hTj3oVUKaM<4)G|>`1)e&',
    '9QvIZwm1EV{FScncZz?wF6IM78wKZlU*r`iC)!}6o?QM8JLh=nkmu)=?B5{#ok4W0nQIhZ@ao*ZW8vHG-w}QDyg7oqTevR>a>Rg>',
    'O?yWvg9A^3`Zmb6Gat6?W#68{@Gc8)`+e8ur(`(K;g3S`m?+4uz}gQ^$o-NYxP*PX?*jBT;@SN7pXK5aQ{6|}?(aF%&Y<pwkhGPG',
    '7!437jk(*zuh2h$bNu0bdw%VQU(tSAhBM=t<~U1m9v|AfwfSNzuh(XtBPw72fr1C0T;Ji?yN7VU*}6B$d`8c28~bkgel2s~zuL~g',
    'H4(0yKljt=|1c|Z_gf!q*9VXFn}Fy84EXO4p7Hl?#ZBdS+xa~{2L$TE$;~EtN?bX*Z?|~<`@cQWU*{Cyeb`-n++Vgay|=!${BHcm',
    'vCyZ8Ue%P%J$Ad(`0A3MH2yL4RW)I6>)OYx^x0^Orky6egfDNX-YPE6pPl;t?fIO2K2nBvp>!1go+CfATlp@I4=43R=cL2-3SO~7',
    't|NFZ`QZrmoNNoAz<ta;-l4pV_&IX_C;w?ru-6g!@gMoo|8p05k9|KZ@3%qmlYsk&s`4KN)p2(B3HPz^Gv$7<!7nQD(e(c89X~tK',
    'H$L8Bf9QJQ|3BF@7m7{!8^EVk_=7!r_Z*<ZAUl#URgr`4l)TdBWLwdHpx{5xRcv}dXBOmI^e6M5&H;=#?$>%o)KB(1ANRVqA79(;',
    'd<Oa_4!O*<KIq)P*1JFG-pe+*hWHms_pW%)wZF=Yv#ghA$1*!XS#8kmeexwNcju*kXZ3SMKjFCtG5-R-?Jujy*L&}$cn)%8@Y9w%',
    'SU#G6dpkdjczRZMPre^NcI$>_GWW02IWDi-o!IW}>x=syVhGav)P{DuL&RyTc5Pl<@0#uq@^NSGX@?8kS<Y{qw$t^K*UslZO?IU3',
    'eH0}N5+#0)Dt;+rzbq|2JlW3V^oPNBMC_G^QQHDNOB<gzAolRb@CSJRNx|{ARKAE2c<1N0*V5q|xp(z-rOai$lb}P;w?D<MKjFOF',
    '%KO}%N!fjdbyuG!6`yLc&Q}ccu13O<i0#33Qv%<-=3jUHbJCiRQb0+HDLZAjPi5RUln<T$cE|9O06k{^%)d9Z-<<_G0nj@kuPm|i',
    'ga?S%*yU~LTa<DCaw4hQQ4-|{+}$5Nca3po>p#Z?5!dqE!`=@Bx>f%768>vh|Cc8PALlz-_@;Vq`u6RE4&GJo+cUI%pZ^+6I0S0S',
    ';ZES6-R$2VWa4fyoXVUt_rr;T-Qs2okD%0U`0@AWP5XU-{x225Az~$PBKt@w7)^1i60XwQzaB>7XK3yrgl#&&H)C;!WKa4EL4TRf',
    '$1OqVr-|<;6Y_J%e+K?84d3r$e|SRqPiDaVqcx7&zKYztfc$d}_S<jAn)0LCMB2*3+DWtVyNUOZ0eli`%jl0+VbvAQmi=ch^qlp6',
    '>LA()Ey)URXGm_C^B)$(pVsqP@ct00Jb7|ILj3Yr=gN+AG-1s<hT_-is6PUi-*v(t>+tXVrf4TrTp5mg4L@)=kly-3wm}cRkAmMv',
    '!5>CB#?Bc<+5PmR&P;vt&<;bLRQ^6W`s29@$A3T{`Kt56$|-p{0qC7^FBQfA)j`D_q{FtCL*su}{JYQmr|O>z{+H#y|M<Z8y+-&G',
    'wRg3(alJ3<w`D^2u;o7d$zP{-YdyI9=gO_5>^axrIcb)z*mlPGe(oJ6M`@z<_{^@sa~_?sGY(U<V}$z$Z4F9&FWbH`{?}Xk<-JPs',
    '%IP<jJs9njC!EJmxyT=<<UY-KVc6TyAKzY@?%Z=W=zRUGgwIoud-!oTooB~&eh9r?PYpr8ix`}M`y;(yKj*j)#E<hkCzJf~?xCoI',
    'Tc-MS%=cnb-WU5g+<BTId+vwS#j!ZgL&STe<^+!SXE(TZcJUEg+eF@xJ-Xo^cMU6eBEJl;-9cY|7eBtR>oNAt0KAWOzwG=7h2Ca=',
    'b4YoFG0<<|hx6~#KSqr1%-;{Ox$+Lk&e0<O(g(ZC@Z{g;zYTb7&|l7{qGk5U@ehTm=MMh3v&Q-P<v$kEUmnw~OvmPv&LwnG=R{El',
    'U)0+*bs^h8KC|_=)2g4m&l?uq6dj2?Uq4Ia+vM*q)E~b*h5q}q1UgdrE`RpZ&(h~K+OEdN;$A=beD%R0>-%HaV-K8$JN`%GGrD~d',
    'Jg5Cl?4GN9OnbMH5+%rjy#8G^?QOu_4gbFO_CHnLf5o6*YT#qhpLp~n_ALi^Wro}NF&%ig(D1L=_K9!L>F<TeyC?f+2QzdAI0u8z',
    '&!nrAW_Xm<-J8hV(RgtwHcUw{rH5<z;DH2Advi0-fcmFvR&GV+(?zFT-gWUGE<63K056vRUwX1%nfRB3q0ixj>-@hxo&Vi){dAe@',
    'Pjm^tjz?`X{fFCMe**YoKJL}xUt5z`w!aMd6JVY?Q5yR(O|)|(Tdx1Ur%^Ad*z2n{cWyb!ifdt@Z*Kv#YrOAJUM<DrWBQ^(8BRXt',
    'gsF}${e0c-wXFPD%#+IBE#%W-wDTQ*@}bQ?EB~7(|Ec2p$vXaQSN>py9@6Lt;iC-yZj<k3;FspoVQb!9+Am5`4<0&K&OTl@`}Hvt',
    'rL8%)TJd4%zqBpTx8Kcrk)(f~_w!xIpW(t!Y8*oYzRQDCx(a%Jx?~BxqWHj_=bC?x4SwPdceFR#**N#S+A(M!*#thiUdr%qw{hMJ',
    '@DCCBl!gCi;hP(gInDR|{>UF^tADfHPmB2FRm67*|Ne3Kk4Hr0@cp;_j$3~4^kePUS>1ExwjqQ+G23_l-)}tk!X}E6J&LN@RLO?x',
    'AnraS=<qyvcNMmIR_r!Ge{kayI9A~vOOu`dIftQmHm0O{D4wHO#~(SD81HuQK38|aGp43-vhfL)gY7Smr+kn195r^{1?057jlr2@',
    'aFp%Tw0nB=Uv@@CNnH4DSRBGXfl@U=(d@(_>%efqG1UE_L11mvlxQblqRj*c@*4|iCq<^@PrzK}dw4tR4nHb5@Ab8(=y7{a_8gr1',
    'H-=(Ef64tmL8COzW6BKgTu5X8`h_sK0q^&RAbxx1LXS=R@gLP*|2M(Q1K&Hkr@?%K^dfwY*M9VVxKi-z82$U-aOB6A-)5BVHIUca',
    'C!fOiC$7)kAHsoOW%3_`{NFjAzyFilQvXpX`~OE?`tMWEe>~6l=X~@(J+XL&9{JGwRtoqjvHiC`^QW@^8_54z!s<@{KT8+hN+AD>',
    '4ESBUetiLz(<JAAko3P6d`H6njm*E<&iw!I_O-K7_klk?z`IA%PVn~TqCY@<L;J7Q;+d!`2mM_^Z7;&y?-1Ner7!i;Hx+%mX7RZ4',
    '!Q4+gKHm6v2~ynf@;yd*d&lEN7hWa(U3MJy{z|I9{7Rq;p2*`Y)Is<>V*kLo&&O^D-4(KDjQ3c~3qtsD0m4ol!Y`|NFVVS~tpm!b',
    '{oBI6w>>_WcV5%^t<b*hQ^@oElfQETKQD2AbN>6eD(K+*@jK|BoBpgE)S8oxm!pUe=I>G6et93|lcRI`es{a~!;Sh6<sRp(;XN7r',
    '2<^|M=3h+sV<z=+=s(pN{wL61jsSkT!Ts~~#s|<pnWN9?<Dc!()6pRJf9$SzjDNhl^~<|vAKzhdFCKk5J$-vq<>z+|{^`EcCrIzF',
    'r@ZvM-A&t4>$PYHM<y)^x^AzGw53$DR7Ln8tgb-6$?%u|2Xq&oJO'
]
agent_bytes = zlib.decompress(base64.b85decode("".join(_AGENT_B85_PARTS).encode("ascii")))

assert len(agent_bytes) == 28715
assert hashlib.sha256(agent_bytes).hexdigest() == AGENT_SHA256
compile(agent_bytes, "main.py", "exec")

if Path("/kaggle/working").exists():
    work = Path("/kaggle/working")
else:
    work = Path.cwd() / "v13r3_notebook_output"
work.mkdir(parents=True, exist_ok=True)

main_path = work / "main.py"
archive_path = work / "submission.tar.gz"
main_path.write_bytes(agent_bytes)

# Create a deterministic single-file archive with main.py at its root.
with archive_path.open("wb") as raw_handle:
    with gzip.GzipFile(fileobj=raw_handle, mode="wb", mtime=0) as gzip_handle:
        with tarfile.open(fileobj=gzip_handle, mode="w") as archive:
            info = tarfile.TarInfo("main.py")
            info.size = len(agent_bytes)
            info.mtime = 0
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(agent_bytes))

with tarfile.open(archive_path, "r:gz") as archive:
    assert archive.getnames() == ["main.py"]
    assert hashlib.sha256(archive.extractfile("main.py").read()).hexdigest() == AGENT_SHA256

# This self-play checks the runtime contract only; it is not win-rate evidence.
captured = io.StringIO()
with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
    from kaggle_environments import make

    def load_exact_agent(tag):
        spec = importlib.util.spec_from_file_location(f"v13r3_exact_artifact_{tag}", main_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.agent

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 93001}, debug=True)
    env.run([load_exact_agent("seat0"), load_exact_agent("seat1")])

final = env.steps[-1]
statuses = [str(player.status) for player in final]
rewards = [float(player.reward) for player in final]
assert len(env.steps) == 720
assert statuses == ["DONE", "DONE"]
assert all(reward > 0 for reward in rewards)

artifact_check = pd.DataFrame([{
    "main.py bytes": len(agent_bytes),
    "main.py SHA-256": hashlib.sha256(agent_bytes).hexdigest(),
    "archive members": "main.py",
    "self-play frames": len(env.steps),
    "self-play status": "/".join(statuses),
    "self-play rewards": f"{rewards[0]:,.0f} / {rewards[1]:,.0f}",
}])
display(artifact_check)
print(f"Generated: {main_path}")
print(f"Generated: {archive_path}")