from __future__ import annotations

import copy
import base64
import hashlib
import importlib
import json
import math
import os
import random
import shutil
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


@dataclass(frozen=True)
class Config:
    experiment_seed: int = 20260822
    start_step: int = 715
    max_candidates: int = 12
    mcts_simulations: int = 16
    c_puct: float = 1.25
    root_noise_fraction: float = 0.20
    root_dirichlet_alpha: float = 0.30
    expert_iterations: int = 3
    replay_rounds: int = 2
    epochs_per_iteration: int = 16
    batch_size: int = 64
    learning_rate: float = 3e-4
    margin_scale: float = 2_000.0
    margin_weight: float = 0.05
    value_loss_weight: float = 0.25
    candidate_class_loss_weight: float = 0.75
    candidate_margin_loss_weight: float = 0.50
    actionable_sample_weight: float = 3.0
    # Train and demo use disjoint seeds. A one-step oracle pre-filters both for at least one better candidate.
    train_seeds: tuple[int, ...] = (
        20260823002, 20260823007, 20260823010,
        20260823012, 20260823018, 20260823022,
    )
    demo_seeds: tuple[int, ...] = (20260823027, 20260823029, 20260823030)
    # Ordinary seeds are not positive-filtered. They are a guard diagnostic, not part of the demo metric.
    guard_seeds: tuple[int, ...] = (20260818201, 20260818202)
    dev_thresholds: tuple[float, ...] = (0.0, 0.002, 0.004, 0.006, 1e9)


CFG = Config()
assert CFG.mcts_simulations >= CFG.max_candidates
assert 0.0 <= CFG.margin_weight < 0.5
random.seed(CFG.experiment_seed)
np.random.seed(CFG.experiment_seed)
torch.manual_seed(CFG.experiment_seed)


def select_torch_device() -> torch.device:
    """Use CUDA only when this PyTorch binary contains code for the visible GPU."""
    if not torch.cuda.is_available():
        return torch.device("cpu")

    capability = torch.cuda.get_device_capability(0)
    device_arch = f"sm_{capability[0]}{capability[1]}"
    compiled_arches = set(torch.cuda.get_arch_list())
    print("gpu architecture:", device_arch)
    print("PyTorch CUDA architectures:", sorted(compiled_arches))

    # Runtime probing is authoritative: CUDA cubins/PTX may support a compatible architecture
    # even when get_arch_list() does not contain an exact string match.
    try:
        probe = torch.ones((16, 16), device="cuda")
        probe = torch.full_like(probe, CFG.actionable_sample_weight)
        probe = probe @ probe
        torch.cuda.synchronize()
        del probe
    except Exception as error:
        print(
            f"WARNING: CUDA self-test failed ({error}); falling back to CPU. "
            "On Kaggle, select T4 x2 instead of P100."
        )
        return torch.device("cpu")
    return torch.device("cuda")


DEVICE = select_torch_device()
if DEVICE.type == "cuda":
    torch.cuda.manual_seed_all(CFG.experiment_seed)
    torch.set_float32_matmul_precision("high")
print("torch:", torch.__version__)
print("device:", DEVICE)
if DEVICE.type == "cuda":
    print("gpu:", torch.cuda.get_device_name(0))


