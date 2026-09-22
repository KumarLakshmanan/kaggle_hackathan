"""Public replay 99616684 seat 0: Blu3s; RC5 execution guards."""
import base64
import copy
import json
import math
import zlib
from collections import namedtuple


_ACTIONS = json.loads(zlib.decompress(base64.b85decode('c-rk<U5{H=a{Mpz%m<U48OeFmO59jj*<*~PB{s&uFpv!b1e*sZZ$bWh#+o5{dAqu*y3eI7$9@t)aqd0er@Okk`iK9y`nR8c{>R^czWS#huD*Zu{{7X%>gwNr`p<v;ug5PQKmOyVpa0|U|NZ#+hpRt*{M(P;-`~CY`1-@u>T3VZ?$zVJ*AJ^7uD*GDzq>m7@XK%C?{;q<fB5b0-Q9Ors~5Acpa1^$@b#<j-hTV)-Q$0}|7N%Qo<2A<;_HWp|6QGR<n8OfeEk0GVaHDWaJApP|M2Ny-`(AR_~z56=bj%vOgo-E`ZNITN2g;td*`1%zJ2%R$H%|_@bS|yOkQ|;PpdQUUcKHOhw1FWkN@@EhvW2hU-0K&Ci{GZUVYfzKmBodga6#uukwMIyup6n;jb4T05WyUj0Bm&<6`WLNSwJtE1y>Br{^ACFfws*7)~!3n!xvW9|u+hnYcJzr&ldAaf=KI*n1-jBF<cFTxT2(e*^p9dEj#|@k*$#SkS&@7Qp}Oqha@|JkWFNW7@dq#kbT&ZCt`P*j`ybh`~62bTnX)iIhEi-i5WYHJ(4!&fnuwIRC&Na`*1t?)8Ts|Gc~Z@b=x?fB7^?qb&m`c%x}?Z6XWl3mK<g(}=AyxhAr+xoND0Be`}{obTG>`7khc@sYY==qL}5d1`&>egO{wtsiZe95Qe&hljkmzx$p(<oV#H4?&*H``x==ythe*e>twuF}GF6+%_}p&o6J|5Z}yS_0)a7b>?P%-x-u<oE*aKYzW_fxPP_()9(KMZ{WHBojc6f{F;wr=e&S-*I6fii!X7}XScC$I9JYT^Y)%UyLTy-?lyIOgHu1=b?%k}*H!P{^RB1oPlH$cg$7Z!?NUb2;Q*R!@9DWT`?@uTJySu9;>oWH_)gcQJUvJ^k6rZ%8q&PwD}(0T^V&8wjI{Cj0}Ye2*Rw!MHic)>!1Jwg>n?>Vw=J;i6f)mFe3@5q!Q8Q~X}J$Rua8}5nC)a2E-mveZd@?v_+M(I^lfDO+039ZuHxBWH_eubgK^pWcX*ARuHSGG*X}v=Al*xb<jxV-t~oFRDtp&1YfO3ouiP7kT-9&_jlPgO)*le_j(xsaF6Is<*u&?!VYgqXIdG|q`52~ueYdyn<l~#4|Dfc^@XHze@AB^Sf*^0@W@L_F<!WTN&q6o#JeKq&jMY50_PB~)-T&2ZDD<E|1=D_6#%H}gJ~+kHju9m}rq8b>(BZ(~9%E?76Tan1Pwu)5IxSu4J)i_MY&yfIM#Aaoa2+}`!mPCAb`1#T%2)xlZfkpmIu)HbR5VV|xuBmz`*_?01`722M{pAqo-@C%ZqiE_7#g4A(a+yc?>ll|*M02m2o%0DebRos!9>tk&5PVO2k2Lq@adafD*5}}PBEU*rDkUNUUcw$Vy-l2XL|C2Q#k#$GfTCYK)m+TA1no591Rx42XpRqHK)h3`}iU8r{fRNAe79W<CBgyAHp^&gKEMqu`h)y47_9h*YZ<?$6&SoxLn4=7U|GHW?Ssg{H892@uT^3L{Ltx0AKk;ksfdZzX4-i;euTE;gglekx7iHf@xN40vwTK?w9U<WcSQh;^u-q9|8<*6si+B>QOmkgE!d7{haiW)nY-ZstqOWnUiV4Aq{RejhkvGyCE7%=&ME?0$XAG)G%wBXo)$(eXt=a3`&~FLrczO16RcXP21nyy?agqLw%VeRpP=qJgrJncy3I%ukv^wCyb^i(X9!igYXQ(x{pmbwJH+j6MWK&nVikidXr&1k;FpdQU*VEHl;7KmQ9;4n}-3y@QJizgXiyhip@NYRSn8G9+JeowM?$V+gIKMM{@(1lX=WlSRALlT?){B8qyopsyJkl%k${6y}2sdKXluX*^<X%+~S#I(R)70E+Q|=58?jl@f0zk@2^1-g|EB3jCi6g#Wl?uZ|$~D8YIZ@8p?+|->27~$AnJ~-pxZVI~zD6Q)6Qn&ff6*4pT60d0<w=Rt)9_o&NlIWFlj6egq6BE~1l@o-<F)Gx8b3fdb4Qm=2D&o=o^*Y`4tNNr+w1K`3Sl#RDZS7zCGoo<)>&Th6StqE4nQehX@loLgs2B~DoG<JG5?EirI5NCu$~%XNZaEIM9@L6h^4dF}<cnqG(8c?Kz40Ss!c=-nLoXE|u67WL1^_<RsrL6pdFhA(?cLR%+kYwt{?!HM=E%%ULjFa#?aIZ<A66{WVOypZz&7q$&dD=3I%FvC^`6=k|=zUD#dqnwb`df7IK!Dw03b8^p3?oEX@a^2^M5T$|_CXNO0bK+dzc*ggQO(Sq~U*bgstehCIZCU6hw1;k8^LG-bC%cu}&*0K11w68?S}?E_AYSp!J*kL+utlHW4}vDqYG`#jF2CcfPT^7DQMHm^!0YT8On#Y!US!WL5jBqZ2h#-7bvj!hqM5+sV#aABWh?ko$egDKg0x8E%3ffvM`NZT*#Qh8@L-Q1RC+PEP#nCsldBAvMZg-Pl%^7!<dETk*4W9{$pQQdx0lCLlBE-aV{^_>ji^LL=Q<%UOzi2*J>x4y(09%&s^bPMUnOM?kw(>9z{UV@RS*Jf=JPejgTK;eUA4BN?7@r0$>dq&Z~HKm<#nB5H}Hq>OWRYpNi||9MjCyX<6)ON4=8w|-wFH_;V{52y|AC$aKKgs_6&6+I%lrWk~t2S|0g4XRzk{Ik$kKovs)XLXnLonE5h_`eh)D$eWU*PCvV>VGqgKv>kz*L4THX~$Jy>w)W-my)`H+=ZPu8>6px}vr3TKXpBQEx5IC~|xE&R!ffM#@+Q0NbDuWRxKqVWn*atXQJBf7+C?}+(ily$n6da1wfbHZ$P`WET4I3J^9+YFBhCa7Ri^$uo*^E_hq{lew2~V`Jtr5vk9@LaRG~+2k9NC`5xMZm-0l0|UauenhzEa8vPt%sp&pNrR{pM!2{&j%^!(1WHb?WPa`l-2tu@tkS#kQWCkh?p8A)+%EL|)U04lA=Swzwe3b+Tk$HmS3WLPfio^DDfpCUZ(V5W!mW6r8jW_fyZxN3Eh+s?wV6CGfgfGqG!EY+;pHkuB%h&Oiji%-gN-Tqo_P2Qw?{0Oc(DR4!mFT1VCMadYb!9Kr4aLv-u~Q9Ml&sF+h9+v_o2?W7?VQw#(Hn>o|T2x6&d06WM?yGAp4D*Z^vR%~AzXaeJhhWWJUc6@j5hjd$j_XWrBG+(h{bm6n$O1cA{@-|j-NBhuVgf%qGv(rWt*&qukXUA*7Wc{+~$+u3)AW&Xnbcdo!mt56k%vs~*+F_ZH^fn5*V2nY4a7WtZ0Sh9UInYXoTLG<ka1dD;nbWPD+0VV;9<YmmIs!Y;&>sTS38i-?2bJE^_1l_drI^rkjdD4hkYH?0xc4Cx4kEIO#W^nj0eXOK*R!23WhwZKj2f@(Xry@=mYju=ttU?`O?}+XLNYO2;OJ09By)sW^0}a(GT?KQl4H@;ML?0`Gs4kqrhdL`Fa;hb>HhA+^WP$|%oVFR+fn?LxDkVk=vhY2Xf?<#2_dTu)Vn+d&P3ObZK9D;8L~40r>vAGOvEHtWzD~acAX0Pn8F*a-hmky*IQABziE5%R3zD3dq%+B2@ZowvWV|H(y6V?iL))LscykKc%DVQ9b%Qz$saGeIk;C=9_VIPzb#`eNF}H7LO3V6j;5|$d{~-8UNX)YL6@Qqu<-J8BcHE*wUy$}3KrW&?F+7|3EBX@f@_H5jh(wr5t(DdP*-@OE^`jSAfR&3^+{THv#nX5`02p6J?OCy5N{p|7`J(bp}mln07!xs3m$5b!b+VBmc9;5#OUC)n4pJ!LD8YeIABy!C?7S}$`acQB?5(JfI$X)p1hcRgX~KT{s>NoHk>XieOYEjOxqFw44BpD4`~irS$=(Cs|I8YRZ_x_llsvuUd-frCB4>=JE{(FOT`$tNO>lXBf=`i*cIp~DI8sxspKXl_{=1M|Jf*tos6BsSEx?4RP~EXpWTwIV?`}l*biH352%tgQbjm(rz%(Lr3yhY(Rk~#6n)cMTtJ4lbj`DXuB+7B3HhT09c74^ZuXGp!!{CSieV>gh(~s`q|k<7ZY9jh(mq*LO;;@`nsKE#Z~IDuyN`^VWqT;wKrr@^X>S*48X&ZBXWDaA$9Os>#{kc9X0I=SP!#V$;J<(g?rA_Vr;z2-C|FyoAGo-=u@~s*og=k*L6NRWT-cvhZjY~G%dmRp`Eao**B9yOsPOEHM*hE}{_7cjj5fe3itKl(RE4KkP-OqCdcM%sQ+vJEDJ7PleC)a{ny~8Dkd3nxy-YGmrSi7lzJ2!>KsgaLY2k3z2i|g?t3`Tk$0!bb9Pijdl3*34f4M@#zhcVL1qmxORITNb4Hbn&X(7aa&(Q8pG+}_j(H_vcw{E~AEJ)3j)===KBUdmIayIM9j8%adWn1uQ7$dX;lWoXAs{;lMtyw5rjitf3tdymS?f5H?x5o@9w)gQc-+@wl=;AO_DjH-4@BQ&tx!1EKMS<;(I{enq!c=Q>$>8s<IC@3y0EJJj5USr)FYeEHqO3g%k6J8egh~flZH<x2PT<o9%WDI<_mIbhrT>%+6VZXpb1HhOm*nyX{uUU)6fNkE8Bb70QR-YIW%kVg5HT{Mq=B}M$|XlvqF|_AP~<!ib;9GIhEhH~?*XXj#l$qZ97eow2|?X{J}-PB8Om#|v91zCgkE_BLD2tfJn43KC~lTqX4cJJK@65Vl15_rwNSX16Jbo^i?%cs^2t3V6vx}EmyHJ7s}$Gl`^5#hf7`aF{yMSWxwpPxDWaIPOgAR?*Bkt7+k95LjrvCv4)G(RBtj)5|7qfoNgP<j*W}3)LWUo&-t$l?A&nTOz)IRTN%dNiGfjQyO!mJ3QxRT-Qs{HbC?DcSkQ*}_e{ZE_lV(e6IDyclq_9ZL<8-(xE6TGub);o&*3STk4rEOUB)I{7B6l;aZs64CJ76kYI$bXDu)Bod4=vZ>m1smZO^pP@1i~%gj^Pbv+@X0R`G^T)zSCeAKiZS1w~tBDtK4Uj)o35SC=W+f&;~cjG%Tu66)j~fEIP}etq$8L+5NXAeN{fP$T0?uH5pdc(Y5l%pAa99AEE+lbW)>6O0K&RftuJOP-;%79~`tK)?Z4p#De0jB1IyBQato#5TVItCB<i+&e-iRBZHD5>DF`5DU)2c0Sj>3L}$#du~?ud=Bc*~&#+(!ta7a!?OktyL9c6}?2O2nui9+MIJBehB<P?WUt4ImCaRh)AA+XVy!_0ZXX`45ehllxxK2oFh)W&us`D09JSzzyQ^B0Mt4@3X+UE1wu}!QO100iy_(Aa4*A<S8g1;cZaCVn%!tI8>DR8FF;=$;uh+YA$9zMoJBRr~(7sNj?748zYz!JaYIWF<d-5>|Qc`*Tif$6NA7Q^`lErX}E<DZmwh)6^oMPo~yyZ5$>u*o<b2s5wN72tw143o_)&!;2C_W6J(60d?{H6%6$7;Mbo$CCATa3<JT<lodv5XuTKrqjX7Em`u#Ptg2z=+JH5@z^A1$)N%p4N{fZd}{FPwGhCf<p&!q<32qXt1{Bqla2W!3N<xs7=nvy_hS|^rJX4|>emv|hg5`!4pF!d-Pc5vIc|}|H*&HfNtk3=aWevV?^c2E-;ufpL}0cWy4srP7AdSMSGq$A0!y_^3Nqlf3rl!ZSrcX8=7wI~8TBc5#mkhT7>kCM91WO^)u}b8L5$d3wwCJv`<d<d)x$WE$TpVY4~xn%1>B}k5;(*4nC>1eiB(Va9ONDC3_$0+bA8u0orAq0+XKuxj)J?&o3!52<Yl4{!&-iZwU<wXLFWmTOrZ!bagPePF3Ja?fRztYcs<qVoDq((u5}mEC2)H2z$)Kv=+&8rV+y@{t7rSrEywLwJ^@3W^)2y!*jhQ%vh=wW02Sf_@}e$cL`j+%X8vV{7S66fzNkhdBKpUx7*ZQG6`2`PYZJh>PwFwZSD^-iUmKZaahYk(sW;Otm`rge&#%Uzft`yu-D-!AGJHVwz0hnURc}~gh%4H}#!&@RMwlp#Xr{E1oU7fD&ar?~BrN^O=v@5v#8!ybPE~aE*O6Ue@Jg{7k5zl8RAC2M%yQ+IRa|URL7!sdv7a414U6|&>&K#E8g2;@n)X&C$0W$gW^sWHY434-Wx#z_oh`8+Xr^INXM*bD8r<20ywThWcwn(Yr#%TJCWN;UXjzk9UG_y~lBHTL<0@r?oO-&6I+wI2qv-~QPQ}wH^yT=Q?G&~mNrDyxp-Mh@{o`*N$q#X7a;MXx<O#+}$?SpqlbK@7+;N9Z#YOF_^?VEEvRa<5(t^Ic%&YLwk0>DFvILSkjupj@f|?9#IupoXnc36h;MP4RP_&pq`slhpHWPHl6uCD2*7GiETRkHI(fAK&yT^YZ`!=ymj9C3frrNUhQb)|DL#{fpqNu)#_`teQ5H%G|a!i)&ozck?)>D^Sv9&-*tD<u*r%}3Q<K#rSVyivV3uX2!c}Q)Inee{<!YMf>^pgXyxiqthoNSVE^ca0pV+7~22OiOwd=1y~lvY^9W>nL<2MD3F3nmPh8nnx(5*2yI;H)7rA-DD^u?WWE!q^|Ng;O|oL>Nd5W%^*BSF5vn31sG|w?VGGT@1ryM=70)5kXn>X8NC=c=S^0sBp<LRS0u6bkatqM@HZ6j7$)mn*mS;E+jJ{zt_Bqjg>@;hPV%YxeC>+YOh};$!4IjC=4rnMd*&bs!1qj9utqKh8e_&Sj8Zw&XsX2S9Wswy3NPL>xSl$9X0}(kBoXVS_7ISG{*A^3YJs~ZgC}w0_O&BYUDj@SEsIFyNPwf2{|@d*SyOT1{Oa@Gbqv}?Z^|A98ei$tf0h3Wz<X`$L7rurD0vl!J%IpT)7qbrsx>ZSiVprW7WpeW2!FUPPe9-C84)QpFM6=gMI9=f|#^Yo}@*Nr5jC<U^KD_Gfd%(n6PD)Gc#3*)Xg1tdY)3ZlIT@2rT4c^P0F>0Bx$KDezaZme>M{0@{?{NQ*pg%f?-~jO;!)cmQC7tOaK$^%5niHF}$FMG#E>s-Y|2kR7urjT_c~C;6MQYt57^D%X^wv9mQSKwzUrn`OIsPB3Dv7ucdA<dJ|ZQ6V6a?>8K2@<rle5$MDujp~_eppY<x`w3M<g#&{BBJ=|kP`XCz0&hi)`G4Y)!VK_1abzspXFF~<z5M)t0Yb1uz(ninoWk7+MTpl^=f}N_`CN>Fzl3Us?sb*dg(Rs4dV`8&?k)mU<0=bEy*jEAdrw-jbwE0n9CL0Z;z($|Lhio!Rq$p_t*crh>`nZv7+GImnN)bc?hTX6t+i)zaQ;Q<eu9^3))`>4k+O$bigfp)dyQS#1PuTUDQWQl-EIXZFMeZV>OW34AsVgIQOqu(uj4B6hZ`YXulW_bBQlXd#zOr~tAU@e9zflsDf#mr0>RmMGBEZx}vRWP3X?syDiJkYgY}20D5jJZ9Y{WT5x<5;#nKK%cVXL!TZty21R4z%4src7QPc?sq#YyAYbaq@Ed)&x(byQg_06})=<wL8YunK!-&`ZHRccoUjVCVXwUy~TG69i1{yzCx<#}3m=l$Th~Lb_~qZxT^X7DYxa!Le6(1hlnI&Q2zoBvUIcFSLhz<`gGiFwlv+4B}p>ERV*W6<q>8zDn^ajpP{Tr95Fk-6=o%Aww!uv6Lok)(KM^OqhymhbG(~JogxQ1krZ2^qV^Jls^S=SDv~_$%U4nf7Fd#Bvp1TLP0PEG@&G!yk|#>*-4$*6zX57fPjsfGwXXq&a20sw^=?s{OKi|sAU=bxtDDzZH6{71H`N+r;oO%zDzSE_Kr|1z`io4!=(A#)+Df#eG9lqFcf@Ns3BLFqQXUzs<);kOX%4a=L~}9JYg{hKEU)HM?nOXT-MgZ?^th}1t!g!=%hPU)s!ffQmyJ{MNW8j;<{F+U}4Q|rOuNVQ}3oRZ)(-vqCrMi69pASU2d7~zEm9@r3iujDtm&8+SPjdi^A)LnEK8Uk*SdYoNZkxL#>11Mm?)$)u@w<fY`q#v0La5QS7m#rcbj9DrPVDzg$^5=JdC0-?dQzb}4x^=#7okOXzD)6*4a3IB_kCuM4GsjqS^?r<6MdqSDW-5ii?`uMSJR-Su998FEs#2&+6MkrFt?bV?`-ARfao*;f|1+ZjsjvS#AWiZjnPtj>yXz?jX$uu3G8qV;NW7(&2p#U;;v%K)-mh>605)M@26HjP=gtAP2n6*kIspn>gEE>YOfY$B%(xYj2v0{4Y(6O)6ZrXS&lGRf!NySwk0!p=g@9`OH}UB%aGn~+2-LuwJYPz5<os+vc)%V(1<>s8^C=%@hY6t)vY+Ie=O0e0(1F2fi>K!oYJ?dObGuzY8F?R6BZpcKDJ<Vm8|p=Mr+8L1#HPB@~j!B&{*<JJRvJdTZ9fy<iXKlH|&YJPo)GKNjo-Kd?&v8f@fMyDHzQDX{X8vWwV-U7){P6}Ey$cj?t&e(EdoS$^YLeq5yVykF-kN)QJsVs?*uDXiw%v~9iLUP@3#wu0+f<Ut<fkbJQV^T<nhUzlO-CMB6M{O+Mh~xMTvM6}X#cOEqS(ir+F|o5nu47J3qd7-4v2RQHtDOVWxKSc~P2l?i7b&xRw|$NpxPW{%8?)dU?c>vW8xOB1{55dZi)$S3Wu}hrGd3AnEn#b=TSj=VT5rwNGJnRxH^WtzU<dumotD!G2E|xfItUaQeA6e~6o4LCZ%5b|tj<9dtU3?-IY&4*CH-@yS&M6VWrSQ|5g{yy54O{3m~si;q)V_slOlC5yuj&Fa$I(ZfivFFYGHIYXdZ-mg=cUZ<|;q^QKN&`#`neP1#<UPq>N5o6v&VGaJ%y_3&^k;SN%hO%+2AvHc=m`wp9uY@C8B3CX5tvq>;7#t^$-*z>lRg##pGZT^O(!#P`&gg#J_bpLk9FDoSHI|A!cz7m*h$dFu=18rD!7%H$BnJT>d2IEax-PS!7%p06vIc-yX|Ar><qb#4ezAIzrxGAhX0M={HPaz0C;6y-A7Vfi7Z3OZDhOig_-aG_BJbt?T*K<UW7A`o4&yAs_gi-<0*j*U*m^i{)Dkw`Am$CkF?rn=W%TnWm%W{TAed0eC#BFNhHbK-$BN1&a-!gUqNFNV>YuBb=1xgPK+9Z%CHGK?#WG2RB+c}_}c!t3iOhgr!Y&{vK)YFX;6ED6RaGXS`8_)m?@UFxJ;I$@TOS?oqG);6k^hx~SB-2xs;@WELP!Z{sL&cO>~H``fpu}CW;9h2&c@n#~J(b-{B5v~72B`i>x4Cya3IdMbTxL=C_5i50xa*IV(uzi)-z|tb3L%LZv%PR`mFiM0MDlFM9HVQ2+Tu_m?)${m?1#~S}T`^G@>r_}&(aFHU?NKC_sJR%LqI??<4jbp+6~x8-ffqTG+z$=h1HU$-hIs{}fQ_|O<o78DW(h}z18dpw>8f**78^_)TSq&fZAd&?fq#t5LNiyZ8@?zy=JP;J=$K8Q+8qtDBHNf1RNl-y^0$dcWUOf}7e0C6b(&n%AUA^RJ+1<^@C}yNc-=;Th8aj@UBwF!JyLoaHL8{_>u47ocKf`T%%IEPruVd?1!pqA4cGI@%^6^O)|um8VL?X(pyOt*TWa+@vQyPCFjUG427;A??-scf)OeWA0#Yo)(MfQTYF}D)A{o3%3>;<#&A_^v;0)LVtd=5GU)x)SFD0AlCR4vN8C&ph1WTQ>wj#Dh;X@ww>!5Kh<o8R%<f6BB!E{1hwIdk<f#(LwR_S|b6EY@#E!!~rU>tWVRjH?p5}N)u$*Vw*D|Mwhp^2DiqacCfv6nN~O8V<rU+U`5$|9yTDH^V)=;D(_IABx^=3^;HvR=<;Z7;#nsX@?e-fm0MY@k<i8$m0Mm7v6Jj~-$z2a(GnF0>H}j$d<0Wfg=kQ=pPolb4{QpE<W`gpv^l#-B2t!ekxaJrPA#9>5~Xnt8B2p+tCEuxv|@sWk|CaBM{sUgQa_yHcJ_wraUrU)1&cdhzXRv(@%oW;Ex*)<9g4q!tNkqM|{DF0+J6-7-l0k=cPBFO;G#7IAgX`QoXav|<in{D2=hB^b|{2T9XswyH9yeG)O#>=D)f`ZfO$b*4l%j=lkMe27*Ps{~B&{?mz*ko#lKo1dx~;SyI$)=H`wVPf*^;Wn-^l@5$4jkSr)S3+ZfUh8?q45>pyLCI-vQd4MM8niDdAI;omzbg@~HtOYkn82`)i{bw6!$H3l$ZXv#1|qq_TTBqj(&9=VUYGhbL89oZQglq95w$GE0*bb6<3@+8=y|#5l9#lixFUtrX0jyt<%fhpmnXd9nRd_QM?lxi(Yd#1d3`Q|EILQnA(PJW|8!A=p^QHm-WN7JWy8>#3c0w;l7u}9w1fC>p_pKfSxsiH${;%$z89&e$pMcT{k8d*j@hyh^(S|NxmX$7R$vUYnt4gSdt|dQ&~4Hi4}0*Jsps<@FY6NJrkXAqrlq5<S4q)bL^jPEd!=`|XS}G%bG-V0NohP=VJ%VlT&lpV1N+0Vi<_VI|3y=a4N<x0h;v~U&0@w9%Ql@|U!1@zK)QF3<anzve*|O%)(gQlb=+!vUR5uoD93(j`89kwvg}4iho9A7EJ^N6{U#?p@Ti<rjc@pPs8x%G=dbc0SXA?JMeV>yEETb2wOHsy%cQ#8xFA_Ut-6|fS^v_`MfUEc@=RVEP~Ez#FBc(I@PDkJuvJ17FJ+lTev<;O;BErTJ$!XtP@Rhv7fk+QBzV%e1IX%dR!DkFgKn?+SApmNK*z6s&oy4XLX<pDUndn`nEtq6X;`nC_|61)wVk<4iCDW(8;`kIT^%e4i*115%-SmKUZQb!NM5KWY=r1@MRwS$_<-u-b5cP>saTe<N6ml^Pi?qng<VLN3$oR7vn;yf^8&0C53~2YC<eh`XkyZLw$pOOV_EVZ5ya-;SBd@nWQDv~xHN1G*pyP@bbv=L!JB1kxtbJ0r}Vlxa|@PfrBpquTp)9^O2?Nd!0MJOYLFB)G-?-e94Vh_N{m<~<??wgX%c4O!cY;_VCv8k8y3BEUoVdExoWAh0;24kkY(zfE^}7U8Ubp+uhy_zj1<^4T3PBN5KLp48uL9>icL{Xl$Z)a91AnYk&wbmQD6|IA=Ou@uM_c(I43oSz(+KV*mkdws%Ku56H{yK*Rcw!tndSvGeS|eQiy#!$t;>mB^~3y1A-)yQk5Opw#u2BN|bqObA$%HQU65uL+OW_I-O?1rLf`cAN)^~)~L&Te{Dm5H#Dimotm|s`owZGDaSFr-%4i2ST1lm4Vq?6^@?LOQhlAYWsXgx#tu0*3@OK6Emk+*z(ZR<a}ibnS5c`N1OBPWBf082eyHBS5-Lk(nJTT$ph}9CWU5l`<IdHXSBm)vYM_g5iS>=L&fF5sjtG${I={UTUy-8~^izS!Y^r<F0<BVrjGv80CEWV$5($NZUqp3;c-0S#oNP2i?3ZQ*ZEDd51(V6j<jd0Eo=(e~COZ(qny!!>#f8QWADZRLQs(#dozST%lNh;hT;n-u9yb;XPnNdK#OT(ASeLR6Tp2=k0t~T}5}TnU_q;PJtGWa%Hj%d6PrEiuj>Xz@WT1zQklngcUX|gmE&@htqwJbFtLsrB9FQ`!cyO!&&cHlHs^7H*wtIv)5B0gRe)aO9#kMrLbPUV{^D_Gpg~mCXl269k8u_Bn#JK~%0&PwnxDFw#B#~!v8M)?_O*mkYK}Kx0*aO+}DXWtun@lLxQss>TsYlgPy!E@V9^N0$f|Onu9vLBD)`$nX6%<+eYex~-+$J*hK`<jIPEbG(e*MM4b3RQ?$U-+rTufn=rtpU^+$ozTc?D%GM#n$xH4M(clScB+7Kl$*eF*^bPP~`K0^xKS#a+rjxMy5(78a<UTVh_7S5rYBO`R3{%dHu4dkVXr&Jb0EgZ*S|J(BNJ+aBAls}g<Kn?;h5sV7S_chJKPR$1T5W!wZ>TH2#~7?h}uagvdoDjJ0FZ$G=-+pq<0PtD#@!e@i8C`#TmO;?%+mpIP8n`KtKBUpYMOC<y_Ok+jl9dY^w1ouhp2GE=1|0$_OHr+?9u&+3d(_H<FoYml0$7UPCc{!Oarmo5#)1wVoX`35RJw~HN;=Ff6YEMI?e@jWr&m(|_bde8qU2d*bbIzkZ5B~?RnmZr')).decode('utf-8'))
_FR_ITEMS = ('MELON', 'MILK', 'STRAWBERRY', 'WOOL')
_FR_STATE = {
    0: {"last_step": -1, "due_step": -1, "due": {}},
    1: {"last_step": -1, "due_step": -1, "due": {}},
}
_WEED_STATE = {0: {}, 1: {}}
_WEED_REPLAY_STEPS = 8
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


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


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


