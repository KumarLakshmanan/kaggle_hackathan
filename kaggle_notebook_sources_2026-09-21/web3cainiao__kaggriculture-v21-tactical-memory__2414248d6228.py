import pandas as pd
import matplotlib.pyplot as plt

route_screen = pd.DataFrame([
    ["Dennis Gioche medoid", 30, 39, 0.700000],
    ["Knight of Favonius medoid", 29, 39, 0.650000],
    ["2/3 rounded medoid", 27, 39, 0.600000],
    ["StopPlanting medoid", 26, 39, 0.600000],
    ["old v20/sash route", 9, 39, 0.210526],
], columns=["fit-only route", "wins", "games", "worst-seat win rate"])
route_screen["win rate"] = route_screen.wins / route_screen.games
display(route_screen)

ax = route_screen.plot.barh(
    x="fit-only route", y="win rate", legend=False, figsize=(9, 4.2), color="#0f766e"
)
ax.axvline(0.5, color="#64748b", linestyle="--", linewidth=1)
ax.set(xlabel="Route-validation win rate", ylabel="", xlim=(0, 1),
       title="A fresh route matters more than a more elaborate stale gate")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()

option_screen = pd.DataFrame([
    ["safe current route", 38, 41, 0],
    ["v20-style SELL reorder", 33, 41, 0],
    ["full predicted quantity", 15, 41, 108],
    ["open full preemption", 14, 41, 564],
    ["half quantity + gate", 41, 41, 336],
], columns=["complete option", "wins", "games", "preemption activations"])
option_screen["win rate"] = option_screen.wins / option_screen.games
display(option_screen)

ax = option_screen.plot.barh(
    x="complete option", y="win rate", legend=False, figsize=(9, 4.2),
    color=["#94a3b8", "#f59e0b", "#dc2626", "#991b1b", "#0f766e"]
)
ax.axvline(0.5, color="#64748b", linestyle="--", linewidth=1)
ax.set(xlabel="Reserved option-validation win rate", ylabel="", xlim=(0, 1),
       title="More front-running is not better")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()

balanced_outer = pd.DataFrame([
    ["v21 tactical memory", 56, 59, 0.931034],
    ["same route, no preemption", 54, 59, 0.896552],
    ["Moon public artifact", 43, 59, 0.724138],
    ["Adaptive Replay artifact", 41, 59, 0.689655],
    ["Soil public artifact", 40, 59, 0.655172],
    ["public v20", 29, 59, 0.482759],
], columns=["frozen policy", "wins", "games", "worst-seat win rate"])
balanced_outer["win rate"] = balanced_outer.wins / balanced_outer.games
display(balanced_outer)

ax = balanced_outer.plot.barh(
    x="frozen policy", y="win rate", legend=False, figsize=(9, 4.6), color="#0f766e"
)
ax.axvline(0.5, color="#64748b", linestyle="--", linewidth=1)
ax.set(xlabel="Win rate", ylabel="", xlim=(0, 1),
       title="Frozen outer: one latest case per current team and candidate seat")
ax.grid(axis="x", alpha=0.25)
plt.tight_layout()

import base64
import copy
import hashlib
import importlib.util
import tarfile
import zlib
from pathlib import Path

WORK = Path("/kaggle/working")
if not WORK.exists():
    WORK = Path.cwd()
MAIN_PATH = WORK / "main.py"
ARCHIVE_PATH = WORK / "submission.tar.gz"

