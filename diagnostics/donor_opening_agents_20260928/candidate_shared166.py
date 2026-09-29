import copy
import json
import zlib
import base64

_DONOR_ROUTES = json.loads(zlib.decompress(base64.b85decode('c%1Eh+m0PalH|YCGau?MN^jL<jYJHkB6t~MRuCEuY%dmA%nqRKc^b^WFI06dnd#<c<{oj1ltxcHICYpA7mo;cb2E?sJp1+E|KlHjKR^5K=l?wWUw`}c-~RsV*>^vmy}SGH;p~?eXaD<e|M!3Xzq9Xt{^iBlzy0mk|MT~MoPGE6&u4%6^sj$?_x|Dar&k}(UYvdY;r{O9*^8TBe)+E#%V+%b@c!cu`9pqq^Zx$qmlxiL-`;rl)0-df-k!ZUd-d@7?8RmH`oj<R_wRoD!=@b{9zLzx@$=ccH?RKr)4TnnE`EE|uE)n_FF$R6zwF88ZHJ%knsc#w@#2x}eSi7%=I!ghzPtPI@zZYu;Jj`(3+vZyo+G>Y_U_fa)ypuq;XmVdeZK$j@$ti}JJGS-FWs>_JUEVjwA~N)_pi@hoc(zJ_TeXBFxye%ZFu+g?x&B3rzPKnSyGL<*fwfEywI$`8~4roeE0GG{r1!2V3EQ9r{CJLdc*NQAD_G*a?5V5PCi-1>b-|~&By!ro9!5tr#@PpHMH?ZPb1iw<<*1C894qeuB+91kM_6e_wE6U_wBb$F!WDPS+^jVl=t2+-f_a?FmK<lhWV;6%xu2naBqG+W8A?!vvGg=b@|2H1O7Avf2m(f##=8mb}+^cf`J7G$q5IPOz5rw>a~RdJwDqR(A}@64e0h&r3aJ8Z9X(TqoOD3Z(8vKKl%-~Ds}@Ny}*Fvp}zYDJA?5AlZW;08{~H$pDR7TR}XLB-oN_z*MGWy|MAV+H~(Y1LBhW;#w5NR{SVTB`#azSJUSMO2W%$dV3)gNb8TTC?%%#e{~ZQWS4IE>3}A6y!`2S8=sI&oH~-z3q{EhRY%V%VO3gDi#e-#nm~OeS^sW*fy|b3+U-usO`u)SZ$NzhH?qQWSo(2v$vV$h$?!P5H5qgczPSEDl<~Gh6(J$7zgZ2E`xJf?8^F3{|F<qyQ3s|k^6+~_ATLu6Rpa8j_BQXUM+k5WJp}*O-uN((}7FGNw;GEGXYR@+gFml8yZH$8)+Jim~cw@(B9ai;rR7xlxI!+7CB{mBtYshFbJZ5AtSzBe_fuFeWvZ8nL!`=ITsUv}h2?8_aN0V`2QBw~soMNiSH>`YR9f`~M0NFypXpuX;-1VV79EKlGBRm|gaVjNxc-!;{Z%JqV!Db4cS1^9`z{7LW;WH)$i~-vNK>R07|LgTVuI8ohgtJisRVeH%yadOqv5tzL3)zdYL&)}P(5LOI$JbELHStbnaOiiu9^UNbv0^;kK2}ic0dy|+GIqeMj>NbRIcGZCd(-A_6UF8}&oYS+463-MVcL-k3P;Y^rNyiR?}vF6E$@xFTH&>$kM?pQhUc<8GnP+_Z(<o~=)hc=4vd75_i*5G%5u{wcK<^9oXFavJK}+H#F>EZ?izwArXu2#8IeZ5Le0|QNe4{Sg4-Jo(y5+HI5AIsD!5`dL#`O|z}8>Cx_kfr0i_?F9|m&VJH9GLkRZd;1B(M>80aH|o4THj4<Fy(eg4b+`}h9}x)*2UxFSvG%y3>ok4jFNdw_xyLO-3+!{7`IfpO^Abv!MShyvb74M1_Br09$A++59%V4-lzX$Tp-l7%0vB%GtAnV=6$Fcq)yw)b)Lh_d`Lu?KG_Bw;o13R3b*XU34bFy(mlo;Pc@#<~Hx1i`DBG5q8`9T*7M<4ynR9E=2=%g@3{<r~Al%#^q7i#1Ym(KWm7gJaY))Jry|9%sXE(a!)ZB<oETkICMW2NAS5QORLD_@1h>Qh0Q6f+l)|$l(mxj!t?;l9773#`q!(F#@=;l7Ps;g(EX)=O!%H0Qs8sk#nz{wZ?)Yg6}%PBYHHRTNDr#1Q2F=3iLs{1mM}g7X_(L%V@%JcrcQPNpI|8`AX>`fSoRaYVwtz8xfRR%&iHJYng$sTkcmkDWALG))YkXK$1zuZ_4MIJ8WPRaCqs`?>$kvvt!KzxlYHyyG*dR(S4Sa#lg%+zn0Qj^1}gjmbU)5*^u^MiS`4!z0Jh|3-h>D=C72$A+LmeKAw&FOA&q9eyi;dQGsRo{}`Ul=ZA;4XD=?!J+3|Kd&(4%IMhB&IW(b6I%m7#?r(4JetI&NRnF@BhldaMi(eg|O@mP8ZpOnZ(#Nyk41~kGo+Mr=LwF+wR&CXJK@UJh(g2Q&{aZF&tpw7Owm%!&w%p?5AfosZ4XlSQJxOX_Jv<)V&;X<8X7zty!a1YfmG%&Bf>GPPoKhf<PlY}?p=74iC&u*$>r6c8xZ1Q>3HCcYd`2=_I_pF-2DbFAD{k1bA@Po01n~W9Ty^<Q6eC4`4UCpnu0j-h+8LzSsOZ~(Sz)Bg3VH&f7XTBmoeeQ><d)k&=-TMYc9xO{7*iF;%Hhc?<`9E_cFX5my?j!33HH<g)*&Yim2kn#qc!;gj(W;-YRy!_Q!+yJ$U<Q(a*PKViBDSwz4C}JXNJ2BIjH11kW*vnqg6O>P|9Mnuz=M5G7Z9w{~}{Pi)?GizXz#3;0=d8{_wZMhZO&xkyALn1#kC<A09ubb75ZOy>#-h@0R^X{IwB77r-4Ih^p8K&;$YLA`e~~A*xKCq+>*hA?g1bXnbU~9)gqt>nXNz!8(*7LGCBa;GD!TEE;%-!a+bire$FHW%|}JuNFG^6k$OBqo!G?(&OR?d!Ep!7n^6Or7WZ}D;5F%^_%bE2A@>f(2<5`3LBiH;FVTVMZq4hdNV*I%85=Rwef*LEsVZ9g9L_ZcSJZo+P>fC_-@cE*5g*NOL|PW?`)JC3A$V)iF0*fl&2IxIef@m6cUad-80pIaO%j@^YR4oRfaBFIk%@AAR>Z!P<^orStUf4o}+;a5lGio>~1&w@y*+RK6`PCqYBC!L(6CTP|j>RSj^M!FV@DA)M_&FQrnuj7j`jSR-6RIw96N4OFoIM#;Pab0_(sX1jzZO)t53WO7ks^C>_`nc*S@_++nj3{aBvXZMpSniaI((*~`W{B^<a<dNQ+wnvpan%2C4sbF||FE{0w)%&1d)Qe)-Q$)UH9zD%9+i4rNuX4IiOWk_^Jm>@qfj99I%+-zBC1bIk1<!L}xDFZiY5@n7_=Hg#`LV^i|B>={)&7*k(`B2ysKxuA5>c|qczyo9nLXM|Xrci+=3ie13CWarVF^mB3Y~mJijpW7Cv62C|lvZUqyp-l93@|d73l&*QbyumoAmQ*l)@52S1L98HaprFy17phHE~~q`dR02IKG}Di^;^wjwiBjYrDf23pYq<Gb_<64C1qF2{T=2r5|VBF6Y(Va@lI@0%udGlZSWzpO*&a9GLfJmf;?zOSfea9JMU@aDchgwc`J)xOLOHscTo|QS1c1Kd{EE}crTlyw8&H?Aei(qs3L4=pnOiPbbpKz72_!(FYg8B7=2nZ>t8a?`%AK(-F!3zl#k=#879tg`Z3_viK3e~rcp^tU}e$z(IKNi<~t_OL5VcdDJbbEH3g<Vrk*<Mg<~QyWka1=?PNm>kJ^fuJN7phU&%u(Jq@J-e;k=GuT5qNX{z)`6(fOxvTUkF25@zA(Y)AN>u5s(oDs6a4bvh~+fvU2^OL&KoZho$<szelC~Ps{bfR|<^a9E<u6@!T-|E8HWV_usxMP1JTb%^JQ-a(ncPlaIIQ?5UBj1qlUA4H)weHQ0=MS!*zTUOS({?|_(7%vSt@_vQClIZ`afb(_C$WQ$2G2mc{J7-2Sh~X72)2Y%WVKEdjnS=<0)mBJB?nO7jYe`@M%yl<XSI-e*WhQ2KkJk#WWI<fPr_^53g~CY|G5QYjF~Wt-{X}93X84J@{H(ncrxV6f%aNV@#TL&-$nMxG7R6wF>FjO^O9=%a&Fu>v^IDb31X{YN~4Pxmlb$?No0*aDxOK=WkfAW7@nTV-n58%+isy=TXkU#lx|sRYCU+o$Ayd<=*hC9s3+{2Nx1<X1LH7o#`*0{*`aeAlJ_!WPS#vVtOHK0oI`c@_`sAgf|nEu;CMPM9?_YTHQVy#suNjx0+f2DUYNafG{5sD?*P^>K?TXCca(PL=dGC+wxz26(kx6C6$rUSVPctm-Yf^HU9~4Vh(f#z>M@hs2*QZijOFz;42b;^GDFr-CxaQYQSk!djg4H*xy-tTlK`Ekx{%nCH1s|cWu5b`ZwhWzQvawYPmrwiq|$FD2GHW`HSCf55>VY>T#kIx8V6ec2_)2MdYatd4GOxTelu#lHBbm#^6<1agEz1)I5VDhyQ69ET}EzH*hELMh+HxXN-dp-AsSCpqg3?WGM}`baUOpmY=p8A<PPd{$U}Yxym+4$RA=Tqdt8ONXetUB%FIR1MNcIKDz-x)hTH~A%f+D#veHB*Iir<Y!73WOJcaw5QhNczV8JXv^lu4e+H`2dZwBMXfX$L9D8CkqAi9jm?sG-bfOT5~w#t^yy>lvYKw_5=!FNz=pHU915d7yfzu#*W#nS8anl$C#)sVU^pwa-u0n5~ZBor&bK3pp2@bn7@vV}h}ZX?W+g~MBiRyp^E-TQcW!C{)S25WJAE%E6PpVkdbc?Uy`7EoT5bbbo2KL+d#(f`~gfdgFzPTxLS!_)Wo-+#aR;uNe4h8(T1E2J?%c=cgi3{e6_h*bH2j}JfIeS9#k>{%;gc)Q?V<v0+u9tAVNB0Uts>3#IJS@DF33kVEzyQP=>{)oVB;L!zx`Eg*?;*IA4Yu|<j9fV4@OY8g5r07aKJ9cxLHQt$haxroYrk8_n3r)Z*F%hL2^TvIhwMp^VRZIHv;k2#~KUsVfTtR<CF&(m$Ow+B}$_h^Jjn%La>c&t`&<yLAjiTdE2iCn_sL>7E=GU&HRE5#v2DG#7zSx2<8GwOJ6M}r^jb1al0(2EeICMEPh#;H}GFbTYZHU&=fhRi(DEBDl%zcLpGhMdKw+f?PQR@hBChqB=nG1j#+l416q5z!f{gRX=mBug+FaS^sLqG)hUPEJW1p?wEn%1o!EFNcE*u};NoRotN>ZZe;89Y&QikF^kg(}}nxB-@u9?+~6gfu5>pN1xQvo>JDRV8AEPkwyN?a3t}(M4sU_|?oWql_v2%Le9>q5L;}XoFE+At1qOg|VW14T&NlDS*@b@YR~XwK_aS<RR(!GNYPv4nXmEl7a@zVemJZGq8O+S;$@~?{lWJQ-f#&)j14vKa4MAsg)mFkPi{#jYGrAWy$6f9%j!}nKx=IE)*8<rqAch#D+`S1PNA1q+g@U0Q!wK+UQ~<3h3_I&#WuT`#;_q>f5mom865e^1NA3u<A<%yJ@d1>jz;Dm&rkvP}-|Tt9y%qX6?bb0-?(q_Qv_!tT>JW5YQN#z~+Ql7*GVlOfTNZlI*A>I@TxUYy|4S&rrxeS~iA4Xlk8qho%mh#GG`*qdW{klnThOlyZ|}s76U7$cqMTRvwD3a6`}>26=!w1zD1blNa>CNrGHf?4MIf7`a6kOPLgQL&<B}lV@lU!YK@ygd+l;4^`Aai&Ky$Zl8xVaakixs3?wUuL;<*kHx0ZCT<EagG<8)8x-P@gm)SAh#?xp;nkSxfHwjJ2rX&*GpP}QJ>X0C60dLuwO5e_)ZeN0dP5GKft#=wuXznw*&o^CpeWlAAS#ARITsGua)f-8@HIF+9neK$_5%znEdQsMQKKX`perzjh$I1M55ExAvQ1INTr7AQUP0E@f(E%j%88M!lxLbj67}DOHFDxXX^Te$2XyXWsaSB<A@Cw{+^H?nkpv{c*oKb!W6CmG8X<2!XT>mj7>7oSWvOTonQ?#UIBs3W+LB?ocGd_{fxkUopm`Yw3X~BhG6l`dWhvCh(856xa;bntFGu817Fn^{Gg(p^n4}ZfWtNcA8-7FN-){>ntOK;*UG$>R4s-v@@C-&;b@NrUY6^3pQCnaxbzosJC#43Akp`YZ`lRw^^Hi4t2kLqvNMiHA%YtH}myiX{2hBJ2A~}9M3}&q`E)34!<)3p|^x{s*Qc}5@pbG8nCJdQ=D29Xz_G+#O==Pf_M3Qj}gQVxf4rkTCi}frM{ZT5?;L;HJEKTEQ43v?&oAw20%>h^Za6BQ*ZC9`nFytm0$1QvdBG9j@Weu1t9S7lfAS3=n=c#z?2-?g7SGM^P<zRWn>4O5#B)Af(d=e>-;9)k53tHzVQz-lZv&;J_oC2$4m>EDRI9|aEeCicxLKExuW>Fv>Ks>+&v;yuLT;C5;;9w=jorOHCKJVd`W-$eySi=fd53E6C6k*;HOn_9-0HJzLP2}_w=f*)s<^V7Sx1PWTFfGN8))Pq!%b{45j}AISnhER`<|sicHF)!!c+3+lH4T`#c&bvoz&8Re=+YUM*GfKBr(U8a=U*G2p(w5ZEP)D^@{HVv>**2;g*(7^a3X}`YXFf&AvuRAaPcuZPs@|W;5I{^Q{d?{iCH#b51X3~d`{pyZ;I~7?Z9D(jw)vGa6?$5a4iRS;%u_WP<1bd_R=Utf&Deb|Afx4%+WU@eh4m7o`|2=MNAjR!xTUOS~FC(oJAyjn=3&88j27%orK$>d1Pnn+2BTTt&sqBot{U{NH^n=eV0pT?B!?be>Mo4q5CfgHnJ$64rL{J=bP$cS4kuaVOOP5wZQ@>5wF%saG6N#);K&y(GQ$;vB3@i>Nw{QV+;Z2H@-4pyL-ngdqRu>DckE<-V0U?f`laNWE(rjdSE~brl|{ub*To%O(?|uTZ_h}wrMcepO0%PHlN?F05IrQU2kLOkUv3J!Oj{#r=gFnI-gUB;rC6ac<%BG*=T*i`U{*)k^Xg<Nx`yNIX-I(SPHITl`7%u!%b1=u=6@7g@`H4*l<jjC-~|5gf8F*{FMbi80?N4>nm9<m_wssG;;7OH|TU#G-DKt2%1mM98f{dL>@!|BxLna;BErKX-a=<;~<I)MsbC>Ah!rgpY4DeW9@F(BkopQ)cxScJ|17r^8$MW|1^;Rk>7KXed0KDiiXSpLEMqzzw3bu{t}}}(ac^oWQQ`M)J$Pi$<9k7#g2cO7uT-^mjK>iw+R42fJJbiv4{nfgng_cRxzt1IL(#q@`x2)9mmd13~<v=$^eDvk(EjqYE{gYuNu<2WwF_^MqVG?6xs{Z0s3|6wwLDNVx!shn$NBh=}-@z0Z?!$2OVf(jAvj|M?DZG-fDp^!xT8sWlh6TtojHTUXYETwi?Dj@Yw$}QQ~kVC*>pAty(gsk)mGUH$Ok}pv(CauR?i)ag0djZM!HcY+6bRaJ_f*JIeOxlO1fHg5r@RwDd0TT^SknfCX$=Nz%8|^#xi4j<q8QKr53m!4`or97>?zW|T-fFc=JdZs;L&EJY(5LoroKnvy7AtR)zS*vhEw5i}#@2Rm*K3{q3!6uvH^(phREv!Cn`fe?-}*NXA(z~GGWu83TyVJ}lZCKdO9sh9nDd`;WG;k6)v9eNeKpqF_P4F$C&l($Eju9fsj7Mlk4)g+n}XqK@96sIgCv`_-vxdwsaC*Z6hR};%r?MpW=i>?X<fC0IA#T)1xPbwi*-c>6l&Ivpm-~b;iHEf0Pum@#CXOSeFCSJ;$D_F*DI{HG&nLJ$=9W@)v9&i+?%KQkN(y!qrjvQtw^Fc1t2Val#LH3l-lnC<f{ln`|uRh8OKy8MIC#^tr3QH7`t5J%G9qfUoJ_|o24=5Bz#H&6zGritT)W*Oq3I7oRIAvRm%S;AoB9vd*z0`$}Mz%4Adocpl@id7T<lK^D;P6K9Z<rut25p4PscG2{pL)U=Ps5xM7KcLE2nd-_1>a%0oFG8kx}EZVnJk|+;4UB~mI|n|9>S*{lvHA+yL2tEM5ho(6#S}HDg>l65sMzPpnhdi<x|X#bwmNY2}nIfPl^nnoLNdIa~2Z&;GnE-p9kCs2*>isNKu#RKn(yu1iy&K=9&npiyjcX2H<p+upIocKBDycogM>5p|7{-Nu^Q?2khZ|8_R!VpiX44t^N@{j-|@kw>~uf+-N*&q1AegROS4MDa4i2UrG8$;;p##MSou`m02}2s*IIRM*eG}u+Vfu7DP%;P!kg2W%p}AyL?szOFC31VyKFV!efVdr8Z!$2`)($k_qdc5zrJSPymveeKJ&qLlH2j%tX&gG=-`GNXDAMEWz2yIz>$1Khwhyz#!9jOYlIV$!iK##HcGgq?Fx}k*LCK#DzSi*o{(AsVbW2m+cFN!SVx>3yoD=S)n3}E5-VO4(ZiE0R&7F2@U%u4d4ik17QQQGmmfTUH^%VC<W6nUX6EgR~0MKCkjtjp@}%sa!CR_EEffXG&i>#3`Xd2N(@%JQiRWiqIm{bZ2wk6?9!?+NeT*V7*rrcfY5@LD)t&oadHGeoJvk~WQ5#E$fI3Z6?{dr7d6;pT`5J?{)nA8R0IWmfP)JNS_9a}<sYOD$gJug&ruTOz$Me=Kt{P9#cCif)njdoJ$eT|ms7_-9)dCspG5M2RY@qE@ntz3s#>V}Z!EO(wE<nyDuXwCK&wCiQ8Dxg?PCc9P_r)}4jqz$G<RPnRFZ-q*ELV3O^+FYVMsti#hlEWVP)z17d6o9JcOPI{9h1j2zqoI2<B;O#ezcr8xmY9ObctVg7;wqlZ%z@rHOK6^oA7>&By`fdGH)hsSu$mIzMAUlHhH<e9|ghy$TO#r#51v3__qM(g`IWg2lvk>uhp5a)j4!zV~)ro=BhqqJ00HK^$UGmw=TvxE~YX<;#2eR*fh6(1HDoff?EVi2&R(gbvD(r-zDKRvE6xWH+qj4c_DRx*WQk*JYSF%v&@C26yA>o{vqKdez5X4=dq-a^PgnKAxm7S<Vz<x|kc#BjeT{!lohj^YC1Cy#IxjQ@I2U58RsNkCw}5c`wYWyvpMHeF=mn`9+}^e+=f!^=#(L>GVGhPR#bpi_?)~Bz(>YF^mU58|NbivVEND;-f=}v#9;6Vs(lpdUTA+!gcqDqaSR<`@ik~-CRjC83*biT(*zpIgu3V?K@&Nya_xov^-H1{j4|DARj-8)y&Egk58OpQfTvFm<hI*EVy%>{Yj>Sy;cBbpc%of4$HZNu*B=BB!)?^lb};|aJ3kBZTJ@T^^B94NXPxYeySa{4vRx61WDs{^v7+Qc}5tXM6D%?TQ+O?mOBNY0nn0FUsX^$8IN+(hU4sewYXKn45upQf;K&__Q|ZJ0r?h+>^M<(v=9bTVG>;#HJqZ+p&2CR<xs}~$w+JEX|SD8IaShPOIuoNoMcficN2UmTq3mfMMBb^moUsi`~k6q4Y9<i9u$C>{Ssz`E=HTNs6QzxbB;w_TV(SI3qqh1lT<=>5Coet#LAX$Wmg)_A`P8?VbYMoi=z2|K}OKY>%!nIgVx4bjuv7O<&bHY9zvpvXID*i`%u1e$Q4a7uI|a`MjhFOTMLKfq6Uj_5bXk%(A46J6V#9?T{V;ZIHu^t4@(9V>>4M_DH95!FL0sK_1-43*ac_Stx{G_8UE$+A?<6n=p8Q+@zrDpz_x6bkpRAY0UB}R7O{$F97w7yX-YlYOM){S@Xtbtr*vV9rG<`nwN%G(&I)OW?gxrs!bBtXqHNRs$lgGqH;zkqYtuDzti_2tg}Aj?9Je+fO2Z%%rKLV#p0Cm9?AsJk26t`~Z>9}_Z2&|?AY5#MoSdPBLRyL(gFOpv1?&##6<y+d##F=skGC%yZVi;EB|V!AMQbH+ZQ#Wvs8+4utd8xiCh>sAQbk_20t&^6fN@=E_$0O*4Q|3~h1d^JlYuU9JQ`Q;arr^dr3-V(L0>=&Hj_8hf{4NqGm$$)q-7wtKz`J_TblV%_!v=#OKhS^!Dy3)Vsu!poS8D2%H(WN*h1;cNZm)4abmtUBO0`|5rYVom9xQ23#~j90S?P>sglf+Y1S5y@md)1KsB$pFd}uZoa;4dvc<#zNR+~hPV`)s55N}K0yF4_vBkipKE)bD<`MTn+C9|fuoO;)`*Aw~Ix%d?G@PH!`>`ms6?{3;GpLM+yO#-8&yP%?t=_hY;)jM~eKHf01?QBE1sV<dlrnYaQmr_xK~RzE(A_lD3hJ|^hXu=x5P?yEaA%=G3|--bW_bNj_*;s8VnAA}p(4>E(wJgCAXu~7TSaOm$0+pdZ1Ew`wZnY9)P3WSNygpD%JU|HjWh$n1JP#3%qk=;5ZxyHe@Be!6${(W%Hq4-<OKi;r=^@`6SbHiux+BxLZO~WpVQT=NQodwosO1RB|`l%stYNi&=`tz{Uu5Y*|#{l^r0DAvPc*js>8zcW3z6ODm0Mreo`6<fQn#H?*-7Ol#BI>4Y9m<i%-*_0v+pQtXG<Ym7uNM_H5^o;AA^#)t4;oQz*>RVFw|gi0Uahp}L8C_U<3|bxR;c-Vz1PL;++rlH%i4xmz%~6P6d!-LTiGQQ2ee(k(D2*uGD~pwjZBB%oNhK5*}|sh}B|`KXJwk_1Pms7tm6#;>l4(IP+~T+C309h8?bfV_ZcQIls#N-=YLjJ<QxZUcf{?~tcCqlrpG8=<(oXw|3D3rWl+7>IC=Yi&xe5)Cme4<>`iMDCABR>*Y$Q97^i*<*4<<|K?Opu9>>74V301EgAm)jp23hEySzP3uD$=WC6<0CEj0FojSh=R*O&yXf4*wW&|E9L;W%9l8`GdtunCL_hj{U&_^@933#c=AB%(U(cOf!0$OcWo6}UPSJQ8l^*@kH&*D)M3tGyqsDB%W;+qA=0w4_eJgp+E|nMa6l$BWbGLU@ly<5BU!qNYVWlQm{qF=Lh2F&Edf@(DUA5*gsD)*EnU6nZYso@>S`3Xk>3Cq~mU?CzqPUe@7ocFM{R{{O?21~?m&E^-`m>=X(-bYS*fPQ1X=l@og>`z(7YhDGqv$dwB^FMz!U=~d!#n7zK1q&&mdzpgvaI2iGBfZQlVwO8mcbXGrMe{=VV|zN74~LQM8?Q2sA3@*@Fa_!BuuO<^CX2}A)=-w>}ShT5x@i;xxgT&6^_d~a9y1|XUb*^l`@DR!sloU;Ov9JC|z6$7{Q!b<)K)6G6lMu{njuAQXtx*K9L{M{gl95fth1e<BE;WMR1Bz4j!QhPs=8+3s#MCiuQAPb^DcFT6Xz`Bx#pDz=(3QgdXkqr<D%(1oxbw?AiTfG1|~IXGMUeLO4?B3ccj4tVI)rFQDI716!Imo-q#s1p@YE?aiRAUgReM5LIS}s&1Y!QUle0Qg2^`LZ?x$B`>409%1e|mAQ@DNjFK&JuQ>z=@p)`1UI#VPJlW2mZG831a_K%q<A1dfKg&ue97-@2f6khpR!-no+()|fIv>kk~0G00v*$ZNlO9#DYZ!8sMm{$_9IzflLKE(aAZSFil}enh#3Y{fjYeofRkYx6U}J2SN+%nurQ^Njy8zM^5Qvw%VMt!Go=B5D=q*f6qqUNfk_^+WlR}<IQhm8ytUE^UhCzQ3#8nwyvPv(H9YlX4WMyRMzEpsLjmA*8rRl$V!{PcF{xzJ3Pi3WX@~sUYx%yNFQJN4v3271b!ggtzb6;lYdMg4rP^cTmb9+@!dT8oR<r2|L37feoZIxfAtUJ|S_&c=#3ac;x+XXh1&hAW1!!Qii0>+)_AJ$p4-?QVc)l1qfF2`9=yfbC$uAe<z(<5fuP9G`7>#G+>G}17y$xNLQC`ohZZP?FIhceCX0aZ$g!QD1LEE(O{)O3LlA^%dxH&ke4>;<C`$BQp?JhOLI<=`e+314aP+rp56Z65i0%4a*(9}uMCeR}x#aB3kO`sjTOI8JuW4m5N(f~_U{B7VTPZX7Ql<1`6?i->fe-7;{j5tM4%$<lf7-ldfn*(3KNYz?DLNeo5Fv-8Ytf+L^wRa|im?pozleo($w)cu^@tdmrtx}SBYC(LghKm~&qeF->M0n2PAnZK%Z*=RTW(M3xwf_xhSo{&2^mRD731>q<ZZw}rb{HX&aa;5)Q@7iO-V8Mq5K}-)!LRf+>|rTwPjCvneS7klpEwk?GQ8P0QpuR~aci%SKigb!A2ezRWm;Z8R;d{%^0SSh5GPAFJ6?)AD&K%`q<^&_I;K3Ng#D@*b|wICf%k#jcK$ocN~H&Lg^%oWgVZl&Jk^#DWdV@NT5#k9xT8g@pf`3pUbXVqRkwP)j)H$J@IBoZHKN)riv&>{ilo^(YmwGMF|^5xx$Mn*dnFYZa&QBczpTuCArGi_9EzVXE~8ie!5P|4{?&jhkX;NM{?#*4-`FhJ`i`lxvIcPHE_s?P;Y}J9ugR6%pP2rPF&1kwYaPw4ADrErm>G?b0#B&YR2SIv&{V~Qa4e1?v-Gt*@kLCXMhE`f?I&E}hd!hM9qjtdUV`8|NGz`1PDTrljdv<+96J-Id%HMj?=F{3Csmw7mzTq`E_O2#-8+-3F#+PK!=gLcT0B2hU;J)zz$*3yT;QFX<}WYKe*O3V_{ZNb&c6GZbu*Hsg4`p3I>EJAKcs|){PxDXpWgg<_t?{i&%0i&zW(sT{rx+D-hzPPSXtz^M_nWf3veKIzb7Zy;itRiTqIsJecxX`y?OikukY?YeEjr?0vWG6avBz|+dM~hb4MxBy+l%-^?yzXwFfu#k*QqDozby7@`=Lur$oOW@83TB1Po?7YP=15Ufa{tl5fH+sYW4*_T%tEvjT5qCCM8SC!p>F&MdK8tCQq9Co<m0-)zUIJoP|S>kMuD5n_dSv%GqcIRjh4Px{`hoD+31nM8FRkksFs1G!|Fx9?ZOd{r1`Hs5i$H@}`S?qHtTxC@0sTE8p!F{c=K<MK-~-g=?2gE4jx3~XKUF*2Z95UyTZ7*J5xQP1qO0cDi{C%V*4&#35$`kPk#z>ogA0(xBouY#Qt-7>B%B8Y6{hJ)yLZY6XlEE5-BUc^KrGPZXt*5T7?nm3WCOr#!4_=Z3#oK`5~!O$Gs+JP3uh#rrJF-agfWM-c8<{6tJ(DuTGrFWI^XoMKAt)ld}h*=($sr9EZh6I5ZIP*S#OL`*o8l9b>&8N+6oHe3ftaT1i=g-Dfe2(XPTD8Q@8n7%NYHQ!pkogloN7pCGV|&k?i6C{+ad1fXHRp^zQG32j0zy8O2H6tCPtksKiq;U_POrJdX2E0)8EuBg%wUP3w#vQ(Kau9Toh)%2Pr!U`M3Zq~O<vK!=)$C_6N$_C0NFypXpuX;-1T`Ho-?mE&qS$|TwA%v@_9=-^Y6(}#v}(&9I_rhV^Y8vusy&igB~wm`f7cTt9j`=;cS#Z6$(2GFTwF@tfS)RLiS?p5VHLm$Z{nl*4`TGxhCGpoY!Zlozk?~g4)|YR#5BHvYyQY#$|yu_g?Q-B!8c0nM4Q%Rb10B?UZK<IDk_)eV`YeNeA8=bG5>2M<4CwLJZGkd1gc@a^fR-4$PJ5z}R)ts6wyT{R`=HB5Nn&Gz!KMXM%DBrTc?Y5rAz)h&03c?Z}9-;P!@tbgJhPPE2Ix30Lf9$Q45#7%t>>_2pq8$GzjLVgv~?JUyguju{5}NW{2Y%*Ik1Z<LhfmmVQ7&A3~H)k7V3o4|%!s9eM7VMOcI1mmbkq_juC>v2-YVFr{GeUWx8U6zOhp>WD+h^4|S7M|D7E6oIbAgP+E8*h6bM~^7WFFSWYa_vAKR_6u&=gb&#7p5Gq-t%V7)>t<HmmqjGGlrkMrvn24d%WpCor95}bNN{qseEJjmznameX&MLF1lv241wz_Rqw0d*DXwe-$>={6dOyNvVzBCZ^?rQTAV1UR&Twh>a0{M8Pq0dqDP1v&XDcsq-P`<sh4YXMbd6%wlcU7YSu5-0Qs8sk#nz{wZ?)Yg6}%PBYL#bhvu~h#?w=I0g2kPfiKGHn3UWmPzfxt3tl5z?{pDVldt^Th@i|8k+lgYH)8R+*lL_;Ql8$irKcc@2a-%Oep5cz++hQofWu3de(#CWogHf)$aOjn-X$xdKd{eovN)Le=+{y@OMW<@&eGOHu{W$xP1+CW_BIy>EX-JnIlfZ<hP)E?Io@g>UyA6<_FHX#hzcyr|HtrbcE#4uJ+3|Kd&(4%IMlk{dtRd;C!Mq1aQC;jcRxKD%PME}{lmkD`^B%!is#JTjE7aEk7vIb2#0q)NxV{q@J0-*+N$${9)OCZ0UQ_mCyHm|PIi)PsvZn4Voxu>Km+TcOHY!TR}b6L6{+&~#peIOgfqE7#NR`>2}W)Ea!P?bJ{9_S<*G)dKIFRk#Dk8jO^cOazr(|4B%`IXP9$SsOW(TUhAkTs@90Gostq?`Azs3oMoTMKL0!vJYE<-Xz^pJ*Wd%I}(F=eH*v^KSH*(8uAareXWjjmB1B|JPW99JV6?2HeKfC4gZRL(KBJj!Q%9%7&!UZ#r*5nH~>M73&{bx7v7ItzJoJZaX<Bh}e*G8t();+IW;LDluErSXw$qnSiSb}I3zZ)E~*et9VwZBZGZsWhmAkSjg8hY<RE)RG^ym$I|BTokS&qyMudw-7iNc$H`PYbn|ULAJUvj2#`HiG5?nxi966$}AhAgjUH@u|z%l5~tH6D0j#1C4iStc>IoTeu(@$_T(KbK0et#HcHpcL=&c{5&RIVCiJ~)-fj*`txKtpx@U73RNy#9AD2t9d%jrbhOlfROZBEyN5+XIiZyR!!rpL*Xz_-AyE_z1Xv%Eb4I7s_u0*H0E2CK=%ox1>ny956#nFQJ~kqi3(p&I#&L|HSxh&;!=*mltf!D7pN;aAWFRXW45d5jrQxJ0CdlSQR2hJ1rPZF&e2DAiq4C8oWW^3y29Aa*L<3!0FsmzcZ*d$!sbNUnw0$TiFKus)UdQ1{IVL0Zv~?}rYPqcX2#R5kj|a8?!PY_nJ(qGF%pSOZ02tqthP{->4o#;tVsc<h;1%Nyafi(Y?4!HnwcGkMMfw~f>SLi?uRa6!K~H9sP!N(vKq){tVvKe?z?IG`ypsB?CpA?*og8KhZei+kPt-qomu-lsXyZzDMwp;Ht6(IquH0-{-2-_%JGEy($|wUeX@+EuN#@F4c~=r53s+d%!rD9zH_!%!Jpt6+CX9_N3k!Tdmi^<{Ii&#=NT6Vk^dMpQff~aI$j&Biky)3dcRE%QW|6w7EJ2rY*n|PXe3)BqwNzBqi^nrpDUWO`Sv*-1if|vn2y=3FS-RB~qtcP}nY`na-fGVBL>Iam9Nwp-wkOPjfqqH0mEsn|WJSWDjejDZL_gYzZHk%5_`YLcq3Fl8#GuGJf`$lYpc!F}Qq=4mr;(Fvf2wDxEcPtTi}PGXMKNBnOd#JuK`(&JH%DoahDzWs>0?m2*U&)ugjwnS81*N{6F**_3(PV4w5H9!WQ6v|tF@CM^>WV;NIs5+XO=jl=|_ND7m9A(STQH<fK@!}$A*mEnD3W7-z1WBr(m0-3<;R}$oK247LJHS$}n|hwTsO!ls)wF^_%av=522+zDS2ydKyTD6f!blUUtmV$W(cbDnbGSW!Y3K_3ujJqIt2k){%XZ%xh!BoR|&V=DD0p2bAGdo;BeX8679tdf}!MyMvGyu#s_DllJ&l7slo$4>t<#*q_K!C*kju5O>P8Nennn|0XBtvV6NJ4tK9w9Ohc*=Em{|w@=^OTI6H9pJLcwNTpVNYxfg~RN%P7<I&U3K{tbEA6+h7a#}1M;cfI<!YHyLCW^A?7C!-@La#&vDBMP)IIfRv*T=J3NPTPYGscv4Y7jC{MARMO#cKuZvt#|-f-%PYm&Nb#$^sR`)+c#J?>RgfjR9(}#Ry;i2lQR!oh(D}Z4|@C<mrm`=B?YfacFJuE)uj>L6k-pFD@(4IAZPcc_bc2RE&hd=^5-zi=4OZ79(1T!%d)b%koj{q2v86WYR!Cmfb`>VRuK$&F2^rlN;NIrt8qPjlO-ECnu{dq|=WvJJL=Gbxm@e_`rlQT9=dq;5a(12ho|6HM{cVsuR(2SZ}xsX0IJh>3qrifJI7xXa`jLjBw{?teFqCrKkSVtT&dGL1z{O{aAI@kSpj*)p(+Rs3f|v&N8`WU^65(NqK#_0-}9{l#n&n$!Nwj6uQ`cWg=H|uBfg-BtXomt{Jw33%w6T?dH5onSxK1R5hxLy)7boQolFj|7(Ty8uQ4V2`FeVt~|bJjRURf1TyI~FHLUc1{*%=H)GUW1BH+!4@zrOcLUvm6XI#NJHqwe72`(TOmq^%a#9F`vfB@0BaF{@G8!e7?-uW*Rf_ZQ3jrgPh9GxPpFAE?GvLMhjG#I*=h@>b%0*LANKR&TxpJLTvxZQXp+>>da%CuMthA5OjCp1htf9dRQLw*RT5*)1qWA@f0xls<a;<~OUty4DNeYzTbVaaIMql?iB5A<7E$dq4NawD(Y!hYRr23H(dJV!0fQN$fi#1X*Lr6RLLap;^(p-O6H0rj1Y>ANhl_>&A99DvTxIoTf=NC?63x8saMwlN9C%2BPa?TCA%JJ}m!z^bF)*|#;%F`h{ts9u~4ThL3pkgZN{1i5SjMk<6;?x2IaGuMk>DxzZc>4bS`|o!|%~P-~7;LnHt&p++;njz6F{B6-9#Z83j>XVR(sbS~_*Xd&1g%Gr46sNKf=G*|XEF9|fn~#LDuBW`9OXp9z!0660)`0PZBW$(=lO9`)WVNv31~EvEbd;_6$kq6cg7QiR|00WV3lvm??p0h<An1<L_A>1z%fm5<YWSTk(o#lNYw)2X)S5c%hNx?&Hg0Jxim`tACzqE=-fx{DUB9in<F#=nEZpHB4l&@m4e#B>vROo!DiSCcNvY?TSF^e#$=KiknmNe?i;;$3a!?p-6+KMFA!4;=HtVUcOM^$0yQH~x9nab9&$#$vR=}zJOQNKqNq9^^?Z-I$}LMQjkMM9!Mu2nE)M`^A`}_Pl}CC(q*d;{=y8!mSsD<O+V7jY8^Cml=bD%9LZD^rh>(khfU!55xS2^RzA5k^fDVDQ%lc6xxy_`a<mGIb(gzHd>;unDpqApiYLMA!o`<~{SG&!!v?g1jLc&0M>NB;o0N>QwN6-ZLphvvs^fH;~G&7juYUY<w+Liug0|82y;~P8z@I0`I1&ksLVH{Rh%|JFTDXsgmnG<LD%;Bqb?7edKL;wi1!!jM66E;A3eUiTitm}?aw@KHKh5ySq0HeuD<nz`rUmL?HB>XXuhjMgv+a)8zDvkjI&ox=S+E^%d1vgRPl@wKBd>W=uJ7POK<uwWcx^6tMP%uwj6IH6MJdIr3Uss{OYAoD^SKem~+hW@}r`n+oMAHV83c&m2lEDlpXlvel`-U)<U0)BG1ts2<k`Q`;cuWsze=J@G1M5Y{Ah5^VI;(FZZbxVG&MLu)tQKymECnw_rQJ102m!o>uy!w<f3IYRvXTP&LlrO<bOIn3Y<Z-@lbV1MCm;Ee#Lr|m4cOP3fEFgi6Eo<h^RmZ04OY^in!);Yf#Va~gE7Ua9|nP)XKTz9=E(I|$sAEyGbTMJAkN}41rtONXwOXnHE@LpJdu$Po52woB6%EMjfosk`VWzxrEp=8<B{eI@Hkp&FULn2WpOOWNNEVD`g{}Hl!9DY9W}5pZfoPZiG&GD<F=h#2EznQ)>H5c;+1coJU?kwC}+f+t}!nChb^}T>`r0LGW#20<Pc7T^-3^~c#o0^uLh?9RwPhbF2V@pbb-1LpIhmA+lvt=WGON~p0V?-#v<xPL%`611N>pvZH`!Zq&l0&y{~sz&L&KHgU7?X0IJZkG!zye8|6!dLnkY8SP^AKP(_3y)#AQPhpK}w2INbui`5q(aU&~CEOVb^<d}yBQLfl(2&UDBPlB)+57QzwI4Ck)lds?JRFiSixHO4Gi>$;@Hh*AwZc_CkkT(Kxh&`P)=l^G_9|LNqP34az`Q6AoE05^r@RJk~^9OjQ-V}fIQu+J+dZ%Ssw@_uf?C8v<&8CtXR+<5#ykKL7;CF~a7j_c*JU{hsmo~tuJveP~(~QoSS|ZMzFu!yKKQK9Zme7L!;$V7pi#!?735pXlLPDfu3{qEE)p4{610UpM$<n5xNLKO3@qk)8TdcMjOEK4yrvN{n$Wqlr9)7483VsMHqriHJl4ziEGXqeT7x0*;iL1~`Ra9l2g}2?*abgzIAy=O!**Q-jreXIpR-XY77=UIctbe)$)p;-1BV-3ii=bQta?TN<Sg#_095Xhd3kra}_svWFv!r-}5Sbhs2;7#ku$BP1P6~lBc%I~Mk`pW@LZY6Ieg=S9I(dH*I&Xy4q5dq?SQNfyLHW%btbl?m##etdiojEB5y%0zUnM!f$1y}wOCcJ>8Xq%RSM!Jj*VE+((XX=x^SbE_;|;!`Cg(6qg_kMABS7HZy7V>~GV+mXDPtur$je`&gg3-kh#fD5&?R9(Q!62ueymL1z=RWdflt1O>xqVaT{^r(2bdFJ&`LJl7?f#%7?x(ku%+4+Z<glTq`E`s3yozCc#&&Jo`coCKRd(C(p2(5tyT_p;B3HT8;)prZW+XgYJtgNN5Km)g)A21v8sos(9%_<ke24TVHl{rf?n(jTB4(6TZ(o_iq;iywwQrJ6Bb9Tor<>PJ{;FEh=5b#eDFdJHynSrnM5<;O1%)cI(V8~VLUohJi0(&tgQ53klGHI2xKG!)w^c`j^cn}Be)s{1OOU&_~=Em0AFCGB~ut;R16UnYVCR?l&?t$e{va~yH>%)c^@8d=?q;=pjMJ#n8(24g?xv!MIcj35|pAScF{EO+!({+R7`~|>kXTl=CY?m2EYeIfPh;+9dDt2a-RjZDgo=2Bk*aPI+;|g7?_mVl(8&1CTH;FM^_iO9FQC#@q=^OW#dj<1t{1nSK9=;5e4MyClvo^#l&zbdVDfk6(-$h380f#1ek#=3)NiKD8ytZaA_?9HB36lQZR#!nFW$NZlVIi9$u&m0~2O7q?T`UO|^7C@}nTsMRuH0dfmp$z$Y(DT*^@Jk%%4yr}<~tC1(veeg~I|D<(p0eg<bw&IyYX#Vx3w$rPH2>iiPQZ0Udo<kcXyRSjpU1LR>V@E|$oj>vpO)!+=C1s^cuoU6YW0x_)ih0Wh(HLP*PQ$rUnr=bI4j1d{^Jj&?`B^dk$E&!m14>*N}xeiQD<`Mi&k0~$qUU!@!SPu8@E%PA@r=VMseU@jAEma4}K%giD)MPjPU1djXFR3lWE+E6yuNJ{*?M&7&g+4*RF1IL{75dkfC3bp^vBcv_SF%r^z)R7GxB#Id3qW#sr^T{(+Wd{1Yf#Ie4K}i|1(HQraB5zCY7Nb3+mwpo+9ue-HEYFRcXE^wpb*a$bV}1({&3HD3BDBvGlbTqb%zExQ;0(xI-Wo%#J#mU75<lzz_svfeA7W_=}RK?0@hRx+h6MA(zX}bObQ1&D4IMOEo}jEPw<Yfu&7b(K}2^j8e$)ej21vRBQkgTjfwa1;;3vtM^gv&vD>qMj+%-nJuEF-L=3<qE6_HRUdA?pv|DTu#HYjpjMzkwBzTq)8=u~unxGju0z(8aId|f`S6$U=bp;Y)Ej*6(;eyC1yph{K$aNRbTn^*n^5pd}KL37-VF>Ls=zuIL<<$x6@kwC23pag{5PNFMQYbcJFp~MlYyzU&HbstNR}FKLuPUF>F4sWruWagRg!&iH)Cfx|S^+Iqr=&>$h&-7kM??XjIm{9e&!fP1C{s_6<Db-K;8+T@{>t8=F2Sf)T?m0&K`01!ostdHrJ{<Q>`SOCdo~(oYl3VN3Ho%X`JMr^asxis(PIug##M)nFd5IZk6qOda2Sq}3khP8tB>OO4HtD%<_07CrK7?CZOncoI*7w)@UoSx*ff=Jkl=kvD2@O=4j2fX#zGCVTZ2}ld#S5yVw8Ok<2^=N8?iKrRI`BgAmIVOH)37N(b;#v<D8fUCn)fdSA38d)HdUn%@gaCN6`Q=K2^)`tYzY9(6R493!3`D41NhW>=$gn{dU&)g{o<U_MOk5qI~nrRFupA7F3iB2?0RGe`6*}LV{LoiLZv5VpGz;AT6a>maareNjCTABb~(Y|H@b=w6efF(g}E>!;q>l&j-0C__cnmO0Kc)vP_0VgNjfBM|=jOq^A<3<pUIdEp&B$A<b%GXlWGwk{iEdLq%phn&YYl8qGK8Cp?-}qK)kIp2;+6gH$$DlCn+ggGM+ZkZod?K%ko^unTY|aobW%qmm>Ch~cuN480pAJAw-3SYzX2eQX-&VqaU@ey0YIM97kK0HZ&|Iwx>=OCt!JnrwO*O#npa^h(&?mP;oWGy#HVXuMrkND3V!#E|G;ut9{)weGn!bS+Dr;}Ky{gcoGl(LG^E4zbx1DuQ_}e+-I9vC`;qxDfPlJ%JH&|MuahU1b-HgS>nH@cPrMqh0RkBc~vXfcrVn??H@ID?D;}8qNsKhdLoMN`B9#ib!P+JC@@9bwY|r^STM(BQjkv8)}O_UAZZx0gOq7EcSEZ?DmS6EZqg4d*s(XF$EO0q<kHr0Pc|hW5CLvlAy=$@Qa${_JMXK7WDY+5{*D0!HnWjIXV71egSNqriv@pzP%JSM`<jZA%;!H3r%yCRI_G$%n>sX<Sn|-lyDye?fpwhXh6~+CRtZ`)qpR$Z^LMWqi7IGprKcKZq`EO%;(TozHo1=sl$meG6tBoUnw0+)(df-gq7xQXSN9_IvVyL(1B<S)D#*`jvlEkA_vEDsThyRL3t<~?}Mym1=51KixgtL79o7R=Me#~lilcx=|UN{WsT~SpMl_)i(n*At)?ZAD=SgUG9hTgyr#9{?AWJ$Rf}6)7-ez%9!eiaOYl=^X;8;Nfm_h_C62UHlT0D6WSW#e*(+ZQdu99O#p!4)9o0C??|O~%V{+L(PD+7rj9)QD6H_J^4v-go2GYv@WGU3E-2WGnP9HB6+r*ZX3m872Vwnt#9cOZznzPIu6{&8;<(UF|NWzQo{duNTg|RdYl*lb6m7x$lgJx3va+0N}m?h>{rE3~il@3?!8YMI6WiYsP_e;yI21b)eswn3r^Fdks-4d=y*eCbsMbV7p$AyY3*G0<9;T;D_64=<34dY+7bs$u{0$g-TvsIiPB-RLtijBZ*UUs8^?r`}{q9z4H!~WKuGNfMs*hUs}v$5wO9KbUYPF`u6+Ts#wl}4nmPwiB-RjS;4s112;bc!AUAjGHT=7R1@gwe;Cxib1Jq{>UMsPa)8kG#H4qGCotg!@;bMl1L+#h=V;W_Nb~t%WFoy0k<MmZ;_SodkFdUGo6+&9ps)(z7?UYf1BASQD`Rh&pnL9RQm09c?#Dk95kp+@EKLmVW2g3o)h?0+Ui^(0P{vgz1_VZ1c=_4pEoQxP8cmo9bueiR1?Kjtq9nYu?77kib?`F(?vD=mtxil2c|$Y=>ZAQG>a<qf_6}50j-LLRGvmv|XgABVZ{t%3EN^b-emU1*!FZg541AthyySLb$;2_E^G%@=z!>Xu;gxZlp74KA|)R+{D>!J0iPw`U{H+m7e8KGlYu8zdV09Lp?^RF;sz~f(fLDYfnwg^~3Fk=V}>3lK-s4Xdz`ooO`0OR62&FPE*QMMzaD~*X^FM-4MYI?F*zFSexX26xL}s4@|M@KSN#-l|(btjv*C5@={2O4|I}R9*#-~NI`24F-{Fp!z?4ZivfHuFwHFT3*nlh>{eQ7pjutmx)&PgMXbWnUB1Qg{^Px&y@V)?wlW6)QUaC!FOJMO#U>*@1Uz^S2JuD#SsY7FU_i*F7(J5)%%v86T?K<r&pOJ0qL&l+NJKS8%XfGbB#B+HkVumjSgpJ&r=!h7irk|ph7n8){5ylSZWhLg)S@K6&V2lYX+DVY5N$?{vQW@sBv9f;mtfym-3Y~8Qk@LS+GURmdJX8}bAlq(NN60WK)s3dxq1u(Fc+7+4lX>f<gSWBhhlYJeS~Bvd_>#7o;vQc`A8RGyOUueeu)Vq@jyi!q#*HRX;rd&iL2d{yjpPk`RQOFpkw@s!ae}ddvLzGcg>uHf+xv%21|2rV`WS`u%`xc7~1tW1geb%O(BFOajpaV=l4<~p$qTJhHju?lmc9mvU(B=jVTJ0+X`K%;69S^fodN?AXHF}Nl{}q7$n4E<c^E0vh)uvHmlUJ%U!##BMb;~i<?Iy4=M$A3aZYCb}{_j%+|FovK>eL$P{9pG%cnRpJ~uNmpqBhTwTJxZP+<QGGT;!FmcQ+-L)Mpdl}6vD|GdTrW8%6D|FO4reIM(g}$9!R|xjtVmigBfXCFzlEV0FNVqmqO$aL|0G5PR13ZIna6eAN6;ikp!{;hQj(R)}tQ;P2sAiC&jHpqe{0Nk*>hUpv>qwx;QYtFAKqaF`GNb@N(i<1x4AnqVY4I30>R$Pk$@)V$o<glt0D=O+1?-erLesl4ytH#uW(V9OGf>oDgwc{_;MOWmKO&WOsV^yg99KE2<>65gyt1;XmXBFbpDHR6z5aQhmeU~=hnk`=Pr>u+sk4>=d@w(ZCP`zZ(2<-xF(js}!FI#9p`Km5%%j2i$uukc8j`930LLj-+o0d^Pr&0QxfK*~Cgt-8bx;A>2~35cT6D5+JwTG>f9!_|uw7NAhvG@uwtxvs2LvUiG}v8YDQW|E2S7PRkY@xul6XB6iWPZB*M%M8@Tz2-0SFU602Shf6)Xn(*oS329&TcHFlTm6{SlMR`$C9JN+vZ%MY{NEs7ONy(kTDv;&)T^hzrxcG||Wtqh-5m-cp7bo#<LF<<#Z?ut?LK5>pD;n7m^_a6#Ja4Nq~V6n=j076-U$z@b&739_6UL(6v5*dV8(Y$#x*REkCQcQBI<Ye+K@ovB%H=}G+!rI1HQ8S<pUg&O3ouJn}F<C`+m>2mr=4ZL>x7xSM9@J8qk*^J~H>UQ^St^zbz1z0lD8eDT5pe32S6D|P9g4rstL+bZ6wP1afES&?5j)5iL-oWCLutrvq#;9C!{=z0vCf940OI<OH(xvo0RTjINfIvkMhhU+H51<$f!*eVmR2U%}j@tDvQd(}bt)dyC)rdGUnhb|7@^fBRDT4O;QdZoNO5zCE31&<3o8CCbY~|aOD)8XjCJ{ewFZU1d3N6fTNj<r!e7h7Qp)3zH9q5Ox*7OcHN_x48MY0#)EP;@hbLdFld}X(s{myi42h&O_MI{=xXS)UMIbf!t+s-UGTZ@n6b0GYysRXGPdtB0CZ&MqTq9#k{(rcdGJK??Zb9PlwQd3AZNjbXM3PC3S^wa|2b1NLPtU8;ik5fWHO&EX+C1w7P7M(KUJrrVSzDC*XCzW|xOaLj3B=tcaPiP7Ug{2q({!M2C?yMq=nG15LO-KgW97b5<MyG^4QW}O=<|yqdhc|}mL<i>_nf}oS58zq0CGi?w(}9n~*n}_PVP>41lF#rIOG_vvy1o`ZRK$Q70dq_cfe1W%umv+HmW_rXmQ`QY(Zht=>6Bhl!X=7W1<bJ^k?=zHwjdi^7_}jiBOvZmz1!NadlmTsDJN@D&`@Rv9O=LjoGXBe5z5GRMo^5o;7#Psj<>WeWA95{Nr?0X%thRaB4AXpmq&1bAT>LJ&PXrfpIGsvS})KIY-5b1g+BIo!b+0CRSQWns9*alN_0o-6eCpAGH#K;okq6Rx=xM2z4gj3XfI5elk>?rP`rX%0$&Y9F^JNz0wB-mM)p}<5Oa!}Flfp>vo+H8C%k4XClf@{1i&!WsfoPLj)62)jE=Qv6qnhH<0*n2f;jAoAk_`#cxJPvz}2CIrQ`w@b*k+ziOPJC35>!}@Wyk)0#|h9!_E#NYh_^LtC|29Nm^<SY{QP6LN(T5or-Co7Dfh|Uc;0Vxmc8+a1Wz(G}@-MeN<+X9dNO6nv_NhX{h`MFSmw%M_HpW+LnP4*!2aQHCz!z>s>ts=SC>AZux}~nKEaFYRCXVAf*w|mKzr}(c<@!#Sp_&8uI(_#eQ5p0LJMCW_VTfJDYEaOK`D`pG!>!d>u<YrGHeA9K{A6CcWD}shTnoA#kNvY8qQ-fv%62C&ws=EE8-2WS_{s(dFF}{>i3r({j957o9CNc5!M@k*D1Pz=&S)3To_RG{y<|f-{QP8nIKavB0~j9r6Mc_u^~ztKx<5Sz@(WznF&r{L(0axWIMb!0P6^is(y^d0mUGl@5o8E~>XhOOgI`2U05u(NOxbtU!w~n+i<h{-*r%zV(LoViTamB4xR(8_kL!To0gz3ykpA>+MhT!Q06ew}@aS;#7;w!s_H+p3>`-g(mN`o2raC+EuBdM8SB>yAQ;<2bZ&dNt<I-G4AqUP_AwXtC|I3AtRXCj-g2s^*BMr4ZdZn38mc&OXFB@WM&6dSd6yVIHLp{GWPrzjXZDc91&-Dy+MCGJk-HofZphanJ3@uZuBkWPAChkmRHAdV&8q2FVAUrz#yc7*wu)sgWZ(G`wXEN9~)%D%f<uSjy-pH4aGigOc{Q7SDE|ev;vw*+7-u+=YF95_|2*K<-h(vCwpZ5')))
_DONOR_DEFAULT = "route0"
_DONOR_MAP = {'PET_CAFE|FARMERS_MARKET': 'route0', 'ICE_CREAM_SHOP|PET_CAFE': 'route1'}