def _trace_actor_action(step, actor):
    trace = _ACTIONS[min(max(int(step), 0), len(_ACTIONS) - 1)] or {}
    if actor == "farmer":
        return list(trace.get("farmer") or ["PASS"])
    hands = trace.get("hands", []) or []
    return list(hands[actor] if actor < len(hands) else ["PASS"])


def _weed_repair_action(obs, action, step):
    action = _align_hands(action, obs)
    seat = _seat(obs)
    game = _WEED_STATE[seat]
    if step == 0 or step < int(game.get("last_step", -1)):
        game = {"last_step": step, "active": {}}
        _WEED_STATE[seat] = game
    game["last_step"] = step
    farm = _farm(obs, seat)
    positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
    unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
    active = game.setdefault("active", {})

    for actor, transaction in list(active.items()):
        index = 0 if actor == "farmer" else int(actor) + 1
        if index >= len(unit_actions):
            active.pop(actor, None)
            continue
        age = step - int(transaction["start"])
        if age == 1:
            unit_actions[index] = list(transaction["intended"])
        elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
            unit_actions[index] = _trace_actor_action(step - 1, actor)
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


def _fr_state(obs, step):
    seat = _seat(obs)
    state = _FR_STATE[seat]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "due_step": -1, "due": {}}
        _FR_STATE[seat] = state
    state["last_step"] = step
    if 0 <= int(state.get("due_step", -1)) < step:
        state["due_step"], state["due"] = -1, {}
    return state


