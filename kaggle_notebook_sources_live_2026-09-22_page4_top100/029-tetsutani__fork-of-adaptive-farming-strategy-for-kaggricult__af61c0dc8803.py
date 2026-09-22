# Live strategy replay — rendered directly from a real 720-turn environment run.
# The input is hidden in the published view; the animation output stays visible.
from pathlib import Path
import contextlib
import hashlib
import html
import io
from IPython.display import HTML, display

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

TOP_REPLAY_AGENT_SHA256 = '3edde59d0a8475fc434185ab3922c303c5c48152d0f80e780658120ae344c161'
_TOP_AGENT_SOURCE = '"""Sparse adaptive farming controller for Kaggriculture.\n\nA complete season route coordinates production, labor, logistics, and planned\nmarket activity. Runtime feedback stays narrow: actor-local WEED recovery and\nordering only route-existing SELL slots by nonlinear price impact plus bounded\ncurrent Town demand. Ordinary SELL orders are not created, deleted, or resized.\n"""\nimport base64\nimport copy\nimport json\nimport math\nimport zlib\n\n\n_LEGACY_ACTIONS = json.loads(zlib.decompress(base64.b85decode(\n    (\n    \'c-\'\n    \'rk<%WhoP5&RdfXW@BJkL+maIwC@g0!d}y2!vrE4gv(u!pSbkzlRp*dAqv0y3e^oTG4Jq&D?w5r@Okk`qO{T{`S+azx@2`*&jZgeY\'\n    \'m*2J-eTs{r#tZ{`FrEe|Y%#%TK@l<L7@reExLy?($}M_+RbAw;zA_@#6jE_ZL@Zv$HqX>$BP1{Q36XFnl<ht+xMhI}C3h{=9xST-\'\n    \'=?_&PRX#ez>}RfAHrIH`i}JzPUU6!To<{N8P!6^QVs=4&J}(*r&7gaC`T;p}P;8&L8~juzipJdpIE8%Qme!e%<@)o4a?PpT7TOU%\'\n    \'2_H_QFlW)t7wx@$%~Jj}QO6`?#5+@D1ai$o;vxcr)zAPaD0>Pkx)JqZd8=$NRh8>^m>~?r`Bq?;HK%aA92B4L9D4-dw0-\'\n    \'xA`U<vTdKn?FH{-LpIv1=(+pOw5$XBru}ol_9@K1eZlUr{#fN_-M;7c`r~H2!BFY5?a#%2-\'\n    \'P)0An(Tx2`a{%bvUf+N9ilFit&CNV$(Dw!Y0|e30V6f)Qti3><?8;a_Fy{&eb*2hnLcZ1`?TR=ilw6r)Kn{H^da$FWWR;?)Z;>BS\'\n    \'KIZ~)$r!-$M1%lyUVM~zkF`5z35V=%VRTA_bF-ydBFCtO*Is}HEd`wI>}~lw|CD8+B~yzQ5F{U*Pnd-\'\n    \'$us)N@tJr#T>a*W9_*Ay2NOHA#^ro*pYj5CHb8vx_znv67Ar@Y@!^h#26lLUpFC^K<y*fU_P1lDq2T<7ZC6_8-\'\n    \'zB(>@z2dLg@^psQ0P2NVDRxMRT?<<BvOmuz*Q@}+757`3Ht#yEs)0-Oq(;nVFQ^vTR2L4*vZ5OR!0at6c1378UO$A+v-\'\n    \'(!bmtv|vh&fOZ|`m{*53{{H$R-\'\n    \'smc`3(^r8Eu*z0<Hnv1ga%G^4v2Q$^$6Uh~u0VuV6rRw*FZJa&U@Q5_KRpaZo>7D?7AH9fsbijbF*%1Phhyd2umsBjI{qiV1Z{IK\'\n    \'%nD1m}dZveFgjjn)ffVcJo{K~k8#%(`TCTpY5BW3!ESR+mnmk@|CXS=OU+?~2?s8k>lOAEQ&BlK&x@e9g{oCrjxcPJ80t16du8A_\'\n    \'}kT7w;LqUkH;v|n<Y^gb$172IsPcaF)%e`xz)bahdu?KFW@lnqOpFFcWh<m=fm6Zw6J#rgXm1jwciB<ai<zL;~ll$doW4Pw#J6tW\'\n    \'@`(L%Ouj-\'\n    \'!C`1)UDjDrTq0oe$#3l_Vlv8B{*a6GkzfE>&dm<xo^=GzVNsqJys`i`={64lX;4`GiD5RJ3i2Wu<r@5|kl^!TA|6OA9+1J-\'\n    \'d+krN=@30IuO1X^5i6-\'\n    \'DdGed#l%eHmDj(74*DNGF<srvw$2c~C(y*1>C@mvM0DketFUVD3ifPx?4S7Z4?X|0Ti?3<6@fMz4Vfo@aLeq=j^XVjFccK#w4uVC\'\n    \'dJCac721!uGI_!3!aL(A%5q55YPh_SN2#yuQBLoYde1UvAyMhl}U!S!~-\'\n    \'`v;n=ExS@+m5PFt&9JlYv94WfB%Kg*bb9T#6e=>1r_K!7y*~nZNJ*492fJB+Z(p4@|8%-\'\n    \')W2{=<p433v@na{gvPPbDksZN1z7DasI^N*K!C2A2CIkvMT`}eh;-q#utQa|;AbM~L4FHLym`G(m{W{#v<xTr%$ARRCKYR2+Yj-Q\'\n    \'AavHzw$&MS+^rre;u5zwQLl@_d`<NE-\'\n    \'e8_`ngfc`25aC8MG)>A1uw;KjHL1xr?jEW6;A;fg|N*lEr&s3970@ib|qe4eiF#!OF%B)#1$JT6R)=a~cgs9~#jI@o0t;zKuK~{I\'\n    \')g5m2xqOvFA$nHaQG8pUEID=ZgRQ@uz@zB^?Ao#6)FogbQY_n$*bB}fldhG6<Z!iA{FT*yN*|7YO`7VroEliFUnID$!7oZNNccN%\'\n    \'?oO?P6Fnk!c-uoy$J)#-*LV5<0xvylP24XyO6_i6?Y2o@x3*A?ee3AWiZO5o3kJfqJ;qkp2*amN-l9O9@-\'\n    \'5T@8urFpUs7a9Y5Im+939_tei-NdvXbvEWY2w9U?RL{F<NgR-\'\n    \'HHqn99jvig)G1`JzxA9^$Ry<{JXK%;yUuX#UBN6mR@TvyR=9G&%%>)+8GAR-9xomiln8Cd-DI#V(!>j)XBC~Z;UWSqoqrlYr`i=s\'\n    \'s-\'\n    \'09m<uUe|l=W0SoxtcLB1jK<=J<x51uWPW6PZc)FyN=bJjM~Z&L+68N7VO4Cp7WDzr6a>Zwd)G_%Z*+TK)6ph)9z~zi<p5ZqYM$AT\'\n    \'sVNXl7(D*8&+r<X^IebLMe(z5tD9G|^F(S+fz``r$>`fyh!IghW1Hd|+32Bco+Y4(~eVn&+7a#ylIBUOopk8TSjiuv{AQSi#Z={R\'\n    \'0rxsHD6Sy0>F@Bydl=Wn7v^xM=fhV|kzOAb<%+7AoCA$5-\'\n    \'$2J~1fBtB4k*nVHJA0oFfvkAp>NI9o|M8yk}Xu?R6L+l1E=fAVm>)<xW)op|_Y<`DJEl!EJh0?s^n|489xqLi>%pn5aiYo`t}O!6\'\n    \'W|zk1<>7xqNP&Q8Z<gD?SGY>q|NUzZa7bT7-~29gki?{0y^mN9YMw1Jqowi%WdBpv7^1g7|;-\'\n    \'O~{+Lf+89OAic7_dCVTt6^s@ugQf-BT7WK9$Bl*w*&Xh&N-X5g%D8HVa~P=`t~iSWrS2cpgK-{3%_S=o-\'\n    \'wdS<9!7iXboU=CP4SQgn>sGj2vk|Gf9>C2{m&+oju@nI)J&2Ma_0VFX2A#sJp2k4d@g&p{$TPa3vhAd&X`ISDGt%jcanyLA0x4lP\'\n    \'QC03}B?6aq9M9_oIRE0-\'\n    \'IASVop5*;hO(D?oBX4BDGS!w88ljF$GC!2R^ReXt{%>;3z?Kl3eeAf5<L;vc=PU)zSFbmgJ5h`+IPh+Ar<<vD-kPL+*Ys)Acg5w(\'\n    \'T^C{8#^*p!euB1pQy@Xo?_#?B2*kI5B7OfX%vF;E!|3XE3}@$QsR<H0T_MaS5;*B+P`Tw#ADtKI|+;6fIK@VxtR<!2@FM4Ox{eP#\'\n    \'gknyOTj?v}QXPtWBk~kf-\'\n    \'F3{XnU~Esz<mkW=CV!w<V%!=|gp*i*`M5fhu97)`hgJrXugi5<#lqHAn*MEVY4FOe*L_(z6rW%Ey04KQ9Nbu+xmnzTU}uOV~WW*g\'\n    \'RvAdxd$8J`371zP20jxfR9fI*k*8En16e(%8QrdIGap@%y--\'\n    \'O2xD|MbXxf2QdJ%*SNqJKORv`z_XWjE~e+Ucvg8=5!XYt(v4_Va}VGDek-wk&nuBQXnRCW1&`Ob~XSkEOKCz6^whdx6Zj|B*YIGO\'\n    \'9MT;%ESY!zD++Uf^+yzU^QAZT8LKv(f3C9>L;iGXjzY9N6BpfPYTCdYIWcMQeo(Xv9H;kc@ZR+1E;ym02Tf0Cm5iDWBs&k$PYxAp\'\n    \'8LqkA2Id6`JH*d8jU8ULfOIHT?*6|`{TpOS-\'\n    \'Af*&+uC|uYPr}sAk4TD|IV?^+JQ}4Jw@0;?QWk0RUYWFJF`y>Y<OJ@PGqXpA~58&TNMP^@!Qdf+s#beIi{UVBd=gj-ENU``Phc&K\'\n    \'j3+*8-ng%B_wQCmkMCc~7K;UW4IvGdJ*F=F(YXB5A3VkWZisdx*RZ#~Wxb;f`Np4^#SezwO05c%1E)K-\'\n    \'VzO1GF=a@Jiy9M5V@G3GDY2g{e@v)T|ns&PADJJ(T#@zW;l)-\'\n    \'=mdap$X>F_A1CkV&RBoKv9dtpn}E)gf4)q?>`;eP5yP|(in<m1lbHZ6Hd&!6x7<9I1_?R78LOF*j#;srmT8{K`^Z5AQi`*e>%X!?\'\n    \'On(G^<<d2c4UhB0DCdCD7G$P9W1S7aX+cNz!PNZtU#j9N|6s}i_T90K*(7;f+oOo2)esTCTWF(=|b(f#y*Ge`ty#e^Av-IEM6r(8\'\n    \'QS%F_DYxf7n0U82UV&iKFHEk(!ry`W)c&7vKToG$&sZ<Df*pK${9nt$hFq6sY=rr48Z;KN*)IAk^N-\'\n    \')Bd%dy99DaMCgR8Je=|hM1Qn7gzz9p4OV_~crL{S#M5Rj6J}FKrr6FNwbUH}|;9!7u_Dznb;Rzx2X*#t9BY%LHOjDHalf&1taDw&\'\n    \'RCU0_v<UEyvMyn_Kgq-Dyb9u;UcGc*X#+?MR5v$*$huKRQkLwpSi8jFa^)eUHP=I(v2`!2Zl%g3znIIdadIApjqFhKQG#NDivdz<\'\n    \'6-glG%ZnyNkbo_4AUA2x?sluVZp}-\'\n    \'DS!dRS}pNL(iN~l|}GAy{>TuG_Ejg*Lrw=h|JU(IIMx`Rp_B}ym_X|lw+5KPPp7y_S0pd~f81kILo(DMLcDL0wka{m4SW1_6%hRS\'\n    \'4`N`CC;l0r|uwqK{>PYf~8Wi_d?PzlMfK|zeZ(J>?QpCDJTcre<yN<A%JKdJ>opipM0O-\'\n    \'=|lot;wsB$gd%KLk6KL!C<`W`XKaA6oIFE=lF5tK&3z&h%@?<9_``63E9Ii?{EF;R92xnNP(z_vP!Cr5tOYW8R#7T_l-\'\n    \'{J`Xi&5((HDmU*PnuR88sT=;Gbb5X8cFH2CbZ>sC34{@BxLNAKwUsL;mOTaX~b;WmVs}ag~rS;l|O=MdJ1a6uk-\'\n    \'$jEFWpk2Rq7bB4nUQUwe?5$@@J+dXsqEoa=;WBXYdkWE^;lE+r@Op?nNP`^l?qpsqt4j)I8v%sSCqFA&*=#eS4Z>A&pJt|3^1y@z\'\n    \'|O!ydq!{Xk$s^#t26^$S(X)R0*HySYT{-W?Rc>oNd=5K@ipcPFT4jbSjRovv<z|hb)7k6p6>-\'\n    \'m0~5)mrx4EUD@=n0W3arh=)w~DFgAmB*EUrZlp02vE(ugH^nUG`0?RDMTnaL{1*aTZWwAD0AYj*2@lKAvWf&+=Od*&b(bSzy=<y6\'\n    \'*wWrc|ggd&{mLQb&WgY%lbca7WF%#hbtfGPp@K@(O1?vdgL4j}_lJXGg7u9PtB&ZPyl5?_lMjJ`LJ8eRv<#VMe%HD5CK#<S$X7)5\'\n    \'N#x=j1z&PFmijL#KigX*sVMj`Z5UNo0$!2KO5u;TS);UT2ig+NQTC0@<BN1+8;W%4p)m=}pDE-cu72x4Ql59@4j%KY7w>iR)5@N1\'\n    \'kSxg-}DiDD&SHzbhrCQ=H)<!)-EEC&Zt-(2TDgG%)I;zzhN=hrqDh@>2uUUSR=8)+-\'\n    \'tFW*@#Ddx%ak2Sqrc(0!5gV)*U%<$^yNse!p>hy`TaE5vC^D3_rtBFS@+#6<!D@QF-SwjMgLLwuvNj=~rQS1IYr!w4s+?hH{X(6B\'\n    \'*g>lS3{<I0;pGUJ)FgAkx?(<bhRbU0+e=Lld##!AatySe-\'\n    \'<M<_HtzEI0Sa~qtu4A~Iy~3ftZ0#zv9VP*A&5hoQdS7Um!;IJkAk~8V~;|Hlc-\'\n    \'5nDVAEJ0%^B%sxs=+@_|x}@Q98wU5*lGbVStfOx=+aP=f3_2`NFkT|1FL2H64(k-\'\n    \'&tHE|M<THsAd>_OkGH)rN6mbr(b#6AfeFdBK5iD_9_oCQHa*e`?^e0lJOd`*!)I$dV*vu2V4*F(7=_@&W>Zo5ge=gYun+rpGv+y3\'\n    \'8Y^pgPs7q*Wd(i#u@2nL@K1IPocEIVPEoEQ?HPr65LSTPoS7(RfGSWLOm`^_#fBBesLBwX}2Q0;!uA`)0+8Hynk81p?uiZ$DmMz5\'\n    \'VgwzwSP6(Fz`mrxcx$!<}WiSf~7mPxWTl`8i>XjnHul+Lf$fLai$*GpQst6<`OeUTLprUAKe*5mB{8NMxJ!L*De_E2rieEp%$%OM\'\n    \'A60f4@>Cbrq9&Zxxee0uTv62$fv4Y9_NoJ5Of#=vQeXq*}=Cf(=pxT%@?=RCy%8!_3v?K!$c7lG3U-\'\n    \'5QMZ{WKqt@^u?tqqHxs|@Da@t(Yqn?VQ3~-\'\n    \'+ZJOGqr#sHaioImE{kynpaFGB2_l&@r@PAB#>rdRx*!0UV44<+j7o!~1<imG8CePKNm0Q;?U3bd@IsjaMFZeHgK{#2{#{x3hQC$V\'\n    \'G)m>k1l<R;mJcAfb&`5L$|yGgidr#{OyLq$hHmiTj9Lv7R|1FUlnxRFnSQN7(7AjrG40uWL3h}Lpm-Ehf0IR9f-pq{nq{ajLY}@-\'\n    \'Pu4o&glVC;007BRY$)sO0{n+GAG|h2<MZH&J{md_i~({L324HS-\'\n    \'B|Iotujm(upvyD3qY&36{0juYGFDru4m<y`3r}UGq;qS*R&$b7Y8}1*wgBC*prVN!6VSk`f`%drb%I2_ACU$+NTNssEG$dJv{|Ds\'\n    \'FVW4EemD|$o9uml$f!eX;R*j&6y`_(O|N$C|E+@0+^M7-\'\n    \'bk#NxeXE$rHS_VD)px15{v1)HlCf*MPfT5{f9++24xHS3wH{kD}<`#(g9d?(Ok9+M(lfJn#B2RisGh}e%7zvqLQPHni3r-\'\n    \'O7K5O{4iyC?DwnXV~4cE3P#*k3zG6{S&h)bLez<+MVw5iLZsIc%MtQYFbp4mxtcN!hPIW%qNWhj-\'\n    \'t`Z^Ox%fBB87G59~`3XCqnH~zmnOUbzlfIKUL^EeJs-G8`n!q@xr2GL_vVvE1g?hB;!(2Xg7ygVKrNS9vltW4-\'\n    \'$B+%(z4|+@!P|z;?Mn4q;1qv@`e@*SJj6qZpjW5W-@XSyo#i3m!tkoPr-Jcpd9b9}({wiYYy(sC$-B{a#u|+G_`5T&}*b9KTfh-\'\n    \'|GAs0gKrzzw;1Diy+2E_lalFsajTIreN0!MdTvSXY@yM<JszE-\'\n    \'N6Y33RN=RHQ<OlQI3$P294_2gb?|wsCwrhnP@psozZSU;yNwg5Lk#@e<rmwiZY)JE;>l+@H6uf7Q-\'\n    \'y76eDPV84p+2@3&FBK6~1S)xZEK7+eklk4T6GE;38?Ma0|`11d4|YzAMr6S&YfWO&T%R$znpxd^UmA~Zv^vR`Cyg(HW+jfyf_nGN\'\n    \'aZbpOy67y3Bs&t)c;Y#7@C2OPh08MCS|$71z2Y7cTkmj+p;R&J@dy}}IUdZ5z!<mB3x#E7V198J9sB_r&?MPlf+Ev7Kq$b}H>Daq\'\n    \'7@CQuTiZ{V{=XNo2X4E{5Vm<I+O4MP-zBm483jXT(`f^?=>cs5+N7IzWAKig@DmSxmnBTJo_i2?eXWGxRao@Z@1Rv=PRFf1UwX{4\'\n    \'4)VuD`EYRZvM6>Qp!8lwo$TIdxV?EuXWipYRp<kRExl>(0T=f)M&vw9bxR>11XkkM1s3Rpa&Bwv=Z3x8~<k3>%^S5tx-spyBrf*A\'\n    \'heIwi{HGnD<CC)?~(Nv4U|E-OCOs_Q@AWV7z-\'\n    \'YKnwBEn<+5>nqgCKIO#;moS6q68B1|;@Bl?Q;{z!;Ish^(EGe4dab7+?zT2t$$LY!a*6dH0+dkPMk`gPz^%LK-VMEwqF$Mf$LFIy\'\n    \'#AJ^^Qmf!i_uNC{_modVxk>{+H)=X&%&AC=^8uGRa2_P3t$lT^>gmSNiPUWk!Q(^w5>aU_k5$rg5GzoS>~a=%kiNu_mYAvu&oGb?\'\n    \'!9R)O8T^wn;H2On^ip?g+~PyQ?O`2V&b%%cnp=rL5EDH>?MEvg`d|P>P=Y4B7%++5r~7F=5M3ZM0B0dA!LmW(#zsdKOP$UT4efvB\'\n    \'067rXU}Yv*WDE%0E3FJeFSgJtd6SaFOGM-VdbN(K*e39xrI)t5if={*bE65~0=H7?wMtNhKQ_XEV})6#(tr!ieJKgd&pcgu?t}td\'\n    \'dAUa5DGE05OMpv#XoA$I;|Qt}CDI5_#|5N);OVo};;TS@{fU0-\'\n    \'7EFkQlsjcP3$(qAL=kdE@kWc2=8BX&l6se<Lr@A6=+zY4MGLP=Ic}=+H1yR#M;n)s=#<4@FA|bw#fcTxa&`KYQp6QvDzWu#@LQ^T\'\n    \'Mq4;psg_9cF$35H&@Q=GYNag*8bdH+F!UCf&BWd)u`I}(2nwJmg&gT%wqH)-A+77sQY^Dc2PWdMivWXgR7`slacU>k-\'\n    \'3e?rk8YGpoKrHmK`ZfDKvwp;OYKB@84yceC+z@~<#BP=iWb0Y9B(fGb|`vlU5WxEG90AN5+q2>D@~PE<lqfyG06$7rLlI_m*Xh)q\'\n    \'h{O~2XY{r)t3a%xNNB2WgzFLQJy14rJn=J<U0hJxhVwYIBQCgcM(9XRz0~vWYB7I!3s$9^fGdpnmI`?UzGC-JpYUgHx;g;^&vFDL\'\n    \'llE<kW^OeanPP3V8*8it!@zEGJok-s+?K+VkWs5|D+iP5*pedZbfG{vPK!VD5oW-\'\n    \'V}n%WN+}WHLv8{YLLlumX^{c9KFaWCMQJ$wkoiMt#m!(l`DcrkLz6pX6p^S}=@~d!$AX<PE4L!FC&77{v^wx}mnqakJ&y)JkO#aS\'\n    \'RkkffzI3-+!Ja;Tb~=RyQ`v9HrK%}sH79yfxei*kCy;I-\'\n    \'SWl$UR=U^?I~myaku^gAUe0veerp2Z%A~?d6w>3RgOwwf=A{=vL3EYHv`$R=lWrk}wAewRjh>kdAGQXW<?(ParTD;S<uiO()iS_H\'\n    \'JyF0%BFk&PgC2&tS#fSI%#Wyl&B}^UT|rWqdyKi3b1@l9uckm(HP(7oxHz{!<6_~UlII=*`FxA2B5d`^0Ll6307<b7D^X?`n~W(B\'\n    \'lSlSMZ30(eyl-14k)V^xt}1}!3CpgsYlS8#Qc$pixj9++Rb++-\'\n    \'W@{|H`}uaAw%}@_>S7ilT@QlkNrfA{Be&!%iV%&&@`|U9V27zAC1ps55<g02r4Oqz!v8oEk?5SN1TO`028T&hPDBII7Kx0+Xa%&D\'\n    \'Wu*=Y_sJ8LfYA}0t3=7kHleSVKHQluO(f%_R|#g^Gsz82w3^9VQt>~QNEBF3VkX@25ghj^ie5nDH2P6aHfRK9_E=wFw}_S+FLV=i\'\n    \'+zl3Vz&qRoTxP;W1_FTTna0psDg85AovWP4k8;ABv573W@a(3N{*iD4TIIf9>QMv;WW=<{4RmFH<q1o)A|>1#0N4p5kLc005je&M\'\n    \'Sw0zU=j?$_?K1+@QSDcy^cd@BpDiXhWPnN+wK(P~ApWCEip_hK5%fPIuSVD-\'\n    \'WgZZaYW$^Xd4#V3y62^SE*D=IkMOjtK}+ka$f#+0nhiA~Vzi6H15&vN(Bw+ur-\'\n    \'iYIu@>6ST1m==)X2WPKH!Pki-z4VDH>nevt}+)f*Mb8#R!@ykTDZ98!9p+XVlOjy%Hwv%EJR2(;4JYAS!@wx-je{dYWDULlds;hi\'\n    \'uT3)Zf(s78WQ1^(Y^t`%0`hji!y;qhuT9gApD;7#GMTKy}!=avtcAN)OhQpzK3x8K1QF3uS0%bo{VwfD|f9#?j44o9WZ(N}CZilV\'\n    \'*++4-D|CNF1cY?xS9A9BY#t;shO}|2E_WsQgl-gBTTXxgw3V6Qy$C#Mvd1SuFdrh;owDz34iEgNY0asr`kPqHI$+Vg^=ph$u`l-\'\n    \'mC$|>ZS#3v9YY@sgpYAa}Q|*LR^b)JW|!ytj=ed)j5v@6Qp>g#(Z5C)QJ+MKSLf>WHThB8!NJ2Yl#h^$;im^WfLk!)M#1jK{4k|T\'\n    \'qjA&I)U<6g_uQ)kVz636>3%mCBodECM9c?P~U@~RZ8YOPUGU6Q)1EUf*zeSI5qC0?@&b<=SkUUZIW2MKaQ7%`%X)#Lek!e(!xp~$\'\n    \'<Cv@BPT5-!L=lG4i1*uF5|j}zSAbvT+L2z_7qt(_|fC76*+jKy%Pwhwb48!>3F?-s1?QMjNdSMD8C>PaK?iaB%M!NWI9Y-\'\n    \'J|~q@+)Oo1LEL9_HM6)&PS7w2ldVNgQt)dnuvk6y)C6d2-6kc$*jh};g-\'\n    \'yhECnT?=VIrnBQ~WC(&ZtqTqO^07Wxk{6ZLbSsqnWQrTp}Gk0Yexymhi$Ts-|Qmi^*?``-\'\n    \'#vt2@Q<D^gMCF$&kW@2mZZEK!~ru45aY1IhB3rTJXny*uQgLB3D%7oaIs@(_+z4c1)nVD`ipksbrZByo);6i20#sBR2Gifdf+Ho6\'\n    \'4;f%8S=)m6eDoGA}F0F|HJh<LW`GmL3Zvx0dl@-b>&c=<JyUV}s$1QDS&b;-6-\'\n    \'jWlOi^REtIM!p~K!m1=8O2V+$>>AFcZI6_mktiC}gOIF=0lv7A^q@sva%lt}?RI(Tj8_-\'\n    \'$>hTy<06$bXXWa*8p)w&CgMo~GUJ%qtrt6j2^q&z_!=Ty~2>SWr*%Vp15a&35qDIF=aZ>=;=sRp+$lsPSE2O&V#FT*$HEwMzp^Va\'\n    \'E2`IS}^D!!|=5j<IQ5^_wokm-\'\n    \'B{s`t6@z`PHes3SBmfgV#IHinll<RSwL*W=eN{EEy#(N3c|Sxs$>M%9)8)^cXKlc@#Ec`oE4Q50ME+PjE$PeC@SW`f1$cU!1bR=H\'\n    \'^`-\'\n    \'&ig2zE(}sg!?Nd2Xv_BuE{F~8C*QCE~rim1~;C3P4jqN3EP8^ww8D6)I$}NTyjf~yEv6>iIRjd7$;8eNyzcAQW35BJel%xYBl=OX\'\n    \'wd{oJzq3Tyll>UA}-\'\n    \'BZEdX2^puzV@)<)1nlo2Uc4PV`7ZiOJ91pFzGjunmyzcTqc*A#HN>fuaal(KlPFNQ)1c%9l~#w7~LNBNMGjg$2wT}`Ka2%7o7c8o\'\n    \'|pv~^1(M(dYZ5ijSmYR${m%#%Xp(sD{i$2L%gnxgDiC=?UL`&dijRwf1avUQs&n4K`$KwDz*ub>)?Yj8IWkr<r`l7W1jy}hbeq?F\'\n    \'f@t_xv)POS}=cB~)U8jKC9__8W6eo9HIE%927Yv(i;QD=d{1l2W|p=@M}I&KtO3j$x@z$^x%IRh4tM+78xi&jPnKAQ4FC<d!cWl%\'\n    \'CqkAX)B5d~i>&YWCRM^`1T0-\'\n    \'TlR%gxh=IC|39ofI9#Bif$;C9}>Z#+phM0q0GS_<rm^1?YirG5C}Hz!eCN!dfqkdH))W_DjDSav>lETw+j4C#kD20zXTl3aM6jKW\'\n    \'EKaOvds~@}lqm2Vk5Tdj\'\n    )\n)).decode("utf-8"))\n_REBALANCE_ACTIONS = _LEGACY_ACTIONS\n_PRICE_FLOOR = 1\n_DEMAND_ALPHA = 0.25\n_MARKET_PARAMS = {\n    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),\n    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),\n    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),\n    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),\n    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),\n    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),\n    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),\n    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),\n    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),\n}\n_SHOP_PRODUCTS = {\n    "BAKERY": ("EGG", "WHEAT"),\n    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),\n    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),\n    "YARN_STORE": ("WOOL",),\n    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),\n    "PET_CAFE": ("CARROT",),\n    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),\n    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),\n}\n_WEED_STATE = {0: {}, 1: {}}\n_WEED_REPLAY_STEPS = 8\n\n\ndef _get(value, key, default=None):\n    if isinstance(value, dict):\n        return value.get(key, default)\n    getter = getattr(value, "get", None)\n    if callable(getter):\n        return getter(key, default)\n    return getattr(value, key, default)\n\n\ndef _regime(configuration):\n    interval = int(_get(configuration, "townCenterSellInterval", 12) or 12)\n    return "rebalance" if interval >= 24 else "legacy"\n\n\ndef _copy_action(action):\n    action = copy.deepcopy(action or {})\n    return {\n        "farmer": list(action.get("farmer") or ["PASS"]),\n        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],\n        "market": [list(order) for order in (action.get("market") or [])],\n    }\n\n\ndef _seat(obs):\n    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0\n\n\ndef _farm(obs, seat):\n    farms = list(_get(obs, "farms", []) or [])\n    return farms[seat] if seat < len(farms) else {}\n\n\ndef _align_hands(action, obs):\n    action = _copy_action(action)\n    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])\n    hands = list(action.get("hands") or [])\n    if len(hands) < expected:\n        hands.extend([["PASS"] for _ in range(expected - len(hands))])\n    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]\n    return action\n\n\ndef _tile_at(farm, position):\n    try:\n        x, y = int(position[0]), int(position[1])\n        return (_get(farm, "tiles", []) or [])[y][x]\n    except (IndexError, TypeError, ValueError):\n        return "LOCKED"\n\n\ndef _trace_actor_action(actions, step, actor):\n    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}\n    if actor == "farmer":\n        return list(trace.get("farmer") or ["PASS"])\n    hands = trace.get("hands", []) or []\n    return list(hands[actor] if actor < len(hands) else ["PASS"])\n\n\ndef _weed_repair_action(obs, action, actions, step):\n    action = _align_hands(action, obs)\n    seat = _seat(obs)\n    game = _WEED_STATE[seat]\n    if step == 0 or step < game.get("last_step", -1):\n        game = {"last_step": step, "active": {}}\n        _WEED_STATE[seat] = game\n    game["last_step"] = step\n    farm = _farm(obs, seat)\n    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]\n    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]\n    active = game["active"]\n\n    for actor, transaction in list(active.items()):\n        index = 0 if actor == "farmer" else int(actor) + 1\n        if index >= len(unit_actions):\n            active.pop(actor, None)\n            continue\n        age = step - transaction["start"]\n        if age == 1:\n            unit_actions[index] = list(transaction["intended"])\n        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:\n            unit_actions[index] = _trace_actor_action(actions, step - 1, actor)\n        else:\n            active.pop(actor, None)\n\n    for index, (position, intended) in enumerate(zip(positions, unit_actions)):\n        actor = "farmer" if index == 0 else index - 1\n        if actor in active or not isinstance(intended, list) or not intended:\n            continue\n        if intended[0] not in ("BUILD_PASTURE", "PLANT"):\n            continue\n        tile = _tile_at(farm, position)\n        if not isinstance(tile, dict) or tile.get("kind") != "WEED":\n            continue\n        active[actor] = {"start": step, "intended": list(intended)}\n        unit_actions[index] = ["DIG"]\n\n    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]\n    action["hands"] = unit_actions[1:]\n    return _align_hands(action, obs)\n\n\ndef _shape(name, value):\n    value = max(0.0, float(value))\n    if name == "linear":\n        return value\n    if name == "sq":\n        return value * value\n    if name == "sqrt":\n        return math.sqrt(value)\n    if name == "log":\n        return math.log1p(value)\n    if name == "log10":\n        return math.log10(1.0 + value)\n    raise ValueError(name)\n\n\ndef _market_price(item, inventory):\n    base, equilibrium, scale, below_func, below_target, above_func, above_target = (\n        _MARKET_PARAMS[item]\n    )\n    if inventory < equilibrium:\n        amplitude = below_target * base / _shape(below_func, scale)\n        price = base + amplitude * _shape(below_func, equilibrium - inventory)\n    else:\n        amplitude = above_target * base / _shape(above_func, scale)\n        price = base - amplitude * _shape(above_func, inventory - equilibrium)\n    return max(_PRICE_FLOOR, int(round(price)))\n\n\ndef _is_sell(order):\n    return (\n        isinstance(order, (list, tuple))\n        and len(order) >= 3\n        and order[0] == "SELL"\n        and order[1] in _MARKET_PARAMS\n    )\n\n\ndef _impact_score(obs, order):\n    if not _is_sell(order):\n        return float("-inf")\n    item = str(order[1])\n    try:\n        quantity = max(0, int(order[2]))\n    except (TypeError, ValueError):\n        return 0.0\n    market = _get(obs, "market", {}) or {}\n    inventory = _get(market, "inventory", {}) or {}\n    prices = _get(market, "prices", {}) or {}\n    current_inventory = int(_get(inventory, item, 10000) or 0)\n    current_quote = float(\n        _get(prices, item, _market_price(item, current_inventory)) or 0\n    )\n    later_quote = float(_market_price(item, current_inventory + quantity))\n    return float(quantity) * max(0.0, current_quote - later_quote)\n\n\ndef _demand_per_day(obs, configuration, item):\n    town = _get(obs, "town", {}) or {}\n    shops = list(_get(town, "unlocked_shops", []) or [])\n    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)\n    shop_interval = max(\n        1, int(_get(configuration, "townShopSellInterval", 4) or 4)\n    )\n    demand = 0.0\n    for shop in shops:\n        products = _SHOP_PRODUCTS.get(shop, ())\n        if item in products:\n            demand += (turns_per_day / shop_interval) * (\n                2 if len(products) == 1 else 1\n            )\n    regime = _regime(configuration)\n    if item != "FERTILIZER":\n        center_default = 24 if regime == "rebalance" else 12\n        center_interval = max(\n            1,\n            int(\n                _get(configuration, "townCenterSellInterval", center_default)\n                or center_default\n            ),\n        )\n        day = int(_get(obs, "day", int(_get(obs, "step", 0) or 0) // 24) or 0)\n        multiplier = (\n            1\n            if regime == "rebalance"\n            else (4 if day >= 20 else 2 if day >= 10 else 1)\n        )\n        demand += (turns_per_day / center_interval) * multiplier\n    return demand\n\n\ndef _order_score(obs, configuration, order):\n    score = _impact_score(obs, order)\n    if _regime(configuration) != "rebalance" or score <= 0 or not _is_sell(order):\n        return score\n    item = str(order[1])\n    quantity = max(0, int(order[2]))\n    market = _get(obs, "market", {}) or {}\n    inventory = _get(market, "inventory", {}) or {}\n    current_inventory = int(_get(inventory, item, 10000) or 0)\n    demand = max(0.25, _demand_per_day(obs, configuration, item))\n    excess = max(0.0, current_inventory + quantity - 10000)\n    urgency = min(1.0, (excess / demand) / 10.0)\n    return score * (1.0 + _DEMAND_ALPHA * urgency)\n\n\ndef _rank_sell_slots(obs, action, configuration):\n    action = _copy_action(action)\n    market = list(action.get("market") or [])\n    rows = [\n        (_order_score(obs, configuration, order), -index, list(order))\n        for index, order in enumerate(market)\n        if _is_sell(order)\n    ]\n    if len(rows) < 2:\n        return action\n    rows.sort(reverse=True)\n    ranked = iter(row[2] for row in rows)\n    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]\n    return action\n\n\ndef agent(obs, configuration=None):\n    try:\n        actions = (\n            _REBALANCE_ACTIONS\n            if _regime(configuration) == "rebalance"\n            else _LEGACY_ACTIONS\n        )\n        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)\n        action = _weed_repair_action(\n            obs, _copy_action(actions[step]), actions, step\n        )\n        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)\n    except Exception:\n        farm = _farm(obs, _seat(obs))\n        return {\n            "farmer": ["PASS"],\n            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],\n            "market": [],\n        }\n\n\ndef _kaggle_submission_entrypoint(obs, configuration=None):\n    return agent(obs, configuration)\n\n'
_top_agent_path = Path("_top_replay_agent.py").resolve()
_top_agent_path.write_text(_TOP_AGENT_SOURCE, encoding="utf-8")
assert hashlib.sha256(_top_agent_path.read_bytes()).hexdigest() == TOP_REPLAY_AGENT_SHA256