# Generated, version-pinned runtime bundle. The cell is hidden to keep the tutorial readable.
EMBEDDED_ASSETS = {
    'kaito_v27_main.py': (
        'c-pnRXSbqC6Da(Beua+Vf{yb5=3_*}EGTAYjR**eA{iCaZ@(CDyJzNvyWaKg4{o3<byam$SGD-{>(?EU^l+B0^RgM)@+RZiii;()'
        '<vluY@TNylbWf96E_IQ!B-7IQ?_a)@6m#V<c*Zn5mce@znfGwYiocQY2%;HLWXblZ7AuLIM^`M9cYr0HGx>#w5lmk9m@D2>t5bOF'
        'i=y(fC@(!M&)s<51{TUzlo^LqUr{4b$fN3_qJQ^LmTZa+h`{p;mf<#zd|O784UZ&l#T#i;`ND9fqDLf!V<gWA$IA|k%80s$kry6C'
        'U-0^k)m@?pe-I7xcH6^SEsr57&SY5IqX>e?iH!8c;mYwIajQBsJ*s3mqlzUj96nEFIpXbQ&%zNxUVQhEs_Ll0c`7cPPtmkJqN5zy'
        'QP1N0m#<&HesL%%y6IsVgHOcVJ5Et;_j+w8vU|N{%$0k6ltlK+moIb+ucFw5MzMaKBzm6Q9pSsAFbe~?!F*rvoU&CNs~Nz9%Xc;v'
        'zdc;=z!#76_xSujTtwew$^7IZOU=c3Hmd_Za0*>g1dFp~xIgXfk5vR}nK6bQ_Im3`q(N(hPdSnr-VoPk3fL4g)M2-Pix|c%;7efY'
        'o%Bu}X&XG9QnGfULtg&>JXi(A{M^{-TYBH*Fn_?g&0Wt#atSxLi4~NM;&34wtt*pe+dn27vwmX0HLM0Ta|~2J%>$E~ANOrxYgxFQ'
        '3#XFFi}`4Km}5;l-VvLcapK9w=E-UTB(A$fjjzvV39av6timm{rdRTn_N6247m-$@KQE?6cp+4-vtV~Mi3ug#TFt!k2F7oLT%uW1'
        'R`%?;=niwMm>Mk9R%B@rT$53MY7)G%>B4UNWR;C7%7w<F(LDe%>9aA`>PDqL@bkPm$!#M~sJhj)S}lSI=(@K`1f=q6if+Uq!1MWl'
        'mQHN?hb9Hk%s4h}%W6Ll4v)wzEwoSPbn+0ZRTF1|4P;e4%SRcdlboIFp)Sb{(MZ4A#~LwaLR7uoCo6E~oi#efEW)>;-Z(bv0<m^%'
        'dtT7zY5`?ur{=80x?&+qrCSTtR?0$GG;>BogGIW9b?Is~9FPnk2S`{IIyAjn^_+;|=MFO%ou`Xc25qkL18SvNi_x&u^rvFNWp>6h'
        'mmN3~gNuz|ouh;wg2cSdiceOdDLpb9>&0qbPVNh+moFlj@cBd!E*6cYlF1X;MCY|?5rKq6V^@j_`Tefys|9B}S6Cse<yt5(5lV8^'
        'EE-a5$DKEp+L(uN$STjJpeBc}oy}1Jc-qCOE~)ZzWDb_s{t%vC*XQ&^0IK9VF`X`|G+P+XPm=<fJD=wM%BHeHRt+2O?KMan3Xq-L'
        '`0P9bCl<SKex9pu+QK0;iBY9wXAt3<UUieJZ;gHJ$*Ne%Cy2qC!wnFMkQ$JYhZRSYz1=u^jpGwQPx^`AferAROOY$O0v5#ZJT6k%'
        'O1jc$_oC^(73iGiRN-`<)8;WslQ;^p#aPqeu>n%1J6)=qW3M1u9Zj0iv0gmyOJ%*Bh0+KSa)$QidV^WhbU2xqPU^Er$K?}~)q*zV'
        '=~`@^cAqJYXn_jFz3t3dO7%`6PK{dYRWnVrxK61yuP%UX-`5T(4bn^p!F@$s&`rf^Tp@*?ACIX*L7Wk}{8-&>8-wxa;@{4V7}CgE'
        'FakI0hDnFTMd-<Dtu>W$5zw#{lP!$FEAGkwUKd%uyj;ar3?MhU?fIgtgtmU)GJk;@O<+?#A(L6r9^usju^bh_^;m4er>&3Q%DT}E'
        'D<N;j9&I`+IGht|W-oY6@1=9azVwLNQRTsM!w!v}tdapdT(rCA+^FB{9<Jr__2eV37nP|bt~GWLIQq0Ur<W&_bUSF7VF8iw)B)Pp'
        '2Q&wT&HUmpGP>HnS&`VVRyl<>9K6ZC=5fx36PAx#pkx$pmXT^S56zNV-GYoglyU4P%J`lTkC$_5EX2b5yqVkf5*MaFiOsJQIC;&S'
        ';BlPW6U%&&BRlz}1jzfgl3pWVVjp6bD;3GhPgcFoY6pf|S((gi=xpwIilJE>DUML<7_+Lh(80N2Y&r;aJDRswCH4|e(wiZe<Y@E='
        '5=$1CT^Fv{_&$s*8$G(QHj~FZD3wN?p?qqd7Wp{TM3)+(Y}gfJmdao$-|Un1W_Q@Q=5&9--)eX#alBUGmp=5Es!moclkC>XBfkJ='
        'l~|2KxKlRN+>bRkCg<P<o6fn6JDf~_({Mo7+GCpRQHd3CRkU<zWe=8ZYUP_shgfjZKn0GfiK$v|7>c46vdRLN79Vde&s$9Oatm>g'
        '2<OLWH&*t}2F#!|0Y_-NE;>2cYYT>}FHls)P_BT7XOTuE7l<BJrajUweLdX`>hm$G6G1sQUorJ?bA7g`Jl?QaJ+kWVPBzy|2c&A2'
        'Uqxo=#x)ek`4T+{Lfl!D(mS(<wtc}RVs^1kp|5mzc{CSYNJg)V#0x<Z%8k;xPsfO!wwAcP-A){hSf8m9;a#7q&YUbUJ9p_qZwnN>'
        '#Th&TtO{llG36YlE8dLD=fH7clO#$#XYZ9oFirJh74-^plj&im^@+Jp_S#C0V}KJ{nA+AHJHafMx-QsY$STB_cBf2DNH7CaMKi0V'
        'YonFO(RC`e0KqLZ_LIj>Oo~2PNytRErmI0gMQ)zlBho$}8;_iP*;vwCjwbU&4&(i@-pNP%tE4yTmwT&;+B)^KgPng8K7kB1E7Yq|'
        'r8t-6seq2-?j%O}d?PrzP8nTaR7cxdd?c(?$-GW;mmWNm3VVvkN=f)^)z2tSZtY!uy3DIonOzx414~`FJ%aZevuum)F8nOQ6S*U8'
        '1S@bG&KMH3Cyv=L=0>}=xlLY`Kw_2Lb*gn6#k};DW7Ef42|6B+wnz%|Y0^LByXjfJx*Up;;w0SUTuHOR_2^Qcoi{;x?Cthgb~fBq'
        'waqRQ4GhxlG#3Ws=op;U_iLjtnDbal?1f+vGstO`nQkU}G$07$?%a<kE2DwUPAb5SuGQMsPvIp~*_D+jm3*@5>S->tRYtvH+!_I?'
        'Lx2JI2Ue>@#AZ>ev9)RK(2Nu8b{q{jTjG?Y)OX|J_H<okw!&msDeP)7<kXlPdx7?>K8)o$<i)p-!R7j;)9{ygbaEV&o~)vAvDHb%'
        'VI9X0s*NzMk}hqcf?4aq>-}`Qq>5w?R~g(gE0%-+R6aPDLA$?VGGzc!+sks))eoaGkld)28*x8TI?+}d55<y@7VoxWXD$cYDpbIP'
        'db&1DE9sHVW7nxq%`P)7(#)1rb^xJz_Q+Qdqf&-Pz0?MPYL$aad(#ZVPSp43R}=sI7)s7#gWQ2iO$x)bH#NUTYCh~bYGeC;gv5&D'
        '&{-Ykc}9zAr>wRGReZ1!+4gn@!m83WwoGn$U0)AMc)i;QL%*1S;C7n_pR5*0NRBSX_!`1=I0$B!6T7Rl#(tX%2nIrE>3ubRPV+1<'
        '=|iK6&$0r+Y`)0gnWW-M8yK|?os?V}SE(t@#AnJzvN?TK#Y5;`Y9eL(igo!;SZ?5_DUEcZ-H7ZJge91kUXd`aq5?4<oa#FyLC6#|'
        '2{u**UsflKlR7~I@f{P(_64)va<rxlupqKug?iAiRm=|3xu{jEUYA$Z*&T0v$-PSxTXK`x^4J<3i;OUDkN9IrMMM*+&HV@K&|g)M'
        '!aTUk4i-hqJY`wA90;#krS!5!DviA=uEIXL+s<~^#ift%2U6F(39T*i+!c~SbZvS4)QGd6toluPR37D4!CGaq$*z#XA?^n^OF@~Z'
        'VCE3ol;)!lfgjFOG|h>XPHVZe$ohq(F40o01&y#!aWP(TVy-d04y(nYdZ>iCX{%;LPb!6b0R<v<3wIOU!49eY6dQ&iiiuGAr8d}3'
        '#*JE81e_`WPgUzuY?X))Gl8^RTv6#pKq&}4do!6)%to#|9_i|*PmO!2k%6_5-grpwL4zy?Ix&*n8%a>0D!XaBl8zTRw%CZ54uSnC'
        'lx=4RtJ5@GIS(>2a5*;0!-Q1V#ZA@-k(t_LKx)Hm)g^zzXg+zaVxWm8dH}BFL<w3hBl;{U%3WmG>KE+nI@+!I1f0lr3PUe;;6$%~'
        'NVKw*(RvE4M<p+)3|obOC03QfF;yQ$_q#)|u-rpQwCLNs0@aAOLLh9;iDo&%Fk@@S`}u8#3h$NjhH>J~rcs|~TS>$l*yt3|pQfpK'
        'P5?IBO~4;)qv2XIRcUsPtf*xRLJ@&il~XNEWbHt+ezjj))cP)Q92-<B#tHCx9>>!`3e>8F!%^MRQ=RvzUMLAKQ>EZ^&`DoxbT_FI'
        '{LntEMHO?2n1NjNSfW?-V2#8RT=|*|n3%6sIfiTgJxZwMzU1|;#Ts78kb5bUE=W-mr$KceEo4L9Elam!=*YL*!0j#`ECrC%da!+&'
        '6A-pof7dB3utB%oO*NV5fNE(=8Yb37??zq?Lh~BSwj#0=uIICLqEYb=GkY^La|++W@vwzr(P~XsNZYs~!9=2g7p9rhD1(^U6M)r%'
        '<T*#7ZV{qR#Xhzw9Fu^)9bM>pG7|}Vqo7X?rNZ-4iq0lhQE8=XR==UnV#Rz>FO*o?FY3anzpn#@eVu%HVH^<FkO|F{vwdm@uJR^z'
        'h-V<!Amna|o-rZ8cbxd5=%pMQz}tYajV7r6CI~_~0$u50m(0)v`bmHrAL}?*IyIJ55|O56^4t%kkYX)%_Ty$DkB56Wm(6;QMg|W8'
        '{Q?s8D@BZ7XkJY^hDxbUDA~w|u(lDG8#^ngX+B^mid|sr4X<$AjhG=Z6&hmHA%b_ZbOb6cL;L)xp;SP$P1y-8?XPW8oYh_f`x6q~'
        'd41D1E=#k-#MfYVOK(pdS?x1h2;%ufqAQsig!SA>=mDY>07e6}5d)PeyBcMohJuWI<rt8dO%unaIp-$(o_*FELtzN`PKWV!UV>Wf'
        'X1LHu`qz8b(lSz5WOn|8%#HlPS*1{IE)%<QBbXX9+G;l<o~&l@+$!g`(4dq~qe6en_O{(!5}Pm`(&%MEUAWTsodCWR@wK9rxi4lw'
        'LBI}YW{HYuUOQSYF4yQpF-)b9S~(tUl@<&!+iZ`KSfQc7?tECJ*&Fn1usg&;(0**kQaj(U#rRq=AC}V=(a1<>wEW663$#U&EtlaV'
        ');SIFw%O;xnXOU4gDbIUCnTCK4<dnUS;q`#1L93y#o3F693SFfEH$M0NpFty0z)y-I#kJ3gYWFc06C1e%S@!^_qMLXS-!jLi7{G8'
        'lW9TlzSed-(dc@sxsYAhZ_k0)d=~JExs6SQe8Jh&Rzon0n|q6xF6LvEDN<<-dbJKl`C_9H&&P-fU-v_m;#v*%+UG*3gN%fFYaLz-'
        'v2JbRoyA+Joj(S&Qf*X;CV(i^<`S_^3JS#=zU-9t*L^W-Jix&m1nw{0bvoH-ALfbJL7erUtcX0WCY-onAl*bM!5;}gIePocQ_#L{'
        'I0Eu@qy0i95Q?C$s{cR$I+obxidQy~lCQnid~PjQNPiix@^P`>iCQg_XQL!~0HN3b$C6!&on-6TP><<oXDD>VNaMPxp4oaL5z4OX'
        'GUA`AvOO&Z{B2OUwi*Yw+k&0EOF@lUXjwI4DMYI!HkUD*@sGOw9h}L=g<*E$J6+UtsX(^LYNe&2em_<Spkq9j#)3nklvwX_2|w1X'
        'ry}Eqy7yPL?4rWXGm~x-*I(s(vvDNtU5ah?d;>8qRe;6G@R|q~1Grd;_L*V0Z1;EmZd%@3x^gCB933@_;IfxFYD-EOIaNclR|Qj?'
        '*JyzW|H2wo7n8+0A3x+*qfQBrEpqPWjuDuPc{J*i;IW?~y_P(U2%BuQ6zol;<gl2r7S5th^nK;S;0l#;P$knC4*F1-gYESoWb@T6'
        'ySO5DT?mwh6*ExYjB-lUD4von^|Tx}O<wW24G5T;pGj#vK==Ze8H-6@pg!qEb8tC&?Me-JyU&G<>mtyuQWt2Ko5zTxmm--mwWytV'
        'pBYavJ(Eso_$HkQT=a^9Vr<OYU8FC$?w+B%L?>%PPga(l$#}i(QXtgO;_F)bn3vby)BYlLh>I>ydP?EarMuMuEc9KS??#7uV*_-0'
        'j*)zGXLs!l*;}-;kH7$0M2_SkgJDhowj+}i5{st^8Z7yCxU|{?rke<U+@`p6N@`z(T>?C&YV|-7VC^(rEwjN9W-m&yykWZ~Dk(*?'
        '__m=b(;||3d2y;)jSbc|Jtc^;H+;0>K+fPr#yd%*N*&s$hQrbo<+_7@bGt`R464D*P;Z^3!@6!;u^4_?F0gG*&XqDHz8JoquK9)t'
        'km(wVoJ*jUZ4KvcNDS7dzTTY15%`+)O~X_^gbxnaqOQ5JT&l^oZO_udrdk{124u8{cUnib#O_8bRY)D1FxhUmeE4L#K`<xvn>D3u'
        '>lI(;ieF=4ahHX#<~f(#5y6bG7>(-?+raY|COwX8=Ae2gsH+z8s&zYb4^i{4{c*NQ3&C>$m<^dI3Qs2WR2ST-G8Af?w4;;WrC7cM'
        '@tn7!!|P&^-XB-zA++?tVCsVM)p#<`D%G}rmD*ucfyYSK^yez4&S+y2R~XdC7B+R$8_ca=HO{nQX=lAIoCZ{Xf~9Lw(95Q%>_pOY'
        'OE8)4bp#)$Nl>ZPj&2~LXD3MwBgAX42riu2)}twB_b7=fo>J=^mge^HIm&1Dg*>=|=FJ0$AM^2!Yke-J()y_!&czz7Ij$}h0a~p0'
        '+%VN(w0@<~56vUP@_tz8!M+}qO=uH+JHz&yT}KZx{88;m63rbNk!tx8%_q(C<*W`);39~x?KCk9Y^wEb(6wVKIOh|iVS5n{9|5dS'
        '^+LkgG^hbGkYeIa6Z*73R)Xq^-5w{Hy_ZUAq2kZVNQ6eO{3~0x=3cQO^OfBSI@oq;9%uoR>bi<u)Mi_b+xWJ!8|9dE+-`;$f2bl^'
        'fly&$aa<_aI8O>`J_^B?{i+i!x0+)Wi~?P~>;<;vgQ+&Ircd)NGep@nKc;C3A*7qLHrjPch)t)&lq_v{T`n^lO|f!7W!a4TN{DyE'
        '%v(Vu2`782#(|jZ7`xUx?m4_T93qu@g8SHvqKTQ-8jVBCbd%zyoVq(OsWGfJQPF1Dxm-$Y7TzGh4Vv_tUR_~kXQQF&aue#xzzL65'
        '6J&3S*SlfOUM`VI6i@MZwRIs$){3G4+)N%O6azn5@nfz-mNLpJBN^esxzDF8ve~MsnPG#S_t0QRYiikju#Ssx5+TtVmRV{u<cc2P'
        'XlPze)znQT0P8**Y$ULNoEukrO?hg>fs?f_OPA4f)UPpaM&=T=Q?}WNj6fh(;zw0)iSOxYdpPZ*=ggGamZ#fQ^BBZZ4OB4Ao=u3c'
        'jTa~91_>8a-7T0nc1x~`5^UM(j7&U>FZ|%8QZAztd@a%PwY-d#xs)t**Q5OzFOJ|*A>a46EJmFTmTYb=QngXp8!QE@Cvk}&-sM7!'
        'CAnCmLNs%5z5vWC-l3*ZBzz&=YAG>OH@qlk#N}=WUa?#(w>XgcrC!ycl;t<~1hO7F8ANjmR3NVPM={ySNsh&#QoN&$o9Y~_Pt%R`'
        '(1h&@UERs^b`5COmBLsi@ynuhTqWHe{ZT4u=iQ)EE@0|1T+A^IU12*hamJ%E(%tzvqgt@`M%d`~`y{uVU6a%(%Iq5}#DB5(MJA8?'
        'd(q>ne35%;nva4aT~>YhZo{k|`I8T5MZ==zT0=M*f`ADV6RYSQ``A6#(Xg@Rl$hQ+PIuk}03W+mXid-K`DuJpti&boRT%W!J8)NS'
        'CdhGC#B#%>%%dSoIL^FI$uA62uu&$^Jddp7G?6YwXU^WfU}WR4L{Y)s2#@k!eZ_{Tx!3aNgXz3BDW{hNu8;~^q@{keSQR?WC#(G8'
        '5>-X0(J{?^vD!LkvnC#`<jMmyy&Co7LJX}B@QAwElr11ro98P!B2JG<Fdm9u!)v>RqH<JEqcDLQEHsg2(TO76anJ1fc7E?d_nkYI'
        '+v<`lJ-7p=YVItT!(cR1wcE`eW;){UcOx&RVL85dVp@%A;^-af7M&9E;%M55ofi`$sSKAQ#tLT+r3UR9boPxe11Q%|<S&_B*-D#a'
        'zbUujq=tZ<3f?Yc!Mxj@AA(NR>UE-S7KwzU0RvR?wwXK#W;%<S-B@d~HcCXjBd0ogpoef8Lz<-##Dc5TQpf{xaUm(}>QFn5h2SPn'
        'MP6r8NV!_i6o3!`h@oEPXy-$1K-t6!mEojpISDtoXpi~HzP<xd*&7pbl|+1#V~miX3ga~vogXjD&N{L?$`m<2Cld)cpztMMJM_wa'
        'yJEpf-0Ph_Nw3fan>sY&Lw3EDl-^FQ^ON}@unQSnze1<jnL+>wTVC4>JV(6Fcxs_#i0m8=?RYSrWQ}&C#pw)i4#64yQ10!ALMup^'
        'jcV8I27SD80uLFsS4nxZ#~9Zs6S*d{^l#!e*-caXU2-xD$a`Xy$fA(YFSq*f?CcWvy&C*vFoYyr&S87B#e6;@uk^2G1z+=8uW(){'
        'nXZ39^v(0C<HgF{y3k53(PKge;Mj563N%wqWNY?2y*w?{!igAPs`f6~Ru>=pn}JlFwzK&(mJGf6;z@jtD?z(fv&~s6(DrNkz+QR_'
        '_IQcPdvS%~DJ&kZb`MmV7%odgCQa`SEH&^7QS>B);AkJEWYL_Ld%;rskU9ZQ2}aD~LPAgVj03*uE{g6(zb!FUJH;lid<<_+d77_J'
        'Gcw8IvzT>GpI+Td^eiLi83p*nXxJA{m;)l*$WGgG?0T5yD}hA6JQ#W5tQJp28zx_@ISJszGa;MlETtwGGZ)2t50;BjH4+%l<5sP@'
        '8qf3D#pZQlLj^-8F5Jt6(``Q?2NlidpPdv0f_Iu%$X=Y<CYN)FN9pTuR0l^~ISy&%uqpPaaO_mx4kzuJ-fB1O5?v{F^SmrYletid'
        'E$UT1zu>AssK3d&n+1Q~+w>Cc`eh!78`EBEmE7gJA>UEy@GA@2Cpx9hsR>2*9j(MBv0ltvPg<<l5xXm|mOR;seL9H`PsUc;!~?Ap'
        'oHBt`B~>2Umu_-1*|xZ819-B^EF^8Lwu?qsACDn0lQ6K+K0cey`UMET#sd}Y(oSef4~ZT5tRaT>q+ADAVy8LC<T`^=tUl`DsW_DE'
        'bgx|v-X9dU!0rw@<7#b|FpDVJ9)(o6Lkp*C0qZr!L{u1Fcd1%_ks9Q!fz=+a;MZvdecg(rbdH6aqoLZ*WS7=~R6uBHhzF~9&G*+?'
        'yjrUG@}*XNt92{b81L58=WA+n6jL3UmBdAN+BJ>-G#waLhV7bG*&ORm&9}Ui5Gpra4dj98ZuDs?lVZCOG#y>(Gjrps0$d+GB})YD'
        '537AiZONupK`HNGSuM}FRXS=0H&{dw$KwKY$c{)Ncd1F!3ZQ3+;=F_&Np0@ka0b^d>COGh*Lt-K<dz}!+3`lpH9IzSI#J7W_y~#v'
        '#GDCeYvv<}=mwbetsudRO#lsnr52d3`NGKX;A=+$b8-t!>dE?&*#|D8RADmYTQo>{wT$F)AWqfkp|Kjt3de-n3_P{jQee#cW4%DN'
        'dI78co)}mpo0r6zUj%}+!)dfgEBPr{F3r!|6V#29wdoc1j}G36Oa?3~>doTobbmqFrRwN}1}8+xEmW)iS>QUH2AXXupeIz4+T!6d'
        '(9+D%uGWlZLa18Ju@WeF<@Bmqj(9iSZcSABd#t+853^b(?&qn{A`dY+qhx}GO<CFJLEWj)UOo^gNR^PEn5p&sg0QR^Y&7_Ve{<P@'
        '-n3S&RQf{EA0-mhh#%H-yDkM9NnzbpLr0>VS)+q0QD9ZIw?{5PRC4U=swf)pS(I3auc-_u#io1l+U+ZJGYnx^xYh1~wlB`6dZ(cc'
        '6YU&V7<R|?bCJi|OKmx9onuOMytc=i#;lq1S+)7a%I|S79(a{%^#)eMlg&^sR~!SIpuMt=l+meW*nMkJ710DejPGWA-wXP$iGC`c'
        '^9oLkuTFXsXnF!E>l*L}@XOquWum*On9vK(#?>Z9V*)rQO5+A}s*T+3)cJVg@@t;XD4Y}LGZ}as>q6Z~<=EAm-eW#j9mS9JmLF|N'
        'bv0<IB3oTYrDJ5GVI6y%B&txkDy<n`k*&;~`Yg2YPIp$PAW9H@;7K`fKG$vcL@!4#{X-hhL6Q7g>*ets*sEa8$r9COyAv>mQi$It'
        'W%S}iL0eTB=45Yp0VP_ytzWPNUb=WsG<dGGy2yUI36A&4qc<E{M@&j5{n@B2xXMc|ip5f#s18kVlIV#2pq*U#NN6rEOl7p5Pbvq-'
        'sq$<mcdD7`f)W`lzpp1dNI9O4=Om-r43no|zi%}yJ0L~2-E~4Zy0ov$E7w(4Xiwmp^8=6UH+eMO4$i{rp`E0zgC-0j@I>iumocJS'
        '!$?`eyqtyCyunL;faEfbZk~*%YGiy)TGMFF$>t-pgQL-AIa4|)aX%-kRrgd;nXX4C_!_Jb4Rf}t&JNH@mUffECK}KCIvY8I_=P$q'
        '96JM@S#D%7n~Oq>-u6YeChaforDjfvQ-zY5ix;tCYa@hvwIrYQckTFSHOB&nhCOgQQ-zq{*o=KgZ+z6RcX><><*I}B+=yAcWKL#+'
        '4*G%hp?jshJTodx$w4IFy3CT(Z9VRbDf{i5JOD_B_4dhh9n3`sW{Bv`rey$)l&K1x$iKeAG6nWJEJucNW79^jfnmMzIsg!gPDxm2'
        'i#{`Ogsi6SKh~2quafkov{I!|fx1;`oUzY_TBp-N**8_?3S81tT{w5J%HuKKZ0xGF#Bc}@+o)~if}}u!WQc^)P2V(`-W`VC(&@=+'
        'KFeXv%z@k~{#Gcv2&UW9;8+dxN5L5$uGfMKAk)i%{gTm5wxk*93tYD6F?l@}SmPS9mjP2*WEHKjPfd;GzJf2)J+EIsj>Y_*&5b$a'
        'd<N2PS4c$1^J@ZukJ<GeZ}$@$4JQpLm}qW%^V(*5!aIwQ-2pFst#Ud{=}zUka0*Qz79ZopwItC^sIp{-0?W1<WhKDO>T20AsI17Y'
        's~IxnT_uuK%#BHxV{*^=?QPZDpf^$r55&r$NrLK+!|9}M#kw>s?dG+qU+}_IXR$8j_*_>PRK2WXuanG>u9Y`nm&xnlY&eYuPwCMv'
        'MN!5n36Q5+v;<pY6lvAP$@IYN_R(&RQ^U4mV|DKUFl=^LvDYa!p9#fz%)1a*jR94Pv7|I#Z0u{e-V;`nwcE~H<kY;s%r?NDHqrvu'
        'Rx2~wC7?nF>Rt-_Gdr7$mjhqUvy)j=nM4Mxy$AR8l0aqz#OD|Dc(fG~Hy5Ad={<kd0&{}hS7tc8PwWbWOw_}Nf#U9hG`|Mgn;=48'
        'bJ=)Yjho1NHx7_k(%YB;z=-tX!zw@{Mad`^;Fv(+3PG5|fl}OzY?8_5j{r0}`rx=XQ-T8Xt+~~=sjM%<RV7Lf50=@*_2hoDr^3ww'
        '{cbEh=#Q3~FTK%N4QuT$dW9jk13JMn#}Yef!HXO+s$$7#fmX|z<xXzrOZ~;E$)*5cIE=2ev{>#JcR;S)X)7%YO7dE5g@o~GcpBZf'
        '3XIpWV8YjphRU_WW(0Of9u&4w%!uV<OkdK?EV|wK;^KCu$H(FP2J=RC$e103b{a@bZ6lRB6SCQb3eVyW`~rgCpI<NiYMDYL^%Vra'
        '&=g)mTPT6yZ{Jk?<-4n2=nhqP04gn#q?}>+3th(BC{d=-R;PwKPoVEe{0rSisV3g1J1B*=Z)8q)zF$W*9PNMo%L5?sZyp$O{=Ru)'
        'w~w!erkh{CIoK)ZMpBmdYXtoEz{60ABJYUNH^eyf4*O0d=_2;YHrgj|hzaP0h}=0!qRcb;9X$4qn{aV^eF`0waEhAT@L}YG0Q_0x'
        '<U2L^gFqW^k;G%RAGlHIcd4Dr=m#2Jt=^E{aiYlY0{^C@cD>cSOZqld82O}^#NS9dBFWZWQ0RS<@jnatVpzece!W$n;?$ij^e-BI'
        'zja7lzR<lI*>N0-EDx~$o0pW(CjL<RT^HY6zj66?>eDHDN4~?{=l$(v>)*gj)PTThbg%R9pwBeFeX_HQGC?VV?)6Cuzhm6h^UWQ+'
        '`9DVCX!}EiHxl1GFM)oM+F1`6T6s`>I`oTXuT7HuS{?sKk}tiZR2!#y&qel-(4CA+_+1^JC+O(?_WgQidT1ZNDINODbGkUDyZv(q'
        'DZJA{Ck_nWxfv$)<;#}^FL>xBZvs0;viNVF4R3$*I1d?1GIN9?^Wa~1@kGHR8lr5NjLh*a@IvIw=lJbU=S@qOJ@>)yH=6Inz&n`p'
        '^!B<z?smbLrtVVu>fAe%x-)e7af~D}ti%Hkq~94mp8tW%$M`#s&v4JF>-<vO@&KpEg1EGF#uOFVowDpucW@nPolD@ZrB85<*ru|V'
        'G5!YF<0Yy7#JDX(1oSBS?ccjZUv-{kq?-!A-ZkoS$mcvr%)?6t?<^>O$#C{pSHRmF2{gmq_yLc9Pw^f%j&L^!C+_p=?cxb@<9)h('
        ';(dCl@2kM*TV8iuOcD+AiE%fWJ93x($JY+p>wW$CbkIBIijfzFgZSf)d4GfB6X^Zzl*eOH_Ix7!Kz&gD3I2Q|x@Gi@WByN6|B2EQ'
        '{ufdgS7W#LU;u?Ro_cytAATzQVMk}!v7Rb1Hh+&@cUsP8&Pjd`J3ubEn@S$=H^NV%w}*zK`@6tz6z|U+f{s{E>E30ykN&uk`FWG('
        'cHzl-BwhyYBjAJc=`|BZ5|=W4SKLzp-#i}^dpW?LeB=(nAJoT7KDj%SyPR+H`Op;j%{A?BqTe68GyQvex{LP4=RN{DGjsWWtlaz1'
        'cm81V@&fqby3O6z^v%vXBQJU2C3obF9{6PPkm1LZ|4&D>|K^N$_#c0{w1575x6Fg6t9MhBc-m3TO;z7Ks$z(5>(12ekNF(FdF*F='
        'aKU~+&Wic`1b&MC#_(Z`2ZOISexFtU!~Xf>@bhUzj#o_&P?s0{0oQd!|K{o2D*wD3-h$ix`u70&wMAl0y!?tKrp|CYeSatGv%B1!'
        '+vL@6p8MEqq7Jk(xhKevttbOq<^bHLc7q0Q>*m|tLQfFTF&GT~d;}lYBkm+`3+okjeiid>zB{*n2tuEn@eTMlxBc=f<%i+#V*LCN'
        'DEscJ_jUKd>Zz_h&oAi53u~^r?(4=~il21%+oJrt#d`<4Fa6xx3VdY8+Z%Vz(~nI42o|m?Z+vc=gl;pv-(>GN4^2pnVbZs!jy59j'
        'n>Rekp57q-dfNNzO|l*T^|4EE5q=ZkmarWnFCl-tk-81uE?#l*HiKV+=6%dv4mSh-cz1u--rqc-k9hhV`#mZ>v|-7j`83L%-XD_K'
        'x3>)Tr2G&0=w-bf|D5d)S2;hwJm%&=-hJoW&HrTMX=+jah>bh`yJ+%T0|4LDFWwgJt%myJYIykGZB0Gao+s>-UoTYQiJgB$@b_82'
        'arhAZyQ-+bQ^=3al>6uGUQAK8_}4>b$v>^<tlYOr{rKu^^qlJA=es0#U?)F*=KC(vkGrrx-E8rR;BBvSdt3ACTP)-yhb-dB=I*q!'
        'x7-`{{JvHFFAV=Rw%tOL8{ggpF!=wb#+L`&IezoJg8Mzx-)9EiT!EJ@$Eu9U14mJP0XZ^!GToc)o(}Qh4=<bF7y8pXZugPTj`2Vg'
        'W!Gt)8(A^mcj>NR-|prBUl7m7fBmy>Jol$JNGGK|F`c5MG^n@Aw6n1K1E-L3mZ)PW!YPRUh1@O2-R<<}-1^S;mucKEp0&np3b)(G'
        '3f?$+aTc)GQQpmGzW$2@4?Vew;1&-bPX3C8FBg4oj9-TRh>U-Bz8_!9^{N{tT!(+!^EUno3%VzvPx0$h`uUqp&L<l1U!T(4-{%^4'
        'OT1!K9*~`&_U%!gJ*{=Wc8K57I`rMC?gdF<p0yzO+SAGR{E>Ur`hTwYeuFl&zk&3G{ubkAj$d(Z?_Phu4L#-hT`Xn!H(1UHto{QU'
        '4E+Nl1i;@RCm_9{>x}4F>SN1wSLsX3kGh1uzo-t}^1v-N?40UQ(e0<gZ|{MB^YEG_N+PR^mIGoqb*}S_<t1fL3zp2e*N$^KZtlb^'
        'R@w2-k;nC8#IYOjk+MJa=6>9`|9o}@UyJ!E%57u*A;4QC+NzRhT8o=Qyi4Gi>n676f36?Bi+Y#-WA#2>($75*!fzx)e?oo}!-;Mm'
        'y87~aY<?H+lM;Rv?p<5|BwXZA!o4GZ=qvIr=%<42wr<{gr;mNVe*0Yl;LZ&MU)~`a&TdbVp5^VQ+VsPWZ(;8a=Omh2C~|fjmMXbR'
        '@~#hgao-U<i)Ckj5dAcEe}0QKH&4I)qQcid48uQfA^o%KJe|fB`u=kZw81Gl|JcvHi~o$(f1KKT*?SKvUn8O{e0{p3<DU18hYq-s'
        'fWH@4n#DYRx#1b09@>2%AU{FyQ+f0sOCl%A-5)*H>MbFC6z|Wz!na%J<h_P@Il>eA0e4Rr&ynA7?#4HMLwG#?4f^>57W6x(SF7Un'
        '@SEomQ|{f^XT#zXx@IZn&A%V|{s;{>Di6*si9dy^--G}kJl>*+<m_woU)cO7QcfsvjR}74h}>zs#+;S-N=2V%6?td=a?i()ebA~i'
        'uwd+m8GmWf-6V1g+S~7ge6slM$#2#$R*L$$w{rt?pe<QaxQ$a2-XVT(mE2}zxWfEn*YF0|;q@|e^Bg30r{es3v8Ug9k2i(9Yzcq+'
        '=U!ybLH?x^`JnzJ{`h>T?S8BSy*9QtzPE62pWI(>K~q^+oO$=<Po4ey9_$9}#3=C7{_VcH9ZD|h=Y83edDzKbpB47M&r`oS1Mms+'
        '_J_DlCYSho&kp_s?mF77!F!YbkFDM>?=s(ZlJCbKFLK<y#Y;b%$DVt))<JS<=RP%dAEF??BLAI9A7=e@do%HGGyi|<KYx}O{EeDp'
        '@XsKhRrev!2kI|Q{a8VZy9@vF@Y#fTbyffOKiA2j4{}?Fspw?j`*FZ8>iDdUzftrjpu5t6yH##--Wux9;t6?s20x#{;GgFA_m26C'
        '3GZ?0CH{Lnd(d#h(>+zaC(mEZ_nt5BP&YUIyOisC>Yx4i?z?YJcw5kSirHto=)WZDJH|gJ=>L?H|9?)d{~y!kEBZZB&F#?oKPQrp'
        'J%?eu*G>PF@ot6tU4}>F%GtHb++Ba7e5){=@cE?ozo%%<f^jguL!UC`!<tS=d=w?059mWK*^hHAM&8_QP2Yb>>vQAsPp4h~ewy&I'
        '>Tj*IUk+p*Vk`T5WA5c+z<*p0-#n3LkLB$&=wp?>^<ZAD{g0;0Ly}L~=ohEI5B+>UuDD5hJFP%|TMy4u0e3pz4aF%!b$-X|2A}Ke'
        'A622exgWBKx8q0$(pd?2Ii1V<p~j8Dr?UR3uzT-7<_`|hI|=X)@;(CAW2&FdGafYl{uG089K!sAp5IS(KW(=^x~ZR|@$cUt`87QM'
        'O-TB;aQ*AIP<{`|kA}C$J$ZosEz|tzIO3Q2-8}pcjr~v3Jx<4dUkApI8^2pS`BQ804}$-xG4ubjCf|+<o&^qm|L2T-80`0E``d}$'
        'ucDkj&G6$0*ljy~-hq4^^!|QE_iz3AUnqT??!Jw@jyN~Waw+k&VX<4$Fr4Ypj@Rn8s)+yUysp##jh{QA@c#lW##S}'
    ),
    'scripts/fast_kaggriculture.py': (
        'c-rkdTT|Oem+$@+Dm_Vw$7>TpGS0_W>wpQa0A_77vok7}N=R+cMwYaa40u`p_dVxyx701kgk<x!OI4uNm(%Cg=hmH7maGleU2Td@'
        '#$4A3*J+X!h8M?4;T2&L=bet|^OJNd+d-Ji=DnBSN8zpf4C6dyejz{qBTr)4&NgucA>Z7lS>m(21XP4;)>$Dwt4-_|NfPA}ohaM5'
        'zUSYI@zg7DOF4QCpM0R$reS<1`$zG%Yn*sd<lRQB!)N%bRVc^L&L*8sXEvQKjAH^~0VBc)*kJcEmM75zv+Q2#Wh^doXRz%2F}^yT'
        '&R{aF`4_`{U~!OSCN@`IUbx@9ySps(HxY8v>|9Jf&qlMqV1ZZ(^8oMW)Lx#Loz7%2zMR8kr(?j6`RDm~v@pAdc`};Krqo(YFGq_h'
        'w&si3=+DpN+3YX;x*T6judp%x@`b)97hlb;05hFlVBgtzwwPQ@{vOZp>&tXH9~1EDp9JrGJidk{%g*&|dU|uRKtu>3XZZWFb26J='
        'D?RU*o%uQM5y*ZXeI0XLKF@BhPR`x=HAneuG`k$n=I-Ta_H|4>lasM~G8>OBU4$XgydE#ylhGOBbUpd|?~xb<)GmSB=aX^S@z-c}'
        '<<1w=*_aUix0})FY;;8!JLVOUb476GoV2kC=q_eJ)Xi*+v!34#k#K@`2+ix!9EZ$Zr*m^PS-70CXMxygJ~xL(AE8cXi*slX5bE@X'
        '+6TyWSP#v2(EM{u%|l7m<mBtkHFUg(u~T3oG>?$Ni_ys#+8=oP3fFwZ<)a12XK4H`)}N1Ne{hI{zA8iPKrButU$BWte7>1noVr96'
        '^t=-Qc&{W71`Y|#_!QgkN&XiX<CBG}s0WN3iRGYrwCY2*v+HmX>fAY>@Ck&#UoMbxDwu+wbH33#@hMbG;SctXt|phG3&ErL_~L?i'
        '1pA?~xs$8Y@xSAKVZqizFfRdnGFC~(TU`UYp>42uvu2rBFpG5523ej=ug)f4DqL9_=1IWj1xs_}{Xt(~;rYb^j8C#Dh!oy=n|N6;'
        '5C4mC=JU?H@Uj9-%w-a@EmGF+%b~URbm?W^STW54mgUzhTWqpeT?{8Z#{N?emmWwS<o7H%@lwwZi!Du;^B)-t=Bf7>pWJ(~k9hQZ'
        '{r-CiEqRRR_epvaM~VM!5*I9c@FL>2K4H$HNEtp<hEEvw*Cv#Rt-Ne~?#01Lk{6d?s1)X`iPCE?^VZ19=N-zcb8<R919oSoX?DOA'
        'vw*FPyvR0wVLTg~FfKm2g^{G6%C?u?eFEVXgCqEeKN&mYY<?4m#mGn3^XYX!Py-0cyMqb}384vquvhmmHqgwS!~RkM;Zo-(F_}Oa'
        '2}#u%9BC7I@23uKxesXqBa!_EYTGp)@4cdnp40W>aP39V1Dcz$z%7!%1FyBJn!Z=|f6_p$7^q?d3YxjzgBOyQ<1@qrAG|m7H%0is'
        '+#mx`+mJ;8C$4Lx;JZMRU4-x6Ch;aO7n3;B$OD}S+;U$@H7L3pg)5e)UhL*@nDlieTDTLmH~?hOB18mR*%Kriz}{Hnv66hp=@1k|'
        '47lE3;y;bLG|Am36kL~@TauxMXe>#M-T&NpK?d}|$9)LCUFD}l9M7RMH~@G#9K76l53MkMK)BegGam-rZ)}^(QJU(;vP(w<LJ7h4'
        '3Xq^UhqLEq3<8M_+dJUiZe7%Jz8YD121j$RcH^Ldhc|Z)mUY?Txpe_oIQdDob$$oTMP~}(2=My%8l^dyklgv$;4Sq7uRsC125IVj'
        'vdQ$d0mzdhJdeE;RurE)4@nrjF;=<jXAI3X&OJKBjezU6Iv&Ali+_Rv3?e2*aWG&&bh6zyj96)7T{;a#c}(9J5nC0_-YmSkFH}GR'
        '?;5a*pf?7%4OoCSuhT(kusFw9`gRjWg=HJR{gYzLAu%Qg76FqnQmH~hiU;#>-Sg8FB9dwV`|fLf=@#@jNcg~#%VcFhv~GxKv&Wvo'
        'yvSi^aFVhQ{1)H>f7~^O*~UNc6k8ZaH-^x+;s82Tfv(MwCj!c_y$9jERrceLW8S@eixJmv(|7a-6wALqjy<$M)R7m#vH$k%-~<1<'
        'N7F{l6$DBm5-fkr-x3q`E3*U@HvihgID4tDhit+BcD%?otm?O^l`-_hk~bi=e=YM13)qr_?K&RVB+J{7jAYK`SZvaWIgmDVF}GN9'
        'u3$oOjJbqm%kQ2KYc2GK+J-RFrQsk-!1`K9jIJ!UEp*65yJuzI;}CbE&EYTK5M2oD2*(B|^zhS`dcenyjeaFDvH2AoruwWwW0rX_'
        'J^2bTTYct1W9GAoW8nKC<b?&h`il3>6`FX;<vje=WoP<XlENUR9gd_Fy=Gm?rsAf|VaXJw*RCzlJS{A_g+!BsR|o2=RA0J@#Z+a('
        'ny;-dS3Iw>Na?LFXgFDAS!1lexXlGC>)VDE5L}epr+{vPs#VF8gHqG14g#zKnf+=~!rOIPb)qq^LdfK>VUVYv`}6^I!GEPH{E$Ry'
        '(qFw&^5&{d%~mZcW-39RI#=n|;Wi^beT(L}y1p6usr+gTilsYYo08icQw1sxS<*jNb}9nz;{>5!I3P-HD5a&ukOW;HS0IQt018uj'
        '(DmdH6rk$?FL%eR1I6_KaxhhH*y8~XPG6Q&M8v09N6}-KQ)pSwOOZ_7ed+dzpF)x5t)j#eXAgU7=Z&XR7^uQj$0==hj|Z>YrSr73'
        'iMXeVvO(WoQr}kZYXOZYvkYOEGNRbGzqGrC+O@^5HV7ED5OR$n^4mICWLOh2?_IV6Kr(P#p`>dxI4^(N5Zq7_3%Xtg>VR!o*l~u6'
        'Jj)sFlvdHbqSH!mO?JClY`|k&9vz3OZno1Yi5zM`%kUa&54%pCRlJ5#!jMQ-2?XbL4JZM|Vn?OiWfDRQ9D=)SG8{MtX1>_!E9D{p'
        '*|G+#yIeMGm3fsy2&0T}mav6f*2)oJsXTinfNFDT5ng*dF=NB(gDeek+9;0`ym(cms6~w^14Pgmh$x^bF>Ha2({$Jry0pSpctI*!'
        'e!Z-jJWDI9SsEzRb)7#IOG<;;$o*c$BUuivq_k5#3FVBs4C)(-yz<9(+ex2;zp+$>gjZ&Ql20^fREBo6ZF#~PE`@y!^^;ak6B(>+'
        'FSUrIGLg@XKyyo07+p?1;6kT@eggm215~cmFe=rXJFP~*hs=UmyiprP4!{`xsf|>IuB5Cbe8tqfJ`MZo^OQ)l;%7^QnX$DO#t<e<'
        'A3$(-49lljw(Zx$$bD{|2A4A1f&JJW%d7`4+OQ$NxPbw06BUFE1s3p^o1!AyHsVagm{xPh?8#?oVOWc8%EnoiKp^r5j#ArhtQLEf'
        '3A~>K%=M@wVDUc!DahW2nCs~o8DD@&8D@7ed$dehQ83<^wi+&nc^E^+9s5iG20|fLQc&XEmFJKVjl&0ecdW2vNI*Hh!>=foUE__V'
        '&f!j<Pm!KmVA`t!rF9rv5hSA`<~0ucc1LqmT?)LkQ_4$O!$XKRD!iKn!n&?uVLaI7sk2SUh^#?(D?GT9q?AKoRgVpMCqram(hQS%'
        '@H6;WnI%aYM~+*Y9<5K(mnV7Iow(ZKw+-4p1Kg)?BYDUs=(3G}8UuqxIWzh%14b#9x{biFPB^H;I^eJd1dA7xVVx>TVH<=fYl19S'
        'NJ;Vz<j&FeMJdYK!@<$7lO<$CMHp{bgE?X|RW{X~Qd7Ep`#TUsIP_~Ir-S|p(Ft23;0ap-i9_Imfdun}MK#KA$#}?nX{XogspX{D'
        'TVrDHW8O^{=2&NQaV-JpVyBCfj#s??MZn!>aSadN&pUX3#7lb|70b4J_v|SM?^s?~Hpu#5xic%(Kwzj8mPw$n9*39H5p(m+?K;eJ'
        '&_nlyAsEQEX#&hL6&3Qq`h)?f7|>DDMDoEeTU9k*u)-?W)Iwju*>ae(+Y5p9l~uP^=2c=4o+U(}ZxaVd+%qx+sTLk5O`_1>x+P}0'
        'MJtCba`{eHn<WWGWwgBKx_41>>qWWi3jS`WSSM3no?BxFF5{gLRHC-!z#7h$$9uf_5OXU|sG1=LAva4cjhA6ymGf*W;R5vU98a9m'
        '^8yIT)x}E6j6}$oyqci-ck;csUnOhm%B^~C)G#eHPq;y}DS!p{<n8FUk{}>^@z!dlGW<nKFU;v(3HtO((O^kXDV8cfK#^0`X-ju2'
        '^#&wqT1l@qza@#2vJ(tdq83>vMt%!L6?%$AdPce4YxERUv{cT=T75-0f=Zb*cd+kVsL3c|p`{_BvytaQpQaIYX~8&{s33m~!MK_3'
        'd@)*#xs$7nTui^1_MX7<hZV1>4MN)_u(}f9suK7sbrE^g+oY%<tqMs+PW0~(d%&ixDyB?B`hqY=^XV$xxvD%hTGdUGw6gK^ZpQs`'
        'G5tKEXF;dqi}9lDs3~t1CxagK*i(TDyE30iiFU(hAaiG`vd)vNV1b3?+d{;eY&1PbphC@Mvf--w{u)*1S2DU`rfZ@u57@CLDlN6#'
        'L_ZMPN!Y9Z|F8c4m(_odh7VgrD!BZ^EaQSyVkHNF>E+gdF$|f1OmE1eHk_@6Ck7un6t+%tne_|rRQdZZg74BR&>mufjnYxCIC2yX'
        'OMea>wszhnY;oo@2uG8Q=|{f0Pxyi3P38bEIET$sEznkwA}Pvkn$Z>U9oYOzLS;aSA?JRB)x}$rp`jC^7ZFl?OvMVG%gJM!hj+1u'
        'w_(Bz^{QDaXL*7FTXYTn=&ejts`-$w9Lt2IoG;^HOe!dwxP#gJ$nv}b!)8F7%YiV*;G!!7*MQ11{L}YRdPK}K*PP!+;ng^p5~fcn'
        'GCUY<6Y$cWatXTFEO*9D4B+O{_-_(4tinIt4)IWDYk4i-HSm$}v2uxD5k^r_EjhEbw+{;a{221LAFvM7tm^#=JzJ^!7o`p)ABvQf'
        'AkH6`=VLIpmbnR70Nd4O62|qp-NtHpx5ifC)BgehNhlYmkbY6hgCHExW@ovq$xCWCNvbVdT2>`3yujvF;p$;$pBsHq5w=<%J>%<U'
        'dnX7?f{m<{InQ!Bf2S)}@DKjd8QMGA!Bwk}oQQz=Va_3yuOuG%rLjUEnuMBmQu5m9<1Ul5ln$F^4G#KPjrrI$4hBc?>kvK<KEmg_'
        'BWN9dgkMK}`1N6MWb=erIVJ*#Fs1YWl}e5HSf`h=Y~}ipFTe>Gnxj=mc`AvIV01SmRJeTIB;Pg34!iEzs^W5KX4RitI1AsjUNA0L'
        'dTYBYZUAqVn^8zj5wy6{YS3vyS#k{a(t?xd9n8_kCTK+~0EW|FHt+F-vR3Ncgi?+18#1iZc~4foyDRo^WUUWc;%=q&icZ*A)P2SC'
        '$eRTMMoqi5_`a-jM7PVW;TYX|$l|n?GYVYn_IpBZNH{h!sNgHwC=#Y>Z|sQwoun6R)@d%c?NUTWsWE@-1(>4KgU}*Bw#+WtjiG6m'
        '_X)>XfGaCwd*ZzsTck((rHm1ELbt5<E3~yPsJQeqG`E7>!-%Rd)Nn#VkU~B>4edbM&-Xv@)O{H4CA8Iny?*nb70jz|X}%lJmxZEa'
        'z4mwwvh@b%JGVB&y*#Z@6kBk&%PU$K`iX8{^rkWw?{J0(OY*Ufe0x{^7bEoSRi|*HOZz1;NjJ=8<H$V*;P2lai^}*5JZZV+!01BI'
        '|7)l}Xi$HQS53<QJt@P4<qwc5mmr<xRe{_EuM7IRPFA;sPTLJ5T`qEaUFodQ)Mcyl#y8H=aSPxMK8Kg>f#Nh?@9<d!J^LaI<2M<B'
        'C|9VDUKWrm;?JboUTBGTQ{VAMlwAq03t`k%Bh=7+a!X{Px@pKS!S*#uH6};c?L$l`a7V7S&KW3k2FsSa^87WI<$|Mb&U~0IzG`zc'
        'LkF{Tcc@(7wD=_+A)4k(Ac@>Id){CE3h0A9&<8&Wz0Lf)eHUB?y`yOJ4gFua)!@agewM0L7<*Cqc17{`zvLN9<1GjF105grz2q5k'
        '_@ffAW3^W`bwF?4Jg;~#iojgT*LqR%i1uIyuq%N3V%I&<@~&l{@^#Yd_o^O2{rGm}XmcxGkdvUgRi(9pNEgt#Wj7%=-JXfZ;~9VL'
        '_U!dSbV>F%*MpeKAKC5oQyps#LSn4HG;4db^Kw?eZ7Zk{MfWDAHN3fZJv#K4a^-gTN`6P1DBtxrJbVeS{opx^lr&g)Klz`A#D5p+'
        '{0}u&!DR'
    ),
    'vendor/fast_kaggriculture/fast_sim.cpp': (
        'c-pO3ZBOGk5dPj@5wX&#WlOc}ozRJJl{j`+$A<+(K{^RlkxAUvB6V`M(`|0m|9*apV>=F|==e~anP*--wr4&doaR*qqa%velT}$B'
        '4F(??+C@rPhA^8B1{Fnk8NGnz`T1qaP=RBcbXDL5S~{c|TE~L{+%iaTbaZtT{TvJ^BUQ?xZ?i{?m{P;Z5&x^WmERK<6=m#v1F}>E'
        '{(XAJ3Eb{3wlv+643a%c5QA%@<=4*vEsigadlg^OCmGTA%fFMyo9l<!+*6iFP^^WOM}_#MPp4-cu;O?QJfIwUQM@3WxpDkh0p?Ox'
        'fF=N=HOM_A;Aw|h!io&kE^84cr=S;47|PMVkR)IOP!67RXhM>b1*R~q7}~%jBelb;5zI3?J(^xZ%<F2I2&>6+fh+3na+w3nxIf05'
        'CVgwLO>(q=v;;Vz43@5(aaI`RE2Y56^fy4(I@4KE@nE8LfnnY3p4<p73H7G`d3$;PWp1zCKnj{{d&{Fi)CUw$OZ=w-8R2>G7%M~|'
        'wRfrso~~e~4BaHx4`07qW)vU7j5dI)``bGofbhn5G^EcQE4)cwU`-E|!66|xMp`sw6H=!4jlw)n2;4wi!Cpr4TqolE`+A(3m|;-T'
        'Rl&>!Ad6(df9TWaxnF_g1+s((0x>H{-6+1hzy0!f)rmyIOM+5Jd$3J%xC^C~nAu;qcggk5?BVj}>T9=VB-%@xeIO*IbAVPwMO>>H'
        'FMpMfO@XrGXhD;dKz@M?1>)>CT{$D29Cg)4=|W%3d@&LH=nn}~L;_jGuYC-EMEo5Xa?FUEur1`=>QH^I0M2sQ==VgADFY0p{HCDn'
        'f)kFXLyd1W3WXWuyIIshl^M(-<7LsO$x$S7=x7<s8?JpNj-wndSeHuBa>W{x`t<<vUt2`J48mo_IF~2yr_w65>=b%YkZ8#FfF~9('
        '4*3+T)kX9<jy`@A>&Bk=Ym5o{e3Ir6kl`rqVe30b>>A6?&({cFh=+ctJd&7`sRoTB_pn+@jf+V6hq!Y=L&9NXd)swMop&UY;lNb='
        'T7EUiNl}j9h~$mLTcOwm?%HT~y~$LM`o3%`)HpglJ1~X1XV{-Z-FCbsi3Ykqi!D@KrEdoBOQibkJ(ed^c@~=hKh4J`*weXpX!Ql|'
        '9o+V2KaPsZ92Rv7LB)z+q;)9w?G-QHbsQZlB-J+HL_I4qS=Ql{u#5`5+|!e35XJcu*{uj=B%N5DOT)I#H3vAIMGG;Vg@Jj!Mgz5a'
        '4GrydA5La!m6n?4r0tkQa%#V9jmTDsY&#;`QJ{kDq>3(0d!-t-dj7PvvSkNi0fHyPFGT$~PKQEpB3kj$SQ?y&CVYILeA}jv4i$Ae'
        '`Gchw@0PUYfp=K#jto6Ylr49H(22HYhgW2~lY|zxMu=C$JM)B=4h<4rH9NQ1c7cb&)VT;mmAYJAcyFqxc){?CUKFnyG6Z+7>)oQn'
        'L3rJP*M0D|CAUR9Y8*bi;yKW-mRRYabeAokD^3obV{KR|e-bFmuuYBoM3dGzU%taSV4L0;k#IuJTej(z5V#ssQj|)uTp7i35EF_8'
        'Su2)<n)o)FTS`3me|A9{YR4=m4v*Zenc#%wsOSZRx+z~}KuK(M40{7_=BrTb@^$SDamIJ~L@V~hW5+=qda?^DuzBGC+Lo_p?9)A;'
        'w5aAo)S77sO1H%5xzIqIIZ<ihw_K~iOpKDJ-+9S0FTCW4xzVuNAyP^4HpFY8%!8nHafIsFc7y)_AKf@n'
    ),
    'vendor/fast_kaggriculture/sim.hpp': (
        'c-rMX?RMKXmjC?}$jsIw#*!k*NvCVY?ol13@rh%lwldj{k5;86%3>{%DoNSaWPHv(#6ICZ$=(lu1V~VllXPa!tlK0K30wg8`(9kY'
        '&z_05?)7!#kCwA!8F?c1=gXO!gpv54|N3v?iiztd)5&rsj`#M&B8(CdPQ;DgrM_6zcb+|i|HUgW_OAnR9lEo)D*Ql%(b$U)M5XD7'
        'D?h3EV=qYjkvkKS7ent@B%w&Ao_N1XreOd*5-(ar9{gQJc$JnT{^muYn0oF)xU*R}auXjKF1$#@iMObV%Dy9#$iMaB?MjTo#mc>!'
        '!7>szfxkl$du}wEijf;2z&LOh@ia_?8;r#yjBbRt@Z)go#r2&(E+Y4O?usxNc{_jfgVAg`_QcE4+)buO`hz$b!$fnBB0sp+AGx#Z'
        'Fap%gjfYX>uCxb#SgazLNjR@h7mGja>;&%Iix=+5Lkx>gJ2>Uq7ybx8@#cb{BDnYGy;mQO`xi_a0gD?=y|_S8;oZBVWVWh{K9FbP'
        'M{xpw-+E#Zh2!N2DCb554=Bwfq_?9eTrlO2&wKCXAXTJ;OYej~7UOUU6aoP7zXAu(>pNbsoQo5j?SWVVhQAvofCB+PAK!F4eQ_un'
        'RdL)oKkxOcqThSh>G!JQqJQ4`_(S*n{O788*FEi>RYmv5AK~-K>D#LK*z28E#p~{Q|K#-Kuif)1f%~!7yXXR_-bd*FrrUjA6=%bf'
        'e)rwQ&O>`=6b8Ur_lpSG5niMiI~4z3e9P-R6fcUeI%g;EI;Z$@zrEuJGe7XeRT$2M9}f{36}3p;5uZRJ0QDdO;-!Mx77zJu5?yP0'
        's@YmPyMaG<XC-})4jC<CcUM9pgdmu&!iCGg2i38NnaaIIfyTY}!}pzw3#KxBIqRMG-_WOv-Us=q+qvk|hmT$Okajyce*57)J%0sw'
        'qYv*-JICFu#cAhEcI@<l3-HsM&iP-u5?sn44CLg;wC4{WPEKD9k9!g<e}#GWKb&XaUw6B&==E{$^t5~2A8HIok2~iK`Q+>`ozs(7'
        '$YqR&cNRpvgQcH!84vG<Z%(l9I~e)rA*|w+`g}oS@@GkN^_BS!zg=`sPie5PK|xfh{z#17#N7dXhf;eCT>Q$L03RX8$DTK?vaT4e'
        'd~Y@$j@?xiRLs5pm2~{AJJVjYnMK3kIs`2WESHK)CQ@oBl8j3!Ap^h?BkhwAO~6;HD#Y_DV(wd*3FszIJisGZKB*AZv?ZJFQ`6_U'
        'rmSLA+ZWK{J9q(qn$#AS?g`bF)sSr4Y(U$l{L{)B%eI-SQn0^M?OTO8LwizZ8LwOr&e29|90Nd!JDFYJi{wrC-b6e~LUl;=Gg6Jh'
        'IB9DTWA&*`uM0FZi8dvgk*1ak$xgFuRH+ItQ>Ca=Zok1(XDJgzK}I!b@)Xmgon(*a4P&uHpcdf|)qYCH-bdN~MZP_>+^4_MK&13R'
        'Q=s8{>Ml%NzaE~RoOL@O)USsZKk?t^ef;;d_oMs=$@v<j_Uy;5hW~eNbmJwAf3|<(%8ezqPa19Yu-}%$UU{?dZa7I_@b^T$cCW%)'
        'PkYVZOURH7{;qTWw%fnVtb`#ztry6R4a5~8SS?S8M*X`+x=i}sYFGtpUjy+X!vwT!*7G3$+^`GWw~Z7=t6{)s)Su^IeA}=KVk?8u'
        'ERI{%DB09t6a=*OB7?KvD4;;`0sic3a9D6P{h>hYw`|L?VHG%EtwqB}v(?J4zicfi2x=7#9UCv!uR<d%h=!@ybegC!(?w|C6@<(T'
        'l2l2?lq?$~BUhN6Csp<IKK(@gUcKQ+{`4oJau0q9J-X+2ZF&>m`QXEf%0xBApAkq`I;#Wa=G?dQ4K98<ps%Wdcxr8Q-ap71f&YJS'
        '5dRh>m3ybq7BG7ta&2efbp`le><N2^X5*mHq1h<!LJV}EtyUqZFJ4Nd6&H*@617V}-@O2tvA*^0M_wF56PgO>`wBp;LZ=!Ev19g;'
        '<1AsK-@$aBs^02D*7{*5`#YN*dzYR0V&*3h5m8tnAZCDIV$3Sc4U)JGcE%fp^TiT^I*iZirecNunqoy&S!I=2P>8%Jio;%}eXE+^'
        'e6$ND4xbO*`68|;o|4YbmM|c&ITV)zjY6BdM4uiqWI<>uDrg&g<n(sIx8K|IogDq6OMg(OwL=%F=+zUjUQhLB$VShk1m>H9EM|}T'
        '#+N+p@gbqv7*X1yZAO%4Y^xC;c5*xy@w<nLY$PAMim5oKaDX05<^B1|ad-IowAVW)XQmQ`%V1ntK*;Mkj#HP7{}c;;;Q*Im@?#dd'
        'K!X^;(Tm#DolR;<So3bZpepXBK4>04R?)HuJU6;p!2keh>`h#Vr^P%R1HVcpM4C$eqQRNS;7QT6;Lok1E3;Z^yLZJx!!mRjv<uCE'
        'r*?_;3=Y;?OA(==+o@iKQGve}^%GDW^a?;Mm}Yyzl}z<iQg4y*2@Ay#v{LetAs<x`3TO&kNELu63VP_)YCpMQYA_6QQZ`J=9JXO_'
        '$~B&{J`CdUmQ+{P1#>kOlE0KXitq;GAP$=1d-!u8ZWR-KdDJw8pchy_3GV{sSB8s|aUtxxc!Tj}=WX}=XX(t-gYyq($8Uxg?=j~='
        'PhNM<-*wL~hRh1`A#(TedA9>0AAGH50N;1PukO6=%69Kh{`%Jrx8VmD?|Qxdo0G2o?B~w;+3=#@Lr3|HUQk{HuyNMwgWXA{KI&=E'
        'WytzI*sL&0ym5tEIx6RL<&E4WkQQ@8UU2J2VKDcAJj-Afj&4Y#z;I8+FHvw^A5B9P1_O}uOTFmJBF>uM0@7%v?>ZN6FXa?7SGLkz'
        'ikC0Zg>uB-)i-ieovPUK2WH2#*aR{Ao_UYfVGv?QOdV_<5WB<L1NLo8hC)BfU<n<x)-dahuHiPA0mvp_>5%0lw?=3lvSLgfW^Q7I'
        'Wv`_n!c4h)I~-KEnyDco2Hn6x{!9cA;7rbTY+)PfGUoCRr+tIVF*;8FZ>1l=*CDvEA6(D8no6y*23jm<Gts)wB`M!^{$t1r<m{r~'
        'IXmuR{_VT3lrVy!CjNDrE23}8n}@Mw=6#5Hd~`Se+-hV>{3>*#@i6xPhDM^Py#UP~C9uHZJPf=Q=2jsp$zEf6f)r4k>xU{n9xl8H'
        '6B_WY^<0BF^~PW;7VgMTR@ARyn9Dm4-%s6uOcr><jTd_7a4}@1HdJX6PWc)wVsAFn-)qB<JbYYeq0eyYN8WIb-UQ5!AEPGx_W6+0'
        'Zsa9?)l8qq#;WhnytjT}m@CmAcHh14OEcAn2<G@LCL{a9k6r$kGdWtmrOzo?^u`rGAY{o6=^!`w*P()+trLd@XUk348`gzL?J87g'
        '0JJ`W^W5|hC-O|C#K_$6ONT&H))9ZEuF8(X0F;7jn+@&&ArUY^5;FJL+DtaQAGw<$0Bg^H=cA!}>-sa=$ugQMT#%aZM#}`^q~SPP'
        'rFa31ECV@PQCZ9&dU6Clo8WhS@hK=y^I?8IW;Qb3F1%oj;)b&yUWLKZY(%zL&^X>$idIG;m<`Ya-j4XC>b2j(UMQ<Ge}X$+0cio~'
        'TWjV(r#QhW!Y4TfwnJtrs<RJgC$v}doTdRYn7Gm0i@=iw0UkpriL%6T=4&4o<c>yujr_r}psg(QY2ZDCq+SmE553O$E2&o$8@~qV'
        'l8vRdP>M++iTE5Q?!}kXe<1%c@Vp4);r(Sg{XvzUth6VYE(lUuHQP3`0y5;?iv}(NeXqF-9vb671M%C^9Y+{i7r~&P_ffdBJ9iaJ'
        'Z_OJUnkY`W7!je93pMGb+&Ust)p*FM*(6Lz%5p4(N-Q?g`dUwF0Up1G4r35#D;uK|;6*jsY=RD;Si{Jd)Rue9V}F#yRoVcKA&QG&'
        'HX|@YV&Nv!7(=lLm7fF#2%Mvb3+54XS-ms%ZgE!>lo4;Cj=hnOnF|>VLa+s&p${T|1_6kI70<#1TY3Bnj7*KUW~Z3ya2MhVC>PUa'
        'Db79?5PXhnR}iy+{8dE|rjSNqJog~J;Z@9+5CC3z6lcz601Nna=7TAlt?Gsb1%wQ5yj8pzje3tD*G17rP39y(NkG@0x8}nD;@}!Y'
        '!hl-{t=zG=TG4{_&3#<tl{a;7{cwp2d#s=>V6|X_kzUKdolLwD=#{$oW$eeGfyUnW7sc1oy}=<1=u8m>SdBsS0*uXpMoAQ|aE~gD'
        '+e7FY-T5)j?$(cel;1=Z4b%;FmCm4yzo`|^YD1$qR0`MHOzIIq4nc&Oh9#)p)ex7rbqA$~iCz2vL|~LGsYW95MjoZtCQ%5{X!rCq'
        'HlUD%4r5gOx>?CVS-4<d!)3yJa2vum<Q8{4rj*7~<}=dFMxf`bFzFCbu2N+x+r~ST_2qyQ7vhkbrOb=ZQ?^_V_Vy4JYE#?6E*dNy'
        '&fX!V)KHl?a=Zs~@*w)Lm!G~dZ)09chbjGbV?F{V19Vny#7m)1m^Rq8#oP?UlS4Vu-rkLgh#OqJ-n)peG*$R341d#xfA&N(Hzp<w'
        'e>HLVD=xrzfc*vr?$Z9XnvO57CxF+9d*f|MZ3A;J@x9EtXwFRm!?hyCHgE`25T}FqZ0A#kxEpJw{AdOe&r89o2z&Zf7DQ0)RgFK8'
        '4Riw2lZPG6*X8tF7W<GEQ1)r1@5kk}3AiP(`CbEiK}AjsmHZGi^YLX%LXo3#GSF1)6cb(+qd&vV;J{Hg)k1n{+LP1|NF4;!=;;&U'
        'l`(iknIHSLq7;{uf2@%40rY8y?ZKyXogvOvR+hBWr*3qu$i}`!z+O<cU)v+go`b`M85tNdHwq5XE0DC$NTg;&$k3+9+Fx_;MC!fc'
        'i^hQPm2=uMzmF?VXp$W5UN*lqXqU#ok`Bb_%;m`7h7YL?na%LiL)!!+Ir?i*ZtBe-5RdhoxbjDb;e-V5p7jWq9*C=0=@S^faR}~d'
        '^YE-IT89@O#r~lz3n1omXA_w16=qypMs~Nd0vV>)--B;_AX=bpc}G!u*mN-O3uBz3W94V=uaN#6dwge@PQ}`>Zrz@?!9ty3@BCHw'
        '{Bl3d*tDu*Uz8<!s0Zy*T%=vpb}R44H-xr_O5`Me8p0PZ28SF2j0)q5aR#>e^7#OifurSIra9zbqsD+~KgA8cwtCde9;GdtswH!)'
        'd}M3cD#C23mRYO)BE0>qRiS>3*E{~z#e~UPF0n0D@xeWs3!0bs``-nBbI>RQhv;wk8!?2=s1yIHqAVOe!2K4W?iI_D&2j{4zm5}8'
        'IIlLfcYy`rBSOH^jcf-Ci|$4cJH+C`$LMkao|!*7pmoSR+Gujk>tZ7iC(<KV&Oi37@a7Qr*cBrfhd+OMaDdwZL}kQ9fU%cU92z!N'
        '7V@F7hY0{^IDM;9;ToXTwX9u=cf&_v;{pG?gx7$TMSd3(&DgG(&=yXe&DmmLZaYruD#FGg&3s_4r5aXdB~S&J)5JNfoSl3Wop!wE'
        'j`!A%_r;DpKaTcSgUkCtU8b}ux`G3?1(r1dI?{{zKFzKjq^Y(1`U{pId&P+alB(Pu7+9>M3URk%>$KXw)5Di+Qv+GqA*pBn4|!49'
        'uJ1{sUD8GRL;k?F#b@p|JH^TaJ<5r^JHR~iq$4*`KV>x-DeEz>rIG=rp%<9@SzLyG4G~oUnkt!Mx@!g2?N7=<sb?~UZKY7MmE9FC'
        'X!qQcX5M**`Jf9`^!@dYPjNhS{>XUjBHUe<Y5;Xf#Tg8J7BBp4zGY`lws}SzYUItOj@cyA?qV@p5swZf4l016r!>FCpo+t2<bjZx'
        'Oc>L+!p#~3)uB1i+Tt$i5LdmNdljCivz?k5dn0!>q(o(0(Fj}>1u%$m2^?c0M|@Mngp^i@kwKvGL4_BkDa*QamNQ6g{jI_^H?tyJ'
        'Yc0KM)%=@v&6#Cr&?8oo=2lA$ogc|lXnM4uXa^+h78Lw};`T4E`BrXvDg+kpAet5ApsILMmxm1o0*i@~aPE%;Z#dk#Gk;8psRP7I'
        '<o&kvVo;sPD)LAI7Aj%x7c-FPnvSbFG)!ZyB(QJ-PN17`H%b(9@q8@C@MPhQ>w3>u-duW-qi~7oaS>uli~+{WtGS=xLk&r|U_2NC'
        '=1c%>VjY@09)m@Wp+gdKCY$Fn4ly$bi|_$;6*|s=-LpeAnC<c++K1QST}j6lj66?~imS%r$^+E!u05CqpMsTH7~U)wFis5uLZ@!3'
        '3|gf%b6aL1TxG!6KoqLj+&V`jpvf`rI!r70(M!`_Vi=bmmT=Te%m#zKJyXR6X<?fmRMMGLGpnj80&+YhqS6&w);8j`jr5}%dwbwo'
        'slFq`i<}>PK7!FW;XNAIRI1H)G_a%xlITaKOKumCxwPPLX`&7vshQHN0a--ws+OJ!FcaO%1empoi62v$8@4tl?iDG!GFddfR}!Bs'
        'XIG_?a#GLj*vT*WnkIoK=(8zD2nGQSKUt-ZR`kf|ff<0On2n)EnAqVanfjFlrijWsC8#1(CKwJ1_E~R1=UEQYuXLy-`-&%9vTu02'
        'C12l}GBB<09-~){w%FeR&8|N~C^=s*1wt5E<$%zf@=$2r7BE<23<`~WAYhhIu&>HnU9^4SUAr?;VO=$H13ZIvM`3j2X-dS%2~&kH'
        'Mqlvhh~hW=yh@+0_^D&XwC({T2}|7B;NB_gw_4k8W$9;|$Aei_%VmHE;wtjo8(mV;kGMs+ONb*D<nUnv@x#R6L##!?y&}xYfh`DU'
        'x1O%9CH}9MAQxDq6?q<8EDtoxGSb0dBwgdofut9OQG%5KZ!2Lx+L{8*;>{+sC(3(*;DhO=E~jPi2$o~1O@2~{;3xMenpLEyouItC'
        'gd4zNpvuZp3-=4EOU^js!BH^-1BhwiI_<z!sC-NZrm}XFrB%BqIem$eaii3LOz4{W!qC&4@E4fj4{lIV-#85ZW{?6&VZg&jfU(QI'
        'j}f>Wp>35QQeVkH?yY>1laL!5sB!%S;`~&*=Xh0(6NTa2C;;bZ)vS}Lp%qKFbW0QsZV_k}mm@Vf$tsQG*cU<_kJKV)Um4f6cSs=H'
        '#@N}@2a8~58+Q_b!cmPoS-MzownoD9tou+V8hlXkD+vd~=3O+@jcn9GJxbm#=~YG(0993pmQFx%JnCuRwqwL;-EsHELMruir-*Ud'
        'J4AdFfGV}K9yizq)p-8XhUqQQgrbz4n8iMhO(<o=qRzR2dy2^(b=r-`s`1e^i@>IJPj?WNVv@)m*VB`DxDa_Lj<Z5^%<mwpsw$Bi'
        'fGLwshYT0IyC?KCt8%g}MFC)1@YbG2jHXl8DJyc((}MY*L}kKoPHp%q%ee?Vem82cvY6Bk%Pcs`S!;CYjw+^KS^&YuHnF#Ous$vG'
        'IUd&N2FXZkWV^)6vkNF~JKCgk)2_PuF~Xmq`ZyK;nPZl4RA6<(bPWQ!Iw)%T;BmTmr&KyrdNrH*<6M3Wr>tJOsb)CF0u7xF{v@q&'
        '#OEp)l&ju^OrvqFkOR)tk~}iKD@G`Hd~lk(*;SEUfK$PhHJk<6-T8{*nbeDgjrJ-x8Up=59D@=pbfZLC{AdAf7CMf`b$Q@iZT{J&'
        'W2;d#de)j&U2!0Ag%DpsW8(lkXB3~V%inF*QJbTVG?K*o4$7D`$B>*KP>gDnyq5E0v2CgPF6T-H0!&rn)jr8kUTV5<EAATcg;S{U'
        'yfi*+m-f1Apy{>K$=Jmz<f&jdkZ|aad8upijPhXC8BMNp=ZadUg|*oA=#aA^-;0)=OAS((Om2%~Q}wUUwOZ`G$CGoMZEfVk7x1aP'
        'jbk&X9vZ4M_Z;ib%ULxAq_1+lwzZ5c>&)$B{X7;|BiT6@_a4Xf+?5RFQ?~fi>DWaoJ7oaULdI<36lUf6+q+vhu~EKkQ@Ys{;TE&-'
        '>bU~}N+nt&y$3#In38O>yPHFka@*4tr>?ui#%JMgGt{q+*e?;p^vwQajK+EadXjel_3Lq(&Ia33asWU%u9-(s+Pb<UzT~IOeE|j8'
        'a-1(Q&aX~>e2l`|LQUyBFB_X~6Tjqwc-%LNym@$w=S=J#;U+Qsg2iVyD;;dZXB#l^Df3`;j}^hUGe>Gm$uOrV!|mU3mMWnC?1|z9'
        'RQCDhBmdNBPBy!CR@tR9m|KbMCU<b%f{GVuZNI!HrXtYJQf;egN{?TyF&?H)vu-dbi;y)X&EI?^YC2`SSW0W{<k<!km}k_sr(3$o'
        'VNcLy)iYmIPrwx-@;(l()0HLAX?8zZEj+VAH>=JCUFZ4%-7rQwyE9*25Rz?H=4w$MSE}>)YMkJ=v{-vn{R%W)42->NuBNFSsVZGg'
        ';A9729dj&-WW7L7>jO-zvw?r8$Y$+EwCrx(j+RsiV`DXsEBvDZP^!2>vXqM*CDd@I1o5%n4X66(T@m6Axk8q#miE_p;i1eT^WA$W'
        'MA;K{3*Wl1j#q(<2m@o+wz)8pD)}g7NpV;f*=cSq&EttGM8~KztOs(F<nhyy<?CUcrKC6^0B)Q5XGMb#`HekUr6UW>)pjP{?L*gx'
        'auJ<8ZTAH%MS3w?Ls?-%N_!1iiUS<FT4;y|AN9g9r)}d`3nDV|<$!C<gaceHS3`*U#*ZFE%W>w<K+;tkiMKc~N)xfxiT8KiIUc0*'
        'YNK#I*N#lCEGTccZTOXX_$OEb-{E+Z%~IFNOe^cjiS#ZQJ~@#e;V1E1L9INV4=lVulAU9E&IXk8h`y1G8PJTRRo<M<M5|oEBusuh'
        'c}IuAvTI%aWbH1CGy$JT4j~rBF{`=jgp#Vg#5MtC`LI#LBpGMQDqgCL_vty`!V6gAubCUOcGAF(KP^KnEpzFdb5a9F&p3_m2ByoE'
        '@E+%d2s{XD@zUq|?}P`cW_}zl@Um4&D!RD$v*^TmAeaDU@E<n;P9n%D$X&_LnuN+m_*xnQF9Y2$olWLtz0KY>T}T3oK1m(a2yR=V'
        'V*;O@eC>=;pvSr^p-V8zeD%-M6^KF_e!W7#wmb<gbNemR3BM_AAU_gwR`t?VXS40j)D!LY7z<uwk^kY8OXp>!SAL&v0yclj(i&IF'
        'DhM?KGj6j3c~!%jR5MFbRW-uK*%i5=SF)YQ+SnderPU{NbX7|imq&(L2PRp*1fpr{#m8D8BGj&D%fZbKj;CjuoAy0I%hB<)OF4Y~'
        '0C{;s#0nejBUGh!J)2ICZNR@Z!P~$}vvC;wDZz4P5ihYcv?RW?aJHnBW}M0h#+ZD`^WQ|SjK-2avS{Ae3g1j~9<!#9hIM?}LHe~='
        '&$wl;$Srmfm*c#)CZn((sTZYLq(@?OYh<Lm+3UD@o2j!|`~S-hRvZ;>%+w}pp7b+yv8EumIpDR$SuN8wEAh-!NsB%;6?a)Qy1K?('
        'mV;+EWId%bnv=SAQ%&x0PsR}hfJ!jbnYyFH>=q%*WeXWy`3m&{S?RIXUcWELq#c&?Qbn}9!9@O&4J_Nu*XN4L*~g2ngWFG_L9bRK'
        '9F3L>HyEwV!x+$o&-}J6hl9<c`6@QfrHDf6PDePZ^q=h@$5MuJfW3)+kYnj=tZseI#jPbG$A#NVy3PR?azm$s!3|Wk*~Y6T#4{m%'
        '%%AYM^5VqY7c=J4H0HvAIl+O4_yM~EYzgJYgzb;{bb(yAKJ*rq=dJ<|3v=>4SKIY$nmx74E5`SB0ZQ`<B|_xgCy^^xm0b%}(^(af'
        '#LYlF_APg|WU{CqWT!5Jb+Y&65~eN>P($;n`~1k}+Dtk8tW(0DeL@&<u+>>$S`=}A@i?(oySDuiWaC!7uauF;^O)ipAFj-p&N!u+'
        'ojNTZYo#-a-$?UXyd?3knAuG6E-$5s0q<Z<<Ygs@^Vk+prPs#J-58ZXc6%(IsHDqK;=#aP!Y;2}%&y{G-z77d^0q?ww_r3Ar!<nJ'
        '8Sbh(Mk&ZIO=KL><jUf#hjMJ&ubf<m??<kN()0-?tF<)Ix`j0Dev2(iH1wN(tk*bSR^++gRnRR=Cy(`LXL?8;OSbQeH5Kbq)wbG1'
        'c}z-@`lYRYaT8d@CpCNLZ$t~{xHd^@R$AKQ5ne&D5KHcm-{B7VU8cFPu&Yg|ylY!`7IdD_4rN=8624!Z)300;QE*)$r-;&VPx<#-'
        'H1?OXnIrzwu)^x9Rjyifey4ja#;!kG4O5n9mY(DfSQcB#k`8-QI&(L~3v8(YtT_)W0==tUl~|cL#S<f&?)Ok8_Mdt!MbY0b6i3;d'
        '*wou+C)V((meyM@Xy+C@3|WaJi$zU0Cw+e;s5~_Nu35XnrNM{XHnV4PdgdKng@8*MqqG-aiI-<!!dZ6L`jD;(t;lPo9h+*k@uQ()'
        'bCR_QFaJ9Fm(r4VZah>s?H*!Lyj}#oU1_@xf{V~?j9%=yXDu;F>T9kkF0MBZ6kPk(b_#gi@xe6}uv=Gnudz^Q*nPf-J7u+6?!-aO'
        'QZH*Cl|j8+Z_cuY-yq;rTsN6P4vLm^vWxpaGy3n9*+uSjWYm&x<VGxB%5fB^l4M;;d3)m-iN}<W=W53*G$C2D?vx!JlK45yt<`?+'
        'B2%i{ouPQxpwg7#{Fl{fPZFabbe+dm)J=(2!uRF6X}!uZc8k4u<Ssmj<+7uYyaN{RlpQ_f%j0R%sIl6m4MmK4EmnH%hE-Zgv2{7V'
        '9v*oRG%*XmKU=T4kJ4*L%Ab(R%hi;RE!MN0OEI|s=2N^5{-CV3|54h+Wd$&`DwF1>!zk8?ZCM*HSyQWgl!`MgnY2Q;C*qT`DpLDK'
        'ZBn0XHrGkL^j8Ozt2*8BPZgYseRe4j_(z4tCHY=^T8oeN?9vSD{L8T`js&dz9*#%ly~uef8iRb~W66&eZ=ewFHK?Kk{$&#B9U1tW'
        'r9^scmac{}u7%eDUWeg07V$E=#jSS)fn>!iH~3m|`VDyM&Vu@567V^B{@fccmS23|#qu9?+XY|OL-#=2ue@0P-?;EXpXWd8)(Zny'
        '+gyFITzm0_(l}T?{Xl$e{POyp{{?sB3eN'
    ),
    'vendor/fast_kaggriculture/pyrandom.hpp': (
        'c-p;JZExa65dO}u80n<ez64|QPMmN$RsB$@q*0Wrm7<)_*b6K%Yi@TPLa+Sy&aPjvp{d$aS0J0&nc10V=Z#JWez@DqRm|E!yxIDa'
        '&LaXd!UbWBz{8FTNx0SObnpWYD*}YQP#&`lVG;x(p@7faXJNdt?)Aek6cyfs<Jq>2-<}DdAoTa<XFvuB{3sGinU#teCKx*<A-4XG'
        '2~#s!!78Q!QF~$)Zy{k(96Srtf`=G5+449{0<>jIMH~{XZcb%;5%V@aVMkz-2nics2CLk`?*(}2ksFkbh!p^N^#d90uYfWtz4_kr'
        'IrsNUoAQCOB`kQn0f}x?Cdra;RMP9}Ga@QwMB0Rf)Mv1Zc_=P5=b)$dm6F22AZ9}HB#<;_m)gN4k!lwiMMqmTCsDjZ*VaUHf$%rm'
        '2raN$@3!1uZhVMYKw9r83!)?>a2*JV7RqUb^n$W6pSD`e-w=co5qkEQ@U_(nB3}r&+oxBAlx;GPXmHg6T;vr`3ecr|-$+pLu<uED'
        'CVLaUYBUV>?!uv^WnN+$rsNv0-c_qpMAjAfb73$O+EdT~L%hgQ%y3J=gcM8*KEfY_$4X;Woscw&U{6VeL8tH_Z6%)Re6*jef?FBY'
        '>w1~~$KI1$Y~c<txB<IDT7dEnZjf4aL9JAQ{d6p$mQv!Bqyvyhkh=7WqFY7{nq%GU;zDT`5|c0R0$<4M-2ACF>pQSt7uiZox1mPy'
        'Os6*p>G9s7)qFb&bR$EbWlFQVEx=n6rb5$82}ae0f@gmWBV{3Z^#HB8t$U2gsrE5YG?w_dhFfUE%!P}K=TrFLjexO{-sAHVg7E9z'
        '-H-Ps{F#y90vtvD`Iq02+(adlyMdg0_JnoFP*8!RN|IqHXr07_4>0@qaR1Zq-bc6syAJW;yce1IxhKy5<cTrE!*0!Q;!k0jcA#mU'
        'ea^CqOlsLI{qe7C%EIO-$4Wc**$F8Zri)wI`gD^Y=$K9V^)-x4ok5eZ8w`eHJ2}bZ3{oz#2!`0UPI0Lt#+4&DkqKvc0%W;URQ;m6'
        'U138|%}J=Lx8)?DLe=-QvFzf!5Qf~}iL`))aiW@V(LGLNosWn#vJ(v)xJ};q8Qx*T6~o82Jsdgqcs%S|Hb&aqM2g|ydj}@AJ#r?K'
        '?w~*F+xWC>^Nj12=4N0zsFblWMKDcNk+SMVrexN6r5a9V&?&QxUKa!HxokyvZrZl2vXOc_Dpy`rH8Zi!!4&M;@r8&{kXRM+vS782'
        'N<hK=f}6~R7yRfdjB$@ez)cNf79Q?Jge~RDFq?P7_1#p_Dv!x}2Uo=uP5L|53@(1=KC)p-kT1Fi>oht>A?5J&PU#xjUAc@BDMi=t'
        'Z#jMOB}vDKw1K6w4vrLDLwAc-54(N$JjV<<dXv!^j>49rdfcd7p4j8L9WIi$q;xIQB4ayUZ;I$zr$t72&vk2kQJ21~2q_ne>UHZ@'
        'rX$^Ivj{FR71iL%3M@ANT6AfxdcMF1HW$@csM)B$RLMGHr`zxKx`SS#l2y}-Qe63kxzn>vjLtKo1~scgQt448q)NYv5kezaK=WP='
        'BbRB?kbN3I$FoNch%*@u?5;CT%;V8adwmJ(+Ju&6p>c~ToNNAo(RG#ms^Nz{*@bqy(TfYvjO<Ods5cSA|1!g2f6yHy8a_Pnas6}_'
        '$91i@;mxV*Th}_C8kX`osSJd&tGamr92#<KC6}YHKG!uh5c!nid~-ww!=XLyP5O=krTq_LD#zkK!*FQkPb0ri2k`;(^N<$i>OZ8v'
        '0I~T5L;'
    ),
}

