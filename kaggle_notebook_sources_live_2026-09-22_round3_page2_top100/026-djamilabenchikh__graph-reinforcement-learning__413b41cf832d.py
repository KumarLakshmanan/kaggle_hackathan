

import base64
import copy
import glob
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tarfile
import textwrap
import traceback
import zlib

# ------------------------- configuration -------------------------
WORK = Path('/kaggle/working') if Path('/kaggle/working').exists() else Path.cwd()
BASE_PATH = WORK / 'v16_rc5_base.py'
CANDIDATE_PATH = WORK / 'candidate_main.py'
MAIN_PATH = WORK / 'main.py'
ARCHIVE_PATH = WORK / 'submission.tar.gz'
COMPETITION = 'kaggriculture'
SUBMISSION_MESSAGE = 'V16-RC5 + GNN + Double-DQN residual RL'

# This is the wheel path you supplied. If it is absent, the script also
# searches /kaggle/input recursively and finally tries an installed PyG.
PYG_WHEEL_HINT = '/kaggle/input/competition-2/PYT-20250912T012549Z-1-001/PYT/torch_geometric-2.6.1-py3-none-any.whl'

# True = after all validation gates pass, try to submit automatically.
# If Kaggle CLI authentication is not available, the archive is still built.
AUTO_SUBMIT = True

SEED = 20260825
EPOCHS = 20
BATCH_SIZE = 32
HIDDEN = 24
LEARNING_RATE = 2e-3
WEIGHT_DECAY = 1e-4
MAX_LEAD_FRACTION = 0.25
MIN_VALID_PRECISION = 0.60
MIN_VALID_PREDICTIONS = 2
MAX_CF_PER_SEAT = 10
MIN_CANCEL_GAIN = 0.0

# ------------------- Graph Double-DQN configuration -------------------
# Residual action space:
#   0 KEEP_V16
#   1 DELAY_MELON_25
#   2 DELAY_MILK_25
#   3 DELAY_STRAWBERRY_25
#   4 DELAY_WOOL_25
RL_ACTIONS = ('KEEP_V16', 'DELAY_MELON', 'DELAY_MILK', 'DELAY_STRAWBERRY', 'DELAY_WOOL')
RL_NUM_ACTIONS = len(RL_ACTIONS)
RL_HIDDEN = 32
RL_HEAD = 64
RL_GAMMA = 0.98
RL_LEARNING_RATE = 8e-4
RL_WEIGHT_DECAY = 1e-5
RL_BATCH_SIZE = 32
RL_REPLAY_CAPACITY = 6000
RL_UPDATES_PER_GAME = 35
RL_EPS_START = 0.35
RL_EPS_END = 0.05
RL_REWARD_SCALE = 500.0
RL_WIN_BONUS = 1.5
RL_TAU = 0.03
RL_MAX_DELAY_FRACTION = 0.25
RL_DEPLOY_ADVANTAGE = 0.02

# 18 real games, mixed opponents, alternating seats.
RL_TRAIN_GAMES = 18
RL_TRAIN_SEED0 = 3101

# Never replace the RL candidate with plain V16.
# If benchmark fails, package the RL agent but do not auto-upload unless forced.
FORCE_RL_SUBMIT = False

# Real-simulation data. These are deliberately disjoint from final evaluation.
TRAIN_SELFPLAY_SEEDS = [101, 211]
TRAIN_STARTER_SEEDS = [523]
TRAIN_RANDOM_SEEDS = [743]
VALID_SELFPLAY_SEEDS = [857]
VALID_STARTER_SEEDS = [1069]
EVAL_SEEDS = [2003, 2011, 2027, 2053]

ITEMS = ('MELON', 'MILK', 'STRAWBERRY', 'WOOL')
BASE_PRICE = {'MELON': 250.0, 'MILK': 160.0, 'STRAWBERRY': 120.0, 'WOOL': 200.0}
SHOP_PRODUCTS = {
    'BAKERY': ('EGG', 'WHEAT'),
    'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),
    'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'),
    'YARN_STORE': ('WOOL',),
    'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'),
    'PET_CAFE': ('CARROT',),
    'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'),
    'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'),
}
FEATURE_DIM = 24
NODE_COUNT = 204
PRODUCT_START = 200

