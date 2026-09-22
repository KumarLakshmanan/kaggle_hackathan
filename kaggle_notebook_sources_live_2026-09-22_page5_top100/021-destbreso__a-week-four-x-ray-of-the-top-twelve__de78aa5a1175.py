import base64
import json
import zlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

_PAYLOAD_B85 = "".join((
    'c-ri}-I5$Pk}i1PPmxC5?3$^0@c*N$<*?ZrnOf2e$vr*Vv14Tj072HWSjAI6(nw={Gy4wn5^J_==W1`}uFspyi|mKU2mqOZ%!;ha'
    'A|-W6-Bd6#0&qAS4*%R89{>8g)sr{zJYKr%7@mBwdcp`(zbEGRj6eAtzs2)6r{^*KK%a8<R1Y`13wN0w{^#GVR{x6subx~-_dY%J'
    '@~4Z{-@B{$#{KBhqxk94oxeLdzxWY9)AgMze{mVdTbwfUR8&tALoM#J`qA+oCssVwxc`^WXC1$~=`P)Scm9)GeLL@%H9985K9%#1'
    'sciJjjHOR$yXWVZ7avxCxVgG+44BXRWmcP~blxwg&3>tPYTEsNbNbEcyhqXMQIMx*-sAbr*;%8{bi3W-vr8~|_4?+GJMUclVcxlH'
    'b&mN}^Ug(ceua8U+I@fRPOmRkf4q6;-Zw_AnjN#JywNdf@mVYVRO}eFzdrpTesgp6)5W`+dDptpb&?j==$f{>7Q4Fs>gS&?ZUWZd'
    '>YIzV?tKiaub+MU`q`Wa(;`Bv7UK_|^{+3wxca-7-=pVw$F|imc-dH3x;1#q_^uhha@Q9Z7jGL{gtR(^m>omL|N8Im<K^m)?(*i{'
    '>ifU`hmVc^X|sQMl>R@&({~piF3ua>vR1c5w<OIrc};i9_=`6em#f#8H&<^@TRrn;&$89?!2|x!fBV1x^Z)vP|MTDezyJKV|EJNl'
    'Xm(9oTLy2c6b1Fu?zz87|GsnS-$u_ZWu^^3&YE&iq<{FI|Kt3B{*Rv<UANSk#z4psy8hFRKaJ<B5LYj6y7>OXWlO?!lK|0L)&~>t'
    'osaJPo6~=3bZeU3(x>_e-M(^{*Kggs)vLD-+t{kndrOyTX^+D7>v(;2^HW32SWB5{!CPyqwS91kXLr~{FXQu@%U7r0wG1NK?3T5p'
    'yJ-+v345^J?LYmw(O*k>X&99D2+aMbQ+M%WJb&vh1QCtCTk1<Q(i*GUwMp4_*Z=j@Uqf~NZ?KAbxB8Rot{VNfbeN|0DC!dyS$Gp;'
    'V-d5a0wbcOIuGs^8^!7Axoz~?)Ll^6{0P1N`Lv-eSxZ?dtB#_qUcA4ItLLYe?p>o})9jcZrQ=ub^lNO#?u;7Q=(?q=l(9!yPS<ba'
    'WenZfP5f|rcGdtjq}e&YgFOFk_1_YnytuhMxg6R_lnjJ?HGom7lr@yAfr#P$w=jd#FMn`9oQBnltLykfTnojzhv6*?PVn{3L`=G;'
    'h<ft7VYE-s)71ue9iJIh;vOh_b<?F^q*PQ0#mBo~)73?YSCx%+dOnQw<m!4&()Hy{T>sKxy`KDddJRMC#J#zU=~wcUi)m5D{-ldn'
    '*CQ)%=X@OS<;Bf){DP9_;?)WN$931RVJ@8?S|HPni_3Q>!TpqOraOOGxBKDDmHx(-13BS|=KO9DCsYir3Bjg&RGu)q?!xM-#jALB'
    'c0h}ksCkRZn5xD8rfLy9;o~}r{^I=N{i(ky9i`zE9ziku{flR>2TOHY_PF`#^~+~}{<{}1Uw)s2cG}wT!}Dh^Uw-#`*ab(K#m#SC'
    '{0SRnvN$K|S5IDl_sz4{-=!_^DI0G6WgJ5qe4~4iJnFga?wMpGJV;%A^{20gJ#o^-xcA2wFJFK4r?38x7cU2+K$oZg{M~nd8c>fY'
    'ZBN8v(b?Ik6dC;s^$3_9%;3!-oZOtBUSFMbKS3hTLtcQxEHU!?VU`T%g_c0c@7HFBCWUo@kl&L5c8D!Lx%1Qa?(C{+_xX2!Uh^}v'
    '>F-~>_=iDg%*Ly4PcMfh1u#9$+!M@tQVT50S9kN%$yFR2S94LYh3-Y7pcjgQ+@Ld&@Zs_z-1w$IGBfeLlJtuYKzQ-|dQwBH@z0hU'
    'Yqc6y-JmF|2e-XWtJRvU|Mt7_k4mwR`i*^lo5!ruZ;DuTJpD!u{bc%$JeA7M^bu7}4JVgrIOsDqYtmRdZ_*I9Tg6c=?x5nxF1aQR'
    'xu#~WHE6Y>vs{y{^|wdG?NC~rSK4$`aYU9Sv_UL|fi_cdf|n7z`0~r7%j}$dWlKMKoI(`EpT{H`V_Kr~66RDhohLF}sdXNOuI7uB'
    'UNsYw(o?0IFTeZl)r&z7+NK`lgiXUfP!H1G@?u(gP&M?Ryj5QI>p=#%BM#7mbK`5ZQp@xpZ#`C=<*OBIJ<#-RuU7OnrOH3w9}LJU'
    'Ra3#l0V=hJ2<_FWjH^$mQ?;4tKPDUcj}m%!qtUR2l9q<<)~HOF!!_zoCB-XCs;rP|HRKhdi)P3xL_O6@G%B^Vg|($5D+^>p*-}Gh'
    '%9d(fo}N^yB=hxbO=IC}+1M0>-d4y=HB8}sI(5>XRP#!2XH`oHF@>K+tHO|{w`kQ#iJEFV7!+;AhDocEUDl<|cKKmi6*6PnGDFL7'
    'ip-b>&@c^#>n-lyVqKa93Jy@KwHg!$sKKUAZRzNyZrvNk$~t!Qomtdr$8#-%`BtSZKHn8dEf%oSj2~59t50bHTS;fyl{fV@v-be`'
    'g3nvjbRWn+Tw6;~fya%NCmM^a(gk@nwlp1|%#;1fS`l7p{|U#_9Zm;ERnZb#2)}A)($%c?5ljOhv|)Tfcj&pPPwr^$8p|3GUszi#'
    '{S9-MEHZa17sjNi#g<MlT9{{P8nrNAq=gkP8}tU}MP;f_tYoAZ;F)Q*Y;YCCCx@7}f*u6%cOv&K1vpE1*rA478t@J#?o#!;TdT^?'
    '7i5c6E(RC`_ING^X2qw}uWasO;JRrK^TjR(OB+50+R(6E@6oUmLl5#XRNk;n9n0tDBn;xY-$9iIiq_g%S37hpa70l&TV7OBl;Ng6'
    'Wp-}+8eZ;AHnOq}9V<w~qd;3jP<QmAYF&A1ix(9X>bVzHZ*{Uu!-~oT9W^Z9VsX~6DtjLe^d9WoZROly%0$Z@y+9IfbE2|o<G7=S'
    ')d!l6yPXGgsjhB5*vKW@@#IGK(*otIKEEwpuJS|}o8#oiFm07KpHlT&HdB*InU>?=9;U4^4OfIFdrVt(m+%$a6}~b>B{nrw)@8RS'
    '+09l}<$2i9r(9NU-mI9ls5%^tUsc7>M#Y=VUe@s1%9hub+)1BO!em3C3RyWj?_jgaxr>%<0fVej^&LG2T<y}Rx}iN6&G9Yjld|dg'
    'Me6ewxXu^ai?{k=`EtE?cSE-2q_|a?>d$Y@04{c{rBWYLn;ODDsWz1}-KT8})=Pd5M*(Yv%7oahO|`v)W4De-Z7wz2aO_f3nTvN)'
    'r<Uw+*K%FM{Yjl#InN2OWEK`<Io-7)Op}&6wFf$9i#oNm<pR)^1zo9AwG{*3txnbAFuzuJ3~%XO;jKH*@h$3<*n3)|VyO+;gz>Lp'
    'xB6e)*;#xO!`V;&>t5}57tiY+jk)>Yu1w+u3f6pnz&VGaYB^DyA5qm#i2=8&TJu~rHLX&5u50Pt^R86UzC|wzb00<9P~Fnn-HKM)'
    'JNRUo-I4diO~ZWQ4L=;;3Zif6*-fyYvRKXMGczZhZ)p1sbft+VO<U&&O`4Xed2G*AN_`yzvkm&y9euCNn940#qGbyDkT+B>zg6`X'
    'XRG;q%U!_cVKKHt8|!U{Y(^%x8Mkz~Ah1RpQfx&{_bX!sE1Z2o=j*rb!)d&vQj)zod$CU4JpQvlliJU3IjmJhw2U(BnA(%yS9=~='
    'cQ#a=Q0mB5s-kqC^1K7+XL6Ubb*b`H`*XLpm1pI2tdytR6~xkNp4U|ySCjIr^D0})vlwBlyu8+^qLC`GP<!&W_S8+o^<LVO&$TB#'
    'vi4-VY}uvS({7P;T<zIXi}E3}vKH&j`2ofSx^p^6dfVC0;yGnps$&|Un)6?p=hW(k&Qtd>K}joQCH81hH3qp3#rkB|+G*fG-AIc)'
    '2<z+0oZ7_tN>;jY!um$dEzsJ;%UIve0jh2(QE^v`lM-nfI#Vdt$mmb5)1_En%w4Cu^drBc>s0TyF8ST&_%_!mIY>b^51H=JZ3|7u'
    'Er;mQ60GK@pO0md(yfD3n+N%;FqGxm98;NE{Y!J4YIAhQX~RLF%^p0j6@PS`J~~c+g^tr5=Gd-m)Xl^0hvh)s+tIp1Np2abeOx_9'
    '_s`?m>AS0opO$OXt)p9wavhb8Du@(EwNdRSRjYHYN?RtXrbjnX_l2X#kxf+oXrexvs2{~dy>|ZH*XO5i-d^w3evP6UJD%LAZL&l4'
    '&5hlANA_>COUK#*XReE96C0j<MprYR!jsR~YL*N3<TJk7@?t#sOsulU;>l-n)uQ&vXKFQblRWuMujWYvPd+oNeU|%^&+Ka3pNj#I'
    'ReNK^Pjpq=+PJ}18(YQ5lK1ZV^7LO$K3rU#UY}l^yR(ry17|1wNRI#C-;Hzl&-H!!k@|Un{`U5B#Qqlb)97z>E^S<G|F`uF=Lhvz'
    '-leyUna=<F%kAkF?#eOrd*Aum{oknvdL+sCjn32kdfHTp-P!4Rc+`fE+VD{uK5E0iU2XWmoyW72gzmH94DkO&1Ljxv>nMM9TRk`J'
    '+myXJ5&wAd$FE+#dVTW!vzOoQeB{-O=ihz%hvqYXdhzA6=ii^qX?h3i9yafr)73w`e9^l7^;h41S?*t7c^Js=;@Rfo<@U33^XmFC'
    'y7yn)T)%UdS8qRKvtL{n;@PG9`E*@0?#T~~zPWLi;frU_Uw`%8x39Lyo&CJQ$=R<P3~l_ngRi@voUu1QI&$|GvbUaUQ@{04dl0jS'
    'ZX3(47iL512Qc=<4@{n%UtGuT;^N)OAVKS&{h14q7{<R?KX}sPkF%dn&H&lQ+H)5l<QH@3INY9t$Km!id>n2T06F}18$xa@z_n4*'
    'Hb-n$xaErFD?0r*-;v{gMc&xd>^Hil#P8l)b(Q;@KY!n?-)?OQg<d}Ey-*~|)x?SXlx#e|&4a^wYjI-!{39oh#fc(in|%}-*^C}m'
    'Wc2f0t<1S_m!9TV^QZ620Xm<9t?|*u7+SMK_pD*^`F(n8UfmZUZ1Z6c*EeQ=HWN)=G~U!Rsl9ujMK6n;Pv4&>a=!8#t6-m$&i4_%'
    'M^oIjza2Zso}TW?kvZSR_Udg&w%ne*TlLx9`q{mzj;S+?B~bLg+Ouz0JIL0k3P;q=nYw##AIGYYvmH?G*{=#seD;*OMZ@2<r<PP4'
    'e<wXum(}`kzXsi<>F?9y$I+h;;|zR2C*!@w`-nCkZR|%*Jfe+9wDE{GK8^(;7FrOrvG3pAiV&RdKsgV>mHl>pi@pO9g4pKBoqLo!'
    'W%YRcc+{bfI`kJ}{XVqS{;MAE9mail==|3{^54{W7mWKiIo>_v{!Nd!G49{Wco!nR%`}J@-o(u>h5h*UBAs_=Wf8BQq_Ytxm$4sC'
    'M6}Z-W``oS&qP#bKc>DK$;l7a*DUAx!FsAvsUNJ5c82zYb=OGzez3k;`Q#7Q+5R;3UEOX}{g{_b+OGQ1=y#s}erR7yd)k>)|6n}b'
    '%GH0kezuMP9I>-eOQO{`(=jVF{L{sGIC*y-<H?6|UZtx1o4*8Fm3|sKSl0rXK0uTY#E|lZ@FyY057iO0s%E<;Tg~QkYtxscwwk3`'
    '7M>(>=S?!Q-K3Bklyc5Co8+WW`riG^$%o5R-)LAHwbd{qrf!%SvDq-wEH~U?*O|AewrQQdp15vtB0M)J3#IiT!F5TD;h<K$%qOVE'
    'M#l4P8{5$rD{H57QPtk@#mdO39M3N0k?OQeXRM|(MCo4r4YoYKe{FO@Ih{%fZEVLw`P%V^VV4=c%R1iJ-V)LwtorC+W?-vFR(jk#'
    'A2qOUIz+g!4Pd%+4Yn;RHJjd;Q~~BuOe~ozB>XylOQT3x45#k=q;u!*%505e20_wHi*18%gsAazoZGbGCpk&=oKu!FGkx?nQ*0r;'
    'qpWR>&r&meqiS1bD4RZfy<0krHB(Lh&CL!!2`<N<T5K}JPDNDf9VD$hF)iv1t%zTQprckBJ`(%k;^OSYfv`!}Jn2u*hQqE`AKc|7'
    'bl!g%9$|#3lsNeG|Gc_5fBN(IDcUz<>MUF9AgIN+?uXNho6D>G!Qv-p?($7i!*8H`KMWr>q2t<f*JUory8ii^W;)1O{@VAG50}HV'
    'te*_-dY~^+^m}4{Pp8@n6ERfFN&8pS2vv>x>iY8ZL!5dqAG-Zw`^(~U>v!`by64r2<KcX7`snV-+xRc}JmM2_$A3KO`##|RJ)y%5'
    'w)b&1yWVw2?QKn@Kc=J2OX%!<qH#^>_-DW4&itPxZ-qlz)BPc|Z~bG?hUERkopEH#sR%o+`@QX~|FnJ2KPBz`{b;{G-xu_=pTE1P'
    '?rv-I6VV<P%g+&MH^T~tbdW`BY{_W)#Vh=dw40;}Iib*qI-0$_J9K@9JGBt*xmLII`z_KPj!nBh4(&@M<WSn}gX;Hvd|$3-mg`7+'
    'AHE;3uikA02d!Ap{<~b80HE*kUA#V$v17975lL^8dNM@7aMvQ4DuN39ohOD6DU&Ir9nnPL8PO4~i3BcTR4Ua)5{L=GP)>{`(i<g&'
    '^n$<|Ha-L)La$Y7Avhw@OGxiBy=+qGxU({|zM#bLHT8_KK(sWz7dmNI&>k=d<%C7wj7MQKRly2n1a2zdQ%!XA7#X)h_k#5d_chqu'
    '2_2NuQU}sUs=TMTqasGEglADO<~m`yCc>!>obY#D41<+NoZy5}p(1pv7)Ik6i4o)DqQfJUQT#d#K`Vx5v=Y`3%?*aHdKSIa9K#Wu'
    'a>j(RMo9q`4KsvG5+d#dtrh+km53%a4GslG&;Zv*r=63i(%g7Pi7-YP1GED^D~YE;JC;5qN_Z+*$9PXUh=SQ~X&+T@Szw}PxTatL'
    'RYH5qV^p3*pfF;b8ikO1$l+l!vn}fkf&z9Zk=j<nh!h0N7)cdL(#<^R>IH{HNfs#}n*mWtx?CEu_k>4qR&eeyH>!_83GPL&@jTRq'
    'Ql9c?RA&MjfjGv*fF9h3K!*GAoe4%9Xzxv+iT1&ukhsv)rYG<levKYIgX35uD*X(p@Q`{1`YqNY3EC^KLa%fmdx>8l@97yE8S92|'
    'V=^$sg6c>(CNHM9v^$J;rlxr?Y+S2-k^zhU6E{J-q!NEJW`;QseP@(&F+ls!&=YM1Bo{(0L>fmLO_1QGhWXS}<xG#2k4bPIPZ92v'
    'vI=9;Fb@Wpl`tx%C&|0!%V|$i%!&;0M5$Sel7cFbBkd3iO4GGUT9V2x$&<$lL~r1xNMx(D;o({smhJ?JnWIS(l#`4oMgpGq9&KVa'
    'd<PLy5;KGK!!V;s?9d~%ca`@^<{{n~MKC=b;itsvOEM#p6dBQZ^e=)<a|5wq+KZ$Sv4n~4NC$3WDli|t=_9lw*i9AZ(49(3tQ)Xh'
    'VjXCh`f1KJ^UzfNuvT?<U)mY5HpzR8Vtq#?Ay1M(k{%p1zK@D0zIT{$mm~@^j@A?;NehN?gZmx99;9_t5D6$8JRh-uF#_l!!A!(9'
    '1ucrT4b9%OL*#u4-^aD8C{xgmO8a5<Ju#{eAT4PjpBhqF;8s|y4^Rpj2Q5$<UBp~~2jD5BCDH5fr~%~++NO_ACjtUgP+H09S{}%E'
    '=C}7%r~*qkH7=%o)u(Aqn-ZiltyK>B!P0VR=M-L1k8AA1Ds2ehFSXExNrb$@{v6W`=^%KZ9AkA3_nDLtR7WNw7{R0?J?w>;R-05$'
    'Hj2~@4kAUYnmLFXA<NN0#2(y1R4L{CzlzzDV(*`7$CH&S>8^XohEZ$pZQ$A&Xb8)VaM)P*TN;lU;f$v{+UWMSx*USp1*16{fJiHG'
    'i*~!Ww<Rz?-09DL&i8?~@gFhpT@8Q20>l2_o7w!{$EC9TPrIM?{rpbO37GNZ-oW@+f8LMpccZ#L-YEC;J(7hpxMT!&aXWUIWG>*l'
    'z2D5<L7yBfGdnT6xyStWi`TY2d>ps)eUW}&?vPzBIsI}yvy1jvy%*@6T(pNuh+Q_adpU^cXk(bkz7Xq+KKUS0#F7hG#VNWGVFy~p'
    'Bz}OQXDC&M0=smM8JOeVSYUnF)Sgr3jbYTO#3x|ZfaL~Y=U}jk1p1`&yaO5m!j!tVfDhV9?qJe-EjmMlBmgVGVd56xwug40d<Xgz'
    '02HAxpus+X22MGVu(36B!Wo@>DpCapSkJBS8VFK*n6Lu02Ij2i!EqBJ?K=rz-x=?W>~+*Iy1UT%pa6>ioCUBSV6_blCTs%Cu>D!J'
    'kPARShX6+S)eqPa7z<#-4Dc2=s2|3nS;XIg%{m~?fG&9tq)Q`r9RONlF|bSs7O>s}B6O_lU`lJDI%_cii#6qik)2bLi{vl2zS9=-'
    '0mN@QFT2333z{<;0|10_UK<|4eg}jBC=L7nK)%yKCdA;Ri7s(K0EFp|;y=md1kfu34E_YfYzKlcLWOBoq;ncHf)r*kKyE~m^x%06'
    'GD*0nq*D<b#(ebB2LpN0sgIs^;25aIR7FT9xYwbF<o4U*J6rP<fN;1@7&YB6z~v%&GWkF|nxdL2%?)!5kgWp|0Aa>54>_a|d}V^u'
    'm}Ti~4+v&xfR>=vfM%d)6}=I%qxdBxd><t1SdW$g<wCD%2dPmJzzBd!cOtMTJ0f~!A?Xl#fK>)WtCsPd34*rG;GO`AN<V1<0yGmL'
    'xkrGljK}>RAdCWvW7?Uc(nVloz(@i{b^!Af1L49ZM^#dB$&Uv?!x~7UCM7VLML&R=R)rWb?vQ2+02z?a2JTc$4zpwpB-cTI7~cn%'
    '-rynuyPbhLhz2}GlM&#MLpXwV&WM=2t*X-w1O&9D&~J~G1}Z57Ky{o%$~kdFM2J<2hf;|JL9h~%&JGTGlEA)-#D;VSZ0w`<&`aQW'
    'a<ZWP{qpWr;<O${gTb!XDv4`gY@z);<)X96kfX^dXgRoVtz;fLhYIW@3{PP+$rC8C6twcrN&`tyEJhN9?^WM*T>ykm@{b;{R=i=s'
    'xfr2|oWO(#4#}4e;sm__@YF#|SWCj3?}@RLCtoV_gYz<ZwPM2gMjOCy9i?`RE8#-&V`5pQ*{9GF7zqVjPd+%sEDu=2n0BWqgc&RZ'
    '>4`2UyX02ZXk1||$&r|rCDYm~%6)(ummXTtgUwvgppvhGcRof~Udb&(Ea;D(hFj%b3<3|y@!;SfGh$$U9~71)Gzb<f>mVPr_f8rp'
    'GiVBo-CE;&2%5kMhzA>Fz(9KGlCyz%OVfrEqQui3h8c{+7&{M<#(D|hG*x(B8_&Tri}lZxN^W0pQVvcQ7WeXf?KD=&<!Ny3*+jc1'
    'QcLAT&`C$ysE6zWbR(?pAVAnO6=nuBp<^bE>I9Rnv#d{!TN*noe8_|c+ZFGO;Y@}=W5h&o%e8dECRu`B??^8-*J!qPXazetC4(~;'
    'le2*K^)2JEH@aRyW`+QelGrt&U<AfQu+_wn9%e>K(<MR2*53D0rbQPpD+*gb$G-tPCw}!wS7RT=-pjm%I5-HmkG|uvkJyGe)Dqrw'
    'eP=uH8j>Wt$U}sB0`nj<;6Oif5NRrym^+AOdFG>gh~LXS)cav3i<icfYwlA7&AK6Ph>_#}vn!W~?Q##*PM?AH<jxa)7uN=?sBBYu'
    'r-<b}W1CAMXU%mnfc$QWJL{el9S1INOAIWPf$xT|-v$EGN{=q1<I{fYKl>r)T;5B5Q^RTZ%a)l+-lM&f^Xe1Oet^u}EqAX!+@Y{d'
    '`+hwGnK4b7>5nJH$KiWhzq4t4zi4@1x;Nc9OLX}Rb<6Zjp?5Ct!oW~-?Us%%GY9L)TlQ7|@RG2Q??=ubO3=+D+%tl^lo5o#0q^oS'
    '7$iXdz*U;slo}F%>^ceSjY>nUwLqtgzz_!rf}Pq4pfeF*Ms~>)&bbcB3qxSW2iQ;eSELX-_8SjC>wrusP&f_gC*r6!YCDf*ZN^5<'
    'H-c!Cu9rbfo)^y2+d#0%M-*YsYpZ}jLt+##f6yVM>C@1wUiQ-V5?4_J!l(NVmM|<{+`*rn1e(K)%LHsf?_>bF2*D?x3PvSh*Gjp*'
    '5BnE*7GsymQ=)HK$U>E%a;8094;(f?Q^W!#0{|;OYye@ffPzfqqvH@@GQ+$UAW(yQDZ~IgFO`K^j`4NU;erF5f>`_=pj(FY6vi3`'
    'PH;dx$v`OXkd!3?@Qi5zB*93)l_j*(N%<%#Qd~Fj-C{;zste+nh|$8_PuXBf1c|k7ga<lgAQb4!3K>(PmIsm-xE0dB!x&R0T1cB='
    'r)3O@Ak142PT)dg9J1Ho0O@*Rfgn2JAwV>V*)TGBSR4;fX_6VIl3d9M(93M>lh7u<cWaKV7o+ycQIWFAl8XUi0%p0Sa+6ePY~c!I'
    'Lw*9FSqfJ%;W248<;cb8A^JY88e%#bVwx(<APFh+&fG<2#1Ob2!0I6HDNn<)PG}IFR8*1~m=Qq1oq~)?m&7_G+oJOt5~pO)T!Hth'
    'OR@#2>O~U%l;6=O!NHSpJ@zy;JqwY?PWzODLm`K~F@vUnfN34?D>KkE1UQ#6$c(`QR01;gDT&NFF~|(WJ?P%0BneD(m-y~eo(f<v'
    'NWq9@!pc4>7iHqRPB;~lVZjZL5qj$-{@Vr7MaGO2DPOUbaD0oNNq^~vwdz#hK-J2|lzS&-?7(Z?qi+dO@ByIT25GhPkY%UAS>4-^'
    'DDyV;9DG{6qU$Ah%tdhDr<<LE7V>Ed2ls9#f;MSjSkA*CBa%kPM3T`1<=xQq@2F>>Wk?rIl2RQdW?QCprXaa2Kv(EQiWQy0)Z;H8'
    '%`q%R87+fMCxMX3!2&e|v2l{8EXyQZ&_6si1zv-EDEDA67;qv=swlWLnCp;C84shq>`k69Y#H1ojc>94kS^&Nt*pd~rb0rXAqrB&'
    'q@4pb&JTN&fJDenLhb1;36y}2)KJ`*3dJ>^_7c*qg-h}d&6FHk9=bMR=U^f+UaF9CarP&v*K2jUHKf|cL3}*rSbZw}EhbgrL`uC8'
    'GSHMw34H=dNFox`qQn*|4VVcgC%p&tl=KpdB>AdSPA>E!$A&9C>pBRa>a7o+g7p|EX0Fp%vJyItTA4EQdT)Dem&iM|_-U;s*Ri53'
    '(JMICyi2QJ#>k*(lB>{aPZcvvI?Eh3K?S=&sAwSk0<wUiL6QRWbsrR%ofhK&(PWZ>v_~b$kxAYm*ig8zwB(?{2=BeHB<&xX3=inJ'
    'dq|};+PQnEDh@C@hQv|xhIZuJ=wa7@LQ1KC+$QF(`N%6{J*~V!j7#FGXk^nDN2%YP+CBZV4{YjwM*Fy@(cTR4P-%ucq#Qcx>o~Mo'
    '5UHdK;-0h>dtQ3r18cF*^2!P$600#n@CY5q<bq6kllF}?|0OY4yC4E>?|kqeG^rqk7qDlNE4~J#bO$)SXO4otC*QaG(F4c%#P^!}'
    '^|gF>hg^~OHFPWelOpd}q}zO7yN&p!ypv<ldl%a0Yqh-&`EFi^1$?jWNBIyklQ7IgV+sVWcX4G>q=jzCjNhd(mgIxj9V4^Hl6Mf>'
    ')jE>5cztMQkX@FOb61&}<bAz&7FkZI0@VoU0{yozJL`@*GKJ2>uvSf3tL3`hkJeP*s^5R9@-9B2ydS|aG#DnvRYpqWVmRofFj&`l'
    'Zp|=2hWSg06T_JgCkLY!SegaOA`O&U!hwrmhcarcw8W+)Ay`O)MgTmY@<BohoOa1Pg!K-1-=%Y2u)C>XN_a{|&j5i4-v=CG6-}Fx'
    'u0@WgnNGksjwYS`aKvk29ZQZ=;1{k5j8{gC0das8JP45@wyfh(xGn<RY2ehZ=N$o-Fg#Evdu|L@j!EHcWUB8J@15xwhK4r572kne'
    'W;l<%@tAlf7AEhz3NX9M=o6q0oJeO12#Z)UN?|TI;LwoouPFdVG=?SE4D4&V1XzuuHbOFpr4DST$+5u!6EFhDv`^t!5G^`QY3Dsm'
    'eJ%_$qt6z-_n17T*wO<|HQ(3s;h=~7aC~7n<HQ;5(h(sarR77u8Q2~>EEn2oN2%+8YJA|vaveI%MhG1+Q`b3S0Rx=|u{L&)3hN*_'
    '1{geQw8?P?LdZbA6Diu=IR>26QLoJX_zp@zJH;yQ@C=4P0SM`k#s<a<+>yaMt8MQcO~>>cr^bT>h=c8!>J05{u%H*#DsZ&NuePT^'
    'f|v<ymF-*)aEY;E<#YoX9l;!k$cbDg@1u;Hb*7dW0l!F`B`IQ!wTU@L+rXgcmZm!?NyfWCA@81py)LHwu%4yAJ7s!pU@AE*3N=t9'
    '@Ru}>U@aFS;0*?Ox5<AY2u~2lq+~+jAw>|ZC;;IOS*u1>v2Rb)%8YEx#=$7M;nCP@rie@DxFEgJ2%FrDN^-ClG9;jIQmO|PwAU`A'
    '1P^E_i*<md+NA|zAp5c79c)0zlA)$gDOaE&>F1OVX;KQB#|l44X8hnK5+is^5+u8RT&td@!#)IZfb~b1)GSGtQ`T$E5^U~+N%@sn'
    '+`=i^Q`2=+DIji@G$oWF>5`Y1+TQVi6)Poyt%@ZQlK(O#iV<nnj#r4C^88-%E+G|)4{O!y&agq_r}REX(*Z5wjk26V+69-U^J#fG'
    'o{lL+tXY;ki;!uiVSPg*2F5$?(z?I`hUQN`^+;n(N4gxL9d?V9fa*Icv@pF>LLH>vYk5!Utgau98V&kANM^BWp&==!>+yk73o1J%'
    'gP_iX8Uwk9=7aWkfD2Bp6IOcgTJ=~aT}X+T&@&w-#YTsBv8!XmjDl*-Ql1&4F)(a}*imlfI~!zU7>D&j=5Yup7p%La0OY7=)@Qe6'
    '(!_2!AnG*ZkYx@P&K-1L+OsH@S*Mdft9KNF+)>Mw?K>>>5EYdi!+}H*hc!z<sqEO8MGH+U(|O+{`aM>5yr;bDTHe>Rho1F@X{<sF'
    '&spPL#8P1WAU`f(1)5G;+d*He-m?xPN)nP%;IL0==o1Bcy^}%VDYP{lhwFyiNSj8Gl$A1GhQ`4%&8?j|hT0V!M<0>=2xrUsb*AU='
    'hiTLp+VAJNPvTK4$T_;FZuw^bKEp(>-->ISe4Q=7+yd_(0y7`rt?L(*xmliMv9N%}-r#bGm;vL56D!9GZihSFxkK{M-V<9{W_nZ4'
    '<D%j`%Zs->2<`P+op4!9Fxwv}xt~nl>$O_9{orf0KLj)1K9BLZ@_y^c?!xza93qsY%L8a%UVbawzkttN?>A=RZl~rRT;4ZyC*4uZ'
    'XL;gNe++GNINuLS1--u%?Wg^riVuwzP8=$1s1epB3^Wv~=#8NTw#v0xlOnt#nebvL{}6|$nH)0H*G6)xtuWRyNKa<qlCso?C>c)%'
    'Y0Ac@+X1n3Mxx(So6$6^E=3f;!SJp$qhlkXoB^c!b-lOY+6?b_5H8XgtCYY1!hI^DgbU?Tu0yIiVN$siJRj|Ph(o%hN!Q#CcE1^e'
    'oXh<ztuh5#B(xm0;)6?7tSJ@ffigc%19}4{$iq?tUHx#<D$zcSF9p>Hx}q7zG(4%zz=jwDFx5bNOz9waYdCt_?c%$e)y)K%94On7'
    'C{i(v^_hg|*O9!4i@3%asi@6Bj!(aWM=_-YB}RjVY0_hIb2B{@xB}`kqc@qSvQ<OX36ajn$U!0l?yGbkq7zb)!SyqGNG7?@rkiC3'
    ';C&t61<NE$GpmPEK0>6bNj^aEog~T|2HpXys#K0d$f3ZGFhUP=#s`7n!>n)<yh*h=21zsPqj~A%j1j}aN$TY8#fQpTRcgR-gSf=8'
    'lQe%pq<+>bP7PAAmYIH-IkT1%JZuSO1^2B<^1h}tISx$1uj`XOLm*pt49q0&XiPPkyf*igcRKJrCP&UlpqONgRcloZP<K5~nkA_)'
    'gQWL9(c6jj$Y@ZQBC~EG@t2x3H$;cQ#gB1tBSM-rM>ShaI~!I}I`w0y6T=DC^$9bdN~$TLlrIac*J~Y#{?ln4bQf%*mnL~&Ye^8v'
    '<CC6AC5wj2Ek>mRSLp<KqIX!6iN#bUDFeGxGS1L5UQh89b*Q|j7?>Ll`}J$u2R);OQ%Pn;`X!xzO7}72YH$(gU@Xm=l0i4iK^deq'
    'F=!h%4BCM)!(rKVK^lxK4uy66kdj1(Rh{xmCpfWqt*YTXCEvW`35|ox0_e-e^_}6#bZj|k%JnI<EbnRk8WYor*5q|i*t~|tL6Qb#'
    'X>QmgEvazTTEB|4c?~<19C$ZKR|qN4u$*?6HWZ_(Q$c>vk!e@rCT%NpC_ZG?iaz;s<a&oPUehs&M6C6RAS(G+(kU?!C%r!uj!TrL'
    'p+L~46`l@%r$P`R>F6Pi6Km#xwVLHU$&46JDVi+r$|yy~;zMYDNZ=BjNIvdXyqollN$n(w9(D*e3{(&Mk>_QfGLeUL#L<M|*D!J1'
    '5A9IHgZH|1whY9GnUARP8II9Gq&`mZp-=SB5kTi7?VpJDb#Q-~JMUA{erG4v9qREuOvT&Ye|#?gZS(!tFEhVRJ@XspyME;RLcTws'
    'gJ{VSodNFB?4=PE=(E|>wBxlPwQ5dgxG>ug#+Y^J?co=)$VoeC9HyAYv?i05uaL-1+GU$|!#*bM)d`sCf3`|w&)0IscUraNC%%g#'
    '7&~TxkAS-Ee572<Xl#L&Igpc6agevM4v#Qm{h%CNAL+wJ2UZ2|y%`*Ue5kqM21L|bHblV^a>p-$3{F5IR4R@E@aVJ%T1&5klhUWt'
    'do&1|j%HEmfv&}HOfH>L93Xv9y+}FlLDAlKQl!%#>D(Wl$3M~GUG0w*4Lek3HheT@o9}FUtx{6o8CJ>k(tg?{%YfMcywh0tt|q<*'
    '@LlzK;5$pML6XjB2oVRqN8>b@rqWTBUdj-94ZcenqDa{v{lNEh=rZwL&<(x^-=zxpiSJ>}_da%a=KJ5A%!qXf?maTYZjqTSSKzv_'
    '+t%uDNoJNQOEzDtk%~z<iXoeEeL2^WY*R<B|2z0uMcx%g$Lg<pt<I8&ER}lhAZmR(b@UMFM-R~>?T@rSqRvN|d6b#oyf^nzW*%kc'
    '6MKjr7sDg%zgF7sg7#xV`+Xbjhm7`z6SQlz9}3#<@#`Gz_a6=IKg!JEv>yX8$Ap+;8!?BBm<O3zBj!*LbC2seVt$mFN16GXl$n`_'
    'h^J4c%{)Y3{rvOAO*lP|t8Xsey7w`xzJB)Y>t~z3BJ+U0qM=&Wbmp;g{-u<#DHi3{*KE4p2>4X@eSKZkqc+8>NR=_H3bx#NdG+g}'
    'a*?NezrHhTo3_}|o!qz{3SG!8Tf4r`!~A-%xy$p>%HeNA`LcUvhTM(z9rwBX7_`^*d)Ea{rs5i)-R_{heRSxamAC)4`2O&;XL=uq'
    '_N-GVac#+}o~d-mq+3F&tYGL6>PugsoSvz#gDclc97E3>QQpI+k@rLRzUH+Vcsj*XgCBWH*QG2o-_?xo>!6N0o_=rBuH%%EBdRme'
    'c@Ik8FtughDfb8Yan-e|_NHmTg?9E3v@e(UJRh{NubMJGpWErFvd81Q*-v{#W8$e<m;EtA9S$?zXX$iS;rn<!6fd46EnN>swpucC'
    '1YZ$baG#X{lUyo-ip_`2RN*T<Hk4pq=brm2DC$yiBR(7r;EYY8l|GT4n;EKaEKlj*q;ay;`=PfuB<C}cD%k+92hVx%!$-Ef@u>)M'
    'Pjsq-YjjfJCVej^mE#?XSf>ithIPYd1X7XTUdiz{=$bgxG#yk<CkC5cuSucHGjeXH-7lp*Y|_qm(7rA;P}43e+SviLPumA4V`fSE'
    'aywC$rH{^IYEADACo~nip{W2M2X--(Ct2`p*cv#VafT1HtSKA*G<qOXm+MfKYOfD^TD|^LkJ6^ZN8@|HgYR>h(OG8VPMKjJRc4mc'
    'uEI9$eM{ceeR2QcdPZeE!>7-3m)a?tdM2e@ST+>OBF>1R@XOfPA$o@Visk(w^gFGx5xJV48u%Xln0ZENDoDfx%liF}eBZqes82nt'
    'TeaO_how_iJQeuy>jKPd4blyxE!t`CRkAW-`qF%tN~(onL28!17o!E%mC&2Ct7H1P_Vb<1<ek*CXY)u5pP|frx6{5llXvp5*D9-I'
    'X8ln&UaeJD)+$@C)npT-f9XK`woNdvRc(}E^W$b0U0nU$%kQ6k`+CzqWRLD2x()jnx{W_Ay{&-r-U7;DR{_!c<7GohsPS^9J@-k6'
    'Yds*gjt<|1vcs3#Z7N{YrK0zJD)63u?W_C4XAkV!`sh+Y@8P2!pM>@>($y8(hmV<rigw#q_hU5&$E00l{Gj8eiq?J{TfQ6p8b1sY'
    '=LbwSBozv=#t-W+B@XyueIi_}@q=U`eIGb|S(qqhwens1x~WhBOiPvd?u~tx(7skhX~k#SjgCUn0eR9j?QHl}tj9DVCL-23lIi4f'
    'I^dt7k2nTyTTXl7yYUm>2YjXq?Sm0A(atK`*>P!4*#54x5B{N4j}%+S+BZ>XAMTH|dw+b|A4bpg53FbIso(9V*YCy0vQ%c)o)h7_'
    '^;%8E9)!idJgwDGt<|nttKA?o@>9u-tz^bFWTyYPdsB<=da%$A&@;Z$GviuyY4!TGelM$c=UP3Mf2f6hm`_RWLphaHC@6i!evN(7'
    'S8;eMJTzdRR8n<~ef)%d;x_h4pDK^z%9^l`uCY((RBt6c8rEOe!Wrs#053aE)_6IU;2H3;SmWjN`Q?O{Wp5_D9BUs7Nnh>(US5Cp'
    'Oi%VgQ0YU(!1^A#Dt(HkpWLy>!1{}6?<d;(P1@I3KUEamO?yA1ogD$|k1oNfmJA)Mx8gtA5BIGYe`9pKKjDXUSYyQcT$#c7oQ_J+'
    '1TYg2PnE5W>K!=HrSDp?n98}RV`0waw68&0`ULkxd+n#-!zbR?rxp|T5$mBQ+J|Sj!!4FRz0QtCJ3Ey2itjb%<dI~)^MUqtDVT0I'
    '?c!6?PNz~eqn~2pJ7E*wDY4!C`F_N;8d__WEz&dmPI`vis^8-;R==}{mv^QnnQ?~A*Qycx$TGvS%*0>p-t-aHDw*`m^0hiEN5r^P'
    '^IW38{`>oQx%#8Kym`0!{;&Vx<EEF0k|Vf@QmyvcgpbA6M@TW5u%z#QSy_7fX#aI(82+}8Bxu6*Bi|p3<NO*kY9DF8)p4Ld9qq@^'
    'GcaEIN16GR=$Vgn<g8JcLX60oj9Eh4MTzExeaKWChmMzmjKy)rN(*$XwR@D}IJaRAL0jV*O0=fRy`)v7C70b0Lm)KMPKV(DQqc5y'
    '=1+ShVNc-)zvD=Pp9(+l{vnDIHTcf9+%rQgW-6#;szO$3lka4x>^gX}NnLP*S|dL3k+VGoX8i6WXUhtm{MKb=E<9{g&#W)1A}ym^'
    'ZbQ#ZGBYdEBBpBIV{1blYhpdt>qpwS1U*R4kV@XSiu=e(N2-st>6(%6A{RenOK7KS9Vs{Yp4RH^I`UY0hBCUPX9z2WdPr4JNo@0d'
    'EV|^U%$W6;7N~uoy{YN6&IR*Cwck=QeWqcv=p37NW0|*NQ(iGdQGct<{KECjylS=O+RWTUSMK`a;^OU=bBI3HBYHHze=$Hm65Tz@'
    '%%jZwE$W$HQ%#?q@cy^S_g}6P`qwNoj}@!uej+iqZ0mWnE#N~3pihQe_>B2dqLux4z-Lq1=mr=a4e$&e#0Kyguj>ml9Ar?xpt?A5'
    'ab28`R|R+TI8enwT04iT%G<QSzRfD<Vsy%_QL2&;>rfOKD$}7*`x>;-OrxF24B3=-kv?lh@&VJS>T?3Cx6%GFYn;TzHBKJDIka!3'
    'mJ>DEIaF2Qu7JMU_;eZ-TcCe^Bss0s2Xa!7xnpays{d9UVY5j)oxLxrZU!fX7{1B%5u9>#b1=EOJl%Xb)4uumSQ&qGZLsxPO*&HA'
    'kLH9H8xf0*%J}Q^&34oIUwa=1Cv<Tpxxpp&(9WSM=#o8~WG~;z#uo{O)Wz{lQDnx51$)ykT+hsNh>}j7Ifq`nxwu@tzP!15dwRa*'
    'A!3gnqTdK&enk6^9-=#;eZToVq&4bHXI4Hg^88!!R6MTLM-S1Q_V}CS`=f_w^B+Hc+l*|5^-Zy4TOK01fjcI<*sZ@&{IM+A*0)!D'
    '9p;=Y*>JRUieEGBM?sx6+MjzBv&$u;PPvKjMTM;=nHdg0n1}Ze4X87gbUCv5EjhYI`=<S^q4ZH}Q{n7!9E^OVRFFi4YYecgRkkM;'
    'B)hq4)OnPXD+^^Nm2a!`3>i5tif7J@<51h_L*w@cO(kZ@GiN`ZH}}?Wn)OFdIXjxnnEKmV)mk;vI^3E1RD0dW(_QOtC+d%pK9oB5'
    '8>9>*hz(ElPCYZO)xja0yoz%8ggyN@(F;+pRk7)7rdiLBefuh%)@tUv6%gHD_1=^{M86xHL{HwHp1+AF-A^aM{WSWCo-o4H?}_<6'
    'E2qz1fA`I^*WV2(L{Fty8%xihy?puIYusZ`?Re|OmtUr5p0e@p-@N$Kci-X;c}lWZDz`4?t*fVMyK(+h%erxsJKJh}9MJoV^NU^M'
    'p}EI5?tQ#Ut*Lce*B2j7uHL%Kn1~Q9YT2@P%~Lghm(Si+dj77IPgymPHy3B8Kg4MaQYz@~#(BV(KV7W;-d)8v?nk%f%Ul1gKfS!V'
    'KDml9`SdbPbaXI3i62g{E<(IIxxTn|XK6Mmud7s1MXZ|j`s${;bno5yPj2<?X0Pmyy-Ko?)Fzmi_xk+u;=}3>H&@qNBjx-01owCJ'
    'X*LF`G~@Fwzd8Npbh9(Dw==q{Gb-f<TQ#?K{wcvr@O1V1=8Ze=T>N3PV|iE3stwK>OXeQouifeO#p;hY@7(*X;i|jwR@-BIIB`d>'
    'Y$ubcJZ?4q!xxXee~GulMN1v+-0;2D&|Pv-@7Lj7;~NKyv#vCA@6OJK7n5^fv*+u0eRcCwt)5O`w%MYMhg;_tKPFkp8gEOZ$LBYf'
    'uTH=Fw$X~5w?f;k{L`ts_%WWpbr-N<8ZD`LOT69Ei$1QNLoGdzXQ%J3E`Dk>W@e3@-<+MboBPt8xqorz*QdV4C2~MZuYSVX{pJR1'
    '_`M6OFHg_T-1%v%QF=h5@7y&uwa#7seDOnb9@znny?%S~-d(L;UwKI4yLi@Wj~~$9{~kkV@t=yFjr?x#Z9VyL)196AlMgU8&aXE_'
    '_s6#vsp-$?s$oiexVTzdSoyCfm$4s|_w(0ZefRCF6H1<oS10@*#~0Acd8l6*ZtQ$%bC?q;Y}K$YJ`E{+H8VOs4IyGxnIfNt1i5P4'
    'C!dBIwQ3kGpN15@YMC;hh8DBhZ{JK*sR@EK=rYe$lPt^m9>Uaf%3hs_e?0l)S1(_^KKcIH%WrqkXjgL+DARQ?Rca4S(>rZCC|T_?'
    'i$2ZdQM%eRmOc>~Y}GKKJ_ar0ZdH3FPC7TVvH|6(o;wfBQ#$h<Fk1T#7^MDo#{@MEw}+U-tZv+HdOajt;Ps%5#>rDLZ+#+l-8!Fm'
    'xVLfEbl9+MpNe=YHrcX-@P;$U&YR{>t=!@Y-{-DLlY26FMRquChM8U)U7Its)?b^9UAts9`LTVE5ATlMe{kpV?Bs{&uP-jIrmi8N'
    'UtC_?T*oi6Y>t7zCs7#N1uESHL6r=;W173srTIiyE3`0LO>oWjAt;$Xr!(GQeNa8;VajQJVnd2ya1$r^fwzh4Y^2i@L2ISB7k0X#'
    'Jqw!PfyuOYB6gkOG)}$9F2>#(l3(G$_O$ohhVcfKlm+66o(vn}Vzff4Fx`k$X{LG-rm=LrrzUzdHBp+%dkMhoexieOtEBhbOpR&`'
    '1+=lLQON`EJ0_x<SZIWatP7o<M(ctFS9_DYHQsh6P})r_6kJoTIzNrJ_tJ%q@osto;5+Kzc|Sd&grZ%~3r{=Gr7&Fg(<?@H)N|#d'
    '%Z+wMIU@1O@5T^uB^%S$@*5BhA0nom_C!94#xX=gJvWb{@hBQ?(U=>_zcewSec$;gM4lebY*d8w-84oIlC&qCqr1d}cZ_v9NIP|F'
    'JyBFzpGlWiIo^Yn(<{c=AbRPX$UByxLNPOi+@3J$A`j7-=?QC<<|fs>o}N%5q(Yx|njRVgchNed%QlF?c=SF!!5M|5$SI)uq+^j#'
    'h>e~|*Mb_$sSFd7X(xNubJ<M-?Q~!~ecWc^m}FQ4j&^S9wo{RN))PPNzFGy(ERn+Q6_Zylo`3i4AMPzDAx7uHEIoA}6~vl2!TS7)'
    'A>KwqC%0VWl*d4%@A4eeUPXy1o1W-tq(XQ-z0w8e6PvQ&SQQM#Le}K&azZ(l6Qv?dlP*HUob}P<McPL%h{S51w1*O$Q^=ReYtj&I'
    'AOu<XI90wUhE1enpw>ySa2l=UjERtn>P+2Y&66&DA!wR(D=1@7b0IG^(7^;#I=5k1uZ7doL<!NM7bvAkaF{op6w<IP(U3bRPwMg$'
    'jzRQXAgm=Pe|qudv*+KR9K%k15D}T}IJc`3%&xPNOP56?I+wncMe~jm!BQ=yk$ErZO*Gz#i7*{g>WGGJ-nHXs4mo4Oh_caf0*PU9'
    'dc~;-IZ|3q-G*LKj@gr;u&@^?DPs~5!#mD<7xN7fG4w84Jt-S5dxd?==V>4@=v0>2#;n04R}k+k%$DM5O06#&j7ncYu{LX;u2)<c'
    'NyVm!ymLP~;P*GDtABX;;;6gKOf>GW%gnTgC0NtU@+=x32g0!EI7|<f)yd2laWX^+t;0edi^EO?Ro3qm4JZOnY<a~q0lvGAnO(++'
    '2#!MPacde2RHK%Jl<m)>Py8V!(gX86au$nz0V`4&Yd;az8|fL=0^z$v<Lj@!{qjDt5rZe5YsUQ%Wdk?xGqrjBej?eh*wwMFOxEZ#'
    '*)Z6_J0I}O^n?dPY;Yv24ci;t2^O=hgukFuMO0qlB3R{ZHc2oLNRPyGQ!k?LHMW{eDTIX)PkWOYq`VHCg)AEaw!M&$r~Hb7@}>-Z'
    'Ws$_JrCRB6Q#P)rXw}ix#;@4(AvFuIOZxoE?HDE)tlzE+d0G|MFnKA<#_0^hXwk(~vR=ns7={zAxYNCx#=>-3eNlypg^(;txz+t7'
    '34I@FRK4)i4JllYJxSzOFpYh{z8>u@7^aBEv%gVrJ2N$c?`@B6GrI*h9f#?eRlkz3t0a_Sw@WZ2fff%KKo*^-xulkdNiaMGvW5NH'
    'o4X5!ARgA6=yEzh#4ZJ?ExIe^X1ZYdYytvHG02W)w}IQM>&xige{pmD&Rt%;{fs>tq7P_@f?<#`0AIPw+PK{iO(hsSq`S{!VN}!L'
    '`b@`6I;8AKNXx-zQ<d7JS@Qw|(O5vt0OYo$!*wB^UAmu7-(~Rtt^oqZzLt$Z16bDEa>F?VOlbqpph~&mw5t{ikpN}EW}^qXqYn)F'
    'dTN8hrj8D(HoF=+%)a*!kvwtGH539eiAV3OvYn1`V(GAWs3#&X+F-Q_!bMgl4*CS7WMdx+P7-TbUici~4p@{H6A!y`NZ<O(;$a=t'
    'pd@2Tm~@>GBrg{Y^RMT<vePSyb<9IeWi!#HZzl@wvUW8Le~&_CA(V_M4{)2cnlVr(39V*JNWj<vOS0R93=7N`{VOT;q38JDG*JM;'
    'fH5>9Xv33*QtfWohbZg7YG1_T2S(rAxXbXxEFAb~csx2!+amH9d3ltO{SxvRfO(XV+a%;M4)Yj?*%61?EiI4Xn8$F;EF6=?WsJrg'
    ')0BM#!@s4d%q~eef<^mF5fpG0OU{Mt?UG7j(J`&qE<vFTP}>`bS4N+lE9~gD+ikBn4>{?x*KHP~QP_dI;RB9&_*^S2_uPh*4pP!-'
    'Up%LM2O;P)3g#wgr@hN=ILGi(j~yj5NP!I9MK%dauW7_B7P7!v!d0ZE3)vW>g8RPf@}8}^busj!zg<v{VA%ea1ciXlu}eGHM5zxF'
    'wz19JX6ZZX3>*A37H^akl=JMz>4@Xe#waKCz#Z*HGFGNpm#LzF=R6O;gQ=1}gjsB1k6G@G&QB2GVL=I(4Wb}o=%|yKV+^Ks&{X6N'
    'O)49x2}ES43=AwKyvbgxAcUZxG}tAA@@U^a+PAmax4VSq(ae1`b7y95KOD6B;s+*A&M&TGcX9FVWXM9wB9cPTim2k>Hl~C8VPRzV'
    'K4XSO2z2g9fHI!^2stnzNFcq;BBGS)C^qS=12}g*h2qJlux;R+zznRM)hc2Qvus8R32mh;CB+rZ1#AVA1;DXjQ{_Wt^FBd6bT-Xe'
    'g1R7u>U55u>t1V0sK^cw*9+H4>3Qxp(o{~)@a*sCIuH9d6vcv>F}?3f2*riYV#2fhLjZcliOMVtqU!_nRd&1^?xlm>nYXy)5V24+'
    ')5pA@aGgfm7wyec85}9g!X(%wJ88Pi)804_1r@WU10nKYs>=30v(h_s9V!v=XD-0bX8en_u$=Vx<LsxCv696<kGMdy9`;ZcHVz@_'
    'c(3wC=Vk14bR~deA_RvyLb4(;_*<`SegX{Aj&<0nrvU^=bca1Vv$|JKS}n7C%1A40kL8&8)~Dc>ig`k<RH`>3R9PpOe<Ns|%spsy'
    '2~M$MG7h9eqfLtshAfy3cIM3mszpc1WL7n*4~z(%O~$?hAb~v_GAx1=28_*=fUyZsK01$<!qm06!E6@J0XT^;b?f`!dZ#<jvYLQ4'
    '*P<BNFs1@#v&)uI-}SQ7SUR*MFmMqZfKYy=!!!_?tpMn|;5tZj-j4)@LiboVMM|zOKFBXN4jWIRK_l-JV?J+ZCW(U8MLjTu?b{IS'
    'J5vYP5~0tW%)Egyo^)GwA$H(`1enP2LDNB3Fln+hp-n@iQ`yke5sND7m@7@V6deP4$k{XyV68h^?Xxgddn-d<SP`|1y)9;j0<^^j'
    'nq`FmvcSA?F&mn&Glc0PSJ|u%Kp@QMY-U8Jg~qNkElWzA6pZOS&xuZjb({AG-g)dW+GbTpgBF|xniI{GW)K4!Ga`Xr!y@&XWPfq!'
    'h>yzUT?i@)L+f=x%m(nx36rC;(%>3A&#y!W7Q-4OdCyH*cY*-bZHdOl;qPpIFffxvn%82_0pVd|nJn^v<Y1_E*|N9T1Oj-NJpr&<'
    'fhT-kzQA*^Y`ZS_tZhAI!F!Rl1~G<O;j*$yxmsAzzE`;oOlj0s6cOz${?{{=cR|v5rA%I}p@%Vvo=F8Lu*-Xq(>shXu(n}fPHm91'
    '3t*-*VPGV+778v$<0)1Sw=|16wpt1ePxCeqv<0-0C6o@iP#Sb(5$$3M*m|BV7U3;4p0|1Unlr;Owyc|?RGx}dylQ%aU^L!Uc4FES'
    '8Me5b)P#))BFb}S0SJR^NtziXU=aqOAL6z|qdJT~2?l{wG9E}yZ^AZ3J6Oeela;2o$t%=lgr^d3S&5KiXJ918KD(KWBLcetEsTI2'
    '1LLnNYFvuwFsa#k_g=dIxKaQR@E-OcCUs_22MDM7yl9}asS(QMjW0%veXMs`VtWP%;G^^zc*G872&369?SYat?EUOzQ-l#m49$uN'
    'D-pY(5WUX^6s(^<_E`Z?-}RbcJ7IY{Q8qeQCfWaGuuLO151F@D0<%mgn)e0)-5;T>vzh^9G?0^$!>M7R@xb!_q7@8qAl__JL>+o-'
    '0?VeJ>wE8D{AN8IJis_`_iQ^EiX%)Sf&E8;ktCB3-Nibn_`I`soLj90F)nNT4n}ZS&{<Dm@OfB`+3qsfbQM%*c0NQ8r3rGfoJrX^'
    ';7A$s6Ie_ba28D^I$^us=1mw<+dI?s*<$V#v>K6G<d~TQL}nb_Ok$-Rq%i6n|AP@^jC9(R)M5b{qag?LfS;`HI@@J`Mbs%NxX+0R'
    '9mrHLF$l}L6WSk2KdW!ZzcMzcAdB$Ah=BslS`E7@4_z@TmB(Hbu+gxrk!%myGdV*h!er?HGV&sF8XQ)ZW$2bdp+L07jFUF)DwxZx'
    'fO-a-EoIqmiNtoXik<c+CK58|d}g4If=cRno&@Vihn<Y7?3ln-Z+lCXDquJXgD6Qi)<OOQcBE`8DVP}8e6lY?!bAh!%f3TcQh|3+'
    'd>PsHJ;y&f>sCXF;7}l01}%(s07QV@Y@s>|RF0*Y7iwUzAqwe$fj}vt&x-?FjUob2Et}ttX$=jXEoJO~iWn)g{RtERBOi8qR{GdQ'
    'J=SK<h=-NjCE@}r31`qA4qN^-I4SS~vDsn}&;=YOMOJM#p?s{|JbdAK*HJ0UUIPsR4M7T!<>`~g-eg6tpkjrjuu})=m`<HvxXbY4'
    '#pS#Em)Dz0MOCGNZmv(yriNBe#%{<{7+rcS9r^xZz(eF|f&t^b5AJHLuK;^4-TKSe+WG1A$@R_U`PIpXczH7RmugZ$)2tu)(Ot*O'
    '(&Of1lnMHD>bQ58@A2zYa*#Zw8+{E8ji>O}m9MED3lFUF1*6jyCHWrD_wsYxOr;xFf;?r@CEhmUrF}XUAz5*r?<$fnrFbf*OZ!x?'
    '@imiQ!?V)^XxH%ZS^jh^RI(DPbZqhiLYGTYp0$Nu`IPEe$5Q3ql+HAui#!VXRAwG=UKJJxzki5V*Bh+O%-eIJGFzt$IeUiXXUbKs'
    'nz<_66lF}AVwpz|il?8cs@j<bRJv37p2<^9Gn-jq9nbGjlW#JSdCyqY(s)H>`B|gUiicMhXJLbZVrpK@xTNP?B4c@wG`x``b}Z_V'
    'dR6(yaki~|YNy9crhRP9JmuSs@jNrq<a>I0j<e~Wq+|7smCAilBJ<C3dPV1#mB?556=kRK7&9&J)XdZ($WgTbo?gbQ4erSq)A)>^'
    'V)oNq9ngk4pzK$8Rdk6NN|a2jOW!}bj-e_}f}4N-`xnn%XI_?dTKH12qrMd7Ca*8`-b*_Pz$#CBT0UaB<mE0ccj+X-sVOyGW{Is9'
    '`o?ATtjO)+0abdNE;%Wee3HEtw`I5@(@;GCB{31XE(bF)d-dei>zB{|{C6*2zWly$w{UO&Ri4XL#oDZ7s<mBT7A=&>%0sByDi0jx'
    'QWW0hj!n5FHIaNyugwhA`Ce(MzS?ALF41!!Q}1%c8do}BseEN-ztSR4c_gBFMe~(uTunSGeAD??Q@tx^qO&og4GvBfj7A0)#rH8T'
    'Nkg_D?&<-AV}q5sgw#Jjl(@C7cpfKfT$$NbEpB>`xXCO~vJx#lYo!QxeMM$h^&;lm9IVXs|9<1b$<6uMg@1SQK890wUN)$2|D5dm'
    'k=@_E$hBjkVbd>myBU93l_Ia(SYMYNFBL1BR##Qj3n*i{xuL>gc1@;eHSHM9wAoggDc#k>&A-%y|7*Kl#U~zCv~gxz&9Wv5lx}qP'
    '>d(776P(UF6NI-qQ=-*bxm#62<7ShBVYq)8=H>`R*bl&_0LgP~s@M#hO3N2vQ#n=g-H%NHx~CO5$EHMx{n*qLb9|B}+_Nkrnh8o!'
    'oAF7(r^$X|8GcR;@Cs<Mf<$R<7AP>^Wd(Dxg0Aw;CG$cSxmTdf49E%&69t?BHs=ReP0RFv$kv2lHKb()yvl;Gr@Me?6_4cIv8kS6'
    'f;keM->D7mjOoktWw@*7IFM$*Necjnkvg#kI58vF!UbmQyZKp>=aClN4)cqZeszJovH(?+g-V*Lt$p~k;+>qvXENBZnT!dS<}HI}'
    'bKXwYBDEFbR2g5>?1Qjbl3Bsz8HJkc1L4`VQsj+hZwkxOJYMO7TW$U|TkkUOcfh>kJ)KdD%)KdD@O>tW!n!egA!_CQD6WfbKZwY4'
    'SN%3UZYy+`r?^@Pm5N}$PVjmlP`!@<NVCDCvzcRRj7tlGtl(&dGX=TeGTTI^z)@N7PK7}WRxB%I3(!_r&djkKE4?Kx*Z^f^WNZT?'
    '-XEmenNevfB-e5UR8X+s|KfQ{6lP)z0%Yd4%hDUO_1)H`sgXJ>$kdei(`9<fc#1(RX9h9LlgoC(f^Ced8*UZ-kRav3pvR#t^NNFW'
    'dC7amZ5XvI&xgAz1eW!Ctg8ag>A@^tJT(u9Odsw_9(-kva<zwpcSfeF24IvN3{AJO8f(B)Y3KNj$u@pdE&N8<a%3uX1DVohXRO(m'
    'YG6eocB9qOjpn;xxG;@IwP+Dl!0rZI)=R+Z-M-y*08}N0&Y-H~at2ko5sRQI*NdPkA=#>FKvlCJsqzAvSOGH`?3BB##8qT7W+qC+'
    'uApAdtLR*XDP=1*nsH(QvZ4f9SvI;wL0h7Rv?SlF!n+x#mQD+T6THT;6@63x7|Jv%PHL#G^bvxnX3qSL_~<MYT7|Z>oXuM`*lMn('
    'muW%r6>OvhOI9tF3B;qkL`5sNMFy@VPR$D6iXB~rZ&`5_;P)&zWI0+TyRcTi;KhqlIbmoH0ngF`Y&P?$&ZavfEW==v?L$Ti>NOdN'
    'GAzH0g-t=v8Shdi@&h6V8K}@1dXg;K#+1lwwyI>FcbV~k&duu*KgK27i(AE9;Kc6Os+h@XNiNV?087$C5sJSN%xda*2x~@9=T@nx'
    'z$z~gwS-Z12@tB%yqtr-I$$abgxv_vRnO*jOTdYm8u^lPDaxfPfSJz$7b_7mRsr&Y!zryoUi6-@l{Kyk>?*WY{G<im(aLNuagG{D'
    'nilBf75KT^Wl=>Nmt}ry)|H4l)wNKmS-7xB60PjuPZwPMG*>x?tZV`$3uaY0aY&t0P<d|n%u8?!c9j*vTzXX{F0}kdvQB+qjaAQ@'
    '0^PnW9H}I%a(CpVS;hb4%rR7BtEEWpw}WDfyJH^CFRJw6u6UJ<aMbv!xi^Sy1~=yjE(h*55nKU#HG*TyqpO@Y2w<(iFKxkPN}6P8'
    'zC7YeO)KK6o3Yh4j&I;y$rlA&5BwPPLFjds1T1nSyP#LfhEL8eNCKWd$9@ZXEfB7OUM1ZRU+oMVlv}2Po@54*N_LgV?{d}(b`}>m'
    'R~fbN0(V78Czhnn7FM&kt6){MRpzUyrIdkLLSweXyhzC<u0Sd;slqwYw={+pGKk|PxR^L_1n8>wWc!w&>C|h548-ik68U7s@laYT'
    '9)J|5VV`eB*jb$koRKCkm%4UQ<jay$T|Gc`1%^q+jJCvRt6><v547^eFn3;*5D1m?)L}hs$t)YtCff^)RllmjvLdB9tV**qs@#go'
    'dAw6FHG>jaqTrb=GSi}M0je1o=mJ!8c!d&H;;JRus`Lih+LHym1oc<Rztaqrq<ULBJBkCPfmO-gt51(mvzcZ$6VR7n)%_8xI%ra*'
    '=8DE;$rII;wZdj8j3qmw%FIufyaWk#K}Dj8m1qNwv2sc4d|%!OrB)H-VuM4A(s``4%37w4?6#w10n=GHyFgMZis7%DNV;NOF-G~u'
    'VDxP{z7^|qVV#*@GFwM;tKfBo{CNYui29OdNf8aC@o|u93zN*_N3?;Icy(0}m6>@UXyw;vMFZ(a%3a+~17>xu`SQ!A|El&iZAj<g'
    'P<VdeKr~s&J}%(<WH6OCuCfj;I-y!ZMN~yYENvruhBh1mqTvuwjo$cPhX8vRm`X_vgebc&YUQ?t8XJK}R^pU3kSi&@HISonF>IA3'
    'CAY%Of;WIOZ-!oJ6Soq*B=)Kb=-uXvY(`XBd$_Hn;CY}|?dpsX+HSTvUbXIQo^!0ZwKE93eW-c^4a<Yku#j^!Y}ourtX_5`R%x>Y'
    '4O^QRasv$C7R#-2T4|NAsb`jK$@Hb9el+97lK)#Bs?4SeufS6=uDPz!RR*sWq-`E~<s}*`D@dD-7G4?<1x9jHpQP0#oLrs7m9t!E'
    'q03tpLbUhEI-bK5HqQwy9)?28Jhiw^K+bfQBgF-WlEShwlcsiU<VR%*;FH>;QROJ>5~-E5NG~g=qBkSGjaV^HP<>G(H{*qDEzaEn'
    'CI6CV^DA$W`D7`}MyAMZflyHrthb#w#lbF%kd?klB67|O)p-|Iv_j0PoVcF-TKcH33U;RX4O2qLVlN=BGuF-a6>l7sEiy7mgK8X0'
    'D88dA{kSLyTlsLRL<3cnN_NR)@u|UerGHr60593im1|0u2debv{Om?&`2kwD%Q8YfG?*(ZSj=WAv8Fn%#~Np<X!hXGO)}AlOVI+w'
    'DnwnM31wAWQ_h0JRhYO$u&60_H{hFXB5GOia3-~oB?_n)#rUs|iQXL=vpxCUHS=Y`A!eS1Tt%#_W2(GLZNBxA7pFn-aBN=Ermuk%'
    '-iiW^dC8BK%}}G6othSvX)b@EF<ia(>eIyK)ZVLGknw(B*x^@o%EiVKuMP$5KkL1jp27BCmIYKA5RK!>v|6h6J~Q{Lj^OS;{?Iz*'
    'dhDzFLt}lc6SCacT|iJZqLPd?qnf07l$F@UU|2NMkaYtKTh>I3&4aA_u<$GsTeM=hriI3vxSO>pu*(vWjU{4+V83>!*B7fl4)tj_'
    ';j20rzN#t4T*KE9f^M9erHjz36^qcTWV`D*5uz5NS1}KU(YjjB{2s00YKA@~m6nwlA}{u4iTkpGL3x2byx6{CBQTqTt+YBtn}Mg='
    '=)h#`n-g}+16<ZeZu8xOsb$G|E`h-+CE6S(m^%+T%0~EdmRwvFt7@EU%xp4s-gI^JwW{i*<t#&(Rq4tV$4cUJ2^6sk5veK~T!p`j'
    'q%b*4R_2Q{koUxJYwyau3{^gFTGb#c9+DEbEs|3L%_W{+aO>1uw$W8K+*QW1A_v%1$q_Dx1$4GrbWQ^`B{x0Kq|WJ}Hs^9uo=p#y'
    '*tZP1@&y-ac2Q1^m%RVtwV<@%Lt24VEw=$|RY!?dHN|M{A*=9Zm5NY3TitC@K<WqT9Q$%Q+_E{arB#Ke4HwE`z|}P1Ve3j&(U?Yh'
    'q^>fQ<(?chTOrgckW}R)tNn?{rnaDM^PDMdWa$?AcnJ%ODga#Fm36rJc<IM&<l16_DNL|+Eu{*F=Rj-;lON%-hy^bW2+r$RZ{-%K'
    'N@!J(gU{2;O%;*Sw}ORF3tj6{H}k8y-qS}-SZ;@1>C*J$W24voCzxA7@MB*+z)buGAuIV5@$g^F(OK0fbHr6E?YMbvbU8Lvyai6n'
    '%?%W&mPB90Zp=*^nZUN0Gc47j{9sF^o<qxL{`&NX_|47LPZ#fQHnF8X7+Xq9=h)KH2DUVd5{1c_r+o{!RAL{v6b}e4$vjk6r-$a0'
    'VOAeY&ETbAJYIrvRm!fQbqKX&B9k1*%y_aY%al_vcnvA4vQZhW=^Dk7oX44=o7gya`!FHVy|{9A5;0qyqU1Z~fKt9Hna(K-$>dqh'
    '_H|WqiPd$M<Tg~~tS-1z)g8{R1XTw~Nr{qIhhUYS<I02_j)yBt%+t)CQq}p_Qm=QGb1ic8hUQEwo{!DRY$2;0mQcApoil-Cj<2eG'
    'kCF^KwXD*V%hhz=w$w4sFxFP3rgChQr6OVviz~I<4#Dd>te8PtL2BjLavj4YH5Mdhe%TIOvijNTZi|GCfM^va&6lDMsa80*9MjeE'
    '9uZM9J5SfTQjNS;+kg%w^H*1qQ?n=PS_esGGx4-aT-J58rK(@V8U>0sPJfbuAWgxQEwriX*Y1le%Mn@DxKgc{a9y3s)<<xwBEH#h'
    'FG0#9T&g;yx`LQyUZA+nAr|%Y=y{HKl{mh@qW`qG^0wfkdBl|qa3z}^bv*XfMjHPku6)Fm4P4ng&Z?WhvYEWPRVa5qvTR{ku_L~?'
    '2w939$Wjp2LYB=DsAZ*oIZ=H68Je$t{`ul2oSw(kHy3Xmrf>E2vu|HN+r*gW@WZH6RjjI%(qt@E5Ywn-*|&BX#N;_IrvWj!z57vA'
    '+Jc>Y{#;dUhx0m;DQ6K!R)5^Zl%uG$1Sd0CELJP$HSo)K^ENCB{*k2qUW&}Ys;VAS_34}nK$-H{nvKlR8A_(~IAxUdf_lGleoVFX'
    'ah6uvZ8p43oy%CIziuB%r5hkp=2@zea`W7Yx(<@zjjzsBXj0BUYD1QuLlp}Sq_#emq^ePo8HO%L&dS-&a_BV4@ci36IoM$H{>*H)'
    'Qn<)rBVG=_(UKT1Sb2ct5*nf$iRI->72M|JTxLskC#vQMl}d9<@g%vMgL1dWV_rn5`YsLIdymY2HS@>p(GQs}yQ-_09rY}#zQgAs'
    '`0R9<ZGKXP)Uib}uVGX}M_t!Zs&I@hM_FmPD+;z`rO1$+AC_diKD((4RLTgef<o*;K1b8~=#OlKb*V1F%jP9l^`$KXPzPL!#$^@a'
    '-RQ02T&vE~Mr_$OE~{MWI(qpxRx*h+(-n2&ip>g4Es6Rb=^*OHC2z#mo0s>iA}fC>0O=88{z4!oz2`yHg4U#=t@^)eXI<Q8D3dM^'
    'WmYFKt3$7}6?EK(H@8|fvXMJWg}VK0C>^J!QP#*P!{!;W7hPQa-OKNRC^rG6JseP~MR-!$qvA=m=QQWX#*+;z|HyE%%5bfYVcv!('
    'tJK|$zINeBEw=|#(M7k?IDb`elJi6Hq^d&Di{WIcwZwTHxX#gPddm^ckBKKq8B`IsA}j?@nmL}#g$}qVao*~aHkQ<QQWQKn3ArgD'
    ')$)B1Zp+fD@nlZTHJMhbZcB@O#FM{#JXs&vBe&tn*7ryj;K^2%Bw1I9tv;J-_IF%jt*nA$RY{)RsOKZ$N!`5U1>sefx&T9dz$I&5'
    '(#EB(%OO>PQ!!`aW=-VAk<LdvxeHHL^{1)>(_(f-mIf*x@#G_(e8iKGt@8cSd*I2f9M=7KvVr_q6HPXeD?0#VHo~%$x6hr*dmvBE'
    'xK#77=3oCEXl?aJcX{(}_5EM}!^chhIekO)-X}77BWrfykxaP=g325$X=TmI2h5tykfp$&>JuZ?=VEGTNvmo@RWfViM5Um0rQ52l'
    'c_g#`o(yS~BdQxH#|}loYSnA9#7Ya|6;&#z9lyErQF3QFpXJVGURFtq`2c2h&P>aB_H6YTQ{6gUS$*S2)e&7bKa;ru?5i)AR(Y~j'
    '5VJa|TX`H7Ruj7WsZ2dTm03QUYfGu$EON9|t;uhwT)oQX>{*hp%2!&7OGM>UnYMfZX8KBLZpP%~T2sDOlZ~lTyw_&9LPg0-Pcr?m'
    '*|Wu^G5;vcR()NweJYcZIyttgK-A8jtukWk3eo14W0``rj%8N<qI_9>xv1od)A|haMyA4{*|Tz1(&qnf@7s1HNsjE^`4x?R772Ir'
    'yWS-23R;P~0+tI1kg#afC3B|1o^GPMXGu!nzsn=5D)XEObMwrcsvZuvW*5zh%*Y78nA_cs;a_1>jCnGipe(ZjoNC%6&7RC9?Ij2-'
    'l&}^POwz2DWoD%;6S7pHzLL^s(<yznoIVYwvdp$c0e;T1Oo4@|N)9ol&x+FR=2S}?(sTZKiXVr7e}eg$6tt#*Fu--2{)}ar;jcV>'
    '*6ywOb72ep($Z&7f5jL2%VF}tt1bGPKC9%JCeg|=H6))XKeaGZs+K;h7iOlj(q~H@Rc0zPa8)%w^I45sif^IRjh*@B=If_VpT1vN'
    'm;Q>HOi^kwe?m#-S$ID=8m(LYN=h=1k;vDQ%-534*OJWFlFZkVOg1Wmg8C!p)?_BNmm#zw^=i?dY|%31gqA4@O&~d$kL?6ltC^Y^'
    'o5;wEV*QX&8BXS-S1d^YCZd{5_k4ez7A!>k6I$XxjM$xG&!PsWWkV9LHJSe&jLMVKB&bbrp5w3An#@<Da$1www3^JMfwNZCs4N#4'
    'l}d{20P^)bn=*}RGNA<x8kK4{(z8rTi7suie*XTuPoLlX%jX}zeE<IA%C3|vqLx94S|-J?JhKq<u_5X#YH20T{=8AkWB#OIy6S7x'
    '@-=Gt8nt|lTK)}1El;LdGylp;$|o6^q8OM?F)+*KFYKT|V6uO!QA;#1+i4N98nuMlQc=NV<MaJ_YIPG%9ZN#c>M<EiHYrUb5lq&-'
    'MlD~XmakFER|E6gMlH2ooVlHiCVL6yPt<~z@)IzBO1mg%S+59M{_60}+wbN3M>>BnF?a9p7YnnM<ZB7#(Yn0vCfM?^ILW_u_16*}'
    'zxcAd`RbN${`t?J-u$<lFT3w<{&)l5`Q^Lc{doKN=7*b)f4+J1PmkZ-c5~GoHoCg@Bv=lg`opKLPwMH@KfeF?@nA^uOP<W+)wpYE'
    'QPN9~J4-%VoX273A}MZ1O^+Fj`moyhSw{U|`bl~7cRzmldb3{ZATewP?WLsbu3PISMVdc*)XI7uN3G20Y1}O|7dON9{WWskuv2dR'
    'Af7$!&4QjYXdj$ADnzGIhmzcNi(Q?Iow#3^M0`xjsJ%$b*R6H-O=5d_Hsaecj(!|>OEFzZA|)2@+e=e+$-w5GMqPZ!`8qC=OHEN;'
    'da+9j$G%FZQFp$3<yyB~rOC@4$JCl^RyuWlsEiq2Fp@F8)Er)VovW`cY}UC*z49o=T(b`^yUsPov^|H;wJRmefuhql&_Z(DvOSS<'
    'EMC6wBrcM%wr5ytW7N&puvzPVI9<AerXR#hein{56fd24b6bzNCiw7@Q+VLf@mWT!ca}erM?Z3@ZOJ1QFV~UB!a!0zd+7i8{vY38'
    'LeAn{*(%lIx|rOK_waB_nU)tDXP16kZsA=hv0XOKg9!02OT2xoiuUYc3;r7FZJl<#JA24moSZYXIgxY{a3?zORTR3#H;l%dB&7J0'
    '$YD6x7K3+N$sw99WRh$MHPjcEa&D`)r4r&*+C-`?mS-68gp0Y*Is9gYV=Uz=`YlOZei>Tuiyh*&W=OY^^L4VVk1M|X3j18^hVQmT'
    '6S#^lx|B%y8AfdbIG;uzfE0im2Ps!FxZuA9S-b2uLZmjA>Q#&0^@<DJN8?cg!JpVhs~bl~4Jln`gt*x0<E0K@-}SBJh@mgfb<Co~'
    '3)Eq4tV-+T(`Zx73cD!DD`p2hXsGwZCNCxEe9)Lgsn^k~NVvdw*3Xhfv_8k!wt7$ODwo35*3TcCM?o%7eztpW4Y@zNY#kKA=PRk9'
    'xz5YdOO4idGruVQ%@9(#YP<(=m;B4{uo7e5Iwg{e<wA|U*6RFosK44EYm6IBr^c!=+KE{aVt#oM7Gm=o3h1)pI(@P&QtW&UnCsKd'
    '9CFEiYhhMjHT~>do=|;j?YTIa)(-JFcvsw(hP`*na`SUWo`~dg_Rlr+vHQd|m$oKStyj8FoNxKX2VJ{_YFn!#*K`$acS#@Xa}C<i'
    'DVn&pb@{jyj+tzi3K5^$1>V=Im)ln-TUHXhzfK!YF`lmn*@nhhs+_B3OD^8G5aX5WE(^^(i|{_rj_RCI+&0vZwD8Dz(p*w`9$m?b'
    'S2{0>agu7gT7@ppr8J$n?o#50tLIQf5lN#b4i&&${j(@52I+UYiC&RPxn8*eE%YsYmJMJP0W5E)1m@|}<B&i8_~C=$WOng|SGROK'
    'dn@yEkam?Pv{s)>c$UT8&gVGh&PldOCf)46k|K)K5}qR{WhqxRmLyx<Tdwllbspm41(8;5U}tzc`slXyf)6c+bfrdEm(XQ?>7`DP'
    'DR8oLW4z9v)J^&eJP8&_TZ8WWK?zE9`F<^*E3xbI^@W$Zo8!ePE~c2SHX3qQz%Nl{Ez&+yLI!bVD`BeUdAd+S9wyVCXEJ8sC8f;_'
    's>CYST5e5}t1nOVq07WA`Gn-O;LCX&#;1INqxwwM+z8Lbwhh%vXF%5(7CGe>zoB-xBtN#QBtO<G_3~u{Qt{8d0hWsH3nUzzcu>uu'
    'U7O_=yI%C|B241jHlwM9>dLhaj9R|g=ofWbOSh4HowO|}mT$Q9U13#HSR_?<l^-Vfc0u;SPaS^g8rs&jbN;&Yy>8FN6rRK2u(Fnm'
    '-#U<5NcF1Ji|SnN13!DrN`?3t2FH@(qGWc~r0^GdgOvs6e_GgYY#m8%+rjo#^4D2(DN4>SY=t)Gz2bQeK3tiP<NUJ(t1TPUZT*Q^'
    'TnN{hb44x)O<a@oRF*YS(zNPzX<D66N9SJH&|fkowzTYBPMX{HJf~qZGG5|(*dr|b<Jc8`0tQ{oO5TWz+DSZ%Z7f+_=PQTP!Rzj;'
    'xa6^~hfN=z;k;U6t^R_s4uWl?DV)~0xuPT=Ht!VeWBat>LWdBZ-G-P=CcEOcj!suJPxJXx>2_Rrw(!cx;VHQ)$F!)W4^Ph+YEU(~'
    '7bkM>V<<{I1wTEP%rD5bw$u+hu$)`kdhxxulFNCK<zF4Dc;Eie$&?BkKiu5z7W|vHKm7U4hi+cK`SRoKn<v^OxEwjY{Qlh^-+%2>'
    'cz5&N=iTn1$H)n1;rQueIqJQ87vP@$L44;Uf8x_SX{Tl-e=(tX(y`GCK=XvOh2{x$+h~&Eb~-ygIe8A>Z$Wn+VN)J3B))9nBmB{?'
    'xGGCM!PFhAQkVXeFr+WL4<D2##v>8-U;e{y|HtyI6KK!d|N8g;{4f9T+kg1qfB(<R7tRgd4qyDQ|M@?EyS)8ah6y8D?6lR8`u2Xj'
    '|MbT%xQFi7?yy18!LGSq`{l!!Pb+XQ?$-}ndGO)9K;84hZ{OWMAUoC0tI-?%?(@SbTxx;~pIVjF|Fc5skBBxZsk`6QM_?$6*xheh'
    'Yb$c^zl>>3@C(pMo0EJu>C2{zt1o%m#?|Es$v6K5xiqBsI3ajBV&XE%#Us`tkk=8;>R5ywe<R~FK*TN89q}EHuW$7Ta>B2da%`ji'
    'bZq2=7<)Vf?Fe0Q9A!CTj+{nWe^W0w7Ve1Gayk}=FjZTh3t0queesT3t5ecdBK?%4lvm>6-IuSQ-~Zuo63!G89|2D7a40_aReJaR'
    '?oUUkh_~(+_}|<A@H+O_vA>S}b?mQWe;xbl*k8xq#}1%^Kiqu&{qE~uo3ay6fBLH55`KZ3LUYNlhv8@WFZ0U3uKT~^u^W8m={mfw'
    '`?uqXf5rSg{EhLM!MevlCnNsy<f^LdT;N1~c1O_u?(pw!@ArGRzpeZJU-8So`}=S8Z`r@{tk<!>j{Um-?%eJEImfoI&cCkv>)4O<'
    'uv_S%{0w9NCCjE?x?HWU?7uOc6;@-P!x3~)a^r)ZD9b-d9{%1h+N0mOa_6$d+aP)8_xCM?{oP%^Gu+?Z$*!-VD=F^pYgyK_hTUyn'
    '*s!eb?(lDY{P*^-yZ!$j|9jYhyN8Rk{Nu`DDB}BTpY0%L_0z))MRVrVDu*SO#~bVMZ;^VpliPlacYSG!^kKGAcV+$Dmt;cK{#u5g'
    'SM|=#zdz&HhjXeG{*Ex-n`a%nob$cZ!OQ{<82`T8x!c1Xx3UO`=xTAh{4E97xik~`UJvX3@VOlR_qo^ooUzMrK63iD0xefKxA^(b'
    'F!rDR!-vx=KO3JBn`S!md~(BiS9k8D8mIab`OGg_HeEROyN9vo!`SoRid?Pv@zYwv6V>!3kzG9!kl#J>$Q$o=O-gmCOV^t&S8qm+'
    'pvOF+4>$Ms$0mkv?{5C^^~cY<drW?P%!+;c@!gjnZ<k!6ev}TmP;Yl1-hcQ0_QURwqxg`uxjf;Jrq=IWP(dE=yZ!XXV~<BUB}MK2'
    '^oI{O?>`>i=YHdJdrJDc`|<0ScVF&4ecqjV)U@PRU2MMVzdimEGN!`t4b59`i0RbZ$9P-UV&G+Q^s>HF`I46%+a4u1e6wr#>NI|J'
    'DQCXA!mH08M)BOpbID9Qcnja&e){p_{Zq!-v476#$;(+jJooU_w|}^K|M__LV|Tn(p0Wa$wJy+0@Bciu@jLdYUdH0v`Ua_TY%usZ'
    '3H;i(Qce#D@{nyuccf#oqV{`#YEiZf0Q=KD+_BUg#-|%nKg{bJN@!2nj7v&r6MKx&yX_=#nZ(!4AbfxBQx<2xqcp#HM5^gD&dof#'
    '2sjN=a@u_FV>=DO7q^*(6jx8PNbTX2@-uvd-QLVW>anT!(())*`xV*8%^+etHeJ`=;5um@*C6IpY-$S8r_0_zd+l2a_6x+P&0d!*'
    'K=IpcJhl2$$-P$iI?9#~@~Pk5(wixy3B7LTuz<zDnex?7hOv1=|NU_YA&0s>bsomhNmuMU`WcqX){%doVi5aW$EJ{LJKfNaj7$#Y'
    'mY#|AgxEIk2u+MLn*?Sk%8{fc2pTowsdx4aQ`b$lzt82g&kLx+mfrg-<ir(XnQ>TG?PtW0#iq!lP-MiZbUrX4xfoMan6QJFWGS;d'
    '6v7U0E}}2h-Vu>}ArqzFdr_9E>$Ru0z01?=#f)96R-TbiDwjFwYX{h$?&v!f%(ZfpEl(0J{5`Eh_7W!KFD`GNQ9+(0g$eoW;z?Y1'
    '@e`_wdCRbuwogZ~80wbnco<nZK?{^SOg80UpX6?z7JI>BtjQMON#U8Rx5!qT;yY4bzO4Xr0utCM!$<}9&6nA7Y-M0YX5iA6Gq1EA'
    'zddNu_Yx#bE}NOu4CC~hjqhv><|#>$KslmL7BxAXfLXM<+4pp6b$u{7HY>4Mp`d%ZI(dl?MIo*NN>jJtt2qqsigH6fk(MZ$TZ#F!'
    'm_bn<`4u@T>kUVBaL!OURJ4-SM18RdYe9Oq`C{CXHwpDlhG{#|09)!sCMPIv2O<5?z#y`>SJNp=L0V)eTlP#VA)0a#(Dn-{+C-7d'
    'W=9uGG#Kg)@re+&5~O6(0ZZE|i2)3XlCym{WXs-3N~N%Ug=c-dHRX6o1x6CLY6r0rsWF<TCrR)&MJ(B26W*S;rpH=s2+cM<q~sZ|'
    '*&3=#>$7y)5#@NWUax3aRV)jS`AjrvuJ7GsC4C56>!^Vgt=k#M0v~jmqoz9XO2@GETDSy9qaOvE?|0H~6UWC^rKYXu#>&>Y)7SE3'
    '|CH@K)@!w80c_&L?cwOU4oG3y3OHi>ie|(l7Zo{9(}-QSFu6ouwmR7_MIo_?l6Uh$E0PvSQ)HwhWaV3*$npYk+?0u?B5rFZE>KM;'
    'X`rYw{YTYe=BBbQOIMoH9@g!#B|7qPy9(jhDB{4oL~J_g)^fXSm-tjqq*YK{bhL!7`H56_$|468B+eAK&K9<AD+*T}C2viP;9-k>'
    'R(!QAkQD(jBNMX6y7<^0v=eg6K?Z5=FR~tra-4lc%_0|FQ9SKt+q!)H(m<|)AW{5u9$3Pbq*tRT+qt&BAty=GLbhMAokT>xwIXFg'
    'w<v(Qlr2pblo2_^G}*DZRYkj=2>apvR;}nq6UiniF8G);Dp^}uwesz_t=z65qH4bt1EKT1)A{R4^>(0(4&@DDM9jKuot6;;1)2+;'
    'T(7Yx(F)v<qPazw{1tJ>9zAK>rIO;oi@o%V*}6uLSWpL<xz!C;tC_YYVK@EZjD;;-w3trs2;!9JlP42=L%x+PDMd*-wEjC0xTez5'
    'OtZppr1J+*aukM>x_Awirp5laZkTTGsGfxQ)+lTZbQB+?nTo46k>nG|A4N}Kw@ci{cSxlSil%i!?^zz893Y9X9g2rGdJxi!F|JT|'
    'L@$7NlWM$XBM{%MNpY|S&;^p>j9b9mPiyT%v;%fg)r^s7-1ZFeVk@?7wmi`bjxR|2s2Gf{0pAW=y;3p;%d%{_)rx8r^O;q@tOasf'
    'R~afe6tjH*V^Exu><(1C(d^AgiacixFDssTrW?N%V=2OlIz^y&1L(A+qIhLW$X3*h40Pv}Bi=OzGrXA+=+QALHXp0vvQ>?U>GoFy'
    '+uZ2ZiDGa?RJPsLN4#QYN<@6M<yDE9SM&xdl5!Q$R(#n+-`&W`Hmgw28M*uV9nFrVI8CIdTrp}?x9+?O8y~CUi)P1W(&9CsKxHNN'
    '#bM=ctCq=<2d509HdHK{7R5u=qbS=(if=dQ{Umneovml(qPRa>Mi#G})m2=yZN1GaSJIX=yfi$Gil#=RNQzgFW%icB3k72o2Po;h'
    'v880^O!!i4j*wNax}ZB+38t(jTH_?z*Oiktk;;nV%Sj1!t6dO-?Gzp-mZM^Ht;iy^N!UIsQgdmNdJ;uZQ5VT96Gi`E@(s#3$vEsc'
    'C^}5d6l7D92l^c+WlT%1k`mz=ahp4p$>49wo{%VT8V|<MsMCz5h#RkZ*@!e^ZHfm9-FR9E7xjmw&#kg29`ney=P1KGikd7}DjsJg'
    '1V(!ns}}hu4y^e;yaV&FThd#m(WNO!y;#(&yVD^kNfV3c6bRc*tI1&iH!ExhPKh+dTtOW;DRGyj{Vcf1!}bB0obX%0+&nndG({$R'
    'AaBJ8?wSk46BR8yILy&h+(;4icrBumqK8=)CHW>N!_U+__#K02*^e1*4Mq9r+5||Dwq1q3yWnMNS&0RDaB6hZQ!({1HBVCrlS5Ta'
    'Gc-DPL1)+Y@Ptm20wlLJ+D_P=2e8qt6BqmuNy%D^Xk>WBLz*2%GgKP_BMMqhfr#Phj?MlS&b4BooM3$qDv@$#ftpj;5>wY$1m4iL'
    'p|R{iVR4GTaXGckvS4x~i&Jwl1lR=^CX9ILkiFT3<ZV;0b6JoVYDmL%ecM><>La@Rm56UTc7h&oCokgA5L2A#UB!XWjuPgV1tql_'
    'Ik^daDT<0vy5Kyik4ie5WQ@(InN6)=o@3c&Kl?@=&7#G}8?M%ta>1>nTFwpweOb01(Z%7J!8+PbqpOB!Qf#fGg$;rmL(B0h7=ckz'
    '_6r3C>h^&7P!jrE6gF7EUGEjeusGb(x~1)kp)T!)PMI0=Qk6SO^w#mn8Ck97HS#W@r%*|=ad^s|;!Z(-ev&Qeb|d8UiV~G18i}at'
    '&#Z;5pHG}Yw0>y?l0m)LI$RU@9<sv7NdNGfXwI%7#VPv5id$~8kaGe~mo*;=)edwinoQSnS0Tg{T}jE4>jEFnmZIp0M*~wEgzs7?'
    'q%$NX+`w^Kt)iv{jFBpVWZ(ISky^WaErv?~onFN$d9_Pt$I}=U>#`dN*3qlT#ZvQ%0FIb3rT7OkY^KxVlC|5FV##n>Ts$D<wUpWv'
    't(u(NaGBkf8F#vdY$WG3^B0x#tu{quufzaS1W#)8ibvUjGNjfxpr<t`uaN4kkiDdgc@0{qquWKW6}~C1by_Da*|0_-m29gxXH*Mg'
    'R-_j4dqrD9$BlDQ@fW*jxzZ@jZ|O*+L=b2aPVqx{)cG{OjYEHlbF<K_CX{4}yoyo&BgVI6@+!)lbz=OILz6+rQk-KA-9buDga;Q%'
    'u3LX)u7x}~%KC6jN=w`pG-8w>V{8E(AWrctfHV?ChZ5gF1M-SnHDz*ZZ4HFJelQOu6}i6`=iwA(u!L&GlU9sg@u*@<K(&+>ZL*nn'
    ')Idy9q3ER<NwLk8NDM@iS!~F7MR?~-5+f?)o5`RO#ncJ2k+RyV+_5s-lv2?Io-t9XA3BL+m{5^Svh>%1EOf<bLxMr`o~_cm#SCCa'
    'EkGS=#%d}p!`oxzKyh?04uzA(RkD%>3r{GDkmt49jxiS7fwyQ=(aLDc81dRF*rlS*s05xDJ7p|?yE1I%$1btMXvLU{zyL#0tZTtn'
    '^aHvbAtsoHrsZUyZCti)v87A<Db}zZW#(;G5^y^WqZ*<_W~$ImDh9qF#rBCR8eu8OMdC~i(W<a;EtL8w@t7CY$C>QtrE2<0FstUp'
    'i)9q9xcXKVVsmU-ee0A;n=bM29g2$}KuBB5hLz$$6$w!(NN*nF_i^j>A@90ZERn9fX56l(WN8B7X_a}BOEorQ$)?8WRF;X$M)7Da'
    'Nqh*@u%+B4uvQ|<mQpN4@l;62rWX&MpOoCOT)?Z8HB+cmAx^85W)v*hQwoh~mPtuHSz0QBJgG|gmO~d@)7&YLS`f0W<91snPLzDj'
    'ybTS!l};(h;{coHU-l7MrbbpiHS_}nr&wK02>;{q)8T8R$tu>!QfCR;wie9J2`!qcR3BjU$0@bI9Pd^~8YR=BZwH!Cxl@XA4kx{s'
    '`?g*VC2!WzzG*4frJ4MMk{F!grfL`faa!EIu??x^qq4c|wLncn;!(6a?=4&M;F|<hSvhMiO$>w1k0Fgm^9ne@dS(R`rBqC#R1~;='
    'o>5#XvMzYcCURN{Zp3)F3kugr71b9dJG~1MqR*(X@W_5vg~p>J_d>BVhP30lI*eZ9fI`YzP@LKYEl))S@!pYfD|O=FldVi5Yb{45'
    '=d&ba#9ql%3;`8BB?q?aT7c-{y^@k4prUs&Z;DA6kj-unY(-oNEpK||gj4-S6<*TKhC0c_6}=P<R2jv=RjW`LQc;C`gF+5PvQ;Y%'
    '*XbfyAVU=K*nZ8vG3E6V1rvQ#wiL`#v3??mYeiLk2cp{2OwAD0$w5(lD^_!<YANMWItA>+C*gGBHjy==9Q7qM3(sgX_NfR>>0%OB'
    'T+vO*h;>TwgA|90uBbyRCapxeyE%c(V9N@`&741^E@>4;k}|o770xKcp%vpVVUmTG?B1#vsytb4O-XcHlC#AW>`Q3^`VA-La~cqq'
    '7k);aNoEyRg=kM<HdLFY38Ix&s7QcAdP6n^(JJI#CWt4By-vEk?p9=_Z<4g9avdMpHK};x@Bm1YS*E2@>*pG0_A3z%hhA1imk*1t'
    '2lm7%Q>hq5)$+{QJknHkUUWs5BJHBKnVPK`N9_96bQn^RHISo#+C$WWN^Iw847NCL$;6hCB`66~;&Df^*SxG)pRH`j+CbA36sfcI'
    '%z-iulm&NKF{otFE<QkSbA+7H^cJO%G`fkWF;XRvXhvSEmKM`xB5H)OsKYcvBK`b&WRD7m?E}Nb@EST?GAO6TjNTMwl&cNV?4C?1'
    '<jONvz7Qp0d1ZAMrCJEHL$pYJYt7CfXK*1^wJiiFs3m7D%5Sn60@e+x&Lg5N(F#^+99;{U8k>p_x;B!WT7`V2uz_Oag@oj#z}j%7'
    'n3{gbDHcka_#s=(baQo+fIW|jk1C-AmkE%ZvlA3m4VJSklr)N!#L_%i36Gl=w`O!vm5Nsyy@qg@t0gQJ@(WfVCMQ~LB^_*W4-|_o'
    'xHeUFhOk6ZvitlJIdi6M&x*7Xs##)(&T<(hR?8H9h;rlAbJQg~P<Tm-TPJv8(|$r-8c$fI@hG?&DWG1a!OC{Rret9)bF7kk$zPZd'
    '<y~>Mebm(gVmr!2sN_hWDwEfo4JXZTAYX{sS+uHfT{3y{L?xoEhLR?(HtifNQ!%Y;Pc=hMAuiIo6maV<g-E(8!=!>=#kG`buqES)'
    'YpA|DGCH*w6g%2PaiK1rHt>uqfK;}FX_IE6M9VXQ%qp}cY<omCz-v1RDrc%F5^2dqH7TcSJa~s9k-EKthJ^;G%ch5d+p-FuDiWS6'
    'DmAy`%7dgi@mIMh+M)|9ky_m`IpE6#Dp@_R(!|a&^0ARlq-3~txkOTag1Dofc~hZTTNlMH-*ajSHWk?@*2l`xnlAO4@Iop6{}p4?'
    'ay~htr<S-Dvhug}FF6ZA_ihy;OyKug{lB-+<$Q2qBJn5*NtK$m9p_s#b7w<N2o10uLFGk~Ng=zIkk%O|QnjX;uFju=43G*1^YWxk'
    'LMJd~sVYf;;Aj4+rbUfR%B8YtO>LAwij;<Ao3Ywa!!yZ+@{H0f4IyZV>Sk$I-)AbtQ_LnlfSP?5sU9Ls0GgJV#RNY?!M^JzhPURy'
    'UJ7lP)suI%svA~JIY)KuN}fGsji}0CCgoZ&+LzKu7(~<pDaA(n@9f2FR8q?%eztPsInC}umyeIhPqaa`RM&=U449zp#A#*K7})iS'
    '5gMXZ3A?h!Cs;iS*81vzdM!VP7F!9>tq-|IxoJ`cBPGbhH8F8kX7a!&2ExHbZF^wY;L<cFDy?>tyqZa1+J+ACN++cL8M(|9!e3Ga'
    'ymk8KNj0k^xvina`B++{3D1@b8sHrl<0wi|b>#a~N`7<9c9qI1wM=7YUG`eXD|&F1dc~My6hn<ktO6U#5%sqBacy~M5K@%yKQZyu'
    'oD644jV?ijQhKfkV5Vg0elxj5>aC_mNDUS+ZU5TTA*LK`71~!a_^tf;wSu8!^%1<Bsy(kZL8+$5o@BGKO0AKzM~iOJJe2^$x<EzY'
    'FpZKewfrtN`!y#Cp%3W{qQ#k7=c;+Qi|ug=(XIycu?7<ww?(T2mK__Si6iQuC7LtdB<odhSXm!OLGU(l{b|v=*l>&rNX5$6P|Bq`'
    '3`s@RUB-&FmfRbtd|j)erT%+rt<oy*OmVZPgiI_nEePb%cvK(<8yp?cfd30wLz+6a;KNv~)_IeYaa~6ClWasS=C;ZXR@7R`S5#9;'
    'lFd;W5kxIuNqG9b;*MiZrY)sViMbZ2Usc*@&7FkoIzP*i)ACserA3*FM3SGHy|Y%q^CYEKV|a-W_SJ$uZx*Vt+NZ39OjOg_Or$|V'
    'V9|&-HD~8h`IzHGc-g83LnA2-{d~>YCf&}^nyF1RM}1i8q#>$i$do{)j#FBYa9^{c8f4YZMKC=#ouN_}FSQiTBqw$dt6S;M#AZ<)'
    '6}Is$K47mitzX*e70OO|Or-EyE1E(fWX(^<$423#oO7yIEgIS}=R#}Iq*R)z36)}aBG(*Jba7!ke^rC7$gIj*h!z0~$wWO)W>;AP'
    'RaR4_xZ-+CDGcnOfVxzAgOW+@5btQaNYS)lL;`hz(}-EJwTsSnhLxFgk&LKws@BlhzzH)5kC|ekiOCWtz!c81Vl7mQZuMBlVC4Xw'
    'IQ+HlTZB2MCkeY|y3$K9rK^|@>_}DYij6HM<bYqqfi2cn?rB%;{xTOk;F>e5I_!W-x5$AFcS6z(#yn|ryCjyRsp%XnfEe;4C^{|s'
    'qui`J^eE@uJVvYZeHG&}n(R0>%Su@r=P68bp0vZT^e;51eSr%wMnJt4+=YN?2cMqt>q@qZyF7Jw;grtQF_*Nm@c^6YIpNX^jgGm!'
    'q|)?fb`)zUX8oy{jeTua#F%@UVkmZfqVIeL_eZPJb#(?wBh$Qq>}Dd<R9eKfHp#y!C7H(Q47sEQ(;j1=i5ha5xUNexUQbl2g>6e9'
    'b5F0mjMoZujyZ*vwWKsN2ET&gQO<dEre;lzp;Z!DR}Q5aMx8PU-sLO!{Zg!GEOVIT*u*%|YqF;rZRMaKs<|fgoZ0qnmHwg`)K$!a'
    '(NvRdA&IG5+h1oc`BPLwhS$+F=QfF8Fl40S^)Cz>r;yPK=155fsll}Kav-%q2}G49HfJYNS1<sRH=}hqI0}Yu+uccw*m*(mhzCh_'
    '4aW+qR6Er%yGih)vNo-VmsH6ItJQE+XF5=9gODS*Hd3*hWZ!E@E$s7DtEgf%xssnjaIZj$wBr5h?TRv4;9#<OE^Oa|ES$yU&)sx4'
    'gP*n#;%*{};V#)OMc<%3mx;QjDU3EXtg1paqs5sAKL$TR)ms>JG~w*nOQvNVRcD@;NHHd*cZV~b<765t?Gx<7NPShK!j`CGqnZW~'
    'SlN&nA*yLtRHLZ|2y7n^7i3?ETeGge_Zr%yoAFIsL@bu8<s(WKYT7D;NaGgNhD+V2>hlCof5BF>OkWebwU5!6UL?j^QtQ9s1U+_@'
    'G`$5xBagCnp2@MUxy!=D8J5@~S|$n4in3yIByYOR*Y47Ep|5TQDx=1Ts+n21a!4!4nvubA6w${45-sdrIO)}w3lFp}2+8g)^m0fF'
    '(MHWPeLP&wHpvK9Y!+vJO~(JF?x(`A;Yvh=(YMs(6=yowO3J3ekZpOy7*Lv7>KVwo+BB}3-@e8Rj<^=<<za3;C^e>^kn!2<45d|s'
    'RY{Wy*-s+o+!Fpmvro7yQ&VbSSEhH?yxumpd&{=*KM{yh9H)x4OZ|Oint4xM={5B;lt^QcN$5qBCowczv#~s)2Oo`DOBH6-1r+So'
    '%)v#)w25tnOS!cbTB&x;;CeSTQ^9oAu!5*+y1dYuBA-ogEunUSQ<Q(NBhXvfs*LhbW+i@FDM<5#)srVqH?6#3QRHm)xFkpzGHepI'
    'U%7L%D96kbFY`Pwu8~&rIE8Xvl}3WzY&ho0AkffQE89g?D>iBNT2E4+x}-5{DQD$<j2K_^PTk22*>QMS<AGUb$n_<A+kiZzFShd|'
    'i(YF)SSGkRQ#Yk^lSFIATUPQxI^l*1X=kd8)AZ{QCkND1XQioUUGv#;$Xfh`0qIV7W)5;cu>g*(A#i(VLV@IF<}QWI6~KN{a;@fQ'
    'wPGHv7|iUZY-)%(&hlcoG)h&3r%uR~?@CeU`$Hypy^9adjv-WMcKXPar>zNp1{qPpk*nkdh25__NYi+iVpzKwB%4+9M}9~(kDNkf'
    'dNj*ya5Fh@RM;4kQV18?3|y4!2DQL(qxiOhdOtb0D_T)C=FrR*Vx?T9Woe$WWLI$58zBqlNS29<#9Wk(SfJ!AXQ($#H<xh>lyU=!'
    ')Pg|^+AUzs*-S27r4lO^U~+!qi>nB-oi$7{u85BsH82i{R@-bMeXk#oCa^1-<sd1bBxqV*H5W%}FiGSdRZ|Wu>xQy8RifgibPB6q'
    '>a%RZ;ld&9Eo_Y{r*G9hq}qYfP!v}@BUdU}@^vEhQk~#Y&sLk;xy<sQw5U2Kzyv>W^j_RwG?t0~G}tb%7R{8$rM-E!%l*wDuwQD}'
    '%uK1(D=r=X(%Hya5!y~Bv`LCz!!fP8X+%ZY=vdPP(||e*#~RB7?Nu@RJ+)zXYB_SAxHjw!p9MuqsWvtFNnTu6NNjMnRgU)LOwS-N'
    'G!wJUvZNUxQ!OVTV_PdMXM{o}VMvzJb9Zh|)V8%Z^;c~QHF>)!Z=~#3rImEoPU<8LGRmx)iXDOzm`Cm8ttx18xU@2Zj-6iJp3Tgy'
    'W=HK;4O*4rQ}$_0`lGAe>`$-PI!SU;laF~){(7N<-ZxVW`yw)7IicE=$W)}k^O|^#8%y9qckbGJ*4h{lER>3Xz>qXb{r-$~)@%y;'
    'WEF?3bGh;qH&b&khM6tUiW#y@t=LKD>wuQxO<Ln1D2e^aO<;LeC<j`4dLtb0pzHB<k_|%*T$SZo>cO+Ao2)F<Bx)ZoIamGByf&+1'
    'QO(~eR^HJpuoSAdQFYdcm|8OlGdXsZ4yo{0v(X^ogR4d``~Sshx%$mc{aV4oY36C)T`Zn<euAN|B$s-}8SfgPjh%+fd!c1yNKVu)'
    'K!>4rc9RFQXkZnUSM!tDQ>dkdOt7$5eb=i3#X$O%VjC{V6?Wigf>E%zBF*xP6=H-sPbwDIpx9R(%oLuwD(%#|j!Q7Jo~bvU-2$Z#'
    'Q7$aASizueE9yZ3i)s7#mGO09dBK8la!T0t=~8H+LalQ(V1;fB%pCaKdrQ&gT}$Wp<5TgIEbYOpgqzgF`lT<ZS>s|QGObL;St64H'
    '6w;y@*<6{ViZT$R8H`^QQ7OpN9PCs5*mg{FQY^>-Axe14&9Jk~#E@q9o}MrVS$eiwN%lmz8hf&5ziJ4lf}5RQUlnW=yC$3;AR)yI'
    'Gu>v@ORGdmEukfta35>|<}d@~^O}o3UeAA5Gf>t3cy7w|h1_H1wO15*+kZ<T7!4U}N#=H@XU|UdnYdY2P2(m#6J}*=nx=%&<*4S*'
    'UVy<esWX~s7Fvc7d0!P*o7gzx5)-*zwSY=B`;ae9WV{tcD5mqn7rXw|4%L#utk(EOXK~L->Ou3S_ue+$I4q}#ood!}a$%{GP8h6*'
    'Q$?uP+di6kAJwc{TAln0O-fmn7i{?kXAvnDPPM%?W?+|{IhT@T&ZZ+Ntg?!<K7pn-!VQ%!om+HfLVgr)rnR%Kt+^7s+1e#KhNe{1'
    '$z)?bnW@C9;I4)O&Js&WC0@{$P6JT7+#jmOEv%q}Tgi4_6<aCHTzsj;Nb;l&&jG<B*mPpoS<RpUFmT#+urO1cw$SpEXqPOy$=s26'
    'LJ@CDV&~d9t@y`Cz498o7ELuItu-gr;waUN&6!3V17uwY8YxS5xs5u_g$jxaYvDZjnu1wnfqiDY9~9x*5MzPM*L_pb=G+Cq*~%Rg'
    'Jc$)Pkb<bUNWE(Hnd_=PXbdVv+USDo#4N=(-c2TIRF`M?H5#5WVcROz5FA!g&h`X)U+nt$ZnZU2jCqPOXf1iO+0V45ID;<qcH&i?'
    'EWoVDAbWd;(b*6>)yxxU*$x`m$c*%EwK_4)01mhgRtXc4-)9D-J4u03v+MHANxd}dwkyV0z{H_mjGdUw97HEnNuuQ+6`M*phNUo0'
    'ZdNvF+@`QhP)9X(wQ2%tw*^wefn0H|2K!d{Hd-fAQ+#nU|Ai;fXA>82Qt>|X9x-BxW?`?C>QpC0uoY^ygT&SY{lt50F8m7H^isIs'
    'Nf{O=@6AMn8pblYVD+ZXHAxU+=qDwlkZcPznk!=`K61+l6{pi8=wOx!lx#zeIosb{>crnXak;E|O{o4_vr$>G1LkY|#WJhJ)T~_L'
    '21r>2qpY?*Z<w)CC-sk%KB4t>G{F=55*0h`)+A0F31yv+t_0J#)3Wk<ySZjCPgZMY?<!6qzm#~gGoxj;8O8ZKp(%ZNT&CjLq;<?e'
    'hqEZ%?P@gfQG$<lO7z5YFh!1>I0j8zg+nd)@!@@|>%^<DHIAq&k&-FKZ80y6<j(5#ZTA%WmQ+9sV`|;5r#zW_VXHpz$@C&j%Nb>b'
    'QKTZ@H@h-=RZ~2vnYnZd&IUqfr`M&armMU*#YM4H5nI{Y5xtX|O=HLM*qm5yz7SPr27#R-#1yjDa@_`%n;ouYbaHi<s1?|T;+_eK'
    'yc$ZgcCLA!^bnpjG*eh#xLQy5aiZ-u8~WS?<ef!Hm+JI%by0$CA<6_)(wT1NS?UZ|6I_~mFv;qjm`+P(O1u_3H<e<q$^?S4Gb^(='
    'GJ3Q7mCtr{D92G0F*<_^&E7^#r6}0eVSPZ7Z>CF|D~%^=kS2+mi5;{8cUGEjO>)LpjfgLW@AR!sIvXX)6UPdJ5-MKKnTaf7Mv*zY'
    '!UwrD!n4M|F4OESe`#vo61y<--%M+wngulL8XZmDDc%OwY_pJqZHz5Avv&3G3Od-$dfHFool3+OI9U!_t3cZaS);A=v}nh^qK%-%'
    '`SF*gAFepnHc_HTqP+4jfzrJU+-6l!XK$SvZej?vOL<tWc2gTu%1rd(gJ09)fSk9h<ki{P4C|h2mwO`Gq!`@9XI^0=sXZc!-ICRc'
    'KXJTN>V^KxL)n^@ljx$I)VKy^%h@*OyJ@Vzh$h<>w5V$m%$*SSB>rf(78jQyaTR}I+T{ume%3WW1J|$*W+F^IHL1Z)!CHV7O#lH2'
    '8OjbsgAU@fSM2~#mN}B2TjQ-<5~qfaxOQA|mU4>YY_Byn%T%IPE-$qzJDc&VRfmY#LaPPUW)xDEo`@z+rU}57GnYlp8iA)v9arq}'
    'R~wo}OO(viQ1;tuRnEz*q3vgZ%cSF^>*U09p|<b#CV0w(pHUr0AFftKVXFH5ln@fD0xl=lH)NUxoeGv<ESMA%&z}M!ILr0sFt2KG'
    'x*1bm$F9nxL7JAJ$gJPHID@}a*echAXdGvv*{ri9%f-P{QmnKXnqAa3Lyit&ioZ$dn0rFlF_uugTv!w{3o=c-q>NmygYZ|<`V~jA'
    'm`Mvu)v)CktFsQb&V<dG`LP$x*wD@TVKyNdoE@XHT^ePQ>S(h;_PHn?{s~;;4D!rRvhJPffM%bdiW_HE4XnK_3Y)jvm`>8}f;X3M'
    '*0Lts-l$1*C)a3JI-wSric+gIYqsVm-N?9K*|eHR>+~XaLm<NX)bNRHXV}EoG-(Pr%M{~ZyOu7Ee>Sr&qc4sbDPU~NNxqIIRF~kV'
    'yLxm>%0;$F+b(6F6!D3bgBF}!AX{zwM<h*<OUOL%!L^H1>?Y;Yn7_9Gcuru4FK)49B3R5=o^43494V8g!IO4o3b?+nVyYrsC^E$Z'
    'ix*Z7_$47CUER`m5;|O5zcPtm*pRo$Y(dXPnbwvto5@6W50QQ>?bO_C2e9nKQbsGeu*Hzi&7?}Mb5O1Acx}5$pU}97%9c`2wgwcM'
    'W=@}0%s9SXR=X-VS0N?DRDUPge-q%^W$<D`zE11#4xIta^!rtKQSprn`ZSW)P6sxr>8fSEyzeLH^SH~=KPUpJHcyQ<#<1zOm^4<M'
    '$N$7R6F`ca&N~Iic~wH7fcM&IGo73~<`gPO(b(cCX)&Z#=MlLa#Dg7pnnQvZxz}()N}DyeOJ;UvvJC(-su$Puh3R|iykQNIjNILN'
    'Kq^l>ouv_|u2LG>!USlU6FfESZ(i$5%MsVkpEM!4n%l%dr2sEUXFueTEJ_Rp;?7-7t7^8PSuIT%b4vWdliO9_FE`1zou)WZ6|CY)'
    'E7TNMQNR7f;gnbn(&7W&Msi+(MJpZWrH|tDjHLCl>IVY!{H%4Y_r-4YvVyhtRqJqMMxCo|My5Ea-(S@`Ns-H&OiB}H*9U+zzH2k-'
    'LO;?P{97wv;0!RW2@++1Y3wdA{(Vxsh$Q`$^F={MU!+XXpERss+_0vIjm58Hr_gXSK#gHeS`~6$>2@W;A|Q?53xjU9a;c4<inlw1'
    '`8-Kow=+GK3{tV<H+JH9E>No}3d)kL2zGVW^f+_8Kpg-jDU}>1(P%|_d%N(8VXM3587FNeHOSH>E@G?xlZ2mY=Z(@nXrWM9DlD#6'
    'sMi^PTIIQ2;89z$J7dlO!R(f$2dqR3fJE$ur-F910u?b^zDd;~Lt@Ny1to}CZOEdfQ<}F`=y<h9Bg}S|^81xsP;R2ADqG1+xib5G'
    'PK-UVlL%HN`HFtyYc|2u)=exGOK;UyHcY~%D$s_f^P?yqF_!b;W4&T7c3EPkqi~nXI8g*u%*Vw?k}NBTGyl~#Pb}26E^=sUc?lY7'
    'Nt)yab?uB&nEYg<e(P;o;RC9DRJh-r)(g7k3&I~7itWUa!7UjS900CqR>9b8#0;j~O9jtLv?>`ewk!Ss)wf!JUp?OP_V(uE{g=1@'
    '@!{70cev;6hfn>3qwV+h`}h5_rQ<%m{rK+7kGIQ@y0!iI(GR<ukNty(2fTUv-RIrz<KZDW$s>upd3*E2?e6o#qeBQ!pMJdgw?7{~'
    '439;VZ~pT5&_C=xzx(>*=a26mZ+V!`X=INT9;b^=q;L`O8^Lc1eAACCeA6m?;}cwj1{bxQF1oP}7Xp9NT`9xwOTgRU$pIfA6$Tv&'
    'KHB5cGQMXp8Smkn=-``JVVcRovyzARCtS`1cV%4kEby=#@U{lO&jr3ILf^n@WSm*96`zKG;}<lvh_~U?GVX1vGMH!Ai(#P(z9$D9'
    '8r)Vq&MoVISKPpg6wo5Pr2(b-&YR$y48v><9{|Jb2V(f>jE_d@Xf!ry!wZk|!J|U^fj>clsJLxS@B&vI=hj8cX=vWVdU%I-)rfb&'
    'Hv%i*ahwZ!{pljW)V#pS?Y9X&4KMuY!Z*CYvAK%J7^$#08Ld?GND_E~YZGBQKDEKD18k@dKr5Yj!jl8eAUeD#9>0nB8+cC?_)Q4-'
    'XbCt1xIiZBrQj6s^aoxKn6^kAY+Mvrst82sQ-E($!wWo$$e4VFUGycuZ3PZ?zkuHq;K07%?_rq8*nCb2M+Ubge1A&#jmJGm$jk7&'
    'J6v^qXGr*aT)`A^0q`6k<$C073t%%`z>|rj8^{UYVAA4%FA2OwP#Q?*fA|)94Gsn=rNMIaF~evotr;-_TmXk#i{xEn94!D4mw4C$'
    'R67=L=;=aW0wN%QL_nSjstt=L6D}hB4SOpAUlS7k#Nhzo6pF{cam+5EY(=J$kh*Key-BzLpm+2YfI)j8bwN_?Tn!!&0}LnPLMKpm'
    'I%9|5WRMd}7AXD(hLeyYQ%r+LM>wF8faMC_1l+gpO-79b*#nMDL<T#Be5}78XA^NSxSknKo*=tfY=+ZC1+gip9!L|sK=PoY+kp24'
    '2gDv691wcIQuzSiWO^E0AQ^QX4+iRB5tmQ{tO2Z42{=)ZMpA3kXC2V!2oCsSKW#8K53DR8#|y|k0*a=9M=S`i&n`6+T;Oj)g7@?%'
    ';5T`68>(Urk3Sj*0%s?9;BwvQ!Ra_0C;Wc(PN1m}kqROXIs%1;2q!*7Tu{0|BV=^}3@Bt^;r#*zid=i?DGRrOUe?zWb#M^eLXQSL'
    'CJ5~tt^n|YkUYL6;M5|H8HWtqCln;F3JP@B-Qc3a(FrK_y6%?XqR=-5E?}4q-`Nu01vYVLC=lI%lY{__ARuE631^d$@C$xZ>2Dkv'
    '5*N<7j|}#?!9GXSH6mK|5$%cS!5)boXg!L<ZyH{JBH7OxJ`EQQC4fgE-de!JmUZF`Xp@FgkUBt3?<)oCSu-vUKDr6+J3K8SH}4ln'
    '1eqwR;<5!?5BLolTU|?s-w2$R=mRcjz~P|!=rgQ=!_7{()&<uCiKRBA4>|=6_YgJ|RF~B#Bi>c%Hlmw`tD*mm?w^PxfEq>TsknRz'
    '*T3Oy;IHt=1(vt~t{7YtWYIO@D&b_9bI>wH8BqW&0Ep9wmMaR3C~#IH%D;#fX+#w<qD9&@CwON-;zUnCUupb}poLu$N^N9U$ZrML'
    'CWQeBOTYp6!A=MIhR2K-73l`|BO+I$+fWjqcd{=h3?SkbMkKFDci|UsHU+hb0P-eeSeZVqG~hKJNf<Bkfa+11=@&>Dcx?D^Wj`Pj'
    '<kqW&!3XfdAa{#`-vs(5>pSCpMa2TeKQilD@z^2JI$||QLFfjLsDwteEtwqg=M9e_QZs6*eVvd1an<<(DKMhEM9Z!(G!kl|4MpjR'
    'dY%;2A1cW^6vZA_U@%Wq&-*;%;3B#-y1<hjX`zs%p|HZ0N#N0mDEwnWP7_lZy^@y}U2LeGBSQ&jFNH=D8rLi!rJ)tjheMl-^K@08'
    'r=yk0IM49~{EcIwp|sJG(emT#>AB=!gr9_j7Dz*bs1X5?6l=soaGUU?(b+(E<>~^*iN`r3+ed9W7F01ZKA<4cAghT5H?!b*EI>}H'
    '-;kRa&V4}s7%)H)(F?Q^kZH6~xViZLgy#XtA%RsM(Wx0TZU@qQ8O<@2(FMx=)djx3(l(*vk*s4G7%-kRClcbgOA&8F8?-M55)B^h'
    'j5<-q1DtV}(4Evt!;jVjsjeUsqxGnxn{a9c2_4Pjz8YwF7d)L|q@$9)8HyjVYNRH77@st>s7s*f;7LObp&~yl$oJ4ni5N?a6*SRU'
    '10BdTda1`zV;~H*f{<`*s4kE>5z<J&(7D6+(^yc&D|qaX&?>TI3`DM`TxgvmUf@xqbBC1P@N^(OCsaQpMmb1W(zzky*dwnYEt3?>'
    'MDh`TlW?3Qp@`YzD$_~DGmL^Wd%O*e)`VL_+J7LWB9N7W5{{TS#-BZik$}rd!ZV`Nab*CNG*Yu$7+5BxapP{{Dtp>z(SH&$>C1U!'
    'gCn7OWC$LuQICEGG=*Bw!?;q(w~YQmG~c>bg8m`&VPn=sz#|Ya>=;lf2zYGz1IXoy9!vDJU^YO&AV<Fq{h#QOp$pv2fEMgxLLUD9'
    '*LCvHQ`XTbdx)}h9HyesH}ElrODXw<ABBk%4ig{vH*^~&zhEj7f6?&w6-NVv@6emLzQEsLR1-}?V`b1@UcHna(CE>1xQ2KeCLlRq'
    'M;D=<bsN2h#&+hTF?`9?k%t%bG|Xi|^VfOFXAKnp##Al7pobBG$dHbVrwz$~ZX16?R2|#sB+xg*v0?nQ-$gqThC~$xYe**{`@v`^'
    'N06UP2c`~bw+si6Mq5S1#-qu@vs?y?n-fwVk`(5oF-_wIW>l?agDE$zQI_FgHvBNmP(v}!PsR}AikA%2JTVc@W0s|7#xz<%3{Sb}'
    'nx0FE)AY2Oakw=^wvm=5jGji6f}~2n;n@%;B1&naU1JW;o9jnU!z>vLgSl974?-U84&4?<*{QU>yrM*`LVG=WvKyYMmPP|W22NDu'
    '(})U@*m(sg%dk;KEv6I)Og47-fGC60R+Ijk6(>W{Z=4A_?roGV%`BT9%>+79lIV!8R2dp5W(;~v&@F=_+6L={`E_o*&-5%x0v<9l'
    '-T~LnI#R5x;5d<c^KXdmD`l@E4Pn}9K^nlQx5L<(!!$A{u?!x~j1>p!$EQ7y$dmH#WjImq2d`-(o<c8?!GR*$^yuzrNF4=PWW;v{'
    '6h?Gzanl6XTu?I7l&P=)Glu$YxVLe58>#7NXz+I8bTE?1H4C^;R9L{2=CYoy=Y<OZP^H761!R$2^gy#lJAu-ECDBC~eZxx~2J0ck'
    'kM;_WIL0wn3yPH*!+i$^M~RuPg8knYDvU}+P!#Z(ah|lCiE^dmKtH6>2<jb}&c!>0j^tGp3{g?l`E}$qLwZ0Six+|sSWi4Q(s8FU'
    '9$Z2Grj7(~KotVV$>e~1fU1Q?Z^Q_`!(5TRXL+!-^qbJAj0b5$^dl|kGI5wp<}e?x^UkVsSei1QC!T*9F<%J-Z3g4^t4G&1Tyz=j'
    '0PUcsRU57+9s=}nbhZpnD>Q;UoOYt}G33~orON9@x*ipT;5YOhK{<t$E9;sy+PO6P4e^^m{3Z|BFCBMUw~Ui3#J&7rJ&4+38Zm5='
    'W<2IH`VA@UboOZlY8YrlL~TNvC)MM%HXL;rFlI1p@a(gymPRf(-doyrKNNW^So}bD<}KhIq+Q2zREENx4kDk|GGJ`Xe)(xYY8dY8'
    'mMR`mv{Fc%QB5VE2|8gUG-yFssVXC71;@s>(U#C~XoKl#VIbZyA(&-IMDsLc%2dX>yD&Nie5lf3Fe_poX-=Nppmk);&^pzT=0ax|'
    'Q+-^d(U3f-WiU?CX-FJkSrHfHMH#UOI<R4=nbQ*Hk(zF>qS1q^KkF@FwCzYKydR|0k?x3Oha!XOMjU1|^Y6(VWPNpTI7o)C#y{fM'
    'zK&!WO^nniBw@@@BON~?;~;<kN<kZ#;HYT`2KlHmk6ww%$b16mf;lV|lh4b?iH8~-IgjiM8W#EwsN#KP2E>ugJu)ezVGS!eZrGXY'
    'MsjGSQObz^-H=R3cPCYmjw5OHv>>$9B*=0e92BhIa|!2ziF_;Zi&a>Os>w%q1jKhoRxS%~T4*+(hsGBUfV?Q7v=P@BnWbZ^2x%1y'
    'oLwY=KnsA;XLLq;av85I>pYaBZRF38!720u-a=onu`|+1m{FtgM~)3l(CnPbkF>lLM=l)9hDR4Cl^3iw$`7fg4CFJr9Ej><q=2&1'
    'ga~a&DdZcWttHcbB&taZNrSl{s|ucq`iBZ4S)OABe&oW7Wn>1EvPUO_sGOXgv=lf?ep()C`J_@2Kf$NbsYRI(X#Ywc2|lu5>QG^K'
    'qvc$A59&ZZkW$99Ekk>%4(=)=M_r7=<wR|V<sem#qKwXQWJ|2fk2qvDLtl7Gqr*j~o1`641da`pRvi{b@xfz<a~oZdyR}c7vWRwn'
    '+Wqi{4>z9y+vv-Ww?Dl9^5y-f1>opyO8p?k;NCvL8GYT|{IGoS-#>l6zxnv)cX!|4?DqTJ=i?1u?mm6qEr?1dJj6F|muIEp9bZ4c'
    '|HJOf>78%h_Az`s<uLUR+&B4e=SnHEzq`HN-|z3j{`P)<zuUKcpHS?x+L!&^u77xYzq{{Ocl&<VZg+Rza=+Z|Z~ABb7j56aEqfoH'
    'mf)KWzYlz0`=DaFEw}r9+uiQdzU93vqut%#@5+7|V*mK|{-*73!+l8i<?!KdcVG7X|L<<f?d@%!Pu_p~;k$hwb@9u1?v{UdeUQ6-'
    'y}xUHJ<Hwg-LflvO83jU?{{};e_NJ4*q8g1?svC$rS&iF%l%EC)Hfe~C!apR>N~A0W6%4N`hN8PTHlPc^ULJ!Q{LyW-=$LeH13w&'
    '*zfx+`~TdR+g<A49A;nceum*M<EhKK-$Z}km${F&FZ=RGyS=@?-*@)85Yj&T!>~K0-QMnUE4$ElChYbL)$hx$ExYpearFQCG>x}E'
    '{Qm2=J<)ediq!(^zu$EMx6s$U^R642uI$`?Y0>2F4xjgbmsWkU+<w=VA7=4BFW`DRch`UI_PbVEC(LiYDR~+3>B7}6=?;HC4Sbp7'
    'VXB9ZZ~WmC385YC>ErJ*qJNbSpZ^Rrm0&X-|BH`Ps{UabQtM%W3%b)`S89%j;rg(ATlUU(MY_-aTMqwmyf?J^PwOtVk2JcaS;EtQ'
    'vY_YJ!?!6cTe5tzTjnSWx@+yU^fRn}rrA90!Q;Bu1I<WZT6ZIdTW^*R+g<-GJxnw`On2XJsmBxj@V|fg)$!j4{6Yj%MD)Z1oML}~'
    '+u|wuqhoOlsMt>FC<v%{3JIM66<vM+kv{`ak<%4J8YMzT%5cUD42p5~3#AWH?jh#8Ao|%VTbVL$DE+9862;mu$*2zVrSm8&kta%7'
    'I&m0Sq~I=j>B)$$LuWprM^;kj;~?_HxQ@;beuFirE|RU<;#n#)eojBnqi4~wQ!>yXH>;LGzKbW5gN!b+^f?qzM^2bH3_fxsvJ8AR'
    '6y4@;D6UCkqs%4>OHv*oQE{T|xG>6Zql-39g&D>O^C*>uRw|DI5FBQ}+eV&5gtS_(Mi?b1)FG`<dNw5_<4-8{fl`q1_rA6vIBXu~'
    'G2~I~k&*!FFbWt(7qyNqID|qrIetUQ7qmGt;;ZBvA35x#jhsp3izYNx0;Kf=oISSn*)N!fJh2Sia$`?WOG84Z;M`zmNqTXv2Oq9c'
    'IAG-sA30(;rb2V0l_A-KJ3uaxNZ*VeMqb`Da+vy21c3cObcQL@uf~y^lw}`Ykduo%M3Edkb&#qaDG)^x4ij+*I1@!tA`wf!M}opC'
    'Shs@VOe43Jj{{NeIn>b3Iz`9@5b3}nUZ}&GZ<lBZaHTSOo(Tt;@Rsqk5#DlkqYHWskA~KrzM(*v5Pmh~owvcEz$)3k@tC2H+>e(H'
    'm4ifpm#7e7F>Ti`F*6Fi)wno?T(YPE6v|FUw`W0`!ps#c%XElP*X>K38gfjUjVHE%Q$w(hzBa=R8SNn>g`<&?Q3c7U&k%+<R*J7c'
    'w{hPK@=v}%Cp%Wh8&Au$y97L5N4bm$K-#BW2H@DdSCoB-RZ#_(s-VLh0ft?r^kTx@MqW@eeS=`($a5NJsO7<Jh?war4F?%=<rKk@'
    'R+VUV@W9b7@Sa9mkbp0(xH>p$l%o}Sb;Yq&l&TdekuUK0)HKQ(T3z68kU|R40d7_y#f~7?iTsI_QT!L2DIzKMr7EMP@<TNEK+_JR'
    'MWl>90-dJ|{2PJpkyAE2zX<Z^5XW$}Z*gEdrq)KMkJtnXU)lmnbuEps{&8qHGSsaqQZCaC@>9OR2bVBB)<n{6^c#K+{w9oaCP{d+'
    'd_pE(khO8vCZ*Le-3_S=i5&s9$+uH6S%N@<5hA63gBR$UskBx68(OJ6I@OeMMqM&O9Puw|7(w%KboAnge=+5h(M)+k<SfpH3U0%V'
    'Yo1Ob9oW%tD)Mk%_%O<5Ce45)Hm@5|SRS1?YE6Nhfn^_3C37aa3uPys5nc}&HQHd-#>*B5OU>KEbpV4_C54WKAIZlsWFMmw!ioSg'
    'Py~{7i09HL(*_(Iq4N6$J|GNli!#~*<V>~Z0S%C2kZhTitSlq)5*ab0I#Mxe9WI-U$ctnp)p>?Ayg(wNRih3u_>(jeuWcknGqTA-'
    ')EWJVgR{n!2I;TNW0-JcNJaQfXnGfwK2fBvL``yJbb+FioAEG#j?ONnE3u9>6e!Hj%YdfG{DK({s&BkFxCfDN;&Ii`_GmboR%oG;'
    '4m3}VidO51B+=5y)k`JL6>Z?5&dJQ2I5SN&(X7*GI{0J+o<{#VB|TD;9_)SK5i7Z0)Y0!TH&CecO&FMHxJqTDP>_O!uC$e4%p(>{'
    'XNcB<2G(#cqBpAY7-n35gHy(qIOys17|!$*XT;tStIZ@)z)ifufcY_p!oQQ~+11!Hpsxn*IX01@rJ=v+B9BNW;j<F1Oi07u;NLiW'
    ')YKZud@`qGq}0|SPbX$gvWKKn#R*6p&IT{2b6V9q5O{(#SzYA8p(Q$_b54Xx>Kw5k3T%$NPPLF&uR1xe4+l0HBYbjP0BUX)Mm@Ih'
    'pa!H3g!E&S4s4W$!3Bg}@j^q1^nOGHtVrk#i$IbSIh7x22t>|lzyVf^iH*Fl$BV}t22Y1Jw-GhsIytf~NOBXeEoC5*(@+5(Y2Cs;'
    'CDbC?NH^yvm!Yi3A=3`f1>IK8Qn%8`0zkW(_(^5=5~@x^7Ye%Ds~h1furIO>8ugJ=KafuzO)wO%?7GLdlti};eJjX8kOPzb!VU){'
    '1|&x6O2?wc*R#<T3C~Ih?o9^xXoM;khDdgK^k6Te3j*cw1T;9r@8jEskLKT$;l+3alqE%zqX!U%Ax51En22UdOGUT&(Zl?3)o2gs'
    'Ct-Nuhm%f20Ks(L0|pgT4D82Xk#TrYub_xDd>ZZHc{DJDP&B>?!vU0YCQA4dj6fKOh{EW+(RroY`0$S?GUO3g2<JVx4o61BN>d|f'
    'KDr=)OF#IHpuNjLh5UdKk|z(Xjh2I9LE8|rG!ECZjLz$D*Z5+{a%C_9N=I|#hom0V^yugZ+fLc1VK^E;+%?*E8IcXq1FxBkz6odH'
    '=8o?gV$Q}v$`WZoObui7Sbx^B<Mkim&hTh>0;6T7*U&PjA)&`HZg3u*CrT5O0s0WC?(2sQ5s8hVmEmuO8`Xvn^Ftu$5iG35D~PKP'
    'CoO~8dr$H+5BVEGSrbAj@w7DhTZYVbjO9Bd$VfXq{0+kq6UH^6kP_6V*V(;i$UovKoUls^HB2WT&N_^ilXhK(x#?+`!XD3hKdm4q'
    '?&U$+yf1aYyAtK<G4SRPo4Ag4is3~Gnw(KxNBEwM3QMT6afCpLqSRAr86gN0QYMa*{Ma<iG$O*psrCd*n+CNHJU7y?sluVrg$#dF'
    'MtjYW%yG0;#EdDCpO7yJ!U}(rQXFCf6ELf869+m5L^o(IdlDd|q8C5p7fr2WU`u3-J}WxBDI;PNaWarDo;$iAs3W4yL6JSD`Jw*g'
    'BT;=F*7XblsfUQ(44s~aBtwd38Es4+_9tlLbBpUdSWRI#YwTu@?5&KRHIh$U(jp_MT#{UQ2!c+uWOR<GBVoZDWZ36`=#28@>!79w'
    'BN3Ewp6Fo2(YfOH^Z6w{l?R1o^cp{~Q<#|BsG|jOU1qdQSR*WL;o>FHi3T-rPYIut|4!-(u>%>wauaJI1%m<MWwcItT+Ek;M>CAT'
    'w25fAM?uz`7m$`pM^HSrm7}t_(UFfMo=sNQxGu1bbd@~fW~^T15u`sCh!H4uCS_%WI$yYwEe@0wY#G>vZXD#>68JW$&#3T{bCjrI'
    'B!LNEi}@baXA$Hg4Tj_a=~Qu0-^F-=l+sVA=6O(YfvMd>RFep(pXik8uIM;0s~M@Qq$#Bl4Re`f8UY6pY7EgJ5|`(KJx7HIb@ZOp'
    '2JRkUPo6k`<b@i6@KdfDIY7B^nA(iwp->!|t$d>BHlkuW(`j_3d3VS#Ac$zR+%u9iRsjh`kuymmQVe8ZxEd{G*fU4%UBXDl5fQK>'
    'VbqAh$3Yq}f##JsDvT?Es<MVKwb($~4^4?Q(yUj;uCCW`--9~b^r4wYW^))+Su#D+1syd;)gI*?6BseQ6!i+h#+95Q$z``hb$+Ca'
    'xKZ;DZn8m`u1Iw`kKiri7@L@33$gwtk0@YtxTpY<Mv3k8JVn*RsGc|tZKk0KzzHL6)Dwfc;gIx;Bc#AsMupoXV^%PEd0@9t!Yp|i'
    '9qAR&C=d&Ry&vZJF@q&_j;!O+n)y)!9OjM#7d*oSkmw@%A)}FC7YWFW_53mjm5?$*Qh;hxsOXHnk4*-O1+i*3JdbH4Zv8;Z^Kr=Q'
    'XqjC&1Mz{u^Xd20R)wlU@z^Eok4e@*V}_PTJWK}6p2Z{mhTJoRug<8vad1I(&z!(RjR9m(#GN=Xr0NyjnUbyu#S`0&5`sypBY!7r'
    '-K2ZS85X&W;s?~NjGFwA^O!cnD9QIjXIUF$Eykf3rQ~ts?~D?TJ!!i|JqnSM@5VAChrU;Tjvs^-)1pIx5I`^G4dcpSk#)DNz$HeI'
    '%{A9cu@t?8zU~_=#ovAZ{@-pse)s9e`<t5$j$$8Y`HlRQ04XjQi2FT)l)c1%KLc{sdW!pd>tA~Te%9gt!dL$r4ZphG(}q4!^nG=A'
    '`vn$o+2VWH;{M6)OVc|I|Jwp7<^%9s{Ke3e568{8J3t*~fV~_2CujWo&5y*x@E44}Sl!D~*h`&gc|0M11;lf=V3D@HZ(V1;X{{Wf'
    'F#D?R7us&ST61v=Hs;*{pV1wV9KY4@$3Tj|dOYWEzuvt6@Fd3He*OOQ?#uU|KHPsfp8H2A#r9-(`Q#oyS|;)MS3Lezj(@eMzm^IA'
    '>TwhYyu`O3-v8U~-4E|Se)|0W>z|J=|M+hC^#MUq(t_mppfbJvv_E{YeBvJ-`S!!^=6?72G{{F5_4fBSf4uqf{rm6Uzxh*obAWz4'
    'Dors_7yGAQ^!e^?KHq)+<?E04??3(K%logp({EB~+Hd~x?|$><pKku|4?li+^ShhhzrTI+pFY0-{pnXZW$jo0^6BHB-~9GHjObB`'
    'JFd;I`v3ps{{uq3NeT'
))
P = json.loads(zlib.decompress(base64.b85decode(_PAYLOAD_B85)))