def show_farm_motion(env, seat=0, stride=6, duration=18):
    frames = list(range(0, len(env.steps), stride))
    if frames[-1] != len(env.steps)-1:
        frames.append(len(env.steps)-1)
    observations = [env.steps[idx][seat].observation for idx in frames]
    player_id = int(observations[0].player)
    farms = [obs.farms[player_id] for obs in observations]
    rows, cols = len(farms[0]['tiles']), len(farms[0]['tiles'][0])

    colors = {
        'LOCKED':'#20362C','EMPTY':'#E6EEE9','WHEAT':'#E5B94E','STRAWBERRY':'#D85C70',
        'MELON':'#61B873','PASTURE':'#4B9DA5','WEED':'#A66BB5','OTHER':'#A9B8AF'
    }
    def category(tile):
        if tile == 'LOCKED': return 'LOCKED'
        if tile is None: return 'EMPTY'
        if isinstance(tile, dict):
            kind = tile.get('kind')
            if kind == 'PLANT': return tile.get('crop','OTHER')
            if kind == 'PASTURE': return 'PASTURE'
            if kind == 'WEED': return 'WEED'
        return 'OTHER'

    cell=27; gap=2; map_x=34; map_y=74
    map_w=cols*cell; map_h=rows*cell
    width=960; height=405
    parts=[]
    parts.append(f'<div style="background:#fff;border:1px solid #d5e3da;border-radius:24px;padding:14px 14px 10px;box-shadow:0 10px 28px rgba(24,68,44,.07);margin:14px 0 16px;overflow-x:auto;color:#173322">')
    parts.append(f'<svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:1040px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg">')
    parts.append('<rect x="8" y="8" width="944" height="389" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>')
    parts.append('<text x="34" y="34" font-size="17" font-weight="800" fill="#173322">Farm topology in motion</text>')
    parts.append('<text x="34" y="54" font-size="11.5" fill="#607168">A compressed replay of the full 720-turn season · tiles + farmer + hired hands</text>')

    # phase rail
    phase_x=495; phase_y=35; phase_w=410
    phases=[(0,.17,'BUILD','#2A8A54'),(.17,.67,'SCALE','#168A9A'),(.67,.93,'PROTECT','#8B5FB2'),(.93,1.0,'CLOSE','#B78312')]
    for a,b,label,color in phases:
        x=phase_x+a*phase_w; w=(b-a)*phase_w
        parts.append(f'<rect x="{x:.1f}" y="{phase_y}" width="{w:.1f}" height="7" rx="3.5" fill="{color}" opacity=".72"/>')
        if w>45:
            parts.append(f'<text x="{x+w/2:.1f}" y="{phase_y+22}" text-anchor="middle" font-size="9" font-weight="800" fill="{color}">{label}</text>')
    parts.append(f'<circle cx="{phase_x}" cy="{phase_y+3.5}" r="6" fill="#FFFFFF" stroke="#173322" stroke-width="2"><animate attributeName="cx" values="{phase_x};{phase_x+phase_w}" dur="{duration}s" repeatCount="indefinite"/></circle>')

    # map background and grid
    parts.append(f'<rect x="{map_x-8}" y="{map_y-8}" width="{map_w+16}" height="{map_h+16}" rx="18" fill="#FFFFFF" stroke="#D6E2DA"/>')
    nframes=len(frames)
    for r in range(rows):
        for c in range(cols):
            vals=[colors[category(f['tiles'][r][c])] for f in farms]
            x=map_x+c*cell; y=map_y+r*cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="4" fill="{vals[0]}"><animate attributeName="fill" values="{";".join(vals)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # moving farmer
    fx=[]; fy=[]
    for farm in farms:
        rr,cc=farm['farmer']
        fx.append(map_x+cc*cell+(cell-gap)/2); fy.append(map_y+rr*cell+(cell-gap)/2)
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="8.8" fill="#FFFFFF" stroke="#173322" stroke-width="3"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="3.2" fill="#2A8A54"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')

    # hired hands
    max_hands=max(len(f['hands']) for f in farms)
    offsets=[(-5,-5),(5,-5),(-5,5),(5,5),(0,-7),(0,7),(-7,0),(7,0)]
    for h in range(max_hands):
        xs=[]; ys=[]; op=[]
        dx,dy=offsets[h%len(offsets)]
        for f in farms:
            if h < len(f['hands']):
                rr,cc=f['hands'][h]
                xs.append(map_x+cc*cell+(cell-gap)/2+dx*.55); ys.append(map_y+rr*cell+(cell-gap)/2+dy*.55); op.append('0.9')
            else:
                xs.append(map_x); ys.append(map_y); op.append('0')
        parts.append(f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.4" opacity="{op[0]}"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in xs)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in ys)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="opacity" values="{";".join(op)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></circle>')

    # right-side legend / readout
    sx=350
    parts.append(f'<text x="{sx}" y="88" font-size="11" font-weight="800" letter-spacing="1.3" fill="#607168">WHAT TO WATCH</text>')
    notes=[('Capacity expands','More cells become productive before the closeout.','#2A8A54'),('Labor circulates','White/teal markers reveal routing and service pressure.','#168A9A'),('Weeds are local shocks','Purple cells appear stochastically; repair should stay local.','#A66BB5'),('Deadline changes behavior','The final phase converts operating value back to cash.','#B78312')]
    yy=108
    for title,desc,col in notes:
        parts.append(f'<circle cx="{sx+4}" cy="{yy+3}" r="4" fill="{col}"/><text x="{sx+17}" y="{yy+6}" font-size="12.5" font-weight="800" fill="#173322">{html.escape(title)}</text><text x="{sx+17}" y="{yy+24}" font-size="10.5" fill="#607168">{html.escape(desc)}</text>')
        yy+=52

    # legend
    parts.append(f'<text x="{sx}" y="317" font-size="10" font-weight="800" letter-spacing="1.2" fill="#607168">TILES</text>')
    legend=[('Empty','EMPTY'),('Wheat','WHEAT'),('Strawberry','STRAWBERRY'),('Melon','MELON'),('Pasture','PASTURE'),('Weed','WEED'),('Locked','LOCKED')]
    lx=sx; ly=331
    for i,(label,key) in enumerate(legend):
        col=i%4; row=i//4; x=lx+col*112; y=ly+row*27
        parts.append(f'<rect x="{x}" y="{y-10}" width="13" height="13" rx="3" fill="{colors[key]}"/><text x="{x+19}" y="{y+1}" font-size="10" fill="#53695D">{label}</text>')
    parts.append(f'<circle cx="{sx+4}" cy="389" r="6" fill="#fff" stroke="#173322" stroke-width="2"/><text x="{sx+17}" y="393" font-size="10" fill="#53695D">Farmer</text><circle cx="{sx+99}" cy="389" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.3"/><text x="{sx+111}" y="393" font-size="10" fill="#53695D">Hands</text>')
    parts.append('</svg></div>')
    display(HTML(''.join(parts)))

# This is the same direct call used in the diagnostic section: build a live env,
# run the actual agent, then render the replay from env.steps.
TOP_REPLAY_SEED = 70117
env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": TOP_REPLAY_SEED},
    debug=False,
)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    env.run([str(_top_agent_path), str(_top_agent_path)])
show_farm_motion(env, seat=0, stride=6, duration=18)

try:
    _top_agent_path.unlink()
except OSError:
    pass

from pathlib import Path
from collections import Counter
from cycler import cycler
import contextlib
import gzip
import html
import hashlib
import io
import math
import py_compile
import tarfile
import tempfile

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd
from IPython.display import HTML, Image, display

# Silence only optional environment import chatter.
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments import make

# Figures use a light, self-contained canvas so the saved outputs remain readable
# in both Kaggle light and dark themes.
FOREST = "#F7FAF8"
PANEL = "#FFFFFF"
GRID = "#D6E2DA"
TEXT = "#173322"
MUTED = "#607168"
PALETTE = ["#23864F", "#168A9A", "#B78312", "#8B5FB2", "#C75B4F", "#5577B8"]

plt.rcParams.update({
    "figure.dpi": 92,
    "savefig.dpi": 92,
    "font.size": 10,
    "figure.facecolor": FOREST,
    "axes.facecolor": PANEL,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": TEXT,
    "grid.color": GRID,
    "axes.prop_cycle": cycler(color=PALETTE),
})

def forest_axes(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.grid(alpha=.55)
    if title:
        ax.set_title(title, color=TEXT, fontsize=14, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT)
    return ax

def show_forest_figure(fig, quality=84):
    fig.patch.set_facecolor(FOREST)
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="jpeg",
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pil_kwargs={"quality": quality, "optimize": True},
    )
    plt.close(fig)
    display(Image(data=buffer.getvalue(), format="jpeg"))

def show_forest_table(frame, caption=None, formats=None):
    """Theme-independent compact table for precise audit data."""
    table = frame.copy()
    if formats:
        for column, formatter in formats.items():
            if column in table:
                table[column] = table[column].map(formatter)
    caption_html = f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:0 0 9px">{caption}</div>' if caption else ""
    html = table.to_html(index=False, border=0, classes="forest-table", escape=False)
    style = ("<style>.forest-table{border-collapse:collapse;width:100%;color:#173322;font-size:13.5px}"
             ".forest-table th{background:#eef6f1;color:#274b38;text-align:left;padding:10px 11px;border-bottom:1px solid #cbded1;font-size:12px;letter-spacing:.02em}"
             ".forest-table td{padding:9px 11px;border-bottom:1px solid #e1ebe4;color:#294438}"
             ".forest-table tr:nth-child(even){background:#f8fbf9}.forest-table tr:nth-child(odd){background:#fff}"
             ".forest-table tbody tr:last-child td{border-bottom:0}</style>")
    wrapper = '<div style="background:#fff;border:1px solid #d3e1d8;border-radius:17px;padding:15px 16px;overflow-x:auto;box-shadow:0 5px 16px rgba(24,68,44,.05);color:#173322">'
    display(HTML(wrapper + caption_html + style + html + "</div>"))


def show_kpi_cards(items, eyebrow="Observed in this run"):
    cards = []
    for label, value, note, accent in items:
        cards.append(
            f'<div style="background:#fff;border:1px solid #d5e3da;border-top:4px solid {accent};border-radius:16px;padding:14px 15px;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
            f'<div style="font-size:10px;letter-spacing:.11em;text-transform:uppercase;font-weight:800;color:#64786c">{label}</div>'
            f'<div style="font-size:23px;font-weight:850;letter-spacing:-.02em;margin:3px 0 2px;color:#173322">{value}</div>'
            f'<div style="font-size:12px;color:#687970;line-height:1.35">{note}</div></div>'
        )
    display(HTML(
        f'<div style="font-size:12px;letter-spacing:.10em;text-transform:uppercase;font-weight:800;color:#176b42;margin:18px 0 8px">{eyebrow}</div>'
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px;margin:0 0 12px">' + ''.join(cards) + '</div>'
    ))


def show_insight(title, body, accent="#2a8a54", tag="INSIGHT"):
    display(HTML(
        f'<div style="background:#fff;border:1px solid #d5e3da;border-left:5px solid {accent};border-radius:15px;padding:14px 16px;margin:12px 0;color:#173322;box-shadow:0 4px 14px rgba(24,68,44,.04)">'
        f'<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:{accent};margin-bottom:4px">{tag}</div>'
        f'<div style="font-weight:800;margin-bottom:4px;color:#173322">{title}</div>'
        f'<div style="color:#53695d;line-height:1.55;font-size:13.5px">{body}</div></div>'
    ))

def shade_season_phases(ax):
    """Light phase bands that connect diagnostics to the 30-day strategy atlas."""
    phases = [
        (1, 5, "BUILD", "#2A8A54"),
        (5, 20, "SCALE", "#168A9A"),
        (20, 28, "PROTECT", "#8B5FB2"),
        (28, 30, "CLOSE", "#B78312"),
    ]
    for start, end, label, color in phases:
        ax.axvspan(start, end, color=color, alpha=.055, lw=0, zorder=0)
        ax.text(
            (start + end) / 2,
            .965,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color=color,
            alpha=.82,
        )
    return ax


def show_market_motion(prices, item="STRAWBERRY", probe_quantity=20):
    """A tiny SVG animation: no GIF, no base64, and only a few KB of notebook output."""
    prices = np.asarray(prices, dtype=float)
    revenue = np.cumsum(prices)
    if len(prices) < 3:
        return

    width, height = 960, 370
    left = (62, 86, 360, 205)
    right = (540, 86, 360, 205)

    def path_for(values, box):
        x0, y0, w, h = box
        values = np.asarray(values, dtype=float)
        lo, hi = float(values.min()), float(values.max())
        span = max(hi - lo, 1.0)
        pts = []
        for i, value in enumerate(values):
            x = x0 + (w * i / max(len(values) - 1, 1))
            y = y0 + h - h * (float(value) - lo) / span
            pts.append((x, y))
        return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts), lo, hi

    price_path, p_lo, p_hi = path_for(prices, left)
    rev_path, r_lo, r_hi = path_for(revenue, right)
    q = min(int(probe_quantity), max(1, len(prices) // 3))
    impact_score = float(q * max(0, prices[0] - prices[min(q, len(prices)-1)]))

    def money(v):
        return f"${v:,.0f}"

    svg = f'''<div style="background:#fff;border:1px solid #d5e3da;border-radius:22px;padding:16px 16px 12px;box-shadow:0 8px 24px rgba(24,68,44,.06);margin:12px 0 16px;overflow-x:auto;color:#173322">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px">
      <div style="flex:1;min-width:145px;background:#f2faf5;border:1px solid #d8e8dd;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">OPENING QUOTE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[0])}</div></div>
      <div style="flex:1;min-width:145px;background:#eef8fa;border:1px solid #d5e6e9;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">AFTER {len(prices)} UNITS</div><div style="font-size:21px;font-weight:850;color:#173322">{money(prices[-1])}</div></div>
      <div style="flex:1;min-width:145px;background:#f8f1fb;border:1px solid #e5d9ec;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">{q}-UNIT IMPACT SCORE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(impact_score)}</div></div>
      <div style="flex:1;min-width:145px;background:#fff8e9;border:1px solid #eee0bf;border-radius:14px;padding:10px 12px"><div style="font-size:10px;letter-spacing:.11em;font-weight:800;color:#607168">TOTAL REVENUE</div><div style="font-size:21px;font-weight:850;color:#173322">{money(revenue[-1])}</div></div>
    </div>
    <svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:980px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" role="img" aria-label="Animated market price erosion and cumulative revenue">
      <defs>
        <linearGradient id="kgPriceGrad" x1="0" x2="1"><stop offset="0" stop-color="#23864F"/><stop offset="1" stop-color="#168A9A"/></linearGradient>
        <linearGradient id="kgRevGrad" x1="0" x2="1"><stop offset="0" stop-color="#168A9A"/><stop offset="1" stop-color="#8B5FB2"/></linearGradient>
        <filter id="kgGlow"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <rect x="18" y="14" width="924" height="334" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>
      <text x="62" y="48" fill="#173322" font-size="17" font-weight="800">Market pressure in motion · {item.title()}</text>
      <text x="62" y="68" fill="#607168" font-size="12">The same sale becomes less valuable as shared inventory moves before it.</text>

      <rect x="44" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <rect x="522" y="78" width="396" height="232" rx="16" fill="#fff" stroke="#D6E2DA"/>
      <text x="62" y="105" fill="#173322" font-size="13" font-weight="800">SELL PRICE</text>
      <text x="540" y="105" fill="#173322" font-size="13" font-weight="800">CUMULATIVE REVENUE</text>
      <text x="62" y="299" fill="#607168" font-size="11">units added to shared market inventory →</text>
      <text x="540" y="299" fill="#607168" font-size="11">units sold →</text>
      <text x="404" y="126" text-anchor="end" fill="#607168" font-size="10">{money(p_hi)}</text>
      <text x="404" y="282" text-anchor="end" fill="#607168" font-size="10">{money(p_lo)}</text>
      <text x="882" y="126" text-anchor="end" fill="#607168" font-size="10">{money(r_hi)}</text>
      <text x="882" y="282" text-anchor="end" fill="#607168" font-size="10">{money(r_lo)}</text>

      <path d="{price_path}" fill="none" stroke="#BFD6C8" stroke-width="4" opacity=".5"/>
      <path id="kgPricePath" d="{price_path}" pathLength="1" fill="none" stroke="url(#kgPriceGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#23864F" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgPricePath"/></animateMotion>
      </circle>

      <path d="{rev_path}" fill="none" stroke="#C9D9E1" stroke-width="4" opacity=".5"/>
      <path id="kgRevPath" d="{rev_path}" pathLength="1" fill="none" stroke="url(#kgRevGrad)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1">
        <animate attributeName="stroke-dashoffset" values="1;0;0;1" keyTimes="0;.76;.92;1" dur="7s" repeatCount="indefinite"/>
      </path>
      <circle r="6" fill="#8B5FB2" stroke="#fff" stroke-width="2" filter="url(#kgGlow)">
        <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0;1;1;0" keyTimes="0;.76;.92;1" calcMode="linear"><mpath xlink:href="#kgRevPath"/></animateMotion>
      </circle>

      <text x="480" y="338" text-anchor="middle" fill="#53695D" font-size="12">SVG animation: lightweight, vector-sharp, and free of embedded GIF/base64 payloads.</text>
    </svg></div>'''
    display(HTML(svg))



def show_farm_motion(env, seat=0, stride=6, duration=18):
    frames = list(range(0, len(env.steps), stride))
    if frames[-1] != len(env.steps)-1:
        frames.append(len(env.steps)-1)
    observations = [env.steps[idx][seat].observation for idx in frames]
    player_id = int(observations[0].player)
    farms = [obs.farms[player_id] for obs in observations]
    rows, cols = len(farms[0]['tiles']), len(farms[0]['tiles'][0])

    colors = {
        'LOCKED':'#20362C','EMPTY':'#E6EEE9','WHEAT':'#E5B94E','STRAWBERRY':'#D85C70',
        'MELON':'#61B873','PASTURE':'#4B9DA5','WEED':'#A66BB5','OTHER':'#A9B8AF'
    }
    def category(tile):
        if tile == 'LOCKED': return 'LOCKED'
        if tile is None: return 'EMPTY'
        if isinstance(tile, dict):
            kind = tile.get('kind')
            if kind == 'PLANT': return tile.get('crop','OTHER')
            if kind == 'PASTURE': return 'PASTURE'
            if kind == 'WEED': return 'WEED'
        return 'OTHER'

    cell=27; gap=2; map_x=34; map_y=74
    map_w=cols*cell; map_h=rows*cell
    width=960; height=405
    parts=[]
    parts.append(f'<div style="background:#fff;border:1px solid #d5e3da;border-radius:24px;padding:14px 14px 10px;box-shadow:0 10px 28px rgba(24,68,44,.07);margin:14px 0 16px;overflow-x:auto;color:#173322">')
    parts.append(f'<svg viewBox="0 0 {width} {height}" width="100%" style="min-width:760px;max-width:1040px;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg">')
    parts.append('<rect x="8" y="8" width="944" height="389" rx="22" fill="#F7FAF8" stroke="#D6E2DA"/>')
    parts.append('<text x="34" y="34" font-size="17" font-weight="800" fill="#173322">Farm topology in motion</text>')
    parts.append('<text x="34" y="54" font-size="11.5" fill="#607168">A compressed replay of the full 720-turn season · tiles + farmer + hired hands</text>')

    # phase rail
    phase_x=495; phase_y=35; phase_w=410
    phases=[(0,.17,'BUILD','#2A8A54'),(.17,.67,'SCALE','#168A9A'),(.67,.93,'PROTECT','#8B5FB2'),(.93,1.0,'CLOSE','#B78312')]
    for a,b,label,color in phases:
        x=phase_x+a*phase_w; w=(b-a)*phase_w
        parts.append(f'<rect x="{x:.1f}" y="{phase_y}" width="{w:.1f}" height="7" rx="3.5" fill="{color}" opacity=".72"/>')
        if w>45:
            parts.append(f'<text x="{x+w/2:.1f}" y="{phase_y+22}" text-anchor="middle" font-size="9" font-weight="800" fill="{color}">{label}</text>')
    parts.append(f'<circle cx="{phase_x}" cy="{phase_y+3.5}" r="6" fill="#FFFFFF" stroke="#173322" stroke-width="2"><animate attributeName="cx" values="{phase_x};{phase_x+phase_w}" dur="{duration}s" repeatCount="indefinite"/></circle>')

    # map background and grid
    parts.append(f'<rect x="{map_x-8}" y="{map_y-8}" width="{map_w+16}" height="{map_h+16}" rx="18" fill="#FFFFFF" stroke="#D6E2DA"/>')
    nframes=len(frames)
    for r in range(rows):
        for c in range(cols):
            vals=[colors[category(f['tiles'][r][c])] for f in farms]
            x=map_x+c*cell; y=map_y+r*cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell-gap}" height="{cell-gap}" rx="4" fill="{vals[0]}"><animate attributeName="fill" values="{";".join(vals)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    # moving farmer
    fx=[]; fy=[]
    for farm in farms:
        rr,cc=farm['farmer']
        fx.append(map_x+cc*cell+(cell-gap)/2); fy.append(map_y+rr*cell+(cell-gap)/2)
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="8.8" fill="#FFFFFF" stroke="#173322" stroke-width="3"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')
    parts.append(f'<circle cx="{fx[0]:.1f}" cy="{fy[0]:.1f}" r="3.2" fill="#2A8A54"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in fx)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in fy)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/></circle>')

    # hired hands
    max_hands=max(len(f['hands']) for f in farms)
    offsets=[(-5,-5),(5,-5),(-5,5),(5,5),(0,-7),(0,7),(-7,0),(7,0)]
    for h in range(max_hands):
        xs=[]; ys=[]; op=[]
        dx,dy=offsets[h%len(offsets)]
        for f in farms:
            if h < len(f['hands']):
                rr,cc=f['hands'][h]
                xs.append(map_x+cc*cell+(cell-gap)/2+dx*.55); ys.append(map_y+rr*cell+(cell-gap)/2+dy*.55); op.append('0.9')
            else:
                xs.append(map_x); ys.append(map_y); op.append('0')
        parts.append(f'<circle cx="{xs[0]:.1f}" cy="{ys[0]:.1f}" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.4" opacity="{op[0]}"><animate attributeName="cx" values="{";".join(f"{v:.1f}" for v in xs)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="cy" values="{";".join(f"{v:.1f}" for v in ys)}" dur="{duration}s" calcMode="linear" repeatCount="indefinite"/><animate attributeName="opacity" values="{";".join(op)}" dur="{duration}s" calcMode="discrete" repeatCount="indefinite"/></circle>')

    # right-side legend / readout
    sx=350
    parts.append(f'<text x="{sx}" y="88" font-size="11" font-weight="800" letter-spacing="1.3" fill="#607168">WHAT TO WATCH</text>')
    notes=[('Capacity expands','More cells become productive before the closeout.','#2A8A54'),('Labor circulates','White/teal markers reveal routing and service pressure.','#168A9A'),('Weeds are local shocks','Purple cells appear stochastically; repair should stay local.','#A66BB5'),('Deadline changes behavior','The final phase converts operating value back to cash.','#B78312')]
    yy=108
    for title,desc,col in notes:
        parts.append(f'<circle cx="{sx+4}" cy="{yy+3}" r="4" fill="{col}"/><text x="{sx+17}" y="{yy+6}" font-size="12.5" font-weight="800" fill="#173322">{html.escape(title)}</text><text x="{sx+17}" y="{yy+24}" font-size="10.5" fill="#607168">{html.escape(desc)}</text>')
        yy+=52

    # legend
    parts.append(f'<text x="{sx}" y="317" font-size="10" font-weight="800" letter-spacing="1.2" fill="#607168">TILES</text>')
    legend=[('Empty','EMPTY'),('Wheat','WHEAT'),('Strawberry','STRAWBERRY'),('Melon','MELON'),('Pasture','PASTURE'),('Weed','WEED'),('Locked','LOCKED')]
    lx=sx; ly=331
    for i,(label,key) in enumerate(legend):
        col=i%4; row=i//4; x=lx+col*112; y=ly+row*27
        parts.append(f'<rect x="{x}" y="{y-10}" width="13" height="13" rx="3" fill="{colors[key]}"/><text x="{x+19}" y="{y+1}" font-size="10" fill="#53695D">{label}</text>')
    parts.append(f'<circle cx="{sx+4}" cy="389" r="6" fill="#fff" stroke="#173322" stroke-width="2"/><text x="{sx+17}" y="393" font-size="10" fill="#53695D">Farmer</text><circle cx="{sx+99}" cy="389" r="3.3" fill="#D7F4F7" stroke="#168A9A" stroke-width="1.3"/><text x="{sx+111}" y="393" font-size="10" fill="#53695D">Hands</text>')
    parts.append('</svg></div>')
    display(HTML(''.join(parts)))





with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    preview_env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": 70117},
        debug=False,
    )
opening = preview_env.steps[0][0].observation
opening_prices = dict(opening.market["prices"])
opening_inventory = dict(opening.market["inventory"])

contract = pd.DataFrame([
    ("Season", "30 days × 24 turns", "Every investment has a hard liquidation deadline"),
    ("Players", "2", "Both farms affect the same market"),
    ("Starting bank", f"{float(opening.farms[0]['money']):,.0f}", "Early cash must become productive capacity"),
    ("Market products", str(len(opening_prices)), "Sales compete for price and queue position"),
    ("Orders / turn", "10", "Order selection and order sequence both matter"),
], columns=["Mechanic", "Observed value", "Why it matters"])
show_forest_table(contract, "Environment contract used by the controller")

price_frame = pd.DataFrame({"product": list(opening_prices), "opening_price": list(opening_prices.values())}).sort_values("opening_price")
fig, ax = plt.subplots(figsize=(9.2, 4.1))
ax.barh(price_frame["product"], price_frame["opening_price"], color=PALETTE[0], alpha=.9)
forest_axes(ax, "Opening quotes: useful, but not a profit ranking", "Coins per unit", "")
ax.grid(axis="x", alpha=.25); ax.grid(axis="y", alpha=0)
for i, v in enumerate(price_frame["opening_price"]):
    ax.text(v + max(price_frame["opening_price"])*.015, i, f"{v:,.0f}", va="center", color=TEXT, fontsize=9)
show_forest_figure(fig)

highest_product = price_frame.iloc[-1]["product"]
highest_price = float(price_frame.iloc[-1]["opening_price"])
lowest_price = float(price_frame.iloc[0]["opening_price"])
show_insight(
    "Opening price is a state variable, not a crop ranking",
    f"The opening snapshot ranges from {lowest_price:,.0f} to {highest_price:,.0f} coins per unit, with {highest_product.title()} highest at this instant. The controller does not equate that quote with profit: growth time, labor travel, repeatability, inventory timing, and later price erosion still decide whether the asset is worth funding.",
    accent="#168a9a",
    tag="EDA READ"
)


%%writefile main.py
"""Sparse adaptive farming controller for Kaggriculture.

A complete season route coordinates production, labor, logistics, and planned
market activity. Runtime feedback stays narrow: actor-local WEED recovery and
ordering only route-existing SELL slots by nonlinear price impact plus bounded
current Town demand. Ordinary SELL orders are not created, deleted, or resized.
"""
import base64
import copy
import json
import math
import zlib


_LEGACY_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
    (
    'c-'
    'rk<%WhoP5&RdfXW@BJkL+maIwC@g0!d}y2!vrE4gv(u!pSbkzlRp*dAqv0y3e^oTG4Jq&D?w5r@Okk`qO{T{`S+azx@2`*&jZgeY'
    'm*2J-eTs{r#tZ{`FrEe|Y%#%TK@l<L7@reExLy?($}M_+RbAw;zA_@#6jE_ZL@Zv$HqX>$BP1{Q36XFnl<ht+xMhI}C3h{=9xST-'
    '=?_&PRX#ez>}RfAHrIH`i}JzPUU6!To<{N8P!6^QVs=4&J}(*r&7gaC`T;p}P;8&L8~juzipJdpIE8%Qme!e%<@)o4a?PpT7TOU%'
    '2_H_QFlW)t7wx@$%~Jj}QO6`?#5+@D1ai$o;vxcr)zAPaD0>Pkx)JqZd8=$NRh8>^m>~?r`Bq?;HK%aA92B4L9D4-dw0-'
    'xA`U<vTdKn?FH{-LpIv1=(+pOw5$XBru}ol_9@K1eZlUr{#fN_-M;7c`r~H2!BFY5?a#%2-'
    'P)0An(Tx2`a{%bvUf+N9ilFit&CNV$(Dw!Y0|e30V6f)Qti3><?8;a_Fy{&eb*2hnLcZ1`?TR=ilw6r)Kn{H^da$FWWR;?)Z;>BS'
    'KIZ~)$r!-$M1%lyUVM~zkF`5z35V=%VRTA_bF-ydBFCtO*Is}HEd`wI>}~lw|CD8+B~yzQ5F{U*Pnd-'
    '$us)N@tJr#T>a*W9_*Ay2NOHA#^ro*pYj5CHb8vx_znv67Ar@Y@!^h#26lLUpFC^K<y*fU_P1lDq2T<7ZC6_8-'
    'zB(>@z2dLg@^psQ0P2NVDRxMRT?<<BvOmuz*Q@}+757`3Ht#yEs)0-Oq(;nVFQ^vTR2L4*vZ5OR!0at6c1378UO$A+v-'
    '(!bmtv|vh&fOZ|`m{*53{{H$R-'
    'smc`3(^r8Eu*z0<Hnv1ga%G^4v2Q$^$6Uh~u0VuV6rRw*FZJa&U@Q5_KRpaZo>7D?7AH9fsbijbF*%1Phhyd2umsBjI{qiV1Z{IK'
    '%nD1m}dZveFgjjn)ffVcJo{K~k8#%(`TCTpY5BW3!ESR+mnmk@|CXS=OU+?~2?s8k>lOAEQ&BlK&x@e9g{oCrjxcPJ80t16du8A_'
    '}kT7w;LqUkH;v|n<Y^gb$172IsPcaF)%e`xz)bahdu?KFW@lnqOpFFcWh<m=fm6Zw6J#rgXm1jwciB<ai<zL;~ll$doW4Pw#J6tW'
    '@`(L%Ouj-'
    '!C`1)UDjDrTq0oe$#3l_Vlv8B{*a6GkzfE>&dm<xo^=GzVNsqJys`i`={64lX;4`GiD5RJ3i2Wu<r@5|kl^!TA|6OA9+1J-'
    'd+krN=@30IuO1X^5i6-'
    'DdGed#l%eHmDj(74*DNGF<srvw$2c~C(y*1>C@mvM0DketFUVD3ifPx?4S7Z4?X|0Ti?3<6@fMz4Vfo@aLeq=j^XVjFccK#w4uVC'
    'dJCac721!uGI_!3!aL(A%5q55YPh_SN2#yuQBLoYde1UvAyMhl}U!S!~-'
    '`v;n=ExS@+m5PFt&9JlYv94WfB%Kg*bb9T#6e=>1r_K!7y*~nZNJ*492fJB+Z(p4@|8%-'
    ')W2{=<p433v@na{gvPPbDksZN1z7DasI^N*K!C2A2CIkvMT`}eh;-q#utQa|;AbM~L4FHLym`G(m{W{#v<xTr%$ARRCKYR2+Yj-Q'
    'AavHzw$&MS+^rre;u5zwQLl@_d`<NE-'
    'e8_`ngfc`25aC8MG)>A1uw;KjHL1xr?jEW6;A;fg|N*lEr&s3970@ib|qe4eiF#!OF%B)#1$JT6R)=a~cgs9~#jI@o0t;zKuK~{I'
    ')g5m2xqOvFA$nHaQG8pUEID=ZgRQ@uz@zB^?Ao#6)FogbQY_n$*bB}fldhG6<Z!iA{FT*yN*|7YO`7VroEliFUnID$!7oZNNccN%'
    '?oO?P6Fnk!c-uoy$J)#-*LV5<0xvylP24XyO6_i6?Y2o@x3*A?ee3AWiZO5o3kJfqJ;qkp2*amN-l9O9@-'
    '5T@8urFpUs7a9Y5Im+939_tei-NdvXbvEWY2w9U?RL{F<NgR-'
    'HHqn99jvig)G1`JzxA9^$Ry<{JXK%;yUuX#UBN6mR@TvyR=9G&%%>)+8GAR-9xomiln8Cd-DI#V(!>j)XBC~Z;UWSqoqrlYr`i=s'
    's-'
    '09m<uUe|l=W0SoxtcLB1jK<=J<x51uWPW6PZc)FyN=bJjM~Z&L+68N7VO4Cp7WDzr6a>Zwd)G_%Z*+TK)6ph)9z~zi<p5ZqYM$AT'
    'sVNXl7(D*8&+r<X^IebLMe(z5tD9G|^F(S+fz``r$>`fyh!IghW1Hd|+32Bco+Y4(~eVn&+7a#ylIBUOopk8TSjiuv{AQSi#Z={R'
    '0rxsHD6Sy0>F@Bydl=Wn7v^xM=fhV|kzOAb<%+7AoCA$5-'
    '$2J~1fBtB4k*nVHJA0oFfvkAp>NI9o|M8yk}Xu?R6L+l1E=fAVm>)<xW)op|_Y<`DJEl!EJh0?s^n|489xqLi>%pn5aiYo`t}O!6'
    'W|zk1<>7xqNP&Q8Z<gD?SGY>q|NUzZa7bT7-~29gki?{0y^mN9YMw1Jqowi%WdBpv7^1g7|;-'
    'O~{+Lf+89OAic7_dCVTt6^s@ugQf-BT7WK9$Bl*w*&Xh&N-X5g%D8HVa~P=`t~iSWrS2cpgK-{3%_S=o-'
    'wdS<9!7iXboU=CP4SQgn>sGj2vk|Gf9>C2{m&+oju@nI)J&2Ma_0VFX2A#sJp2k4d@g&p{$TPa3vhAd&X`ISDGt%jcanyLA0x4lP'
    'QC03}B?6aq9M9_oIRE0-'
    'IASVop5*;hO(D?oBX4BDGS!w88ljF$GC!2R^ReXt{%>;3z?Kl3eeAf5<L;vc=PU)zSFbmgJ5h`+IPh+Ar<<vD-kPL+*Ys)Acg5w('
    'T^C{8#^*p!euB1pQy@Xo?_#?B2*kI5B7OfX%vF;E!|3XE3}@$QsR<H0T_MaS5;*B+P`Tw#ADtKI|+;6fIK@VxtR<!2@FM4Ox{eP#'
    'gknyOTj?v}QXPtWBk~kf-'
    'F3{XnU~Esz<mkW=CV!w<V%!=|gp*i*`M5fhu97)`hgJrXugi5<#lqHAn*MEVY4FOe*L_(z6rW%Ey04KQ9Nbu+xmnzTU}uOV~WW*g'
    'RvAdxd$8J`371zP20jxfR9fI*k*8En16e(%8QrdIGap@%y--'
    'O2xD|MbXxf2QdJ%*SNqJKORv`z_XWjE~e+Ucvg8=5!XYt(v4_Va}VGDek-wk&nuBQXnRCW1&`Ob~XSkEOKCz6^whdx6Zj|B*YIGO'
    '9MT;%ESY!zD++Uf^+yzU^QAZT8LKv(f3C9>L;iGXjzY9N6BpfPYTCdYIWcMQeo(Xv9H;kc@ZR+1E;ym02Tf0Cm5iDWBs&k$PYxAp'
    '8LqkA2Id6`JH*d8jU8ULfOIHT?*6|`{TpOS-'
    'Af*&+uC|uYPr}sAk4TD|IV?^+JQ}4Jw@0;?QWk0RUYWFJF`y>Y<OJ@PGqXpA~58&TNMP^@!Qdf+s#beIi{UVBd=gj-ENU``Phc&K'
    'j3+*8-ng%B_wQCmkMCc~7K;UW4IvGdJ*F=F(YXB5A3VkWZisdx*RZ#~Wxb;f`Np4^#SezwO05c%1E)K-'
    'VzO1GF=a@Jiy9M5V@G3GDY2g{e@v)T|ns&PADJJ(T#@zW;l)-'
    '=mdap$X>F_A1CkV&RBoKv9dtpn}E)gf4)q?>`;eP5yP|(in<m1lbHZ6Hd&!6x7<9I1_?R78LOF*j#;srmT8{K`^Z5AQi`*e>%X!?'
    'On(G^<<d2c4UhB0DCdCD7G$P9W1S7aX+cNz!PNZtU#j9N|6s}i_T90K*(7;f+oOo2)esTCTWF(=|b(f#y*Ge`ty#e^Av-IEM6r(8'
    'QS%F_DYxf7n0U82UV&iKFHEk(!ry`W)c&7vKToG$&sZ<Df*pK${9nt$hFq6sY=rr48Z;KN*)IAk^N-'
    ')Bd%dy99DaMCgR8Je=|hM1Qn7gzz9p4OV_~crL{S#M5Rj6J}FKrr6FNwbUH}|;9!7u_Dznb;Rzx2X*#t9BY%LHOjDHalf&1taDw&'
    'RCU0_v<UEyvMyn_Kgq-Dyb9u;UcGc*X#+?MR5v$*$huKRQkLwpSi8jFa^)eUHP=I(v2`!2Zl%g3znIIdadIApjqFhKQG#NDivdz<'
    '6-glG%ZnyNkbo_4AUA2x?sluVZp}-'
    'DS!dRS}pNL(iN~l|}GAy{>TuG_Ejg*Lrw=h|JU(IIMx`Rp_B}ym_X|lw+5KPPp7y_S0pd~f81kILo(DMLcDL0wka{m4SW1_6%hRS'
    '4`N`CC;l0r|uwqK{>PYf~8Wi_d?PzlMfK|zeZ(J>?QpCDJTcre<yN<A%JKdJ>opipM0O-'
    '=|lot;wsB$gd%KLk6KL!C<`W`XKaA6oIFE=lF5tK&3z&h%@?<9_``63E9Ii?{EF;R92xnNP(z_vP!Cr5tOYW8R#7T_l-'
    '{J`Xi&5((HDmU*PnuR88sT=;Gbb5X8cFH2CbZ>sC34{@BxLNAKwUsL;mOTaX~b;WmVs}ag~rS;l|O=MdJ1a6uk-'
    '$jEFWpk2Rq7bB4nUQUwe?5$@@J+dXsqEoa=;WBXYdkWE^;lE+r@Op?nNP`^l?qpsqt4j)I8v%sSCqFA&*=#eS4Z>A&pJt|3^1y@z'
    '|O!ydq!{Xk$s^#t26^$S(X)R0*HySYT{-W?Rc>oNd=5K@ipcPFT4jbSjRovv<z|hb)7k6p6>-'
    'm0~5)mrx4EUD@=n0W3arh=)w~DFgAmB*EUrZlp02vE(ugH^nUG`0?RDMTnaL{1*aTZWwAD0AYj*2@lKAvWf&+=Od*&b(bSzy=<y6'
    '*wWrc|ggd&{mLQb&WgY%lbca7WF%#hbtfGPp@K@(O1?vdgL4j}_lJXGg7u9PtB&ZPyl5?_lMjJ`LJ8eRv<#VMe%HD5CK#<S$X7)5'
    'N#x=j1z&PFmijL#KigX*sVMj`Z5UNo0$!2KO5u;TS);UT2ig+NQTC0@<BN1+8;W%4p)m=}pDE-cu72x4Ql59@4j%KY7w>iR)5@N1'
    'kSxg-}DiDD&SHzbhrCQ=H)<!)-EEC&Zt-(2TDgG%)I;zzhN=hrqDh@>2uUUSR=8)+-'
    'tFW*@#Ddx%ak2Sqrc(0!5gV)*U%<$^yNse!p>hy`TaE5vC^D3_rtBFS@+#6<!D@QF-SwjMgLLwuvNj=~rQS1IYr!w4s+?hH{X(6B'
    '*g>lS3{<I0;pGUJ)FgAkx?(<bhRbU0+e=Lld##!AatySe-'
    '<M<_HtzEI0Sa~qtu4A~Iy~3ftZ0#zv9VP*A&5hoQdS7Um!;IJkAk~8V~;|Hlc-'
    '5nDVAEJ0%^B%sxs=+@_|x}@Q98wU5*lGbVStfOx=+aP=f3_2`NFkT|1FL2H64(k-'
    '&tHE|M<THsAd>_OkGH)rN6mbr(b#6AfeFdBK5iD_9_oCQHa*e`?^e0lJOd`*!)I$dV*vu2V4*F(7=_@&W>Zo5ge=gYun+rpGv+y3'
    '8Y^pgPs7q*Wd(i#u@2nL@K1IPocEIVPEoEQ?HPr65LSTPoS7(RfGSWLOm`^_#fBBesLBwX}2Q0;!uA`)0+8Hynk81p?uiZ$DmMz5'
    'VgwzwSP6(Fz`mrxcx$!<}WiSf~7mPxWTl`8i>XjnHul+Lf$fLai$*GpQst6<`OeUTLprUAKe*5mB{8NMxJ!L*De_E2rieEp%$%OM'
    'A60f4@>Cbrq9&Zxxee0uTv62$fv4Y9_NoJ5Of#=vQeXq*}=Cf(=pxT%@?=RCy%8!_3v?K!$c7lG3U-'
    '5QMZ{WKqt@^u?tqqHxs|@Da@t(Yqn?VQ3~-'
    '+ZJOGqr#sHaioImE{kynpaFGB2_l&@r@PAB#>rdRx*!0UV44<+j7o!~1<imG8CePKNm0Q;?U3bd@IsjaMFZeHgK{#2{#{x3hQC$V'
    'G)m>k1l<R;mJcAfb&`5L$|yGgidr#{OyLq$hHmiTj9Lv7R|1FUlnxRFnSQN7(7AjrG40uWL3h}Lpm-Ehf0IR9f-pq{nq{ajLY}@-'
    'Pu4o&glVC;007BRY$)sO0{n+GAG|h2<MZH&J{md_i~({L324HS-'
    'B|Iotujm(upvyD3qY&36{0juYGFDru4m<y`3r}UGq;qS*R&$b7Y8}1*wgBC*prVN!6VSk`f`%drb%I2_ACU$+NTNssEG$dJv{|Ds'
    'FVW4EemD|$o9uml$f!eX;R*j&6y`_(O|N$C|E+@0+^M7-'
    'bk#NxeXE$rHS_VD)px15{v1)HlCf*MPfT5{f9++24xHS3wH{kD}<`#(g9d?(Ok9+M(lfJn#B2RisGh}e%7zvqLQPHni3r-'
    'O7K5O{4iyC?DwnXV~4cE3P#*k3zG6{S&h)bLez<+MVw5iLZsIc%MtQYFbp4mxtcN!hPIW%qNWhj-'
    't`Z^Ox%fBB87G59~`3XCqnH~zmnOUbzlfIKUL^EeJs-G8`n!q@xr2GL_vVvE1g?hB;!(2Xg7ygVKrNS9vltW4-'
    '$B+%(z4|+@!P|z;?Mn4q;1qv@`e@*SJj6qZpjW5W-@XSyo#i3m!tkoPr-Jcpd9b9}({wiYYy(sC$-B{a#u|+G_`5T&}*b9KTfh-'
    '|GAs0gKrzzw;1Diy+2E_lalFsajTIreN0!MdTvSXY@yM<JszE-'
    'N6Y33RN=RHQ<OlQI3$P294_2gb?|wsCwrhnP@psozZSU;yNwg5Lk#@e<rmwiZY)JE;>l+@H6uf7Q-'
    'y76eDPV84p+2@3&FBK6~1S)xZEK7+eklk4T6GE;38?Ma0|`11d4|YzAMr6S&YfWO&T%R$znpxd^UmA~Zv^vR`Cyg(HW+jfyf_nGN'
    'aZbpOy67y3Bs&t)c;Y#7@C2OPh08MCS|$71z2Y7cTkmj+p;R&J@dy}}IUdZ5z!<mB3x#E7V198J9sB_r&?MPlf+Ev7Kq$b}H>Daq'
    '7@CQuTiZ{V{=XNo2X4E{5Vm<I+O4MP-zBm483jXT(`f^?=>cs5+N7IzWAKig@DmSxmnBTJo_i2?eXWGxRao@Z@1Rv=PRFf1UwX{4'
    '4)VuD`EYRZvM6>Qp!8lwo$TIdxV?EuXWipYRp<kRExl>(0T=f)M&vw9bxR>11XkkM1s3Rpa&Bwv=Z3x8~<k3>%^S5tx-spyBrf*A'
    'heIwi{HGnD<CC)?~(Nv4U|E-OCOs_Q@AWV7z-'
    'YKnwBEn<+5>nqgCKIO#;moS6q68B1|;@Bl?Q;{z!;Ish^(EGe4dab7+?zT2t$$LY!a*6dH0+dkPMk`gPz^%LK-VMEwqF$Mf$LFIy'
    '#AJ^^Qmf!i_uNC{_modVxk>{+H)=X&%&AC=^8uGRa2_P3t$lT^>gmSNiPUWk!Q(^w5>aU_k5$rg5GzoS>~a=%kiNu_mYAvu&oGb?'
    '!9R)O8T^wn;H2On^ip?g+~PyQ?O`2V&b%%cnp=rL5EDH>?MEvg`d|P>P=Y4B7%++5r~7F=5M3ZM0B0dA!LmW(#zsdKOP$UT4efvB'
    '067rXU}Yv*WDE%0E3FJeFSgJtd6SaFOGM-VdbN(K*e39xrI)t5if={*bE65~0=H7?wMtNhKQ_XEV})6#(tr!ieJKgd&pcgu?t}td'
    'dAUa5DGE05OMpv#XoA$I;|Qt}CDI5_#|5N);OVo};;TS@{fU0-'
    '7EFkQlsjcP3$(qAL=kdE@kWc2=8BX&l6se<Lr@A6=+zY4MGLP=Ic}=+H1yR#M;n)s=#<4@FA|bw#fcTxa&`KYQp6QvDzWu#@LQ^T'
    'Mq4;psg_9cF$35H&@Q=GYNag*8bdH+F!UCf&BWd)u`I}(2nwJmg&gT%wqH)-A+77sQY^Dc2PWdMivWXgR7`slacU>k-'
    '3e?rk8YGpoKrHmK`ZfDKvwp;OYKB@84yceC+z@~<#BP=iWb0Y9B(fGb|`vlU5WxEG90AN5+q2>D@~PE<lqfyG06$7rLlI_m*Xh)q'
    'h{O~2XY{r)t3a%xNNB2WgzFLQJy14rJn=J<U0hJxhVwYIBQCgcM(9XRz0~vWYB7I!3s$9^fGdpnmI`?UzGC-JpYUgHx;g;^&vFDL'
    'llE<kW^OeanPP3V8*8it!@zEGJok-s+?K+VkWs5|D+iP5*pedZbfG{vPK!VD5oW-'
    'V}n%WN+}WHLv8{YLLlumX^{c9KFaWCMQJ$wkoiMt#m!(l`DcrkLz6pX6p^S}=@~d!$AX<PE4L!FC&77{v^wx}mnqakJ&y)JkO#aS'
    'RkkffzI3-+!Ja;Tb~=RyQ`v9HrK%}sH79yfxei*kCy;I-'
    'SWl$UR=U^?I~myaku^gAUe0veerp2Z%A~?d6w>3RgOwwf=A{=vL3EYHv`$R=lWrk}wAewRjh>kdAGQXW<?(ParTD;S<uiO()iS_H'
    'JyF0%BFk&PgC2&tS#fSI%#Wyl&B}^UT|rWqdyKi3b1@l9uckm(HP(7oxHz{!<6_~UlII=*`FxA2B5d`^0Ll6307<b7D^X?`n~W(B'
    'lSlSMZ30(eyl-14k)V^xt}1}!3CpgsYlS8#Qc$pixj9++Rb++-'
    'W@{|H`}uaAw%}@_>S7ilT@QlkNrfA{Be&!%iV%&&@`|U9V27zAC1ps55<g02r4Oqz!v8oEk?5SN1TO`028T&hPDBII7Kx0+Xa%&D'
    'Wu*=Y_sJ8LfYA}0t3=7kHleSVKHQluO(f%_R|#g^Gsz82w3^9VQt>~QNEBF3VkX@25ghj^ie5nDH2P6aHfRK9_E=wFw}_S+FLV=i'
    '+zl3Vz&qRoTxP;W1_FTTna0psDg85AovWP4k8;ABv573W@a(3N{*iD4TIIf9>QMv;WW=<{4RmFH<q1o)A|>1#0N4p5kLc005je&M'
    'Sw0zU=j?$_?K1+@QSDcy^cd@BpDiXhWPnN+wK(P~ApWCEip_hK5%fPIuSVD-'
    'WgZZaYW$^Xd4#V3y62^SE*D=IkMOjtK}+ka$f#+0nhiA~Vzi6H15&vN(Bw+ur-'
    'iYIu@>6ST1m==)X2WPKH!Pki-z4VDH>nevt}+)f*Mb8#R!@ykTDZ98!9p+XVlOjy%Hwv%EJR2(;4JYAS!@wx-je{dYWDULlds;hi'
    'uT3)Zf(s78WQ1^(Y^t`%0`hji!y;qhuT9gApD;7#GMTKy}!=avtcAN)OhQpzK3x8K1QF3uS0%bo{VwfD|f9#?j44o9WZ(N}CZilV'
    '*++4-D|CNF1cY?xS9A9BY#t;shO}|2E_WsQgl-gBTTXxgw3V6Qy$C#Mvd1SuFdrh;owDz34iEgNY0asr`kPqHI$+Vg^=ph$u`l-'
    'mC$|>ZS#3v9YY@sgpYAa}Q|*LR^b)JW|!ytj=ed)j5v@6Qp>g#(Z5C)QJ+MKSLf>WHThB8!NJ2Yl#h^$;im^WfLk!)M#1jK{4k|T'
    'qjA&I)U<6g_uQ)kVz636>3%mCBodECM9c?P~U@~RZ8YOPUGU6Q)1EUf*zeSI5qC0?@&b<=SkUUZIW2MKaQ7%`%X)#Lek!e(!xp~$'
    '<Cv@BPT5-!L=lG4i1*uF5|j}zSAbvT+L2z_7qt(_|fC76*+jKy%Pwhwb48!>3F?-s1?QMjNdSMD8C>PaK?iaB%M!NWI9Y-'
    'J|~q@+)Oo1LEL9_HM6)&PS7w2ldVNgQt)dnuvk6y)C6d2-6kc$*jh};g-'
    'yhECnT?=VIrnBQ~WC(&ZtqTqO^07Wxk{6ZLbSsqnWQrTp}Gk0Yexymhi$Ts-|Qmi^*?``-'
    '#vt2@Q<D^gMCF$&kW@2mZZEK!~ru45aY1IhB3rTJXny*uQgLB3D%7oaIs@(_+z4c1)nVD`ipksbrZByo);6i20#sBR2Gifdf+Ho6'
    '4;f%8S=)m6eDoGA}F0F|HJh<LW`GmL3Zvx0dl@-b>&c=<JyUV}s$1QDS&b;-6-'
    'jWlOi^REtIM!p~K!m1=8O2V+$>>AFcZI6_mktiC}gOIF=0lv7A^q@sva%lt}?RI(Tj8_-'
    '$>hTy<06$bXXWa*8p)w&CgMo~GUJ%qtrt6j2^q&z_!=Ty~2>SWr*%Vp15a&35qDIF=aZ>=;=sRp+$lsPSE2O&V#FT*$HEwMzp^Va'
    'E2`IS}^D!!|=5j<IQ5^_wokm-'
    'B{s`t6@z`PHes3SBmfgV#IHinll<RSwL*W=eN{EEy#(N3c|Sxs$>M%9)8)^cXKlc@#Ec`oE4Q50ME+PjE$PeC@SW`f1$cU!1bR=H'
    '^`-'
    '&ig2zE(}sg!?Nd2Xv_BuE{F~8C*QCE~rim1~;C3P4jqN3EP8^ww8D6)I$}NTyjf~yEv6>iIRjd7$;8eNyzcAQW35BJel%xYBl=OX'
    'wd{oJzq3Tyll>UA}-'
    'BZEdX2^puzV@)<)1nlo2Uc4PV`7ZiOJ91pFzGjunmyzcTqc*A#HN>fuaal(KlPFNQ)1c%9l~#w7~LNBNMGjg$2wT}`Ka2%7o7c8o'
    '|pv~^1(M(dYZ5ijSmYR${m%#%Xp(sD{i$2L%gnxgDiC=?UL`&dijRwf1avUQs&n4K`$KwDz*ub>)?Yj8IWkr<r`l7W1jy}hbeq?F'
    'f@t_xv)POS}=cB~)U8jKC9__8W6eo9HIE%927Yv(i;QD=d{1l2W|p=@M}I&KtO3j$x@z$^x%IRh4tM+78xi&jPnKAQ4FC<d!cWl%'
    'CqkAX)B5d~i>&YWCRM^`1T0-'
    'TlR%gxh=IC|39ofI9#Bif$;C9}>Z#+phM0q0GS_<rm^1?YirG5C}Hz!eCN!dfqkdH))W_DjDSav>lETw+j4C#kD20zXTl3aM6jKW'
    'EKaOvds~@}lqm2Vk5Tdj'
    )
)).decode("utf-8"))
_REBALANCE_ACTIONS = _LEGACY_ACTIONS
_PRICE_FLOOR = 1
_DEMAND_ALPHA = 0.25
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _regime(configuration):
    interval = int(_get(configuration, "townCenterSellInterval", 12) or 12)
    return "rebalance" if interval >= 24 else "legacy"