EMBEDDED_ASSET_SHA256 = {
    'kaito_v27_main.py': 'f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8',
    'scripts/fast_kaggriculture.py': 'ba9c50a28d57af1d73605760064ddc10c0e6b22bfdbaec9367e6f7ce599821eb',
    'vendor/fast_kaggriculture/fast_sim.cpp': 'bd37778ad92103e35327ee6284cc6280b70b6456d16a8db7dc530f941f901c38',
    'vendor/fast_kaggriculture/sim.hpp': '4796e149e0cb96003ac24d7c7f47bfb27c87995dd5b1ea729a6ddd36255cd449',
    'vendor/fast_kaggriculture/pyrandom.hpp': '3cf452b176fee366539aae88d8b66efcdef0643e8fc531547321d386bebe9d4d',
}


BASE_RELATIVE = Path(
    "code_agents/kaggriculture_20260822_score_top30/"
    "027_kaitofukami__25-27-strict-future-v27-midgame-meta-reset/output/main.py"
)
COMPACT_BASE_RELATIVE = Path("kaito_v27_main.py")
FAST_RELATIVE = Path("scripts/fast_kaggriculture.py")
VENDOR_RELATIVE = Path("vendor/fast_kaggriculture")
VENDOR_FILES = ("fast_sim.cpp", "sim.hpp", "pyrandom.hpp")