def _town_demand_now(obs, item, step):
    demand = 1 if item != "FERTILIZER" and step % 24 == 0 else 0
    if step % 4 != 0:
        return demand
    town = _get(obs, "town", {}) or {}
    for shop in list(_get(town, "unlocked_shops", []) or []):
        products = _SHOP_PRODUCTS.get(shop, ())
        if item in products:
            demand += 2 if len(products) == 1 else 1
    return demand


def _future_quantity(step, item):
    future = step + 1
    if not 0 <= future < len(_ACTIONS):
        return 0
    return sum(
        max(0, int(order[2]))
        for order in (_ACTIONS[future].get("market") or [])
        if len(order) >= 3 and order[0] == "SELL" and order[1] == item
    )


def _pickup_reserve(action, item):
    reserve = 0
    for order in [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]:
        if isinstance(order, (list, tuple)) and len(order) >= 2 and order[0] == "PICKUP" and order[1] == item:
            try:
                reserve += max(0, int(order[2])) if len(order) >= 3 else 1
            except (TypeError, ValueError):
                reserve += 1
    return reserve


def _existing_sell(action, item):
    return sum(
        max(0, int(order[2]))
        for order in (action.get("market") or [])
        if len(order) >= 3 and order[0] == "SELL" and order[1] == item
    )