_DONOR_SELECTED = _DONOR_DEFAULT
_DONOR_STATS = {'donor_selected': _DONOR_DEFAULT, 'donor_pair144': '', 'donor_default_branch': True}

def _donor_schedule(obs):
    global _DONOR_SELECTED
    step = int(obs['step'])
    if step == 0:
        _DONOR_SELECTED = _DONOR_DEFAULT
        _DONOR_STATS.update(donor_selected=_DONOR_DEFAULT, donor_pair144='', donor_default_branch=True)
    if step == 144:
        pair = '|'.join(obs['town'].get('unlocked_shops', [])[:2])
        _DONOR_SELECTED = _DONOR_MAP.get(pair, _DONOR_DEFAULT)
        _DONOR_STATS.update(donor_selected=_DONOR_SELECTED, donor_pair144=pair, donor_default_branch=pair not in _DONOR_MAP)
    return _DONOR_ROUTES[_DONOR_SELECTED]

def _donor_action(obs, configuration=None):
    return copy.deepcopy(_donor_schedule(obs)[max(0, min(718, int(obs['step'])))])

def _hire_recovery_schedule(obs):
    return _donor_schedule(obs)

_QUEUE_PARENT = _donor_action
_ITERATED_QUEUE_RAW = _donor_action
_HIRE_RECOVERY_PLAN = None
_HIRE_RECOVERY_QUEUES = {}