WORK_ROOT = (
    Path("/kaggle/working/kaito_v27_sell_tutorial")
    if Path("/kaggle/working").is_dir()
    else Path.cwd() / "artifacts/kaito_v27_sell_tutorial"
)


def valid_asset_root(candidate: Path) -> Path | None:
    """Return the base-agent path when either supported asset layout is complete."""
    project_base = candidate / BASE_RELATIVE
    compact_base = candidate / COMPACT_BASE_RELATIVE
    base_path = project_base if project_base.is_file() else compact_base
    required = [candidate / FAST_RELATIVE]
    required.extend(candidate / VENDOR_RELATIVE / filename for filename in VENDOR_FILES)
    return base_path if base_path.is_file() and all(path.is_file() for path in required) else None


def unpack_embedded_assets() -> tuple[Path, Path] | None:
    """Materialize the generated notebook's compressed assets in writable storage."""
    payloads = globals().get("EMBEDDED_ASSETS", {})
    checksums = globals().get("EMBEDDED_ASSET_SHA256", {})
    if not payloads:
        return None

    asset_root = WORK_ROOT / "embedded_assets"
    for relative, payload in payloads.items():
        destination = asset_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        raw = zlib.decompress(base64.b85decode(payload.encode("ascii")))
        expected = checksums.get(relative)
        actual = hashlib.sha256(raw).hexdigest()
        if expected and actual != expected:
            raise RuntimeError(f"Embedded asset checksum mismatch: {relative}")
        if not destination.is_file() or destination.read_bytes() != raw:
            destination.write_bytes(raw)

    base_path = valid_asset_root(asset_root)
    if base_path is None:
        raise RuntimeError("The notebook's embedded runtime asset bundle is incomplete")
    return asset_root, base_path