def _repay(action, state, step):
    if int(state.get("due_step", -1)) != step:
        return action
    due = {str(item): max(0, int(quantity)) for item, quantity in dict(state.get("due", {})).items()}
    action = _copy_action(action)
    market = []
    for raw in action.get("market") or []:
        order = list(raw)
        if len(order) >= 3 and order[0] == "SELL" and order[1] in due and due[order[1]] > 0:
            requested = max(0, int(order[2]))
            reduction = min(requested, due[order[1]])
            requested -= reduction
            due[order[1]] -= reduction
            if requested <= 0:
                continue
            order[2] = requested
        market.append(order)
    action["market"] = market[:10]
    state["due_step"], state["due"] = -1, {}
    return action


def _front_run(action, obs, state, step):
    if not _FR_ITEMS:
        return action
    private = _get(obs, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    moved = {}
    action = _copy_action(action)
    for item in _FR_ITEMS:
        target = _future_quantity(step, item)
        if target <= 0 or _town_demand_now(obs, item, step) > 0:
            continue
        stock = max(0, int(_get(shed, item, 0) or 0))
        reserve = _pickup_reserve(action, item) + _existing_sell(action, item)
        quantity = min(target, max(0, stock - reserve))
        if quantity <= 0:
            continue
        market = [list(order) for order in (action.get("market") or [])]
        existing = next((order for order in market if len(order) >= 3 and order[0] == "SELL" and order[1] == item), None)
        if existing is not None:
            existing[2] = max(0, int(existing[2])) + quantity
        elif len(market) < 10:
            market.append(["SELL", item, quantity])
        else:
            continue
        action["market"] = market[:10]
        moved[item] = moved.get(item, 0) + quantity
    if moved:
        state["due_step"] = step + 1
        state["due"] = moved
    return action


_YARN_SECOND_ACTIONS = json.loads(zlib.decompress(base64.b85decode('c-rk<U5{H=a{Mpz%m?#hW~980rMt1PV~sJAme>e{VIUg>2sRH+-h%x1j3n}s_jYx4b)R#`vyPukQ$zCH^VQwe)zzQ>=jz{n`StIA`}OLdK41NG_u<3UVRiNIzx?OF{@2qRPcQ%e%dh|OxBq^6{rT$qPk;USr^ko4pWb}DT3zjb81A0_yF08tU;Xgzak!ei`0}?OhT-kgAO1MpKfJ$M-Ok=Ve*Wh4_TBq;Ki=Ix{lkYJhT$jr#byw%4~PF<O&;Xkn?Ha0Y4T;`Lw&y54<9~${j&EDj~{>d`s(=Prx%wG?tS%n0?J?Q&gtwozyI{^{_W3Cpa1yj>oi>a;Q4n-4|9L_W*Dbw^2Ja8^#0?xeAOTL)0f4b&d}Y*;qlvt%`fQR`{vG{h>Ks4zwh+v?h`<kuFp)6B^)<nWk&4Eoksa>mwx@;(+{*PoSlaA4>T>{hlfuMJAy2nU9R&_^;x(sQv%Lj%Z9KkX9riAhtp@^^H;v`_>_1j<aaC>U!M)|yS^HRyYxiQy^qVm9XDSuLoFELYwWMA55Z(izuG!5$VKwLd;SRP$k#Z&%H6-?R+zqEU-EE&KfL+)^Ph&tkMHi^{ma)yY8@H4!3#sPdlPv`FJzu-LnFS*g_-c~=AyG^uH>Ahn4a44erT9G`<3y)&{b}}=G*8~_62+i7=7!&!YKpyviXv?j}Jf5FF9V^^h;1A^I^FE61`nK@R#cfU31&$n%jDg{nU61m-uG>Q{Nt+ADy|IUk?UDH!hsQ?Q9A^e0;pye?L4v{uP)D@NlOUo11w%cghd&$5r-;KH?<|y=RSe$2oIPi`IMo-8G|>vTc$12DiSob?T7==Bj4*H1l+P)o9umn#6EyOF2QO3+Uo_U*1czw@Y(aa}|PFJjYcA->HU_=P!zf$4tG0h7_%QX3`WpAN!_)lh(d|U|`|u)jW`tPocRq@P5l!-Cn42*#q0TkoorTGEH&9-I2_6cn+R7#!d`O4zd$QOSHuW1B0&rUNaS2BRS4y4vk=nXP+**Ef)dCvi7%mkDbl0F~m7LhrTF&N`~al5!b3aFas)UW|s}dy?|G$g(0RIE}-x%#K!6qBHGxaWmzm7bg+l#v9Q}0>JBVrn8!5zn}@w*lgD2^ejpXdaN`XAwSPF>5#-HSMivNWOe3>Coh<b{m-G_mYMxtr+QoN|f6)gDBj~Tmv@hFu^3>xOyO`RTQ3~hu__G8$Y?$0Jhc@2urAYe1)_Krr%B0tT5-_mK6+RCVE>DH)P+1Y?rS&^CAekHH3aEFRJ1aD(sN|unbAs-L_<QIxj)y=%fsP-7hamAib9;5|8e!mQe9cE6-@mkX#9rrP>}?Aaz7k{7dcHwK&{su6uDb*DttDdm;v=Qv{pv$8p3zb()Bh<dcs_AgimP*Z^MYI0eYdhoxtxGC`|cm~f-gpg1@XZYyB@9Scz2I4oOs&)A)17g+cSRC=<^|LBQvQY>|&oKVZy*~%s(BzD)1Pj(U04uJ#FDm4P>_22bx>zR2tv9KO=&29tC(yCyLa78~6^G>kJoUSBFnl8b`))rV_4MatLrnoVD-$_?F!>--(+ApS%e$lu@Wk=BP&Hv;*E?C-*t&A**glsjLqb`ZH(OghLwKZEAPb&VGY+l+as+JOuW__O4@AbkQ7lgvVe_R2Wn=;ir}qV*_`^2~FESJlr3Pz|gbIk*YqNgyU};^W>-ZI6w4!$DW_Y4X`yF9pq;a*gX#FJWk7$cK}Leq=V5-S8u)Xupdiqq4}yjZx$_OI2w!-npb3nU*UP$TtYP8rY47IjCUpRawX5}+pljg#xt9tZ^M6zVcuTFTTk+a#}@^LF*xw!RDge*rj&N!Sya-4gj7F^bIID+5uV-L0<#DXfP<Oii;!aw-rE56WKT?)3@ek7N$n5tRKPM^j^&)H;kO5!U%#qi_LPQFIC<~eR?f{dGPyD^a~^M@mI1_*2!6>xPt)_d&7j`vQVcM!CErB#;T!CGgLuVxlej}}eOW3H(_r`TP_w&tymEod-j+|oz6*LY<1R~8@uNEgz{DhmH_ZU!GDYm(L~eW~AAP<6O{AFNYO$~o*x>Ty(fu*5jsJ_y`@mV5(=VqY_jn_OKkQ~mYl)WrfuP-1=W9W}ZbTx!5A;{uCVR)(N9edJq&|FZh_T-SR!4nQsf0YrY0$_=-THA>A%ADEOE2<@8aF?KbXdBizDEI<6kO=Z8Dt_Bns*n^9@CI9oYI2+!rWI|XZ*(-QUFoHk{ubNThH}OA^^Y%B>w2NR*)AKJdztzV0j?qKKub|Ozb-un=Arm7Z*JL=S+NKe;XJy@Kz^hH?(D<`<e26z-bTI5dM296EJR*OBm1Yoi=W(%^-l~%dzBar0p$BWVkPXcXqK>sXz#}@UfO0lmVhi@D`ZX++^MXp0D+~%KQ!cT+yitk7Z+ButKr`%b3KW29EE6pGklQ_Toe?$oV~skC$f7e$6>9u*bYIZFb|GaR`ZFl(RO$S33Xhg7`ITHV+Qx@fQx)B4BQ0tN@x-Dg|s8*^*&ElsDwr!4*IEb)5>VL8y&>?9Q_-@DJfiB73BYQtS?iTS3c4?Yo#@4FvVvRWPiKb49Eum;;8S&doq>5<*AlJerAhm&p-L7$P-sp^-0@9up^<(rEy6Yqx1dUxG1etnKUtK}HKK8`oOM#kj82aiyD3S%2n516a*@YOqx@nE`S;__UlA+AD1(-;sB7>7rh+QeOFF`HXKj#Qu&MfZ<w1tQUz%>@ZKx8BB?~Be}ya;IyV%r(U@aq@X06XoSWBXf&_nXB9`Il>)Jdbpy+6CM$qy;8F`n%>Bk~f|fklTRVp<WA*xkae_jP6)XlX=o~7)AKe<*@6^fMv7n9}C8iTt-340K-etZBvwwWys-0`mO!)N9jKe=8PtPdtbX#A$sexTY7wOGg4_{D1&61JVF3bTid`apV;gR;YIMcGp340K!K}>nc(Cup;ghXx3Gi6qs5LjXG`0R)v9>f7#P4=+>oL31s*j=Pfe`Q+n>{#!Mu{wpfYT+)x$=G>8XxeB(#GKD~Js(@e+#FQa!Mx-TXWYgY=Yb9JToYg18>d{rfxV+P_E=PZ5-V=|9H6tm5D{SQE{0)owThV}l6k5T{8`8xiE<v5tqec~8!&^zje;SqCVcVqGMHrHehur%OO;v#IpdX07TZwE+*h3>dSPNa$|h2bhfqWdk_+d6Gg>b{{n}@26^~$0QL|Yci(~&8115h1Af#*%=)LxScE2DsL`Ez0-4!-21`s6V;Dm-YsMk-hVJ*0l8)d;SpeyI{=C^o55SrayE&R*0={o(K1r9B)06s=?{Ha+5p0%x#1NXX!L-?8p%<dcPR{=lu)bBIn3pz(}eA86#xDy|IPKb`Lqp*jUKU$jZI%s0K^E#Taf=Y1VGq{2M8*mIORX~guOu<JHqhuNM3NeY?`__3zKC>V0p`>Mt^i}9BN30wUSS1pig?KNc1EGbRx#^U!GLU%|LB1MGBBC8#6fYgu#Mxofe-{O>+Oo#&NEr)q6cnw&sRuU&MiUtlV!}Dp=Sguq=^lX2oB2Vo5#d}>daQ7Y2z!9yWPXXu3PNpj=QziuK-k@&G8WrDBhlRXp)U*&<c{fIm8*Uf9`CuID7fkwnZxeVHhKq^SYqVgFoZ|QwTndvo8UB8JlwQAD0L|X<SbL8$Ce+gtVen9Te_mFV~|j@WU1)j-rXT72yCEm-vB$JZ<5p4I9HGHRuagggIwg}d`7#mu!t){<IH$nE^u>brs^<-L_09AUvYt^Zbr(!n^Hnt;>Akrtd)cxLS5?TfgfTcv6Iy~b|N?d8_l_vF`VO92OaO{(F-rqlGK!|ke|vq_wP*>2THdq6pypiw_t$gW<7g9gsW`-zD1KT(4XL;9~0oq#Ig)BEmG?#(OC~($@z#2=>}Ky3iWUBo$gvb3?L1d*FjN|B^rK&g~8TSMb{0Tx{A+l?}P+UK^)VPT%=YCL?A@c`E=zwv9<aOOTY;@OH3WCO|f0R(WJ3(IINq{d#a>byLAC3l?!t$;2)j_p!<pNZz-}XqBfK#2F52{F+HGmR<x(h8|i>oZ`sE}@P>(#hiJThxfcoa5T;<ZO}FZKkV3CQ3YLLW5`rpXBS*!Jj)h3Jx{|+T<ttqknc@v>5}aaGpMMx3cQF29QEN(1{>%w@cmL<9y6Z)KREq3>D@gF8XR=Gf!u--h@<(b2<B#7q?L_cGqk2EoXJjcUE3RJVQtS@AoZ_(h#pQ}_Ycgl7O7HVAQton}zSfn1Tj0<(H{Gm~yh+kMQH?-aPAaPV?FfXtfk<hN-)t+JDOHK2cGrMY&ZW}Y+9;+9R&<JZMGF9I7+qnKQkj}im}G#i>2UT2To}Wj=;u_@>o!k2t&hLf3dSsxC7)klG4Ca-92d`1MKY~}8}Y8L4?6hb#nZ?Smd2VFve_OMP|cuDjJ^q@)4_DSqGTSE`xg@)n?pi<%z{_e%_jwWg&r8t#f_>y*!)2DfgUTSVnWJ$A;FKAS+3w2?3M}jXE6rACN3Q{t{bLjj%kFO{k9$)$|ABaJUlEWeJ#a#riBqj(muWX#$%UzTRInbW=q$bvR_?t!|WlN%}qT^9E5-Rv;_@*wd60aTTGBxWdyw#qDpQ3TKApUB@XN-rGIn7cC+y+)s#>(O8W*WT>FAXfgL6(fy1QUrfY4Th#Av<Xy`W#OIa|FpC=BRl<-c$(FN?y*y41b`87m&7rN4FaT9V7#3^-?$TVXhbnl?{BI+KfkR_^wSR}p@rHbiRE>U3$=w_NUaZ%$l$usKQ7$4}QP%8O1P}ADbx+M>UN;O&OoTf8cQ3_5LqqZ6>$)`XG=g!@Mpi&(#y++*!z0zl;Wo&C89+Boq`99+qcVI+l6+i%Y3R}h+zPe5=V3t1`0HQVN#O=`5?m9>C+kd<W-pY{L>Uw~uxN$%HmmPB#E-4cxTQ0=-w5`zb6RlKn1l6+Wf_~DO>4nqNXh^&zNkM(Rg-X630^grUygqaPH)E6&ONOGSW{r19B7@bh$T?*JL1}XHbo0>BcDKf$G%xPduSm&3JI8D~{^|dLo8saR8a6R(;-p5j)mMu%0_@sH+VDylPme>!4ibo`^=nV*+SKjP={lWk>*t8u<j}D?UnDocH4@o(*msn9FIp0yr_Yf>YH0XJOK^y3_-@?8DQ>pjxO8TIP^a6Ucq?7Fs;SH-77X_0LptnalZ9TJV-+G4j*u>V!Rn2E=xL5@i5?|9O(Ceywoyh^YCj`Q`P-rMXi;l$K{8rv&b#E`l#~xB=;$QkC3KV8VowDaE{mPeGL?DFLdximANIVIoHIa6W&{Vq*5doIFS*k@VK*<O!v0#Wu-`_}8`#_-pcAqz*59#84{K)?Bxb$tPQakEK>F=y*wvO}%H5C}oSN32&CfqQLzzLY53!ax?aKEU(!OXANrq!wiUq>LFctG_DrBH8SG1S0u$&k6W|Y+-><G?SP|!{Mb^L)Skm+&yKzD3S4gw+1OrI}w%;h|!!?Mvz_&u=90|CQbOmqCY07g2i&QV`MiFHg{Qcl0zE|K!i-BAnUocR|CR=*-6141HX?&R8=$by3iIMa|^lbA_zZo=5VQmPUbZ1duDjr~`t;{%PtnRdUVhXnd%M|o>5(2ePS{^ZC`U5Od5D~AO8SA$u_>u$yxD9B~W)h?jaA7hX_ZIJ326s`)9T6VF;ZJeQ{5-$Rx6f$LYheDg$ao(xm5olY*X?@`&>vY(QFGZ6cIQ<O05oJw4h%KPB;95J+wJy#IARHedP*qSME^~nmi2SO5P%%VBHX(^Ngc|?Or$hj4g6?cwWNn40b9@S``V9oIry*tpb3GfIM&to4kz(i|1fiBCB*2e8IuSg!WnCNf`7MyFBM~z~`3dYxB|EOm1n`)Ti6;7;PrE8mfMJmy2kzfFysC;!1w<9adLz40(VszZY|+Xer3+%fKd9_ncF^>?h8QzMese(6X)JHB<||RTMA5H)XAGcSBJD2-p*p}4kekM2gCrM%Y~iF5V{nde?3f!YG%1xcwJ-L#C6i25fWX}$V&9p%A<#I`cd0@3(6FG|1~ChE*sO%Xf)*LYo_v828Ky1uV1*X+&dx`_OfH1AJiz5e{sVx68AHXps$PfN(QS(#!ag5c0!5?6R$4fZB$R4yqs4$FUjA7n4I9jdGRq|p4S=j9T_L$%N;%=8q|S|79+TLOzXhmbr@IcS>_T5P0!Y;M4KDvBVk3FQN;{Pqv&nS`wNSE#mnf|_LTkJ2fUm$e)$SY;D^k}v;dM*a%*Wh+^+Eb+u_)|5gW3Z_C{P{TXs}B|@j-3g8I>puQe4nd145)rb@G6Oywx(O_C*lVNv%jz+9{-_!@l4}iUD%ME7tngZYa%MXqM}o&w2OH;f^f=M3Kv)8392M#Ci4g(TbfxEN1~jf?_HW2HJf)hOmAdS|?v&e!F%M@lFy=)Ov-Bwc`hkZ?tdq?W~qH2FfV;U{+SM;<p|(Hd=$;8umr-!;~JgrY+S4m}C7xG5wU54!JOX3XB1YLTah1ASjiu7p8<r!KjH_leIja?*f?(`6_iu@cN{HFB$C@wN2qojJhBu<<?msO9G*7SrUzW?dn9=-)T)!6iTNKm-hbv*eL^cwY;@+i`&&&B^8|f_y6F*lz1>{xtUCn(~S)Btlgb(omQl|1;6^7l$un*m_N$`9qF0aH(3q7=dYA<D;rWRQHsydse22Rxrx+mN_3(|k`6r<>>0eLc`n9I1J^9pc+?z4j*1fDckDXFbE_;!FND;lZmpZ@ol~-byv-8sb6piDIJOaz8&n6yt5igyqVhlrLQbHGBU<L75MKON!%+8X!)C3PM+4B<6tt>V1ynng66(cD@B}O-UnK!&U~f>(+p=~^fkMOz`Cw!x?H_owl^w)N$C|5^gX9BC>U9BZMf?htp=dQw3MaJ!;wto09oYyV@dPr5Jp`3}6meo%mXa;V3?m@W#im|ymgv-wQTd^HBJyA*A{Ee|p})_tB3~3cHB8HsiHe;>KB88zrOYj-eMQZAk-!$fxm>6;uIgs<9}1>zUOGl4NHPf^l@D=*?Tt2s6+=Jcr&{BFN0y1S)sZHhIZO!d1XZGUUW?j}9!>|1z{0CRjHf$-MsUOzhJG5ZQ{57|*r6RV;!SRVFRK;iR42JrXeTu1am`6Q<>`RPZ1a7fmKnCqVGeb`_iEVU+&2ZlOISoRp%#bguPMjFhL)^TWjN6hYe_@kSff;n&bmo)8DnF8)qAo}Dn*K#I4bj!x@=_#cavNNdlVd$b;#mFgFyw%d3Yd%zl@2WX}WmXte8mTW*C5g%LHb=$YG4YkEpXr0SwipfSdS9dZ+CG_?Oge-2+nut7z7Q{#7I|mEpFDorE~Sk?I9`2f<GIyem|r-621~5+t-DIxOBO@Hf`Ex{CN>378HHErF4{)#@d8X}vjlj!r))coYI30yamN-sWHrQ8pBr>M2=yx`8vrWwtjp)d>;>el0qMW4*9qE_H5B0K*?_CBjK!wnP%?NzsLNo`}zPYI$IL$1ASKk-~m{lU`U3D}h;AS}ey%!G1?G#4G#GYGzrVxuv&Ot%gR!58CNdYKAmeK#lH3UM<yaE5k32a(8_=4gE5?`$6f4S7~sT?7#(l0<M#vCpRocVi4t6xcsUE33enN5$MT!So=9$M;0n>t#k{|Bfb2SJQA(JcT)1PdQJndoeEUN?Z=v!3v|voemZD6u05rb!udU=ofMJk=pyI!b7eFTT!>k9YFn2oNkiqvDS{wSUPKek4pf@h!TlBrT^|bgNEmOQMM5&{GrsGxT?kb0fU8^s-6bYLA><pvs;X^_^T-{#Dk{3b0Lb{sUPqouCw0aZVGCjowcR`l4nn)>NyDb|3;)rVyN+9}#~h2Cyb~cRNy{K*&2>_e#h;Qyq-`X34gBgTw*l3-)b-fWW{#(eS#0n4yJ9f`kvs|~Duv_m@wmKke;n=~-V+JwYhE)+fUa$YtwhV_#rn{MEOU~EgexjY`>bVEqdD;iSmdCS7W8gA(Trlr$|%pONk-+`6w9n5sRt<C0C-Mor67B?BufMhiGpbtrUj1&xMsM5$JOXTv?F!gO^!x=aU`<KL?X?Hhm~f~GPBga3@{q8f>S62?vDr%AV9q9p}y(KL$8F>ngB<r|APcRy%4)ty&DvtgcrJqnlgS8=g0VVzM!QM(7y-~wyy>_uPc@+ZQ_1{`BqPQ<y?X=rI7~%(rZo1V;8urRBlbBkkGB71x5-JkB(In1`qLl5#-q(+Pk!6y9#?(q@v{Om6=f^=xlsMaq-DSEM==o7p>#@&r|?1Ttozevh$Au)h1G;-=2@FJwy1~k5;J+`Ts+8p)BN)EIZni{w2mtcA&ma6N(0%(>EnbkBE(=I4>RPIlhVj_=7~Vu*KwjB!HyXY!*~|;zDm5XoSUCOQ`gudTna@2aZljKdqir210Z{d(camnhiyE=uMC<ToZd}?Q>X;t6Y?>S8MK{m4Qyu)ViiK7C>K82Y9X}+ofF=JH}w^I`<OehV%`V5yU{H5>knKg7e)TioLU<s$j7pS%B$9P1FlII64BPhy4;h(cD)n%7E}fwk&ql)Jsbun&^dhENW@CU=+szbCpn6q4hPZD#an%;hNO6EQ+JUDA$=bTT$$;UoiVn$0t+gq&C}%s`nH%9!a_?2g_STK-2z#VpMK$%R6&uuz}dOiHhmWOAYZ>AO8y3`7pTN+M<bDL6F%I+kI)>vw9Xc?F#6|x~g)Ml}fi96Qv$%ebcSJNvb5VH+G`_rChNT2W6sejXv0xDkD$(G)R5T(w)gFk&5Okh&NAz2t}F+1h9nKYpNdu3aYaDx)*a%ah4-)U@WMUg-viNdeC-Aahqx0J{0^tO(MgqbS=w5>}v5A2kw&?<|Taw9dOYz>uhKu*L+%$RPCo_;Via=TY}bTGv^D4)P`E%YCBDyREE)7D<q1+M3IQ1!pydH)W0Q@1dZqmQn0Q@3hnmuqCQMLp%LQAM5c7p!zzh1HB%mUDZ7Y=;I`><7EnMr9e8v#+OviT<~bw@v@d{2A_s<-$_c=q7{HVImEcAv;XSN|@QqhH2WcB{kfPKDO&yaLg}_hcG*EeRcIrLr@1bi9JW82jC^-Z05s7d|UL=ajIA;o?2VTQ-^tV8i2Vg#M`rTMO)z$tLt4f(7MlZflsAm`Tt=uQdW%q?A*{{gT&wbSJoF=bTwVDbupwiD=u3j&+FPEc3n`McnPV8>pB?yFAO`89srY_~u?o_|2U_ikxD0I`-`_v>|@r8Nl%#>*`Rg6DyLW-utLiyIg4Ov#JR+Luu8NsIM39xv&Q2bCk2HY1T!aP}wx}{%}*m`FfrWR{b$W$%jKhIstYIii{OqL38CM0dAwQNUY!h{s^MHWfzy<$%#l6(*a6QotSblh$|<-tRRKq;zt2jW)?vAtML3oCO8;l&<oemP^L^@yT<V-qIUZfzi&Z-YLu3XS9~wOO;9GGw~+5XLaKG>u=AJ2#~~!pIqVRv5r8%gKv?vY&Vs*SOMR8gah*Ll&fmEQm1=nw0I+S$upD3t5sHAFT9HtF(OKsvk?#xu`-Q;6fLDK*|wYp#M-p&>)!ifYRGhBSe-Cp~CrL3k-*2)7XZHZgMPk@2i2HoTlSF(U}MowjVaZf}Jxk!fsfF(vb-Leh^52k7T>laGh(URo>LaNS44gNn@Pf)YUZl^)I?)k<GpF(|G0tA-Ji?A1&L{2-Lgyj3(_|#1Gos?kGsQ(qU=`*#_6AZz~dX*a2vg<)QYXNy|6f{+c@`9{B{o+TPKK;(zv75-ZKpngzPZ?V;5BNG9QCO`F3~Yww?HtsYZf)rg9Ob>W)S9)%Ou%&}+T0J(h#sbTkQdu^6#kHj8~glXid^e*1rdm^1BuY5rdZH-)!kb?Hg+CyTsRw2MLSm6?g7}(Xq_&8ZZ@u4?rHyfF@m{V!t;$p>B70=o4xSdi$w?n^wujN{y>ji3sIK6~2Q!4!?D?N^gyP`{t#)ECC7(!%nPW84y`HV8Wpr5GpK%^-*q4ZQDy7z93k}q7~zWeZ8or%ctlI3`e+tsfpQLK|Jc4N-4BYL$WlE8J^)F;l`ygn?^j7SVD1zCa42aR*t&}FC{)8{y9RqY7n9pZL%>o%k}R#RVfVIioUhW1*IU*2XZ(m<$Cbk<5ah}MfpEbZeM&4Rs%z)Z?*s))ZR<XD$zKg8vW*w!K}q>doF+PW<%ytdEF&^}9NAr9Os{R4FNU$LtY`*8*1sU*R~zCkq8EP8~5W8^g_DYpo+FC<+UA0A)4HPAWcvD6|!8UPheSu)qHu{ArR<MJAG&i(Fp&GJz>JzC?F5L?~Z34Wa@R<e#vJeuH|&-8gra(3uQ`u7oP;^$DMPgRgGQ{z$S)5ALlQTMG|&*R9$PB4X{z@getNNUw1(|>s0H{qz|8})!a87_D*r?qNrn_g!PuCx|b*+xhC&OFgv1r1Y3VAS4^CoU?>$%s5l7)^K~(zHc;qq#E=gWV_<!Y#V*(2Iu^ow2sRZS8lI>Ysc^o-hj5W?5`?)+cu<R;H+zmWU!l7yPD2n;xy-UVy4(GE&)IJX+e0=}c%do2>XzSYuR3LhXl_$eac3c4E7RW6KImA`}D^R$-f|AmS1t`_em98rO?(3v>w3O-TGl@Mj_KXl=ttb1zz)0#Q~dK}8|%*uPO~v~U#M4i+whKe)Uh56IH%YAFcLg8R6+CEO(JX_`P<9v)>nxrmRXv%9=i;(7*ppV3~cvt4d=YHc+FzoKV%LP|IYA~n%n@F%$;<*((x6Tx`LO;J+Cg)R;E+(Yjm*z0|gL!y#La@V-GjJ%sFwjfr!;jNL?4Mk_3Q8E;fl!m-er@aw3om9yQ9S6;(H3%_uBFr;SFYkw&D-<pdH|Xh8&<>-(U+7-QElqeo60dI(y+cw1Wek(3e+iG-G|7SH2_#wHX#DfNsqVy+6PG9>vV8uq4T3gtmtOs-3XpIcR#AUl8%o-T0-_{jJH(TXA8L-DeEW4o5+L;n`ymY9;mA(I0O9MkihtM<gQ^jK=w3ul0*zNdD)I(Qt_!5C`#eMVB9}H_-=Yn29Usy8=%?`9;r{?^$I{s')).decode("utf-8"))


def _v154_route(obs, step):
    town = _get(obs, "town", {}) or {}
    shops = [str(value) for value in (_get(town, "unlocked_shops", []) or [])]
    if step >= 153:
        yarn_first = bool(shops and shops[0] == "YARN_STORE")
        qualified_yarn_second = bool(
            len(shops) >= 2
            and shops[0] not in {"YARN_STORE", "BAKERY"}
            and shops[1] == "YARN_STORE"
        )
        if yarn_first or qualified_yarn_second:
            return _YARN_SECOND_ACTIONS
    return _ACTIONS

def agent(obs):
    try:
        step = min(max(0, int(_get(obs, "step", 0) or 0)), len(_ACTIONS) - 1)
        action = _weed_repair_action(obs, _copy_action(_v154_route(obs, step)[step]), step)
        state = _fr_state(obs, step)
        action = _repay(action, state, step)
        action = _front_run(action, obs, state, step)
        return _align_hands(action, obs)
    except Exception:
        farm = _farm(obs, _seat(obs))
        return {
            "farmer": ["PASS"],
            "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
            "market": [],
        }
# ---- Codex V6 boundary layer -------------------------------------------------
# Parent policy: prvsiyan/kaggriculture-frontier-the-soil-remembers-rain
# Parent source SHA-256: 78bee1edf0cf091df9652b96f7601e39d61c4ac2b87a4ddb4702fec6f4dc28e8
# V6 changes: public step-153 route latch, official-shape normalization, a
# three-quadrant land ceiling, safe PASS fallback, and bounded public-state
# opening/liquidity/SELL-slot overlays.
__version__ = "Codex-Frontier-V156-Coherent-Liquidity-V6-Limited-Dynamic"
_PARENT_SOURCE_SHA256 = "78bee1edf0cf091df9652b96f7601e39d61c4ac2b87a4ddb4702fec6f4dc28e8"

_source_agent = agent
_source_route_selector = _v154_route
_V6_ROUTE_LATCH = {0: None, 1: None}
_V8PublicSignal = namedtuple(
    "_V8PublicSignal",
    (
        "step",
        "day",
        "hour",
        "own_money",
        "opponent_money",
        "opponent_hires_today",
        "own_unlocked_land",
        "opponent_unlocked_land",
        "shops",
        "market",
    ),
)
_V8_STATE = {}
_V8_AGGRESSIVE_MONEY_MAX = 1_000
_V8_AGGRESSIVE_HIRES_MIN = 5
_V8_EARLY_RESPONSE_STEP = 2
_V8_EARLY_WHEAT_RESERVE = 1
# Market corrections require a positive current public price and Town demand;
# zero demand never creates or enlarges a V6 SELL queue.
_V8_MIN_SELL_PRICE = 1
_V8_MIN_TOWN_DEMAND = 1
# These are the inclusive V6 route windows for the existing second and third
# purchases: standard/Yarn are 160/158 and 252/265 respectively.
_V8_SECOND_LAND_WINDOW = (158, 160)
_V8_THIRD_LAND_WINDOW = (252, 265)
_V8_LAND_PRICES = {"second": 1_000, "third": 2_000}
_V8_MOON_PROFILE_WINDOW = (6, 12)
_V8_MOON_LIQUIDITY_STEP = 264
_V8_MOON_LIQUIDITY_MAX = 7
_V8_MARKET_PARAMS = {
    "WHEAT": (25, 10_000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10_000, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 10_000, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10_000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10_000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10_000, 332, "hinge", 0.4, "log", 0.2),
    "MILK": (160, 10_000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10_000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10_000, 200, "linear", 0.4, "linear", 0.4),
}


def _v6_seat(obs):
    player = _get(obs, "player", 0)
    if isinstance(player, dict):
        player = _get(player, "id", 0)
    try:
        return 1 if int(player or 0) == 1 else 0
    except (TypeError, ValueError):
        return 0


def _v8_number(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _v8_integral_public(value):
    """Accept engine ints and integral floats, but not coercible text."""
    if type(value) is int:
        return value if value >= 0 else None
    if type(value) is float:
        try:
            if value.is_integer() and value >= 0:
                return int(value)
        except (OverflowError, ValueError):
            pass
    return None


def _v8_public_farm(obs, seat):
    try:
        farms = _get(obs, "farms", ())
        if not isinstance(farms, (list, tuple)) or seat >= len(farms):
            return {}
        farm = farms[seat]
        return farm if isinstance(farm, dict) else {}
    except Exception:
        return {}


def _v8_unlocked_land_count(farm):
    unlocked = _get(farm, "unlocked_quadrants", ())
    return len(unlocked) if isinstance(unlocked, (list, tuple)) else 0


def _v8_opponent_profile(obs, state, step):
    """Latch one public-only opening profile for the bounded Moon overlay."""
    if not isinstance(state, dict):
        return None
    profile = state.get("opponent_profile")
    if profile in {"moon", "other"}:
        return profile
    normalized_step = _v8_number(step)
    if not _V8_MOON_PROFILE_WINDOW[0] <= normalized_step <= _V8_MOON_PROFILE_WINDOW[1]:
        return None
    opponent = _v8_public_farm(obs, 1 - _v6_seat(obs))
    tiles = _get(opponent, "tiles", None)
    if not isinstance(tiles, (list, tuple)):
        return None
    money = _v8_integral_public(_get(opponent, "money", None))
    hires = _v8_integral_public(_get(opponent, "hires_today", None))
    if money is None or hires is None:
        return None
    animals = set()
    for row in tiles:
        if not isinstance(row, (list, tuple)):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            animal = _get(tile, "animal", None)
            if isinstance(animal, str):
                animals.add(animal.upper())
    if hires == 4 and money <= 5 and "COW" not in animals:
        profile = "moon"
    else:
        profile = "other"
    state["opponent_profile"] = profile
    return profile


def _v8_public_signal(obs, step):
    """Return immutable, current-observation-only input for future overlays."""
    normalized_step = _v8_number(step)
    try:
        day = _v8_number(_get(obs, "day", 0))
        hour = _v8_number(_get(obs, "hour", 0))
        seat = _v6_seat(obs)
        own_farm = _v8_public_farm(obs, seat)
        opponent_farm = _v8_public_farm(obs, 1 - seat)
        town = _get(obs, "town", {})
        shops_value = _get(town, "unlocked_shops", ())
        shops = (
            tuple(shop for shop in shops_value[:3] if isinstance(shop, str))
            if isinstance(shops_value, (list, tuple))
            else ()
        )
        market_value = _get(obs, "market", {})
        inventory = _get(market_value, "inventory", {})
        prices = _get(market_value, "prices", {})
        if isinstance(inventory, dict) and isinstance(prices, dict):
            products = sorted(
                product
                for product in inventory
                if isinstance(product, str) and product in prices
            )[:10]
            market = tuple(
                (product, _v8_number(inventory[product]), _v8_number(prices[product]))
                for product in products
            )
        else:
            market = ()
        return _V8PublicSignal(
            normalized_step,
            day,
            hour,
            _v8_number(_get(own_farm, "money", 0)),
            _v8_number(_get(opponent_farm, "money", 0)),
            _v8_number(_get(opponent_farm, "hires_today", 0)),
            _v8_unlocked_land_count(own_farm),
            _v8_unlocked_land_count(opponent_farm),
            shops,
            market,
        )
    except Exception:
        return _V8PublicSignal(
            normalized_step, 0, 0, 0, 0, 0, 0, 0, (), ()
        )


def _v8_new_state(step):
    return {
        "last_step": step,
        "opponent_profile": None,
        "latches": {
            "opening_regime": None,
            "land_timing": {"second": None, "third": None},
        },
    }


def _v8_state(obs, step):
    seat = _v6_seat(obs)
    normalized_step = _v8_number(step)
    state = _V8_STATE.get(seat)
    last_step = _v8_number(state.get("last_step", 0)) if isinstance(state, dict) else 0
    if (
        not isinstance(state, dict)
        or normalized_step == 0
        or normalized_step < last_step
    ):
        state = _v8_new_state(normalized_step)
        _V8_STATE[seat] = state
    else:
        state["last_step"] = normalized_step
    return state


def _v8_opening_signal_is_valid(signal):
    required_fields = (
        "step",
        "day",
        "hour",
        "opponent_money",
        "opponent_hires_today",
    )
    if not isinstance(signal, _V8PublicSignal):
        return False
    return all(
        type(getattr(signal, field, None)) is int
        and getattr(signal, field) >= 0
        for field in required_fields
    )


def _v8_opening_regime(signal, state):
    """Latch the first observable opening classification for one seat."""
    latches = state.get("latches") if isinstance(state, dict) else None
    if not isinstance(latches, dict):
        return "v6"
    latched = latches.get("opening_regime")
    if latched in {"aggressive_visible", "late_signal"}:
        # A stored non-default regime is authoritative for classification;
        # _v8_apply_early_response still validates the current signal first.
        return latched
    if not _v8_opening_signal_is_valid(signal):
        return "v6"
    if latched in {"v6", "aggressive_visible", "late_signal"}:
        return latched
    step = _v8_number(getattr(signal, "step", 0))
    if step == 0:
        # The first action is simultaneous, so no opponent action is visible yet.
        return "v6"
    day = _v8_number(getattr(signal, "day", 0))
    aggressive = (
        _v8_number(getattr(signal, "opponent_money", 0)) <= _V8_AGGRESSIVE_MONEY_MAX
        and _v8_number(getattr(signal, "opponent_hires_today", 0)) >= _V8_AGGRESSIVE_HIRES_MIN
    )
    if aggressive and day == 0 and step <= _V8_EARLY_RESPONSE_STEP:
        regime = "aggressive_visible"
    elif aggressive:
        regime = "late_signal"
    else:
        regime = "v6"
    latches["opening_regime"] = regime
    return regime


def _v8_action_shape_is_valid(action):
    if not isinstance(action, dict):
        return False
    farmer = action.get("farmer")
    hands = action.get("hands")
    market = action.get("market")
    if not isinstance(farmer, (list, tuple)) or not farmer:
        return False
    if not isinstance(hands, (list, tuple)):
        return False
    if not all(
        isinstance(order, (list, tuple)) and order
        for order in hands
    ):
        return False
    if not isinstance(market, (list, tuple)) or len(market) > 10:
        return False
    return all(
        isinstance(order, (list, tuple)) and order
        for order in market
    )


def _v8_opening_queue_overlay(action, obs, step):
    """Use the public Kaito48-compatible wheat-seed quantity at step zero."""
    del obs
    try:
        if (
            _v8_number(step) != 0
            or not _v8_action_shape_is_valid(action)
        ):
            return action
        market = action.get("market")
        if not isinstance(market, (list, tuple)):
            return action
        adjusted_market = [list(order) for order in market]
        for index, order in enumerate(adjusted_market):
            if order == ["BUY_SEED", "WHEAT", 6]:
                adjusted_market[index][2] = 5
                adjusted = dict(action)
                adjusted["market"] = adjusted_market
                return adjusted
        return action
    except Exception:
        return action


def _v8_apply_early_response(action, obs, signal, state):
    """Reserve one wheat unit only for V6's visible-aggression step-two buy."""
    del obs  # The response consumes only the public signal and own-side action.
    if (
        not _v8_opening_signal_is_valid(signal)
        or _v8_opening_regime(signal, state) != "aggressive_visible"
    ):
        return action
    if (
        _v8_number(getattr(signal, "step", 0)) != _V8_EARLY_RESPONSE_STEP
        or _v8_number(getattr(signal, "day", 0)) != 0
        or not _v8_action_shape_is_valid(action)
    ):
        return action
    market = action.get("market")
    if not isinstance(market, (list, tuple)) or not market or len(market) > 10:
        return action
    first_order = market[0]
    if (
        not isinstance(first_order, (list, tuple))
        or first_order != ["BUY_PRODUCT", "WHEAT", 4]
    ):
        return action
    # Fixed quantity: 4 -> 3 on the scheduled V6 step-two wheat purchase.
    adjusted_market = list(market)
    adjusted_market[0] = list(first_order)
    adjusted_market[0][2] -= _V8_EARLY_WHEAT_RESERVE
    adjusted = dict(action)
    adjusted["market"] = adjusted_market
    return adjusted


def _v8_market_price(signal, item):
    if not isinstance(signal, _V8PublicSignal) or not isinstance(item, str):
        return None
    for entry in signal.market:
        if (
            isinstance(entry, tuple)
            and len(entry) == 3
            and entry[0] == item
            and type(entry[2]) is int
            and entry[2] >= 0
        ):
            return entry[2]
    return None


def _v8_repayment_reserve(obs, step, item):
    """Read only V6's own pending front-run debt for this current step."""
    try:
        repayment = _FR_STATE.get(_v6_seat(obs), {})
        if not isinstance(repayment, dict) or repayment.get("due_step") != step:
            return 0
        due = repayment.get("due")
        quantity = due.get(item) if isinstance(due, dict) else None
        return quantity if type(quantity) is int and quantity > 0 else 0
    except Exception:
        return 0


def _v8_market_overlay(action, obs, signal, state):
    """Narrow one proven V6 SELL without creating or reordering market orders."""
    del state
    try:
        if not _v8_action_shape_is_valid(action) or not isinstance(signal, _V8PublicSignal):
            return action
        market = action.get("market")
        sell_indices = [
            index
            for index, order in enumerate(market)
            if isinstance(order, (list, tuple)) and order and order[0] == "SELL"
        ]
        # This correction deliberately refuses multi-SELL queues instead of
        # becoming a generic allocator/reorderer.
        if len(sell_indices) != 1:
            return action
        index = sell_indices[0]
        order = market[index]
        if (
            not isinstance(order, (list, tuple))
            or len(order) != 3
            or not isinstance(order[1], str)
            or type(order[2]) is not int
            or order[2] <= 0
        ):
            return action
        item, requested = order[1], order[2]
        price = _v8_market_price(signal, item)
        if (
            price is None
            or price < _V8_MIN_SELL_PRICE
            or _town_demand_now(obs, item, signal.step) < _V8_MIN_TOWN_DEMAND
        ):
            return action
        private = _get(obs, "private", {})
        shed = _get(private, "shed", {}) if isinstance(private, dict) else {}
        stock = shed.get(item) if isinstance(shed, dict) else None
        if type(stock) is not int or stock < 0:
            return action
        reserve = _pickup_reserve(action, item) + _v8_repayment_reserve(
            obs, signal.step, item
        )
        executable = max(0, stock - reserve)
        if requested <= executable:
            return action
        adjusted_market = list(market)
        if executable:
            adjusted_market[index] = ["SELL", item, executable]
        else:
            # Removing this one impossible target is the tested stock-safety
            # exception; every non-target order stays in its original order.
            adjusted_market.pop(index)
        adjusted = dict(action)
        adjusted["market"] = adjusted_market
        return adjusted
    except Exception:
        return action


def _v8_land_timing(state):
    latches = state.get("latches") if isinstance(state, dict) else None
    if not isinstance(latches, dict):
        return None
    timing = latches.get("land_timing")
    if timing is None:
        timing = {"second": None, "third": None}
        latches["land_timing"] = timing
    if not isinstance(timing, dict):
        return None
    if set(timing) != {"second", "third"}:
        return None
    return timing


def _v8_remove_land_orders(action):
    market = action.get("market")
    kept = [order for order in market if not (order and order[0] == "BUY_LAND")]
    if len(kept) == len(market):
        return action
    adjusted = dict(action)
    adjusted["market"] = kept
    return adjusted


def _v8_land_overlay(action, obs, signal, state):
    """Move only V6's known second/third land choices at a window's start."""
    del obs
    try:
        if not _v8_action_shape_is_valid(action) or not isinstance(signal, _V8PublicSignal):
            return action
        if type(signal.step) is not int or type(signal.own_unlocked_land) is not int:
            return action
        # This repeats the final V6 ceiling so a direct overlay call is also
        # incapable of emitting a fourth purchase.
        if signal.own_unlocked_land >= 3:
            return _v8_remove_land_orders(action)
        if signal.own_unlocked_land == 1:
            choice, window = "second", _V8_SECOND_LAND_WINDOW
        elif signal.own_unlocked_land == 2:
            choice, window = "third", _V8_THIRD_LAND_WINDOW
        else:
            return action
        if not window[0] <= signal.step <= window[1]:
            return action
        timing = _v8_land_timing(state)
        if timing is None:
            return action
        if timing[choice] is not None:
            return _v8_remove_land_orders(action)
        market = action.get("market")
        land_orders = [order for order in market if order and order[0] == "BUY_LAND"]
        if land_orders:
            if land_orders != [["BUY_LAND"]]:
                return action
            timing[choice] = signal.step
            return action
        if signal.own_money < _V8_LAND_PRICES[choice]:
            return action
        if signal.step != window[0] or len(market) >= 10:
            return action
        adjusted = dict(action)
        adjusted["market"] = [*market, ["BUY_LAND"]]
        timing[choice] = signal.step
        return adjusted
    except Exception:
        return action


def _v8_moon_liquidity_overlay(action, obs, state, step):
    """Add one tested fertilizer sale against the public Moon opening profile."""
    try:
        if (
            not isinstance(state, dict)
            or state.get("opponent_profile") != "moon"
            or _v8_number(step) != _V8_MOON_LIQUIDITY_STEP
            or not _v8_action_shape_is_valid(action)
        ):
            return action
        market = action.get("market")
        if not isinstance(market, (list, tuple)) or len(market) >= 10:
            return action
        if any(
            isinstance(order, (list, tuple))
            and order
            and order[0] == "SELL"
            for order in market
        ):
            return action
        if sum(
            1
            for order in market
            if isinstance(order, (list, tuple))
            and order
            and order[0] == "HIRE"
        ) < 8:
            return action
        private = _get(obs, "private", {})
        shed = _get(private, "shed", {}) if isinstance(private, dict) else {}
        fertilizer = shed.get("FERTILIZER") if isinstance(shed, dict) else None
        if type(fertilizer) is not int or fertilizer <= 0:
            return action
        adjusted = dict(action)
        adjusted["market"] = [
            ["SELL", "FERTILIZER", min(fertilizer, _V8_MOON_LIQUIDITY_MAX)],
            *list(market),
        ]
        return adjusted
    except Exception:
        return action


def _v8_market_shape(name, value, scale=None):
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
    if name == "hinge":
        if scale is None or scale <= 0:
            return value
        normalized = value / scale
        return normalized + 8.0 * max(0.0, normalized - 1.0) ** 2
    raise ValueError(f"unknown market shape {name!r}")


def _v8_market_curve_price(item, inventory):
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _V8_MARKET_PARAMS[item]
    )
    inventory = int(inventory)
    if inventory < equilibrium:
        amplitude = below_target * base / _v8_market_shape(
            below_func, scale, scale
        )
        price = base + amplitude * _v8_market_shape(
            below_func, equilibrium - inventory, scale
        )
    else:
        amplitude = above_target * base / _v8_market_shape(
            above_func, scale, scale
        )
        price = base - amplitude * _v8_market_shape(
            above_func, inventory - equilibrium, scale
        )
    return max(1, int(round(price)))


def _v8_is_sell(order):
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _V8_MARKET_PARAMS
    )