BASE_SOURCE_B85 = 'c-pmlXP2T{7U=i>6=fL)w7pBrj-r4dCV~hUdbNlO3JORv>u-N(<?g<B=Dk_3K2*Uu`|KQ#*7NhT2<4MpJ(px1#n60%lAX2UbrpH>q*~5XM_w)+ZSHS8-%<X0et!O@8C%Qoo@TPE<g;&Yb8CBid)8gce0x4^wAr_B-z2oow-~zr1V48F+F0_!1@4=FEtI)sY#qgQfftm2&5F7E;z9xbHBZ_Hlc|nVg<P!9j$+Z{23_f+>5b7Bw=_w*qmHOS^UV5^O0P?~DBqlNw-Z%a6dQRVwPUxy?20->Y7BVO_~tt3qoZs!JcBTJnv0^RX>ZL7L}gGHr%U2`Y!qP==@=tF3UlLvf9^Qe^+NX@U5O7FtPGcQ;LH-qdgzt~mR6FF+BG$W7U4~;5jze}=Z&Om`?z-QEzyo@5{%^RMwbakWvLOeXx7ftTgHnupnS=9%c-0rwTHP0yV9eHm_(in(d|M{jw5nJs@dtpN~xv7Nx!z3Md}@lYEKxZm~2Egvjo$)hL3}61dHG*a)3ou#js6!Q&z4;cFSwl(jWW1nN+=a@+Q_)h|CmfuURlIriPA`E+j`;QXNgp)QOyOHJCg*%7M60QD7yCUQUmm>~a&{z|CgmCi7|)!kntQmng#7SFNyK04zSHjTORd6}I3MJm-AJ8Ke>WAfK?qIcp3qsX-{zHI80u4mbQ*8ZaW!TF*Hd;&hv;C;fT><$)G=BK35)(LuAU)M-fmY>P?FC{-SV-6+@ACW{pj?@ZBSKL*&)39x)AJnid!jkS=TA@bOKCKBwtv`8=KzR{SLI?er!jXP~9qG7B(&1YLH&r*{$+*o3((;`z!$Chc&Cv8za?sk$lIjvYJ9nbHI>ez@z7p3tL-jvOA57@UC$xSZJBa=okuv+E<kHcKZm~RBGIUV2Dvs}B}Cd;#0giNDiG9|aic_OO{88UP}4``*6G!JaQk-}ZIm;;<~ucg*zl5ZyAN_i%oia0E(4GTQl7fq0_0(^?B!}?}G$8(G0I59FLK5zGBsm#_Z+Ob%hT<mozV}N380xy&8BNcB>Tj@Dw*=;=9YsmRMk<HFfJ)G~s78C2v1AaPmoT-xAeNOJCtlc%Y_UIN(P-UVpq=);{g}|rmz-xt;{2DCA)}8ngw77ydT$T!UGmV69?N!%KA(2j$E~_%GO=MfS7&9~3xFvms&>=5=)K(=nGKqw?>+KvLmNA+dtD}@!mDEmIF7xAZ8sOYn6Uka=TBFNheY?pu!n#V&vyHmaK5h$%L&ZGTB1)H<)N{=Wze<r6C6Q^ymU+H6NrJtMsTmegj$-rLB3Eb0g49Umdrl5_9HX@sanorxW+L33L7U|qz|>h9o1P+4bunPMir>K^BTO$<%T=syZ08}7K1Y%x6#;2v(MR*E*wrfxlfZ0*T5%SbH)CiV3G@8{oSc+w5fL`o_^7Z*NCt{j_X)SSfe__#<r3>-F520PE|nuIuv{AMz$`Yps?plcIO>PiINfLz8Na)!>^jbVGnqIMd;yNZ3b?i>=S6-Y-|Pd99PpiJI)0whn899@&CJ$X?LsUU_Qd6_No^X%ILlmhxqE3#Tg3E~S$k$^2i>HG{k~@uOV(&w?<OF+vMb)~S)<rZ#yZ1|at;H;YSiRbe6&@iDgr3fJTFm5jF3SoDKwT&YMk)wZTB?UrTs-^->S(mV-yh&69#Ott+aHM(gPi0M-Zm(TJ|YMT?;00km7V;0+P|E`P5<6Dt5>az-o%Xm3s-LAB)!5Q|Y2kqeL4};o9k1VZhC#$v9cB-gk;f)t4`zwi2myI+ucFRdx!ef#P!6wQw9tyfMxoZk=UZJnmo4<Sd@>G9)Uqkgz7=x|zWW%J7!5=t+$-8W|KR_S0mR4sS!VrHA6~F}jZ&xqMr2<Tx;CXG`r`&MyjEbC=$w^SxQ8D%rIv0C>*+j5~?r6*~*ZYb!LVV9l<>_(G8v6Sq?GIG{?TyLNZcvtap1{5ZH37IAq`EH`eW9MN^?cq*M@<2?=FJ0L_%4T=)5v^bFzrv$-kZ5)n_5}u@_y+SvXi7rOjiqYngMRX89FEu(!@||-3Iu#?MIGbWO$4>qfxfVe<HmJ2XTTW==9ER0$7%prE{oFi1yO4q|AVp%6JJz$igQxjCBrN+h<yT82dCZpOOe%g67pWVi<c9h1jY`yr)2eHnMRG=%cEQO&L*Hk!MF=lBygf|SF8xIz;qLS(1&=2^5P+(1H!)4+ZFhyW!{t?{5uJE#%kK;``AmIf(J+>sl@mR6T&Ao6uXYyfYMABg<$JLbRH`p8ad$pFHjIVWfWorvn+1wbuN-<`qvgxSjH8`>mozK!x`V2K-5Z8aH#NFGH;}z(-deMDKMX9l;%*dosy7ly=JZ4y!4xpA?gZd=t<Z-URvMM#eQLitU1$#zikmjOOWBb$G3;{*c9<z-v@96s(Umg;Qrd<9C+xCQT|`(q#jVOy!yJJKZ}by(QXX2#Gf=C?vItal@?Nv6#G01N?6zg>)?JN3y4^lk^#ijzCHaaxKFX8*;5eQv?2Kg8RBdkKoB<vzMv4|#k2|GKH7c~KV;WZF#>;WLT-pt8y)<rZiur39YE*{GayzmXqq!InGD^A7$i_}a#~c*0<12;xsE;F!0#XcuwbAujgJ{TQdmc$%2&hDP3%)sCIJFt#TTL=1jX0VmxEQwvs%dr<xr~b^s<1qceW#c5Q{`HXk7nr{HaVpf>lz;pihcby$&li)$LQm|JkO21ZH7Ld1@T7dv@aEUrqD|#sV$8+*wfXjGy5o_jl%A}ds;T_RC0^0o7&X5`t%A&?YoIV3QW{7Hr0qtPg*3t3oD^P95N1sgR(+-x0lP2d3tkf<#GdPV&RnEPRHYuoP(b>o#mEqPmy!(cpR@3q$%z@vD|#IbaCWn!+Uxe8AK;?ro3aTp((5kNN5*UD<Mxop+3E<a0jZEI-0XfiydU+%j$Y-o1<+lXaF$4+PAy3Y@-)xTu(SfJGt|xrYWpXI$xL`;(oua??May)bE(BZ90i-<2^-L5zo$GLMu<o)N;_Bj(3-sd@e!TeLTrT$W{wKR4a2}p&0|+)PhzucWI#1vLTfE&=Tb3MeG=^_LkuWaK*)9d#q*j$#paD9GXA~8KlN#W>Zm)c~fnMg$mBINJLI2t24UTKP+=gf2C7vdO*oXC+h>4)|{Q<<x*Ln_Cu9c;-FQMHF+3PZ>E_8NMPVc1s#nX_Ec6zC}v7k56wt2HRz3mHqqUV%FLdeyF^62dbd(uSins_Ol60dyE8&Qc5E@zh@I_lW06|zvMaTnWr`sxqnL*pSuD5K1)3F*WhcJNmJ{i<!?zkBav2~<Jj@fl!W>yavS;zdbvw~=2xHIX5KXUKinVcaRySa?N{ratK9+Lu-Y(XuWdbV06;p8FVJp^d6bA*v&1Q(@uAHFrvq-^V(9Hq7LA!EymIUjgKG=%039J)7gVCOh^=j8+9nUi5>ol)1h!S3|t4=*y9<M4%5+O2`EP7o+*<0Uib_sT}CW_su&T{jbnV;SA!=U?`kX-l*Y&vmHKQx7YZ<5ZSQBur~_OOi;t$y(9j5V8h829{)p5T)1B{T*!uW}^9P1>x_QEjR!*GrcgQi<cVd&mkT14owYSs0&(cDDoVQiY(+!eeE(EBF#LUtR$749Qo6p<-Kcj1oE2>W4C-MVkXzax+ZkAhb{_wXU@-5(;m0jL{Og&@w)g?HMJFb9*gF0B43YOW=CZEELBijnm^$tBi&Qt*qiP20s|ZT9;hSFQnrGZv^U>$sj!|z-}^J>V@LS0Z}hw96{O}JHKl<CpKJ5bPRJi*^;h=n3fH)OR2C+oo+2SN@JNRwp#+aHP~L7q1q}-o4tf6OJP9HFfI&?>``Z)KOHtnGH1cH*w#2n$M&e2A{&^!-NJ`SZ?V&9aCR^v;bmFWLr!6t9-M*1rhfsuNoZlgTF0#np_Kz?`xPvNWzu3DxZoOob*ddGy=)(^z4&5FVGyk|=VR;0B*S}?Y#t*=02Op&RLN3SbsD8z(7h?K&c$wZ22ih~!c?mmVYgyUWts~dO6|gSVsTk9;z|ul5|`LDe6VO|xn;K!*)Z@Rf8lvDw^HY*+Xx}&K66oQb$c2LnaXfjX%30pWIgXgw*ooNtn&^2V%CeP@z6z?Lc}k^8V@a@J$UwVSf$8b^wY{tu81R@tZ*4yOzTu818=~>Dw#|zTVAY5L^Jg;pD&wxj;9J_b9+7<wdnd_)vUE+PNPG=1YzoQHgk5oS_qn|1yqu68qH^r`UW@5vUE7ZMW{M3Z4-$)_$*hul;k-`pmC8~rQ%#>6p;%J4pXrB*o2{85FW8?rC*10h4xjCC%H|kSMt}h#Mq|}w?pRESORn`fkdLcwanqw96YaW8b*1DZs)Us$MT~DLb;csm;n|!a%^*Z{<h3iv1+j+p0bLYw_}acg;<Lyu#4~m#v5yB2}*7J<kHz!fFnhD<`tY(IlmZ<s<G5yk3`DzN^eezLQTr5vF@2hBFk8_(+Igvt;Y;4C^JdNHe!B=dP};14=cM=lwX0Ujz`dBq%pxky{(ruX~B%0pbt!RDz`c37I{4591F;_v*$xy2Bk+m9mnK}u4w5|giKrn!e}GXzFC{u8Cb6i7KintV6I6uR2!zw)NqEhL=riyZf$t)Iqc||80MriRb20E(T3972sW<u<E;}N!eUE;2#pGJucUE_T+8RnYIQd2T5Ui=3JtHot$SG7W6=GuDuanw6#?qaUc=Psq6C$c?s!zGog%r(Qk@_4bvK%wqgS!rJV|+dI5Or5IERL|QKmG^+*m@-?9S5KlddU3+og%-vfiKRTWe&i$5y?NUS>B@SE!bTrG^5d**+W04qPTw5rnAT&WGb<$B&zUNaixV)Y-u^yL?1%CW(xbiWfqll$cjMF76!LW!O&v!!qu)s>}fwEFvd+kbc|+Q63A`BN>KtwbLc<-P*vy)jL_P&0lu&!VH|oA-a?FQpA+1RCtrvb}@4agm%cev>0b9nO68P#j|<DGUOnr!}`bxjm_TqFgi`WOUu3RJv=HFwQx)6F4#juHpyKmohn3<^@ul>mzQ)ioDljczhXm}XD#yS&BVrvM~|eAluvt;?q=+?O5Lnm=~OzJTN{Q#tkq*@RxRO_Rz4?HCdgJST$Alv*O_KlW?_-fHZR-eVMk?mmC;0W7>4Z$G@oUuvVHaAQl8J>rm5<-PZU*ft>+;h8kG;{DzYI^6r+!svr<cD$wq09M+_re%g3y?9b(o4(_4lXTj8h(2ZlBx$s$wFyV=XhPKt(_-t~)g<C?`<leuEs?Ru<e8uPQessnJi5#pEa>EPgc<fuyc0kc|#PkIPO>N+~!o}tqA#77d%_{Q9=_$3U7oovanTZ15((X}u<P;&lAlyQiYgJ`-W7aSMAwfk|VJTQ}rTxi+yA>KE+Xh~l{wJaBJ)Jz&s;1VQfifpulxj_LnsFc(N54-c&O^SRoJgZ+2dlhEqZ8LwRLy0;QRRuKHghruFi-4*}&R^#m)$(j7=+}Xh<D@Prz(Fc@p-p3~H8qH5^MVu}UZie5K|#X&TtBW;0v@RyNg#v`03>le2pO)l*oZ2N&-3yv#nlpx9O)mDr-^|$scd(BAQ(E^+C-BjzM8KS$5x;1l+U|ESC|MElkvB^PQ@NIYhy8FOU<};9qQ7)IOB@etzhO-)9j&t8RY7@O^L<XwQ66Zeh7ru@S08ymSN)n>Pov+yxK4UB|DQ|cDftQhV(2`k71XzEjkUfRF<p>gMwgaG@EZWbo?61_T)~s4HWPYr7C%G!PluOddawSZY7bU%6ig?!Bt(<(K&l4@O$i*2NGhM*Fv4^F*iHjtW!FCaib?REmT^4<zj}=e!o%aVUQ6U?1WPSJr_4%&})dH;k;ql+q8Y%9N`O;!RemKa*HjRR;KoNKvqt<ffj^)0w^}J=xG{KIhX6?L$%C!vBGO`Lx|MIMrFllRJe1%Gwnom9X~B8!;f_AoZbYg%-Dys{;27RrD2_57Y93LwpqVKA0$QU`KXbi_X$P2W=VHp3Cdt_*mTL+)Uf+BoXm}LMFdB8i!|?9sr7o!!tK0K6?W@pmB|)`u|nwEq&81>qFFG6j7?IFbI_$;U7$Ic-`7u!Y>Wrhgl!LMZZ=GgdjU>$wQm<D#6IR3yk7Ok0tzIt5PjYjh=OIThC6~d#h62OL$>9{0!0!hS_Vg~m>5yTW3r#E(vXB>nX8D(45OY{t6!|oD_{}0%|tAVh@z2?G()SNCAIZPIT20MhwiCZohOt*Pwgg%vwb>kq_J>Ak1)|~BYVn;t2C)F+4+r!;)hTji)(A2ruNeTs-T6r+8LI7qft-y+@jtj1x!uZ-SR1ftI-gWQ#-dxJj72TtQ|^*n>x}|JZ{>L5A#UwvYYH7ZaN?jp&=+77Q?}LK1!(Pxq;!;E;c-zd#4GfBoddjkQ;URj<w7!R9b6CCCQ%_a(m#$88{3W!t_M#i--B1xlr?4YPj2-$sT>qZC74A3hq_CtcQ6VY#~5py-E|O+~&r}T96&_&PgqXFNbz-N)A<m8fp5TX>(C~Q*0K}tRIUI<J#HX+}h!G2cERt<hf0m=@XY~)L6|;B*zzZM?h@zz;NZ*Sdckv9lN9iE88D2<aTv+Qq-u^3)<`=KB0?^A?5Cy4aC>#<O#fP7t;(%9aHLPJ5CVfVSA~xT26K|NJcSf=h1c%Nf<?L7mp#CMF|Zu;JhN7JUpHrs>|vmEhakAX@TgeZK$TN^QBnDo*s!tJO&#rK=Z*74V9qE<ZQ2*`J&2*p;#kJ(Rj1U$645icSJsBpGddd%zL&AQ&LJlofnz46K9SkdKpfL$K@@zEp%#(pE%thlS5+tV<?J@3e}ijMZ{g`APpL^gLkNiDWKFYt%Sj$G;ZV^UR~xHEVV6Qr$It<iIXyF6f2iz2dnap#Hn8y#%f#GjDyh?*K6f0bC#`%J2X+OyH-!#RZG27vzN_`l!cg>Md{kAb2#+X{gg6i;!bh<N)=pIrP^v(Iho)AnYE_%LB?6jhx#l?wL$G5{7Xe#p2yaa=izS0g-5w*a(>)4y|qzLmQf{dZVH10K1sn-%naiKzCN<31nqTmHs%<;m(35dMLT5~yp8wPwSoj7%gjU_0>@TKKF5^K+%&TpRPA=?-moIm`TYo-R!VwE9BQ>w6*eIQ22-I@T%c!*D4o}u&0R4sT-ILloTT~EmPdy2ZM3zyQKDL)$=jeWY!IeniOOc-Ocw>&Zi*DG;AfG`r!hEERIFryaVxEy5MErz-Odn=gtAOTrw}ymbB-&^xl1?c^fi`3_06z0G7GIey?`3(07V+s2-=>)-j1xUQkRjE8z_*YHU-bP95=U!kJ0J^?cubZ%mX-j^~G^76O9saRvRq!ZTHfY&g!(gVcIIKlC*G6!^Ut^T~ppXm8u`oAzI$_x7$rSezGb)G^Ks4b10#yt2J@#N@0po-TEy*%g^LoD;3k1-Qu*|aFj6CUN-e*kG>uHP>{XKjb5bHT7b;xWOUi6HWAy3<DNVbh`YJ*;dG0iSeGBn+BvMwOlvgV=v@lTiX0WuEUD><^SMJdH)sTJhln{X#)Pvn^mW5i0A4yD!jpM+Hqdh?;Q%%`4#I^xDR|v8G@r9lu94ZqXFF?d7kG|rUQ<|2$;OaDCD+;VIF?v86iiG>wOFp3h8Q0>kQ=h$o>8!9c6!re9nG|Xlp!7tt<bHEU)ncVn_gwEpO~eABwAP>a@Gxn85K|Dz-5Uk4`bU{HEuG^dev-^;kwEtJBOo$!A&Ke3>P8-6FY3fi(oponHjn)B_q|YV72Qw=HI&TzAnJP!HrM4s7X|s(~NRq#)V`!m!~C_4Z3JB)x-zl=6dV4LI_mo4*gYlv1Q9h-T_9*iIYRh!aA;}H<40hx}WXTo!oCPnVYyjC8q4YA!E5A+Sbe?aouapzCc-wTuSVU*GwtxFPNim8?kIZZl#e+2Ih$}o0a>Ep-dJT0}Wq~-7s5?h37Z@*qoQA6%li(PQqC12eo;4T|XOg)xsmao3hwzQYB*wYIhRK^qSr3;Lt9x?ghO_gxSt^A-`Jk@<o$bbj~OqLnG~sOiowq(npS3#~0Jd;}Yu(+uM4zQSc8my@k`Ab9@VC66y%dJL~YgBk2u03(xIkakkCTL@UiH7+>+cex$bF6O=UC%*&Pj7Cp!<ZM(=U;p%aGfzcVB-$Ge`E+!_I{*XS+4(ka&$@``f!KI;|X|MWnhd*XI5k{UwGPBVZ^}8YBc%c!iojyn7Xv|3!sPZ_)MIze%G#(#GPSjRoe0wM|=oZ0%!%~k)dNZ8t7acj}W^QV+WwrClq_QYtc~c(Lq1nJdvzc*X1I0Hm&d)ph>UN|n*(E*ITl$nOZEMG~$K(+zdg*8I=+aft5yD2pv-AyUhUgUtVl7NPlhTRqZ^`Af32R<vTsgGM8LW@?;w1_lhANgVq=zjy-%!tSP@IWW$kkS97W7Nw6}g}$OV6F;-TrXcoL96BfvEP<Zk?xYaW<3LlTnKfTahl|MaW852DfmdfW@5%b?E^lGDR2ha6>H5%R!~sn@GK&LbnbRRP0e~M0jk)mf_fJ7(p;e!{lD0)m`m@uyD!Mgnc#CY2KVz{<0TTq+@Ru@OrKexwHq?+8$<G3p;3ONR!4!c%Pe?=73o5u9e8N0<{u#H#43iVzu6m)tNydl23#Q>ue!@x_s&l`s>MbP~7KI(awsW8=KB5yxv&=yl3sgqHC3sw_UEeaQRSZ9ufDtJyI^Y$^j?Urnt-(m^IoIN_1iBlC131@LMu6LZ?KvW9rvpEnUaOIfBfVVQ(p2jF@vMlDo!$OHTZ2RWnl6^lDM_*WpTIapc<(sR19=*i=kl%Br446=SBT1%AqP)n<R*T;t7xI$noY%&d0?$2AnVb}YO<*PTedYqOcyzy~>eaEyXzPQo*zF$-?}QjA#k!1hr{$d{EqSdlKe^Wc3_=udJ>r_JWm3RhT6ci?Qt4}{fBwScA&?I&0rkHJ0jV%!qloY9#%4So$e#nDi(><pB+1!G(pK<F8Rb1DN^%noX-Sztp*y~dORD_y`b=Bv(jaK+sitZkF=WO8M$uUVmJ(zyjfp|`TKKU3_U3?U&M%uKKg%*G;4Z#XSZq-sQh(&c_=k#7ghm7U)&xY$k*0khomdvrWyf&4Xt`{fqTN3T#4%2Bj2yG1B#ie?E7G%WA7He;9SqB}p_(g(U&^I*C?cROP-7&OJ=dY|9<-4nN%GTNalnIPWQi^3{-uJ)5&9wIhOsL9+4gH<?NsSxgxrS~+I7uXmi3-Fj(Yn_FYsGjy)BfHs1b~@VkFEj=quo(1#vCA6GE!JQhO4TRDO!BNIhGLu9+gO9$YqQfJYsPu2D3D`K43E`Hm&=(DR+{CgCQA%=o5pD|Yf(LDaw3MY3-20kq%=H04a4iWZSBwt(o`W;Wr_7|ew^0(*`{{6UF4vE={w#nMRtY8aisLP0Xu`vtI{08@ZKPw)iaw@l|*mdc_cDTNgKj+(uYGH%C%)F*_$Rr6TC9^mQaW=b!J^_J#APZgx9YNZdzBv;sCbt+g_Nz*<?p*#;|In@9Ep<3_fT0L*UB?iBhc0zTeB`SR^k;yD75T%BtYCMQxZJ<&eTw-UJ<EzfVMru&`WW_zd1b#cJY&x?qR8?er>~fn9vq-?j64EFl)EYWTdUC1)$_$nT)uiHlP4;d<wj(VDzPrEa~W#$$Dto|RR|=+3}?DDDlj{W&A=qPc2acWMb=XOw=eJ{tFP>`Kh_nU>@%J5Xk|OE&kVyf+bwWqA~j0;y`DaFd1J+#t;LtiR=&{N=3IN$XfrYiG|U)G1z0@<V_H-E30@^k8(1k+Rf}s5hoA&U%w!!dr+7j~zpeu>}>qo;>hFi-zX`^&;7!Wt1SJQO2?J)9RHH9gSY5<{eEFE-5W$#32JgJDn8Ju*4m4lsIPENgR<I;Z&=;T!pJGrIC{I_6e;5bZUl7=w#^H(kWrt@is=%j}4MoyOpXZ5N(O76Fk$W@L-^2;e`aQg(Wa(%sG!+Z`tV8PYKn1Ke;K2$E@6`k+DJ-$TIbrCc5sh7VWiJVA#SbLJ|r@>aY@rQsY7)Dk{!KPBO=c!;m_jo7l0Ri0B(Xeg@^*T#tkVr#HH2ZQ|+*`}|?I-tHQga6BKbZ;-}ypO#AHVm3D&(OkhCE!Mi+M(l`cg&9C{hom`?OT=zfuXN(xfNU}8VyGDHl3h5J=(ZqewV3T1l^{Or^TU{Lk8f8ZyCx6e{c3?O2em2S-%?XAjOQ~3!)$_dhL4-0l^qV9w(hvEnaN~dI`)`iQdD57tl^?UXv$7F87^MuHvOG^i?G%KgU5uA(@=qqrfX3)WXAVp(<5?@xTTevP2Bi{7DA;+U8dNhluDn^Z9GiCsni-H!rIW^cU!>>Ge|{S^G4(Vc%qv}V(Zx{+rHWyQZ%6Yus(*}YtbVV<+SB0C-j)ytXsS)Ejsmvjx{b=tWI1;$68VbLjjgjX4f{_VWY9pz%x9V*Jl-HfXB0#c&+nk5V(TjQAgr435;rAz^X~}(?Tz7j&XIC9VX<P(zy-i<*sM)@v*X|BJHzX74txT+tm%iIWOlp3LEqD>BRTby^craavdaQ<6``ngNdS1jk(pT)ZBx|HQc79P?VsiEpNqQ*UNy~j|$eB9OdopY?`#9el>I&t8Tj-1L(x)VAlY<J54%C)Gvltcx~giwp)ct;7Xo|w7av!m2@h7%mh)gWf8e)uU781lKs|XKXOu4?V`_5YYnMMhg2q(Q^y>QX-PgMXal4Up~yTV`VncJ%$ZROYPDP4jcx4=z63>ki*&Vt#+Z^F@@7eB&V+y{fUFcgo#8q@U}O#<X{nGlG8RTFzRDixXf<SHQ|Vc%e(toZa56eHdh*eaMd4*t$4`QT_%zvf6ChmQ8evtgR4P=^f85lrk<MP=LeuD$YDX$^JMpo~WYS~|s}HQgB|<)8*(R~h9^$<z8k4;h$<6CyTV(muo))&fA%SV~Eo88j<k+h&^sX`mZcWx9gelsS@Ct2edmx{?F?O7}<mUV|bIH$`{%9Jn!p(4{m&Le7aZNYX7y^Z+o=%gSW+5ym!&FsXW_PXCB}!RyAw|xr@%o%Zt6RP@mNLRg8g)|0lwE_zeYC^NKzWbh%}r+`g&jM0f*^A>myOX8w8wPsbX#b8VO<@Uq`CxWORh2|ASYpQu~SXm=HN)AK{QX$YFtnZ3jn}SC5E{~-`YcFalh(!SCx?vogevCcZiO(^G@Qa7C^b-xxj`)G~JU#Dg!MsM9PATT0AueaD83<7YP3K`sK!F-&2#tXAt}*H8`oo6V(0dk-)zwqRY_#`u_AUs@3h>|Mqzf9bg2<jqYy)hUxz6<xHPPc_KJ-{`M67r2hSMe%{EgC%K-oeg5}T68ir1yzrG@--E~V_4@sB2>QQ0bp0j`2m=40eJ6YU{y=nn+vEtgi;e;qg1yUB{3i9A3@fo56HKFg|DEM$4DAryD8LOo6D0W@kQy`zlz#?axO-+><1zX;{D8S@<PO9$6v{KdgJYaP*PBwGW%%E51`i*ad_OWmIXYmJ;fTkHyLO+yziqbagjDAUl=@)d6N&)g8$-WvP4H43ZM<NtqZ}8o^NzDmF$~{q5&wwt4Y+}F6v6c+3gtS)i%jprydnOqj;{h<zkU0*P}HX&EqK6A-uTM*r?qnY{uC_A{wC-fEmHyi{UD{OPnxTlt|yyw<qdeD&Ar$C`;Vh|zGFT;HvhWg{EQ5IfCa0b;sgc`9%RpR-Y`7}?*W4kf^YQZ@@6B?HVW`^=yyUd>wlo~vHzLISGZTv?_W%o<hiF=Ch+p-mCnmc!08<#h)HF8e|Uv?vYf!3zYsgWbN8&uj-fb#H8z^-y`FgJ<824Lpa1d9qW%8!&sSSMPOfBg;RXkPJWg89BGA=m(8pJ<UzRoV=?m(Yqc50$f<HeYH6GvC{)+XVFulV6g6iE_TtyC$%-mN!y^0S#JjC>XhcgA+flap?`4~w1{VDap75s+b08rVu%2VnM-CZRw@OQ+oNbieop!)~IpD;ew1B3xvuiSm+;j#PUj^^i`oBP94<!Pgsz+(q|p?rRqMBZpiQ+g=wRRQ0hJ_LJrfIs=j1421$mAR)Z?u-UR9(;b1=R;HA_czo2#`<IVP13)&=UYtN={$D8K(aUbAA#}M`b#-@in#!Oyt&Q8*3#Y1j%+R!;GOT}Cw$;5kry6*ywd*}u=d|M;{*Q3zu$2G{Q223FG%0??r9rE3RH7f)%T~Z<!Ybe&U20*@*KWD9Rm*Te)R_SBNar<*A?iM^-ly}jPXL?`A+Yv>VF)6{y6-6HR4>^dQU*hTqp;^aV+Qi6Mx()uaDwAcRZed&p*#yrrsg&=Xbdrd9K_Y#d6-<<z6MfKRuS-<qLrBUiJDf4?hge1Pu8A+(o*BgZFs({^C)uFkoOQ2>khyb>3Xzf%G0x@A>9e{vLLF(EEq%^Ti840srQ&-+smXV(|wXKR+0%eD={tz<rQ<)ze;47LucEW$j&0kAQiL!G{)p4Z^<*)(6-l)ZtGN_fl+R<Duz~hU6tVylL=G=dQriUBJgn<>6TOb1zEx=zP8hoeucP1zvG~ZH`{7{d{L{_u3J?ANY-ndl3wfymR{F6RP{>{oy?s-o^MOQ$F_IV&HDPAD?~x&DP(a;vY%$b?^67^r8~q)Vx=NJn;RYa((|)wq7y+LlJs6;ZAv#_AgiQUQ00Wrl;?ZQu-olaPZ+q-|wzyy07Nf%#ZxIQ~uIC#c+Yo*3j<3`*gSDp915>4eyqH3B;$w6ZCOZeLY=$$>N`t@QK2QB!6wKE%3_ZN5As+Gq+4nGkxWKQC=#q#tee^&ci3cemn>Ll;b^r%3pW>?<ayn`IY!*zJ5G7{`pomzF-VU1j%1nd`7Bl0<`I;3jDxbxfkKY)9<bLe?#!^lH5H*y(PL&bY11YQ{lVyAB4U?y(jlas(%Os-rYbk{lKEKrvN8y`wkR@#22%DvfHaOeE7n<y&r-9>KXU<<X5M7IjEU${u{iQmiM^{eq-$W!wTR##Ow0E|Jg5I+NB3%P|{vc2K_rGw7R$y#27CGGe;1ufqm#;cK8qI?ltaVo<G;t&t!iQ<9_0`mA{K{e|-t&b)c6ZmP3K^?ymCuA2@i?(_1~br^XlOeou?<p847szZ>==N&eaAemvtX^7-etFa61@J@5NpPNg2T=u0a5QicAe$@zi<`uCS=_xH8ut%r4jw0(EVm+bsezW!X79<cZ2w;BDvD@%`K|EVs$;r?S``rEnvqe^{c>5;htgdc4GZIucbPu)|?FPy%Ud|@;Y<^J{yzdt^}et!S7^q_F(^tJ1GwZ{ufZ%voAH>HJQ1jdm}YyV<`dxiL7h!=n-_;pSRwjX}oAUM9&ZH)=;`RTs@(024Go&A&@QeW&6eahZXrhaR-UMRe@cmYdy^M1@N_m!7A_o;`wr#p9LZQsk=<G>v>IN_TcYrYQpq&vjdV*NpS>sSka?%j*^*Bg|F?(ZjqObUJp{)gxR!MCGdgZfoX2{@=0uhYgG;OF5D`u4lvZ=vAd{}EWSeK|-E-tn~ozEgc0?H&McCGo8izow;!2fad6zP7->DLnPXC42*T2e^0Bsh1hyF`oQL|NNwcuY>P<8~#G|=O0Jl&kDRV^*TZa9Yf~fHZN3y%yVx#`b4+;{An3_EZ;ToK=Yn7w%UB{Z-YMARh*sjo>xAp>UHbh*L?ep^Z&g&`}Y^W_$UYu5`p8~&j)>&zuhQ7;NAuLDtr2O+1XaTBd~v#{;Q{b8S_3Y`yz1Qe}A;$pY;F9A>Z4M*OBf&jd6b<`^B?g*WV1L90G-C<}%3Uo6Vo?^}qSzKU~86fAPTk2zCTMrmi5Xeo30IH#+~2%|q}n>HO=w|41qRqa3-O1H7o}vr6951o(29@RGLQ7VkQ_w<W(Y@RCQtw<+NIUtZR{DD>V<{Cp24N8Z16cz@RWhhQ&OdTqFabN{nN?!pDCxvvF(f4r^#e5!sfE-yN@eZ_sbXZmM%dV#*D>lbC*uNK}<fB#Ac{2Llc_yfh)+VF+TzXc1_@qw%Y|0>KMTgP_=2jV=zALl<s(cLP4$=mJyV(UfKUmCerv;BOi=>GWQ-%#r3xBu4;<LiBu>I4i+j&FW${{ALl?p5sl^O}E(i>;&WUfaM=H>NL(zqJbP>S6r{<SR@7eP8_z)Ub9B*z<oI7;k}h_sBnR9`x|bN8J2VY5yDyuLmlx4eWnx(0+IL-~7Y%f?nvW_e(Dw&fTqFaJ}6zf4&NQE1&;ZYwx4*Kcx0|bnj{DC9Yn?{Qkz%3yaA&qF<Y?_oKhZ!*8;F<f;F++xm~;`&Fg@m8l#&;PnRg3#M0M|65T3f4v6@(7hAa+($^<0sj3<k$!=A3HeW!{j>qzjq|3wueTX@eqXr1&lJ!vTK$?Ye!MXM{g?Xk^Pes%{y5(LhfMPxen0Mn9uW7phn?P?^cR5wQ6515FcJOQD}M!gey8)d2~1up=I4)WzVu!%)8^CLE%fK`ddW$z_5MA+{&Y3{i<a&o_ji}PU-Hm<_kAaFZ(1K2;kRM-PXqQJNdA34^9SJnBB}qHz5n?R`nBsM9)E(Z4;BA@f&1yBp<judzqsMYXNhl}{r9i?@1Gd{{$bC5y7T=7)5phzpLVX_{tqXb!p8'