POP = {}
for row in P["rows"]:
    lab = f"#{row['rank']} {row['team']}"
    POP[lab] = 1 if row["rank"] <= 5 else (3 if row["rank"] in (8, 9) else 2)
PCOLOR = {1: "#2f6fb2", 2: "#c2571f", 3: "#7b5bb5"}
PNAME = {1: "live singleton", 2: "clone clade", 3: "public-family pair"}

# the house X-ray colors, unchanged from the DNA chapter
SAME, MUT, PLAN = "#DCEEE1", "#B45309", "#0F172A"
XCMAP = ListedColormap([SAME, MUT, PLAN])

CROP_COLOR = {"WHEAT": "#b3872a", "STRAWBERRY": "#b5486b", "CARROT": "#2f6fb2",
         "MELON": "#1f9d6b", "TOMATO": "#7b5bb5"}
WINC = {"d00-09": "#c6dbef", "d10-19": "#6baed6", "d20-29": "#2171b5"}

plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "font.size": 9.5})


def shown(name):
    import unicodedata
    known = {"カワシギ": "kawashigi"}
    if name in known:
        return known[name]
    if name.isascii():
        return name
    flat = "".join(c for c in unicodedata.normalize("NFKD", name)
                   if not unicodedata.combining(c))
    return flat if flat.isascii() else ("".join(c for c in flat if c.isascii())
                                         or "team")


