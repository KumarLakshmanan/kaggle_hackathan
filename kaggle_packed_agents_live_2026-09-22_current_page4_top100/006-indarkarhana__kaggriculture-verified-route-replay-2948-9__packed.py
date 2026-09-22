"""E071 frozen THUNDER-route replayer with bounded weed-slip repair.

Base route: public ladder episode 90565430, team THUNDER THUNDER (adversarial
evidence from Kaggle replay data; not our invention). Our additions: verified
shifted-tape extraction, hand alignment, and a bounded weed-slip repair whose
mechanism follows Kaito Fukami's public v20 WEED-recovery transaction.
"""

import base64
import json
import zlib

_TAPE_ENCODED = (
    'c-rk<U2hxNmHaCMKhJ|n(XyR4#b#n58q1L6C9(ryFu-OJAjm$<?%N{&J(e{RyV-'
    'S5)%m#1mh7kD&?0%i`<^;=s($|e7yte1Z~y$;Z!iAv!_O~1on2qQxc%{m7k~ftfBx%#@7}umpMU=P+duyHe|P`)^NSDXSKGV4&|m'
    '%W^Iv~C`*{A-*~N=5-}UZt_vJrp@GsXNw%bpmf4kmp-{1Yq?!)%%=F5xMlYjYXdvW>k%Zt_iL!YiL-'
    '+z90GyL4E+uMKr_`|rP=kNaV`P1-'
    'cSEFwK{9?DgzPazf$IGjm5BD$kZyvrn9H;B;#l^4<E2|CrKN`1T{}<z7JHL4U%a^IT`TQ`(db=7!1e*8oO}IhBVY7ZeH9~e19zJ+'
    '7=cr76X4tmDN`Z@J^5(c5(-m@Y_HMf$?So$fJ;n`~z9hf<r_shcoPdW$-'
    'L1*5U;5>pk2m}6*nH33j(2C%F`l&T%UGV>Y_BFSA6qc^%fnW&@t+)r`!<cbvpu_Rwk7ZzgKtLTxc{~NtLw|p!hoV5LmOw`iTy8h8'
    'qeu+>Nl=n?Vw)42Hd|&Eto+c$P5>ZD?0p!=TF6W{=Vqc)iGG7sS&kTEII;ehjw}__Z(z#(W3Y4$6kE(k|B<tMGx-'
    '{n?882{j;gxg2TE0*Tdh>^=r@v@Dum1+`qs+KyI4k<Buy^{)BOXa6j_d2QDuzw(o9!`P265=KSLPKkrAkW8da(;q($rKJa+Ne(%z'
    'JUGneA?;j}mz&?x|%-'
    'fGYY)mx53lTj0(S|_;{<FsaC1z|^5@E3~@r284R|W1!{YTN=Bs7Y3kVA(tM8JykvIvgkKts%V7{m%vli)Ov7S&F~AYN4(45z_6gm'
    '5Cfz`&gQ0mXf_(=c2(;XC^T1jz;AM{P$whH*c3!_U*m@n84oj6W}XF6hktB7Y8N58tkjzT`O@ddexkshp_cV|0egL|{m@M~!uH$c'
    '(9UI38)024S6V;e*L|?(kJb7^h|or}^n%umS<(+Bh)s6IyU6d~@$;C(=1GGZvnof0nkhK_AYp{v-'
    'Ohoy1G6Ow;czOCn<Eo*f!65(W)^Ws;eTKfc>3jfz=D>+*4Gv-'
    '6BIOiEHHJ>&R<tbiYIr<?&b110c+&EMxnQ#<(P@%z#FMl);Y<+Ynw_^7Q&Ywkl*L}yU9hn#FPHcBpc`1lH~fugT&Cn(FVTMtj<^{'
    'e{@q};;L9cVRg;9n4mB~RgnhW$rHMBbnOxpO?_+rq{1e*vT_9?<Pe-VE?*U{LQH92ry8suWAHGK}>M@3$GnA0zyK78%=$n0(gg+a'
    '29mkEbOiZ0%5EfeBl0j;|(TJGka1vd41XHx88B@m-HBL>c0tZ3zwB2u^2ZbX+~3GhBft#PeL@wuBMeKXdyS3|?N|{de{9G0gjN-'
    '+rGj_Id~wuWzo-c7NPnUH$d$SKeC0to3a?YKAwtNx<tWW((gua48qUn-Ls>Ub#-'
    'SwV0ZicBI`<K*LAv^cFq&u1ig@8y0bR+alez=%_@RQXVh2i){4adknh=8#sHL2IUR78FIOs`$1~1I9Tr$8XY+QiCMSrurMD(6E@_'
    'z*Lzjs_L-%f%~4M-R&+(PYYzvFM}<*`&By@i7(zLl9>Zi5BS|*T8t|t=+fTaKWY-ZE`EWX?dWLH(tlq-UAS08Wi)(Nz8`Iw$LS;u'
    'a|DhsR43q0h%kkt(O>%-'
    'B?R|{@fIN)6rON1zNT#H4PiHY&vutyQxh4@Ls)uAL^AZ|#JF>DTPxur2v*m4trI(EfUIdqoht?}^=nTU<I{@5-'
    '^(=6P`1ICUj&c|}uac@7=BbLRtzq?SPGJLGIMDsg5!QItfpBwZJhf|>g@gb^&*Fl(Zba9ZMj}u<CVZC!s|v*uCWUC8d*c2T31_s-'
    '`@>51T?iXAt&(&T7BtwpWIoUokJgjx&MPh}I*ICv+PO)HO1WTr-'
    '+IX!51(wL5b!zSzUzqbJwKJC0YrUbJX9z5Q6@BxPd=aY1lwKU=5L5<L`IE18=ODVNPr<qc1pAZ!|nFvx?s3Uf5A^DT)l472~S7=^'
    'waspU-n9V{_AldN3#->ABG-O;6B{G!%w-'
    'C#_b+F=h4F!U89>f`x4PQat_I7tktffL<7V29XI?kRCI6^Yh5BlQg*j2gAf}Sd9L~Eg{-y5iizAo2ik<=yWyFYEwyTR;)5h_2-'
    'lL!T+`vhifAiB9DdM<f>6m5ujE!!#jSWhATVsh>WR*97LCZ@cU=p{Xi%>EHjhFs>vVSBT>pLJAy6sP452eo5)l`%w}6IJCs~W=IN'
    'ks7*GhzlQY!q}{r9%kJ!%6~W~^Nf=te&TZ4lgDL2>g%7d0Sz<X6*i&QX4}8C>1d^WKa(dm}aMeEj5!q}GJ(w$g>v{leWjarv-'
    '>ye3Y*PQ_m8K!nu+BGFj5QKXjH5sg`twVqiK$CX*lVbt*~$nfFvbGH&fU7*_-xK`6tm3j5^Ie`TkY_~hWi-vns?g&L_r%r`x@{ot'
    'LJaOyRju>@)`E;}mx95&-Nax<nj<-#OYs4CKVaK*)pVebO{7BL>aP(C72`{e3`iGmFhOKSSiBxCSxAB}6o)-'
    'cQX>DFRCxGQA@$kOCy8NWqceL7ka9Pa`zlW{~HVX=N$?SBR5}Q9{#%BA8*}t03CYzA;#y=q^wH+ZCz<uw63+tp{LWV+AnT}{>UEY'
    'yrFq6N@`{iV}xOnIr`D`(X9m6v6!`}yS(c9}CWgV<(Oz-dM?o)DXsCAbf^rmpA^X`Bi&TAXQ85NYSPb!J86w1PXAXP%PS#MjO*%0'
    'HC1l@M*@i%>cZT@{=1lqiMn{1XZrjTgAo5uTV^L^NRimai8ok@Z#A{--'
    'cD_S+kDS2{+Y8ljKupG>4XOpI_mM`HL!adVEw|YPS(9tY7)k2w!qkg6n_^1)G%|xfCV2Blu)l!iWn;TID<g!cW>NU_qaXL4Z`?~e'
    'MY~yF4gz9n*>;-'
    '2{1p&L<ryE5~N&Z0P3>9(tOnRTKe?a+ko(l@3homh}#9eMrGMiDMCNs67VcNiTF0AJ`7a+MLu&|}mzD}izV5yLqV%J6z{+RP3bBJ'
    'R__I(4M_p?y8^RM)HudxH{<k^)X<HXi%MO^~wox3NlLkucQ5M-'
    'l50QBIQlmNBh&WsjX_wRISucBV_6jmwWYwCDk(hFgM8Y7qLQpu(hYWzDc&!cQSw}wEU%~g-'
    'PmLR4!5C$>RF}9YJ7Etp#@Bz?hl1cQbm9e!!1~b4ZAjG-'
    'D4zod=krQs{Nof#3TO1Q3$Yx7<iA9UrCs$de7pGZR<weX=I9H><O66P~1C?^H*nBIq!W#jMB`t)nL3VajLjeq&L^i7}qBoC0+pwo'
    'ZF@O#e*14!PiiQ{|FO6~1#&z)oh&IS*v^SGtW(OE#8g{e7V~$V4ls*O#U*Hq&L?CneXibnG1ON>#Ood3d7$(IvF)}~jEk6EUg#`s'
    'JJd~f;&z0n}jKDHbDm;0ZC=ux9)~hQzfP-'
    'k;iA;bd>{=tgjt11spfhvQc#*a!xF(0v<UYYOhe=_6k6c?Q24^baky+_QJCDZaR0p?{CbPJGVjLt7&B!{_YBrR4|0Obe9t|7coE&'
    '3AF&%B2U6W3M%Z7S2z46RlmiRy(o}IQ)V7@XkhW_p2InuIIfKF?ifAgTfltiJ+Sf`7(@FH+MJzIJ#A$_hm3PZ@`wrR9tMwDFic&b'
    'fknTZ%}MY@$2P%v|)DDi?04US6eI$1`ebSEuPS4yy|+UFRVhR3!9cJzc(wwl(@k)aS+cjv5ZI}Ru{JESv4Z*WQH=@L|R=1;iS!y0'
    'O0y$@>P&!(qc+T1Y3EZOu9@siIvpmQRf$3e|Rx&@9L4I%JWuDCCo?&u%o+pVajE6pRaFnxjWS4qJmu2G72*#v+(U4>|ZUKiczl%6'
    '*NiK9lA=mAt%AV6qFs8r06%GbgJIDz~JVKh4ww|J2GOkgvpK*CP!kLrsW*Z%UGb4<0lFTcAgv$(AGeE-'
    'q!`F=4t9HsXAYOl^Ll=AH*_UkF+t=o?*T3(sLcW1`!=t7foD9Y+P2){HxTARjS8a0?L{E{hBFO+KF-'
    '#0N_AQ6#^$!Xx$FME$73ps4>HzlRJMl#@=F@x`>^G4j~f;*?!dBMH@;h9s(l28M59(uBE5_{=N%8L{#xNzO#2U}4HCSfzpsO1uOK'
    '3>0GBBR8lX=QDl+FZMwU~gnnVG<j83waL{=$3$Tl#XXCu{E)CwtdbMl6FN|c_>|AOQ5DNK6Vs|o6ZyV0a8IlmOdpc+a0%9cIyhV@'
    '5?E-*vxDwItwQH#JL3UbE9e7SpRs+|FK>kpa+Yg(S?(CwC5}soq+*C6kR88J^`)->C!V|RUA(K@85E;BFoth-6$EuvLmA}Vy(-'
    '<=^Q)V8fFA2@JT)z83gV(v&CU?*yA%vC<WRw$SgAB3L3|F&KGm~#BFN+nN!;Wc3Fru+j<gA3U=@^wU$NZ3qB5|6UE+>@W816D3}s'
    '8x`K?5jLs`8t_%Usz#14jwZ0lhhr4#eLk4m<!9(Q6x6PqxH#)$m!a8i%e9H<&l(7;wd&j4G?9E2Y00e@+n$B@{QHwXluZHrnz4I1'
    'v$qJTHWoHsvhGIj@n_MK_Xx}l8$5omgR2yStwVEVPjLx)NG);Zg&NC_C*t)B7iR^cz-'
    '5kgUXn3I67v0gLh8lL%HrNCaT9RI)_id&!@m(tEg9sIPts7{N9B?O^2gHM~I6$D6bGO6Pbft|8w(A(=Fm}{*+^S)6*)Mpf$?gRvF'
    '1pp&0TCp$n2(-0{5+}@h;_M0vgMX8-4e2=3WwueG+XQmA~Iv#m)oyo(P3jL#KQm-'
    'f}bs(jbfd*%`H_m=q`a72R@5mLKEobMt_KyM*gF!24HinY`PuEUJ}<uuR1iF5q_UhtCPj&dl~Z<p*m(;36e>)H=MqHgk9FCe}EyN'
    'jOfU!O*zC**LAT8afBpS0Zxi-3b3dq=Zti;tX`H_@06K=lY3vD?zJ9sx<-'
    'R>+NOfN)rEIYmH}fuFOgjweXBy~Ie;o@?o!o>*{omm26q;-'
    'sT0w3bmXa6$50wYLGSuo%fPEd3!ikCT*Uon7}7y<)H;bVQ>K~=6dmR{^DO_+CYQtWoKp|j3B(?`QslRlNhqK-'
    '2%(q97fP&}$~jLr21d3A;mbpcs2GDvecrMnuh#5q=Ls`Ka^w_J=EO;6om7lVL|((kf*Zwvc!OTd*CeSF;HFIZh=ilC<=%K6J>vvo'
    '7=+SL?8q6GxLg*7ekUmOdmDN1!C-9?NURR}N~ldH8!g_!)7t`06M{SNQ_rSl6>(=8RYWT4a=0^!T2<nln;$X_E;6d+-'
    'as_uK=XE3bN39riI&UxAt=60`bnreILJM%%cY$u4#o3birv&~e!pIz=V~jMMi)PJt6LU~!UzhPni_kGC@o07M{X^mxh#3&ss<`&`'
    '+(TE!I$H}SB80x`^&O`1xP@$Vo%?Rjs2<cfU^29{<=M{P7Dhp#iv%md?pz~R0<7-'
    'P=q`apUhPmNhnbW=70`Lr!q(#vdhO<pig;TX|X1mOO)7!^ss>>7h(2Pjtik4sSG<-xgMG=Hy8-'
    '93x)^<*{pQrM{(O)4F3s`=)D@lokRFXEeu!FF?^VU#(J_#&WTBvg9ceLJ9lsD=LK=5Qk3L99_(bp*)+8js?y-0z-'
    'C~Mk4~gi@A!Un0!JEh`5>xf?B39nC(|5*S|m(0L7w{nZ6_N;mg;3ssqh7>QauI4&6H&_1*;IbC?;Lir0U|2zH;)WRwpxglFJljVq'
    'NJx2lK^#ZV{;ZPIQ-'
    'S7Xd&oYiYNwq|4ZplEI%zmGp5@B#TDDGWzp~UB@LxSXR<0TSHRbF&V1<9#tNyB*~_?K|FJ`iVp;(Js5FqWgJ{WOs)6Y#adl?b?_~'
    '1-'
    '@8|^sP$bW5z~vWM~pKZloFDG=|ts&6sd4@ENYwhW>!h^)Oq(YzN714^a%om)Tx51ay=P}oPfr*MdOPzBx%OHlk3&x5%w;3;xcbR)'
    '>#oeR4Pj0B2`|FA&CbMCF7eal3w8Xh!7f1&fBRBVPeZbCYzmX2b`l#2IeLaSqm@lALrsH{5gc=Mi8!j0<lj#76wZxD9_uJr`ldze'
    '!SPG5;?u9rJD5cb*bXvr-nt!P1^4?^f7Iyz`LwrEo{^5RLUrNtFzHUgV$Av`U+BSP1y?wMvKQ-'
    '`^54PkD+fDHR1>W`KZ_ZihCdS^=6IerVTZ^ZvZiW5-'
    'e23#HiAZA?&mnxx{$!%#d)KTl3v6{D`+cq9Y}9ZAe>ZuHmgzbH^K`71M6#s_QM#a(8e6IDNK&fy()b+Fs)40%h0g#Fcm%Gum5@7}'
    '~z_7O0hZJb5elq^@e=G-'
    'b9DS#{;m9M#0BJ2hHpe(Tz;%*1Oa1d>jvwO*a#!4PRPM4`M}LlCA_ZfubnS&ozkkRYB#i?|n<PmfT6FGM)Z%vzK>3&(!+1N#=Z9o'
    'jtu-`27xaqbBU<ThHYMd%kK*2ivZ5O#?&)mqm9uagXH6>PQB`^_FzM*B129Gk{i(9YK2rbvNSp+-+PPnltf@Rs{M-'
    'bn|JO1=fgwwo=1T*TZc_8-'
    '0ZfFZwmzVdHR0acQVIs8tU5d!9`1(+f@T$0T12kca@4yL=H+SEVJb<DWU*5FyH(hsA`$sTH?AB&PlcMxA$t*+b3$W>GqLco0DUcq'
    '<GYT%>QEw?Ct!tIvPo-L80YJ*XS)Sp8~4|hgM>L0Cc*?)BDPBs-QxNgtV-'
    '7Bze*|HFm`^`Tqwtz^~_%Yy~Y8A9bv%)u1w*>WRkh)~!b}D?Vk<EE492p4#Jng!2HL8(nk3$M_!*f}%6hmA>Umd<(Bvr8<$>i`$0'
    'S91r+eDE_=d}rs6B2Qd`603q9Tz0xC^NwkqUV7ioe0A(zCekFttqS5$SkTDW`N<V{9U>}13GWe6GpC<Cj7NdF2&V8ry^|+cCiBIE'
    'w`KvcDECxdWvw<2Jde3y;6O#tUTF!UAc-'
    '##pI_m*~B{BpfbJeP)#1{1L@8p{ABfx36N5EpIL|X0;xY6C*sfl>@S$Fpk8&i#Z<U(hM9pFzB4x6A|PP=@^R`ZSEapbQvRVjZ!+t'
    ')*_u5x>G(i<?D69Z^x4OMl!A$PP5h93rB^z)=Tj|zC&~z&YM~o})1Z9Di3WgIk26O}bre5_R3iNpKss@pxjns$oQNqOeMP{>WJ7s'
    '|%FJ1Hktbf`r=3`q&>%b6sGj#23_taU$Bo60g9LcQ=|fj9=RxL^(R_nxb8w1{U6D*KwM;FdxTkOpC^|sXIXIOz>Je0Il*^!pqa#-'
    '(Js}&{0e0_Z8o$CN!cJG<^pn%Ez^%US7X9aXl+rQhll4|7k^A&=?2zDu$i-'
    '%Q{((z?UB*4ep4Qe$cA~*V&``*B>&5I~get2?lX;kF1$c7bh=UTeAKI$UP*wme&8g@<gj#9Z>A*IU*)zSCCwp4#UR&H#ypE|@r>n'
    'SoYii^6B_OYz_mQZu>Pyw+d31UD=FsY;89*~Vu&u;mH7KJBSp9Y$$7tCq2m+{$0az``Vmi=6t)6pH2Gp_;5@9k&d$|a6YM(}A?^&'
    '+3ucqB(g^SX%IGV{dml@>5Dw4#R$qbuL6q&PD&cbc(J+C>ohZz@_N_4O_w>h0n0SBUpvtP0*Q!yN8(G&Sc0uNIkAE%YDERLq<d<C'
    'YU+es?tg}oEgyAbm*1Nsn0&Pye>rwC@OT;=$U!`|+B++H1RC%(dok`Bo?tGqT-0yHvD7|*0Hxrj-Kryt;8;x9+OV6ge*I14DDmdo'
    'ssUYpVEN-'
    'c><^1j2oVCra!X414CSG?p&2o4=?8mO6e)(bo$Tf*?`gF!qx8x(2x1>aWY^+|Bca2|p<?G82b%pMFcnOjgz=vB#qm;#9eM6Oq|l{'
    '(7eK0;|H%S9!hKNcy=SVhpr&249obw?GhWMqCEkM+7<%ww`nAGNkWqR`}J+pJUhI(nUVPFRu2x^DXJ6HH&M%X-'
    'M&)C3BbYO$^$NRq_CZo6=obv^zi^&egtv_78dVJ9tW%Mys8I_x{O?A*qoGI71I)Z}NJdt!>KmrHz(b-5ms4;S#N-'
    'UmEP`pV`w>eS(suefTsVw-'
    'O<${#i3A=rtx%99vBjQ~VRlpVDcLMZ#`cOG62$v?P(IE4txOq={SQgSHeIU<Kanj$6J)|q$P2t=H!8)lV-'
    'X1sK?!e<!THTHo=G1sqlnR(SZPAy*M0&2~hb$Zjk=u=d_ei`#Xp8$`m=L(T6+VXs5s3~(Jaw^<uM9=ezZaO4KH`1vq3XFEBG}pD@'
    'eO`~p_9_qc%N^lXIFU0uS5{c#0w5M*Anxe1y6n1?aYaqQar*-%q3(NR56^Ga_F7x1IbF|`e>Vj+aSsaDU2o4AbihF9!0c0i2-88-'
    'a%Wc|#!sI-M=}j=v%W?3B@CRPf_RJxXK1f04Y6rtg?`}?+Z|D+Ts~z2w$M(1noZ6C*9E5pfy&r@B<{(CpOuL{-'
    'IgPgNSFlze#FNK6~%CBEPc9GkVn1#Q8q{r8}%NNb_)2X?QU5xQr+;iKoGG4B2+6PHrQuAuq9KlB{3A{C}>+@;|PWAz_-RIOztV;_'
    '#}vDPs04hR-'
    '2K9q5}lA^{d{F%W^lFMt$4@rlTP<W3J87y)wsUnK|OH6JV*R1zS416f0R0*qx9+j_)(M1Np=p1)Z<2@5Vs!Dj#UtJ$-'
    'mIIWTA4UafVs%X!#SE@l%}w1{^mFKI=uiIfFKR1J^eF74=(Y%W5X2x?Lp(mNm`D28&f$1tP77M)zIgEoT07<fB1>6bW-'
    '8o7Is_lm))YTh0Lch!1Afqlg))@c3~)!^+&6``MLDduoovZ5i0D^_M|3o<xhX7xRBECUs_gpOc>&JId9dugBIQ{g`47(+}}#k(G*'
    '#94JLq&le8`pSFpMgJ-xv%BB-!oVRJ+NiIYdS*%|-'
    'Ybz0Ohg)5);*1yYYM8<jqb1;sJgi^Or3a2#jn^(CnZ!8PNGj3m8@Qf4mae<TT^dV{2u5kYbg_IEM>=#em<{_>-'
    'T188YTIdi+S?;Y0D|XuD*T}E<cjeUhbX}^eSgK=uR&>IlZ0Fi9FKm-VWpGQC+5i3<sW;YW^)mSxN=Z(M`PxW5}uPRBqBOp~zEmN#'
    'CMXze&_C-'
    'd0!Xmd6X*!IO>`Y1Y_N!`rY8Xy#l(c3bUN1UR(9{nX*ThC__TmPbRMtCI||SQ|;mcu~4+ChPG%wyzZ7O92sQXMTW995YIQf!rc{p'
    '}7p^y%8sBBjpWgRsoH4-Z7{{<<qzj&eHdWr~x=8WsL!LEERV0=DAuKXmKjBM5WhVg-'
    'R8PpD8=UPSwrOEVn++tgTZiZbVSi*(ye`=R7uDB1#dCQqzep2}}mUX4=R2|1OIFNu9~vM7@Y2npQFO#R?`^SdaojLB1uRzsAL8_?'
    'FS_B$CtYp$-@})UA>1IL!)0Nk|UHV^jU{KoYuUP@POhsSkVm@p7a_k#oDaRq_plRdTykW?;);W}InJJ3d52WgcPJmzs+(5-'
    '*0W@sFO;+Iy11o3<P5q+c8FT^}0W+I=nR7L*%%i@UY1=oYzR4ql=Gu&wbPTl#8-mZCiQA@s!>y7ud0-~Q|N--%sijQ'
)