def _v8_sell_impact(obs, order):
    if not _v8_is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError, OverflowError):
        return 0.0
    market = _get(obs, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10_000) or 0)
    current_quote = float(
        _get(prices, item, _v8_market_curve_price(item, current_inventory)) or 0
    )
    later_quote = float(
        _v8_market_curve_price(item, current_inventory + quantity)
    )
    return float(quantity) * max(0.0, current_quote - later_quote)


def _v8_sell_demand_per_day(obs, item, configuration=None):
    turns_per_day = _v8_number(_get(configuration, "turnsPerDay", 24)) or 24
    shop_interval = _v8_number(_get(configuration, "townShopSellInterval", 4)) or 4
    center_interval = _v8_number(
        _get(configuration, "townCenterSellInterval", 24)
    ) or 24
    day = _v8_number(_get(obs, "day", 0))
    shops = _get(_get(obs, "town", {}), "unlocked_shops", ()) or ()
    demand = 0.0
    ticks = turns_per_day / max(1, shop_interval)
    for shop in shops if isinstance(shops, (list, tuple)) else ():
        products = _SHOP_PRODUCTS.get(shop, ())
        multiplier = 2 if len(products) == 1 else 1
        if item in products:
            demand += ticks * multiplier
    center_ticks = turns_per_day / max(1, center_interval)
    rebalance = center_interval >= 24
    center_multiplier = (
        1 if rebalance else 4 if day >= 20 else 2 if day >= 10 else 1
    )
    if item != "FERTILIZER":
        demand += center_ticks * center_multiplier
    return demand