def unpack(hexes):
    m = np.zeros((len(hexes), 718), dtype=np.uint8)
    for i, hx in enumerate(hexes):
        bits = np.unpackbits(np.frombuffer(bytes.fromhex(hx), dtype=np.uint8),
                             bitorder="little")
        m[i] = bits[1:719]
    return m


print(f"payload {P['generated']}, engine {P['engine']}, "
      f"{len(P['rows'])} submissions, {P['hinge']['episodes']} distinct episodes")

board = pd.DataFrame(P["board"])
fig, ax = plt.subplots(figsize=(9.2, 6.2))
OUT_Y = 33

top15 = board[board["rank_now"] <= 15]
rights = []
for _, r in top15.iterrows():
    lab = f"#{r['rank_now']} {r['team']}"
    color = PCOLOR.get(POP.get(lab, 0), "#9aa1a8")
    was = r["rank_0819"]
    if was is not None and not (isinstance(was, float) and np.isnan(was)):
        ax.plot([0, 1], [was, r["rank_now"]], color=color, lw=2, alpha=0.9)
        ax.scatter([0], [was], color=color, s=18, zorder=3)
    ax.scatter([1], [r["rank_now"]], color=color, s=28, zorder=3)
    rights.append((float(r["rank_now"]), shown(r["team"]), color))