def find_runtime_assets() -> tuple[Path, Path]:
    candidates: list[Path] = []
    if os.environ.get("KAGGRICULTURE_ROOT"):
        candidates.append(Path(os.environ["KAGGRICULTURE_ROOT"]))
    else:
        # Prefer the embedded, version-pinned bundle in the exported notebook.
        embedded = unpack_embedded_assets()
        if embedded is not None:
            return embedded

    candidates.extend([Path.cwd(), *Path.cwd().resolve().parents])
    candidates.append(Path("/kaggle/working/kagglericulture"))
    candidates.append(Path("/mnt/98cdaf31-9385-48dc-bb56-ec7db2148738/kagglericulture"))
    input_root = Path("/kaggle/input")
    if input_root.is_dir():
        for path in input_root.glob(f"**/{BASE_RELATIVE}"):
            candidates.append(path.parents[len(BASE_RELATIVE.parts) - 1])
        candidates.extend(path.parent for path in input_root.glob("**/kaito_v27_main.py"))

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        base_path = valid_asset_root(candidate)
        if base_path is not None:
            return candidate, base_path

    raise FileNotFoundError(
        "Required Kaito V27 tutorial assets were not found. Re-download the self-contained "
        "notebook, or set KAGGRICULTURE_ROOT to a project checkout containing the agent, "
        "scripts/fast_kaggriculture.py, and vendor/fast_kaggriculture sources."
    )