def _v8_reorder_sell_slots(action, obs, configuration=None):
    """Rank existing SELL slots within the official ten-slot queue boundary."""
    if not isinstance(action, dict):
        return action
    try:
        result = _copy_action(action)
        # The official action contract exposes at most ten market slots.  The
        # parent policy is normalized before the public reorder helper runs;
        # keep the same boundary here when the overlay is used in production.
        market = list(result.get("market") or [])[:10]
        sell_rows = []
        for index, order in enumerate(market):
            if not _v8_is_sell(order):
                continue
            score = _v8_sell_impact(obs, order)
            if score > 0:
                market_data = _get(_get(obs, "market", {}), "inventory", {}) or {}
                inventory = int(_get(market_data, order[1], 10_000) or 0)
                quantity = max(0, int(order[2]))
                excess = max(0, inventory + quantity - 10_000)
                demand = max(
                    0.25,
                    _v8_sell_demand_per_day(obs, str(order[1]), configuration),
                )
                urgency = min(1.0, (excess / demand) / 10.0)
                score *= 1.0 + 0.25 * urgency
            sell_rows.append((score, -index, copy.deepcopy(order)))
        if len(sell_rows) < 2:
            return result
        sell_rows.sort(reverse=True)
        ranked = iter(row[2] for row in sell_rows)
        result["market"] = [
            next(ranked) if _v8_is_sell(order) else order
            for order in market
        ]
        return result
    except Exception:
        return action