TAPE = json.loads(zlib.decompress(base64.b85decode(_TAPE_ENCODED)).decode("utf-8"))

_PASS = {"farmer": ["PASS"], "hands": [], "market": []}
_REPAIR_OPS = ("PLANT", "BUILD_PASTURE", "BUILD_COOP")
_REPLAY_STEPS = 8

_STATE = {0: {}, 1: {}}


def _copy_action(action):
    if not isinstance(action, dict):
        return dict(_PASS)
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _tape_action(step):
    if not TAPE:
        return dict(_PASS)
    return _copy_action(TAPE[min(max(step, 0), len(TAPE) - 1)])


def _align_hands(action, farm):
    expected = len(farm.get("hands") or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (farm.get("tiles") or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor(step, actor):
    trace = _tape_action(step)
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands") or []
    index = int(actor)
    return list(hands[index]) if index < len(hands) else ["PASS"]


def _repair(obs, action, step, farm):
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    game = _STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _STATE[seat] = game
    game["last_step"] = step
    active = game.setdefault("active", {})

    positions = [farm.get("farmer"), *list(farm.get("hands") or [])]
    unit_actions = [list(action.get("farmer") or ["PASS"])]
    unit_actions.extend(list(order or ["PASS"]) for order in (action.get("hands") or []))

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - int(transaction.get("start", step))
        if age == 1:
            unit_actions[index] = list(transaction.get("intended") or ["PASS"])
        elif 2 <= age <= 1 + _REPLAY_STEPS:
            unit_actions[index] = _trace_actor(step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in _REPAIR_OPS:
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return action


def agent(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    action = _tape_action(step)
    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    farms = list(obs.get("farms") or [])
    farm = farms[seat] if seat < len(farms) else {}
    action = _align_hands(action, farm)
    action = _repair(obs, action, step, farm)
    action = _align_hands(action, farm)
    return action