for f in P["fallen"]:
    y1 = f["rank_now"] if f["rank_now"] is not None else OUT_Y
    ax.plot([0, 1], [f["rank_0819"], y1], color="#b8bdc2", lw=1.3,
            alpha=0.85, linestyle=(0, (4, 2)))
    ax.scatter([0], [f["rank_0819"]], color="#b8bdc2", s=16, zorder=3)
    ax.scatter([1], [y1], facecolor="white", edgecolor="#b8bdc2", s=24,
               zorder=3)
    ax.annotate(f"{shown(f['team'])}  ", (0, f["rank_0819"]), fontsize=7.5,
                color="#7a8087", va="center", ha="right")

rights.sort()
prev = -10
for y, name, color in rights:
    ytext = max(y, prev + 0.75)
    prev = ytext
    ax.annotate(name, (1, y), xytext=(14, 0),
                textcoords="offset points", fontsize=8, va="center",
                ha="left", color="#333")
    if ytext != y:
        pass
ax.axhspan(30.5, 35.5, color="#f3f4f5", zorder=0)
ax.text(0.5, OUT_Y + 1.6, "out of the top 30", fontsize=8, color="#7a8087",
        ha="center")
ax.set_xlim(-0.42, 1.62)
ax.set_ylim(43, -1)
ax.set_xticks([0, 1], ["Aug 19", "Aug 23"])
ax.set_ylabel("leaderboard rank")
handles = [Patch(color=PCOLOR[p], label=PNAME[p]) for p in (1, 2, 3)]
handles.append(Patch(color="#b8bdc2", label="fell out of the top 15"))
ax.legend(handles=handles, frameon=False, loc="lower left", fontsize=8)
ax.set_title("The top-15, four days apart: who arrived, who held, who left")
plt.tight_layout(); plt.show()