_QUEUE_ENGINE = {}

exec('# Market semantics from Kaggle/kaggle-environments, Apache-2.0, installed version 1.32.7.\n\nimport math\n\nCROPS = {\n    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},\n    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},\n    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},\n    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},\n    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},\n}\n\nANIMALS = {\n    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},\n    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},\n    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},\n}\n\nPRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]\n\nMARKET_I0 = 10000\n\nPRICE_FLOOR = 1\n\nMARKET_PARAMS = {\n    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},\n    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},\n    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},\n    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},\n    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},\n    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},\n    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},\n    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},\n    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},\n}\n\nHINGE_GAIN = 8.0\n\ndef _shape(func, x, T=None):\n    x = max(0.0, x)\n    if func == "linear": return x\n    if func == "sq":     return x * x\n    if func == "sqrt":   return math.sqrt(x)\n    if func == "log":    return math.log(1.0 + x)\n    if func == "log10":  return math.log10(1.0 + x)\n    if func == "hinge":\n        # Degenerates to linear if T is missing or non-positive.\n        if not T or T <= 0:\n            return x\n        u = x / T\n        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2\n    return x\n\nLAND_ORDER = ["NE", "SW", "SE"]\n\nLAND_PRICES = [1000, 2000, 4000]\n\nFARM_HAND_COST_MULT = 1\n\ndef get(d, key, default):\n    if isinstance(d, dict):\n        return d.get(key, default)\n    return getattr(d, key, default)\n\ndef _quadrant_of(x, y, board_size):\n    half = board_size // 2\n    return ("N" if y < half else "S") + ("W" if x < half else "E")\n\ndef _shed_access_tiles(board_size):\n    """Four inner-corner tiles around the shed, in NWSE order."""\n    half = board_size // 2\n    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]\n\ndef market_price(item, inventory, params=None):\n    """Floor at PRICE_FLOOR."""\n    p = (params or MARKET_PARAMS)[item]\n    base = p["base"]\n    I0 = p["I0"]\n    T = p["T"]\n    if inventory < I0:\n        f = p["below_func"]\n        amp = p["below_target"] * base / _shape(f, T, T)\n        price = base + amp * _shape(f, I0 - inventory, T)\n    else:\n        f = p["above_func"]\n        amp = p["above_target"] * base / _shape(f, T, T)\n        price = base - amp * _shape(f, inventory - I0, T)\n    return max(PRICE_FLOOR, int(round(price)))\n\ndef _refresh_prices(market):\n    params = market.get("params")\n    for item in PRODUCTS:\n        market["prices"][item] = market_price(item, market["inventory"][item], params)\n\ndef _spawn_hand(farm, board_size):\n    """First free shed-access tile (NWSE order); ties broken by min occupancy."""\n    occupants = {tile: 0 for tile in _shed_access_tiles(board_size)}\n    all_pos = [tuple(farm["farmer"])] + [tuple(p) for p in farm["hands"]]\n    for pos in all_pos:\n        if pos in occupants:\n            occupants[pos] += 1\n    best = sorted(occupants.items(), key=lambda kv: (kv[1], _shed_access_tiles(board_size).index(kv[0])))\n    return list(best[0][0])\n\ndef _process_market(state, env):\n    """Per-unit lockstep: at each step, quote both players\' current-unit prices, then commit both."""\n    obs0 = state[0].observation\n    market = obs0.market\n    farms = obs0.farms\n    privates = [s.observation.private for s in state]\n    board_size = int(get(env.configuration, "boardSize", 10))\n    max_orders = max(1, int(get(env.configuration, "maxMarketOrdersPerTurn", 10)))\n    hire_mult = int(get(env.configuration, "farmHandCostMult", FARM_HAND_COST_MULT))\n    shed_capacity = int(get(env.configuration, "shedCapacity", 100))\n\n    queues = []\n    for s in state:\n        action = s.action if isinstance(s.action, dict) else {}\n        m = action.get("market", []) if isinstance(action, dict) else []\n        q = list(m) if isinstance(m, list) else []\n        queues.append(q[:max_orders])\n\n    max_len = max((len(q) for q in queues), default=0)\n    for i in range(max_len):\n        order_states = []\n        for player_id, q in enumerate(queues):\n            ostate = None\n            if i < len(q):\n                ostate = _parse_order(q[i])\n            order_states.append(ostate)\n\n        # Atomic orders (HIRE, BUY_LAND): handle once, in player order.\n        for player_id, ostate in enumerate(order_states):\n            if ostate is None:\n                continue\n            op = ostate["type"]\n            if op == "HIRE":\n                _do_hire(farms[player_id], privates[player_id], board_size, hire_mult)\n                order_states[player_id] = None\n            elif op == "BUY_LAND":\n                _do_buy_land(farms[player_id], board_size)\n                order_states[player_id] = None\n\n        # Per-unit lockstep loop for SELL / BUY_*.\n        idx_esc = 0\n        while True:\n            idx_esc += 1\n            if idx_esc >= 100_000:\n                print("WARNING: kaggriculture market loop exceeded 100k iterations; aborting")\n                break\n            quoted = [None, None]\n            for player_id, ostate in enumerate(order_states):\n                if ostate is None or ostate["remaining"] <= 0:\n                    continue\n                op = ostate["type"]\n                item = ostate["item"]\n                if op == "SELL" and item in PRODUCTS:\n                    quoted[player_id] = ("SELL", item, market_price(item, market["inventory"][item], market.get("params")), ostate)\n                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):\n                    # Quote at post-buy inventory so a buy/sell round-trip\n                    # against an unchanged market nets zero.\n                    quoted[player_id] = ("BUY_PRODUCT", item, market_price(item, market["inventory"][item] - 1, market.get("params")), ostate)\n                elif op == "BUY_SEED" and item in CROPS:\n                    quoted[player_id] = ("BUY_SEED", item, CROPS[item]["seed"], ostate)\n                elif op == "BUY_ANIMAL" and item in ANIMALS:\n                    quoted[player_id] = ("BUY_ANIMAL", item, ANIMALS[item]["cost"], ostate)\n                else:\n                    order_states[player_id] = None  # malformed sub-op; abort\n\n            if all(q is None for q in quoted):\n                break\n\n            # Both players see the same pre-commit inventory for this unit.\n            committed_any = False\n            for player_id, q in enumerate(quoted):\n                if q is None:\n                    continue\n                op, item, price, ostate = q\n                ok = _commit_unit(op, item, price, farms[player_id], privates[player_id], market, shed_capacity)\n                if ok:\n                    ostate["remaining"] -= 1\n                    committed_any = True\n                else:\n                    order_states[player_id] = None  # can\'t continue this order\n\n            if not committed_any:\n                break\n\n        _refresh_prices(market)\n\ndef _parse_order(order):\n    if not isinstance(order, list) or not order:\n        return None\n    op = order[0]\n    if op == "HIRE":\n        return {"type": "HIRE"}\n    if op == "BUY_LAND":\n        return {"type": "BUY_LAND"}\n    if op in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL"):\n        if len(order) < 3:\n            return None\n        try:\n            n = int(order[2])\n        except (TypeError, ValueError):\n            return None\n        if n <= 0:\n            return None\n        return {"type": op, "item": order[1], "remaining": n}\n    return None\n\ndef _commit_unit(op, item, price, farm, private, market, shed_capacity=100):\n    if op == "SELL":\n        if private["shed"].get(item, 0) <= 0:\n            return False\n        private["shed"][item] -= 1\n        farm["money"] += price\n        # Sales at $1 do not increase market supply.\n        if price > 1:\n            market["inventory"][item] += 1\n        return True\n    if op == "BUY_PRODUCT":\n        if farm["money"] < price:\n            return False\n        # Bought goods land in the shed, which obeys shedCapacity like every\n        # other deposit path (pickup, shed-drop, end-of-day drop).\n        if sum(private["shed"].values()) >= shed_capacity:\n            return False\n        farm["money"] -= price\n        private["shed"][item] = private["shed"].get(item, 0) + 1\n        market["inventory"][item] -= 1\n        return True\n    if op == "BUY_SEED":\n        if farm["money"] < price:\n            return False\n        farm["money"] -= price\n        private["seeds"][item] = private["seeds"].get(item, 0) + 1\n        return True\n    if op == "BUY_ANIMAL":\n        if farm["money"] < price:\n            return False\n        if sum(private["shed"].values()) >= shed_capacity:\n            return False\n        farm["money"] -= price\n        private["shed"][item] = private["shed"].get(item, 0) + 1\n        return True\n    return False\n\ndef _fib(n):\n    """Indexed so _fib(0)=1, _fib(1)=1, _fib(2)=2, _fib(3)=3, _fib(4)=5..."""\n    a, b = 1, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\ndef _hire_cost(n_already_today, mult=FARM_HAND_COST_MULT):\n    return mult * _fib(n_already_today)\n\ndef _do_hire(farm, private, board_size, mult=FARM_HAND_COST_MULT):\n    cost = _hire_cost(farm["hires_today"], mult)\n    if farm["money"] < cost:\n        return\n    farm["money"] -= cost\n    farm["hires_today"] += 1\n    farm["hands"].append(_spawn_hand(farm, board_size))\n    private["inventories"].append({})\n\ndef _do_buy_land(farm, board_size):\n    n_unlocked_extra = len(farm["unlocked_quadrants"]) - 1  # NW is always there\n    if n_unlocked_extra >= len(LAND_ORDER):\n        return\n    cost = LAND_PRICES[n_unlocked_extra]\n    if farm["money"] < cost:\n        return\n    farm["money"] -= cost\n    quadrant = LAND_ORDER[n_unlocked_extra]\n    farm["unlocked_quadrants"].append(quadrant)\n    for y in range(board_size):\n        for x in range(board_size):\n            if _quadrant_of(x, y, board_size) == quadrant and farm["tiles"][y][x] == "LOCKED":\n                farm["tiles"][y][x] = None\n', _QUEUE_ENGINE)