def banner(title):
    print('\n' + '=' * 72)
    print(title)
    print('=' * 72)


def getv(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, 'get', None)
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            pass
    return getattr(value, key, default)


def as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    try:
        return dict(value)
    except Exception:
        return value


def restore_base_agent():
    source = zlib.decompress(base64.b85decode(BASE_SOURCE_B85.encode('ascii')))
    BASE_PATH.write_bytes(source)
    compile(source, str(BASE_PATH), 'exec')
    spec = importlib.util.spec_from_file_location('v16_base_for_training', BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(f'[OK] Restored exact V16-RC5 core: {BASE_PATH} ({len(source)} bytes)')
    return source.decode('utf-8'), module


def import_pyg():
    try:
        import torch
        from torch_geometric.data import Data
        from torch_geometric.loader import DataLoader
        from torch_geometric.nn import GCNConv
        print(f'[OK] torch={torch.__version__}')
        import torch_geometric
        print(f'[OK] torch_geometric={torch_geometric.__version__} (already importable)')
        return torch, Data, DataLoader, GCNConv
    except Exception as first_error:
        candidates = []
        if Path(PYG_WHEEL_HINT).exists():
            candidates.append(PYG_WHEEL_HINT)
        candidates += glob.glob('/kaggle/input/**/torch_geometric-2.6.1-py3-none-any.whl', recursive=True)
        candidates += glob.glob('/kaggle/input/**/torch_geometric-*.whl', recursive=True)
        seen = set()
        for wheel in candidates:
            if wheel in seen:
                continue
            seen.add(wheel)
            if wheel not in sys.path:
                sys.path.insert(0, wheel)
            try:
                import torch
                from torch_geometric.data import Data
                from torch_geometric.loader import DataLoader
                from torch_geometric.nn import GCNConv
                import torch_geometric
                print(f'[OK] torch={torch.__version__}')
                print(f'[OK] torch_geometric={torch_geometric.__version__} from {wheel}')
                return torch, Data, DataLoader, GCNConv
            except Exception:
                continue
        raise RuntimeError(
            'PyTorch Geometric could not be imported. The supplied wheel path was '
            f'{PYG_WHEEL_HINT!r}. First import error: {first_error}'
        )


def town_demand(obs, item, step):
    demand = 1 if item != 'FERTILIZER' and step % 24 == 0 else 0
    if step % 4 != 0:
        return demand
    town = getv(obs, 'town', {}) or {}
    for shop in list(getv(town, 'unlocked_shops', []) or []):
        products = SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += 2 if len(products) == 1 else 1
    return demand


def planned_quantity(actions, step, item, horizon=1):
    future = step + horizon
    if not 0 <= future < len(actions):
        return 0
    return sum(
        max(0, int(order[2]))
        for order in (actions[future].get('market') or [])
        if len(order) >= 3 and order[0] == 'SELL' and order[1] == item
    )


def clip(v, lo=-3.0, hi=3.0):
    return lo if v < lo else hi if v > hi else v


def product_for_tile(tile):
    if not isinstance(tile, dict):
        return None
    if tile.get('kind') == 'PLANT':
        crop = tile.get('crop')
        return crop if crop in ('MELON', 'STRAWBERRY') else None
    if tile.get('kind') in ('COOP', 'PASTURE'):
        animal = tile.get('animal')
        if animal == 'COW':
            return 'MILK'
        if animal == 'SHEEP':
            return 'WOOL'
    return None


def graph_arrays(obs, step, actions, seat_override=None, current_action=None):
    seat_raw = getv(obs, 'player', seat_override if seat_override is not None else 0)
    try:
        seat = int(seat_raw)
    except Exception:
        seat = int(seat_override or 0)
    seat = 1 if seat == 1 else 0

    farms = list(getv(obs, 'farms', []) or [])
    nodes = [[0.0] * FEATURE_DIM for _ in range(NODE_COUNT)]
    edges = set()
    if len(farms) < 2:
        return nodes, []

    own, opp = farms[seat], farms[1 - seat]
    day = float(getv(obs, 'day', step // 24) or 0)
    day_frac = clip(day / 30.0, 0.0, 1.0)

    def add_edge(a, b):
        if 0 <= a < NODE_COUNT and 0 <= b < NODE_COUNT and a != b:
            edges.add((a, b))
            edges.add((b, a))

    def encode_farm(farm, base, is_self):
        tiles = list(getv(farm, 'tiles', []) or [])
        farmer_raw = getv(farm, 'farmer', [-999, -999]) or [-999, -999]
        try:
            farmer = (int(farmer_raw[0]), int(farmer_raw[1]))
        except Exception:
            farmer = (-999, -999)
        hand_counts = {}
        for p in list(getv(farm, 'hands', []) or []):
            try:
                key = (int(p[0]), int(p[1]))
                hand_counts[key] = hand_counts.get(key, 0) + 1
            except Exception:
                pass
        h = len(tiles)
        w = len(tiles[0]) if h and isinstance(tiles[0], (list, tuple)) else 0
        for y in range(min(10, h)):
            for x in range(min(10, w)):
                idx = base + y * 10 + x
                f = nodes[idx]
                f[0 if is_self else 1] = 1.0
                tile = tiles[y][x]
                if tile is None:
                    f[3] = 1.0
                elif tile == 'LOCKED':
                    f[4] = 1.0
                elif isinstance(tile, dict):
                    kind = tile.get('kind')
                    if kind == 'WEED':
                        f[5] = 1.0
                    elif kind == 'PLANT':
                        f[6] = 1.0
                        product = product_for_tile(tile)
                        if product in ITEMS:
                            f[8 + ITEMS.index(product)] = 1.0
                        f[12] = 0.0 if bool(tile.get('watered_today')) else 1.0
                        f[13] = 1.0 if int(tile.get('fertilized_until_day', -1) or -1) >= int(day) else 0.0
                        f[14] = clip(float(tile.get('yield_units', 0) or 0) / 6.0, 0.0, 1.5)
                        planted = int(tile.get('planted_day', int(day)) or int(day))
                        f[15] = clip((day - planted) / 16.0, 0.0, 2.0)
                    elif kind in ('COOP', 'PASTURE'):
                        f[7] = 1.0
                        product = product_for_tile(tile)
                        if product in ITEMS:
                            f[8 + ITEMS.index(product)] = 1.0
                        f[12] = 0.0 if bool(tile.get('fed_today')) else 1.0
                        f[13] = 1.0 if bool(tile.get('cared_today')) else 0.0
                        f[14] = clip(float(tile.get('yield_units', 0) or 0) / 6.0, 0.0, 1.5)
                        placed = int(tile.get('placed_day', int(day)) or int(day))
                        f[15] = clip((day - placed) / 16.0, 0.0, 2.0)
                f[16] = 1.0 if farmer == (x, y) else 0.0
                f[17] = clip(float(hand_counts.get((x, y), 0)) / 4.0, 0.0, 1.0)
                f[23] = day_frac

                if x > 0:
                    add_edge(idx, idx - 1)
                if y > 0:
                    add_edge(idx, idx - 10)
                product = product_for_tile(tile)
                if product in ITEMS:
                    add_edge(idx, PRODUCT_START + ITEMS.index(product))

    encode_farm(own, 0, True)
    encode_farm(opp, 100, False)

    market = getv(obs, 'market', {}) or {}
    prices = getv(market, 'prices', {}) or {}
    inventory = getv(market, 'inventory', {}) or {}
    private = getv(obs, 'private', {}) or {}
    shed = getv(private, 'shed', {}) or {}

    for j, item in enumerate(ITEMS):
        idx = PRODUCT_START + j
        f = nodes[idx]
        f[2] = 1.0
        f[8 + j] = 1.0
        base_price = BASE_PRICE[item]
        f[18] = clip(float(getv(prices, item, base_price) or base_price) / base_price, 0.0, 4.0)
        inv = float(getv(inventory, item, 10000) or 10000)
        f[19] = clip((10000.0 - inv) / 1000.0, -3.0, 3.0)
        f[20] = clip(float(getv(shed, item, 0) or 0) / 50.0, 0.0, 2.0)
        f[21] = clip(float(town_demand(obs, item, step)) / 4.0, 0.0, 2.0)
        if current_action is None:
            current_q = planned_quantity(actions, step, item, 0)
        else:
            current_q = sum(
                max(0, int(o[2]))
                for o in (current_action.get('market') or [])
                if len(o) >= 3 and o[0] == 'SELL' and o[1] == item
            )
        f[22] = clip(float(current_q) / 20.0, 0.0, 2.0)
        f[23] = day_frac

    for a in range(4):
        for b in range(a + 1, 4):
            add_edge(PRODUCT_START + a, PRODUCT_START + b)

    return nodes, sorted(edges)


def load_agent_file(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def run_game(make, left, right, seed):
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(seed)}, debug=True)
    env.run([left, right])
    final = env.steps[-1]
    statuses = [str(s.status) for s in final]
    if statuses != ['DONE', 'DONE']:
        raise RuntimeError(f'game seed={seed} failed: {statuses}')
    return env


def money_pair(env):
    state0 = env.steps[-1][0]
    obs = getv(state0, 'observation', {}) or {}
    farms = list(getv(obs, 'farms', []) or [])
    if len(farms) >= 2:
        return float(getv(farms[0], 'money', 0.0) or 0.0), float(getv(farms[1], 'money', 0.0) or 0.0)
    # Fallback only if a future environment changes final observation structure.
    return float(getv(env.steps[-1][0], 'reward', 0.0) or 0.0), float(getv(env.steps[-1][1], 'reward', 0.0) or 0.0)


def _module_from_path(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _add_sell(action, item, quantity):
    action = copy.deepcopy(action or {})
    action['farmer'] = list(action.get('farmer') or ['PASS'])
    action['hands'] = [list(x or ['PASS']) for x in (action.get('hands') or [])]
    market = [list(x) for x in (action.get('market') or [])]
    q = max(0, int(quantity))
    if q <= 0:
        action['market'] = market[:10]
        return action
    for order in market:
        if len(order) >= 3 and order[0] == 'SELL' and order[1] == item:
            order[2] = max(0, int(order[2])) + q
            action['market'] = market[:10]
            return action
    if len(market) < 10:
        market.append(['SELL', item, q])
    action['market'] = market[:10]
    return action


def _remove_sell(action, item, quantity):
    action = copy.deepcopy(action or {})
    action['farmer'] = list(action.get('farmer') or ['PASS'])
    action['hands'] = [list(x or ['PASS']) for x in (action.get('hands') or [])]
    remaining = max(0, int(quantity))
    market = []
    for raw in (action.get('market') or []):
        order = list(raw)
        if remaining > 0 and len(order) >= 3 and order[0] == 'SELL' and order[1] == item:
            q = max(0, int(order[2]))
            take = min(q, remaining)
            q -= take
            remaining -= take
            if q <= 0:
                continue
            order[2] = q
        market.append(order)
    action['market'] = market[:10]
    return action



def _sell_quantity(action, item):
    total = 0
    for order in (action.get('market') or []):
        if len(order) >= 3 and order[0] == 'SELL' and order[1] == item:
            try:
                total += max(0, int(order[2]))
            except Exception:
                pass
    return total


def _logging_v16_sales(path, tag):
    """Fresh V16 instance that records every premium SELL actually emitted."""
    mod = _module_from_path(path, tag)
    records = []

    def wrapped(obs):
        action = mod.agent(obs)
        try:
            seat = 1 if int(getv(obs, 'player', 0) or 0) == 1 else 0
            step = int(getv(obs, 'step', 0) or 0)
            sells = {}
            for item in ITEMS:
                q = _sell_quantity(action, item)
                if q > 0:
                    sells[item] = q
            if sells:
                records.append({
                    'step': step,
                    'seat': seat,
                    'obs': copy.deepcopy(obs),
                    'action': copy.deepcopy(action),
                    'sells': sells,
                })
        except Exception:
            pass
        return action

    return wrapped, records


def _can_reinsert_next(base_module, step, item):
    future = int(step) + 1
    if not 0 <= future < len(base_module._ACTIONS):
        return False
    market = list(base_module._ACTIONS[future].get('market') or [])
    if any(len(o) >= 3 and o[0] == 'SELL' and o[1] == item for o in market):
        return True
    return len(market) < 10


def _delay_one_sale_agent(path, target_step, item, requested_quantity, tag):
    """Counterfactual V16: move one premium sale from t to exactly t+1."""
    mod = _module_from_path(path, tag)
    delayed = {'q': 0}

    def wrapped(obs):
        action = mod.agent(obs)
        step = int(getv(obs, 'step', 0) or 0)

        if step == target_step:
            exact = _sell_quantity(action, item)
            q = min(max(0, int(requested_quantity)), exact)
            if q > 0:
                action = _remove_sell(action, item, q)
                delayed['q'] = q

        elif step == target_step + 1 and delayed['q'] > 0:
            action = _add_sell(action, item, delayed['q'])

        return action

    return wrapped


def _select_sale_records(records, seed, seat, base_module):
    flat = []
    for rec in records:
        for item, q in rec['sells'].items():
            if (
                item in ITEMS
                and q > 0
                and rec['step'] < 718
                and _can_reinsert_next(base_module, rec['step'], item)
            ):
                flat.append({
                    'step': int(rec['step']),
                    'seat': int(rec['seat']),
                    'obs': rec['obs'],
                    'action': rec['action'],
                    'item': item,
                    'quantity': int(q),
                })

    if len(flat) <= MAX_CF_PER_SEAT:
        return flat

    rng = random.Random(int(seed) * 37 + int(seat) * 1009 + SEED)
    by_item = {item: [] for item in ITEMS}
    for c in flat:
        by_item[c['item']].append(c)

    chosen = []
    # First force product diversity.
    for item in ITEMS:
        if by_item[item] and len(chosen) < MAX_CF_PER_SEAT:
            pool = sorted(by_item[item], key=lambda x: x['quantity'], reverse=True)
            chosen.append(rng.choice(pool[:min(5, len(pool))]))

    remaining = [c for c in flat if c not in chosen]

    # Half of remaining budget: highest-volume events.
    budget = MAX_CF_PER_SEAT - len(chosen)
    take_large = max(0, budget // 2)
    remaining.sort(key=lambda x: x['quantity'], reverse=True)
    chosen.extend(remaining[:take_large])

    # Other half: random events for state diversity.
    left = [c for c in remaining if c not in chosen]
    rng.shuffle(left)
    chosen.extend(left[:max(0, MAX_CF_PER_SEAT - len(chosen))])

    return sorted(chosen, key=lambda c: c['step'])


def _counterfactual_examples_for_seat(torch, Data, make, base_module, seed, seat, opponent, split_name):
    logger, records = _logging_v16_sales(BASE_PATH, f'log_{split_name}_{seed}_{seat}')
    if seat == 0:
        baseline_env = run_game(make, logger, opponent, seed)
    else:
        baseline_env = run_game(make, opponent, logger, seed)
    baseline_money = money_pair(baseline_env)[seat]

    selected = _select_sale_records(records, seed, seat, base_module)
    observed = sum(len(r['sells']) for r in records)
    print(
        f'[{split_name}] seed={seed} seat={seat}: '
        f'observed_premium_sales={observed} selected={len(selected)}'
    )

    out = []
    for idx, c in enumerate(selected):
        cf_agent = _delay_one_sale_agent(
            BASE_PATH,
            c['step'],
            c['item'],
            c['quantity'],
            f'cf_delay_{split_name}_{seed}_{seat}_{idx}',
        )
        if seat == 0:
            cf_env = run_game(make, cf_agent, opponent, seed)
        else:
            cf_env = run_game(make, opponent, cf_agent, seed)

        cf_money = money_pair(cf_env)[seat]
        gain = float(cf_money - baseline_money)  # positive => delay helped

        nodes, edges = graph_arrays(
            c['obs'],
            c['step'],
            base_module._ACTIONS,
            seat_override=seat,
            current_action=c['action'],
        )
        if not edges:
            continue

        j = ITEMS.index(c['item'])
        y = [0.0] * 4
        mask = [0.0] * 4
        gains = [0.0] * 4
        qty = [0.0] * 4

        mask[j] = 1.0
        y[j] = 1.0 if gain > MIN_CANCEL_GAIN else 0.0
        gains[j] = gain
        qty[j] = float(c['quantity'])

        data = Data(
            x=torch.tensor(nodes, dtype=torch.float32),
            edge_index=torch.tensor(edges, dtype=torch.long).t().contiguous(),
        )
        data.y = torch.tensor([y], dtype=torch.float32)
        data.mask = torch.tensor([mask], dtype=torch.float32)
        data.gain = torch.tensor([gains], dtype=torch.float32)
        data.qty = torch.tensor([qty], dtype=torch.float32)
        out.append(data)

        verdict = 'DELAY+' if gain > MIN_CANCEL_GAIN else 'SELL_NOW'
        print(
            f'    step={c["step"]:3d} {c["item"]:<11} '
            f'q={c["quantity"]:2d} delay_gain={gain:+.1f} {verdict}'
        )

    return out


def generate_dataset(torch, Data, make, base_source, base_module):
    banner('1/7 — Generate REAL premium-sale timing counterfactuals')
    train, valid = [], []

    for seed in TRAIN_SELFPLAY_SEEDS:
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 0, str(BASE_PATH), 'train selfplay'
        )
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 1, str(BASE_PATH), 'train selfplay'
        )

    for seed in TRAIN_STARTER_SEEDS:
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 0, 'starter', 'train starter'
        )
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed + 1, 1, 'starter', 'train starter reverse'
        )

    for seed in TRAIN_RANDOM_SEEDS:
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 0, 'random', 'train random'
        )
        train += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed + 1, 1, 'random', 'train random reverse'
        )

    for seed in VALID_SELFPLAY_SEEDS:
        valid += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 0, str(BASE_PATH), 'valid selfplay'
        )
        valid += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 1, str(BASE_PATH), 'valid selfplay'
        )

    for seed in VALID_STARTER_SEEDS:
        valid += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed, 0, 'starter', 'valid starter'
        )
        valid += _counterfactual_examples_for_seat(
            torch, Data, make, base_module, seed + 1, 1, 'starter', 'valid starter reverse'
        )

    if len(train) < 12 or len(valid) < 4:
        raise RuntimeError(
            f'Not enough premium-sale counterfactuals: train={len(train)}, valid={len(valid)}. '
            'Check the observed_premium_sales counts above.'
        )

    def stats(name, data):
        masked = [0, 0, 0, 0]
        positives = [0, 0, 0, 0]
        observed_gain = [0.0, 0.0, 0.0, 0.0]
        for d in data:
            m = d.mask[0].tolist()
            y = d.y[0].tolist()
            g = d.gain[0].tolist()
            for j in range(4):
                if m[j] > 0:
                    masked[j] += 1
                    positives[j] += int(y[j] > 0.5)
                    observed_gain[j] += float(g[j])

        print(f'[{name}] graphs={len(data)}')
        for j, item in enumerate(ITEMS):
            print(
                f'    {item:<11} events={masked[j]:3d} '
                f'delay_beneficial={positives[j]:3d} '
                f'sum_delay_gain={observed_gain[j]:+.1f}'
            )

    stats('train', train)
    stats('valid', valid)
    return train, valid