gl = sorted(P["golive"].values(), key=lambda v: v["rank"])
days = ["2026-08-19", "2026-08-20", "2026-08-21", "2026-08-22", "2026-08-23"]
fig, ax = plt.subplots(figsize=(7.4, 4.2))
for v in gl:
    lab = f"#{v['rank']} {v['team']}"
    x = days.index(v["first_seen"]) if v["first_seen"] in days else 0
    ax.scatter(x, v["rank"], color=PCOLOR.get(POP.get(lab, 0), "#9aa1a8"),
               s=60, zorder=3)
    ax.annotate(f"  {shown(v['team'])}", (x, v["rank"]), fontsize=8,
                va="center", ha="left")
ax.set_xticks(range(len(days)), [d[5:] for d in days])
ax.set_ylim(13, 0)
ax.set_ylabel("current rank")
ax.set_xlabel("first ladder game of the CURRENT submission (Aug 19 = already live)")
ax.set_title("The wave: six of the top 12 went live on Aug 22-23, eight within three days")
plt.tight_layout(); plt.show()

rows = []
for r in P["rows"]:
    lab = f"#{r['rank']} {r['team']}"
    rows.append({
        "rank": r["rank"], "team": r["team"],
        "population": PNAME[POP[lab]],
        "same sub as Aug 19": bool(r["in_0819_store"]),
        "band agree": r["band_within_agree"],
        "plan d0-3": r["plan_agree"]["d0_3"],
        "plan d4-14": r["plan_agree"]["d4_14"],
        "plan d15-29": r["plan_agree"]["d15_29"],
    })