def _copy_action(action):
    action = copy.deepcopy(action or {})
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
        "market": [list(order) for order in (action.get("market") or [])],
    }


def _seat(obs):
    return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0


def _farm(obs, seat):
    farms = list(_get(obs, "farms", []) or [])
    return farms[seat] if seat < len(farms) else {}


def _align_hands(action, obs):
    action = _copy_action(action)
    expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
    hands = list(action.get("hands") or [])
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
    return action


def _tile_at(farm, position):
    try:
        x, y = int(position[0]), int(position[1])
        return (_get(farm, "tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


def _trace_actor_action(actions, step, actor):
    trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, actions, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < game.get("last_step", -1):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game["active"]

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - transaction["start"]
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(actions, step - 1, actor)
        else:
            active.pop(actor, None)

    for index, (position, intended) in enumerate(zip(positions, unit_actions)):
        actor = "farmer" if index == 0 else index - 1
        if actor in active or not isinstance(intended, list) or not intended:
            continue
        if intended[0] not in ("BUILD_PASTURE", "PLANT"):
            continue
        tile = _tile_at(farm, position)
        if not isinstance(tile, dict) or tile.get("kind") != "WEED":
            continue
        active[actor] = {"start": step, "intended": list(intended)}
        unit_actions[index] = ["DIG"]

    action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
    action["hands"] = unit_actions[1:]
    return _align_hands(action, obs)


def _shape(name, value):
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    raise ValueError(name)


def _market_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _MARKET_PARAMS[item]
    )
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory)
    else:
        amplitude = above_target * base / _shape(above_func, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(obs, order):
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(
        _get(prices, item, _market_price(item, current_inventory)) or 0
    )
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def _demand_per_day(obs, configuration, item):
    town = _get(obs, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)
    shop_interval = max(
        1, int(_get(configuration, "townShopSellInterval", 4) or 4)
    )
    demand = 0.0
    for shop in shops:
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += (turns_per_day / shop_interval) * (
                2 if len(products) == 1 else 1
            )
    regime = _regime(configuration)
    if item != "FERTILIZER":
        center_default = 24 if regime == "rebalance" else 12
        center_interval = max(
            1,
            int(
                _get(configuration, "townCenterSellInterval", center_default)
                or center_default
            ),
        )
        day = int(_get(obs, "day", int(_get(obs, "step", 0) or 0) // 24) or 0)
        multiplier = (
            1
            if regime == "rebalance"
            else (4 if day >= 20 else 2 if day >= 10 else 1)
        )
        demand += (turns_per_day / center_interval) * multiplier
    return demand


def _order_score(obs, configuration, order):
    score = _impact_score(obs, order)
    if _regime(configuration) != "rebalance" or score <= 0 or not _is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    demand = max(0.25, _demand_per_day(obs, configuration, item))
    excess = max(0.0, current_inventory + quantity - 10000)
    urgency = min(1.0, (excess / demand) / 10.0)
    return score * (1.0 + _DEMAND_ALPHA * urgency)


def _rank_sell_slots(obs, action, configuration):
    action = _copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (_order_score(obs, configuration, order), -index, list(order))
        for index, order in enumerate(market)
        if _is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


def agent(obs, configuration=None):
    try:
        actions = (
            _REBALANCE_ACTIONS
            if _regime(configuration) == "rebalance"
            else _LEGACY_ACTIONS
        )
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
        action = _weed_repair_action(
            obs, _copy_action(actions[step]), actions, step
        )
        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }


def _kaggle_submission_entrypoint(obs, configuration=None):
    return agent(obs, configuration)



agent_path = Path("main.py").resolve()
py_compile.compile(str(agent_path), doraise=True)
source_bytes = agent_path.read_bytes()
source_sha256 = hashlib.sha256(source_bytes).hexdigest()
assert source_sha256 == TOP_REPLAY_AGENT_SHA256

source_check = pd.DataFrame([{
    "file": agent_path.name,
    "python_syntax": "PASS",
    "bytes": len(source_bytes),
    "sha256": source_sha256,
}])
show_forest_table(source_check, "Exact source written by this notebook")


import importlib.util

# Load the exact generated agent only for its market and demand model.
# This does not modify the submitted source or the validated route.
spec = importlib.util.spec_from_file_location("_kg_agent_visual", agent_path)
_agent_visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_agent_visual)

opening_inventory = dict(opening.market["inventory"])
PROBE_Q = 20
motion_item = "STRAWBERRY"
motion_n = 120
motion_inventory = int(opening_inventory[motion_item])
motion_prices = [
    _agent_visual._market_price(motion_item, motion_inventory + k)
    for k in range(motion_n)
]
show_market_motion(motion_prices, motion_item, probe_quantity=PROBE_Q)

# Use a real late-season observation from the replay shown at the top.
# This seed contains duplicated shops, making the new with-replacement rule visible.
probe_step = min(24 * 24, len(env.steps) - 1)
probe_obs = env.steps[probe_step][0].observation
shop_counts = Counter(list(probe_obs.town["unlocked_shops"]))
shop_frame = pd.DataFrame(
    [(name.replace("_", " ").title(), count) for name, count in sorted(shop_counts.items())],
    columns=["shop", "instances"],
).sort_values(["instances", "shop"], ascending=[False, True])
show_forest_table(shop_frame, "Observed town composition at Day 24")

# Cross-product view: the exact live ranking score used for existing SELL slots.
impact_rows = []
for item in _agent_visual._MARKET_PARAMS:
    order = ["SELL", item, PROBE_Q]
    raw_impact = _agent_visual._impact_score(probe_obs, order)
    live_score = _agent_visual._order_score(probe_obs, None, order)
    demand = _agent_visual._demand_per_day(probe_obs, None, item)
    impact_rows.append((item.title(), raw_impact, live_score, demand))
impact_frame = pd.DataFrame(
    impact_rows, columns=["product", "price_impact", "queue_score", "town_units_per_day"]
).sort_values("queue_score")

fig, ax = plt.subplots(figsize=(9.4, 4.25))
bar_colors = ["#8B5FB2" if name.upper() == motion_item else "#9DBCAD" for name in impact_frame["product"]]
ax.barh(impact_frame["product"], impact_frame["queue_score"], color=bar_colors, alpha=.92)
forest_axes(ax, f"Demand-aware queue priority for a {PROBE_Q}-unit sale · Day 24", "Live queue score", "")
ax.grid(axis="x", alpha=.25); ax.grid(axis="y", alpha=0)
for i, value in enumerate(impact_frame["queue_score"]):
    ax.text(value + max(impact_frame["queue_score"]) * .015, i, f"{value:,.0f}", va="center", color=TEXT, fontsize=9)
show_forest_figure(fig)

worst = impact_frame.iloc[-1]
duplicate_summary = ", ".join(
    f"{row.shop} ×{int(row.instances)}" for row in shop_frame.itertuples() if int(row.instances) > 1
) or "no duplicate shop in this snapshot"
show_insight(
    "Queue position depends on both price curvature and town composition",
    f"At this Day-24 snapshot the town contains {duplicate_summary}. For the same {PROBE_Q}-unit probe, {worst['product']} receives the largest live queue score. Duplicate shops are counted independently, so demand adapts to the actual town rather than assuming one copy of each shop.",
    accent="#8B5FB2",
    tag="CURRENT MARKET MECHANIC",
)

VALIDATION_SEED = 70117

# Use the exact generated file path, matching the official Python-agent workflow.
env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": VALIDATION_SEED},
    debug=False,
)
env.run([str(agent_path), str(agent_path)])
final = env.steps[-1]
public_farms = final[0].observation.farms