# Make the parent helpers safe for both the official integer player field and
# the object-shaped observation used by local contract tests.
_seat = _v6_seat


def _v6_route_selector(obs, step):
    seat = _v6_seat(obs)
    if int(step) == 0:
        _V6_ROUTE_LATCH[seat] = None
    if int(step) >= 153 and _V6_ROUTE_LATCH[seat] is None:
        try:
            candidate = _source_route_selector(obs, int(step))
        except Exception:
            candidate = _ACTIONS
        _V6_ROUTE_LATCH[seat] = (
            _YARN_SECOND_ACTIONS
            if candidate is _YARN_SECOND_ACTIONS
            else _ACTIONS
        )
    return _V6_ROUTE_LATCH[seat] or _ACTIONS


# The parent agent resolves this global selector at call time. Rebinding it
# preserves the complete parent route while making the public regime choice
# stable for the rest of an episode.
_v154_route = _v6_route_selector


def _v6_hand_count(obs):
    try:
        farm = _farm(obs, _v6_seat(obs))
        return len(_get(farm, "hands", []) or [])
    except Exception:
        return 0


def _safe_action(obs):
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in range(_v6_hand_count(obs))],
        "market": [],
    }


def _as_action_list(value, fallback):
    if isinstance(value, (list, tuple)):
        value = list(value)
        return value if value else list(fallback)
    return list(fallback)