_PLANT_CORE = {}

exec(zlib.decompress(base64.b85decode('c-q}PYjfK;lHaFl{sUIIsUZ_dk(6Y1%862?ag@Y0ww05W&F!jm99pDooh4EsDcic7|NC_}9t22Gk0i7AaP3Yc5@<9UjeemUs?};A)=9{I_ph#!`E<R=@LRk2tke7}%Mw3I=h-}t(wA%=!6$z)|IaXJq?w<EY@LQIjux9{tycT-hxu|9CmCD%*|qut{eyV<;}1Xna6BA*xL{rO<;Ncw{MA0a@ApQvBSwE;YH1h-@U7jdv)XK)q?xywhl{`q{0%(rz|*CFZ#;Vr&*o7UCb#|qzP9ux@ckF~9!FR4Ji3B!Z~a9YKGen7$GzcjAO}}tclICq+4ixYZy9?uIO~lD#j#)5$Ntqa_OIsH?X6>vl65}x#c0_3^jm*8{5!nSNNyjy-Lec$54F)d`;UIsKOLNx7W~&k2Jd{;l0P8(_0CVudZ#)Az8efK`b3CnoMyPFM2Iv?)>GUA@T7J;7<{PJsd*X4=k|rT&MC1<;sAglr2e~iwVeM3pNJ4@=;!63KlCm}ABX)~C0|%p;X0>-HuTxa>F@d27w`N15BjuU960tb=Gf1+j{RvcIIXEg_%Iy2`FK3SRTv8aP*=OLuJ%UVVAZ;0ojRvtUCgL1pu@j!`@_-6>B&F(!`cMLIqMC7?~lBb77PUJ-D>f{PmcTE+ta~dh>x{)A9};y*%sM!>8D5*)_DPAowVSi8UT@2>vtJ0;yZ7)j;1*E^mCFC?}+D_pIn7Vlvb0N-oK1*L)Cf_UkOIz&$ZT_R+ZqAh&`)D>_r)|YuFzl4pv00-E5T+%coI7?60jVsU{KorB#Jkr*!~gt>*KC5c{Q7CG!Mg?M@|P?ZcMxua>2pN1>n8>LtY5I${NJC=lzss6_0U1+koKN{DrA6yuFch&|I0!#yU@(wA}zV$V9?xRm=bKkfRXB4X`o9&2|xhb-kUU%QkfhDwNW4zJ*`7k}PTY82DtqR#xSgLY+3gT0orielJWDT4PW=kNO7yWYt;NZntXB%gzD#=P{}Uxf|=tF!w$8+Fg)D0GkbeD0w!s2Zo$gmLd({%}5H*qn8{YVaeLgrLeIc3*A+gySnEo3O|BW=Td3MKd&NoA}VNjvHTbsCsL7=zv6JPgq5lHm*RiOS`qD6W>*W8u<5!y$P?vC``Z_Pgxc-P66yRV)K+O=V=OkSe&pZjvA{NjrrTKnL~h<QJg_*Xfk52x~!#v*Xfi$UBfcmv!`s7KN5}BfVZ}^kMq@9vj(acmpy*WI=o*FSgd^#rttz;X6Yw4Vdky;#9yWkFj11sgD{m`0KUdq2u#IRVbZ`p>tqUUh-?N93DCjR>;T>e$0lV?3Q*I~<qiwSf(8vx`_Hp*dBlSGG;>xin*l}eNu900^)Vqf@kQ#m4{D8&hzf_J5@qBt{DlVE&!*Q1UiForkBl|KhuBP^3w{+W@H_%XESiQ6!KoAOZfOB|modVaG}o&Dn1y$6jg`o8{PBmkz2RAZ=$#Gz*4GWA^TBZR9=O(lC2h1_rDO*m)#LnWAFN2^a0e{omU{ZBFP=8!W0DA`z4JHTVECp#B;)X$jL(Zt^xr<W>Zl1>ab!TEVOK|q1^)&6t2L2$d+)K~@!(?QoqaqVNn`Kgz3G7d*89CrR)PE*OY@SOe-nxEhm(K&qvv6F(Ri#3(A;1x^!aW0@%;F`ckw}5YX#t@iL1K(y*E7fE=Gf4UkyddMKwSZ_ITLuok@JgMN?Ut#)UZm>mK*s_SJO9(w0<BF3tvn(fgCWnyD4EYR)<2!sGjbFxl6lpU6cY4L+TF$NlpWu$t~0tZ0YOwo{K`6Rg-@x;A6~-w0*z<osgPJLlZ-tCT9Be4L=pZo*AniUGMna9ia&C@Ak9u`hxq0x=*M`v%_nS(cQBQG)IB+7BQQl6mpW0i^~_E@M9lyc9wya=dGQF$28w7wqZNf~0h6=QTun!(Q>`Avm}|*qRGs*QtG?m-pt&e$CZ%YZ!R`bQ-3qm(3Sp>Xgv{x%d_YDo`GjN@E%)@DHQL%unJq2%YRYWC*E_t8@P8q7RxQ2$Ni*?lF_GLya2fGs{nIozc_slf0eT#+|6C%~LVE;6MCn7=iqbQyZ1V_}O~32(gWellVf5!Uewg2v4_@>p=}2g<vZA$x?e;XTVcQ28!2Pg88y3jQ%C(uo}IG%`;oXe&!Uq)pbQrD2z9g@%;p-i)ImX!sRO4uywSEr#E5Xvj1YW)4}oY{WmrEh}_JSTd$2tkZ{AAdSdK}03Xe^%&0`4ds0F^m?1hfCMG0oxUn|O+fB5|)sTK6+HH$@nmL}>KprUTyGZY@Q>1ncDv+jOfRe;en~s{)&Og<RX4iAjc3u|qkVZ?q%2#zeDa`exwV3bP=VZVE8e(ILby5RX&RN@-7>Z%DB;*^g!FiJyqt18YDhX#{5`s9(w<9hFHrdV7ro~~*2HTEXlR7~fw<p$_*$qeRVT!R9>V0GXtdjXH8YNpc3Sy2<47br*%7ij>#1qayBG%_V=qrx#M&yMr(<EL=2>2NxP;mOe*l+Xb76eJ0%wgBHCggcQL(Zu$88IL8SF11z!r*BVE@QOHLLaO-;3>_(u4#af6~8=8O5BDt;8w50tzN_J;g0|V@d5BQj8UP@qTAet<t@3zH%3=)VkMX`UxEC<5mmj(YuwtOqmKR6WN}x)X9@-)aQMnU<QB7-4R|SNI~z07IElj^*LdsNM3KSZ6yD09XBNXgDl$|q9@6W0#ifT@2I+Soo(?z9)pY92vM{(O7ctPq&zKfn%=g|3uyra{&E@pv4Uxt;Gf8d!l;W2wzJC14h(8#~?`XnE6hZNy=+4_r0L-0vO-%dCmHt|I=@W3-2$iSG69*q0{-+6UA`j|!Z1;o!J=R(S&JCSxvMWlxGICn%z=oU=LO2+?MhUr`Rt<(RkC9v8qI*YMM{J)tWc4@%*mYgaSp`9yUUP0q9nL$Y9m^k+{U|xuHC;e`JK5Nt@16-~76s8@QrR}&d!o5y+JdlMfKYc(^3_pPflP<Fryh9I7~q#vn4(8aVsVU3CzXQvW*!A}W&rLPnEcus><4dXB<(ScAIj4N#6Wv_2WlXJmr^s+A&vnQjv~Y98lxEAIugzK=?e&Lf{g(W=*_0Ea^Um(DN_wKK>SE!4SF8MKnu6hG#IP%qY2m3ZGCJ!=2*;UA?WDHOS2GX2X1UdR|j!;LT}82tO-1ALnNd?c*7tH!49O8R=^NG31T(cR@LE0^QFIV_&>C$aut18M4=7G{PoU-^vBv+kYO`%0N8{NWUlG7YDo)(u3pR;Eo952!!}m%w{nW2VdD9>{(RwIE<#&7RN-iIBRKCej@GHwBIKIi;~}&-a_~Dyh~Qq+2JnrwOj7{@B2VDSHN|VdR=Cf#0}5~G&^2RjVr8)RSQ^IWqVZSU{DqwkAizPINO15OG{GX|7^-$IXG&CGxkCtoq;gsyJmOS$mCLA_IKnK+`oeB@nQzD2=w=dINi;`Th(&^*<hB(-L2F`+)b}LyAJce~m+UHu??B?psX)V(4;|2*1qR4h<?b4dWu%`Nb8J{}Ku8FZ0)!(&>sT5#xpnA#c`&t%y*1K9^Jk-5@MQysOeikpqi$QRMs%z60emL)!W*?P6c8C;GXEy5f-@_3f5oCQGt!<Zj@{_uNI4vdlF1`MxX51`bim{Qg(=W#u^}M=?uo{T`nuN{f2BJgHWgMU_Xzg$%Ad}&O&0=%8q0i0Vse|%Y2!@t6j|iwR6uVsU@FLR3Bb;nFBajIzYuRQ1Ol!Xut$`E&DsD1(%8&s#%cj2i7fJ^%OmiafK;L|{~n{+!&{77f>^LE;NceOliSlV8PmAKE8x$7gtHBrR&h$+9RAy$=>EfwormishU1Qt9w*jU9YzXpB>nwZnGyIGL6ZoZ%<h3_1CAPe*p$vDoEC1m2qRlsPzePpf3Y!MxK=k*_w3HVs9fS2(n$e##6^q?=;trMAPxi2a$IOn{fLoM4$a{icOP_cWnUb-U1CGDM3!>2yLi0_Fd##!fFuvF6WD<vg#Md4#1TrMc!j4r#C8tZR(1BN2Z7Q$3$tm{1wg=^oDC5(eHt3DT{7O`%iy|Yj?q^dJ$y(Cxu_jgwWAP2SIBrCVVaC*5U!eWvBqb10kqO*CXO7~Wr%bjVJs$cwT1<4ve9+8p)@mmMPp#T8Q63ZqK~mQQs7L^k2M-9N(qEc!^Mm*?47@XeSa6hV`$=2FcYIG@eJEbh%=0T78f<;Aw7W|NSK&oh~q-vC8InUvBpafxjIBbWE~|K9Y8AtVmR><8pLU6ELcwKH$x1;mv%xq&gt+y?bZ+20fbIB*FzLq(ROBjIu+p-C+&=SLL5vL!6R<AgTo5xum6Gl2iE#JEZ`dhb;L<;L6(EXkgk^wK5K%IUWbT}Yj#J4hu!Cq1JW0Pxg~_D&1);l2wQ1a8mORNv9H;!VwRN~>E!tLkAL3s0x+~*xE?`;-r3aw-B6`?+PaJ;10xf##vL$z3eaD7*)!oOnbWC0O4cRa1qS7S!)_@&nR6t?>L#>BQRkwcuwDY!1`xKLW*`7AH;jbhOCv;%!XiR(ind*fyE|TAT?;j@dH)y^6#_z&mC8#fZw`Y8O!^2uQ=Q$z=};J~WM7dWx0!_dNbS?!algQ8--|sSu^xGXjNCs|a!0u|CT+RIQ)c|Oj^gQby_$zXek9RkJt0qv=Nu@mX@Rl?JIi2sT`aCoXB#AhvukL22`UxhuAr%L7txpnwn(_WK*RucSS)hp$l_dCz@hjxqllQ9A>kARh=|(=&)R%hIGE=a0i7(C+u=(d93tnNBI(jy7tvSE7ccjhE;%<n^;kRpSp>D!BWSx8F=$ofXdr3<2i_gS4LkQaQa7N$J7k4l$5(L#ivW6D2s(WgUb6Ty1VxRXkA>Vfm*eZ?<W~x_T`I0P*@9dsI#}+vL7uLY1nJc!Jy?`dN+lkmPz6Z0atd}8dJx(+uTjr#sq!B8up{ikbGroRPO@EeK4N{4F`JCU7Rds(TxUGLO4^|K0ew|2?a-GbVFVA7@bemv7NLosNr1dh4A8jsnVWmuYVIltceIy4hdArE2y{C1vI=wzWa3L9PAL4l+uD#48+#SJ&x#&JMNf;vBhoGRFpbFp@EA2RSGyQ*st{p2qTsvNft)dm5$D*2f2F(^3+nDi=W!uIKH1UD+6QRBgD*Nqz_c@8#r%0cir`Nsr8%nhTF|?Ih<_C#Au)J?aqxz~L=XNKHu4>i1dgJ(p9SY;+91~Wd7f3GVP^mVMp9_N=W2i!i9>;4K%<jW-Wrsjpw_?{+Vn=g0(ua9B1EeVpPD>lFZ6iA5!!<<-}i=pqZGT+s@WNHKfdE!tK+oqRy6>W*uKztZ$=c5D_IM~phn(e5sPiXAF%;vW$KuUI0G21%k=_l-L$zge+K)B6`<B_FhMJj+mCR`485C!iK)YSjb~3_GEYgx`0R3h)ht62l6l9b)5IePH~Tx1j3B*+=a8s-#00ybxjtWl>5RpH0zCUdg#8%@{(17iYTE!hg8Z~3qNBDV(7&#X7it3kfk#_m76{B!H#iA?F1#c7TY>2`7x-z9puhVPOe2cla4+MU;`bFW-TmwyK3vzfr3*m|tCVP&jZ7a<-x+m2lEq5fPg-wNm;A^`whG|@H1|7%&vEq6o3(V0cvpePWHMGoXBJviiAt48`cGBkJkn$MVR}xh#UCsCQ@tsknNp<g58(bk>h#Z(w*1ifgE`L_DZY6$U93}R?KX>ML4`u&o<crJYcrnz&G;F2XAfe(IeAwgv$Pxcuo)k*A!S&l{DdEJJMYl&gIG9aKu+U$^%RfuD5~%#hIZ$J5#w1|AXEAAv^cjmeaS7$yo1Y&IPSN9s>t)($CFb`S}(<Y545hUu=t`9HE4{7eKC@ypnoz_a+rsGcCG0s?Xh8tE4jC^J=@#RuGrWzC4T3gE{#_*(yQokJUBh=ACEk}*z3=x4uUMm5IxIcvgc%NUGdN`KW;87fTFD2gFwAu|DVM$dQQrIR4{sMS#+MUfd`Quo=b{Dyh9U(nUkmNgTa$w;>2YV--Ho{)R$O@gmGFR$|gVC7LQ1$lj$VWXZOo17JC{3ejY!~9`pQrGkwHGCr7*y)mL=FY-Ej0^5i)>?v5l>b9u!(g?C{g)blYkgke?G;4(}pv<5NCFmO~edGbZ|9o>b$ybOGHa|_8|H@B1wy?y>o%KO2#t%*9V5=jtrxQ4^RJAAEHdd1TeWLhxYw*l%dy46z|phSbhP<Ymi`DjO&iAp)h_^r-9uVe6BE@N;xKm~5XB>h<$;k+YHFRWugD*`RLT*5PKuC4uLiWyBbJ|NhH?^yYdp`$|bFScyTL|iHLQ~83vsC467a&~|dQXODZyrK1_6{KNhj%<GR&jYz=oB%<Za5^-bU#<C>GM1@g!wYDK@<Byh(ZwdVPlbWgu5X0`P0naC1L_2{9>IbMkOC%F5qRJqW;-y#$-f5<K870?&Y(F!u@tIFsAhn6J7hgbPPnyPm89``9j-Z*wQZA=RofIi6o|{*6dz5?NIsS#l42cSG+mt^5OI@{vjHG9=23P_T8sv1thoiBWj@%l*l{USY07<QqB7s=^Y|!V>xrTUC2xk2SbPUVrk}Z(`HUptFkDr=)otmCx_L2+0HZ4e8p%sD$<u|SbiVVvIaEy1NMQs=nOLyvh%t-OiQlbLG#sV9Dw6v?+YW71SC7hEISqgy^GU%o)KQjn<DC_~grkwg%lVXvjpMvO8TRY!w~v4Kuo%-lq7)fQ%9w^!5XL7fO2R7XAn-JZp`&CuxsqM1?m~4g0Y$obUob#7tI{!=7C1XG%>-qB1hI!3o%9u`3^|R7%1$#M>d9$JKv?1h`h+zA)`cgpTiNBD`c=4It~cI7S_oCBeFZ)`Ta+{pe296~=0*SX6jJ99%g4H_72JDaIyK#Uo@<E~PjSIT>nB~yQJj4Fnl5+op!C;52_6E=<6Jk!^;SY@5z^uP6nsf=4*}Q>9*K(Nq?ZiJ52zfkW}((4g!OLB$E0mBvu2D0s}tEQm2uy&53G9uvl%3ZgU1WWuRIC8;&`rluk5v7w2T1R48K~NDV9Z^sPU8W>XL^tDNQbPI2d_qeOMuctq{YN3t(B^;)WCWnv-zyif7F!aVzHZi2W;>V_>3z*_kz9pK2*75Gcmj@8&6_t1TE6oirf(VO0gozw%Kt0zMG#g0wQwO@U<VC<Id-+^V>F2zB*oehra%neMj|`U1UsgUYs3$lWs`IC2{NC_!da;KgH;15n~2M-wR#hCCQ80ZSrQNcNx`xwfO0h81IO7vIP-;Lw8n!8EFLeF<r!Lcr;gU2I!$s+`YCzGyZQPRqvMLK>Pc9<kpv&w~Nod5(v_46#zRA^eSe50FcV2|cJ<3cSl3<7t9VS;K`G!9K=T74k6Q&sz+OT>?|CC2f*=Zi9WcG`>OGj8BCE-cG6eo<;`WW`$%9*Dix^syN1?G#Xvo8K!Lk%s9n&VNgim`Z-gy=Bz-yEG$X~8#+q+aAif+UhZ^jRx=Ng993oa)9XTVKRqi~Pvqtt*RI$~<@Z<HpQ>h+)bNpL@K6rZmd(LZSJmjDkiTyT%Yq6p1s2!7ZaMLU6AIjtXZ8Yc)0)kaO+{W7r%Ok7RnRnBL8NX3)95Ej3<UohrZ~}Occ0<5r(jxR^EugYb8_qENURzLd$j#>#G;4NRRD^ccJ6bnyv4eo^~#lkF?CdtPh-h-s-As8hE}GbmU3$NtrZkGqv;r_em-3mlCghjvmh3!L{r#_sWQ9MHCFpHi&L0lN_M+|YPGpx`UXZ(QF(_*t~Tjr&gK<IVlP^uZiDR6j9tYsW-#;eKJ9W8aBUzASI%Svi2<qSc)+~Tp~aY_3b6;OVc>bF&T2lrS+6)xGy=+00zbVG&l-5@h7VkmhFent(OojQYp;2l6l#>#`zy2W+T}`Ti#>VB0$-F*g}#1u_n);$KPyjLOKh{xd&hi)-2GlN`oGE@B`TSS$a2y7r4t!tp%8FKJ2&R<T5cCy6Z+WBKX%-1M|^zdcAtrl&)x2eW-||f`w%w4E5zy&Ei^N|JRoR<0!8CXs0YB5Edym=p-WLAwDq0H^A{i*gAG3b0zH7CM_X*zyvTxL&X2{!O&GZ~qsOf@RinqJb`6I}qRE<LERJKe>vJX?jCNgNflIMpRYhWvfv~Oq${0u!`NpY`j9_j(9&?Suhi$dGIr)rGn(eSH^3;VQ;XPFLVend2UR$mrf@nC_XM?~$|D@HVQH4ToX%>OL=1}u1^4tn?isjNS${QDfO}_Io$+^j43BRgQtLdVG_u`Qje7D~ubz}yY?{_t_-D+gLqe)E&Rl1qDATHmsrfb_%9rWwE6l3AdG@dAF!b6=p6Q_F^NR>E$!?_#6m(TID;EmZ8JS?3d$s;F75tEmCm(RzbFW9{Z>jD~HK!oZ<UH}evFRJ4(EXAPO;oWeKsc8XH=eg_ZCB_t3{;7zZY0f@k=9NA$<c41bpkfX99LjL1zSNKCtO70qrN&rX2CIE%q#99*W)iBRCO9XjGgayP$#S%mE_9$9prXvMXX&5~v5s(jv<qR%JSJASfQU}Wj*1lxl*xu?NpxrBSb-`8SyAlHSBp7Vjv`T+Ut7St6F0Z5dCB_aGqSmbm$#Z``QYUhD=|Xh-Uw}Y+ZB*|y8sPwwdX#*eGpFl4Nv<|g*?~yn{m3F%W$!g{}gd#Etw{XVU2cFq^pQD3?m=$FID-~)v>JQBG1??-*Z#O2;0AcG!W!;T=ZA?Wbe_irjEKbu$v1k(?O(Ldjqg#jy7zEMYe_&CnI*zo#&{1LKh>y5GH_>rA^LtI%A0(3$OZmrM=iK0^Lc8&s`m2ZXo|ZX2&}}^+eT*V#`7mOS$$V?{idDhhe`y%93?l5y;#QrF>jjRexg%U*|bw70|&9?0f^;?nij--mmSY7ZiXEwx^WahrqOC;6UIUkKdZm%{kp(%+a8cN>v=Tau5^ps{=%eX13sH>L*V280M$E^FdNf=w2|xJi4rm7fYG2q0C7Ee_|1EB^a;GE5{C4m`CibO34%jP`nCeg?b*pFu5lwwcLSg_8>VVq9T66)-9ac<f-E@HGNN;Y4p_@=E(G#?Axb&fJ&=^y=tl)GMY3bxv^v^(k-u4cMmdGs#81<R6K9H4X#4V@U&E^X1+n6{O{2t-;##A)xg-5!CfWJXWy(4W);eyLc-6sNq2R}0%W|vEtZg#qHY9W{2(H29;_28i)ggl2KLq%`W=G>fL|r|r<&OJze?%@DO<!p7D4UnlD(?jTwKT6wk^jo`iz=zRCklmg%>ltMMBAn!d1Y<+ENmLt9a$u?jWRCsEv)ekZK)LX(}pAueTSN@(W#yb*3hC3!;|2Vo!%xLVv$qSus?uHL8gA#BPLDmK&5$vTel}7K_cEz;A}8c}S9~l}b@WUd7~L_6{BiCef7?aNj-dWfKT8zXO*A#%}W8YIN`@SHtT&I7$h{Z&bJyXhjM0`PFhNfgum!zrlM5=$MRt=cROo&pgsEZdtGJeuY0IoIhUD@2Sl2@&=e?FbCNQ=eP3W1%B%g?qdi|VlW1BQ!rO43m2Qpdx(M<lM{@4h14BF>abwj)mjwwfJ^q~RaZbB{qMPg%e-dfmhic$GeVwbED_mu(a6p_M*hcd>JkhJas<M`s9m%=3&XtH8I9c<UA0y&@K~t5R>3d@E5oSR2oiDMkgeRw!?4=sMLUdsSt9R-Z!b_N9a9SwneelJFN(znB~0y=1_uX^KT`Zt3;I6OV!n_)kkJKP!}E7oYlB*KHY2jmqggC-_wbrXf5U6*F_8%G5#&l&{<0Oe6YGH;xxS#z`2}7e@}LP9dd(r1eGYYe%-Wb$4F7-TvVUjtP|cEKhGMCZzN?B|-0}^viiPs@CtLlCmaw!X$h7s=lAV5oensSADoP(@r(~Dx<nFpPc*~D|RNNq3EVZzl7aE3%UFaed_(=x2zEv)g{Y(YruI%ty*qrLY&V!3Lc<@j<Z8$0%Tudp$7dH*I3SkDpV#Dtk#Zw6#;51%sstzY0aSA33!dO)8;_a0fVxjxC(2k|cjpEE-m_LG{jy%xmg}zffs0*5<EHEU>xOlpOmnF0E?=ux0Mr&7jB8ZmB^g6}_WKow#ha%ct{6t|$D24x8>f~T&dT<L2uU<q<_1xO6a@|P%yY^H1ktggSD!L%ES!MpIU4LZMt;!$F*6}JOH_$t6IFwp}?G|6N<yMvRZ5rfYg;iCuwoP@2o_Gq-rJv~%q@@T+E~YvD)C@vlr67s2mg>B;EtkZ6oxf+5o47|;!O<(;ggk@uJbqE`UUhGxX+8ppHcwtRZH~aj-dB{=l>_$1Fd~Vyuqlg}j3?H@FbeB4x-Xl!?}%(R6eHplUWf+ettl;%&#xDw#NOfs54;RVyM#04H$0$@VLhlRvcSVj)(E5~kF-0)32$T3<bCk6fkq|Lt)PXLC|SGax)bX2$belo!Sxl9nZXE*ZfB!NW{2NsO1~$x?My_+W$Z)NDJ4y54~ZjuN=Gd^yhJu)a*Jh=8$!rQknMtaOVMWS0UHv3e8sXGF1fr$TG6V?-%}Dki-E3i7r3MHn&W6(`u3o67rzmn-@^@*`)-sL&+xYrB8h(G1%{U0Sxn|qg1&rveXbCo__EF_NDJal&C}phw_bgfks+V=xc}ZY8Ts0yi@$LjNJ(ahO=Eu)Y5&zTrBRVlw@-|ZAt<7u=++OOv&agluA>(XwrAty3Pzgxc2!@MU7(aYKklYb|4&8jY#N5!+)=|!6{=GL&MlfI*O_^vvf@-tukp5Xz3or7riCJCuq1M`O6L)7NX<>Jrs^Jm$_~}3O_g2j_IYJ<P9RCE9gPKv6uEM5^$(=jAN*oBab+>sp||sRo$_TNvl)LcZU&Wb;a!}d5f8tr8HmPM2dJ5^>cV&`A@X?+6E2PT=@{1N;5i!@_iqO0eT+C`gV`J|(-m;(e&ul0G&6GW5N&qV3|I3s4#Ep~ltNIZQwTU&uLdBhH1R2gtZO)Mt@t_#?_hJPV1p(S3gUp=-ib;jRQz1DZ}s0`ESS$S5!RoBKFX^>oLUbBnd}iTZCqR%aWQLvwY>ig*n)*V')).decode(), _PLANT_CORE)