# Count visible non-pass work to prove the submitted agent actually acted.
def count_active_actions(steps, seat):
    active = 0
    market_orders = 0
    for states in steps:
        action = states[seat].action or {}
        units = [action.get("farmer")] + list(action.get("hands", []) or [])
        active += sum(1 for item in units if item and item[0] != "PASS")
        market_orders += len(action.get("market", []) or [])
    return active, market_orders

terminal_banks = []
for seat in (0, 1):
    player_id = int(final[seat].observation.player)
    terminal_banks.append(float(public_farms[player_id]["money"]))

if math.isclose(terminal_banks[0], terminal_banks[1], rel_tol=0.0, abs_tol=1e-9):
    outcomes = ["TIE", "TIE"]
else:
    winner = int(np.argmax(terminal_banks))
    outcomes = ["WIN" if seat == winner else "LOSS" for seat in (0, 1)]

rows = []
for seat in (0, 1):
    player_id = int(final[seat].observation.player)
    reward = float(final[seat].reward)
    public_money = float(public_farms[player_id]["money"])
    active_actions, market_orders = count_active_actions(env.steps, seat)
    rows.append({
        "seed": env.info.get("seed", VALIDATION_SEED),
        "seat": seat,
        "turns": len(env.steps),
        "status": str(final[seat].status),
        "outcome": outcomes[seat],
        "terminal_bank": public_money,
        "final_reward": reward,
        "active_farm_actions": active_actions,
        "market_orders": market_orders,
        "runtime_check": "PASS",
    })