PROJECT_ROOT, BASE_PATH = find_runtime_assets()
RUNTIME_ROOT = WORK_ROOT / "runtime"
OUTPUT_ROOT = WORK_ROOT / "output"
(RUNTIME_ROOT / "scripts").mkdir(parents=True, exist_ok=True)
(RUNTIME_ROOT / "vendor/fast_kaggriculture").mkdir(parents=True, exist_ok=True)
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

shutil.copy2(PROJECT_ROOT / FAST_RELATIVE, RUNTIME_ROOT / FAST_RELATIVE)
for filename in VENDOR_FILES:
    shutil.copy2(
        PROJECT_ROOT / VENDOR_RELATIVE / filename,
        RUNTIME_ROOT / VENDOR_RELATIVE / filename,
    )

sys.path.insert(0, str(RUNTIME_ROOT / "scripts"))
fast = importlib.import_module("fast_kaggriculture")
fast.ensure_built()

# The tutorial starts with a Kaito V27 mirror to isolate the causal effect of changing only sales.
# Replace this path with another main.py to test a different opponent.
OPPONENT_PATH = BASE_PATH
print("project:", PROJECT_ROOT)
print("base:", BASE_PATH)
print("base sha256:", hashlib.sha256(BASE_PATH.read_bytes()).hexdigest())
print("output:", OUTPUT_ROOT)


SELLABLE = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
STATE_DIM = 5 + 4 * len(SELLABLE)   # 37
ACTION_DIM = 4 + 4 * len(SELLABLE)  # 36


def get_field(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


def clean_market(raw: Any) -> list[list[Any]]:
    return [list(order) for order in list(raw or [])[:10] if isinstance(order, (list, tuple)) and order]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def normalize_action(action: Any, hand_count: int) -> dict[str, Any]:
    action = action if isinstance(action, dict) else {}
    hands = [list(command or ["PASS"]) for command in list(action.get("hands") or [])[:hand_count]]
    hands.extend([["PASS"] for _ in range(hand_count - len(hands))])
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": hands,
        "market": clean_market(action.get("market")),
    }