_QUEUE_ANIMALS = _QUEUE_ENGINE['ANIMALS']

class _QueueBox:
    def __init__(self, **values):
        self.__dict__.update(values)

def _queue_stock(obs, action, cfg):
    farm, private = obs["farms"][int(obs["player"])], obs["private"]
    stock = dict(private["shed"])
    half, cap = int(cfg.get("boardSize", 10)) // 2, int(cfg.get("shedCapacity", 100))
    positions = [farm["farmer"]] + farm["hands"]
    units = [action.get("farmer", [])] + action.get("hands", [])
    for pos, unit, inv in zip(positions, units, private["inventories"]):
        if not unit or pos[0] not in (half - 1, half) or pos[1] not in (half - 1, half):
            continue
        if unit[0] == "PICKUP" and len(unit) > 1:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = max(0, stock.get(item, 0) - qty)
        elif unit[0] == "DROP":
            for item, qty in inv.items():
                stock[item] = stock.get(item, 0) + min(max(0, int(qty)), max(0, cap - sum(stock.values())))
        elif unit[0] == "PLACE" and len(unit) > 1 and unit[1] not in _QUEUE_ANIMALS:
            item, qty = unit[1], max(0, int(unit[2]) if len(unit) > 2 else 1)
            stock[item] = stock.get(item, 0) + min(qty, int(inv.get(item, 0)), max(0, cap - sum(stock.values())))
    return stock