validation = pd.DataFrame(rows)
assert len(env.steps) == 720
assert validation["status"].eq("DONE").all()
assert validation["terminal_bank"].map(math.isfinite).all()
assert validation["final_reward"].map(math.isfinite).all()
assert (validation["terminal_bank"] > 0).all()
assert (validation["active_farm_actions"] > 0).all()
assert (validation["market_orders"] > 0).all()
assert np.allclose(validation["terminal_bank"], validation["final_reward"])
assert sorted(validation["outcome"].tolist()) in (["LOSS", "WIN"], ["TIE", "TIE"])

show_kpi_cards([
    ("Episode", f"{len(env.steps)} turns", "complete season", "#168a9a"),
    ("Runtime", "DONE × 2", "both seats finished", "#2a8a54"),
    ("Farm work", f"{int(validation['active_farm_actions'].sum()):,}", "non-pass unit actions", "#b78312"),
    ("Market", f"{int(validation['market_orders'].sum()):,}", "orders issued", "#8b5fb2"),
    ("Bank gap", f"{abs(terminal_banks[0]-terminal_banks[1]):,.0f}", "self-play seat difference", "#c75b4f"),
], eyebrow="Full-season validation")

show_insight(
    "Self-play validates mechanics, not competitive strength",
    "Both copies complete all 720 turns and exercise the farm and market. The near-symmetric terminal banks are useful for catching seat-sensitive runtime bugs, but this single self-play episode is deliberately not presented as a leaderboard estimate.",
    accent="#76519b",
    tag="HOW TO READ THIS"
)