_AGENT_B85_PARTS = [
    'c-o}ASGTIl_AmOrKE-sQ9>aEB6C!_66hToj021^;L_l&z45**|I`^KAeNMZrotHZv6f5*!^|GpG$KQYdoi-',
    'c45?M)1MRsbg=K9h7*Fx6y$W$&)a*4EGvaWf_KY#tTHMC!6Q*+e+$B|Ed^egf&iT2Bkf61Tbq~?3h{g-',
    'lyqR;4Bd^x#h9GkxP%hgohRR8()Ybi&zmi)o^%a9*(q<$uU5Kgiqdy1z1l9kAh<6pj~{g>o_=Kl(`=u7?A)(>i}`mg_j{PP!c@e<',
    'S3eqCZM{^j|<5>0l0d9thh>z5Xov9Eqss{ZR&tZAQD&rh_I@7urptEWY=VFtfG{5YQ$+0bP5pTGY8`|rO@H}Iq6v$k04w7;JeKe&',
    'INt=RXz&#s&p-{*&8p8oplFKIO1&ekjTSO4E5|8aa-jZ42f|4}u?cY{ca<I;b~|8weszZ+Gp^w+P?-',
    '+x~Jms0y*|9OaPglk$yQ_hzDrqYBNYc5y(Dk)=QO<bt+0hWdO49a&3&1THZ;=AmR8$*|RRn<{=soYyymu{c6VRKB#(qm&u8FYAS@',
    'b2iXtM}tkIgjuAKTyJ{#Ey1NzMKcW&HX}L2faX%pUG-',
    'J2hLb!I(jZ`49SA7a(>(!%}?9;?JstgGpXzgT>iV_(QDDUdsxTN&fQSXq(&t=w+oLTV>v6U29wJqckM^$>6Jow7Sy+_-',
    '%yd#!|2N3v-',
    '21$J&%4!iepZ@cfu4=t@Pd{tH%9HUNrO_2A+nMWB5o8JN!v4%Um0EJ@J@v^H92F&~UM<k5c7DT`KT`ULB;iDjgQ?)bdK>E7~b0#6',
    'XW4d04Serhgpd(bp;86s;q?prA_z)xJ<{seiFB$Tj+%tN|S_H8<ZwFAs*6LBWo`qrm&4x<-vtmp`S7zD-',
    '*sm97eVoqzOiWJ{W1QZke)nqze~-u*nXRtb`t&)#u|xbLk5820+CU<FB?i@9xBm^L+LzN5r;2kn-',
    '+(*w>aGi3S)D$(kvNv?WIwPz<itdZHxD_hz49TNl3NRQ)UR;$0OQu&A%3U`^l#6~Z0M8%?aZ?~5rZ=@GeS7BJ(Jy8Yk==oZ0mI<X',
    'VBPdd0(-EuA<w8%~G#KLLR8VTscnwQ{Z*rr;c0&NEdALp2){0uv!RAUocTqp<Kj1Q7o9&v{mKz-',
    '3OChVN<N25DkY@0_xznY`tWy~_z2Sh?n(?x_Fa)4S;#Ao>bB3t&JIC*gLD|zLk6RB`&|DFYFK+#kREpKCoTNJrV0t+Rk`cE*Zq!|',
    'KlT42=Hj})aufjlsFL6_Qenc?o4BN5-oELS(t8O2y8>_ufxtwY?=yT-',
    '@RD^Et%BXRvZS@V<T<Gqqu&AF*yE4M;ZUfv+3d!L<i#ySF^L8FUF(B~w{;7}GED>F95_%~>vA=J-ikccWiBX5rz?-',
    'zh=>i&RVIPIVAC`uB{L-Mu5?L+oAA2-',
    '^yPkaHgz9l^NQX(`?ew=7@l~(+(9f}|j=gXocA5HZ*>8=&_K}Iq_dUyFJHI@?&ki?$d36Kmk&e{H!zx_`!s2dg5_fq?&uzDteKa`',
    'G{Y4y~B^k@N)KYYL<2mohArl$l#Z_s~{((|;Uv<ZU*mA^5eLpJJ8UUu2EyNit=C^TiieB?9hNOwn-_q>4=IE8tp_FyQ_U3dPbc|w',
    'WX9<$*V`5n?PP3zjs!+!6pLvblGGz8;2q?S?B3t(=acPl_;`lO1+QUIn9_thCE#`n`lep@y1=D`WwQ0sgY@4)I>Wykm37w?;#vRv',
    'ofpNBNK_d!Yi@s0xosv)}!(IoayK7+NzAJyAW|-',
    'S2<Y%eEJeN)7@Elc6qOx<&^^h2v;mzeIIr5U0mviq_AI|Y=YXMY^Y;PhhrP`e7kz7Xt_ue0~>dJ$Bc{EUM1_O{`YAuDOKeqUa^c9',
    '-rfDB#`_u3auy$$)`PUH7@=w$j0h`F>w=tTEYg5X5*)gl2%;v&DEJXjP!=APPLf44@Tbv-',
    'zLx0BoX+A8!;hI{Ya3n_?~X|!13j~l$aEU!n$YL3dPm+{4+Ilx-imPj$Ti;Adum!)ZmTnOBBPmoTdpw6;HUu{9*(qUu$i-',
    'LDH+gm~n?IJW`@0|x)wi?ayvfCq$v{9)s=ePr`(hwz+_M;36i$or~?|d~<r(N6S`mN2tJN!ubUB}Gz>O;AeBp9!r_cjLQ)g3Ll=}',
    '9q5i)T@OXCP1(!6WMI`KSkiWExHaqcEt1=Poz*zJyLg+D6&+teJ<rZRdrvvesC>4azvuEwH!`Cof`_UGh&j6OV^Hds)g?ay-',
    'l41O2=y<6YT1BwVl9d6aq@mk-',
    'VC=$re&3QK*vz9^p_D}nBQq15ZcofJZ&c72=%K)G?b=c1WX23N-z>Tk}=Mh8f^rf&B)+Gg$Bqa8*=#7nK<=iTs2<8dW--GLDmPQ~',
    'Qx&f_{S>Q-',
    '?jRfF;#=$vJlepZAhFMDI#?+h_bOCK^WaM@H#CxaeUS2SdStVe9t9<6pu?rf^!plkAY0mW20GB4~o8h^#0K0|z1=cdiQP-Yp;>&?',
    'Z^;C{jt%O<Mu48I$T%dB{m_lljP=jN6>xHBP0k^MBg?X#vfI9@ZLwCM~g>LL0Z7Sw`t6o}2>qh<7!aJ(1kKTrm9vF&c<^jyx*Ie5',
    'V<OYK=*#z%mRG;16a?&C0z6|6{^qTn3Il+^5smrmip%qPC)9)v_9y!|}D>To&S5Laxt#y8TT4!fQFm|bp<vyFxSfwJ24fM{6Z^F3',
    'TB<<}7zXRx-~gCtYli4-5)(HAgA8v#+$+S|6@nO~ag-n-',
    '+ea7%dOA1Mo{=T4`X(t)j3hV89mbBCb=XXtSfh8y6cWjpWh2J&}pr}Lw%SG#o<Gc!7&vyQ;l(9C>qlg_r>LZTbwe!p6Uv(_uBN0#',
    'b?4}(4u5A#)3HdSlx;N`&1%XqjgzR!nUd(HQ*;L6^VL%kp+gM<S;W2>#xdsZ<fIfYpb(x`fGN01&B$KZLHJIpFh`Mx%YKTvyEEFG',
    '3U@|I_`Sijx!DB>U0dJFRlC}q$(QX<95m|6%;ZGXQ#YTKk$XVUgnib=Z#YOE4e2I8JW;8Rj%nJeq?jnu5q2Jdy6@L``j`t{}?sCF',
    'Bw3YTo2l#65n%l-{L=n$?=bO1a&;LYUegDq-R{kbD^`Ev8a$zX^-',
    '!CqtTeXhYs0YB&J5+EJ@94MwQ`1^IxLWG=yJd$FkOc@<~TIg1RlE^wFSm*_tX763%hpl3(KdE$?=28u-!bZ=q(j%?wf1v8d9J-',
    'vF_j&}@K2mP6cZ^IN2}>q>L~?6$Ur*}qq*7XfJUJE+ve+w${542k1>{sdUk!op<(P?n&o8gmvbwA1vp_H>Up{(>aXAn!U1l%UD%9',
    'yTKIf)9EJ&Tn49nJGY3U``>zsU6+imO)F*3NF)?Vi1pc9kZm&RROC6BcST$lNsvy^jz3MKf{XO%0jwo6z}<a5ZXYb)@L&X;{A?FW',
    '@TM-|AuFs+&5Oj}@`qEW~2X-',
    '(g*;7(ykS6;w@K2NJv3K#%LcZ$~kK&?W;)*FF&tAo^hew<>_kw}&mrPwqg6*?J*q_(lEE_HavVLt?PAR0aG_jSg${Brd;Z71~M$B',
    'es82x8Oln)Y+a`UbS~ad}}rMlWH+4+i|K@Um>B-F^&J%HZ2xh3#%ia=r^AuP+7ioZFy~(C-',
    '<|`h(L4LqG)1XTb@qeAD9Yra|l>AKL4<*6%WT5Fphtdd-',
    '^B_`(7kW<MviiqBG)7r%1Qjml2Pm*rxn)m_93m|h`(OUD%a1C{D&2tN_ZuT><e1UeO!Yo0f3YJ=t(Eag}Z&1NFNFX_^y|4c2S+b_',
    '>L0fttKM#CD~gECix%au3xnYej%ktbbn9>Ic`%RdJpH@kY<&FW1&G+_$%&}6HAyCC#3J~4)trG56@AbL>~b6%S~eMmRc375{b1Bq',
    'RD=-',
    '}5!$Bm?7(BY#uuL|flSZ=kt_`|^AdUHKGYDe>oja<zsj+@9(q?!EOx%Jw~9kjl;P*~=hP~E5o<k758BOY}M&nrVitrpmr)hBJXj`',
    '_xSVP$E!yZE%B(es(svfS<<qt64r$N6a&y*jb=DCBnAw^~)oQUB?I&H0=u#J2=-',
    '!E^~PHbRZT(ejuaFD(Dr*ds%mR@%LLIlsj9`ZMc8N6-',
    'BOr3sy2ei<pZ+&)*@>ezAfy3?Jt;Nk~ESuh3Sd}ogC#_8mE+w!L)X!XF9gCMf;&o-LXkND}TBlcs)#g%kYfxWkf_u%@Q2No-',
    '4+{xc^9scA7sjB2%Wv5uh`cM~-aU-kltvev4aHj=dUN>w%nmUuls<J9R8*j5dK?TY-',
    '*W?Yi|3Dq?4mdbC(ahpUMNYDo_Hu<67i+8(JX*bTGiom?b<&tCQdOvza*i;)%u`$cIM~t{sLbLENOTH84MeNTGCy9`cDLkya?ZK>',
    'q^X@r<M?VezrNPHVVl}}3ezb{)$gzipTLl#W@J7*%f+}FP73Ygei2>R{`R)%$s%;Sbpj6&uT4TaubPDeW!>-',
    'N7b^0@iqm1uw^)5^LBlJGWmLFkIcxbkf6YH+*jog7e0dr-y2Vca!ZAnEE_L11%yBf7yXw+d37Raqwr7ELIPN-**Nk4h`Cc-',
    'h5^R)mLb;u^PJ#6__?d;<W#BYR04M0*1FTiX;iZ%N1J&slN;hZ1Ea_>Dt!VDcd`}^zJ%2Vdf}-;Sv;6&5J;^u~`-',
    'jtfmfJB!yT3m87>R8<@;$$%wVU5Oy~fq*WZRV@e@dO&;f{niaiywn<KlXAztiy^xz+)o^%^iJgo^za^sEK1In(T`jpvWk36_SlrZ',
    ';-RcxSJeWhL#M9u2|?h_PYn=Y7|h-',
    'DH9FqfH(#_AUBKN6Y3BrcL3U5?4Bu;12dBh0H#Z?S%!i?s0_}???};V_{e6eq_FHZTsk5u<9pooIfP!<L!+<o?*V&)z}WS>O*fmD',
    'tOX<%^5Q!f`|p;?}n#I`$rS_HXObEo$g`J?qhytSyAmECD`H4&&fSEUv2Um1J<Xixrr_v;9M`-',
    '6{|kMa&_j&zB9qA?av=X=F%qluvEw=`+^961SPg>vyhYP^h;plD=7}U>SBad9!icsG!5p+EsK@O1N(R^u4^tklgp-fA{*@7<9aK?',
    'J=h-3N73&~JPyVWvb5Z@l*}!touOk*ciC&<xvn>MjZ~Sf*h(*PS*!2|iu2{q<+57O)+CSL8qHG+?b)q-',
    '3mEi{s%=KrmaIm#ZF{Ws*71)&Po3S7m#fI=Yi7bVzWBbBOP%qty+yhM;@%tJ$$kkPC8O-',
    'G$2_{^2hJEmCl%$qxzu=D1VIlK+TLu!6owzfjqC)a*6=AI1Q_CnKqc(HbNYHLx@%0VL5b9xozfOQ-',
    '6p$u>|OIX67g35cIA(4@L|k$d6C?t2vB_uhF2ANw%$eM8jW103In_8b*s!rz4Wznp7QHP$=F~@i&r4ZcB!9RzrMOax+kHs+RQ$>x',
    '~tCm1$kF>@&t@^!|Elrf^u6H3e<NGBoGD@Osj{k^C(C5)ODi_t-',
    '5tcoEiwdmgLC*z!V9_xmY^e0DIOyVy0R87)@L!eSq!SZem~tRL`{-tJ_|3HIf$bjjrvR&DZ-',
    '03CkY5{oYtnGZqAXSxwqYkWoig4$0BksoKXfC<u8dZ<66ADTWQG*IE~pHe%Ww=w{-',
    'a>Gi$$(c+xT1mkCqz`;TIV@La<wnWaw1B99VQz7ZC^APn1YJ)iuddt_tW3#zCv{GwvKfW<AUpQQ^!~Dbd;{8oN55ojMmf7hstdM8',
    ')>9i|BkgH^~<E0z%#b_u(gIeP`rfc{#r=HY8^73_;N(ANk<f7#_w6;#c>J~oKp{I84Mh>{6M5jACO)6AS$*HZrDOz!bZ#8W?YnEE',
    '$&4Ci@5fOH9L-niX8J0?3rF6cwEn)9$?6F(kmd#>YEa3+8#!fj##lMGWUVx@GY=qrzK$x!*xvS##yrr~-',
    'lSQMkVGb?eoh}c{b6NAp%`Kgny!GQUx1vFHx3Hei^qN#aVtXS~fTqiXU1)Eee7zkg?mC`L^7Z{06?MgnG_tiH>cjWL+01Lr4G7PV',
    'pgCH?J)(3e)7P6>Q4=T!m$;w!Zi8?6i<Zr)w`$r7hHb1>7_H5jv?u7ssdg)lH0W%OnrDudSAH&^tBXr*4hJwW97$^PBJMZlc;9t5',
    '6LDHl-azh09AZ36Pz~B=hG}b&vANvBD{EsmBQ&PFx(U_eV_TGi#cpj^v}cPo_Oupc;lb>8v58Gj{kU58^?J^#Hb_+4Rol3-',
    '6asmvXrq27%e12gaEm`sG!8b8s%3oKTzXn>ToltOms|u<XI^NQdAm5?gR{Kdx1@a|jIGicEre75jtThCtOG&2_m(6ddNxS5;A^!s',
    'v>I2pFQk+1K4J!wUZtS>U#FNudR_N9(n4lzW#Vx~m|A0oVzyuE0b6Ofvbf{S;zoJju{OLmIL*U|oph#+?efNrE@)|p+1>&*tJu}b',
    ')cc%-dL0Df*A_aZ*XQ01hOkogs{t?7xO^hJ9Q0#bv*F1+P1S}9Pp@ZVEr#35F{aRbPOms6>YOi-',
    'H~Nw<JPIw>y>Z;TO0mhQ$GH3V_7RZJdPcqzr<qb`rKwepkJ4RU?RT3osL1^<#DVcs@~&>RBXNT49&B#~?^)y^%WFfns%iO(?S<eT',
    'h{n2!zG>8}RxToOl1$yOk#Z?65x{<4@dRg>M(f=n-3#08mv+-Zku#^$`BRmx8}Cb>cj}YqwvMp)-',
    'f$~H%UY?;LIvB*6q$~=z3XZ3(OvBX<zv%j;|x(s$(ZooUwR=y-Idkk{`RPOQ6C=?1uZV9mik-(s!#@s)?{|2RUKKKjv-',
    '}|BYRa^?4~XDeZ>r?(5%Bb&dB%n8?U+?YbodEs)xzxfb&|ecSZr?3nMd<2|QUGeqJ>v_gvLZmlvG`r{i9k#@LyW`24k0`msmbxJ~',
    'lQ5GM|YEy2ga>%l1U!Ots6IXG?bv9yp<Ky9>Nn9Kp!_sBZ%jyc*Er`Y7QdY13REee?S&kdE#ZHidX<xuX+5q(`&ip8V|+%&gstln',
    'Yu@p_iokZ>uTcJ2IN{n{+e5Z9jys%#K^FbXl8>Qpau;Y$y`Luzhm=BHs5y2z6}g1Hdw!F)hR8C`s@w|jfWrzelTWR%x8PxEW1Q7M',
    'lP5nb;VXH&6N%*ch8KvX9!ls&873D#Z$j~$#k`AErmpDzCMYgi5@w!F&&ZF$PNt$x^E_n(LQD%fvTqONK8;tDu*uT5r~I}|?G*4e',
    '@iRT)p<-FRY5&-',
    'LYEe=jlD6eo97*(kPVq;bj5=;zh$v4`vVJ#(r3^$*mA8Pu_|ad>bP&=cF;`?Wk!D5KkXjCEm+)r@E^l<xhqMfAGh_%@rLiy)W>#>',
    'r@xt+Tk{uWl&Cy89B%c|n|P(@vJi7}q>8uU(^6Am2{(wao9YG1oueK9+pn-',
    'a}4NT%C(!+YnArsk7(lTF0s%?6jF$`oNkt@So7#{F%!IXNE>&Zfz{eGyDc}cDPtJxF#$zmOo#ommH_WyeY3^ab7Sam}}#O?V>ftn',
    'yp=R+;-',
    'FQr4Fyg0%{K@*ItxQ&~7J}n{5C`9iDELYwHgb&q)=WzN1r+L(S(P%O58047o3BvurUOE*@^WPcL)e*hv$z%o74G!*pb^;&=(Nul5',
    'N5gwDxWU#0KT{b9&F<j!8(27W*8917@)!V*7&IGAp6V(LGI&Gsf~+eV*9U~kh5tI;$%{czq){oY5GxzF20M45S9d7W;9cPj6W&&R',
    'NtXAk?w<)LnxC!p0V6EnQ@ku4{+c^{^o#nZv}C~Y^TR`=+aatIPhId&o$`RK+MTBqLjVZO}u*L*Frd{wY31#HZo`+nw8yt`^IDA)',
    'v8W9E&d6`xVWrA4)bI-S_C+9Ex~Z&3rpd>ynhQ`fawRq`7QimAK!!D6CVmQ-_*^r27??I)4OBj`u#+?EYejm-id)OW(vl!>&iu?5',
    '*%<^gSZo)=5tvlnyNJ?S1C#lKa<NApY%7oKITWy98|c=Os)FSpkfmn!G5&+c)q_3?Qgxml^K@)lD1az%M@G@zQ*+tJhSl9=uq;ka',
    'ClxQ<Wl&p_DKmIrzY`LoMt;E;AQT&|~ZklD6%+Vege#S7x;V1)8?-f#<Ubd*QV^hStt_d7>-o_FGfJ}-',
    'SQ(q8;YnIOz%vSeabsw;y>uq08WpQC)6egNDWfRW5Np8Ll}J6Dbi1E#BY3he+`YuteB=ezS@!jRpLLm)k7K}<PEI$%xDBD)??<@&',
    'nyzEULf;p>}L&0#wU8Q$gVZo8a6CON1%Hm9y;{-keCrXW;a6Lyt}zR~U(=^1;CPT^=@xJts7%eLZUEp9xs_cR8T-',
    'Y`294*jZ@tJ;vs47DmiU9kQp_fDy;oF0Z0knOH5r~GvCgMxzU>)^$TUt3(;Lm#8?V?`X6jb{I_Wc$@eWx<w;bnz4g>qc{BthhOoR',
    'JCb;A@$e$ToXI2B4|d|#}(n^({-|(KuObIs22;FGSMUzo_24_Pm3kpHU|^j{{vMKH|=YCSPy_k>0oZEa|BeoTUX-',
    'i^^abHPbxxW@5PDcCfA9kA*#GSh`vz3^Mm91$gSf3rlW%G^JZ!Jz>`e-',
    'omB;5?m5%1myo*3=lB);4e<%uYPnMs_Ptz8E(Hqqu)v0HfqY#PmAUx_B9GlfPH8+)qkYz}Z^Knx0QZAnTu*0pKfLBF1{;cEY0&W-',
    'TcroA+qo_{ajz+I8ijPgP<!)xhDP}M>^fT8N(xH3;psNBiRI9^K#Tyn))BE+dVYUMot@tX%}WAnZS+TZKB{nXXO1COVdr^%G}`3{',
    'Is?EeY(I!eoX|JD;Z2O2>~v{yJFbqV?oGhnsiE_s<<d)?g??hmrRwu49$rU*z7}rEe9pJ(ha2&r!YlIbdi82BR`qHaAeZj3dK_?=',
    'm}zjK(;!zxw%5A#!{_kPElovZ*u$BN%LX^#$0E2HI(*Wn>#Z7Wqn=ym<#~{QiIs@pMs^%-',
    'N+)4bf40f?{4Mjl^r|4WpfOw3m~GUWbZ^Jv(*WOLe^1r!cCb)-',
    '<;|jNhDo=vx!$X?@MAGerSV6SZJBeey5Fl)sY;!jl_!!%Bi8Bl2gA|%q^*!9)Znja44na9Q192q9yffcfVL_-',
    'MxCD9v)RzPzzt&MPitHIEJRDTYV1n%Fk1QJ;Wt|`+bWpbSmN&;Q@w8+UauqoEun--1*)-o#kupH2Q2-',
    'TKROPH4wk+0R)4uTpJ0yFZ;KcvLWn^ad4Bgilthk=1Lszb>chwM06lN5lY2(3$ycs`*QMQ8&|oUg0&d}*&zUqCF2^_`+l_5q&VLN',
    'y{mxl7h1k8#%lzwhjpjckDboNvHb)%$q?J{o*I+r`_u-Qh-{gA}gqsI`-',
    'k<D0s)4;O(PcCk?d_W$o#0hzjMaXUE!zRCZDS<%R*`K)h`|Ej5ntKIYNm8M!iZf@fXp1SrW;qyK`86Tg4(XVnynTeBaO)DPd%zAd',
    '|bZAJ>-h_WM^8XpL6F_u@Z^29mh&cIG=?*U>A+M5b&4>$LXn37-)s<>L-y|Z(49Tb<zFy6*}uu5XkgWUT<x1cHg*4-',
    ')m5b+FhyPQ(_Jq^Dv%0>J1sou=u)d%DD}+Ud)v}HxDWLs?N4`JJ+Z@t}?k0o%|%Qr_3}&zrNlj20OieI$Q~@GW6c7lZ?N+Ft<DMs',
    '>p_Wq_eo~PIqN?Kdg2}7`Hk%yr+GP6|~DS&Dlt`qxNGNK-',
    '3y#HyEFRpxfwQaC%QmYxadZS|=HND@7!!G+#>2BVCJDk$S(XZsR=ahV&5_JcND`*r{Ct1yLTD^ZZH~G}pcH5sW7S{;Wps^dOI*3)',
    'X#vHeA0sqq7?zXo4hDo89b<6UJXB?E0%YO8T~tixx<O=sTPzZwrs@7WVb_*<V+J?9|w7`vQ7EpC%a_O`=1e@8M_#C+*8_y42VqsL',
    '~oM7Y}v-',
    '$GDY5>mUzxR!iQ;!_XR+3<J$6Uwd{6Y|l_$1%cfZ3SUjM0k|c%4O!|Y=u<ywUUxS$ELK~H_jTTw`AHEENfR92<K<~QE`Z4n?!a+a',
    '_Uh9Ds$qS9*eVB^5+%fRC57NfWDk5BhpU~obA7~-jVgMDNORtMFjq<aG6c$V|C`5aUC8z_NOb6hA?JB8MjGW|t2!#9Dp}(4;c-',
    'wVRBz4=D`UJ}68glw_ZrtqrFtOka-iXzOWgW3O0+dMJs+5CF@c3eQRsrXTl=TpDeC}_?&8g$#X3@F!v;|(e!G_5Nvu@B(E@#qMWX',
    'eJa*^9iShy-',
    '9s3L$xvlP#t^t92*&V}d!F#+R7DSj1SQ?F1pE=)_k3#o3u#sF4&nhSf|T;rq8MU6Un87xi`a&Y@*5s5tujCyuk>lLmo&`x^6i8ng',
    ';cj|99;S8={gt5Oa-L{*RFt20F2-Q2~>zSC%k@4x(*9k||))Cy?K=%?*@$+Q8qo7Q)W2=&p%|;<G0L;tR!!H=*v9qjKr&WSDS9G-',
    'X@i^npLDt4SxIF6Mp`=X3@`PTzR-=UmV$D4Bly5VuWfWsLtf-GgdpMb$<I?r^+AZ!|J{<R)&e>bvK|*_cH!sNIV(W}g%Rp_~somm',
    'oE`uboN0f@wXKtcVVcA6?pWr|y88#Jt_1F~kB9Hu3xh3mVU2`{wT{%Y?A0CSVqdY~Kz!QjHdWlq|rRHpktq*LgG9@0H=lP;YGE>A',
    'KIE&F(cYfXtR}T>+tTNkOW8}GDjZlAMK-6_}AsG@2&94L6fmU8oMB=Nnm_25>VamkwP9qGW!InLJRGta!S8E0Hm`d=7{g!*-',
    'R&#c%dvsgICOM=J>C4%8L9)*hJSer;rtLT9z4uXVP>}KT)NwD!e}fNCtk4Q&pKXz;yPe~1eZ}11Y~z<cx3gCCtIVjTI%r=BZz?t0',
    'APz}^-q6|%T{<p)v^kh)c`N~R)6fFBwGfR=bpw|iqT6;hp7zt{sv7-',
    ')`q<12aT3<C7TMlaIaE*uxh;zE?n&+Ih4C@+c5tExjgM4j_WO>})3G@K^;w>hyVe!L4+Ay=%j*^)y+X9wC@+5s1gUcZJyuEadI7k',
    '*ABTpAgCJ5NWAQtr3wf*OE!@}Xm+wa<sW9(&U1_D9>53JY1lc_)qOe1YM8mXaG%xnaHd$&;yG7q*(dlTHjx<;O7(iSuiP7cA1@ur',
    'TzNRX9m$Lryc&cBfU#)&L#3kcy?pUv}C|!~4DoZ3<olE=bcH7)k3Z}RYtA)adOxW_a-',
    'c`@Q+SweK6UlQkoZhYob3$!2mS*}10Nk1aJFb^wYUfUk_GEbKKXUE+H;uGlwnol!Jghv^4*qMOSlTY@C%XW>jdSSMTi32q*V^7G%',
    '{pNtsD%u#QZheo&`FV}^>O}yO~z9M6_>L5Q8n49fsB`@jlkv6i`9j4<!a&ReT7naP*?Ie;o1;6dB|3SaYkMRKy}g$({=u%+7aP;C',
    'w9-2^^U@7cYT7p_}#8wGqo~|(FGC@kM)Mn3hXke(nBRQ%Ay`{qlkSZ<-',
    'yC+nAW#Spj{Wt+w@>mkBw%$KWwT*6DIv;o<9xi36M2bD`wPH<K>8T&2vaxN#1iFHg5>+Dc5MVQ|MZmT5KrLPHCdIYM7gWKeE*-',
    'ppWh`S)oaKxbK)QsGcr6h8~Vf>lsH;rXCZ>mX)hvldJE363S_iHqe%&?BCJ(S-',
    'R;E_3p=;M!oB^n6yJCeE$3qR&0HFCC|((QsyPF)4qFPxQ^a<XSKeN4WX<`Vuz$|=rV^Ba#a@TXAiC4>&zh-',
    '=u+{!zWvN)m+{__=!wS835?{{H|i%;XuKIHw)YQvOCE6mf|l$&W{V9`OY3QOM{e<%62x#}Td6LYaC!@?q;r@`;I;`&^OZ1lR^2%;',
    'kXm#jYh5OeC;D)q+7-',
    'xgyqZ4JRSv)@>U)f@R<aoLyg(tlA{nCn`C1z>j>fu$yGYk`p&QsAbzq!pJI&)B@vN@k7`Fh9(n{CVMv!L)Sb~b~i<&&=fO5aCSFW',
    '!3G%Ix%_7%r7<^;~av5vmG>p*bpJkLx?Tu!C#UYLy73PcU2t$RCLEpUy(iuF_6=r3ZdNO>Q(YS-v2nd|w|8=iAK0UnRM-',
    'n~482WxBt!lF8(PTJ<!0=P#gEtq}7G%d!HBUJ)`ao4C08fIhs3VfCv4Z62;1*TIOpynO$aT#NV6`cB;6|^Z~&TMd-',
    'N^RySs`ycp5x&Un;ZFb7QK}-',
    '?>ej{e3_CjgelgSd`E~s@GqE`F*uhaK4ned0RE{5^RIQLRwaA3l_Fb=EG<TZj?jb>qg|Jk?f4=3NA?=KaMmDp)HkV6O$_iAR!vml',
    'nWMUyF<{$2TmRm5?a76SM^HgZ>4Ybf46VPTj@8bOnSrjIaI)(hnwY)W3+@U`pCU*Xsug)4AdwoDt_?wJfU+YiGBRI6EcI^G1=tud',
    'la`~S>HR^v~l5?&5ce(tRM2_|&2LJz6<Ni?%l>^^>fJNCPI0tQygnjI+Wxf5h0vVm>b0rp}YrWdJI(nDJVBh9BZ@%eDEt$WEw;lJ',
    'GXL1Yc>H{F!rN=dPeg1?i@{^>E%7AOHyu4+-W~0jR0Ih|t5W#OH3wG^Xy1x%Mm+K{09-',
    'NCw<3{dZ_Pzg}!eB65FLr=4LWT26%EFt`yS3Ok+@)XfaYUV(M{b|r8q7ByN%iLJUfgcF`*mx|XCrEIE!KdF!ZO6R0u*l2kpY0X*7',
    'aNOqE&aWK?(hD0?3*@j&8BQ^L~XACh^DKp4oK~xvGNSO5hA$PTg&q<~ROAZWIn5!%>Vl{?#arBr*}ghdv!_Q@EPEN?fJa&#)3OUk',
    'x^Cqcguxv(}EBt~=Q``M-Q_>Wco_!Dp-8Jjik7T%XW^tS8m{L<<Hh5yk;EXAKTX24j4xyHT_#tav~>8I2YUuA8knX-',
    '>?ofDe+R*8EsVetDs52CY-WekEvX&D{4AOUib89F0<`G>yA*0nmO@r&VPL+e#UpY^$$DrG5>Mfb#K{>;-',
    ')B_P$$M0SA{YhwJv^_L}EJW_Pr2QU8h8?{b%&-`w?~o5BSoMer`fA;qHL1qjxkpZBA?Xp2-',
    'iE04bU?K*0{E~g#yg}xo`)c{gcQ8sNuG#<TjLzpa%fm<+pu%hn8%V4~_R^wgcJy+<1=XmJ#=pXYOthh~{aERh=BQ8NJ0w^)qzx9P',
    'Dl|b2U!ahC%v!1$P>&Dkp*>yJQa|%D5tZnwhS5tgH7;3iM;JdD0akWw}gSwNx1!SYQ_{yf58QOrBBiClL_j82j*WO~TnXG&qPvG_',
    '89?j<&(=?9kv*C<ejjXNurG7T+0ja1Sn$1SWiA1@S)Wc0Ab4{0wnvY2)K!?8W)z#B+3A5|-G5=FxK27^)Db^psy>mL#NKQp)e-',
    'o)%XcjJ5=CY*~0@0np<2Yz`7uwBRO4ESS1!IRk@~976yK!GDR7`I&a{DbPXAVDZ>fpx;Tjz3{9kcDb6GM3ldkwUolLtc{I2A?QJT',
    'tP7HIB~u_FQ!PrgYqi$Df56kT?WctGG#~L30_8qyRCM{d53GMc3?t#X5Y_GmrC7Ka<4Pfa~eK!k{EYv^>jA<wsvd?#o`uN7G8$8b',
    'V`|jq&+K>hZ;E2=JRMJP#^gX9IlP4&9;_l+JOEirC4<OcAo5zh-fv-HOjWMk{2H_?(!^$3){-',
    'qwy|;2g6FRo|@D++g98a4XQr}tk`WIKJs|-TJTcx0CoNlZ5<7HOr=S>UQVlBLSsc7Dh-L#l*aKIoo$;`J*2vE(-',
    '{7Q;K<2+`Ho(NEgTK=x|wu%u}f`PvlNC+!#E5tn|hp(7GD~KYh-',
    '2Vj7t`BlS%%Wm$pM@J}Nr%0r4U~w$ca~+O69j1kH`5Ut933u_`|LCFpVg1GPTAORVO;8Do3d7WfaRO)^=vPB(k}<e_C&$(w^~i2%',
    '8GTc!r)w7wLl*ragra);ZaKOgZpfbm3b{hmC;OBK8qUT+3B-W$U}8pC_3+&CDw?`50-',
    '05h7b_T{FVTak?doo#Y72Za>E=rWn6)uCy%TKlYNsLZSs5=r^u4OKtA@wapN;opG!<vv^SbNW0{Qyri~E&8d{jN7KV#{rs!xM8)T',
    'R>#95eo;&$=jBT<fKDgvEtTs;rUug7qm8gH<6JD6o_-gy)m7uia5ZZD6yL!^Xt=0@Y<v4Gt(Q+2bAerAj4H;#s6<7DfNFhjV4s@f',
    'hV$61qQUGtlhcK9wh!u!S#QCk{f>>8&-L3x-T4$DCU@9U`%gC(oQk%epi94@jm_KD1?-0YWWv+!-',
    'a;h7SS_3Va%EC4nxd8F=}wNLz|BnvXLePzUf-aL5!IFTdU5faOHi<Z*NMM_2Dn4@>l4`|!WrmMh1Q1fEcJnGFM{bpi~|y_5vyVN@',
    'TnmfjOLYHuAXb|PKVq_T?`lT9CsXZ!aDT%r#N5iMk}xPXbMqBhxmA%-',
    'gC<nVdUhQGrU6faH!<rF+OB?I$GSIIDPG{TZz4!ANy$QFk=lFl2CHYZo<7Y348p^=WNW>5&L6ACE)Je%FOb&hCuAt%ehLP`glR?q',
    'Em)@zK^Rh?^9Xf#V{_mITi_H;ApqoMjhU6PdnG*U!e@9(6)LZ3zqFpAH4$u$~eagcgHAn;(q5m4R%s<x4xW?bv^qA{U_GDJ6d*Pc',
    'T%4gp0`2(I&Y?QKJqSJZ5=ktnO9BN9tYIy@#B1~|CB~EN&VhlOkDSg-IN?RNNy~Le^3?jFzCSPeVeKDY<v}-',
    '%OQL4@xm=3(U^ttV;Uz;Xb<RQJxP*P3SezyTSV=+fbX8y;XFjC%CNe)R+z7*UY%&`ae8<>o63t;6k<ENSUl9L!;4TUNln?Wmvn48',
    'c_25~T+Pc7&94L8*$vLOY77Zp94pUg#1f5|D{VAg#weD=CM~%#wjbVroWA{+lzp>kzTp;Pxxtes_tu(%capBh?ORR9(%>fQ&%?<J',
    '3m;cX#Qqz0B6_HdgZ#&LLv|*%mPRnO&KnAJL${2;7@>UW7q!lCr1JAH)UOp`SPJPvfs7x3-',
    '{kGVtNzl*rj_5FMr|Rb2gA`5l7nGuV6(Nvg%7|t?DPN(D~T`4d628LbQO>}!(;TgicfWGWX*FbybKiKbGYaBdXol4)U<yRR_3udn',
    '^*BLUu{$E7djU!l|{>(^7?MyRX6MX4cFC-4iYcX=O33}p1AF6YWLhav)>3O)!P63*2VObgz1UYL!jef&-',
    '47wyjtA#`Y&Z;&mXq*IHJu?em!bi3BL&nL(l0DpMBVEE{BS(0C%UWnNoZ8ZYTK_r|0w4%hC(D!r_?<7hF)93CG>>4^%<N>}_@=Mi',
    ')%CsreoQ#??xuXlY&}qhrS@T+VQTEo<?h5jHi3p4be@+#+xXN^14FDL<1FF`aFxVPU7TUND8QkG=q(WInoj8?-',
    'l<ap_xnjrJZWR=?@(+YRM-Tao8!_3CVT*zrDO$;W!O>QayGEfY*AE>1;gezDfbM-nXIA=qi1;ie!5yuY*$dtjvfgvHw6I>ZjwR{z',
    '+q_PH4z4emqQ>0H&E)NY0&ah~!f8$5HBy<g(q1;sXd3`Ncw{Z|Y>&*r&zS72-',
    'UK1PXjU?2LTxy1IRTxGoR?=h4C1>6k2x416No58%_OB2I}MU$a>IV|W|L)uQkTtGL$p}H!~E9QAw=Y0H>kn3>{>aFhhjS;#0E>If',
    '94uwq@VN$RWFo#9c;HsqEA3cnN&1`*N3@sh+O~~^rE5iE<0F0*dDx=P-%qR+TqZNMvJ)Hp#-',
    'Yh&SXfHY7t;S`Nl(*DTDN1W@%CMD<lV+3d=zh9dKSlO;0w>2U(%eJViL+j(@}fVI^E|X&!^bz7`!Ok&%Waetc6MRy0*gh|rx~y-',
    'OWhJWEcXIoQl5H?CW-',
    '0A^1xi#k6SxfF{=u>xxWN;o)@;p0bN*%$7@kq$pzu6iw<+fF2@(DxpNQ0Lgn81RvPxX9y7Zb!l@GEA6AwDPbBi}?gN#&&Fl686?$',
    'Yn4JyF-evz(`>n?vTNE-7aeL=fp<tA@eJtP>`P3?GVCFN%<EVZ3u6}frAn!WY5EqR_@0FqW`%dwMY)22^Iu6;r~(-',
    '(QCI_MiA(8C_V<+lim)oZv}pMV|Bw7(I`-',
    '3|q24w(}~@?x{e0Wdi(pWB?PFYSIT6qnn14_9}GvI`rLIDUGFJQ5!{xK6DVfSDrohZiq*f)wRU;=FDe!f`dbg82}s91>&Us0TH+z',
    'Udk~=VTGcK0JY0fOgk3he`pg?>&Wj+<Ku3T}RJ!{wVH%Tu0yY$hA{+MEths<f)%hq?W$A&iYZ0Z&idl`MOrNjeSn9H%7(DS~AM;s',
    '+uD*61mRCOR^9q)<H!%-I$z*{Fg#!o~`n$XPm*|cDO+pe899$>1zKP6(6uZY20+HWh@e$QX2C@0jSPM0-',
    'ay4&U#Seo6pCjbSL9&jZt!YsGwG(`}2@<ZYEEsv`3?Lr+tj?Uw5frx_Qr^qN}I4v82<Z(Ou2WOWJ|wdJ`s~WckkjPBq4Dwh%ut^K',
    'hw-jlMgp7LBWPnr)W~kt?Q+Lz!D;IS=oXBlK2%GVTUj8m&RTAd0Ps9Jfaesav^!t1F8A3PcKoBz%l2NLt2?thIqk=4sm)9dixQE)',
    '<SwGdOF6vc*Sh;GOj*0WP~EB{#*P^6f<}&4a!_^=I60>L;0e=^V!6!>EHX{e_61Hk1@O-',
    'ydH2AC|NI;I(@x)!q3FK0=(LGGOxb9I}WHOnD`{TjH{ds0hg|bHu7Y8flL0Q`^>ZUOxB$WG$A>HU0|Fkf(agtwOS0<TizeOJ?)&q',
    '`Y4FyPZ&4LoOdr>Q*|=J`PQB(HQ_Jf>ipaB6c$_vzXIk%DW(KUZWS2v0qRchX!L{v)7uV>i$HS^yihyaSb?tE)Q;J@-',
    '6?QPjmhFxx4Ng_qIz9-k#QQ4|pxT3%Ty))Nefo=kGwiY-93@P+ol@#Eng^6)G?=C^=I-j{u}zWrL->6-',
    'vIAxXW_7e!L&}JlVDtYcMhj&dr~`X)G1S!`TVeopts7rn{NY@hq8ek79<j_uDo9%_^JudHp5ir)7fo4)1KW-',
    'i)3K(7K02KQ9egWvFU)?iyXSpSq^wy+I^{%eirTU64Gm84@2?<<QY5ac^}Cu6{-',
    '868Kn2`q50uU#LPAM6W?G&Q04i_G6b7QCU5QgCiB3WE9xV4ud;O7jyIXg`;3(s6n7MYNL}EYzVgH355()8q{5tdc&e-',
    'pBO_qm%zAPzXFFbIJqt~kjUxPR?_#BQngT^kF)bnL_xAUW8ZdFJfax9*~eY(LQ(J~TWMFT_z1jfOXN0I15^iSaM&KsoKhIbepB8L',
    'qE)&YWn2+>%<s(rgp@luUowkkhcYrx!j0W6t;lsnQ@(cDlA4K?J5Ssi*>K8q=0xB|V@-gS;m+LUVOzT9E5pucz)-',
    '19LOVvI+a6hi=kEnnqq%210<fSd?d<(`n+goo!5hxZTlP?MwAGNX+rg9r$fEpu!l`1ZgV-dVfz#sBJ>-x5A4BS;s1N*n-',
    '&|a^((m(_k;rpw^W5E0FAB5wa_8e%GhGZ2-',
    '{XuV8reI+2a<)6Ec(!Ki;cEY<@)qtc>302;#`rYl?gss%got8iGvtxS4aF7t}JJ5+RS4Qef_j1;})RPgs+srz9J5FYchJIs^y+Mk',
    '{Uwm>CP*it2u^p3x?P*T9s=sA<Kh7a~uzFt-(8`m%DQA_h&PwA7<@0INFLs_Y`7ZuH-',
    'y*3hsNoTV@*JL|KG%BaGWK##vU9krb9{lruo~r<~TVXd4ZEa;O>**}6fEUq1y}WWLMab4t@c-',
    '+T#0HCW&;ZKVH%C&d*tdMs8}se_rf+Z)8H%kEM~PF4{E7RV)f28&@KIxxJS9<|+|Txf7$MdSWk9<iJi?L&1P`lAP*p3k0J4T%z7=',
    'g7`s7WwXnj#x(vQn#JH_uLSZ#e>527XP=1?Ozg0P}B&ch+q9bG1$M^Ei)1@f?;-',
    'l|LfP^OM+Uj{{1kc7Qf$x^_u$qPE4nN|LZ?9w(I3+yZ+rc9x=>%`|n{SG5YtzgkZKaYPKhs&+zhJ(uP^%+;}TtJ886<El1P`Is1F',
    'O7XJR9|AMe2L2Q0Ee9@-sHB0<%_znB|OPW&LRuYKWl-&NF|NmL}|NLtHQ~z21|NLtG)A{o7?fN(A-',
    '#yJgZ2TtuKffCPfdBeo>G#LhfBE|TvHru{e?I+Z?*GQ+pXSdZ+3jfidt<Zu|NP2c|N7PV{q|`W2m=4VcQV9=8tpz~h|TYR8Pol}Z',
    '3MC0Y$b{q{SL4<{@b!88G<F()bHl{KOp$uo(c1x|2p%Zj{mkVN22t(gJbg3(W?Kqef-%Gd@Zd0PsGncncth-',
    'Z2#|V>&>UB)2;uXRL7s)CM10JnX?-',
    'I=C1kIUw^6E|6AR$_BL)Dzx!9P{6wB<MY?`yYuE>*cW!Y=kPDJazYv75mR2@vieyO2w(fBMy)(0~Sw1A4uLxQrNMv$eJMY=u$eUn',
    '!C%foT6g!y&4|1Ob@KEfE?)s;yl<_4gG2aAvo0n~eU;kr(*ZHc`@A0RR-L5GEdO1UyoLEd?@U)W+@P-',
    'ef>l#BTgx|rHh@s)P5=9|y3mGY-AtUvCgo}I6dH8U8>G(B4OZ-x$s*KcsG#~W~NQw{;oU+Cb8V0|F=<^qk*=H+VxDm}(HsEVT-gX',
    '*;^kLq_h@XZ(fB);RVHPJ2^Inwe77$ayteQ3Gih~B53LoI(ybL_j3RO|g;*1g9(ziMJR1Z<o@I6vrjK)Nf-',
    '<3;Zr_qw2x^4Sv8`CU7v{G~!B;-<M7m@b?0dRu45PMKh63mG?{QDXKWzouDPROXh7O-h043nM%BFL-',
    '7w%`CwZ&PHPAy<;%DkvmWBzzMq4xhgej(o1=s*`Kv0uaOm!4hMh0T+5~gqpUA@oS_?Z(<O_aC6R0uV(VOljS-',
    '}jp@l=OSDxZ$~zfZDK8kkSTj*Fq?&&QqMhbY1fO0S+F8aOToE;1(B*|(3Zt32YI7DlU9)%Vc}{{oNPwm`VCfvZ-hZ;tqBDk`>XDz',
    'X`gEVA&zUyaO4eNvy)W1D`KD>ACJ8?7YpFl}3*(<Y4|7QP<A=9D+`J3zx*D;P=(bg3oVV>{odopAt`C6F$MqM7rQ5uWw&FR$B_Vi',
    '>E}SU;(J(PsY7u8Da~M}3qUhu{XY}PGyAi(w8N~BK20ZZBvp!{IaS|hQ0$p(*rPy$+w4R=%TrV40i`?poBGF_7(t=t|7>3^?*^8o',
    'rlpef$|Igs!4NB4M@xyJk1GB9m-FK_|i(QQiC|eyy`1NjnTA4~e-',
    '=16U#FmWeIslb2jInS@h%`rh`sIpnl&%ZWc1wH;EG`zz(KOl54B|3SJ{95u9%ZPy3xhBa0Lvv1u|lSd6u!g{e^hof0gG%>9-',
    'ziCli-zOKbbd`Qg>zEY40I=Bc(E7by8D4Q1z^@JW8#!)aW=nQ)>oDa`J@x874nV`%%vFPHx*MW>(BGwP3F{8n#MB=y57d1n1BMTG',
    'WlkexoW1Up3?4M4#1F9cdw5M`V6hRoUg`PTGg!PHHEB6vGykhS04wU6^r62pAmS=gUP(N!ZM|kw*|#C^1+=maSz0WM2nY*F^gYgX',
    '%mOcFLzPoXWnKI!y*<d|P>%_N?KFQ4-jyLp6vN6r%^oatFo~os2%^wFQCz@+`(orv1RVfi*Ry3GEd4`-',
    'Sfh3NbH@ufi{7)$tD72$ql)Vhf=kUmkV|mHr44YOTf$qVVs(z5nsu65{FOZ@=8&=mz%r>0=llA&146%rjo}IosYc5JS%ixCH!F1?',
    '~gr1>*KkpgeSy@Q4ITPo_{|HdVfDGpY4V-E~{Ty1Y8>b7=?#$z%uP=h~k5-ou(xhV;^wR~{$2FOSCJ(ksK$1x;7l_8uy&Sgr7WR-',
    '1n^1KGVOHW>EsB>3(-nB_)ik%+)3e9R}vqx6(NnS%FW<K84tH`TwXQ6w38{ns-',
    '7uebVjlRrYZqiZwC)I;C^6CP{V>}u_v2L8ZMc^P2qH&+cU&6;XOE-',
    'o<l(DbR^LMUQHs6}aZz!;UtxyGgpX|1a=^e9V+fn55kaa0(@P)WzCHz2?|=Gj+O@&9@Or(WM%-sBLV1;F4yEAm)Dn-',
    'c=TF6ME+46vy5v;VL*_e;3dBhmI=G5sG)tA+|lZVBqdbRea=;uWESppV(rg^WoOE*nmlua8LZ^|Kks6CqY?ii%dgu20b%JAl0oIj',
    'w#$aX`<X`E!`x;`n$SGq5RU>uWo&jg(Ag&tBDJZ;mn4*4ukQesZ862zKTdrud9Rxr=nYd?q?pAJo9RUq1ZYtCwp@#%jrydIbZz)T',
    'oWngC5}RO-NSiwWl#Ub<c;8s$bH;KRgKCEil7*uiLKKt?28@+1@g1N$mDAduDf--+q9#f1%WYg7}(8-',
    '}D~%?DCeJ0eeDP?0B0pAb_BQzUBIw5k`nml=)T^p$QAb@JRJseboB~dnax);P;(uRqa9N<Jx}>$x!bq^-',
    'cF@RqYlYJ+oPIY=h*Wl+58GvP2S?JrIZwD=uXc<B!H@So7mJIn>Dycv9LX+~0Qs-gSElEG>nP+*B2MsFr0hpF=;>?zWLF;4_L$ob',
    'P;Vi*2<lv0-6LL2X-',
    '>D%um`FmOGEJ=C9No8khn9dv?lmB7@bNbpY1g4&*IcU$DEWeYu{K<A^<sI9g_>~`3m%uP<BA;1&R9R<15A$MXldfMdUWBl5nwUL^',
    '5(Mv&_=tke+^S)+7f2H7w1Uy{vFFl{2T!WjUi0d6uz!OsiRErJ|vdg~FrpJ{N0|AAgKeeC+tW{It29U`H@JS_%AvIMUD2+rmy$~f',
    'p3gdXTt83Xr!+Zo%+sdLWJ|ynEAtl%>IKS?t0rPX)Nb$g3&N;~O?eAm~c2^eF>H)ej2%dEV@iT=;-',
    'Akl}1s~10v$j<OzOUcL8q1yC6p+f7>s%Yp9YTEN=%BNw9uT~)N$UjvXv8cpH)m?88|b>4{O%re#dt)vs*Rd@X*#Nb%Ec`<uA2^P^',
    'M&Gpl<fO+$my>f)WSh6JSfa}2qobCt=i=mNpOog#k~zeex2!6U<rwR)wW_Im+ByBWUf1LH@1;mk(YUSM{1fL7717}!yzJb89_XmO',
    '_JW>6tkf-mO97KW(QoaYefs|qc5tAShVSP(+1&TdpO$bD6oE)bF5CY0-',
    '^|5Ex)u9bLw;Nt*ub1c3HrLOJU97mmO8q2Ib6>guZ=#Vlp)A1ThS{Uzv>rwiKQy9(b`K=mb@+FcXj`%eA(xw*jMlMe)Ip>E&X6;7',
    'qG-q}<lsvGa^?+SPzur8XQ+JYY~KN`NzZ%D|k&5FR~ephtRn@bqFafA#8b?8L!8Y#>rj+R5VvT|cAVZG@|9BfNJdVR-hYwa-',
    '_7F}h$Qd7>qcV@}-',
    'Mj5tDntXu?df&*714iVh!^aztWAm~9@AEW<=OIijNd0O9j;9VAp6I+C|l$)Xw9X2nR&@odDuaXdW#x0<PIV7&j*i)HZAEbhIRKgz',
    'Y)by?eoUvAWG1te?2H)0I0`N1)P&k9Nq>0t*Urp-u&#4W<*XMWEa$*@er7)H9X-',
    'R}yzc{H3h3L29HZLGGCHNPxa#1e%jMBFaS4yDC@HHtV92tjt`Q8I&DHRtqmhAl=et7jL84z6P9F1qSk@C^rT4U%-2A7*+&dc-',
    'j1Lb9~T4w>1>{DgUq&E}tI|QiX3)A#soLC~>`Axr2Fl(O={fy^Bla#!aI9gY#x`xbCc1!sT^D1_Mu2uabx5$kgcAI>Gld;(<XDu-',
    '9`t<L_kl+}bsB)MoXLB0`l<mx2#ff>&@cw_8>2QeaPiA(qn;OmV!W!aHC@XCZ*_k&fg3?e%!G-',
    'r0RZuy8dmIIqxTDiD7w~yP?pg0vG=&UqZrZxzNV=hvEn=_=P4s~98bS?~;0Na_=e%?kdXrb58psBI$v??vDIP^m7XShC9|G(hACQ',
    'S(@-%|+h%|uqo{wxGbBf}dhn!Q(NZsTsI@O?XV8Lo98hh}g4xv^QB>ou`i^GYmqRaAAzgVdw4_j>PS%-',
    '~Vrd(cKju(@cX7zSe(L(&{6)A@@YvK%NeaC@<!>$@LP@vI=?8TYVFGo?QMDY+0CjX+kTh!5T0^#N6$rh)GRtCK)Q@X2Bu`|&Ow>M',
    'z!d4y^suRk_BIXS<$E_15%sSAP${xjStMQ(2RnI3`Y4~Vkr<PEuMJn3(aGEdfXiEA@PF2MC_FFNwnRWk1esl954OmJ(32C@-',
    'q2m4ze^ys|DUE2(2e_8x>c<V&bJCsxU?eF2FqIU*v=s(`6)i?DEFX$OwdbB=z8^OOFZO(;zJIeMB^ziEIvE%3-',
    'C3o?ey|K3!9>m>UA(!q?(=NgHn|)p7UI>^lv5|51AHcPs<p',
]
EXPECTED_MAIN_BYTES = 30603
EXPECTED_MAIN_SHA256 = "630125b3f592fdb773f1fac6532b08e97e829ae188180ea17540b702b606a054"
TITLE_METRIC = "144/150 frozen current-Top-30 replay holdout; not an official LB score"