pd.DataFrame(rows).set_index("rank")

fig, ax = plt.subplots(figsize=(7.2, 4.6))
placed = []
for r in P["rows"]:
    lab = f"#{r['rank']} {r['team']}"
    pop = POP[lab]
    x, y = r["plan_agree"]["d4_14"], r["band_within_agree"]
    ax.scatter(x, y, color=PCOLOR[pop], s=55, zorder=3)
    dy = 0
    while any(abs(x - px) < 0.03 and abs(y + dy / 250 - py) < 0.022
              for px, py in placed):
        dy += 9
    placed.append((x, y + dy / 250))
    ax.annotate(f"#{r['rank']}", (x, y), xytext=(6, dy - 3),
                textcoords="offset points", fontsize=8.5)
for pop in (1, 2, 3):
    ax.scatter([], [], color=PCOLOR[pop], label=PNAME[pop])
ax.set_xlabel("plan-channel agreement, days 4-14 (12 episodes)")
ax.set_ylabel("day-anchor band agreement, within submission")
ax.set_title("The split at the top: live plans left, repeated plans right")
ax.legend(frameon=False, loc="upper left")
plt.tight_layout(); plt.show()

S = [P["stripes"][k] for k in
     sorted(P["stripes"], key=lambda k: P["stripes"][k]["rank"])]