show_forest_table(
    validation,
    "Full-season runtime and outcome card",
    formats={
        "terminal_bank": lambda x: f"{x:,.0f}",
        "final_reward": lambda x: f"{x:,.0f}",
        "active_farm_actions": lambda x: f"{x:,}",
        "market_orders": lambda x: f"{x:,}",
    },
)

# Compact traces reused by the visual diagnostics.
days = list(range(1, 31))
daily_bank = {0: [], 1: []}
daily_prices = {name: [] for name in ["MELON", "STRAWBERRY", "MILK", "WOOL", "WHEAT"]}
daily_assets = {"Hands": [], "Plants": [], "Animals": [], "Shed units": []}
for day in range(30):
    step = min((day + 1) * 24 - 1, len(env.steps) - 1)
    states = env.steps[step]
    canonical = states[0].observation
    for seat in (0, 1):
        daily_bank[seat].append(float(canonical.farms[seat]["money"]))
    for product in daily_prices:
        daily_prices[product].append(float(canonical.market["prices"][product]))
    farm = canonical.farms[0]
    private = states[0].observation.private
    tiles = farm.get("tiles", [])
    daily_assets["Hands"].append(len(farm.get("hands", [])))
    daily_assets["Plants"].append(sum(1 for row in tiles for tile in row if isinstance(tile, dict) and tile.get("kind") == "PLANT"))
    daily_assets["Animals"].append(sum(1 for row in tiles for tile in row if isinstance(tile, dict) and tile.get("kind") in {"COOP", "PASTURE"} and tile.get("animal")))
    daily_assets["Shed units"].append(sum(private.get("shed", {}).values()))