def private_quantities(obs: dict[str, Any]) -> dict[str, int]:
    private = get_field(obs, "private", {}) or {}
    shed = get_field(private, "shed", {}) or {}
    quantities = {item: max(0, int(get_field(shed, item, 0) or 0)) for item in SELLABLE}
    for inventory in list(get_field(private, "inventories", []) or []):
        for item in SELLABLE:
            quantities[item] += max(0, int(get_field(inventory, item, 0) or 0))
    return quantities


def sell_quantities(market: list[list[Any]]) -> tuple[dict[str, int], dict[str, int]]:
    quantities = {item: 0 for item in SELLABLE}
    positions = {item: -1 for item in SELLABLE}
    for index, order in enumerate(clean_market(market)):
        if len(order) >= 3 and order[0] == "SELL" and order[1] in quantities:
            quantities[order[1]] += max(0, int(order[2]))
            if positions[order[1]] < 0:
                positions[order[1]] = index
    return quantities, positions


def generate_candidates(
    obs: dict[str, Any], seat: int, base_action: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    farms = list(get_field(obs, "farms", []) or [])
    base = normalize_action(base_action, len(list(get_field(farms[seat], "hands", []) or [])))
    baseline = clean_market(base["market"])
    non_sells = [copy.deepcopy(order) for order in baseline if order[0] != "SELL"]
    prices = get_field(get_field(obs, "market", {}) or {}, "prices", {}) or {}
    potential = private_quantities(obs)
    available = [item for item in SELLABLE if potential[item] > 0]
    ranked = sorted(
        available,
        key=lambda item: float(get_field(prices, item, 0) or 0) * potential[item],
        reverse=True,
    )

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(market: list[list[Any]], source: str) -> None:
        market = clean_market(market)
        digest = canonical(market)
        if digest in seen or len(candidates) >= CFG.max_candidates:
            return
        seen.add(digest)
        candidates.append({"market": market, "source": source})

    add(baseline, "baseline")
    add(non_sells, "hold")
    add(non_sells + [["SELL", item, potential[item]] for item in ranked], "liquidate_value")
    add(non_sells + [["SELL", item, potential[item]] for item in reversed(ranked)], "liquidate_reverse")
    for item in ranked[:4]:
        add(non_sells + [["SELL", item, potential[item]]], "full_" + item)
        if potential[item] >= 2:
            add(non_sells + [["SELL", item, potential[item] // 2]], "half_" + item)
    return base, candidates


print("state/action dims:", STATE_DIM, ACTION_DIM)


def state_features(
    obs: dict[str, Any], seat: int, base_market: list[list[Any]]
) -> np.ndarray:
    farms = list(get_field(obs, "farms", []) or [])
    own = farms[seat]
    opponent = farms[1 - seat]
    own_money = float(get_field(own, "money", 0) or 0)
    opponent_money = float(get_field(opponent, "money", 0) or 0)
    market = get_field(obs, "market", {}) or {}
    prices = get_field(market, "prices", {}) or {}
    inventory = get_field(market, "inventory", {}) or {}
    potential = private_quantities(obs)
    baseline, _ = sell_quantities(base_market)
    values = [
        float(get_field(obs, "step", 0) or 0) / 719.0,
        float(seat),
        math.tanh((own_money - opponent_money) / 20_000.0),
        math.log1p(max(0.0, own_money)) / 12.0,
        math.log1p(max(0.0, opponent_money)) / 12.0,
    ]
    for item in SELLABLE:
        values.extend(
            [
                math.log1p(max(1.0, float(get_field(prices, item, 1) or 1))) / 7.0,
                math.tanh((float(get_field(inventory, item, 10_000) or 10_000) - 10_000.0) / 1_000.0),
                math.log1p(potential[item]) / 5.0,
                math.log1p(baseline[item]) / 5.0,
            ]
        )
    return np.asarray(values, dtype=np.float32)


def action_features(
    obs: dict[str, Any], base_market: list[list[Any]], candidate_market: list[list[Any]]
) -> np.ndarray:
    potential = private_quantities(obs)
    baseline, _ = sell_quantities(base_market)
    quantities, positions = sell_quantities(candidate_market)
    clean = clean_market(candidate_market)
    values = [
        len(clean) / 10.0,
        sum(order[0] == "SELL" for order in clean) / 8.0,
        min(2.0, sum(quantities.values()) / 100.0),
        float(canonical(clean) == canonical(clean_market(base_market))),
    ]
    for item in SELLABLE:
        quantity = quantities[item]
        delta = quantity - baseline[item]
        values.extend(
            [
                math.log1p(quantity) / 5.0,
                min(2.0, quantity / max(1.0, potential[item])),
                0.0 if positions[item] < 0 else (positions[item] + 1) / 10.0,
                math.copysign(math.log1p(abs(delta)) / 5.0, delta),
            ]
        )
    return np.asarray(values, dtype=np.float32)


assert STATE_DIM == 37
assert ACTION_DIM == 36


class PolicyValueNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.state_encoder = nn.Sequential(
            nn.Linear(STATE_DIM, 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU()
        )
        self.action_encoder = nn.Sequential(
            nn.Linear(ACTION_DIM, 48), nn.ReLU(), nn.Linear(48, 32), nn.ReLU()
        )
        self.joint_encoder = nn.Sequential(
            nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 48), nn.ReLU()
        )
        self.policy_head = nn.Linear(48, 1)
        self.candidate_class_head = nn.Linear(48, 3)
        self.candidate_margin_head = nn.Linear(48, 1)
        self.value_head = nn.Linear(32, 3)
        nn.init.zeros_(self.policy_head.weight)
        nn.init.zeros_(self.policy_head.bias)
        nn.init.zeros_(self.candidate_class_head.weight)
        nn.init.zeros_(self.candidate_class_head.bias)
        nn.init.zeros_(self.candidate_margin_head.weight)
        nn.init.zeros_(self.candidate_margin_head.bias)
        nn.init.zeros_(self.value_head.weight)
        nn.init.zeros_(self.value_head.bias)

    def forward(
        self, state: torch.Tensor, actions: torch.Tensor, mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        state_latent = self.state_encoder(state)
        action_latent = self.action_encoder(actions)
        repeated_state = state_latent.unsqueeze(1).expand(-1, actions.shape[1], -1)
        joint = self.joint_encoder(torch.cat([repeated_state, action_latent], dim=-1))
        logits = self.policy_head(joint).squeeze(-1)
        logits = logits.masked_fill(~mask, torch.finfo(logits.dtype).min)
        value_logits = self.value_head(state_latent)
        candidate_class_logits = self.candidate_class_head(joint)
        candidate_margin = torch.tanh(self.candidate_margin_head(joint)).squeeze(-1)
        candidate_class_logits = candidate_class_logits.masked_fill(~mask.unsqueeze(-1), 0.0)
        candidate_margin = candidate_margin.masked_fill(~mask, 0.0)
        return logits, value_logits, candidate_class_logits, candidate_margin


def candidate_scores(
    candidate_class_logits: torch.Tensor, candidate_margin: torch.Tensor
) -> torch.Tensor:
    probabilities = torch.softmax(candidate_class_logits, dim=-1)
    expected_class = probabilities[..., 2] - probabilities[..., 0]
    return (
        expected_class + CFG.margin_weight * candidate_margin
    ) / (1.0 + CFG.margin_weight)


@torch.inference_mode()
def predict(
    model: PolicyValueNet, state: np.ndarray, actions: np.ndarray
) -> tuple[np.ndarray, float, np.ndarray]:
    model.eval()
    device = next(model.parameters()).device
    state_tensor = torch.from_numpy(state).to(device).unsqueeze(0)
    action_tensor = torch.from_numpy(actions).to(device).unsqueeze(0)
    mask = torch.ones((1, len(actions)), dtype=torch.bool, device=device)
    logits, value_logits, candidate_class_logits, candidate_margin = model(
        state_tensor, action_tensor, mask
    )
    priors = torch.softmax(logits[0], dim=0).cpu().numpy()
    value_probabilities = torch.softmax(value_logits[0], dim=-1)
    expected_value = value_probabilities[2] - value_probabilities[0]
    scores = candidate_scores(candidate_class_logits[0], candidate_margin[0])
    return priors, float(expected_value.item()), scores.cpu().numpy()


model = PolicyValueNet()
INITIAL_MODEL_STATE = {
    name: tensor.detach().cpu().clone()
    for name, tensor in model.state_dict().items()
}
optimizer = torch.optim.AdamW(model.parameters(), lr=CFG.learning_rate, weight_decay=1e-4)
scaler = torch.amp.GradScaler("cuda", enabled=DEVICE.type == "cuda")
print(model)


def outcome_value(margin: float) -> float:
    return 1.0 if margin > 0 else -1.0 if margin < 0 else 0.0


def game_score(margin: float) -> float:
    return 0.5 * (outcome_value(margin) + 1.0)


def search_utility(margin: float) -> float:
    """Win/draw/loss dominates; a small margin term only ranks equal outcomes."""
    outcome = outcome_value(margin)
    secondary = CFG.margin_weight * math.tanh(margin / CFG.margin_scale)
    return (outcome + secondary) / (1.0 + CFG.margin_weight)


def replace_market(base_action: dict[str, Any], market: list[list[Any]]) -> dict[str, Any]:
    result = copy.deepcopy(base_action)
    result["market"] = copy.deepcopy(market)
    return result


def restore_agent_states(states: list[Any]) -> None:
    for state in states:
        fast.restore_policy_state(state)


def root_puct_search(
    root_handle: Any,
    observations: list[dict[str, Any]],
    root_actions: list[dict[str, Any]],
    agents: list[Any],
    agent_states: list[Any],
    seat: int,
    model: PolicyValueNet,
    explore: bool,
) -> dict[str, Any]:
    ffi, lib = fast.bindings()
    base, candidates = generate_candidates(observations[seat], seat, root_actions[seat])
    state = state_features(observations[seat], seat, base["market"])
    action_matrix = np.stack(
        [action_features(observations[seat], base["market"], row["market"]) for row in candidates]
    )
    priors, network_value, network_scores = predict(model, state, action_matrix)
    if explore and len(priors) > 1:
        noise = np.random.dirichlet([CFG.root_dirichlet_alpha] * len(priors))
        priors = (1.0 - CFG.root_noise_fraction) * priors + CFG.root_noise_fraction * noise

    visits = np.zeros(len(candidates), dtype=np.int32)
    value_sum = np.zeros(len(candidates), dtype=np.float64)
    observed_margins: list[list[float]] = [[] for _ in candidates]
    for _ in range(CFG.mcts_simulations):
        q = np.divide(value_sum, visits, out=np.zeros_like(value_sum), where=visits > 0)
        unvisited = np.flatnonzero(visits == 0)
        if len(unvisited):
            # Give every root candidate at least one real terminal rollout.
            first_visit = np.log(priors[unvisited].clip(min=1e-12)) + 0.25 * network_scores[unvisited]
            chosen = int(unvisited[np.argmax(first_visit)])
        else:
            exploration = (
                CFG.c_puct * priors * math.sqrt(1.0 + visits.sum()) / (1.0 + visits)
            )
            chosen = int(np.argmax(q + exploration))

        restore_agent_states(agent_states)
        handle = lib.fs_clone(root_handle)
        snapshot = ffi.new("FSSnapshot *")
        joint = copy.deepcopy(root_actions)
        joint[seat] = replace_market(base, candidates[chosen]["market"])
        try:
            encoded = [fast.encode_action(action, ffi) for action in joint]
            lib.fs_step(handle, encoded[0], encoded[1])
            while True:
                lib.fs_snapshot(handle, snapshot)
                if snapshot.done:
                    break
                rollout_obs = fast.observations(snapshot)
                rollout_actions = [fast._call(agents[index], rollout_obs[index]) for index in (0, 1)]
                encoded = [fast.encode_action(action, ffi) for action in rollout_actions]
                lib.fs_step(handle, encoded[0], encoded[1])
            margin = float(snapshot.farms[seat].money - snapshot.farms[1 - seat].money)
        finally:
            lib.fs_destroy(handle)
        visits[chosen] += 1
        value_sum[chosen] += search_utility(margin)
        observed_margins[chosen].append(margin)

    restore_agent_states(agent_states)
    target_policy = visits.astype(np.float64) / visits.sum()
    terminal_margins = np.asarray(
        [float(np.mean(values)) for values in observed_margins], dtype=np.float32
    )
    baseline_score = game_score(float(terminal_margins[0]))
    relative_classes = np.asarray(
        [
            2 if game_score(float(margin)) > baseline_score
            else 0 if game_score(float(margin)) < baseline_score
            else 1
            for margin in terminal_margins
        ],
        dtype=np.int64,
    )
    relative_margin = np.tanh(
        (terminal_margins - terminal_margins[0]) / CFG.margin_scale
    ).astype(np.float32)
    return {
        "base": base,
        "candidates": candidates,
        "state": state,
        "actions": action_matrix,
        "priors": priors,
        "network_value": network_value,
        "network_scores": network_scores,
        "visits": visits,
        "q": np.divide(value_sum, visits, out=np.zeros_like(value_sum), where=visits > 0),
        "target_policy": target_policy.astype(np.float32),
        "terminal_margins": terminal_margins,
        "candidate_class": relative_classes,
        "candidate_margin": relative_margin,
        # WDL changes are rare; a meaningful margin change also makes this an informative root.
        "actionable": bool(
            np.any(relative_classes != 1) or np.max(np.abs(relative_margin)) > 0.01
        ),
    }


def play_training_game(
    opponent_path: Path, seed: int, seat: int, model: PolicyValueNet
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ffi, lib = fast.bindings()
    paths = [opponent_path, opponent_path]
    paths[seat] = BASE_PATH
    agents = [fast.load_agent(str(path)) for path in paths]
    handle = lib.fs_create(seed)
    snapshot = ffi.new("FSSnapshot *")
    records: list[dict[str, Any]] = []
    try:
        while True:
            lib.fs_snapshot(handle, snapshot)
            if snapshot.done:
                break
            observations = fast.observations(snapshot)
            joint = [fast._call(agents[index], observations[index]) for index in (0, 1)]
            step = int(snapshot.step)
            if step >= CFG.start_step:
                agent_states = [fast.snapshot_policy_state(agent) for agent in agents]
                search = root_puct_search(
                    handle, observations, joint, agents, agent_states, seat, model, explore=True
                )
                chosen = int(np.random.choice(len(search["target_policy"]), p=search["target_policy"]))
                joint[seat] = replace_market(
                    search["base"], search["candidates"][chosen]["market"]
                )
                records.append(
                    {
                        "state": search["state"],
                        "actions": search["actions"],
                        "policy": search["target_policy"],
                        "candidate_class": search["candidate_class"],
                        "candidate_margin": search["candidate_margin"],
                        "actionable": search["actionable"],
                        "value": 0.0,
                        "metadata": {
                            "seed": seed,
                            "seat": seat,
                            "step": step,
                            "chosen": chosen,
                            "sources": [row["source"] for row in search["candidates"]],
                            "visits": search["visits"].tolist(),
                            "q": search["q"].tolist(),
                            "terminal_margins": search["terminal_margins"].tolist(),
                            "relative_classes": search["candidate_class"].tolist(),
                            "actionable": search["actionable"],
                        },
                    }
                )
            encoded = [fast.encode_action(action, ffi) for action in joint]
            lib.fs_step(handle, encoded[0], encoded[1])
        lib.fs_snapshot(handle, snapshot)
        rewards = [float(snapshot.farms[index].money) for index in (0, 1)]
    finally:
        lib.fs_destroy(handle)

    final_value = outcome_value(rewards[seat] - rewards[1 - seat])
    for record in records:
        record["value"] = final_value
    return records, {
        "seed": seed,
        "seat": seat,
        "reward": rewards[seat],
        "opponent_reward": rewards[1 - seat],
        "margin": rewards[seat] - rewards[1 - seat],
        "outcome": final_value,
        "samples": len(records),
        "actionable_samples": sum(int(record["actionable"]) for record in records),
    }


def collect_round(model: PolicyValueNet) -> tuple[list[dict[str, Any]], pd.DataFrame]:
    model.to("cpu").eval()
    records: list[dict[str, Any]] = []
    games = []
    tasks = [(seed, seat) for seed in CFG.train_seeds for seat in (0, 1)]
    started = time.perf_counter()
    for index, (seed, seat) in enumerate(tasks, 1):
        game_records, report = play_training_game(OPPONENT_PATH, seed, seat, model)
        records.extend(game_records)
        games.append(report)
        print(f"game {index}/{len(tasks)} seed={seed} seat={seat} samples={len(game_records)}")
    print(f"round complete: games={len(tasks)} samples={len(records)} elapsed={time.perf_counter()-started:.1f}s")
    return records, pd.DataFrame(games)


def pack_records(records: list[dict[str, Any]]) -> tuple[torch.Tensor, ...]:
    count = len(records)
    states = np.zeros((count, STATE_DIM), dtype=np.float32)
    actions = np.zeros((count, CFG.max_candidates, ACTION_DIM), dtype=np.float32)
    masks = np.zeros((count, CFG.max_candidates), dtype=bool)
    policies = np.zeros((count, CFG.max_candidates), dtype=np.float32)
    values = np.zeros(count, dtype=np.float32)
    candidate_classes = np.ones((count, CFG.max_candidates), dtype=np.int64)
    candidate_margins = np.zeros((count, CFG.max_candidates), dtype=np.float32)
    actionable = np.zeros(count, dtype=bool)
    for index, record in enumerate(records):
        candidate_count = len(record["actions"])
        states[index] = record["state"]
        actions[index, :candidate_count] = record["actions"]
        masks[index, :candidate_count] = True
        policies[index, :candidate_count] = record["policy"]
        values[index] = record["value"]
        candidate_classes[index, :candidate_count] = record["candidate_class"]
        candidate_margins[index, :candidate_count] = record["candidate_margin"]
        actionable[index] = record["actionable"]
    return tuple(
        torch.from_numpy(array)
        for array in (
            states, actions, masks, policies, values,
            candidate_classes, candidate_margins, actionable,
        )
    )


def balanced_weights(classes: torch.Tensor, class_count: int = 3) -> torch.Tensor:
    counts = torch.bincount(classes, minlength=class_count)
    present = counts > 0
    weights = torch.zeros(class_count, dtype=torch.float32)
    weights[present] = counts.sum() / (present.sum() * counts[present])
    print("class counts/weights:", counts.tolist(), [round(x, 4) for x in weights.tolist()])
    return weights.to(DEVICE)


def train_once(model: PolicyValueNet, records: list[dict[str, Any]]) -> pd.DataFrame:
    tensors = pack_records(records)
    value_weights = balanced_weights((tensors[4] + 1).long())
    candidate_weights = balanced_weights(tensors[5][tensors[2]])
    loader = DataLoader(
        TensorDataset(*tensors),
        batch_size=CFG.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=DEVICE.type == "cuda",
    )
    model.to(DEVICE).train()
    rows = []
    for epoch in range(CFG.epochs_per_iteration):
        totals = {
            "policy": 0.0,
            "value": 0.0,
            "candidate_class": 0.0,
            "candidate_margin": 0.0,
            "candidate_top1": 0.0,
            "loss": 0.0,
            "count": 0,
        }
        for (
            state, actions, mask, target_policy, target_value,
            target_candidate_class, target_candidate_margin, actionable,
        ) in loader:
            state = state.to(DEVICE, non_blocking=True)
            actions = actions.to(DEVICE, non_blocking=True)
            mask = mask.to(DEVICE, non_blocking=True)
            target_policy = target_policy.to(DEVICE, non_blocking=True)
            target_value = target_value.to(DEVICE, non_blocking=True)
            target_candidate_class = target_candidate_class.to(DEVICE, non_blocking=True)
            target_candidate_margin = target_candidate_margin.to(DEVICE, non_blocking=True)
            actionable = actionable.to(DEVICE, non_blocking=True)
            sample_weight = torch.where(
                actionable,
                torch.full_like(target_value, CFG.actionable_sample_weight),
                torch.ones_like(target_value),
            )
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=DEVICE.type == "cuda"):
                logits, value_logits, class_logits, predicted_margin = model(
                    state, actions, mask
                )
                policy_loss = -(target_policy * F.log_softmax(logits, dim=1)).sum(dim=1).mean()
                value_class = (target_value + 1).long()
                value_loss = F.cross_entropy(value_logits, value_class, weight=value_weights)
                class_element = F.cross_entropy(
                    class_logits.transpose(1, 2),
                    target_candidate_class,
                    weight=candidate_weights,
                    reduction="none",
                )
                margin_element = F.smooth_l1_loss(
                    predicted_margin, target_candidate_margin, reduction="none"
                )
                mask_float = mask.to(predicted_margin.dtype)
                per_sample_denominator = mask_float.sum(dim=1).clamp_min(1.0)
                class_per_sample = (
                    (class_element * mask_float).sum(dim=1) / per_sample_denominator
                )
                margin_per_sample = (
                    (margin_element * mask_float).sum(dim=1) / per_sample_denominator
                )
                candidate_class_loss = (
                    class_per_sample * sample_weight
                ).sum() / sample_weight.sum()
                candidate_margin_loss = (
                    margin_per_sample * sample_weight
                ).sum() / sample_weight.sum()
                predicted_scores = candidate_scores(class_logits, predicted_margin)
                target_scores = (
                    target_candidate_class.to(predicted_scores.dtype) - 1.0
                    + CFG.margin_weight * target_candidate_margin
                ) / (1.0 + CFG.margin_weight)
                predicted_best = predicted_scores.masked_fill(~mask, -1e9).argmax(dim=1)
                predicted_target = target_scores.gather(
                    1, predicted_best.unsqueeze(1)
                ).squeeze(1)
                best_target = target_scores.masked_fill(~mask, -1e9).max(dim=1).values
                candidate_top1 = (predicted_target >= best_target - 1e-6).float().mean()
                loss = (
                    policy_loss
                    + CFG.value_loss_weight * value_loss
                    + CFG.candidate_class_loss_weight * candidate_class_loss
                    + CFG.candidate_margin_loss_weight * candidate_margin_loss
                )
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(optimizer)
            scaler.update()
            batch = len(state)
            for key, tensor in (
                ("policy", policy_loss),
                ("value", value_loss),
                ("candidate_class", candidate_class_loss),
                ("candidate_margin", candidate_margin_loss),
                ("candidate_top1", candidate_top1),
                ("loss", loss),
            ):
                totals[key] += float(tensor.detach()) * batch
            totals["count"] += batch
        row = {
            key: totals[key] / totals["count"]
            for key in (
                "policy", "value", "candidate_class", "candidate_margin",
                "candidate_top1", "loss",
            )
        }
        row["epoch"] = epoch + 1
        rows.append(row)
        print(
            f"epoch {epoch+1}/{CFG.epochs_per_iteration} "
            f"loss={row['loss']:.4f} policy={row['policy']:.4f} "
            f"value={row['value']:.4f} candidate_class={row['candidate_class']:.4f} "
            f"candidate_margin={row['candidate_margin']:.4f} "
            f"candidate_top1={row['candidate_top1']:.3f}"
        )
    return pd.DataFrame(rows)


round_buffers: list[list[dict[str, Any]]] = []
all_game_reports = []
all_training_reports = []

for iteration in range(CFG.expert_iterations):
    print(f"\n========== Expert Iteration {iteration+1}/{CFG.expert_iterations} ==========")

    # A. The current model guides MCTS and produces a new data round.
    new_records, game_report = collect_round(model)
    round_buffers.append(new_records)
    round_buffers = round_buffers[-CFG.replay_rounds :]

    # Expand the first record to see how MCTS converts candidates into Policy targets.
    first = new_records[0]
    print("first sample tensors:", first["state"].shape, first["actions"].shape)
    display(
        pd.DataFrame(
            {
                "source": first["metadata"]["sources"],
                "visits": first["metadata"]["visits"],
                "target_policy": first["policy"],
                "mcts_q": first["metadata"]["q"],
                "terminal_margin": first["metadata"]["terminal_margins"],
                "relative_label": [
                    ("worse", "same", "better")[value]
                    for value in first["candidate_class"]
                ],
                "margin_target": first["candidate_margin"],
                "chosen": [index == first["metadata"]["chosen"] for index in range(len(first["policy"]))],
            }
        )
    )

    # B. Flatten the recent replay rounds and update the same model.
    training_records = [record for one_round in round_buffers for record in one_round]
    print("new samples:", len(new_records), "training-window samples:", len(training_records))
    training_report = train_once(model, training_records)

    # C. Save the round so every generated target remains auditable.
    game_report["iteration"] = iteration + 1
    training_report["iteration"] = iteration + 1
    all_game_reports.append(game_report)
    all_training_reports.append(training_report)
    torch.save(model.to("cpu").state_dict(), OUTPUT_ROOT / f"model_iter{iteration+1}.pt")
    np.savez_compressed(
        OUTPUT_ROOT / f"records_iter{iteration+1}.npz",
        states=pack_records(new_records)[0].numpy(),
        values=pack_records(new_records)[4].numpy(),
        candidate_classes=pack_records(new_records)[5].numpy(),
        candidate_margins=pack_records(new_records)[6].numpy(),
        metadata=np.asarray([json.dumps(row["metadata"], separators=(",", ":")) for row in new_records]),
    )

game_history = pd.concat(all_game_reports, ignore_index=True)
training_history = pd.concat(all_training_reports, ignore_index=True)
display(game_history)
display(training_history)


@torch.inference_mode()
def choose_with_network(
    model: PolicyValueNet,
    obs: dict[str, Any],
    seat: int,
    base_action: dict[str, Any],
    threshold: float,
) -> tuple[dict[str, Any], bool, float]:
    base, candidates = generate_candidates(obs, seat, base_action)
    if len(candidates) <= 1:
        return base, False, 0.0
    state = state_features(obs, seat, base["market"])
    actions = np.stack([action_features(obs, base["market"], row["market"]) for row in candidates])
    _, _, scores = predict(model, state, actions)
    chosen = int(np.argmax(scores))
    advantage = float(scores[chosen] - scores[0])
    if advantage < threshold:
        chosen = 0
    return replace_market(base, candidates[chosen]["market"]), chosen != 0, advantage


def play_policy_game(
    policy_model: PolicyValueNet, seed: int, seat: int, threshold: float
) -> dict[str, Any]:
    ffi, lib = fast.bindings()
    paths = [OPPONENT_PATH, OPPONENT_PATH]
    paths[seat] = BASE_PATH
    agents = [fast.load_agent(str(path)) for path in paths]
    handle = lib.fs_create(seed)
    snapshot = ffi.new("FSSnapshot *")
    changed_steps = 0
    advantages = []
    try:
        while True:
            lib.fs_snapshot(handle, snapshot)
            if snapshot.done:
                break
            observations = fast.observations(snapshot)
            joint = [fast._call(agents[index], observations[index]) for index in (0, 1)]
            if int(snapshot.step) >= CFG.start_step:
                joint[seat], changed, advantage = choose_with_network(
                    policy_model, observations[seat], seat, joint[seat], threshold
                )
                changed_steps += int(changed)
                advantages.append(advantage)
            encoded = [fast.encode_action(action, ffi) for action in joint]
            lib.fs_step(handle, encoded[0], encoded[1])
        lib.fs_snapshot(handle, snapshot)
        rewards = [float(snapshot.farms[index].money) for index in (0, 1)]
    finally:
        lib.fs_destroy(handle)
    margin = rewards[seat] - rewards[1 - seat]
    score = 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5
    return {
        "margin": margin,
        "score": score,
        "changed_steps": changed_steps,
        "mean_advantage": float(np.mean(advantages)) if advantages else 0.0,
    }


def paired_evaluation(
    policy_model: PolicyValueNet,
    seeds: tuple[int, ...],
    thresholds: list[float],
    split: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    policy_model.to("cpu").eval()
    rows = []
    for seed in seeds:
        for seat in (0, 1):
            baseline_paths = [str(OPPONENT_PATH), str(OPPONENT_PATH)]
            baseline_paths[seat] = str(BASE_PATH)
            baseline = fast.run_fast_game(tuple(baseline_paths), seed)
            baseline_margin = baseline[f"reward_{seat}"] - baseline[f"reward_{1-seat}"]
            baseline_score = game_score(baseline_margin)
            for threshold in thresholds:
                treatment = play_policy_game(policy_model, seed, seat, threshold)
                rows.append(
                    {
                        "split": split,
                        "seed": seed,
                        "seat": seat,
                        "threshold": threshold,
                        "baseline_score": baseline_score,
                        "treatment_score": treatment["score"],
                        "score_delta": treatment["score"] - baseline_score,
                        "margin_delta": treatment["margin"] - baseline_margin,
                        "changed_steps": treatment["changed_steps"],
                        "mean_advantage": treatment["mean_advantage"],
                    }
                )
    detail = pd.DataFrame(rows)
    summary = detail.groupby("threshold").agg(
        games=("score_delta", "size"),
        changed_games=("changed_steps", lambda values: int((values > 0).sum())),
        improved=("score_delta", lambda values: int((values > 0).sum())),
        regressed=("score_delta", lambda values: int((values < 0).sum())),
        score_gain=("score_delta", "sum"),
        avg_score_delta=("score_delta", "mean"),
        avg_margin_delta=("margin_delta", "mean"),
        avg_predicted_advantage=("mean_advantage", "mean"),
    ).reset_index()
    summary.insert(0, "split", split)
    summary["net"] = summary["improved"] - summary["regressed"]
    return summary, detail


# A. Compare the zero-initialized and trained networks on the same demo cases.
initial_model = PolicyValueNet()
initial_model.load_state_dict(INITIAL_MODEL_STATE)
before_summary, before_detail = paired_evaluation(
    initial_model, CFG.demo_seeds, [0.0], "demo_before_training"
)
demo_summary, demo_detail = paired_evaluation(
    model, CFG.demo_seeds, list(CFG.dev_thresholds), "demo_after_training"
)
print("before training: zero-initialized candidate heads select only the baseline")
display(before_summary)
print("after training: demo seeds were unseen in training but oracle-confirmed to contain opportunities")
display(demo_detail)
display(demo_summary)

active_demo = demo_summary[
    (demo_summary["threshold"] < 1e8)
    & (demo_summary["changed_games"] > 0)
]
best_demo = max(
    active_demo.to_dict("records"),
    key=lambda row: (
        row["score_gain"], row["net"], -row["regressed"],
        row["avg_margin_delta"], row["threshold"],
    ),
) if len(active_demo) else None
DEMO_THRESHOLD = float(best_demo["threshold"]) if best_demo else 1e9
before_gain = float(before_summary.iloc[0]["score_gain"])
TEACHING_SUCCESS = bool(
    best_demo is not None
    and best_demo["score_gain"] > before_gain
    and best_demo["improved"] > 0
    and best_demo["regressed"] == 0
)

# B. Ordinary seeds were not positive-filtered; they prevent us from turning a demo into a deployment claim.
guard_summary, guard_detail = paired_evaluation(
    model, CFG.guard_seeds, sorted(set([DEMO_THRESHOLD, 1e9])), "ordinary_guard"
)
print("ordinary-seed guard diagnostic")
display(guard_detail)
display(guard_summary)
print("selected teaching threshold:", DEMO_THRESHOLD)
print("teaching learning check:", "GO" if TEACHING_SUCCESS else "STOP")
print("production promotion: NOT CLAIMED (demo seeds were oracle-filtered)")

before_detail.to_csv(OUTPUT_ROOT / "demo_before_detail.csv", index=False)
before_summary.to_csv(OUTPUT_ROOT / "demo_before_summary.csv", index=False)
demo_detail.to_csv(OUTPUT_ROOT / "demo_after_detail.csv", index=False)
demo_summary.to_csv(OUTPUT_ROOT / "demo_after_summary.csv", index=False)
guard_detail.to_csv(OUTPUT_ROOT / "ordinary_guard_detail.csv", index=False)
guard_summary.to_csv(OUTPUT_ROOT / "ordinary_guard_summary.csv", index=False)