heights = [max(0.55, s["n"] / 24) for s in S]
fig, axes = plt.subplots(len(S), 1, figsize=(11, sum(heights) + 2.2),
                         gridspec_kw={"height_ratios": heights})
for ax, s in zip(np.atleast_1d(axes), S):
    plan = unpack(s["plan_rows_hex"])
    mkt = unpack(s["market_rows_hex"])
    cat = np.where(plan == 1, 2, np.where(mkt == 1, 1, 0))
    ax.imshow(cat, aspect="auto", cmap=XCMAP, vmin=0, vmax=2,
              interpolation="nearest")
    lab = f"#{s['rank']} {s['team']}"
    ax.set_title(f"{lab}  ({PNAME[POP.get(lab, 1)]}, n={s['n']})",
                 fontsize=8, loc="left")
    ax.set_yticks([]); ax.grid(False)
    if s is not S[-1]:
        ax.set_xticks([])
axes[-1].set_xlabel("turn (24 turns = one in-game day)")
fig.legend(handles=[
    Patch(facecolor=SAME, edgecolor="0.6", label="matches its own mode"),
    Patch(facecolor=MUT, label="market channel differs"),
    Patch(facecolor=PLAN, label="plan (farmer/hands) differs")],
    fontsize=10, loc="upper center", ncol=3, frameon=False,
    bbox_to_anchor=(0.5, 0.995))
plt.tight_layout(rect=(0, 0, 1, 0.965)); plt.show()

labels = P["labels"]
short = [l.split()[0] + " " + shown(" ".join(l.split()[1:]))[:10] for l in labels]
M = np.array(P["matrix_positional"], dtype=float)
fig, ax = plt.subplots(figsize=(6.8, 5.8))
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(len(short)), short, rotation=90, fontsize=7.5)
ax.set_yticks(range(len(short)), short, fontsize=7.5)
ax.set_title("shared consensus bands, positional")
ax.grid(False)
for i in range(len(short)):
    for j in range(len(short)):
        if i != j and M[i, j] >= 0.30:
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                    fontsize=6.5,
                    color="white" if M[i, j] > 0.6 else "#1a3a5c")
fig.colorbar(im, shrink=0.8, label="fraction of 30 bands")
plt.tight_layout(); plt.show()

pp = P["public_parent"]
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ys = np.arange(len(pp))[::-1]
for y, row in zip(ys, pp):
    ax.plot([row["pos"], row["blind"]], [y, y], color="#9aa1a8", lw=1.6,
            zorder=2)
    ax.scatter([row["pos"]], [y], color="#0F172A", s=42, zorder=3,
               label="positional" if y == ys[0] else None)
    ax.scatter([row["blind"]], [y], color="#2f6fb2", s=42, zorder=3,
               label="position-blind" if y == ys[0] else None)
    if row["blind"] - row["pos"] > 0.1:
        ax.annotate(f"  {row['blind_ref'].replace('ACTIONS_','')} d1",
                    (row["blind"], y), fontsize=7.5, va="center")
ax.set_yticks(ys, [shown(r["who"]) for r in pp], fontsize=8)
ax.set_xlabel("best match against the public route family (fraction of 30 bands)")
ax.set_title("What the blind test adds: it catches the re-laid-out plan at rank 8")
ax.legend(frameon=False, loc="lower right", fontsize=8)
ax.set_xlim(-0.04, 1.02)
plt.tight_layout(); plt.show()

import hashlib
B = {k: v for k, v in P["panel_vectors"].items()
     if not k.startswith("v21guard:")}
labels_t = list(B)


def genome_id(bands):
    return hashlib.sha1("".join(bands).encode()).hexdigest()[:8]


def shared(a, b):
    return sum(x == y for x, y in zip(B[a], B[b]))


def fork_day(a, b):
    for d in range(30):
        if B[a][d] != B[b][d]:
            return d
    return None


clusters = [{"members": [l], "height": 30, "node": l} for l in labels_t]
while len(clusters) > 1:
    best = None
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            s = np.mean([shared(a, b) for a in clusters[i]["members"]
                         for b in clusters[j]["members"]])
            if best is None or s > best[0]:
                best = (s, i, j)
    s, i, j = best
    fd = min((fork_day(a, b) if fork_day(a, b) is not None else 30)
             for a in clusters[i]["members"] for b in clusters[j]["members"])
    merged = {"members": clusters[i]["members"] + clusters[j]["members"],
              "height": s, "left": clusters[i], "right": clusters[j],
              "fork": fd}
    clusters = [c for k, c in enumerate(clusters) if k not in (i, j)] + [merged]

ypos = {}


def assign_y(node, next_y=[0]):
    if "node" in node:
        ypos[id(node)] = next_y[0]; next_y[0] += 1
        return ypos[id(node)]
    ys = [assign_y(node["left"]), assign_y(node["right"])]
    ypos[id(node)] = np.mean(ys)
    return ypos[id(node)]


root = clusters[0]
assign_y(root)
fig, ax = plt.subplots(figsize=(10.5, 0.42 * len(labels_t) + 1.6))


def draw(node, parent_x=None):
    y = ypos[id(node)]
    if "node" in node:
        x = 30
        ax.text(30.3, y, f"{shown(node['node'])}  ·  {genome_id(B[node['node']])}",
                fontsize=8, va="center")
    else:
        x = node["height"]
        yl, yr = ypos[id(node["left"])], ypos[id(node["right"])]
        ax.plot([x, x], [yl, yr], color="#0F172A", lw=1.4)
        tag = "=" if node["fork"] >= 30 else f"d{node['fork']}"
        ax.annotate(tag, (x, (yl + yr) / 2), textcoords="offset points",
                    xytext=(-14, 0), fontsize=7, color="#B45309")
        draw(node["left"], x)
        draw(node["right"], x)
    if parent_x is not None:
        ax.plot([parent_x, x], [y, y], color="#0F172A", lw=1.4)


draw(root)
ax.set_xlim(-1, 47)
ax.set_ylim(-0.7, len(labels_t) - 0.3)
ax.set_yticks([])
ax.invert_yaxis()
ax.set_xlabel("bands shared at the split (of 30); amber = in-game day of the fork")
ax.set_title("the dated genealogy of every named base schedule, week four")
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
plt.tight_layout(); plt.show()

pd.DataFrame(P["edges"])

rowsP = sorted(P["rows"], key=lambda r: r["rank"])
crops = ["WHEAT", "STRAWBERRY", "CARROT", "MELON", "TOMATO"]
fig, ax = plt.subplots(figsize=(8.6, 4.8))
ylabs = []
for i, r in enumerate(rowsP[::-1]):
    left = 0
    for cname in crops:
        v = r["economics"]["plant"].get(cname, 0)
        ax.barh(i, v, left=left, color=CROP_COLOR[cname], height=0.62)
        left += v
    ylabs.append(f"#{r['rank']} {shown(r['team'])}")
ax.set_yticks(range(len(ylabs)), ylabs, fontsize=8)
ax.legend(handles=[Patch(color=CROP_COLOR[c], label=c.title()) for c in crops],
          frameon=False, ncol=5, fontsize=8, loc="upper center",
          bbox_to_anchor=(0.5, -0.09))
ax.set_xlabel("PLANT actions per game, by crop")
ax.set_title("What they farm: wheat everywhere, tomato only among the live five")
plt.tight_layout(); plt.show()

wins = ["d00-09", "d10-19", "d20-29"]
fig, ax = plt.subplots(figsize=(8.6, 4.8))
ylabs = []
for i, r in enumerate(rowsP[::-1]):
    left = 0
    for w in wins:
        v = r["economics"]["sell_units_by_window"].get(w, 0)
        ax.barh(i, v, left=left, color=WINC[w], height=0.62)
        left += v
    ylabs.append(f"#{r['rank']} {shown(r['team'])}")
ax.set_yticks(range(len(ylabs)), ylabs, fontsize=8)
ax.legend(handles=[Patch(color=WINC[w], label=f"days {w[1:3]}-{w[4:]}")
                   for w in wins],
          frameon=False, ncol=3, fontsize=8, loc="lower right")
ax.set_xlabel("units sold per game, by ten-day window")
ax.set_title("When they sell: everyone back-loads, except one mid-game flood")
plt.tight_layout(); plt.show()

bw = [P["boardwork"][k] for k in
      sorted(P["boardwork"], key=lambda k: P["boardwork"][k]["rank"])]
fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6))
UT = {"work": "#2f6fb2", "move": "#c2571f", "pass": "#c9ced3"}
ylabs = [f"#{w['rank']} {shown(w['team'])}" for w in bw][::-1]
for i, w in enumerate(bw[::-1]):
    left = 0
    for k in ("work", "move", "pass"):
        axes[0].barh(i, w["util"][k] * 100, left=left, color=UT[k],
                     height=0.62)
        left += w["util"][k] * 100
axes[0].set_yticks(range(len(ylabs)), ylabs, fontsize=8)
axes[0].legend(handles=[Patch(color=UT[k], label=k) for k in UT],
               frameon=False, ncol=3, fontsize=8, loc="upper center",
               bbox_to_anchor=(0.5, -0.12))
axes[0].set_xlabel("% of unit-turns")
axes[0].set_title("Where a unit-turn goes: half of everyone's labor is walking")
for i, w in enumerate(bw[::-1]):
    hands = w["water"]["per_episode"] * (1 - w["water"]["farmer_share"])
    farmer = w["water"]["per_episode"] * w["water"]["farmer_share"]
    axes[1].barh(i, hands, color="#2f6fb2", height=0.62)
    axes[1].barh(i, farmer, left=hands, color="#0F172A", height=0.62)
axes[1].set_yticks(range(len(ylabs)), ["" for _ in ylabs])
axes[1].legend(handles=[Patch(color="#2f6fb2", label="by hands"),
                        Patch(color="#0F172A", label="by the farmer")],
               frameon=False, ncol=2, fontsize=8, loc="upper center",
               bbox_to_anchor=(0.5, -0.12))
axes[1].set_xlabel("WATER actions per game")
axes[1].set_title("Watering is delegated: the farmer barely touches the can")
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(7.6, 4.4))
QC = {"NE": "#2f6fb2", "SW": "#c2571f", "SE": "#0F172A"}
for i, w in enumerate(bw[::-1]):
    qs = w["quad_unlock_median"]
    for q, col in QC.items():
        if q in qs:
            ax.scatter(qs[q], i, color=col, s=55, zorder=3,
                       marker="o" if q != "SE" else "D")
ylabs2 = [f"#{w['rank']} {shown(w['team'])}" for w in bw][::-1]
ax.set_yticks(range(len(ylabs2)), ylabs2, fontsize=8)
ax.set_xlabel("median in-game day the quadrant unlocks (NW is the start)")
ax.legend(handles=[Patch(color=QC[q], label=q) for q in QC], frameon=False,
          ncol=3, fontsize=8, loc="lower right")
ax.set_xlim(0, 30)
ax.set_title("How the board opens: NW, then NE around day 6, SW around day 10")
plt.tight_layout(); plt.show()

print("crop preference by quadrant (tile-days share), one exemplar per population:")
for name in ("Ryo Hasegawa", "satoooh", "Kobe BRYANT"):
    w = next(x for x in bw if x["team"] == name)
    print(f"  #{w['rank']} {name}")
    for q in ("NW", "NE", "SW", "SE"):
        qq = w["quad_crop_share"].get(q) or {}
        if qq:
            top3 = ", ".join(f"{c.title()} {v:.0%}" for c, v in
                             list(qq.items())[:3])
            print(f"    {q}: {top3}")

POPS = {1: [], 2: [], 3: []}
for w in bw:
    POPS[POP[f"#{w['rank']} {w['team']}"]].append(w)
fig, axes = plt.subplots(1, 3, figsize=(11.8, 3.6), sharey=True)
for ax, pop in zip(axes, (1, 2, 3)):
    members = POPS[pop]
    bottom = np.zeros(30)
    for cname in ("WHEAT", "STRAWBERRY", "CARROT", "MELON", "TOMATO"):
        vals = np.mean([w["planted_day"][cname] for w in members], axis=0)
        ax.fill_between(range(30), bottom, bottom + vals,
                        color=CROP_COLOR[cname], label=cname.title())
        bottom += vals
    ax.set_title(PNAME[pop], fontsize=9)
    ax.set_xlabel("in-game day")
axes[0].set_ylabel("tiles planted, mean per game")
axes[0].legend(frameon=False, fontsize=7, loc="upper left")
plt.suptitle("What the farm grows over the season", fontsize=10)
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 3, figsize=(11.8, 3.4))
for ax, key, title in ((axes[0], "hires_day", "hires per day"),
                        (axes[1], "harvest_day", "HARVEST actions per day"),
                        (axes[2], "sold_day", "units sold per day")):
    for pop in (1, 2, 3):
        vals = np.mean([w[key] for w in POPS[pop]], axis=0)
        ax.plot(range(30), vals, color=PCOLOR[pop], lw=2, label=PNAME[pop])
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("in-game day")
axes[0].legend(frameon=False, fontsize=7.5)
plt.suptitle("The working day, population by population", fontsize=10)
plt.tight_layout(); plt.show()

teams12 = [r["team"] for r in sorted(P["rows"], key=lambda r: r["rank"])]
idx = {t: i for i, t in enumerate(teams12)}
Wm = np.zeros((12, 12)); Nm = np.zeros((12, 12))
for g in P["h2h"]:
    a, b, w = g["seat0"], g["seat1"], g["winner"]
    if a in idx and b in idx and w:
        i, j = idx[a], idx[b]
        Nm[i, j] += 1; Nm[j, i] += 1
        if w == a:
            Wm[i, j] += 1
        else:
            Wm[j, i] += 1

share = np.where(Nm > 0, Wm / np.maximum(Nm, 1), np.nan)
fig, ax = plt.subplots(figsize=(7.6, 6.4))
import matplotlib.colors as mcolors
cmap = mcolors.LinearSegmentedColormap.from_list(
    "duel", ["#c2571f", "#f5f4f0", "#2f6fb2"])
im = ax.imshow(share, cmap=cmap, vmin=0, vmax=1)
short12 = [f"#{r['rank']} {shown(r['team'])[:10]}" for r in
           sorted(P["rows"], key=lambda r: r["rank"])]
ax.set_xticks(range(12), short12, rotation=90, fontsize=7.5)
ax.set_yticks(range(12), short12, fontsize=7.5)
ax.set_title("row beats column: win share (annotation = wins-losses)")
ax.grid(False)
for i in range(12):
    for j in range(12):
        if i != j and Nm[i, j] > 0:
            ax.text(j, i, f"{int(Wm[i, j])}-{int(Wm[j, i])}", ha="center",
                    va="center", fontsize=7,
                    color="white" if abs(share[i, j] - 0.5) > 0.35 else "#333")
fig.colorbar(im, shrink=0.75, label="win share of the row")
plt.tight_layout(); plt.show()

# orientation under the house gate: the exact two-sided binomial against a
# coin flip, the same criterion the openings tournament used in
# "Everyone is playing the same opening"
from math import comb


def binom_p(k, m):
    if m == 0:
        return 1.0
    lo = min(k, m - k)
    return min(1.0, 2 * sum(comb(m, i) for i in range(lo + 1)) / 2 ** m)


ALPHA = 0.10
oriented = {}
lean = {}
for i in range(12):
    for j in range(i + 1, 12):
        g_ = int(Nm[i, j])
        if g_ == 0:
            continue
        w = int(Wm[i, j])
        p = binom_p(w, g_)
        rec = (i, j) if w * 2 > g_ else (j, i)
        if p <= ALPHA:
            oriented[rec] = (max(w, g_ - w), min(w, g_ - w), p)
        elif w != g_ - w:
            lean[rec] = (max(w, g_ - w), min(w, g_ - w), p)
print(f"{len(P['h2h'])} games, {int((Nm > 0).sum() / 2)} pairs with a result")
print(f"pairs ORIENTED at the exact binomial, alpha {ALPHA}: {len(oriented)}")
for (a, b), (w, l, p) in sorted(oriented.items(), key=lambda kv: kv[1][2]):
    print(f"  {teams12[a][:18]:<20} > {teams12[b][:18]:<20} {w}-{l}  p={p:.3f}")
print(f"pairs that LEAN but do not orient: {len(lean)}")


# ---- cycles GENERALISED: any length, via strongly connected components.
# In a complete tournament, no 3-cycles implies no cycles at all; this
# digraph is INCOMPLETE (30 of 66 pairs observed), where long cycles can
# exist without any triangle, so the general test is the right one.
def edge_set(min_n, alpha):
    E = set()
    for i in range(12):
        for j in range(i + 1, 12):
            g_, w = int(Nm[i, j]), int(Wm[i, j])
            if g_ < min_n or w * 2 == g_:
                continue
            if alpha is not None and binom_p(w, g_) > alpha:
                continue
            E.add((i, j) if w * 2 > g_ else (j, i))
    return E