bank_trace = np.asarray(daily_bank[0], dtype=float)
seat_traces_match = np.allclose(daily_bank[0], daily_bank[1], rtol=0.0, atol=1e-9)
trough_idx = int(np.argmin(bank_trace))
terminal_idx = len(bank_trace) - 1

fig, ax = plt.subplots(figsize=(9.4, 4.1))
ax.plot(days, bank_trace, linewidth=2.6, marker="o", markersize=3.2)
ax.fill_between(days, bank_trace, alpha=.08)
forest_axes(ax, "Bank balance through the 30-day capital cycle", "Day", "Bank balance")
shade_season_phases(ax)
ax.scatter([days[trough_idx], days[terminal_idx]], [bank_trace[trough_idx], bank_trace[terminal_idx]], s=58, zorder=5)
ax.annotate(f"capital trough\n{bank_trace[trough_idx]:,.0f}",
            (days[trough_idx], bank_trace[trough_idx]), xytext=(10, 18),
            textcoords="offset points", color=TEXT, fontsize=9,
            arrowprops=dict(arrowstyle="->", alpha=.45))
ax.annotate(f"terminal bank\n{bank_trace[terminal_idx]:,.0f}",
            (days[terminal_idx], bank_trace[terminal_idx]), xytext=(-70, -34),
            textcoords="offset points", color=TEXT, fontsize=9,
            arrowprops=dict(arrowstyle="->", alpha=.45))