def make_model(torch, GCNConv):
    class ResidualGCN(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = GCNConv(FEATURE_DIM, HIDDEN, add_self_loops=True, normalize=True)
            self.conv2 = GCNConv(HIDDEN, HIDDEN, add_self_loops=True, normalize=True)
            self.head1 = torch.nn.Linear(HIDDEN * 3, HIDDEN)
            self.head2 = torch.nn.Linear(HIDDEN, 1)

        def forward(self, data):
            x = torch.relu(self.conv1(data.x, data.edge_index))
            x = torch.relu(self.conv2(x, data.edge_index))
            # Every graph intentionally has exactly NODE_COUNT nodes.
            # PyG Batch exposes num_graphs, but a standalone Data object
            # (used by verify_export) does not. Infer the batch size safely.
            try:
                b = int(data.num_graphs)
            except Exception:
                if x.size(0) % NODE_COUNT != 0:
                    raise RuntimeError(
                        f'Unexpected node count: {x.size(0)} is not divisible by {NODE_COUNT}'
                    )
                b = int(x.size(0) // NODE_COUNT)
            x = x.view(b, NODE_COUNT, HIDDEN)
            own = x[:, :100, :].mean(dim=1)
            opp = x[:, 100:200, :].mean(dim=1)
            products = x[:, 200:204, :]
            own = own[:, None, :].expand(-1, 4, -1)
            opp = opp[:, None, :].expand(-1, 4, -1)
            z = torch.cat([products, own, opp], dim=-1)
            z = torch.relu(self.head1(z))
            return self.head2(z).squeeze(-1)

    return ResidualGCN()


def compute_pos_weight(torch, dataset):
    pos = torch.zeros(4)
    neg = torch.zeros(4)
    for d in dataset:
        y = d.y[0]
        m = d.mask[0]
        pos += m * y
        neg += m * (1.0 - y)
    # Cap to avoid unstable huge weights on tiny categories.
    return torch.clamp(neg / torch.clamp(pos, min=1.0), min=1.0, max=12.0)


def train_model(torch, DataLoader, GCNConv, train_data, valid_data):
    banner('2/7 — Train residual GCN with held-out validation')
    random.seed(SEED)
    torch.manual_seed(SEED)
    model = make_model(torch, GCNConv)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    pos_weight = compute_pos_weight(torch, train_data)
    criterion = torch.nn.BCEWithLogitsLoss(reduction='none', pos_weight=pos_weight)
    loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        total_mask = 0.0
        for batch in loader:
            optimizer.zero_grad()
            logits = model(batch)
            raw = criterion(logits, batch.y)
            denom = torch.clamp(batch.mask.sum(), min=1.0)
            loss = (raw * batch.mask).sum() / denom
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            optimizer.step()
            total_loss += float(loss.item()) * float(denom.item())
            total_mask += float(denom.item())
        if epoch == 1 or epoch % 4 == 0 or epoch == EPOCHS:
            print(f'epoch {epoch:02d}/{EPOCHS}  masked-BCE={total_loss/max(total_mask,1):.5f}')

    thresholds, report = choose_thresholds(torch, model, DataLoader, valid_data)
    print('\nValidation threshold selection:')
    for item in ITEMS:
        r = report[item]
        if r['enabled']:
            print(f"  {item:<11} threshold={r['threshold']:.2f}  n={r['n']}  precision={r['precision']:.2f}  observed_gain={r['gain']:+.1f}")
        else:
            print(f"  {item:<11} DISABLED (not enough held-out evidence)")
    return model, thresholds, report


def choose_thresholds(torch, model, DataLoader, valid_data):
    model.eval()
    probs_all, mask_all, gain_all = [], [], []
    loader = DataLoader(valid_data, batch_size=BATCH_SIZE, shuffle=False)
    with torch.no_grad():
        for batch in loader:
            probs_all.append(torch.sigmoid(model(batch)).cpu())
            mask_all.append(batch.mask.cpu())
            gain_all.append(batch.gain.cpu())
    probs = torch.cat(probs_all, dim=0)
    masks = torch.cat(mask_all, dim=0)
    gains = torch.cat(gain_all, dim=0)

    thresholds = [1.10] * 4
    report = {}
    candidates = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    for j, item in enumerate(ITEMS):
        best = None
        for th in candidates:
            pred = (probs[:, j] >= th) & (masks[:, j] > 0.5)
            n = int(pred.sum().item())
            if n < MIN_VALID_PREDICTIONS:
                continue
            selected_gains = gains[:, j][pred]
            precision = float((selected_gains > 0).float().mean().item())
            total_gain = float(selected_gains.sum().item())
            if precision < MIN_VALID_PRECISION or total_gain <= 0:
                continue
            score = (total_gain, precision, th)
            if best is None or score > best[0]:
                best = (score, th, n, precision, total_gain)
        if best is None:
            report[item] = {'enabled': False, 'threshold': 1.10, 'n': 0, 'precision': 0.0, 'gain': 0.0}
        else:
            _, th, n, precision, total_gain = best
            thresholds[j] = float(th)
            report[item] = {'enabled': True, 'threshold': float(th), 'n': n, 'precision': precision, 'gain': total_gain}
    return thresholds, report



def force_gnn_thresholds(torch, model, DataLoader, train_data, valid_data, thresholds):
    """
    Guarantee that the final Kaggle agent actually uses the learned GCN.

    - Keep any threshold that genuinely passed held-out validation.
    - For disabled products, choose a conservative threshold from real
      train+validation counterfactuals.
    - Prefer thresholds with positive observed counterfactual gain.
    - If none exists, use the 90th percentile of the model's probability
      on that product so the GCN remains active but selective.
    """
    data = train_data + valid_data
    loader = DataLoader(data, batch_size=BATCH_SIZE, shuffle=False)

    model.eval()
    probs_all, mask_all, gain_all = [], [], []
    with torch.no_grad():
        for batch in loader:
            probs_all.append(torch.sigmoid(model(batch)).cpu())
            mask_all.append(batch.mask.cpu())
            gain_all.append(batch.gain.cpu())

    probs = torch.cat(probs_all, dim=0)
    masks = torch.cat(mask_all, dim=0)
    gains = torch.cat(gain_all, dim=0)

    out = list(thresholds)
    candidates = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65,
                  0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    print("\nForced-GCN threshold completion:")
    for j, item in enumerate(ITEMS):
        if out[j] <= 1.0:
            print(f"  {item:<11} keep validated threshold={out[j]:.3f}")
            continue

        best = None
        relevant = masks[:, j] > 0.5

        for th in candidates:
            pred = (probs[:, j] >= th) & relevant
            n = int(pred.sum().item())
            if n < 1:
                continue
            selected_gains = gains[:, j][pred]
            total_gain = float(selected_gains.sum().item())
            precision = float((selected_gains > 0).float().mean().item())
            # Primary objective: positive measured gain; then precision; then
            # prefer higher threshold for a conservative residual.
            score = (1 if total_gain > 0 else 0, total_gain, precision, th)
            if best is None or score > best[0]:
                best = (score, th, n, precision, total_gain)

        if best is not None and best[4] > 0:
            _, th, n, precision, total_gain = best
            out[j] = float(th)
            print(
                f"  {item:<11} forced threshold={th:.2f} "
                f"n={n} precision={precision:.2f} observed_gain={total_gain:+.1f}"
            )
        else:
            vals = probs[:, j][relevant]
            if vals.numel() == 0:
                # This should not happen with the current dataset, but keep a
                # valid threshold so the model is not structurally disabled.
                th = 0.95
            else:
                th = float(torch.quantile(vals, 0.90).item())
                th = max(0.05, min(0.95, th))
            out[j] = th
            print(
                f"  {item:<11} no positive threshold found; "
                f"use selective p90 threshold={th:.3f}"
            )

    assert all(0.0 < float(t) <= 1.0 for t in out)
    return out

def export_weights(model, thresholds):
    # PyG GCNConv: out = normalized_adj @ (x @ W.T) + bias.
    def arr(t):
        return t.detach().cpu().tolist()
    return {
        'feature_dim': FEATURE_DIM,
        'hidden': HIDDEN,
        'thresholds': [float(v) for v in thresholds],
        'max_lead_fraction': float(MAX_LEAD_FRACTION),
        'conv1_w': arr(model.conv1.lin.weight),
        'conv1_b': arr(model.conv1.bias),
        'conv2_w': arr(model.conv2.lin.weight),
        'conv2_b': arr(model.conv2.bias),
        'head1_w': arr(model.head1.weight),
        'head1_b': arr(model.head1.bias),
        'head2_w': arr(model.head2.weight),
        'head2_b': arr(model.head2.bias),
    }


def manual_matvec(W, x, b=None):
    out = []
    for i, row in enumerate(W):
        s = 0.0 if b is None else float(b[i])
        for j, w in enumerate(row):
            s += float(w) * float(x[j])
        out.append(s)
    return out


def manual_gcn_layer(h, edges, W, b):
    n = len(h)
    adj = [set([i]) for i in range(n)]
    for a, c in edges:
        if 0 <= a < n and 0 <= c < n:
            adj[c].add(a)  # incoming sources to target c
    deg = [len(adj[i]) for i in range(n)]
    out = []
    dim = len(h[0])
    for i in range(n):
        agg = [0.0] * dim
        di = float(deg[i])
        for j in adj[i]:
            norm = 1.0 / math.sqrt(di * float(deg[j]))
            hj = h[j]
            for k in range(dim):
                agg[k] += norm * float(hj[k])
        v = manual_matvec(W, agg, b)
        out.append([max(0.0, z) for z in v])
    return out


def manual_predict(nodes, edges, weights):
    h1 = manual_gcn_layer(nodes, edges, weights['conv1_w'], weights['conv1_b'])
    h2 = manual_gcn_layer(h1, edges, weights['conv2_w'], weights['conv2_b'])
    own = [sum(h2[i][k] for i in range(100)) / 100.0 for k in range(HIDDEN)]
    opp = [sum(h2[i][k] for i in range(100, 200)) / 100.0 for k in range(HIDDEN)]
    logits = []
    for j in range(4):
        z = h2[PRODUCT_START + j] + own + opp
        h = manual_matvec(weights['head1_w'], z, weights['head1_b'])
        h = [max(0.0, v) for v in h]
        logit = manual_matvec(weights['head2_w'], h, weights['head2_b'])[0]
        logits.append(logit)
    return logits


def verify_export(torch, model, valid_data, weights):
    banner('3/7 — Verify pure-Python exported GCN == PyTorch Geometric GCN')
    model.eval()
    max_diff = 0.0
    checks = min(8, len(valid_data))
    with torch.no_grad():
        for d in valid_data[:checks]:
            # d is a standalone torch_geometric.data.Data, not a Batch.
            # ResidualGCN.forward now infers b=1 from node count.
            pyg = model(d).view(-1).cpu().tolist()
            nodes = d.x.cpu().tolist()
            edge_pairs = list(zip(d.edge_index[0].cpu().tolist(), d.edge_index[1].cpu().tolist()))
            manual = manual_predict(nodes, edge_pairs, weights)
            diff = max(abs(float(a) - float(b)) for a, b in zip(pyg, manual))
            max_diff = max(max_diff, diff)
    print(f'[check] max |PyG logit - exported logit| = {max_diff:.8f}')
    if max_diff > 2e-4:
        raise RuntimeError('Exported GCN inference does not match GCNConv closely enough.')
    print('[OK] Export equivalence passed.')


def residual_source(weights):
    payload = base64.b85encode(zlib.compress(json.dumps(weights, separators=(',', ':')).encode('utf-8'), 9)).decode('ascii')
    return r'''
# ===== VALIDATED RESIDUAL GCN (weights embedded; no torch/PyG at runtime) =====
import math as _gmath

_G_ITEMS = ('MELON', 'MILK', 'STRAWBERRY', 'WOOL')
_G_BASE_PRICE = {'MELON': 250.0, 'MILK': 160.0, 'STRAWBERRY': 120.0, 'WOOL': 200.0}
_G_SHOP_PRODUCTS = {
    'BAKERY': ('EGG', 'WHEAT'),
    'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),
    'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'),
    'YARN_STORE': ('WOOL',),
    'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'),
    'PET_CAFE': ('CARROT',),
    'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'),
    'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'),
}
_G_FDIM = 24
_G_NODES = 204
_G_PSTART = 200
_G_WEIGHTS = json.loads(zlib.decompress(base64.b85decode(__PAYLOAD__)).decode('utf-8'))
_G_THRESH = list(_G_WEIGHTS['thresholds'])
_G_MAX_FRAC = float(_G_WEIGHTS['max_lead_fraction'])
_G_ADD_BACK = {0: {}, 1: {}}


def _gclip(v, lo=-3.0, hi=3.0):
    return lo if v < lo else hi if v > hi else v


def _gproduct(tile):
    if not isinstance(tile, dict):
        return None
    if tile.get('kind') == 'PLANT':
        crop = tile.get('crop')
        return crop if crop in ('MELON', 'STRAWBERRY') else None
    if tile.get('kind') in ('COOP', 'PASTURE'):
        animal = tile.get('animal')
        if animal == 'COW': return 'MILK'
        if animal == 'SHEEP': return 'WOOL'
    return None


def _gtown(obs, item, step):
    demand = 1 if item != 'FERTILIZER' and step % 24 == 0 else 0
    if step % 4 != 0:
        return demand
    town = _get(obs, 'town', {}) or {}
    for shop in list(_get(town, 'unlocked_shops', []) or []):
        products = _G_SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += 2 if len(products) == 1 else 1
    return demand


def _gsellq(action, item):
    total=0
    for o in (action.get('market') or []):
        if len(o)>=3 and o[0]=='SELL' and o[1]==item:
            try: total += max(0,int(o[2]))
            except Exception: pass
    return total


def _ggraph(obs, step, action):
    seat=1 if int(_get(obs,'player',0) or 0)==1 else 0
    farms=list(_get(obs,'farms',[]) or [])
    nodes=[[0.0]*_G_FDIM for _ in range(_G_NODES)]; edges=set()
    if len(farms)<2: return nodes,[]
    own,opp=farms[seat],farms[1-seat]
    day=float(_get(obs,'day',step//24) or 0); dayf=_gclip(day/30.0,0.0,1.0)
    def edge(a,b):
        if 0<=a<_G_NODES and 0<=b<_G_NODES and a!=b: edges.add((a,b)); edges.add((b,a))
    def enc(farm,base,self_flag):
        tiles=list(_get(farm,'tiles',[]) or []); fr=_get(farm,'farmer',[-999,-999]) or [-999,-999]
        try: farmer=(int(fr[0]),int(fr[1]))
        except Exception: farmer=(-999,-999)
        hc={}
        for p in list(_get(farm,'hands',[]) or []):
            try: k=(int(p[0]),int(p[1])); hc[k]=hc.get(k,0)+1
            except Exception: pass
        h=len(tiles); w=len(tiles[0]) if h and isinstance(tiles[0],(list,tuple)) else 0
        for y in range(min(10,h)):
            for x in range(min(10,w)):
                idx=base+y*10+x; f=nodes[idx]; f[0 if self_flag else 1]=1.0; tile=tiles[y][x]
                if tile is None: f[3]=1.0
                elif tile=='LOCKED': f[4]=1.0
                elif isinstance(tile,dict):
                    kind=tile.get('kind')
                    if kind=='WEED': f[5]=1.0
                    elif kind=='PLANT':
                        f[6]=1.0; prod=_gproduct(tile)
                        if prod in _G_ITEMS: f[8+_G_ITEMS.index(prod)]=1.0
                        f[12]=0.0 if bool(tile.get('watered_today')) else 1.0
                        f[13]=1.0 if int(tile.get('fertilized_until_day',-1) or -1)>=int(day) else 0.0
                        f[14]=_gclip(float(tile.get('yield_units',0) or 0)/6.0,0.0,1.5)
                        planted=int(tile.get('planted_day',int(day)) or int(day)); f[15]=_gclip((day-planted)/16.0,0.0,2.0)
                    elif kind in ('COOP','PASTURE'):
                        f[7]=1.0; prod=_gproduct(tile)
                        if prod in _G_ITEMS: f[8+_G_ITEMS.index(prod)]=1.0
                        f[12]=0.0 if bool(tile.get('fed_today')) else 1.0; f[13]=1.0 if bool(tile.get('cared_today')) else 0.0
                        f[14]=_gclip(float(tile.get('yield_units',0) or 0)/6.0,0.0,1.5)
                        placed=int(tile.get('placed_day',int(day)) or int(day)); f[15]=_gclip((day-placed)/16.0,0.0,2.0)
                f[16]=1.0 if farmer==(x,y) else 0.0; f[17]=_gclip(float(hc.get((x,y),0))/4.0,0.0,1.0); f[23]=dayf
                if x>0: edge(idx,idx-1)
                if y>0: edge(idx,idx-10)
                prod=_gproduct(tile)
                if prod in _G_ITEMS: edge(idx,_G_PSTART+_G_ITEMS.index(prod))
    enc(own,0,True); enc(opp,100,False)
    market=_get(obs,'market',{}) or {}; prices=_get(market,'prices',{}) or {}; inv=_get(market,'inventory',{}) or {}
    private=_get(obs,'private',{}) or {}; shed=_get(private,'shed',{}) or {}
    for j,item in enumerate(_G_ITEMS):
        f=nodes[_G_PSTART+j]; f[2]=1.0; f[8+j]=1.0; bp=_G_BASE_PRICE[item]
        f[18]=_gclip(float(_get(prices,item,bp) or bp)/bp,0.0,4.0)
        ii=float(_get(inv,item,10000) or 10000); f[19]=_gclip((10000.0-ii)/1000.0,-3.0,3.0)
        f[20]=_gclip(float(_get(shed,item,0) or 0)/50.0,0.0,2.0)
        f[21]=_gclip(float(_gtown(obs,item,step))/4.0,0.0,2.0)
        f[22]=_gclip(float(_gsellq(action,item))/20.0,0.0,2.0); f[23]=dayf
    for a in range(4):
        for b in range(a+1,4): edge(_G_PSTART+a,_G_PSTART+b)
    return nodes,sorted(edges)


def _gmat(W,x,b):
    return [sum(float(w)*float(x[j]) for j,w in enumerate(row))+float(b[i]) for i,row in enumerate(W)]


def _glayer(h,edges,W,b):
    n=len(h); adj=[set([i]) for i in range(n)]
    for a,c in edges:
        if 0<=a<n and 0<=c<n: adj[c].add(a)
    deg=[len(adj[i]) for i in range(n)]; out=[]; dim=len(h[0])
    for i in range(n):
        agg=[0.0]*dim; di=float(deg[i])
        for j in adj[i]:
            norm=1.0/_gmath.sqrt(di*float(deg[j])); hj=h[j]
            for k in range(dim): agg[k]+=norm*float(hj[k])
        v=_gmat(W,agg,b); out.append([z if z>0.0 else 0.0 for z in v])
    return out


def _gpredict(obs,step,action):
    nodes,edges=_ggraph(obs,step,action)
    if not edges: return [0.0]*4
    w=_G_WEIGHTS
    h1=_glayer(nodes,edges,w['conv1_w'],w['conv1_b'])
    h2=_glayer(h1,edges,w['conv2_w'],w['conv2_b'])
    hidden=int(w['hidden'])
    own=[sum(h2[i][k] for i in range(100))/100.0 for k in range(hidden)]
    opp=[sum(h2[i][k] for i in range(100,200))/100.0 for k in range(hidden)]
    probs=[]
    for j in range(4):
        z=h2[_G_PSTART+j]+own+opp; hh=_gmat(w['head1_w'],z,w['head1_b']); hh=[v if v>0 else 0.0 for v in hh]
        logit=_gmat(w['head2_w'],hh,w['head2_b'])[0]
        if logit>=0: p=1.0/(1.0+_gmath.exp(-min(logit,60.0)))
        else:
            e=_gmath.exp(max(logit,-60.0)); p=e/(1.0+e)
        probs.append(p)
    return probs


def _gremove_sell(action,item,q):
    action=_copy_action(action); remain=max(0,int(q)); market=[]
    for raw in (action.get('market') or []):
        order=list(raw)
        if remain>0 and len(order)>=3 and order[0]=='SELL' and order[1]==item:
            n=max(0,int(order[2])); take=min(n,remain); n-=take; remain-=take
            if n<=0: continue
            order[2]=n
        market.append(order)
    action['market']=market[:10]; return action


def _gadd_sell(action,item,q):
    action=_copy_action(action); q=max(0,int(q)); market=[list(o) for o in (action.get('market') or [])]
    if q<=0: return action
    for o in market:
        if len(o)>=3 and o[0]=='SELL' and o[1]==item:
            o[2]=max(0,int(o[2]))+q; action['market']=market[:10]; return action
    if len(market)<10: market.append(['SELL',item,q])
    action['market']=market[:10]; return action


def _greset(step,seat):
    if step==0: _G_ADD_BACK[seat].clear()
    for s in list(_G_ADD_BACK[seat]):
        if int(s)<step: _G_ADD_BACK[seat].pop(s,None)


def _grestore(action,step,seat):
    due=dict(_G_ADD_BACK[seat].pop(step,{}) or {})
    for item,q in due.items():
        action=_gadd_sell(action,item,q)
    return action


def _gcan_reinsert(step,item):
    future=step+1
    if not 0<=future<len(_ACTIONS): return False
    market=list(_ACTIONS[future].get('market') or [])
    if any(len(o)>=3 and o[0]=='SELL' and o[1]==item for o in market):
        return True
    return len(market)<10


def _gdelay_current_sales(action,obs,step):
    seat=_seat(obs); _greset(step,seat)
    if step>=718: return action
    try: probs=_gpredict(obs,step,action)
    except Exception: return action

    delayed={}
    for j,item in enumerate(_G_ITEMS):
        q=_gsellq(action,item)
        th=float(_G_THRESH[j])
        if q<=0 or th>1.0 or probs[j]<th or not _gcan_reinsert(step,item):
            continue

        # Conservative deployment: only a fraction is delayed.
        move=max(1,int(round(q*float(_G_MAX_FRAC))))
        move=min(q,move)
        action=_gremove_sell(action,item,move)
        delayed[item]=move

    if delayed:
        nxt=_G_ADD_BACK[seat].setdefault(step+1,{})
        for item,q in delayed.items():
            nxt[item]=nxt.get(item,0)+q
    return action


def agent(obs):
    # V16 is still the main policy.
    # The learned residual can only postpone part of a premium SELL by one turn.
    try:
        step=min(max(0,int(_get(obs,'step',0) or 0)),len(_ACTIONS)-1)
        seat=_seat(obs); _greset(step,seat)

        base_action=_v16_agent(obs)

        # Decide only on the fresh V16 sale from this turn.
        action=_gdelay_current_sales(base_action,obs,step)

        # Restore quantities postponed from t-1 AFTER the new decision,
        # so the same quantity cannot be postponed repeatedly.
        action=_grestore(action,step,seat)

        return _align_hands(action,obs)
    except Exception:
        return _v16_agent(obs)

'''.replace('__PAYLOAD__', repr(payload))


def build_candidate_source(base_source, weights):
    if 'def agent(obs):' not in base_source:
        raise RuntimeError('Could not locate V16 agent function for wrapping.')
    # Rename only the final public entrypoint; there is one def agent in this source.
    core = base_source.replace('def agent(obs):', 'def _v16_agent(obs):', 1)
    return core + '\n\n' + residual_source(weights) + '\n'


def evaluate_candidate(make, candidate_path, base_path):
    banner('5/7 — Live unseen-seed candidate vs V16-RC5 safety gate')
    paired = []
    all_margins = []
    for seed in EVAL_SEEDS:
        env_a = run_game(make, str(candidate_path), str(base_path), seed)
        m0, m1 = money_pair(env_a)
        margin_a = m0 - m1
        env_b = run_game(make, str(base_path), str(candidate_path), seed)
        m0b, m1b = money_pair(env_b)
        margin_b = m1b - m0b
        pair = margin_a + margin_b
        paired.append(pair)
        all_margins.extend([margin_a, margin_b])
        print(f'seed={seed}: cand-seat0={margin_a:+.1f}, cand-seat1={margin_b:+.1f}, paired={pair:+.1f}')
    mean_pair = sum(paired) / len(paired)
    positive = sum(v > 0 for v in paired)
    mean_game = sum(all_margins) / len(all_margins)
    print(f'paired mean={mean_pair:+.1f}; positive pairs={positive}/{len(paired)}; game mean={mean_game:+.1f}')
    # Conservative acceptance: positive paired mean and at least half the seed pairs positive.
    accepted = mean_pair > 0.0 and positive >= math.ceil(len(paired) / 2)
    print('[BENCHMARK]', 'GCN beats V16 on this panel' if accepted else 'GCN does not beat V16 on this panel')
    return accepted


def package_and_smoke(make, selected_source):
    banner('6/7 — Final main.py, full smoke test, package')
    MAIN_PATH.write_text(selected_source, encoding='utf-8', newline='\n')
    compile(MAIN_PATH.read_bytes(), str(MAIN_PATH), 'exec')
    env = run_game(make, str(MAIN_PATH), 'random', 451781128)
    m0, m1 = money_pair(env)
    print(f'[smoke] main.py vs random: money {m0:.1f} vs {m1:.1f}; margin={m0-m1:+.1f}')

    with tarfile.open(ARCHIVE_PATH, 'w:gz') as tar:
        tar.add(MAIN_PATH, arcname='main.py')
    with tarfile.open(ARCHIVE_PATH, 'r:gz') as tar:
        names = tar.getnames()
    if names != ['main.py']:
        raise RuntimeError(f'Bad archive root: {names}')
    size = ARCHIVE_PATH.stat().st_size
    if size > 100 * 1024 * 1024:
        raise RuntimeError(f'Submission is over 100 MiB: {size} bytes')
    print(f'[OK] {ARCHIVE_PATH}  size={size/1024:.1f} KiB  content={names}')


def submit():
    banner('7/7 — Kaggle submission')
    cmd = ['kaggle', 'competitions', 'submit', COMPETITION, '-f', str(ARCHIVE_PATH), '-m', SUBMISSION_MESSAGE]
    if not AUTO_SUBMIT:
        print('AUTO_SUBMIT=False. Ready command:')
        print(' '.join(cmd))
        return
    try:
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        print(result.stdout)
        if result.returncode == 0:
            print('[SUCCESS] Submitted to Kaggle.')
        else:
            print('[INFO] Kaggle CLI did not submit automatically, but the archive is ready:')
            print(ARCHIVE_PATH)
            print('Manual/CLI command:')
            print(' '.join(cmd))
    except Exception as e:
        print(f'[INFO] Automatic submission unavailable: {e}')
        print(f'Ready archive: {ARCHIVE_PATH}')
        print('Command:', ' '.join(cmd))



# =====================================================================
# GRAPH DOUBLE-DQN RESIDUAL RL
# =====================================================================

def import_pyg_rl():
    torch, Data, DataLoader, GCNConv = import_pyg()
    from torch_geometric.data import Batch
    return torch, Data, Batch, GCNConv


def make_rl_qnetwork(torch, GCNConv):
    class GraphQNetwork(torch.nn.Module):
        '''GNN state encoder + Q head for five residual actions.'''
        def __init__(self):
            super().__init__()
            self.conv1 = GCNConv(FEATURE_DIM, RL_HIDDEN, add_self_loops=True, normalize=True)
            self.conv2 = GCNConv(RL_HIDDEN, RL_HIDDEN, add_self_loops=True, normalize=True)
            self.q1 = torch.nn.Linear(RL_HIDDEN * 6, RL_HEAD)
            self.q2 = torch.nn.Linear(RL_HEAD, RL_NUM_ACTIONS)
            with torch.no_grad():
                self.q2.bias.zero_()
                self.q2.bias[0] = 0.20

        def forward(self, data):
            x = torch.relu(self.conv1(data.x, data.edge_index))
            x = torch.relu(self.conv2(x, data.edge_index))
            try:
                b = int(data.num_graphs)
            except Exception:
                if int(x.size(0)) % NODE_COUNT != 0:
                    raise RuntimeError(
                        f'RL GNN node count {int(x.size(0))} not divisible by {NODE_COUNT}'
                    )
                b = int(x.size(0) // NODE_COUNT)
            x = x.view(b, NODE_COUNT, RL_HIDDEN)
            own = x[:, :100, :].mean(dim=1)
            opp = x[:, 100:200, :].mean(dim=1)
            products = x[:, PRODUCT_START:PRODUCT_START + 4, :].reshape(b, 4 * RL_HIDDEN)
            state = torch.cat([own, opp, products], dim=-1)
            h = torch.relu(self.q1(state))
            return self.q2(h)

    return GraphQNetwork()


def _edge_index_from_pairs(torch, edges):
    if not edges:
        return torch.empty((2, 0), dtype=torch.long)
    return torch.tensor(edges, dtype=torch.long).t().contiguous()


def rl_data_from_obs(torch, Data, obs, base_action, actions):
    step = min(max(0, int(getv(obs, 'step', 0) or 0)), len(actions) - 1)
    nodes, edges = graph_arrays(obs, step, actions, current_action=base_action)
    return Data(
        x=torch.tensor(nodes, dtype=torch.float32),
        edge_index=_edge_index_from_pairs(torch, edges),
    )


def _sell_qty(action, item):
    q = 0
    for order in list((action or {}).get('market') or []):
        if len(order) >= 3 and order[0] == 'SELL' and order[1] == item:
            try:
                q += max(0, int(order[2]))
            except Exception:
                pass
    return q


def _can_reinsert_from_schedule(actions, step, item):
    future = int(step) + 1
    if not 0 <= future < len(actions):
        return False
    market = list((actions[future] or {}).get('market') or [])
    if any(len(o) >= 3 and o[0] == 'SELL' and o[1] == item for o in market):
        return True
    return len(market) < 10


def rl_feasible_mask(base_action, step, actions):
    mask = [True] + [False] * 4
    if step >= 718:
        return mask
    for j, item in enumerate(ITEMS):
        mask[j + 1] = (
            _sell_qty(base_action, item) > 0
            and _can_reinsert_from_schedule(actions, step, item)
        )
    return mask


def _margin_from_obs(obs):
    try:
        seat = 1 if int(getv(obs, 'player', 0) or 0) == 1 else 0
        farms = list(getv(obs, 'farms', []) or [])
        if len(farms) < 2:
            return 0.0
        own = float(getv(farms[seat], 'money', 0.0) or 0.0)
        opp = float(getv(farms[1 - seat], 'money', 0.0) or 0.0)
        return own - opp
    except Exception:
        return 0.0


def _mask_q_tensor(torch, q, masks):
    m = torch.tensor(masks, dtype=torch.bool, device=q.device)
    return q.masked_fill(~m, -1e9)


def rl_select_action(torch, model, data, feasible, epsilon):
    legal = [i for i, ok in enumerate(feasible) if ok]
    if len(legal) <= 1:
        return 0
    if random.random() < float(epsilon):
        return random.choice(legal)
    model.eval()
    with torch.no_grad():
        q = model(data).view(-1)
    return int(max(legal, key=lambda a: float(q[a].item())))


def _apply_training_residual(base_action, action_id, step, actions, add_back):
    action = copy.deepcopy(base_action)
    if action_id <= 0 or action_id > 4:
        return action
    item = ITEMS[action_id - 1]
    q = _sell_qty(action, item)
    if q <= 0 or not _can_reinsert_from_schedule(actions, step, item):
        return action
    move = max(1, int(round(q * RL_MAX_DELAY_FRACTION)))
    move = min(q, move)
    action = _remove_sell(action, item, move)
    nxt = add_back.setdefault(step + 1, {})
    nxt[item] = int(nxt.get(item, 0)) + int(move)
    return action


def _restore_training_due(action, step, add_back):
    due = dict(add_back.pop(step, {}) or {})
    for item, q in due.items():
        action = _add_sell(action, item, q)
    return action


class ResidualRLCollector:
    '''Collects semi-Markov residual transitions from a full Kaggriculture game.'''
    def __init__(self, torch, Data, model, base_path, epsilon):
        self.torch = torch
        self.Data = Data
        self.model = model
        self.epsilon = float(epsilon)
        tag = f'rl_v16_{random.randrange(10**9)}'
        self.module = _module_from_path(base_path, tag)
        self.base_agent = self.module.agent
        self.actions = self.module._ACTIONS
        self.add_back = {}
        self.pending = None
        self.transitions = []
        self.decisions = 0
        self.action_counts = [0] * RL_NUM_ACTIONS

    def __call__(self, obs, configuration=None):
        # kaggle_environments may call Python agents as agent(obs, configuration).
        # The RL collector only needs obs, but must accept the second argument.
        step = min(max(0, int(getv(obs, 'step', 0) or 0)), len(self.actions) - 1)
        if step == 0:
            self.add_back.clear()
            self.pending = None

        base_action = self.base_agent(obs)
        feasible = rl_feasible_mask(base_action, step, self.actions)
        action = copy.deepcopy(base_action)

        if any(feasible[1:]):
            state = rl_data_from_obs(self.torch, self.Data, obs, base_action, self.actions)
            margin = _margin_from_obs(obs)

            if self.pending is not None:
                reward = (margin - self.pending['margin']) / RL_REWARD_SCALE
                self.transitions.append({
                    'state': self.pending['state'],
                    'action': self.pending['action'],
                    'reward': float(max(-10.0, min(10.0, reward))),
                    'next_state': state,
                    'next_mask': list(feasible),
                    'done': False,
                })

            action_id = rl_select_action(
                self.torch, self.model, state, feasible, self.epsilon
            )
            self.action_counts[action_id] += 1
            self.decisions += 1
            self.pending = {
                'state': state,
                'action': int(action_id),
                'margin': float(margin),
            }
            action = _apply_training_residual(
                action, action_id, step, self.actions, self.add_back
            )

        # Reinsert delayed t-1 quantities after deciding on fresh V16 sales.
        action = _restore_training_due(action, step, self.add_back)
        return action

    def finalize(self, final_margin):
        if self.pending is None:
            return
        reward = (float(final_margin) - self.pending['margin']) / RL_REWARD_SCALE
        if final_margin > 0:
            reward += RL_WIN_BONUS
        elif final_margin < 0:
            reward -= RL_WIN_BONUS
        self.transitions.append({
            'state': self.pending['state'],
            'action': self.pending['action'],
            'reward': float(max(-10.0, min(10.0, reward))),
            'next_state': None,
            'next_mask': [True, False, False, False, False],
            'done': True,
        })
        self.pending = None


def _append_replay(replay, transitions):
    replay.extend(transitions)
    if len(replay) > RL_REPLAY_CAPACITY:
        del replay[:len(replay) - RL_REPLAY_CAPACITY]


def optimize_double_dqn(torch, Batch, online, target, optimizer, replay, updates):
    if len(replay) < RL_BATCH_SIZE:
        return None
    online.train()
    losses = []

    for _ in range(int(updates)):
        sample = random.sample(replay, RL_BATCH_SIZE)
        states = Batch.from_data_list([t['state'] for t in sample])
        actions = torch.tensor([t['action'] for t in sample], dtype=torch.long)
        rewards = torch.tensor([t['reward'] for t in sample], dtype=torch.float32)

        q = online(states)
        qa = q.gather(1, actions[:, None]).squeeze(1)
        targets = rewards.clone()

        nonterminal_idx = [
            i for i, t in enumerate(sample)
            if not t['done'] and t['next_state'] is not None
        ]

        if nonterminal_idx:
            next_states = Batch.from_data_list([
                sample[i]['next_state'] for i in nonterminal_idx
            ])
            next_masks = [sample[i]['next_mask'] for i in nonterminal_idx]
            with torch.no_grad():
                # Double DQN: online selects; target network evaluates.
                q_online_next = _mask_q_tensor(torch, online(next_states), next_masks)
                best_next = q_online_next.argmax(dim=1)
                q_target_next = target(next_states)
                chosen = q_target_next.gather(1, best_next[:, None]).squeeze(1)
            idx_tensor = torch.tensor(nonterminal_idx, dtype=torch.long)
            targets[idx_tensor] += RL_GAMMA * chosen

        loss = torch.nn.functional.smooth_l1_loss(qa, targets)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(online.parameters(), 2.0)
        optimizer.step()
        losses.append(float(loss.item()))

        with torch.no_grad():
            for tp, op in zip(target.parameters(), online.parameters()):
                tp.data.mul_(1.0 - RL_TAU).add_(op.data, alpha=RL_TAU)

    return sum(losses) / max(1, len(losses))


def _training_opponent(i):
    return ('v16', 'starter', 'random')[i % 3]


def train_graph_double_dqn(torch, Data, Batch, GCNConv, make):
    banner('RL 1/5 — Train Graph Double-DQN residual policy')
    random.seed(SEED + 700)
    torch.manual_seed(SEED + 700)

    online = make_rl_qnetwork(torch, GCNConv)
    target = make_rl_qnetwork(torch, GCNConv)
    target.load_state_dict(online.state_dict())
    target.eval()

    optimizer = torch.optim.AdamW(
        online.parameters(),
        lr=RL_LEARNING_RATE,
        weight_decay=RL_WEIGHT_DECAY,
    )
    replay = []
    training_log = []

    for episode in range(RL_TRAIN_GAMES):
        frac = episode / max(1, RL_TRAIN_GAMES - 1)
        epsilon = RL_EPS_START + frac * (RL_EPS_END - RL_EPS_START)
        seed = RL_TRAIN_SEED0 + 17 * episode
        seat = episode % 2
        opponent_kind = _training_opponent(episode)
        opponent = str(BASE_PATH) if opponent_kind == 'v16' else opponent_kind

        collector = ResidualRLCollector(torch, Data, online, BASE_PATH, epsilon)
        env = make(
            'kaggriculture',
            configuration={'episodeSteps': 720, 'seed': int(seed)},
            debug=True,
        )
        agents = [collector, opponent] if seat == 0 else [opponent, collector]
        env.run(agents)

        final = env.steps[-1]
        statuses = [str(s.status) for s in final]
        if statuses != ['DONE', 'DONE']:
            raise RuntimeError(f'RL train game seed={seed} failed: {statuses}')

        m0, m1 = money_pair(env)
        final_margin = (m0 - m1) if seat == 0 else (m1 - m0)
        collector.finalize(final_margin)
        _append_replay(replay, collector.transitions)

        loss = optimize_double_dqn(
            torch, Batch, online, target, optimizer,
            replay, RL_UPDATES_PER_GAME
        )
        training_log.append({
            'seed': seed,
            'seat': seat,
            'opponent': opponent_kind,
            'margin': final_margin,
            'decisions': collector.decisions,
            'actions': list(collector.action_counts),
            'loss': loss,
            'replay': len(replay),
        })

        counts = '/'.join(str(v) for v in collector.action_counts)
        loss_text = 'warmup' if loss is None else f'{loss:.5f}'
        print(
            f'[RL train {episode+1:02d}/{RL_TRAIN_GAMES}] '
            f'seed={seed} seat={seat} opp={opponent_kind:<7} '
            f'eps={epsilon:.3f} margin={final_margin:+.1f} '
            f'decisions={collector.decisions:3d} '
            f'actions[K/M/Mi/S/W]={counts} '
            f'replay={len(replay):4d} loss={loss_text}'
        )

    if len(replay) < RL_BATCH_SIZE:
        raise RuntimeError(f'Not enough RL transitions: {len(replay)}')

    final_loss = optimize_double_dqn(
        torch, Batch, online, target, optimizer,
        replay, max(80, RL_UPDATES_PER_GAME * 2)
    )
    print(
        f'[RL] final replay={len(replay)} '
        f'final Double-DQN loss={final_loss:.6f}'
    )
    return online, replay, training_log


def export_rl_weights(model):
    def arr(t):
        return t.detach().cpu().tolist()
    return {
        'feature_dim': FEATURE_DIM,
        'node_count': NODE_COUNT,
        'product_start': PRODUCT_START,
        'hidden': RL_HIDDEN,
        'head': RL_HEAD,
        'num_actions': RL_NUM_ACTIONS,
        'max_delay_fraction': RL_MAX_DELAY_FRACTION,
        'deploy_advantage': RL_DEPLOY_ADVANTAGE,
        'conv1_w': arr(model.conv1.lin.weight),
        'conv1_b': arr(model.conv1.bias),
        'conv2_w': arr(model.conv2.lin.weight),
        'conv2_b': arr(model.conv2.bias),
        'q1_w': arr(model.q1.weight),
        'q1_b': arr(model.q1.bias),
        'q2_w': arr(model.q2.weight),
        'q2_b': arr(model.q2.bias),
    }


def manual_rl_q(nodes, edges, weights):
    h1 = manual_gcn_layer(nodes, edges, weights['conv1_w'], weights['conv1_b'])
    h2 = manual_gcn_layer(h1, edges, weights['conv2_w'], weights['conv2_b'])
    hidden = int(weights['hidden'])
    own = [sum(h2[i][k] for i in range(100)) / 100.0 for k in range(hidden)]
    opp = [sum(h2[i][k] for i in range(100, 200)) / 100.0 for k in range(hidden)]
    products = []
    for j in range(4):
        products.extend(h2[PRODUCT_START + j])
    z = own + opp + products
    h = manual_matvec(weights['q1_w'], z, weights['q1_b'])
    h = [max(0.0, v) for v in h]
    return manual_matvec(weights['q2_w'], h, weights['q2_b'])


def verify_rl_export(torch, model, replay, weights):
    banner('RL 2/5 — Verify exported pure-Python GNN + Q-network')
    model.eval()
    max_diff = 0.0
    checks = min(12, len(replay))
    with torch.no_grad():
        for transition in random.sample(replay, checks):
            d = transition['state']
            pyg = model(d).view(-1).cpu().tolist()
            nodes = d.x.cpu().tolist()
            edges = list(zip(
                d.edge_index[0].cpu().tolist(),
                d.edge_index[1].cpu().tolist(),
            ))
            manual = manual_rl_q(nodes, edges, weights)
            diff = max(abs(float(a) - float(b)) for a, b in zip(pyg, manual))
            max_diff = max(max_diff, diff)
    print(f'[RL export check] max |PyG Q - pure Python Q| = {max_diff:.8f}')
    if max_diff > 2e-4:
        raise RuntimeError('Pure-Python RL export does not match PyG network.')
    print('[OK] GNN + Double-DQN export equivalence passed.')


def rl_residual_source(weights):
    payload = base64.b85encode(
        zlib.compress(
            json.dumps(weights, separators=(',', ':')).encode('utf-8'), 9
        )
    ).decode('ascii')
    return r'''
# ===== GRAPH DOUBLE-DQN RESIDUAL POLICY =====
# V16 remains the expert/base policy.
# Learned actions: KEEP_V16 / delay 25% MELON/MILK/STRAWBERRY/WOOL.
# GNN + Q weights embedded; no torch/PyG at match runtime.
import math as _rlmath

_RL_ITEMS = ('MELON', 'MILK', 'STRAWBERRY', 'WOOL')
_RL_BASE_PRICE = {'MELON': 250.0, 'MILK': 160.0, 'STRAWBERRY': 120.0, 'WOOL': 200.0}
_RL_SHOP_PRODUCTS = {
    'BAKERY': ('EGG', 'WHEAT'),
    'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),
    'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'),
    'YARN_STORE': ('WOOL',),
    'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'),
    'PET_CAFE': ('CARROT',),
    'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'),
    'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'),
}
_RL_FDIM = 24
_RL_NODES = 204
_RL_PSTART = 200
_RL_W = json.loads(zlib.decompress(base64.b85decode(__PAYLOAD__)).decode('utf-8'))
_RL_MAX_FRAC = float(_RL_W['max_delay_fraction'])
_RL_ADV = float(_RL_W['deploy_advantage'])
_RL_ADD_BACK = {0: {}, 1: {}}


def _rlclip(v, lo=-3.0, hi=3.0):
    return lo if v < lo else hi if v > hi else v


def _rlproduct(tile):
    if not isinstance(tile, dict):
        return None
    if tile.get('kind') == 'PLANT':
        crop = tile.get('crop')
        return crop if crop in ('MELON', 'STRAWBERRY') else None
    if tile.get('kind') in ('COOP', 'PASTURE'):
        animal = tile.get('animal')
        if animal == 'COW': return 'MILK'
        if animal == 'SHEEP': return 'WOOL'
    return None


def _rltown(obs, item, step):
    demand = 1 if item != 'FERTILIZER' and step % 24 == 0 else 0
    if step % 4 != 0:
        return demand
    town = _get(obs, 'town', {}) or {}
    for shop in list(_get(town, 'unlocked_shops', []) or []):
        products = _RL_SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += 2 if len(products) == 1 else 1
    return demand


def _rlsellq(action, item):
    total = 0
    for o in (action.get('market') or []):
        if len(o) >= 3 and o[0] == 'SELL' and o[1] == item:
            try: total += max(0, int(o[2]))
            except Exception: pass
    return total


def _rlgraph(obs, step, action):
    seat = 1 if int(_get(obs, 'player', 0) or 0) == 1 else 0
    farms = list(_get(obs, 'farms', []) or [])
    nodes = [[0.0] * _RL_FDIM for _ in range(_RL_NODES)]
    edges = set()
    if len(farms) < 2:
        return nodes, []
    own, opp = farms[seat], farms[1 - seat]
    day = float(_get(obs, 'day', step // 24) or 0)
    dayf = _rlclip(day / 30.0, 0.0, 1.0)

    def edge(a, b):
        if 0 <= a < _RL_NODES and 0 <= b < _RL_NODES and a != b:
            edges.add((a, b)); edges.add((b, a))

    def enc(farm, base, self_flag):
        tiles = list(_get(farm, 'tiles', []) or [])
        fr = _get(farm, 'farmer', [-999, -999]) or [-999, -999]
        try: farmer = (int(fr[0]), int(fr[1]))
        except Exception: farmer = (-999, -999)
        hc = {}
        for p in list(_get(farm, 'hands', []) or []):
            try:
                k = (int(p[0]), int(p[1])); hc[k] = hc.get(k, 0) + 1
            except Exception: pass
        h = len(tiles)
        w = len(tiles[0]) if h and isinstance(tiles[0], (list, tuple)) else 0
        for y in range(min(10, h)):
            for x in range(min(10, w)):
                idx = base + y * 10 + x
                f = nodes[idx]
                f[0 if self_flag else 1] = 1.0
                tile = tiles[y][x]
                if tile is None:
                    f[3] = 1.0
                elif tile == 'LOCKED':
                    f[4] = 1.0
                elif isinstance(tile, dict):
                    kind = tile.get('kind')
                    if kind == 'WEED':
                        f[5] = 1.0
                    elif kind == 'PLANT':
                        f[6] = 1.0
                        prod = _rlproduct(tile)
                        if prod in _RL_ITEMS: f[8 + _RL_ITEMS.index(prod)] = 1.0
                        f[12] = 0.0 if bool(tile.get('watered_today')) else 1.0
                        f[13] = 1.0 if int(tile.get('fertilized_until_day', -1) or -1) >= int(day) else 0.0
                        f[14] = _rlclip(float(tile.get('yield_units', 0) or 0) / 6.0, 0.0, 1.5)
                        planted = int(tile.get('planted_day', int(day)) or int(day))
                        f[15] = _rlclip((day - planted) / 16.0, 0.0, 2.0)
                    elif kind in ('COOP', 'PASTURE'):
                        f[7] = 1.0
                        prod = _rlproduct(tile)
                        if prod in _RL_ITEMS: f[8 + _RL_ITEMS.index(prod)] = 1.0
                        f[12] = 0.0 if bool(tile.get('fed_today')) else 1.0
                        f[13] = 1.0 if bool(tile.get('cared_today')) else 0.0
                        f[14] = _rlclip(float(tile.get('yield_units', 0) or 0) / 6.0, 0.0, 1.5)
                        placed = int(tile.get('placed_day', int(day)) or int(day))
                        f[15] = _rlclip((day - placed) / 16.0, 0.0, 2.0)
                f[16] = 1.0 if farmer == (x, y) else 0.0
                f[17] = _rlclip(float(hc.get((x, y), 0)) / 4.0, 0.0, 1.0)
                f[23] = dayf
                if x > 0: edge(idx, idx - 1)
                if y > 0: edge(idx, idx - 10)
                prod = _rlproduct(tile)
                if prod in _RL_ITEMS: edge(idx, _RL_PSTART + _RL_ITEMS.index(prod))

    enc(own, 0, True); enc(opp, 100, False)
    market = _get(obs, 'market', {}) or {}
    prices = _get(market, 'prices', {}) or {}
    inv = _get(market, 'inventory', {}) or {}
    private = _get(obs, 'private', {}) or {}
    shed = _get(private, 'shed', {}) or {}
    for j, item in enumerate(_RL_ITEMS):
        f = nodes[_RL_PSTART + j]
        f[2] = 1.0; f[8 + j] = 1.0
        bp = _RL_BASE_PRICE[item]
        f[18] = _rlclip(float(_get(prices, item, bp) or bp) / bp, 0.0, 4.0)
        ii = float(_get(inv, item, 10000) or 10000)
        f[19] = _rlclip((10000.0 - ii) / 1000.0, -3.0, 3.0)
        f[20] = _rlclip(float(_get(shed, item, 0) or 0) / 50.0, 0.0, 2.0)
        f[21] = _rlclip(float(_rltown(obs, item, step)) / 4.0, 0.0, 2.0)
        f[22] = _rlclip(float(_rlsellq(action, item)) / 20.0, 0.0, 2.0)
        f[23] = dayf
    for a in range(4):
        for b in range(a + 1, 4): edge(_RL_PSTART + a, _RL_PSTART + b)
    return nodes, sorted(edges)


def _rlmat(W, x, b):
    return [sum(float(w) * float(x[j]) for j, w in enumerate(row)) + float(b[i]) for i, row in enumerate(W)]


def _rllayer(h, edges, W, b):
    n = len(h); adj = [set([i]) for i in range(n)]
    for a, c in edges:
        if 0 <= a < n and 0 <= c < n: adj[c].add(a)
    deg = [len(adj[i]) for i in range(n)]
    out = []; dim = len(h[0])
    for i in range(n):
        agg = [0.0] * dim; di = float(deg[i])
        for j in adj[i]:
            norm = 1.0 / _rlmath.sqrt(di * float(deg[j])); hj = h[j]
            for k in range(dim): agg[k] += norm * float(hj[k])
        v = _rlmat(W, agg, b); out.append([z if z > 0.0 else 0.0 for z in v])
    return out


def _rlq(obs, step, action):
    nodes, edges = _rlgraph(obs, step, action)
    if not edges: return [0.0] * 5
    w = _RL_W
    h1 = _rllayer(nodes, edges, w['conv1_w'], w['conv1_b'])
    h2 = _rllayer(h1, edges, w['conv2_w'], w['conv2_b'])
    hidden = int(w['hidden'])
    own = [sum(h2[i][k] for i in range(100)) / 100.0 for k in range(hidden)]
    opp = [sum(h2[i][k] for i in range(100, 200)) / 100.0 for k in range(hidden)]
    products = []
    for j in range(4): products.extend(h2[_RL_PSTART + j])
    z = own + opp + products
    hh = _rlmat(w['q1_w'], z, w['q1_b']); hh = [v if v > 0.0 else 0.0 for v in hh]
    return _rlmat(w['q2_w'], hh, w['q2_b'])


def _rlremove_sell(action, item, q):
    action = _copy_action(action); remain = max(0, int(q)); market = []
    for raw in (action.get('market') or []):
        order = list(raw)
        if remain > 0 and len(order) >= 3 and order[0] == 'SELL' and order[1] == item:
            n = max(0, int(order[2])); take = min(n, remain); n -= take; remain -= take
            if n <= 0: continue
            order[2] = n
        market.append(order)
    action['market'] = market[:10]; return action


def _rladd_sell(action, item, q):
    action = _copy_action(action); q = max(0, int(q)); market = [list(o) for o in (action.get('market') or [])]
    if q <= 0: return action
    for o in market:
        if len(o) >= 3 and o[0] == 'SELL' and o[1] == item:
            o[2] = max(0, int(o[2])) + q; action['market'] = market[:10]; return action
    if len(market) < 10: market.append(['SELL', item, q])
    action['market'] = market[:10]; return action


def _rlcan_reinsert(step, item):
    future = step + 1
    if not 0 <= future < len(_ACTIONS): return False
    market = list(_ACTIONS[future].get('market') or [])
    if any(len(o) >= 3 and o[0] == 'SELL' and o[1] == item for o in market): return True
    return len(market) < 10


def _rlmask(action, step):
    mask = [True, False, False, False, False]
    if step >= 718: return mask
    for j, item in enumerate(_RL_ITEMS):
        mask[j + 1] = _rlsellq(action, item) > 0 and _rlcan_reinsert(step, item)
    return mask


def _rlreset(step, seat):
    if step == 0: _RL_ADD_BACK[seat].clear()
    for s in list(_RL_ADD_BACK[seat]):
        if int(s) < step: _RL_ADD_BACK[seat].pop(s, None)


def _rlrestore(action, step, seat):
    due = dict(_RL_ADD_BACK[seat].pop(step, {}) or {})
    for item, q in due.items(): action = _rladd_sell(action, item, q)
    return action


def _rlapply(action, choice, step, seat):
    if choice <= 0 or choice > 4: return action
    item = _RL_ITEMS[choice - 1]
    q = _rlsellq(action, item)
    if q <= 0 or not _rlcan_reinsert(step, item): return action
    move = max(1, int(round(q * _RL_MAX_FRAC))); move = min(q, move)
    action = _rlremove_sell(action, item, move)
    nxt = _RL_ADD_BACK[seat].setdefault(step + 1, {}); nxt[item] = nxt.get(item, 0) + move
    return action


def agent(obs):
    try:
        step = min(max(0, int(_get(obs, 'step', 0) or 0)), len(_ACTIONS) - 1)
        seat = _seat(obs); _rlreset(step, seat)
        base_action = _v16_agent(obs); action = base_action
        mask = _rlmask(base_action, step)
        if any(mask[1:]):
            q = _rlq(obs, step, base_action)
            legal = [i for i, ok in enumerate(mask) if ok]
            best = max(legal, key=lambda i: float(q[i]))
            if best != 0 and float(q[best]) >= float(q[0]) + _RL_ADV:
                action = _rlapply(base_action, best, step, seat)
        action = _rlrestore(action, step, seat)
        return _align_hands(action, obs)
    except Exception:
        return _v16_agent(obs)
'''.replace('__PAYLOAD__', repr(payload))


def build_rl_candidate_source(base_source, weights):
    if 'def agent(obs):' not in base_source:
        raise RuntimeError('Could not locate V16 public agent function.')
    core = base_source.replace('def agent(obs):', 'def _v16_agent(obs):', 1)
    return core + '\n\n' + rl_residual_source(weights) + '\n'


def evaluate_rl_candidate(make, candidate_path, base_path):
    banner('RL 3/5 — Unseen-seed V16+GNN+Double-DQN vs original V16')
    paired = []; game_margins = []
    for seed in EVAL_SEEDS:
        env_a = run_game(make, str(candidate_path), str(base_path), seed)
        m0, m1 = money_pair(env_a); margin_a = m0 - m1
        env_b = run_game(make, str(base_path), str(candidate_path), seed)
        m0b, m1b = money_pair(env_b); margin_b = m1b - m0b
        pair = margin_a + margin_b
        paired.append(pair); game_margins.extend([margin_a, margin_b])
        print(f'seed={seed}: RL-seat0={margin_a:+.1f}, RL-seat1={margin_b:+.1f}, paired={pair:+.1f}')
    mean_pair = sum(paired) / len(paired)
    positives = sum(v > 0 for v in paired)
    mean_game = sum(game_margins) / len(game_margins)
    print(f'[RL benchmark] paired mean={mean_pair:+.1f}; positive pairs={positives}/{len(paired)}; game mean={mean_game:+.1f}')
    passed = mean_pair > 0.0 and positives >= math.ceil(len(paired) / 2)
    print('[RL BENCHMARK]', 'PASS — residual RL beats V16 on this panel' if passed else 'FAIL — keep RL archive; do not replace with V16')
    return passed


def package_rl_candidate(make, candidate_source):
    banner('RL 4/5 — Package exact V16 + GNN + Double-DQN main.py')
    required = [
        'def _v16_agent(', '_RL_W', 'def _rlgraph(', 'def _rlq(',
        'def _rlmask(', 'def agent(obs):', 'GRAPH DOUBLE-DQN RESIDUAL POLICY'
    ]
    missing = [m for m in required if m not in candidate_source]
    if missing:
        raise RuntimeError('Refusing to package: missing RL markers ' + repr(missing))
    MAIN_PATH.write_text(candidate_source, encoding='utf-8', newline='\n')
    compile(MAIN_PATH.read_bytes(), str(MAIN_PATH), 'exec')
    env = run_game(make, str(MAIN_PATH), 'random', 451781128)
    m0, m1 = money_pair(env)
    print(f'[RL smoke] main.py vs random: money {m0:.1f} vs {m1:.1f}; margin={m0-m1:+.1f}')
    with tarfile.open(ARCHIVE_PATH, 'w:gz') as tar:
        tar.add(MAIN_PATH, arcname='main.py')
    with tarfile.open(ARCHIVE_PATH, 'r:gz') as tar:
        names = tar.getnames()
    if names != ['main.py']:
        raise RuntimeError(f'Bad submission archive root: {names}')
    print('[PROOF] Final main.py contains V16 + graph + GNN + Double-DQN.')
    print(f'[PROOF] main.py={MAIN_PATH.stat().st_size/1024:.1f} KiB; archive={ARCHIVE_PATH.stat().st_size/1024:.1f} KiB')


def submit_rl_if_allowed(benchmark_passed):
    banner('RL 5/5 — Kaggle submission decision')
    if not benchmark_passed and not FORCE_RL_SUBMIT:
        print('[SAFE STOP] RL candidate was NOT replaced by V16, but automatic Kaggle upload is disabled because the unseen-seed benchmark did not pass.')
        print('The real V16+GNN+Double-DQN archive is ready at:')
        print(ARCHIVE_PATH)
        print('If you intentionally want to leaderboard-test it, set FORCE_RL_SUBMIT=True and rerun, or submit the archive manually.')
        return
    if benchmark_passed:
        print('[OK] Benchmark passed: upload is allowed.')
    else:
        print('[FORCED] Benchmark failed but FORCE_RL_SUBMIT=True.')
    submit()


def main():
    random.seed(SEED)
    banner('Kaggriculture — V16-RC5 + GNN + Double-DQN residual RL')
    base_source, _ = restore_base_agent()

    from kaggle_environments import make
    torch, Data, Batch, GCNConv = import_pyg_rl()

    model, replay, training_log = train_graph_double_dqn(
        torch, Data, Batch, GCNConv, make
    )

    weights = export_rl_weights(model)
    verify_rl_export(torch, model, replay, weights)

    candidate_source = build_rl_candidate_source(base_source, weights)
    if candidate_source == base_source:
        raise RuntimeError('Refusing to continue: RL candidate equals plain V16.')

    CANDIDATE_PATH.write_text(candidate_source, encoding='utf-8', newline='\n')
    compile(CANDIDATE_PATH.read_bytes(), str(CANDIDATE_PATH), 'exec')
    print(
        f'[OK] V16+GNN+Double-DQN candidate: {CANDIDATE_PATH} '
        f'({CANDIDATE_PATH.stat().st_size/1024:.1f} KiB)'
    )

    benchmark_passed = evaluate_rl_candidate(make, CANDIDATE_PATH, BASE_PATH)

    # Always package the RL agent. Never silently replace it with V16.
    package_rl_candidate(make, candidate_source)
    submit_rl_if_allowed(benchmark_passed)

    banner('DONE')
    print(f'Final RL agent: {MAIN_PATH}')
    print(f'Kaggle archive: {ARCHIVE_PATH}')
    print('Architecture: V16-RC5 + 204-node graph + 2-layer GCN + Double-DQN.')
    print('Residual actions: KEEP_V16 / delay 25% of MELON/MILK/STRAWBERRY/WOOL.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        banner('FAILED — full traceback')
        traceback.print_exc()
        raise