def _queue_signature(farm, private):
    return (tuple(sorted(private["shed"].items())),
            tuple(sorted(private["seeds"].items())),
            tuple(tuple(p) for p in farm["hands"]),
            tuple(farm["unlocked_quadrants"]), farm.get("hires_today", 0))

def _queue_simulate(obs, own_orders, rival_orders, stock, cfg):
    player = int(obs["player"])
    farms = copy.deepcopy(obs["farms"])
    market = copy.deepcopy(obs["market"])
    private = obs["private"]
    # The opposing stock is a hypothetical mirror, never rival-private data.
    privates = [{"shed": dict(stock), "seeds": dict(private["seeds"]),
                 "inventories": [{} for _ in range(len(f["hands"])+1)]}
                for f in farms]
    states = [_QueueBox(action={"market": own_orders if i == player else rival_orders},
                        observation=_QueueBox(farms=farms, market=market, private=privates[i]))
              for i in range(2)]
    _QUEUE_ENGINE["_process_market"](states, _QueueBox(configuration=cfg))
    own = farms[player]["money"]
    rival = farms[1-player]["money"]
    return (own, rival, _queue_signature(farms[player], privates[player]),
            _queue_signature(farms[1-player], privates[1-player]))

def _queue_optimize(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    proposals, seen = [], {tuple(tuple(o) for o in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] != "SELL":
            continue
        for earlier in range(index):
            permuted = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            key = tuple(tuple(o) for o in permuted)
            if key not in seen:
                seen.add(key)
                proposals.append(permuted)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    original_idle = _queue_simulate(obs, orders, [], stock, cfg)
    original_mirror = _queue_simulate(obs, orders, orders, stock, cfg)
    best_orders = orders
    best = (original_mirror[0]-original_mirror[1], original_mirror[0])
    for proposal in proposals:
        _QUEUE_STATS["queue_proposals"] += 1
        idle = _queue_simulate(obs, proposal, [], stock, cfg)
        if idle[2] != original_idle[2] or idle[0] < original_idle[0]:
            continue
        mirror = _queue_simulate(obs, proposal, orders, stock, cfg)
        if mirror[2:] != original_mirror[2:] or mirror[0] < original_mirror[0]:
            continue
        score = (mirror[0]-mirror[1], mirror[0])
        if score > best and score[0] > original_mirror[0]-original_mirror[1]:
            best, best_orders = score, proposal
    if best_orders is not orders:
        action["market"] = best_orders
        _QUEUE_STATS["queue_turns"] += 1
        _QUEUE_STATS["predicted_margin_gain"] += best[0]-(original_mirror[0]-original_mirror[1])
    return action

def _purchase_queue_apply(obs, action, configuration):
    cfg = configuration or {}
    orders = action.get("market", [])
    if len(orders) < 2 or len(orders) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    proposals, seen = [], {tuple(tuple(order) for order in orders)}
    for index, order in enumerate(orders):
        if index == 0 or not order or order[0] != "BUY_PRODUCT":
            continue
        for earlier in range(index):
            proposed = orders[:earlier] + [order] + orders[earlier:index] + orders[index+1:]
            key = tuple(tuple(item) for item in proposed)
            if key not in seen:
                seen.add(key)
                proposals.append(proposed)
            if len(proposals) >= 24:
                break
        if len(proposals) >= 24:
            break
    if not proposals:
        return action
    stock = _queue_stock(obs, action, cfg)
    idle_control = _queue_simulate(obs, orders, [], stock, cfg)
    mirror_control = _queue_simulate(obs, orders, orders, stock, cfg)
    baseline = (mirror_control[0] - mirror_control[1], mirror_control[0])
    best, chosen = baseline, orders
    for proposed in proposals:
        _PURCHASE_QUEUE_STATS["purchase_queue_proposals"] += 1
        idle = _queue_simulate(obs, proposed, [], stock, cfg)
        if idle[2] != idle_control[2] or idle[0] < idle_control[0]:
            continue
        mirror = _queue_simulate(obs, proposed, orders, stock, cfg)
        if mirror[2:] != mirror_control[2:] or mirror[0] < mirror_control[0]:
            continue
        score = (mirror[0] - mirror[1], mirror[0])
        if score > best and score[0] > baseline[0]:
            best, chosen = score, proposed
    if chosen is not orders:
        action["market"] = chosen
        _PURCHASE_QUEUE_STATS["purchase_queue_turns"] += 1
        _PURCHASE_QUEUE_STATS["purchase_predicted_margin_gain"] += best[0] - baseline[0]
    return action

def _iterated_queue_apply(obs, action, configuration):
    cfg = configuration or {}
    base = action.get("market", [])
    if len(base) < 2 or len(base) > int(cfg.get("maxMarketOrdersPerTurn", 10)):
        return action
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get("market", [])
    forecasts = [[], base]
    if raw != base:
        forecasts.append(raw)
    controls = [_queue_simulate(obs, base, rival, stock, cfg) for rival in forecasts]
    current, best_key = base, (0, 0, 0)
    seen = {tuple(tuple(order) for order in base)}
    accepted_passes = 0
    for _ in range(2):
        proposals = []
        for index, order in enumerate(current):
            if index == 0 or not order or order[0] not in ("SELL", "BUY_PRODUCT"):
                continue
            for earlier in range(index):
                candidate = current[:earlier] + [order] + current[earlier:index] + current[index+1:]
                signature = tuple(tuple(o) for o in candidate)
                if signature not in seen:
                    seen.add(signature)
                    proposals.append(candidate)
                if len(proposals) >= 48:
                    break
            if len(proposals) >= 48:
                break
        best_orders = current
        for proposal in proposals:
            _ITERATED_QUEUE_STATS["iterated_queue_proposals"] += 1
            relative_gains, own_gains = [], []
            valid = True
            for forecast_index, (rival, control) in enumerate(zip(forecasts, controls)):
                result = _queue_simulate(obs, proposal, rival, stock, cfg)
                if result[0] < control[0] or result[2] != control[2]:
                    valid = False
                    break
                if forecast_index:
                    if result[3] != control[3]:
                        valid = False
                        break
                    relative_gains.append((result[0]-result[1])-(control[0]-control[1]))
                own_gains.append(result[0]-control[0])
            if not valid or min(relative_gains) < 0 or sum(relative_gains) <= 0:
                continue
            key = (min(relative_gains), sum(relative_gains), min(own_gains))
            if key > best_key:
                best_key, best_orders = key, proposal
        if best_orders is current:
            break
        current = best_orders
        accepted_passes += 1
    if accepted_passes:
        action["market"] = current
        _ITERATED_QUEUE_STATS["iterated_queue_turns"] += 1
        _ITERATED_QUEUE_STATS["iterated_queue_second_pass_turns"] += int(accepted_passes == 2)
        _ITERATED_QUEUE_STATS["iterated_queue_predicted_gain"] += best_key[0]
    return action

def _partial_plant(obs, action, cfg):
    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    need = {}
    for unit in units:
        if len(unit) >= 2 and unit[0] == "PLANT":
            need[unit[1]] = need.get(unit[1], 0) + 1
    available = obs["private"]["seeds"]
    blocked = {crop for crop, count in need.items() if 0 < available.get(crop, 0) < count}
    if not blocked:
        return action
    farm, private = copy.deepcopy(obs["farms"][int(obs["player"])]), copy.deepcopy(obs["private"])
    chosen = copy.deepcopy(units)
    kept = removed = 0
    for index, unit in enumerate(units):
        target = len(unit) >= 2 and unit[0] == "PLANT" and unit[1] in blocked
        before = private["seeds"].get(unit[1], 0) if target else 0
        _PLANT_CORE["_apply_unit_action"](farm, private, index, unit,
            int(cfg.get("boardSize", 10)), int(obs["step"]) // int(cfg.get("turnsPerDay", 24)),
            int(cfg.get("turnsPerDay", 24)), int(cfg.get("shedCapacity", 100)))
        if target:
            if private["seeds"].get(unit[1], 0) == before - 1:
                kept += 1
            else:
                chosen[index] = ["PASS"]
                removed += 1
    if removed:
        action["farmer"], action["hands"] = chosen[0], chosen[1:]
        _PARTIAL_STATS["partial_plant_turns"] += 1
        _PARTIAL_STATS["partial_plant_kept"] += kept
        _PARTIAL_STATS["partial_plant_removed"] += removed
    return action

def _hire_recovery_apply(obs, action, configuration):
    global _HIRE_RECOVERY_PLAN, _HIRE_RECOVERY_QUEUES
    cfg = configuration or {}; step = int(obs['step'])
    per_day = int(cfg.get('turnsPerDay', 24)); hour = step % per_day
    own = obs['farms'][int(obs['player'])]; hands = own['hands']
    moves = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
    if hour == 0:
        _HIRE_RECOVERY_STATS['hire_recovery_day_aborts'] += len(_HIRE_RECOVERY_QUEUES)
        _HIRE_RECOVERY_QUEUES = {}; _HIRE_RECOVERY_PLAN = None
        hires = sum(order == ['HIRE'] for order in action.get('market', []))
        farmer = action.get('farmer', ['PASS'])
        if not hands and hires and farmer and farmer[0] not in moves:
            planned = copy.deepcopy(own)
            for _ in range(hires):
                planned['hands'].append(_QUEUE_ENGINE['_spawn_hand'](planned, int(cfg.get('boardSize', 10))))
            _HIRE_RECOVERY_PLAN = dict(step=step, farmer=copy.deepcopy(own['farmer']), hands=planned['hands'])
        return action

    for worker, pending in list(_HIRE_RECOVERY_QUEUES.items()):
        if worker >= len(hands) or worker >= len(action.get('hands', [])):
            _HIRE_RECOVERY_STATS['hire_recovery_unfilled'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
            continue
        current = action['hands'][worker]
        if pending and pending[0] == 'CARE':
            _HIRE_RECOVERY_STATS['hire_recovery_caught_up'] += 1
            del _HIRE_RECOVERY_QUEUES[worker]
        else:
            action['hands'][worker] = pending
            _HIRE_RECOVERY_QUEUES[worker] = current
            _HIRE_RECOVERY_STATS['hire_recovery_delayed_commands'] += 1

    plan = _HIRE_RECOVERY_PLAN
    if hour != 1 or not plan or plan['step'] != step - 1:
        return action
    missing = len(plan['hands']) - len(hands)
    if missing not in (1, 2) or hands != plan['hands'][:len(hands)] or own['farmer'] != plan['farmer']:
        return action
    active_commands = [action.get('farmer', ['PASS']), *action.get('hands', [])[:len(hands)]]
    if any(command and command[0] in moves for command in active_commands):
        return action
    orders = action.get('market', [])
    if any(order == ['HIRE'] for order in orders) or len(orders) + missing > int(cfg.get('maxMarketOrdersPerTurn', 10)):
        return action
    schedule = _hire_recovery_schedule(obs)
    allowed = moves | {'PICKUP', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'WATER', 'PASS'}
    delayed = {}
    for worker in range(len(hands), len(plan['hands'])):
        commands = action.get('hands', [])
        if worker >= len(commands) or commands[worker][:2] != ['PICKUP', 'WHEAT']:
            return action
        found = False
        for future in range(step + 1, min(step + 9, len(schedule))):
            upcoming = schedule[future].get('hands', [])
            if worker >= len(upcoming) or not upcoming[worker] or upcoming[worker][0] not in allowed:
                return action
            if upcoming[worker][0] == 'CARE':
                found = True
                break
        if not found:
            return action
        delayed[worker] = copy.deepcopy(commands[worker])
    proposal = orders + [['HIRE'] for _ in range(missing)]
    stock = _queue_stock(obs, action, cfg)
    raw = _ITERATED_QUEUE_RAW(obs, configuration).get('market', [])
    forecasts = [[], orders] + ([raw] if raw != orders else [])
    for rival in forecasts:
        old = _queue_simulate(obs, orders, rival, stock, cfg)
        new = _queue_simulate(obs, proposal, rival, stock, cfg)
        if new[0] < 0 or new[2][0:2] != old[2][0:2] or new[2][3] != old[2][3]:
            return action
        if new[2][2] != tuple(tuple(p) for p in plan['hands']):
            return action
    action['market'] = proposal
    _HIRE_RECOVERY_QUEUES = delayed
    _HIRE_RECOVERY_STATS['hire_recovery_turns'] += 1
    _HIRE_RECOVERY_STATS['hire_recovery_requested'] += missing
    return action

_QUEUE_STATS = {"queue_turns": 0, "queue_proposals": 0, "queue_errors": 0,
                "predicted_margin_gain": 0.0}

_PURCHASE_QUEUE_STATS = {"purchase_queue_turns": 0, "purchase_queue_proposals": 0,
                         "purchase_queue_errors": 0, "purchase_predicted_margin_gain": 0.0}

_ITERATED_QUEUE_STATS = {
    "iterated_queue_turns": 0,
    "iterated_queue_second_pass_turns": 0,
    "iterated_queue_proposals": 0,
    "iterated_queue_predicted_gain": 0.0,
    "iterated_queue_errors": 0,
}

_PARTIAL_STATS = {"partial_plant_turns": 0, "partial_plant_kept": 0,
                  "partial_plant_removed": 0, "partial_plant_errors": 0}

_HIRE_RECOVERY_STATS = {'hire_recovery_turns': 0, 'hire_recovery_requested': 0,
                        'hire_recovery_delayed_commands': 0, 'hire_recovery_caught_up': 0,
                        'hire_recovery_unfilled': 0, 'hire_recovery_day_aborts': 0,
                        'hire_recovery_errors': 0}


def agent(observation, configuration=None):
    global _HIRE_RECOVERY_PLAN, _HIRE_RECOVERY_QUEUES
    if int(observation['step']) == 0:
        _HIRE_RECOVERY_PLAN = None
        _HIRE_RECOVERY_QUEUES = {}
        for stats in (_QUEUE_STATS, _PURCHASE_QUEUE_STATS, _ITERATED_QUEUE_STATS, _PARTIAL_STATS, _HIRE_RECOVERY_STATS):
            for key in stats:
                stats[key] = 0
        agent.telemetry.clear()
    action = _donor_action(observation, configuration)
    for transform, stats, error in (
        (_queue_optimize, _QUEUE_STATS, 'queue_errors'),
        (_purchase_queue_apply, _PURCHASE_QUEUE_STATS, 'purchase_queue_errors'),
        (_iterated_queue_apply, _ITERATED_QUEUE_STATS, 'iterated_queue_errors'),
        (_partial_plant, _PARTIAL_STATS, 'partial_plant_errors'),
        (_hire_recovery_apply, _HIRE_RECOVERY_STATS, 'hire_recovery_errors'),
    ):
        try:
            action = transform(observation, action, configuration or {})
        except Exception:
            stats[error] += 1
    for stats in (_QUEUE_STATS, _PURCHASE_QUEUE_STATS, _ITERATED_QUEUE_STATS, _PARTIAL_STATS, _HIRE_RECOVERY_STATS, _DONOR_STATS):
        agent.telemetry.update(stats)
    return action

agent.telemetry = {}

def kaggle_donor_opening_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