def sccs(E):
    adj = {i: [] for i in range(12)}
    for a, b in E:
        adj[a].append(b)
    index, low, stack, on, out, cnt = {}, {}, [], set(), [], [0]

    def strong(v):
        index[v] = low[v] = cnt[0]; cnt[0] += 1
        stack.append(v); on.add(v)
        for w in adj[v]:
            if w not in index:
                strong(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            out.append(comp)

    for v in range(12):
        if v not in index:
            strong(v)
    return [c for c in out if len(c) > 1]


def simple_cycles(E, maxlen=12):
    adj = {i: [] for i in range(12)}
    for a, b in E:
        adj[a].append(b)
    found = set()

    def dfs(start, v, path, vis):
        for w in adj[v]:
            if w == start and len(path) >= 3:
                found.add(tuple(path))
            elif w not in vis and w > start and len(path) < maxlen:
                vis.add(w); path.append(w)
                dfs(start, w, path, vis)
                path.pop(); vis.discard(w)

    for s in range(12):
        dfs(s, s, [s], {s})
    return sorted(found, key=len)


rng = np.random.default_rng(823)
for label, E in (("evidence gate, binomial", edge_set(1, ALPHA)),
                  ("decided pairs met 2+ times", edge_set(2, None)),
                  ("face value, single games count", edge_set(1, None))):
    S, Cs = sccs(E), simple_cycles(E)
    line = (f"{label}: {len(E)} edges, SCCs>1: {len(S)}, "
            f"cycles of ANY length: {len(Cs)}")
    if Cs:
        lens = pd.Series([len(c) for c in Cs]).value_counts().sort_index()
        line += "  (" + ", ".join(f"{v} of length {k}" for k, v in
                                   lens.items()) + ")"
    print(line)
    if S:
        for comp in S:
            print("   tangle:", ", ".join(
                f"#{P['rows'][i]['rank']}" for i in sorted(comp)))

# every face-value cycle must cross a single-game edge (the 2+ graph is
# acyclic), so test whether 15 cycles is more than coin-flipped single
# games would manufacture: keep multi-game edges fixed, re-flip the
# single-game ones
fixed = edge_set(2, None)
singles = [(i, j) for i in range(12) for j in range(i + 1, 12)
           if Nm[i, j] == 1]
obs = len(simple_cycles(edge_set(1, None)))
counts = []
for _ in range(400):
    E = set(fixed)
    for (i, j) in singles:
        E.add((i, j) if rng.random() < 0.5 else (j, i))
    counts.append(len(simple_cycles(E)))
counts = np.array(counts)
print(f"\npermutation null (400 shuffles of the {len(singles)} single-game "
      f"edges): median {int(np.median(counts))} cycles, "
      f"P(>= observed {obs}) = {float((counts >= obs).mean()):.2f}")

pop3 = np.zeros((3, 3)); pop3n = np.zeros((3, 3))
for g in P["h2h"]:
    a, b, w = g["seat0"], g["seat1"], g["winner"]
    if a in idx and b in idx and w:
        pa, pb = POP[f"#{P['rows'][idx[a]]['rank']} {a}"] - 1, \
                 POP[f"#{P['rows'][idx[b]]['rank']} {b}"] - 1
        if pa != pb:
            pop3n[pa][pb] += 1; pop3n[pb][pa] += 1
            if w == a:
                pop3[pa][pb] += 1
            else:
                pop3[pb][pa] += 1
print("\npopulation vs population (row wins-losses, exact binomial p):")
names3 = [PNAME[p] for p in (1, 2, 3)]
for i in range(3):
    for j in range(i + 1, 3):
        if pop3n[i][j]:
            wi, wj = int(pop3[i][j]), int(pop3[j][i])
            lead = i if wi >= wj else j
            print(f"  {names3[lead]:<22} over {names3[j if lead == i else i]:<22} "
                  f"{max(wi, wj)}-{min(wi, wj)}  p={binom_p(wi, wi + wj):.3f}")

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
ax = axes[0]
xpos = {1: 0, 2: 1, 3: 2}
for r in P["rows"]:
    lab = f"#{r['rank']} {r['team']}"
    pop = POP[lab]
    ax.scatter(xpos[pop] + (r["rank"] % 3 - 1) * 0.10, r["rank"],
               color=PCOLOR[pop], s=70, zorder=3)
    ax.annotate(f" #{r['rank']}", (xpos[pop] + (r["rank"] % 3 - 1) * 0.10,
                r["rank"]), fontsize=7.5, va="center")
ax.set_xticks([0, 1, 2], [PNAME[1], PNAME[2], PNAME[3]], fontsize=8.5)
ax.set_ylim(13, 0)
ax.set_ylabel("leaderboard rank")
ax.set_title("the ladder's order: live five on top")

ax = axes[1]
matchups = [("clone clade", "live singleton", 10, 4, 2, 1),
            ("clone clade", "public-family pair", 8, 4, 2, 3),
            ("live singleton", "public-family pair", 10, 3, 1, 3)]
for k, (wname, lname, w, l, wp, lp) in enumerate(matchups):
    y = len(matchups) - 1 - k
    ax.barh(y, w, color=PCOLOR[wp], height=0.56)
    ax.barh(y, l, left=w, color=PCOLOR[lp], height=0.56, alpha=0.45)
    p = binom_p(w, w + l)
    ax.annotate(f" {wname} {w}-{l} {lname}   p={p:.2f}"
                + ("  *" if p <= 0.10 else ""),
                (0.3, y), va="center", fontsize=8.6, color="white"
                if w >= 8 else "#333")
ax.set_yticks([])
ax.set_xlabel("head-to-head games (winner's share solid, loser's faded)")
ax.set_title("the duels' answer: clade on top of both")
plt.suptitle("The inversion: ranked below, winning above", fontsize=11)
plt.tight_layout(); plt.show()

gl = P["golive"]
young = sum(1 for v in gl.values()
            if v["first_seen"] and v["first_seen"] >= "2026-08-22"
            and POP[f"#{v['rank']} {v['team']}"] == 2)
print(f"context: {young} of the clade's 5 submissions played their first "
      f"game on Aug 22 or later; a rating that young is still climbing by "
      f"the number one's own convergence table")

import matplotlib.animation as manim
from IPython.display import HTML

games_t = [g for g in sorted(P["h2h"], key=lambda g: (g["date"] or "",
                                                       int(g["eid"])))
           if g["winner"]]
rank_of = {r["team"]: r["rank"] for r in P["rows"]}
node_pos = {}
for k, t in enumerate(teams12):
    ang = np.pi / 2 - 2 * np.pi * k / len(teams12)
    node_pos[t] = (np.cos(ang), np.sin(ang))


def bezier(p0, p1, bend=0.22, npts=36):
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    d = (p1[0] - p0[0], p1[1] - p0[1])
    nrm = np.hypot(*d) or 1.0
    ctrl = (mid[0] - d[1] / nrm * bend, mid[1] + d[0] / nrm * bend)
    ts = np.linspace(0, 1, npts)
    return ((1 - ts) ** 2 * p0[0] + 2 * (1 - ts) * ts * ctrl[0] + ts ** 2 * p1[0],
            (1 - ts) ** 2 * p0[1] + 2 * (1 - ts) * ts * ctrl[1] + ts ** 2 * p1[1])


INTRO, PER, HOLD, FPS = 14, 3, 46, 16


def ease(t):
    return 1 - (1 - t) ** 3


def render_tournament(ax, upto):
    """Draw the tournament with `upto` games shown (fractional = growing arc)."""
    ax.clear()
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.42, 1.58)
    ax.set_aspect("equal"); ax.axis("off")
    wins_now = {t: 0 for t in teams12}
    last_date = None
    for gi, g in enumerate(games_t[:int(np.ceil(upto))]):
        frac = ease(max(0.0, min(1.0, upto - gi)))
        if frac <= 0:
            continue
        w = g["winner"]
        l = g["seat1"] if w == g["seat0"] else g["seat0"]
        bx, by = bezier(node_pos[w], node_pos[l])
        m = max(2, int(frac * len(bx)))
        col = PCOLOR[POP[f"#{rank_of[w]} {w}"]]
        ax.plot(bx[:m], by[:m], color=col, alpha=0.30, lw=1.7, zorder=1)
        if frac >= 1.0:
            wins_now[w] += 1
            last_date = g["date"] or last_date
            ax.annotate("", xy=(bx[-1], by[-1]), xytext=(bx[-4], by[-4]),
                        arrowprops=dict(arrowstyle="->", color=col,
                                        alpha=0.55, lw=1.3), zorder=2)
    for t in teams12:
        lab = f"#{rank_of[t]} {t}"
        x, y = node_pos[t]
        ax.scatter([x], [y], s=130 + 34 * wins_now[t],
                   color=PCOLOR[POP[lab]], zorder=3,
                   edgecolor="white", linewidth=1.2)
        ax.annotate(f"#{rank_of[t]} {shown(t)[:12]}", (x * 1.22, y * 1.22),
                    ha="center", va="center", fontsize=7.6, zorder=4)
    done = int(min(upto, len(games_t)))
    ax.set_title(f"the top-12 tournament, game {done} of {len(games_t)}"
                 + (f"   ({last_date})" if last_date else ""), fontsize=10)


figA, axA = plt.subplots(figsize=(6.6, 6.6))
TOTAL = INTRO + PER * len(games_t) + HOLD


def _frame(f):
    upto = 0.0 if f < INTRO else (f - INTRO) / PER
    render_tournament(axA, upto)
    return []


anim = manim.FuncAnimation(figA, _frame, frames=TOTAL, interval=1000 / FPS)
html = None
try:
    html = anim.to_html5_video()
except Exception as exc:
    print("mp4 writer unavailable, falling back to jshtml:", exc)
    try:
        html = anim.to_jshtml(fps=FPS)
    except Exception as exc2:
        print("animation unavailable:", exc2)
plt.close(figA)
HTML(html) if html else None

fig, ax = plt.subplots(figsize=(6.8, 6.8))
render_tournament(ax, len(games_t))
ax.set_title("the finished tournament: all 80 games, arcs from winner to loser",
             fontsize=10)
plt.tight_layout(); plt.show()

from collections import defaultdict
pair_games = defaultdict(list)
for g in sorted(P["h2h"], key=lambda g: (g["date"] or "", g["eid"])):
    if g["winner"]:
        key = tuple(sorted((g["seat0"], g["seat1"])))
        pair_games[key].append(g)
big = sorted(pair_games.items(), key=lambda kv: -len(kv[1]))[:4]
fig, axes = plt.subplots(len(big), 1, figsize=(8.6, 0.85 * len(big) + 1.4))
for ax, (pair, games) in zip(np.atleast_1d(axes), big):
    a, b = pair
    for k, g in enumerate(games):
        won_a = g["winner"] == a
        ax.add_patch(plt.Rectangle((k, 0), 0.92, 1,
                     color="#2f6fb2" if won_a else "#c2571f"))
        margin = abs(g["bank0"] - g["bank1"])
        ax.text(k + 0.46, 0.5, f"{margin/1000:.0f}k", ha="center",
                va="center", fontsize=7, color="white")
    ax.set_xlim(0, max(len(games), 8)); ax.set_ylim(0, 1)
    ax.set_yticks([]); ax.set_xticks([])
    ax.grid(False)
    ax.set_title(f"{shown(a)} (blue) vs {shown(b)} (orange), in time order, "
                 f"label = margin", fontsize=8, loc="left")
plt.tight_layout(); plt.show()

h = P["hinge"]
goods = ["TOMATO", "CARROT", "EGG", "MELON"]
vals = [h["beyond_knee_pct"][g] for g in goods]
fig, ax = plt.subplots(figsize=(6.8, 3.8))
bars = ax.bar(goods, vals, color=["#2f6fb2", "#2f6fb2", "#2f6fb2", "#9aa1a8"],
              width=0.5)
for g, b in zip(goods, bars):
    ax.annotate(f"{h['beyond_knee_pct'][g]:.1f} %\nmax {h['max_price'][g]} "
                f"(base {h['base'][g]})",
                (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=8.5)
ax.set_ylabel("% of turns beyond the knee")
ax.set_ylim(0, 14.5)
ax.set_title(f"The shortage is ambient at the top ({h['episodes']} episodes)")
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
order = {"TOMATO": 0, "EGG": 1, "CARROT": 2}
for g, ax in ((g, axes[i]) for g, i in order.items()):
    sellers = P["hinge"]["sellers"][g]
    names = list(sellers)[:4][::-1]
    ax.barh([shown(n) for n in names], [sellers[n] for n in names],
            color="#2f6fb2", height=0.55)
    ax.set_title(f"{g.title()} units sold, by team", fontsize=9)
axes[0].set_xlabel("units across the crawled games")
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 2, figsize=(11.4, 3.9))
bd = P["hinge_by_day_band"]
days = list(bd)
GCOL = {"TOMATO": "#2f6fb2", "CARROT": "#c2571f", "EGG": "#7b5bb5",
        "MELON": "#9aa1a8"}
for g in ("TOMATO", "CARROT", "EGG", "MELON"):
    axes[0].plot(range(len(days)), [bd[d][g] for d in days], "-o", ms=4,
                 color=GCOL[g], lw=2, label=g.title())
axes[0].set_xticks(range(len(days)), [d[5:] for d in days], fontsize=8)
axes[0].axvspan(1.5, 1.55, color="#f3f4f5")
axes[0].set_ylabel("% of turns beyond the knee")
axes[0].set_title("my band, day by day (no games Aug 19-20)")
axes[0].legend(frameon=False, fontsize=8)
mono = P["mono_by_day"]
mdays = list(mono)
axes[1].plot(range(len(mdays)), [mono[d]["top_share"] for d in mdays], "-o",
             color="#c2571f", lw=2)
for i, d in enumerate(mdays):
    axes[1].annotate(f"{mono[d]['top_share']:.0f} %  (n={mono[d]['games']})",
                     (i, mono[d]["top_share"]), xytext=(0, 7),
                     textcoords="offset points", ha="center", fontsize=8)
axes[1].set_xticks(range(len(mdays)), [d[5:] for d in mdays], fontsize=8)
axes[1].set_xlim(-0.35, len(mdays) - 0.6)
axes[1].set_ylim(0, 100)
axes[1].set_ylabel("% of my opponents sharing ONE opening")
axes[1].set_title("the monoculture in my band, day by day")
plt.tight_layout(); plt.show()

mb = P["hinge"]["median_banks"]
teams = sorted(mb, key=mb.get)
fig, ax = plt.subplots(figsize=(7.0, 4.6))
labs = []
for t in teams:
    lab = next((f"#{r['rank']} {r['team']}" for r in P["rows"] if r["team"] == t), t)
    labs.append(lab)
colors = [PCOLOR.get(POP.get(l, 0), "#9aa1a8") for l in labs]
ax.barh([shown(l) for l in labs], [mb[t] for t in teams], color=colors, height=0.62)
ax.set_xlabel("median final bank in the crawled games")
ax.set_title("Bank levels of the current top-12 (a level, not a calibrated delta)")
plt.tight_layout(); plt.show()

mine = P["mine"]
top5 = [r for r in P["rows"] if r["rank"] <= 5]
bw_by = {P["boardwork"][k]["team"]: P["boardwork"][k] for k in P["boardwork"]}


def hinge_units(sells):
    return sum(sells.get(g, 0) for g in ("CARROT", "TOMATO", "EGG"))


metrics = [
    ("band agreement (identity)", lambda r: r["band_within_agree"],
     lambda m: m["band_within_agree"], "lower = more alive"),
    ("plan agreement d4-14", lambda r: r["plan_agree"]["d4_14"],
     lambda m: m["plan_agree"]["d4_14"], "lower = more alive"),
    ("work share of unit-turns", lambda r: bw_by[r["team"]]["util"]["work"],
     lambda m: m["util"]["work"], "higher = less walking"),
    ("WATER actions per game",
     lambda r: bw_by[r["team"]]["water"]["per_episode"],
     lambda m: m["water_per_episode"], ""),
    ("hinge-good units sold per game",
     lambda r: hinge_units(r["economics"]["sell"]),
     lambda m: hinge_units(m["sells"]), "carrot + tomato + egg"),
    ("median bank", lambda r: P["hinge"]["median_banks"].get(r["team"], np.nan),
     lambda m: m["median_bank"], ""),
]

fig, axes = plt.subplots(len(metrics), 1, figsize=(8.8, 1.02 * len(metrics)),
                         sharex=False)
for ax, (name, f_top, f_me, note) in zip(axes, metrics):
    vals = [f_top(r) for r in P["rows"]]
    v5 = [f_top(r) for r in top5]
    a, b = np.nanmin(vals + [f_me(m) for m in mine]), \
        np.nanmax(vals + [f_me(m) for m in mine])
    span = (b - a) or 1.0

    def nz(v):
        return (v - a) / span
    ax.axhline(0, color="#e3e5e7", lw=6, zorder=0)
    for r in P["rows"]:
        lab = f"#{r['rank']} {r['team']}"
        ax.scatter(nz(f_top(r)), 0, color=PCOLOR[POP[lab]], s=34, zorder=2,
                   alpha=0.85)
    for m, mk in zip(mine, ("*", "D")):
        v = f_me(m)
        ax.scatter(nz(v), 0, color="#0F172A", s=150 if mk == "*" else 70,
                   marker=mk, zorder=3)
        ax.annotate(f"{v:,.2f}".rstrip("0").rstrip("."), (nz(v), 0),
                    xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=7.4)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(-0.05, 1.05)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f"{name}" + (f"   ({note})" if note else ""), fontsize=8.6,
                 loc="left", pad=2)
axes[-1].annotate("top-12 dots colored by population; my sub A = star, "
                  "my sub B = diamond; each row on its own min-max scale",
                  (0, -0.9), fontsize=7.6, color="#666")
plt.suptitle("You are here: my live pair against the top-12, metric by metric",
             fontsize=10.5)
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(figsize=(7.2, 4.6))
placed = []
for r in P["rows"]:
    lab = f"#{r['rank']} {r['team']}"
    pop = POP[lab]
    x, y = r["plan_agree"]["d4_14"], r["band_within_agree"]
    ax.scatter(x, y, color=PCOLOR[pop], s=48, zorder=3, alpha=0.9)
for m, mk, lab in zip(P["mine"], ("*", "D"), ("my sub A", "my sub B")):
    x, y = m["plan_agree"]["d4_14"], m["band_within_agree"]
    ax.scatter(x, y, color="#0F172A", s=190 if mk == "*" else 90, marker=mk,
               zorder=4)
    ax.annotate(f"  {lab}", (x, y), fontsize=8.6, va="center", weight="bold")
for pop in (1, 2, 3):
    ax.scatter([], [], color=PCOLOR[pop], label=PNAME[pop])
ax.scatter([], [], color="#0F172A", marker="*", s=120, label="me")
ax.set_xlabel("plan-channel agreement, days 4-14")
ax.set_ylabel("day-anchor band agreement, within submission")
ax.set_title("The live-against-script map, with me on it")
ax.legend(frameon=False, loc="upper left", fontsize=8)
plt.tight_layout(); plt.show()

S2 = P["mine_stripes"]
heights = [max(0.55, s["n"] / 24) for s in S2]
fig, axes = plt.subplots(len(S2), 1, figsize=(11, sum(heights) + 1.7),
                         gridspec_kw={"height_ratios": heights})
for ax, s in zip(np.atleast_1d(axes), S2):
    plan = unpack(s["plan_rows_hex"])
    mkt = unpack(s["market_rows_hex"])
    cat = np.where(plan == 1, 2, np.where(mkt == 1, 1, 0))
    ax.imshow(cat, aspect="auto", cmap=XCMAP, vmin=0, vmax=2,
              interpolation="nearest")
    ax.set_title(f"{s['label']}  (n={s['n']}, twelve recent episodes, same "
                 "instrument as every panel above)", fontsize=8, loc="left")
    ax.set_yticks([]); ax.grid(False)
    if s is not S2[-1]:
        ax.set_xticks([])
axes[-1].set_xlabel("turn (24 turns = one in-game day)")
fig.legend(handles=[
    Patch(facecolor=SAME, edgecolor="0.6", label="matches its own mode"),
    Patch(facecolor=MUT, label="market channel differs"),
    Patch(facecolor=PLAN, label="plan (farmer/hands) differs")],
    fontsize=10, loc="upper center", ncol=3, frameon=False,
    bbox_to_anchor=(0.5, 0.995))
plt.tight_layout(rect=(0, 0, 1, 0.93)); plt.show()

L = P["ladder"]
sc = np.array([a for a, b in L["pairs"]])
nv = np.array([b for a, b in L["pairs"]])
cut = L["bounds"][1]

fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3),
                         gridspec_kw={"width_ratios": [2.1, 1]})
ax = axes[0]
ax.scatter(sc, nv, s=8, alpha=0.25, color="#2f6fb2", edgecolor="none")
order = np.argsort(sc)
w = 151
roll = np.convolve(nv[order], np.ones(w) / w, mode="valid")
ax.plot(sc[order][w // 2: w // 2 + len(roll)], roll, color="#0F172A", lw=2,
        label=f"rolling mean ({w} subs)")
ax.axvline(cut, color="#c2571f", lw=2, linestyle=(0, (4, 2)))
ax.annotate(f"  derived cut: {cut:.0f}", (cut, 0.93), color="#c2571f",
            fontsize=9)
ax.set_xlabel("ladder score")
ax.set_ylabel("navy share (plan differs from own mode)")
ax.set_title(f"{L['n_subs']:,} submissions: the texture only breaks once")
ax.legend(frameon=False, fontsize=8)
ax = axes[1]
ks = [2, 3, 4, 5]
ax.bar([str(k) for k in ks], [L["elbow"][str(k)]["explained"] for k in ks],
       color=["#2f6fb2" if k == L["k"] else "#c9ced3" for k in ks], width=0.55)
for k in ks:
    e = L["elbow"][str(k)]
    ax.annotate(f"{e['explained']:.2f}", (str(k), e["explained"]),
                ha="center", va="bottom", fontsize=8)
ax.set_xlabel("number of bands k")
ax.set_ylabel("variance of navy share explained")
ax.set_title("the elbow picks k=2; extra cuts buy almost nothing")
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 2, figsize=(11.4, 3.9))
BCOL = ["#c2571f", "#2f6fb2"]
for ax, b, col in zip(axes, L["bands"], BCOL):
    pn = np.array(b["per_turn_navy"])
    pa = np.array(b["per_turn_amber"])
    ax.fill_between(range(718), 0, pn, color=PLAN, alpha=0.85,
                    label="plan differs")
    ax.fill_between(range(718), pn, pn + pa, color=MUT, alpha=0.9,
                    label="market only")
    ax.set_ylim(0, 0.62)
    ax.set_xlabel("turn")
    ax.set_title(f"score {b['lo']:.0f}-{min(b['hi'], 3300):.0f}: "
                 f"{b['n_subs']} subs, mean navy {b['mean']['navy']:.0%}",
                 fontsize=9)
axes[0].set_ylabel("mean share of episodes differing")
axes[0].legend(frameon=False, fontsize=8)
plt.suptitle("The average texture of each derived band, across the season",
             fontsize=10.5)
plt.tight_layout(); plt.show()

ths = L["tail"]["thresholds"]
means, medians, p90s, ns = [], [], [], []
for th in ths:
    m = sc >= th
    means.append(nv[m].mean()); medians.append(np.median(nv[m]))
    p90s.append(np.percentile(nv[m], 90)); ns.append(int(m.sum()))
x = range(len(ths))
fig, ax = plt.subplots(figsize=(7.6, 4.0))
ax.plot(x, means, "-o", color="#2f6fb2", lw=2, label="mean")
ax.plot(x, medians, "-o", color="#9aa1a8", lw=2, label="median")
ax.plot(x, p90s, "-o", color="#0F172A", lw=2, label="p90")
for i, (th, n) in enumerate(zip(ths, ns)):
    ax.annotate(f"n={n}", (i, p90s[i]), xytext=(0, 6),
                textcoords="offset points", ha="center", fontsize=7.5)
ax.set_xticks(list(x), [f">={t}" for t in ths], fontsize=8)
ax.set_xlabel("score threshold")
ax.set_ylabel("navy share")
ax.set_title("Aliveness by altitude: the median never moves, the tail rises")
ax.legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.show()

EX = [b["exemplar"] for b in L["bands"]]
heights = [max(0.55, e["n"] / 24) for e in EX]
fig, axes = plt.subplots(len(EX), 1, figsize=(11, sum(heights) + 1.7),
                         gridspec_kw={"height_ratios": heights})
for ax, e, b in zip(np.atleast_1d(axes), EX, L["bands"]):
    plan = unpack(e["stripes"]["plan"])
    mkt = unpack(e["stripes"]["mkt"])
    cat = np.where(plan == 1, 2, np.where((mkt == 1) & (plan == 0), 1, 0))
    ax.imshow(cat, aspect="auto", cmap=XCMAP, vmin=0, vmax=2,
              interpolation="nearest")
    ax.set_title(f"band {b['lo']:.0f}-{min(b['hi'], 3300):.0f} exemplar: "
                 f"{shown(e['team'])} @{e['score']:.0f} (n={e['n']}, closest "
                 "to the band's mean texture)", fontsize=8, loc="left")
    ax.set_yticks([]); ax.grid(False)
    if e is not EX[-1]:
        ax.set_xticks([])
axes[-1].set_xlabel("turn (24 turns = one in-game day)")
fig.legend(handles=[
    Patch(facecolor=SAME, edgecolor="0.6", label="matches its own mode"),
    Patch(facecolor=MUT, label="market channel differs"),
    Patch(facecolor=PLAN, label="plan (farmer/hands) differs")],
    fontsize=10, loc="upper center", ncol=3, frameon=False,
    bbox_to_anchor=(0.5, 0.995))
plt.tight_layout(rect=(0, 0, 1, 0.9)); plt.show()

lm = L["live_minority"]
print(f"the live minority at the top of this corpus: {lm['n_2700_navy25']} of "
      f"{lm['of_2700']} submissions at score>=2700 have navy>=0.25")
for name_, nv_ in lm["leaders"]:
    print(f"  {name_:<28} navy up to {nv_:.2f}")