if seat_traces_match:
    ax.text(0.015, 0.96, "Seat 1 is identical on this self-play seed, so it is not drawn twice.",
            transform=ax.transAxes, va="top", color=TEXT, fontsize=9, alpha=.82)
ax.grid(axis="y", alpha=.22)
show_forest_figure(fig)

fig, ax = plt.subplots(figsize=(9.4, 4.2))
for product, values in daily_prices.items():
    ax.plot(days, values, linewidth=1.9, label=product.title())
forest_axes(ax, "Shared-market quotes remain non-stationary", "Day", "Market price")
shade_season_phases(ax)
ax.legend(frameon=False, labelcolor=TEXT, ncol=5, fontsize=8.5)
show_forest_figure(fig)

fig, ax = plt.subplots(figsize=(9.4, 4.0))
for label, values in daily_assets.items():
    ax.plot(days, values, linewidth=2.0, label=label)
forest_axes(ax, "Operating capacity grows before final liquidation", "Day", "Count / units")
shade_season_phases(ax)
ax.legend(frameon=False, labelcolor=TEXT, ncol=4, fontsize=9)
show_forest_figure(fig)

# The live replay at the top is produced with this exact call:
# show_farm_motion(env, seat=0, stride=6, duration=18)
# It is not repeated here because the same animation is already the notebook opener.

movement_ops = {"NORTH", "SOUTH", "EAST", "WEST"}
crop_ops = {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}
livestock_ops = {"FEED", "CARE", "COLLECT_FERTILIZER"}
logistics_ops = {"PICKUP", "DROP", "PLACE", "BUILD_PASTURE"}

mix = Counter()
for states in env.steps:
    action = states[0].action or {}
    for unit_action in [action.get("farmer")] + list(action.get("hands", []) or []):
        if not unit_action:
            continue
        op = unit_action[0]
        if op in movement_ops: mix["Movement"] += 1
        elif op in crop_ops: mix["Crop work"] += 1
        elif op in livestock_ops: mix["Livestock"] += 1
        elif op in logistics_ops: mix["Logistics"] += 1
        elif op == "PASS": mix["Pass"] += 1
        else: mix["Other farm"] += 1
    for order in action.get("market", []) or []:
        if order:
            mix["Market sales" if order[0] == "SELL" else "Investment / buying"] += 1

mix_frame = pd.DataFrame(mix.items(), columns=["category", "actions"]).sort_values("actions")
fig, ax = plt.subplots(figsize=(9.4, 4.2))
ax.barh(mix_frame["category"], mix_frame["actions"], color=PALETTE[1], alpha=.88)
forest_axes(ax, "What the controller spends 720 turns doing", "Action count", "")
ax.grid(axis="x", alpha=.25); ax.grid(axis="y", alpha=0)
for i, value in enumerate(mix_frame["actions"]):
    ax.text(value + max(mix_frame["actions"])*.012, i, f"{value:,}", va="center", color=TEXT, fontsize=9)
show_forest_figure(fig)

min_bank_day = int(np.argmin(daily_bank[0])) + 1
min_bank_value = float(min(daily_bank[0]))
peak_hands = int(max(daily_assets["Hands"]))
peak_plants = int(max(daily_assets["Plants"]))
total_work = int(sum(mix.values()))
show_kpi_cards([
    ("Capital trough", f"Day {min_bank_day}", f"bank {min_bank_value:,.0f}", "#b78312"),
    ("Peak hands", f"{peak_hands}", "labor capacity", "#168a9a"),
    ("Peak plants", f"{peak_plants}", "crop footprint", "#2a8a54"),
    ("Observed actions", f"{total_work:,}", "farm + market events", "#8b5fb2"),
], eyebrow="Trace readout")
show_insight(
    "The trace matches a capital-cycle strategy",
    f"Seat 0 reaches its lowest sampled bank on day {min_bank_day}, after cash has been converted into operating capacity. The farm later reaches {peak_hands} hands and {peak_plants} simultaneous plants before final closeout. This is the intended shape: invest early enough to compound, then stop treating inventory as wealth when the deadline approaches.",
    accent="#2a8a54",
    tag="MECHANISM CHECK"
)




archive_path = Path("submission.tar.gz")
with archive_path.open("wb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as archive:
            info = tarfile.TarInfo("main.py")
            info.size = len(source_bytes)
            info.mode = 0o644
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(source_bytes))

with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getnames()
    archived_bytes = archive.extractfile("main.py").read()

assert members == ["main.py"]
assert archived_bytes == source_bytes
assert hashlib.sha256(archived_bytes).hexdigest() == source_sha256

ARCHIVE_VALIDATION_SEED = 70123
with tempfile.TemporaryDirectory() as temp_dir:
    extracted_agent = Path(temp_dir) / "main.py"
    extracted_agent.write_bytes(archived_bytes)
    py_compile.compile(str(extracted_agent), doraise=True)
    archive_env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": ARCHIVE_VALIDATION_SEED},
        debug=False,
    )
    archive_env.run([str(extracted_agent), str(extracted_agent)])
    archive_final = archive_env.steps[-1]
    archive_rewards = [float(state.reward) for state in archive_final]
    archive_statuses = [str(state.status) for state in archive_final]

assert len(archive_env.steps) == 720
assert archive_statuses == ["DONE", "DONE"]
assert all(math.isfinite(value) and value > 0 for value in archive_rewards)

archive_check = pd.DataFrame([{
    "archive": archive_path.name,
    "root_members": ", ".join(members),
    "archive_bytes": archive_path.stat().st_size,
    "source_bytes_match": "PASS",
    "sha256_match": "PASS",
    "archive_syntax": "PASS",
    "720_turn_archive_run": "PASS",
}])
show_kpi_cards([
    ("Root files", str(len(members)), "main.py only", "#2a8a54"),
    ("Archive", f"{archive_path.stat().st_size/1024:.1f} KB", "deterministic tar.gz", "#168a9a"),
    ("Byte match", "PASS", "archived source is exact", "#b78312"),
    ("Fresh rerun", "PASS", "720 turns from extracted bytes", "#8b5fb2"),
], eyebrow="Submission integrity")
show_insight(
    "The file that is submitted is the file that was tested",
    "The archive contains one root-level main.py. Its bytes match the compiled source exactly, and those extracted bytes compile and finish a separate 720-turn episode. This closes a common reproducibility gap between notebook code and submitted code.",
    accent="#2a8a54",
    tag="PACKAGE CHECK"
)
show_forest_table(archive_check, "Deterministic archive audit")