raw = zlib.decompress(base64.b85decode("".join(_AGENT_B85_PARTS).encode("ascii")))
assert len(raw) == EXPECTED_MAIN_BYTES
assert hashlib.sha256(raw).hexdigest() == EXPECTED_MAIN_SHA256
compile(raw, str(MAIN_PATH), "exec")
source = raw.decode("utf-8")
for forbidden in ("Dennis Gioche", "Kaito Fukami", "CanonicalTeamIds", "SubmissionIds"):
    assert forbidden not in source
MAIN_PATH.write_bytes(raw)

with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    archive.add(MAIN_PATH, arcname="main.py")
with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
    assert archive.getnames() == ["main.py"]

from kaggle_environments import make

spec = importlib.util.spec_from_file_location("public_v21_agent", MAIN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
assert len(module._ACTIONS) == 719
assert len(module._HAZARD) == 490
assert module._PREEMPT_LEAD == 1
assert module._PREEMPT_THRESHOLD == 0.55
assert module._PREEMPT_FRACTION == 0.5

def exact_base_copy(obs):
    step = min(max(0, int(obs.get("step", 0) or 0)), len(module._ACTIONS) - 1)
    return copy.deepcopy(module._ACTIONS[step])

smoke = []
for position in (0, 1):
    agents = [module.agent, exact_base_copy] if position == 0 else [exact_base_copy, module.agent]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 21_260_806},
        debug=False,
    )
    env.run(agents)
    final = env.steps[-1]
    rewards = [state.reward for state in final]
    status = [state.status for state in final]
    assert status == ["DONE", "DONE"]
    smoke.append({
        "candidate_position": position,
        "status": status,
        "rewards": rewards,
    })

print({
    "policy": "v21_balanced_tactical_memory",
    "title_metric": TITLE_METRIC,
    "main_py": str(MAIN_PATH),
    "main_bytes": len(raw),
    "main_sha256": EXPECTED_MAIN_SHA256,
    "submission": str(ARCHIVE_PATH),
    "both_seat_exact_base_smoke": smoke,
    "ready": True,
})