def _normalize_action(action, obs):
    if not isinstance(action, dict):
        return _safe_action(obs)
    farmer = _as_action_list(action.get("farmer"), ["PASS"])
    raw_hands = action.get("hands")
    if not isinstance(raw_hands, (list, tuple)):
        raw_hands = []
    hands = [
        _as_action_list(order, ["PASS"])
        for order in list(raw_hands)[:_v6_hand_count(obs)]
    ]
    while len(hands) < _v6_hand_count(obs):
        hands.append(["PASS"])
    raw_market = action.get("market")
    if not isinstance(raw_market, (list, tuple)):
        raw_market = []
    market = [
        list(order)
        for order in list(raw_market)[:10]
        if isinstance(order, (list, tuple)) and order
    ]
    return {"farmer": farmer, "hands": hands, "market": market}


def _enforce_three_land_boundary(action, obs):
    action = _normalize_action(action, obs)
    try:
        unlocked = _get(_farm(obs, _v6_seat(obs)), "unlocked_quadrants", []) or []
        land_count = len(unlocked)
    except Exception:
        land_count = 0
    if land_count < 3:
        return action
    action["market"] = [
        order for order in action["market"]
        if not order or order[0] != "BUY_LAND"
    ]
    return action


def _v6_observation_ready(obs):
    farms = _get(obs, "farms", None)
    if not isinstance(farms, (list, tuple)) or not farms:
        return False
    seat = _v6_seat(obs)
    return seat < len(farms) and _get(farms[seat], "hands", None) is not None


def agent(obs, configuration=None):
    try:
        if not _v6_observation_ready(obs):
            return _safe_action(obs)
        step = int(_get(obs, "step", 0) or 0)
        state = _v8_state(obs, step)
        signal = _v8_public_signal(obs, step)
        _v8_opponent_profile(obs, state, step)
        if step == 0:
            _V6_ROUTE_LATCH[_v6_seat(obs)] = None
        action = _source_agent(obs)
        action = _v8_opening_queue_overlay(action, obs, step)
        action = _v8_apply_early_response(action, obs, signal, state)
        pre_market_overlay = action
        try:
            action = _v8_market_overlay(action, obs, signal, state)
        except Exception:
            action = pre_market_overlay
        pre_land_overlay = action
        try:
            action = _v8_land_overlay(action, obs, signal, state)
        except Exception:
            action = pre_land_overlay
        pre_moon_overlay = action
        try:
            action = _v8_moon_liquidity_overlay(action, obs, state, step)
        except Exception:
            action = pre_moon_overlay
        pre_reorder = action
        try:
            action = _v8_reorder_sell_slots(action, obs, configuration)
        except Exception:
            action = pre_reorder
        return _enforce_three_land_boundary(
            _normalize_action(action, obs),
            obs,
        )
    except Exception:
        return _safe_action(obs)


_kaggle_entrypoint = agent
