import copy
import json
import zlib
import base64

_DONOR_ROUTES = json.loads(zlib.decompress(base64.b85decode('c%1EhU5^|`lH`BkGauC5Bt^~}hvI64rPKl`ov<eeg9UC52ORbmnA?3?+<!l)yQ?ZQ+}zCEBeL1l?h^~u#mxBdh;TDE_xO)zfB)Bi|F^$=_3Tf-{>QWb`Okm<m%sh}*`I!W_T$@6pPv2p{MrBd=l}CR{_nFt{rcPUXaDlgfB)Zq`?qI*`t{dmfBEj?`)9vB_dfjj=YRU^j~{Qp`T5;X&z?W~<uC8w{`Bnm%hO-p{_x%RZ$CVH{_NfDFVCJ|pT7R|{{1)4o<IBk{fFBho;`mRe*Nh$@8AFU?D@^``-i7r|MuJed%o+=ckll3=O0gRx!QDW^S6g*Uj6<|{N??ifXAW#upP3jIS=hk8g%(<_GM@g|1YFTzr6qS({{qo-~9UQhue=o{pH#2eV4E9e?=aA`f2&efByNq58wRt$G4w;`uTTDBCi;Jxqa36C-lwv-QZ6j-oAT(o>V%e55N4~BKEVne?)xfZXS0}`Ssa9{BG9lwf8^RzVG3i&4=^T&)>XzD@OGG2iwO!e6#s*e(d?1Z$94gL3;moG_r?petq`o_UF+QE?-F_JN<O?<om{)TZJF|U~S~d5C41f;L-NCPd>j(KX}|>`GdC>^21N(ow56Z;VJM<zr6kF{m0@P;&UIKg5RK~HNN2TI5I|!=hlX%GrP5+IsN*6>+X)xd37zC-MC4|2j9Q5_uRwAe(3e`AqP)eJL2*~;jt6G-2I28u7lHqwh!^{_QQww?|%C0KfM3=({~@f`|rESXXhXKf7{a#KbO8P|NC%4?dRvy`wzc6yqo`W@7+PS`sTMqCvL-`Oqz7{+oH32oN+l!XD|WU1YySbbvCHcCuq3rqpQ&A*uMGW*VzPc^uZR^`EO@WQt!qk4|TJ0Pfn$DflI#X<pt+;Af4ej-E0kA-f;Qj!>1DbB5NWZljq-b-o!kqcwR~;pKaEeuU0zG4u8QozSvL9Jd@I^P6JFGMd_>5UKtI5`RLi-N^f9pQGb3;y*C}EnK1*?Bt5+;Cyl-UY&&aTFf&%A7p)koX@53z69SFM_D*!zn}5}ZDA@9X+kk!R!b_CXi{6uXwDJe&>k@G!Uwl3i&tArOYOnOOfm3@~q!&L2nZZDx!6Vjk13&%r@$D~ve*f{~KLMvNIx&~_om+r>zYY*!W9c-Octe+#ok#Vuhm3zLx9aRk`#vUPqy`7KWZ<C3V6z-N+>#dyHsRQX@u+F?F6Zqib0}v|mdLIV4t1s{mkv07+CgKsxGT)7UDAcqSZ!AQ`nPSUg2P9QFsp02aL@~qi8y}1n6tUob$$BJKg?k@4pQN#Ml3t$rFt|icNdqqtW9c`GPV;AWbiPe18^R?xD^Cu=}2<+?8Go~mIXd1$=RY?d+~@o`W61n??s7QJ<nuZaA2V{g8v9}gg4B{0M5e}snzrI&wtWnWSl-?^*v@aZteghf&+`7u}U;~2}}4n-msb!1aHVa^y3F<Q5U4TVe$nj)3=UhbY1f`q~q~s#fI!l>BAT5f4=<fi3lB?QF+3$1)n#X(f>Km?+F3_;Ia$HF`bh-T5xMp^f)0n*!O(OT_;WeVnBnk&veTx&Ij1br<9814HrPr5QjNkC<wKiT?j1Vk$vcl((#?p^eLcokL<)>-hTXVQyN&K8^~`wvQM31vwCzMtgZ=L94F;nkJ6g<mVL?jtoH!!-siaL^BIQ}96@VDaff=Ua*C!s)#H+ME<srJib+q^kT0xsRp-?b2l=XCy(P}-YKQdbB%B%Al?1mvztS94!?AQW&C82>Cw1)zI6Sdo#<Ou=P|4StJ}(dI!{?duwsZC*=ACW~U&y>~z02cfJ|l4-#S9J~!{NgsU-Rm!?`-mfs7LZ8$v8bm=C|A#x_VZY7D8S+lPet^#Mp@VVJ3}wyDvnq)Y(ubeADgAn+_=(mV>mt%!ee+i3zEfo#6KN!$Wlm#`k`B`@=U3W4;;wRuESJKO4B^F&2LQhA2_Y-hmF?6#n+m*%#U+2Y&a^jqNw*4;K5&`+7r!+#`puFGzCJsw8qL3j(?tCpzuw^Y~15_|=acBms@>g9!!~U$b)95EM#B0sA*R2SPiIu{E&-NURJna(GdvtN+jWr%S4wjAcWDOV(}Ob^<PM=#)VjGe(n7vPDP))HwNpd|wX+Q2(m`Gb6DAh6UD$ujuXMhN1;8GLMKxT1u(BYAYc*E#*3lxf-3!W`Kb&G%zS&f)>S|tPKeb&`dj|jL7`EH>vcov(cN`uO3;6Qx)mFJ`AqTeF;Lr-69l59BBWy4kUIz#dRr5<aqEH9I4=|h-jAp<)J<U2-V<l%S`35Qba}lH<V1bBv-W=7>c2i<cBD55^-TyDHB~{0I~r@9RpM_;9{mtIN7z43;>NvMSEPv=LOW9m{Y{JG@G;9rd~LzcTxj0@Rg8GyXYBf9Kf@$&n<*jd0Fyu(>Hybfk++GM;Quqa56Jk{Q7Uc`_|_eAK3~jy7To$Ao>2|Rw8@#+I|-km6@SD?hGs*hRTP<9WQ;D==XnNue=mZ4}2YoqEdePkziE%A0GopZPJ*ZGLYKPo=cF_B~00YPun0T3$sl_CI$EyfHLKNZf2?nr<U)+!v`zzd<?gJdwcuoeGE&!d;9U@?Ol9v|NT$5-@pCoc5{)ySjzJ=_F3+O=WTS`X%+~J!9(yjxgVk`c4(IeOM~&(CzrX<knYJq;vWwNfqqpRl5<l|{W|^2iTyYpcmLK#AyD2A=5KZsvmoSIr>~kL#Ci`*1{LVhoH-zWB0>mJ9yCfcl-IHq6RZMX{=y7Bj8`XG4PKvT5<-+4O+!xz7ze0kI$HuOWEH1tE*I-QO8)LPtC`DQB;c1?&)|r8h=$*9^O>2D;Q>{kChmVAnl=>j*NjZ*?T)z3i?dBay$2WR`|m#d<Fn^i*JaJn>&$mabB*$H-DPQM-Ho9*H-n=W$3(d;qX%(ggU1_DB6Y3QiMddPELlgul$J@Kd;!3~04z4%u)&wAtm<~Buk6(9rC<k??U;Kbm>A$C=yw2y;dJT&h0%~KXYHfl4YBZ~uEHA|qt!qtDUh97GG5v0?Rj2e9bf2%%Vf&vy`W0C(Vz9_423Hno`OjUCVpx8rM8I_i|7^*Ox&W7$tV^JQb5rpWbc^TU1}~Lyva;Jf9l_GqeOAFjlN>;(_$OS*ty}CCAu>DuZpiSA)Xguj}&Iy0|4+Db@R3TCYIyA0DzR0lYRSo<7M7!)vu!J2(05niKv4kAl1vF;s*vnYSGwYdCu1`^<(t+Z%Y1t$dI7SiVn!!7=OMjli{z|D%exqldYC-aYO#+p=~M2mFoWd%dohp8Sz{qZ7L@%OP(tBvOzPpKV*Tdk?<;Mu+K99lUbjK0}A+4Dz+qwuv|d<=|bQVAdC=g%NGtuoIFw`TB06rS`b(TM8><1liSL!J9}^(7f?wSov@U62E~aXbKqQ=Os<4LFN~-7V54YN!2<FV_g|c1Q5Ai0jAQ1z^ffkMv<HD)LQ>dcst56dw=sbLCxV-@v0-mOI5uxAU{s=q56%d5Y&6oK(bAGT5?G?HedDcrmXKiiCSY9C^8<~+?%9Ls``L8J`J$1V^BC`99iatIrrIvO+`eHPunNHD{Ii!DO`Nt&u~Gt*B%AAEJPE#ypc+tiNnicT9wX-D>&G8l^uNJ|Qb4c%?FV4{2g{IMQJtu1z}V<5gj#ZB#n85*wMY)jX0dU_&@@>>d`|{U24&|eyebV{Q&BZxLBJINGG&iM;_d(|K<O`Z46GuIh96Xs3yjBB#v!xbpY=^XV#sKT*O-@h`4r-i3##l~8|4my_|J-7Ue76PuLTn`FC9~-9+FL==R}V^TNvSg*JYEITOO%?xB)Wfy~g-6p9T4#z%5Zsyga*f$R~O!sFg;UAEeC+lTfRW+wn>mN}$BT){h>Z(1>1vQ;Qtp)Fh*vyAbsv7aUU!8+g|MtrRGr!sM=l0oRRqza4r?N!rrPkFqi1dd5u>IQvOsYbyx{b`8Lp<_lnp&I@a7hou@3h{4xvjg}@?6pGl6PH%<jc(p(&;QtkB)v%}#B~$$D3}OO>O^OEpop%8y5<Fn%daH$f?tC(UxyT2q1;8PcnqQY|vg`-dRtWzObj~RjNc}J}k4_OmvR1)ecsA~iP8!JGCL_$iVQQ64(#R9JM)7or1DNSacZo6&-=C6a-c(bTm_#=;m6hiSA2us=Ri0=?G(0C_mV>`7KzNFsyap3OZohnq3lZ80Q(Gju9L%rA@C4sNL><%{#$O<^zl`Z(2A~M%iToKWVo<|$c4Hl#mjZl(Rv@MRC$q&^Q&32xl=vze#xj#YgQ9<71-hnlvj7@EIJGo3dhdjopoIxR3@BFz89x86wnI+^--!f`bU|%iqw;a<>p~35P@se%Oc@D#kCZ(7CK?W-1|2;2Z2v;2TZ$E43t0yTCa}Zxn!44ya<5L#?2>hXVn$}Psv?CpWAm9B4eS!B0;O9$f(abtHa5i#V)f;Ql-#ZWG)-`*R$D&FVgeBGJRl=mDM-SKQF-D|aMmz^Rjx%SwS<c8>~n>L<(uOIcKpaS=h+U{Xwahgaw)~|wEQouT#+4;9@YFt`Forr9olbX8}O#@kU?^nYmoO{zN3XvEkGQ~uBK!9{@ZUil|3RB9*cf#AzD()^^1vSuL*1Cz*Nab5pd4`;zQ;9OCSdx(tj!#kg>JVS!TE_y>P?G>XF1`j3yLdhNYlgC>ZmjFxz(Q9FE{wFlVO${Z*WsI-$)9SGA~}b<w5kG$v?Io{%J7;W4oF@?mJefu|PNZRWBXy!)&@$2Cb^LD}=U)I(aqSUdL8^HEjDT9GUoQUm@mAS>l|T@O8%77HQ|8GA;4HUYC~o>vC&d?Jsa_^z%ahGtbTH=c%4X;!bU79)SzjXhvvH<k&t2-)5wM9rxc^jBadWxh?1E~8?$#<%Apvu5!86tz4Xwm@rtX+t5=Y7`@Hj3!=9R)HqE^Twym>e&5~$d~^c?=m7TkeRjZ+z!C>+U5u5w{`|}qOvs5tJ7;F=T>#IMZN3J*GT9y#^HpA1LyEssqOcK!>F7O@B2d#4g(W_ScgCs#K5#<4Xzh_3G%q7%T@CfauRZOJ_t|4<QqbTlu~HigFVveSyJYep#Uxypx|PrNm8~S$#BEN!ro8lPOr&mR7%x>G&IUVUAuCaPt16w+3{iDls<Cf1DpW8|B8wxi+9(R2UR-OoyzXqQ|^v+7RtrjX5nJ2Jn6O$(Y$mOqn4X9;<)EMNf4OEj7{Q3?<3<@+z<EJlp4qp1xauYnF~$96E;WMgXS{fd1|B!NQHz=o#RLO+4NwN2{R1~xrnU`I1=o^)7gM(y0*)zuw$Xe76fCcQXXzeLAgd%3DGTTN&=HikIc8j>k70B+WwNXMVJ+S9wJbdX!gcOk{B^ov(A9+s}TWjA@K?Dd}S~zd%Gez0I@m%C%8KLd|^<4kWzev$5)szy<ZI=OxK&u7hCpWJKraO{8eHDS0b}uxLM_<U0+PH8%GwN6sZ2DE~l9M(kK+Lr#I`84U!&EtmKrkI3Sxd=2CEZcP)uwh4><3vnuaklpUCfPa_(a3b^SXO*~yxeV2&cf~>y)i*f*7^4+{j0#G#$H93Bex#+r$a*=4q?7o{sk&{ObS6FcTpwJwRX!&xRNRJszoI%_rqX<xBhNb0dW9X>1?BMufLrv8-dxyTauvl~yEFokJW>L4&ieh(vpa`)e7Az!Ks6`|t9dap!v#eA2*GuRhiZ<dz8Zg&<gIHN^#7j)yWzfh~-AZ<EjQ9Yrz@=5@mg<B1iiXMLpaF+LZpq=Qt2Rf+gK+eE7S4J>x~H1W2M-r8-w-qxoG-YCOh#}D98!eIGHa`|j^YS|YKkR21M~u`Gf#kUQ*U8wx~y3)iz^&@>4b2vM-JoKyf5KIK#bR^or)(s(b5K!2_1PJMvq*0<PwLI{vvP~a>SkK0X*Iy)CX7YSxi%e!dI~8DsgKqu>kDJ`*TFbbLqYtwYh6<@uo)!JYWkXf-$fKEXg$a&YNJjP|Rfhb~{i42|zhF|AAqj80Badrp!W8_OSWo^(MerC9DTp#t5Y<$g$*8To0ZSNXv0y9$v2trE2>kQGL@!N#|AWKB*3*8ndD@b@$kT$s%IC-rq}@XfRmTH-IW=jQ1-iI@LzL%=vEWWK*dtL8#E-kP4{Q4I=O?Ty&w-;3x>W9o~^usv%({8t6SECU-A7-(yZ;TR|R5fTTQCgGO$%HUJ!ryL3x5725}vEkK({r?9uudeN{<Ed`4IC5M;^eQRU}omHf9T#)#%KC$6yS6uL3?(tQ?*jHKbKfmlSNqQKIFPw@+6j1pWqzg#Y{wvBPtf-x^7_S#=Elegqkn8u>7XR}y9N6XGYujU{G_b3U7AIL?_il!;Xy&>j#8l8r`h}~QR=dRr@Rk=ethLH%U53Sr{&o=%6{bw5U??GS#bE3VlO}}Y8hTRto^DKFYtZ&UL0uaEj}hMHpf^f#B8=xHQuvin`~-nj@_SA?@Kg()|IiWM`|Me>z$xll<StgME1LPPvx>m-DuR7Fyl71|&RSN^f0`l|2>~G{fPQ6g1A4DwVjaN?`|nTZA3SVL{z5Cw!c7VqE;N`RyNQ0EGP{&PLtMukvq6;yOymoK{}s6lBMw+3zZR_0d=jES4vy~Mvk6~`xc(0NZvXo^hW}OZ`tmmky>Rno(+ft>-=GP6;eYXVLipuQdX!&JP&$F)o$r{i%;WpX9kv~ndcEF4JgwlsfDUP2B+3k;Oae5#D`xPsdX?W7gF`H<bh;!S6OZ_*5DL#uY9Vu6SqoL6J|3mYfT|EF7pGKPD{BVjCDB3(*ab7(LpRUI2x8@~c7vhv>l7MLjy|j@<$!!5hqhpZPtm(EaJ>Q|hG%=^3cDI_R#^hZBJdxO<Fsd!gU<;edQL-;^yY^d04y}4qgT{A;30J|=o}cg?)(cQDi<x*{;MtT+$}KP1q+}h0I7B5D~%OmD6Dy^tRT@BdtU|CeU6T^D2J>+7yR{I^fufX5N$@JAd;yzwu(FkUYm@V2t+kW&?RPa{X(D#9uKEvpL@u$vrziBAT9}CR0fXRI2##^cr66p95!1Rp>m=+hLqZ*_dkHySCKec$~00O##hrN7Vd=%FWnjoTiwMD9d4hn6-}h29K!XFNJEiuA|=Y>NT%b!N()fxFsZ4?Ne}ECctVTj$xom?t+Asb1i6oz++S19P)!riRU=VIi!sXDRRQ?02J#uxLNN>$H0u^ec!=E0$fE$85cLmz!fPJ9bU79fXWE}`!J};11i*RNodVv9E%AicYB+&o=&2Ypc^;co;E{`)@?igjVT8#l+%8Y`&1ybM`ezp3LcVj?wuuIMI%dno0sMCvF&2K?3)PBUiCqJ8cB-X9W(Di5xNP893)YKSR)I}M49r+@iLx*SQrWCbR}YVXS}a^kgn7jL19sW!*FtpVVg@IKJ-E1Suer=3kF~2(Az7Ne(=;pj5a2hf)(ZH!Y>-p(1q>C;tim)K;0I)@1X&Fpp0KWQuHva1@;V5{zudcM1wF;)YRWB=am~Gj1tk{U{0_5}f_RE-ULaXN2Tn&!uNv~*SQtMhIQ0I$)K}sb(mM;?WxVW6bZfgA`FfI|T)nAgzI?4yTq=6NBeWS&3*l#o_z^8Y_xbcP@Cke69_lv&iH#TON7&tNU2*()%JswXzT!prS&9)Mo^4aOA#>+3Pym*ax)DqYAFg38OfU&#0bL4oCYTm}+yGzIa@5WTJ%Gz3p$Np6izza)-7H56IHz)X`6abM01wy*IC(l*UR0H8)wtcArsNXmW^o3e*or_t<CpT-V=cIhy+Jn07$QbOVOAth7CT98lz=g^y9+h*be;1fmd9m%Ujd%EXtRYTmd8E{IbO!d2`H25$AGSorAB}bjh3*2uke*)eiA}FM9y0&BjkvGzjd~qDgwakG~+XD8<Um){d+7}-Citx!(|UB2~Ms}sCn#h`Vg8GwPxk$xm6IDRn%w+tn~=fDVMab!R-(dx#|N?a1?JuMj8rd3Y8_B883RE?8Ua^K8<mk{2XKo(kf3dCgwm4o9&B0oNQBZPVB|&lm;33j*|zPmHN0|HBxq^iy68jCt~vCnw$E&$d~#2?KZe@5YnJ_3=c&&)ykeovrGV?+Xx9U@n$SJ3HnEiXvAKy|JP&eo!kJCG|L(cTrcNtY#H*7DiVyPy5bEt2o11WohX-b4iZNYrJQldIxeq*8S&=Z>E5JxI`B8i6<nRA0Q%q*b2o(@zRwUlA)6jaKhP>$z=kXZnv_qs40od~Bn3rkA&|A>|3RovszaZ^0bLM`<_9^$q$7nVXIO6V-->yI2%tm_INEV9JSSt!(Z1{)GMXs`QUGI1&a?4xf6JRmLoonFHKD;m9kB5}RGA&T@N~mf{o-6b6H)}W8BpOzJ}zc9<?q^TU8L(w#pY?MOs<D)wwIUk0Co+LyrkZ3_SvQ<Q2iy?g*>-}?X+|Uqse7c%tgGDm2o3%HKR77J=?<U8}R8MsHka)SF4sjWVzjrIA=zR!)Yt4<vs%iV{#LXU&m+(9%zQW8=EbT@_{u%nMyY)X$0t`eToU@j$Zk<%C_sgB<t@nlAd17COs{yGh6)mWU<*{2dfo#Nc&FGr8XW@Z5Sdy<X^#a)wo@T<^CYm5kZq6gq+=LTk?EWB|6S~l>$a)__0dSMIw=U^Rkj*@U#jIB)V-%2ok+NBcrs$fvK}_H9g=C6C+F&e@z8>NDV1S03b0FvllzbE@0Vu*&=>0I*V26<_h&iqP77m!?~zJ*RPnsuY&|$?MP6pg4P*|eh))ZqStx86}OB8;6Y;BSKxTzq8c#)`5D3<$VNJsv@4Ls#+D*XBMmkzdod{iE5WKVD)F?KJgU}EwUApvX+~*SD<~vWOxXcNS-#B{%ZU;+=AE?dah~wNajq$8tDu<YsZ6k6;Y?7Inps$j5VEVBRm7t5{r4;dwFLf$;wywk?e4Csi&L3T#WbdVGSn<JaW7|iO>3xZ(|v;Q<r<V^xtFnMUc+H8#_zXW$d^-~W$39*SOkSkKZ$9Qd@z(k@xPQXTTUPVun~C*DrC-ZrX&|akd(T7Onc5U_klw;<AVb6fly>HwRHxOq|XFe#?oYzN@KoM1UNnBuN;I<Drc8~Fh4sqr%^~bOC6X(N`_ER?sAx#?i_fbNM2)w=>1$eFsWw5vLLEaw2yX@;*LqJEKRVFKP?ntkeL+8ymR2Cmn_ndL|z#g_GFP$M$CbQ9C_m0L6#e+O5zgiP(l+|YTOcUxpN_ocHhrZoChM3r+Bh$vumkblwub+b?e7P*xfQ%Sl<l;BUA`a<Qo>+25C`BDWFBmzuUKWaI7W^f-2sKf0AP^R}Gk3Pyx^uH&Oh_{iqe`a=3Xr&0UB%WWNN>mKZo$;~;wNWC1a)mG%EC6=TksB87Y*N*E|Y<Pmfbchth}!rYj<xMdr*ik%bW++L6qkz$h8c48Bfyqk=Ccv@v(OS0t2YA61GkMLiT7B32KSRicJix7Bw_rIl_0_C;6yjw=YCrojGX{_XXnwit&6G-G7oJ}C@cEo8-_5gz^h8krEU{y(3FD(O60K-?!@B=G&f%bZSm5_8-pu5MjdceD(b02Px0QWLXghCJ*l&e1&5<-D{N(VHHi`1Y-ivOWQ-MEvNp^#{MW6@C*%0_95Qv`_)2GSTZ-SngJHpfbNV~M~9vM2@CFpgHTN0L;ySYwkFe(q8*XqzQ@Q=6%jYJJ2<sQZT*4M!C!c%p^Kp#vCczL=jDdEsE7T{w0xL{hkr3l8yfH4Jh(YCA6>2k5GFDGlb&HOoUNZ74Q4b}Q3li79|T+1seBD5Fx&*csX%2t}{Q&ySCpZ!#>K)}T1o;=HcK-B088qHrthlS~^}g`az>em~m&qK3g^iHy8~YyZL(`Pub7r~mcUZ&KfBbgih`PwR=Gs;rV5*pm@nDjDgeC}5SxwuqOVeJJT{y%wTKSFXvRu(aMpFc@I$aIh?}>9m!Fqnas}eUCr|iussMsRnQe0gfU-9D=#heqAfCf(3}Jiy}~oe<2M-lL4g+#oTLZEz~ycYy;xNbQLD_Eg<(x-S^5l7U<trlaz((gk*g|CA28un#YC=Z3^KuqUZo5G^xvL5mvA=_iM-?ZohW%8FJhy05p>%LC)03kYa=alHl#EipWC*mnz<G8p^UWrZ`&$e5paGBYKsqX%-cZ<rth0$xa{`EO}OATsj401BAqRv6O-k9KwV#f;La}4i|`LViAQglE3Q_XEDIHMSjtLzSrK%`hVcf(5e_uv{HTn%g;#iI1<HyTD<8|g_aoGq|*CDG*^H&cUt6yeegD=O&Jm=u`;$f4l_6w))b|{cF)E?RYlx@^p6f#l_iQ?IDq)>-HkIR(&{yAbxvYs*T=lZ<krms>gw?eU0fIR9f3GWlQew#>1Jj1il)AU_=3@2<mDzhgxE&#BB`L@i!uEG_c2*f*_=G8hGjTz3~k9{#+W@=k+sMGCV=)4e1?;x1ikPXYv`z<)IMTM-=B%Lgq#kRmD`s#Nr=G$v0&mb)5HkSPUevxnhnJ;2-Dd~w8n1*dqJ`21;zZ`*n5od3%?m@#bWrlSIk8e=9fwtu=p}!&yXzS?Tk#KD4YPe4hTd%w=_+?%0*3i5dnQoO$U6DA~!aN#mu6b&<_tpt9V1?3aj^l>(+TSBLx$$5*y&UUc#`Vtk~ui-)!5v+p3yWszA^5h=f3Ln6Z8w=ClDv^mu9K=DwLM*G$kQ0hS?DX5SNoBo<CKg$09In5I$1pH*?NK)5F!Sy`=N2br_D`x#$<g+w7CS>pbgu<Ya&$KIF!IVebmug?v-`XZ7l2H4k9h7_wfx}_h2d}n;cT}h6~!V=eA4P*ywn>r0D!!-(HnwO!G&N-sk$Vl{nm6_I02L+?l7H2?prZD9s&-AAn^yCn$dT+HnbF^nePzd6Ez5_?KrJ`5|p}uHFZ&Q^XAqf*8Q9aI_a$iU+gry-?um%khG?k0-vj{7Ug4#FJw6enO3VA$y7?lqDZ@NrO(0e4nKAUQ0k<Px6OfA3W!mmJ<HP%-pfGMr!cllxRDSaC=8%hhyN+lE3c+yUiX^Jt{%}k%!u-1tbT?Lg{p_uNRUTU%lW>$k(uLwa`m^DU7Y7+uH$Z#b}jlSa7D$vO|*-J9vj_9G(FtY}3n)W0xFHfCY2eO3<!$90?vMvywzD7wFAlQ8quG!t|wN7`9acup?T+)y=%2D}4tXBzT=YY8QpRXFl7p0Desn;p9sWtQb1C!@a1k75@lI)uet|-8n4`L)j^XsBg8U4D}LPTc;8mJQ7jrz6@-$Z5}2TP4K6)jZoB6P206}!w~;6gLt5_NSBcFKjmvx6$)Ab)@zC%Jo};GG^`wk62KPO4Uj4VL#>G96KCq=kQC@ewO@G0H0z(PW@zRS0srnng~VRLfZ4r$AM!neyJuXaIOa#xb)s0F=foth+$*thWeZ?HYzP!|yEJqii}CzfaU$?<X3O1E~O2!RB{vGUqUtS2OO{n<*GNQA9Xl(>Ut>g+;V(kF<3VV`;SZeCUB_KKGI$xI@RKQ)%!X?Cz=uoB+;CTB`3J)@IjghRTJkU__KR#4IXFo+OkWMZcsp;X@!a+}fDwAVQK%ycNBvBk25yrjF%B6x*ai`vc*4*61Zr70EY9DiP8Sz83ThErzj>uz6exr=*Q2SIt;P$z0DoHvi8?QOkBM4fR+ftEQkrB|LyrLZbH@g3q{Stk)4H2qdipu+-_wRDudof!KYs+TAKXKpKucJ6wwmM?4Wpq5oH_AN-{WYDBHl0m3xC3)L--AfwzLu0mCKj^7QEWG5K8DKM&@&387Q745Q4%t<1xHU3U2onZ<Ur46%Dp{ygKrw1h2PyTWu^PaXVTR{fpfL_`Nv_QND6nld85|AAnt7ptIzJrRcL&_kCcI4gBbVK|<@UOA)k%55AC3GmbD~v~DJu2xgNwecOQp(Y7G9w&V$AG?najUr_f({pYlmbcuG`&zq3$&ffT>*(gxe!=XwApr}P$MXZccZBSN(iwe5ZVFo2$op_sM`pe1JOe(R~U>Bn+rA=@xwqO*__C^Z*O$pN_8DbXPrNJbbxgm=i?JSjSn^T)01oPZ_l6o{a^q6-~M*>>`%Y?<W-5OfhjvLPk(v)!*}1my_@&jUmmE9O-jxvLOTEY(_h}d|8a9=>prt5=ta(K#@$;IM(E+0dxm89<#{B>$D#kgEMxv+l%zrYztjZo<oGOTa*@8;dh(xt{_ev!fBo_8r=NZnDeS{9x33!iguXey8~o|R+jsBJlPWZ;cfb7IB1XmI_7U-+yLsF_#Za%K>&Qbr!%NuTEeb%cypJ`q&fml%%-7m2cgSLNCU-W-lcU=MNU!wlFP#qT!CMQt)3o02jNKOuPhoMJmb~}!Toxjd(;8oZQZrUOw>C7L*{uzYUw@O0QG{%Bvl}<*_~1s>xXifMjs4K;<wNecUsEH#(hr@E%q?{toF24&i0oDs^+Kg<E8gmTJ}L3v9SKB;)Iqn};OD#(x8YEx$@z=U>V|4u77W<KjPYxq3Te3PxroN^*uMGW*VzPc^uZQZnmE47L*1<0eX*KVzA9kCr869-o2?<jN%nMCfNTlJ<VdacfL?lLMZ0Zo)|szXI?oP&!8pFyPs}`%(yK^HG;@MvWtwIxyJZ25H!!!TKR=*Y0rQh)#tcl8^z@D+3)9lV%bd%Ju`0c2#ZawKnn5?gD7+H&Qao3XRgLM&E<CM~eu;8=(R*YbLBUfl5l8aH8&Pg@>CZ|(n??j<ncuA$4D=Zf1u-{pE5p00gzsXl!_86F0Rn6+oyHPx2;_O@wR*~}I(yQ-kI5LR!NDyVIOs9hEC&y_<i&zbICi0sJHU9CC{Bq$XzFB%>>A-vXL=H96i`3ypfOwA6&<Ob?80fRHmiR9+mKlBs1YN~>Y6Sb^nzp}jvp}QY_4@(pZ@a?b6AaoRQRb8%g%YJ9!<;L#U(CllbWTB?SunqRJ5>!cZ{)JM9#)*o<KWT;B%6kExNTAkI186;m`bDl(^NX1dT@}^I;{miZDlb!;B2zJZzC#JwN~aCrw7i=_6L(V^-tl4lp7(um~EfM3a}WgrDOLt4TrdhTKCxevlS*L8==jUyw3=>u5&THD5zI9&c7`$i9?5e4+klC~Wh&gpSUrJYm^_&l}C?|D5Odgn)l=*@fen&Pg3DxHTzyoDdxBdp_l^6DI&Mpm}x+cgriz2iVJ}l#1jHEctFp7Yah{W)~`TbEo^z8KvVpVI}&EbncOz=+)+}bp!d0NA{^RY*vpzvhVtSaNhMOt!Z!Bmz>W<<&4R_w*`k396@VDaff=Ua*C!s)#H+Mh6@*t^HdG_!b(?lUM+EuugbFYY5AIIhxF(qoEh4+RL3ljtgmn^olUb=)MNGtI6Sdo#<Ou=P|4StJ}(dI!{?duwsZC*=DkvA>8Z|pwMc8z9ZN{uM=^uL$8h+t$k*In^LS7h!ef0&GER??`7L*buAY^pg^-ud<Vr^eF*YK8m`S6CHAQ1H$c8fEn;JEgl|#yg<sfaZRedFXVD<Pz!C=Vuet7%CHw<IGF)=0;3CF-U6N3$<ux5G(I&@R`+e2rK(!#*+jupMYQYST~%)Z{}(AA6ZlYM297p;;am---}&)%<qW+eVUopfD4lAt^k9z@vrK*h^xK18E@9;=iNis#XK>J@JjoL}_nm{?f^=v?e!)a@%(M1d1M6e0n|TtP{~_-w;*SA|nfO+e!s@B7S!i=bCU|Cl%sDcXkV70Fa1s~q3Z^EQB%JYHsl>|n@}J>Vu1YbhqT8PukaoJe72F0+SrFCT3sH5F%o5-;3}MDXZ$Q<Z8W1;7jb@<lm<*eRYWTE`}b5l>L#zbMhv@(HegS_PVySMG=I*PFvI^Z{S;3nC}MH_z+jpVm}}rw1+gO8;##EHu=D*oAM-h#9ZQ;fIsqqb#PQ{*J%CtkpG1vTGw!7p1qlt|(Sxb`V?feotDq7_>zl*41R&n^h7hN&>{81Qdtr8WAXZp+e#)0ZNYjEzK-7#=AouE5DjCioUMXX$noQL~kDs?%CI~Dn8Li7=JZO;oDh;k=a^35NsYmgVtIB&E2NOgBHJ@1`7`wdONd#r5`Rfg3mDyB$by{(0}APIDAuJlYmaS#l}dYRY&gvQ?2<g;I{6|sj?=AA~(R0{HK9#n<VZ3L}(3Oa@2%q_;#s?g{E<tf|&Fg7CWqKCE<FgfdR=lJ}lyzIw^I0#e|X`wQ3yOD_|eX!DbQL+E_i@?z_FkmKtH)c{Pf#j(Lj>x85F}TWR6!%dM_wl7gC0$Qe>*M3t_`5{xFID~v}e_-we$=3QT{-h&zvpSSbYL@(-m3&%A(-@|x?1jF^f>hbC>$vRcXy}HoJsdw)WEr^0%L8;hTLG<nI?Wgx?-R_ZEKHY%z5-Y8~ex#ecJv3QDe*k|y49%7Pa+@NS`RFqVPnposMwhYBsNWul2GWa@4HV<QTKV+feD`hE2zWVXr8p0mhFDe+fm#XD@=(5(7eru-0_<wwbEQ-X*OJ>qFO|8*DbgdaW*zl7ih)jJ`mkl~r{5oNlgWUW!m=r!^eR!$@ua6(!;(84rcvE0y;HXBCZgy~#c2eD6d;Q#srd{(;En=@D9*8Q;{oxV?-h&hZUK=Zx0p_bT|Vh2ZQ}je2ik_W-O3D*-F7qcm&}LIqS#|}o0YbFFd>(1H86&BK~@Yu7Q+m#4=}l0Q9KJ-V4OVH^wl(%%wMi;q_f>b4m&yIAE73KA7UA8=HL)Z^?t4RfnjfEfyn0vWZYe<%P!~Qp0_ijMK3aFl-viK)@S!FYGOOTTkAgm^EJXO*V*{e|ID6vQ^pOfk2FmIVlB`aur<g3+N6`5jThdju(^vjwm6<D5*Nir;@whgtLHZl$2r)SRKQ9$nK1Y;4;jO@3<w8z;M@iHz~nL8VZh;l)1A+PTDTUOK)}*bC?zI(f+D(G$=!AknkhngN<h-cm>3Ff@9-nHpl#y~Vo5{BIwY!kh>XF8K<{V=S0Vlr;W^w#W9<>3M!d9?+zX8cBAR@y6A|bGV+&kz#9|?(>GXd<d~WrM#3AgM?G(3TwlPybxxNmYs%Yv^1@Bdvxz#7RY>6XCF6;t1YNQT1IF`oADzy-0$PuuW3Wo7=7&oC((}<-??B5;1Y^`ZLry0*^TEK6jl28Z*&2>hZG#;r9%jw+i%xAiM2zEcPqfG@D7*^%|5&vjzQBii(84~8%cyL|8WX6~m1C~w=3_q3^k6CL0Gy;mXX4&lf;;`q!K&W5`?o~anh;S4_`y}Xj^)d;PUOlO3=nScYQhuD+<4vd9WJW%iLC}{?krGe^BAVCXFU%YM?E0T05zd<r;FoeF!RAZd#x8-5keLcw(T-6>Upu!l76OFs*ikDxb_%L2ia@hy2Z{P4Ica#3c2m5`zQ}CB&6FfYihLevfSh*pwZA|qVaL~t)<`amrtpJBTamdYAKEc!vVA~zH8d^q3LSn34Flt#a<huII&b`-=!)V}kte>^;^H|-1GmO<+3;`=8yql{j)XatPO#LJn%<_ybg*fcqllW$Pmu-$W7JFdMhQ9MuECGE1;>S!%?vbS`lE5X@5fZwtfK3xp-GGzWlsuYt_10c1T(pu`~~}qfCX$C8~*>H3CYw2Zv=JLBRMC_22o#S-wnR1X9UI4<tQ>32LkNZcXqQ6Eo{F#qvEgf>ou=tWW@^+brD)S9%v)T&hWDF-$O;s`NUGi4V{-cfEN|1Eb$kh?S=3UVbmiiim9O~%3qZ<Df3H>!I4LZnk^L$m-FPca5gw|dKwXXg9F&9MNF(D7aC*`COP8PWaMt2SqKmUd_z&jB0Px2CaPA`oM4yx)6&AT1HCgM3J%!7U@kL*@hMcv1e63l@&bEK1ch(?<K298W`T&dp@)hMpe1na?wl%)7uEOOb^(;Yp&`K4t)X!daH^&+%8!$slNDvAvfS{gyEmZIE20pHL3@{VM1KcC1wwl_MA)$v!|6EO$F4?yu1>8caGm(&1hOMF2DbI#w?+D11XVKvTGv|EyoXe8R2lu{;OYQ*dP#-ZfK{Q$qVX4r&(a_#d`|w_>t-ewkeA8`frxj~OR&6RC{d*Wj%^mA1qT}FY2~^u8|*GF)&m+FD-=~WLU4;oh<03_C-U72(d9vrR%@YzmYhc{q~m&7%9hEHTOerASmlxC*4}B8wFB%2n0bjX)CQdC>8v|mKOT5BYJ~!z)(#L<;BBOs!#7x0JdyfFrfol484&7{M8L)xI~H*PF+$3PxReBGW=)VAL(>ot{?<o^H3Oh}+afN6xhMJk5<NZEw#U>$fwTkAUS`I0G0<v7DuwNe9fTdxH4~t32hIjOg4hC^s;ZC&ZSjoCLe6|m>iLc?DW+%k<|y))@wYi0SJDqBL*g`Bh8OF)0Xe`}sTHhATx23k^n&dx-%Y0F(Uun4`x~UimQW7i7W)15qt{!p^!snW-E$7RxZ+nJ!h6m1(8cKP6Q&!0RH-Ct_G7YsSh&bVklSKv8m*L|C{YVk*f?aU8tUqqS_Mq?MCFc!4V*NHI%JgBfVa4Y<`p@6(kw6pLIfp&#Huz%)<i|-B#4`3{|T{Df&;8Lb}f8IJ+Vv^?=x4V$abn(?#7?xs8JJDQVklLYtsgJ)-iO%Hfzia**Xhk5eMFN!Gv6Fa~vn&gGdAsV+;l1JM3FC^eaaTKS1JM-G%6Lv1|iuq%es`4@6{7rRYgT9E;*&gwY&AWLl8QNds|yfaU`hwNYId#q4Dr7jo^aT3|Z9ujU&+S4rOr3rHd7P8Xt)Zi?Wc-6585iPyEo3}Vo<{DQeH95ik~1AODoCPFO`gu{3LJ-v*9MAfhFz$NI?*NrYEEhI_p4DbWeqOZ=b$-c{+#2VJ&ggo!^rFYY`HLxu=@j8eff+-?7`HrD@g;|FeUnuJUq4o<CjmKPRmo9jLsf_#$QXz3=iq(gHrmrYDVZ2B-1OFX~M4hW3fn;!Y0^DUaxWHAg2H9Xs!|MVi)I>3e9w-12Vi1)UQXH$0s2KrG#RAPSOyV4h3xH9i0#x6>RyRBmd?MdIMBQ1G9E>pXhBvQoazlVJ@yk7{s7#?wFkptf)CM9hBJxt6#l2wO3rYnVg30kk8d&PaX^E-wJt+c%Wsz=_yX4y^T+ON7cFJ|@v{!(vRo*rvC0f%RIDf|5+I&T8E}RfJPCJT)5v`4riS7Y5Z<WvYiz}ef%gobV^Ub^rb(qq0%4~7bO<+y_8P$>SY$G)KXk~V`fHNp#nm~Tu@aE~2Lm*?UB6t2KAwv?uQ^H3u4fZb4+PQd<^+OO}>hH>Z$r+86@`oM8u)(@ny{@2&NOCKlaJqV<Q4CQP$$%>%JlI+||CvQxhy;oiWCGIaqV}>ovp{lIj^koFB(&ETm04tMVt-SrMF#(7N7>6=71eA^+2zX0G3ZlQUd=#OtHhkyUJ?Icx>Be-@4^usDu<?+IPtq+dg?Ov3k$Nvr7W@(;5D8xRe%uT_IxPe$OD4~u_~tCTv=)=PD5%>(U;7bgP!~=hVx)_*Uns$OQV%wFTAz`3M@)^<QWGP9zz?|QXSA=u3#vkh`hFfk~Q092W7u$&68}!&lwb5pvl&)1NCt~Z(YmSU$z*XiyTZANMB;(1)7;}ho1VZruWMS+nRkqoK%ik;8s>s8%2@>aHG)Pa{2C}f(W+DZk1v8z}$u4Um8M*EpC1_g5m40G?I-H6ejOT1s@OrJNoeZuI|{6tWP2AJjf6_f{axk_BPlN7%gv7&g!frYwpDyd$#804Htln)%kzA{r>Gww`ukD*IyiYGgSp+vJBx1%+dt$2Um{lf1+K7Jcgn*4o>hn)qhCJCGe*)i7*CFXg&!|An(deW9py^o3LC8>m-IWx|(Ubf}tUTFQIC|C$*rn4ckZsH{j1;xBp?6^Y&q4q>RVmp)^YGudq#)988@lL}&Rfscn-`0V93vB-Yc-KH;H!H)kW)kKnC#{Hj@10n9KmzOWmnNK1n|hDu=)L)2qrF=Wh_I7@<;aKU}8>i{_I<}VOR-DA!u{~*%om(3_4Ie5%E7XnU~5}}$K9slQ{g9X%#*wf^!OIxk43l<GgAuG;#5nV%5=ZCCGawY0uwblf!44Ny(l25UAWGw>~jFBzD+8p2kRbe`9bdV<MQ&^=NtVD~)(KWn$5jdO87dsfU{pG2A!%YUH-#ijhK0dhu1-#~Ouj7h`yEy=A3izLMG`PZJCFk%|9=facuIEWu-eV0A#zYIhh(8TWcfE8%ZcJD3S8|E@YxPjheKa%Rk;xVVs0+R-tP^?=HLpN`{wo!6b`N!US~1QDzsPWogwA8Q|H}w(o~O%(UE3yvdm&C=6#UW_Z365?W$}A98)VhnX1U>L%k>Hd1Ky~05H!ZRiSV2zD#x3KS4Po^H@*NI_^D}PgnpS^v8Ma&F*1&UJ3Av=s5JR7vmMZU5%Zpss)PhDI1J#ACzFlY^ryeDxfh;IEc`x*P}O4f%i79KC`3`oU?3~(X1^dOk)PrbJ=wh!J6TPKU@p%X@($;fWq~peB1zHE3MNR0kHrn(?g^G@K6kx(#qLH9$#wv_v*AF3gx^QLS%ZO|ji)IcGd8yS&G?gaLP`z1tnTn!5eq<jMb#BgsgT)17Zr}hrfCkSw7F$f?l=FPvgCme$ZBnlS9WX@9I|SgPmh%;7t!>^2)RPR&lE{XoSW{sM#RlgKg`go=_SOyG`<FC|7zC{*2v}faGPXlrjMXTlmNU0{yz26x#}0;cINw|(_CJ<2nH!NM8WkHVJGp>k*9~MHF{a-OH8B_^3vQxW01%Wf+(dddfv=U9%Md283Y*1F;3p?u8I`eRBp{qRSgvGL-PtK2gPLL9MpH%(m{tY1<a$uKlSOt_;RrS*?A9XL<7mGHs$wvL0`aTx@1m8?7;jGMh{Ku8Mt-EIX6izxn0@Wc9Fl4X)kfd8gJdpn42I1CHNLzub2ZY^z+)iAT>b6<Nb77o<&Z(s|^cc{cv}|^-X@^e0EhqQZ(@DX%-EvMB)0G^bkp19rEQwFq`Yj{F-lBu(h6b@AJ0NNg%cUSlU?c5REv|FYV_B`<otMM34~i6i@n{@7xa5WRxP4s^%kTL}AX(NJZ4!DApziwx5cfuTXq`qjRWI9-eNAemGF`$d%I7rcci>Iq*-xSJj+FRuzKnO?i&<?vq?^je-x1Z_67vuS)c9!k8Qr7J&lzL4YnMtDcs#N)1m8B(6YR1pBafvRU)9g2LFkrU^yVI7&fqM&!h3-EOaNiXgN2cHvl0<lv?Io{e*pL7q4Qn8hHaI15xS3CU%P!9KXn0tmC%5PT)y?1dW(OxyudU<s?NYy*;)-pvHw=dN!r+(Qug4)Sg>aCX<<j<Fbnh`Tz0<%)2d;c)J!t5k$*)O_P{#I6gVk)m>{v#{KR#xtI7^cJK%Y7`0nrfUMXP=03(5Os7gO`F9=V<7-LDImTQAwRH~==6|SjUz2FVIu_Ltf(kRaJB0JkD>UXHx-YKcC8(`xW|DyEC5}c|3>Tfc4AqADJ`@gZjX$z;OxD@mT8c8saq2kmM_%B4mQ|bI<{<a8D{J^3BZsoq{4XM<TVn@XOme#z6D52s+%z<8=bsNc*!=rCf2Q|iW0a9Mmf#EZ|C0lrSLiF21mMpjcF@^1BIH9yIJ5-Er1G~w3wMo^t)hk$-p&p>A|+3c0n}Xh!#-N$5=3=K!Wqd6Kl8QqJ*l6v5bgF3yNjgBTW@6wv#+<*+jTSlMzt`)mhyRA(k)9y$Zk;^|?NsaFj$BMDw#m>iZk#KoPPX1b?`CaPv(lb`_!a*H1IFEUSzSU4vqC`#w597=1sw+?&mV-U(~ahK!M(2wg?@q$^Y@{vLsOQo&K5!3D3{uPn{aYKhX#n4Nd`u5@;43EN4s&7QeU1e3s9p%vgL3o;*G^sEdQJwg)Q_j4Q;P6Ld1P_<w20h+2O=!7_YtXwZdB_PbRNG#hZcnCsf(f#V?$uaLfHUO*yI;YKG7}^1%A_f_H9A}L+l6^xL4+HfV-D9FVYPLK9?sARmDhlFwUy)PU=&-h%E#&q42V_ARe!H-ad$>}YS=3!!$c`2*%fRsL_JNQzYFtuDu@bvZmMefUI00ZMY5>?LT7EBCHdNqZjtGkB#=#l5|1yk?Rk+aR0aI|3aT^%?-qQ1Cfq-x@dXW2Q&fsLaYAvj=GPyO>7TZDMb5iOyGQEvxV|n%~UfMfTZ(sRWzE_d;@qije$@)pL*9Uxg!&sV9gq;9^97;zYI=^Tx-(r15_ZzL~MtZ+Iib@;R$<d3+crtWO&}bor6jY9O!>=Mvm)tQkUFaOfaIi|D7)Z8GZ+KWv=^WDhC3WkPbQ2ZRO9K#1SPnc9=Sb~PT99hl+FFExf$cxZ2Agrj1UpezJI=b{@aK`>O!<Lbe>r^>VJK;oP34V_?zqEN28qW3F_-`_GwiGbjaA#)k@v^>OMhi)JVtCc<19P@a|ue*dd2j8@dLTCyfYk$U6@(Es9c_E1dyR3*`K+QNv(=r$9#4q&6#OC<^=Z)07Ht|N(aZA<!st5rA#aV_Ds2cCzxmf&*QFu0@CMuhzZIkZ2{&9557p$&0l?ScRh7-e|hC;{$;>Z5Oa3)-hJ?TMbP2FRj_Hj9UkT(`gRFGUsh(>hJc_me&TP#xuIEoHcW*fOaf**(FJgxz{$m`ahVv*QUIXGIj<p76Px%8b}<!FN33)jI588Qx^L<hVH(1cDmkXx9Oj%V0xICXdu=w!amv&TR1m7dfk0I`CngoRmW7_-5=RlPVI9w=zFSMu&rxS#?23Tg;tc%g4vn*`U1iaV<1%p+`pQ8BP{VX64@8~OvyMq&(7Z%yv)R6kbHS6GoqbF_y)K=LjwOq^`?4b81T^D-_O8Xsz>uQ#sLxedNEmG_xA5o=)M~z9dl7O=XQAuXgUl|F`%BNT0o7*JenVkboX`W-K4_zT(c?w?9_|v43C+;PN6;SP!rL!GXm5APcFZI+;`;FePi=89dnyc=4f4m~t~IP^ai@F0ewz*UqieXsM8C$8coNQk-H^tAzDm}sRP!%zq<{EHg_P-*%+4R2EBAYv{`~2AS6@{lC-1F_0)}?~i18Jp$Uuh25rGl0>Z!0qH$rw4P?6WNNb1Ds#b;`nrU+<pth_&yVHXJ*rF)CKB0!jc27CNMBB*q*1q$WiAhisI65Z%@@hgWvqWn}s#d-Rrf}WNkvCRF&z0f-0DdW&}Dp(Sx@eP1iIX^IqJE~k`$5s*oW6E4eYO@WMA=e^UMbC6BvWnz#(-Es}oO85g#L6dGzZ@yHw2OvdrMG1p0}Em+ZHlwOlx>62EX8X**#<Gl)}3vppiUype4Os&h*TR3WWbLwos?mX=~gz$oocm~nv2YQgbrTP-<BanU|aBatXP8=%xl_5Y<`mNvHuznB=UY{QAVI>CTG-jy7zpB$Z8f^?3PHtPg|tU$+AFBVEKv{P<R-jsM@(<;|sDrZk~7rg&sS^^Fa2c6A5%Ll1C;x!mmubs-0)C^*EfAmvu;p9r;0$D@J8C)_R&_k?L~I2Kz1ZLmukyYa7TV1Tu<2Q^ujRbfT@aV1zENS>_|k_d5V^p~CQ}%^8)X!T4lZeq;>z@xUceN!!%gNfhhGz3B&ZC=m!E^>2(fq0vy2F*)pN0)R(RmtHl)<Mv!;>A9NXvQ0$Ov7oj%AD@_yjc_%;>mftX^*bm9E>t7!F<3Q|ps5CG@dLxnm`k)HD&nq#iGi{Y&mT>vuaPD#{RDmmI^t+;1l8sO3`SY7N*F3O3b>6KBui^Vc>)u(TP|csI3M(NRZk4pH8_ZED=kuC<TMVFk_$R7<<`Ls*OHRZlF-A@FjdAY(21+BEEN!FA7KJ$?O#=dLzY}*x|e7uPBRPXNR+RUEDUFRVui<Ghp)N5CB1F%^&cP)$!{+MRVMGiZ;U7kRNS8*_aKLkIM*<l8qJc*Llo6~Tz-X8Cm<ZaibJz3fcRk~4yO46tJ#3nAX6n|v}-t-`lotic(Nl6_Cu>k*fiw<wp5HWy3fr>F(-|5PxFkMdff#8pjXllw5cGz-$_2mF9PeETP5BKeQf(K7sH{pIz%;2bVw1|K>!|0tr2w`3yK_DGhe1^@|8|4QwSZbN&@5-SZ#bVkClZZ4DAx7t-(Ndi`-WH7-@ds^vUOUs_YIr2ADSjx3q%2(f4URSeyYoLU_g6yBN1Lu?zU!fxE#5GPA27Ssp0(Res%2+My{~Cvh*5@6c6G{_%fC@^I#<7*2ucJnXNnlcr~3mfz4|$~_Yi6X_MUGI1*9D>(N9CMOavz*IqHq(By6iye%Bc4jAvd5G4()^!zO3#?o(u&WaK>Egy@WRu-H8Xsir7>e&08DqI8PRTXG?%5WaE1;T|TT69Y^Xpmp(|Itq`EDo1L}k38lC+<T3p|n?bd*llW*%H6Vav;COJq#pCy{aNJf)(^8dg=0d2*a(i$Uu#el3p7$m1&VF)5#C0ps~r^IRqb2OhP-t@J73xzF_gkSi6gj!MKUIEDMs%jhn~i0F{6v^1@E@dCtx@-nG9`m<BU3$Pjl!&-7D&WuO`u>=p2*{kXLpbKSWOImb@%LHZmz%_}8i8;Fz`}Qv<6RNPW2P7#fy$cxP=B04DbcsP%5%RYtm*e(i%`<Rc7A=!1sblIb6EdeHydtXvx8jTf;g?AYjkD8H={*ZjU)@#fF!6EJR9uAsx3S=Kp&KHQp(4BJs72<>85D=SI-6d6g~II+^;=FuE^Vsy$5?m8Nw~lyPf?f>VS>U~l$wS4!0?S+yySs|MFsTQOJmL55w36a5SR^wCL71V`7k`ER$1Ga2g~3(1XHP{ibSSET~gCk&1#WoZp#p!)NWe?+~y9(Qej(3WZ+2taC$lE3>djgT&O(rO&=1{!i0?7DQK_3|Eo2aYyVl}9-+NdJ}x|PGYfHblckPaG}g~hM88y7dJd8R&NxBFDp`$=X3ZhjI0DOF{5LR)BIz~EO`vaV7IOmtjW+z3GP=o_lvbJt#rootMZ`$h-A2uhRn{!GpnM~2`E2qtBNJV!I2YH!wof-Xl4YRHod44d&My;<*8G#%O!AE|`l(h&pidfN_JIGaCB|e8rtS(Qy=r4#-A7W!#BVdts%Nb>C;)V0&{l+WkFd9JI?Kf%`W5c4tmr)YnS`V$YuRfuPlcQLoow`jLD3AeNBCf%=ba`bE1(STMm`BhzB*RnG5MiHc08GO{`UOY-~aXB|Lt$r&;InQPi>SCJ-p8P<>@bPfB5eEw|7&2`%A26^!@t}w?90X$nMvl{__6)j}LoOtdbol*|Uh`?k!0jp@(PgRVTYI&m%cL4*dsa5Ty&QNj2rrApT!^5D%n>&k+pXlmGnlcOSm_>yK|g{q(cA^kVqs_EqDb&^PCIgFk(E`|kaDQbj7l-7kN)h_Uj;_7U-+yLsF_#i&&gFP)Bs_BK(FT`{}TUD2`r-TASX@|?lJ@Ev>*2r1;cfwP<3+Cbww@_+^YMm%%%gX5vV9vqah_d8?v1;bMqn_oNE!gHDER8A`kK#?(OJhwJ9o!PAo&CH#p03k1$-MC3-(W<65bkx|Bc+!#~FGR-<@)O(A?IWTy71zP(LEDF*8i<JtQk!K~lfOGKD#ZMtTODpn>Ylg_hcanW$ouG?)#HpCl@zjJy23DH{5l&{0J`fgJE)LT?%2Nh<JZ{)aP+|zR?NlJyK%`w-K^Y`Qz>2GlCKKlBhnd;)6Lcpp>|5}i>!%wOpZxyJ)ox*9gdUFHtWn+E1hSDzhE3+>?dZPN$FK63C?hW$Zd7{mC*p0kM7i$^10uo^HaO~ZfeX}uHuq0EBStDZL?+0<-}N(UbJGURtS-xn-G<%WbdT)xA|Z7Axc#`xhSRf66N%^(xM8Ua)~&SFWxA>$C^>#kev0ifl~|W3qUg%=rbOuV{YJ1K&XAzjZ!>Z+p#&yIzWJprPEmA4P9CWsy2*&EVt_HN&7w~W26QLw`Aa;$6&J@JltNSkaeLDi)6e@l<h<yG<C8>c8zeTGd&4qEvTP%(3mam3iE20bm25sn^nL5Z74bQs1YN~>Y6Sb^nzp}jvp}QY_4@(pZ@a?b6AaoRQRb8%g%YJ9!<;L#U(CllbWTB?SunqRC$e3F0f57#&!`odv;<NIm-f{ljLmCt-W|e9{mb`=J%q+twwQSJSv$FE2&k4Il>!eWB})3i`42RE&KE*O-9D)BUayIR^#RlFd{gx2pX$Ilb5iBpW_XyNkQ<2+(SQpkQQ}8sv9O>kTQMiXhzpHUqd<`Z&qx`zLY+Eq5kK~-=2uj(HWH|EL-q-qZ$35^ZcF=@DDD#a2(S)siOtACPj}Ef`fg}r`&bo1Rw@9DEmyeyyAR-y?jckNZwE=pxx_2L8#sALZztBbRRmSbbKc?eG2H@BRk>br_FW)`He^RsWWU=k3><YHT~ec>rq<M-m)(_pY<NV-TNF@Z5Iwnj-WN7xI;ZvUGrkrQ#~$8XSmJdI8W7(FRXM`=hYGi`Kqi0J1w_9?T{Xwgfm0ClHj)ISDK@0IF`<)2`VZacmy1t*f8VSI4`K=YfYb*2le6eOnKWmdlK_rsq^zx=e=5frs<9)B<`b_!Qo>#d|2dbUKLB{6{_kzjxR~Z=`k|D<<8L6v$C`h^3s`H>F6Mm8-NBUvgeY*GM2F!WJ8(oO}8&^I;3n^4$}5AACfeO+{pCH?d=CqTJv}4_~Gpj-!P2%#;ig?MZ!#a8Drr?4d$8Nfezgi{^lpi0lzzzk_LYx)i=$)-ssTP{`R3*ndC*Qq{yW{2<VshE1(&P|4%1f*N-G94}}L2c0OqBHu#{K0&(DNpfDXzni&6U?Es@?En{gBTIdtCShlHD1_jRUP<@0q@$|>|Y;BFISjwpdu`I)2WbroH<cCN+l)SCyLZGshF|i^=<-5OKoR69V&(aivuIfT5kxGtH)TNz#TC$Y%ADKV99jZ_th8#w;fNij<O+s9rBDaXI0JDIs7#Uv5bxrE{`CgS*uv1udRxMw^zXjNwW<SniU0&>#{%koYUR$_5bFbbUhLI2WlBaD>f@{|W@v=HQjtYA6SkPhnRXk&dKTSq`hEfl^=*$rQiGQ062xU<k^>=kC^qRESwK1lPc3a(>#ashdfitC*a%-ltQ@ol^Tg&MMfR&cc&hokHfjr{N0KzOUGvmsvy}`1W-QIC*9D|dTGe3L7rn~m#gxop4=glce)v%8<BRX+)^7Y`k42e96IXQk*=%gG!Ea3yfKu7i6o+g^Ee^67<(r^x(wP9dpCyzS^^1mJ#dSCeN|3Ye?vjFxCQj4qOQIXpD^^cF#&aZyTK<(1VB{&V<_0a@p_&%EG;@1&b5nLh+b}5>uWQuud>@FN@o)Gp2D_wq!4Ssuj`{})3N9Zy8P>5KaH_B~y^0*j2^k>rIVoN|az6$Q8-g|e`1*8J<cS-S#PGLdtes&`h^U0@bK_W*Mep=jr(6!iY50gywAIv_hNs!_BTA<9mVQp3ao${kJE=On#e{Vt&!<fvJUcFfG!keaeALD*^dpd;e(qFx%fMPJ)xanQc`hKhSdcABwfX``Zu$JI36jwi}>l}#fE<?N8-r>A;U|w*oQ6?;Va2;Mese7FTB)q1O@J@XN>beX+dr_&zBlqzbv^u{y76gTPCk+n}4pszKAgVP~BgZ%|x@k2~rGi!<M*+v+O28U|BaWWCQ8%drQJ9C;6lHGk_JF9lo2>XM6&DQ$K?&LyOaV;)*uat%atRAQ;K!YR?F<`g=&UMLX-kST?fF^-e-7D~Tr^R3*5Hn*vk?9F^H?-qg_2c~C`<+8J2W+O62+aoo!UbTpG5T&x>~B!NeYUg@N6PP3Pv=F1TQ^H6H_P06<~<N`WHQ~t-+9bi(Sb8yV^FyQZ8dH(@|!-EthEL#lzGd97Czzh(%1v%5q}d3N!|AlkV5sukI2j?m<k<dPv>f7XxZJ-SYbqXNSBgB$PY=piRz(v15c$WnQyV*U`ib>LFC!VAgK%RWZoHJ5B-!1v&x^B#+CpK6eK<woo~e_^?*)AIqcg3nh>Xr82UM24lAV<SwCM`-EPF-V@bvx`(+$1Q6Of3EaaH?lDn<xKvt~9XIFLJk$;}@SgNt^A`%WjQ4wCM`$b(0y2=!6eeh<3VM##a23K^KKuZMK@wFH*cb^H3c5w|Khusx#EfhX?XNt35|?aRf|xZptiuSiL3>HXl_Xs+9EjVV7R(!-eWwY3a2>Wbu=y&Y9F~HU@Fdy(QP?%q3gu@E|0~P8B4(^lX=Vd7x}<jJLpHg5f}uSO8yXJ{#|Moe9p4lv|G=<o+^(1fdmEl_AFNtDPlDqHoj_uzNpahX1A;Q-YpH`yv`#h^yYFc(qS%4ZR?K2q^ZOHl`AD@!BmPHS|9yEwwm2ys2ItAr=52>CTZN3{n4922NHQyfaEJSGSnF$n|HsM}`>)@<{rK_r6zK!3z||q4%PzAcFw6}NX5Mujewk(s=KlqTK*@7TyE_Ua1?V0B1pM0vQ)oyG!~PzHqp>M51X{@SmML>y;m3;fw36=aBP4W0BtKQE%rU~#G$Tsp5F2agf5FpOXc7eVR%cp<SAnv@hOJDMWK|Dmevz_~!V+UPQiwLPNY=xFvK!};0RjIsVsA?K3{>BQ?a;z7XnDb+CKqC_E2QJGWw5NkY{(4+v;e&qMo0@0Te+uzn+5=6VFW@v5JxU*g@!#^C5Ky~G|a}`J-@o>;nG4$U_{W}w`KpegEi%u-B1;7WMSvg+xnV7hZXE+vp}YFjQ}C!V-0>^dMy)f){Fj4^}8Y7?7UL0*DY{5al<)idPRboUoWa8I-%qAaFQP!QL(W`DqjdUS<kpxq=1SWycvk(ew=p_up}5x*%K*&<12XzCUD?@7HqDNUyv|ol^+AmX_xSaG`Gw_h@-u4-}V$4;89mUC;9lUV0Lu+x~Ve$2_5~N<i9w!>}79liIDB&NF+qJzHWe^fR(a_`<HG|sSJ^~nf|xs_>s627HI%uk(NHCVNs!H)HGlvoi$EfZ>3==tX>hmAVG_4P?TR#Tr+Af&ej42DozREiX7FGGo>|Ydy9njkUB9PgG8N$r{8`WAX-yK8NFL<`-QqtApF<6bwMu#7W)H&_u_JJqGV>cZUQAjzxG}-dKc@l!cMykx%c0GJN)0X2B(9w-aM(uk_<5o1=v-b35bQAq&WzsZfd`rD_24SO{A>kuzcz|chIIZh6Ib3fMlm3DW;j+h2CEB+5K>pp@59rejy0eanF{Drd^>i%AU(O=Lye5WR#JJXYODYCl6jKf{!f~)nozTj<26FiRw`G?LDi0G!2V#;@_!9WM8rEB#S@+A7DuuMUa{;1KtIoX21}Rv~w3nXG(dtg~O0z!&r=UmMuRUSffGg<hA*}vtQ<^vE;UJLB)WgsgMNH!a^&;Z)!I76-uSqLLO8!4bW;y&QGOb>Qx7DS5_dYUl7MR-lV#LaygwA);0i&-ZnwU9gFM(ICC1E;8FVPY5W+o5O-ev%?KA?ZoW844PSjJ0XA25n50hi#e_q;pM?jLcw03H#}q;=fjdQAJe1-^+?Ys+`YE&)#^Byh$b_g8sGx?3fMZ=K1t{(kx!*Ek7^GtPaVIcgF!&JAZ9jHdkEL8D%<{IDBq>Sq1^OF)N!RGwY&ZfiDT;OG4oEX>Y1R`m9O71r_I!}u3lRX1rzKQI*29Q*>dZ=81`XgQ#QK{Vch{4WW{`#lcYljw;`Y81UxQA!^SE8^f?>OLBgZ6gvTOl@h7}IFvlj*u<(pemVQ&CtuH<vNZ4xDux|_&hxj6Hu@gdchAL<#tPG&YZR33{)gH)`gbM%noy(fy#f}Av&uM&m;Z7#F`Ou~$s65dR`J}Ye-!h12oy=}N~6KlkYYcHQvoy^IQAg`l&m854e?6yaS+jqU3iyYQLAzH44>5E4;QzEt%`4so?%g3ymogF`iBEg7^754EVD%eaSP>9THAr9zz8}iHsx_BidlxYpkAZ0^xtO<6gB2|x_Q=o;$dAUgi!4FZFQ^$%${n{F2XzYo2S1Hb50BY>gw73?2>c##lIjey41}h#oFUfF%U4M~u(iB9YXsWbbn%D;JC5S=(TnbaB!~{wJBeET999u|5FwJRUcQyF-3wG}bnJciAlmavw=Ox^+Fdu*ec-P@^E3M3+nV|?8S%t8DC3<GFd!zv~-_V9D^Q=1}C^jH_Ne{%0Jp_eoW98tZTFiJNK5c=!EtJcsgO>r~eYFhHJ%PxcpG=n{u^iVK5>J^&*C<c|;pB@YdGL%JWoR$em)0wjSe__wJ0s?E^U#`DFq7G<pphT3K;ky#3{mP0u(}aju$XVxFJcUX$YwBx1F+Qf^Un7zV4PBDP2*3e@DGb6QR==ZZC;hU1hx#VR{~D_G&up19P_}rTEGAqYx9Fcmf=_<k(Cj2U|gF}w-rWJVaN=Lb(3*ve36A5F%c!#DV)kAB@5IhO4oE;KXV5Fbkm7sk%TVGL4GdL#g-0uCM2wkC;x&}cSN3vZ9p{LA`<n!5e59&roqS$WD0-<Se2j1?xF*gvt#Hqn)@EEY(rGkt>lv(oyY8o58Pg*IhOeB+U<uj1MGg(f}DO%t~mcaoLi2@>Z7a>{M<#=ceh{A>jOhr^a~GyW=)9pmI`3~Xk>z5OTc;m;30jpQr?DMkw?1kZ}o(6c3dDYTv}@>m#S4-C!0alocN45sws@<Piuy<a;Hs~6}t6){$F%~NH%EKRqRHseENly+U^f0WG}V{B*vP&u#@)A=ukrMxgc5O`Yc0NM+K8CtqrvS{WXC#i*0Y~S8k^?BKOVu#(~bcAcU6;wtqJWKG)Qdo{6D(YMNaoh~=4BLC(n+<gBh#Q9S<Jd1~$KZU$Io3a(fhj2<TtiM%{I>XIXcmdGyZ5y7_16@ng}+A9w=wN^@jMLNy^X2LiNSm&lLdph*$*&>gNFB&A|ZODRu%?wUS_e~od7so74_T14A0n=VJuBv#MTr%<EO9#Qtj8LPn&whW~QFd)0ZODzC+u^NyD;TTp2(3)C8**3td^#^7$tp(F@iYt`cywMP8HsiS`nXaPA$;n*8=Y8%v@R!Dr_N!1RHEeITFihcF1ap3?)?NwNRC02XJ9gTi~s2guvsD!Y#@dzV0FTvi*64!{u<>$DxX{~3jglgp@k9=l+zwS+|Ip@WOGA7A%bmV7QQTD{45cJ$We=2pP*k#m{={@u~Q4!KpxBoYn72qO=S*TV}ryJ-F1=XrA#tven=J`T9JjI2`DAk2&ph)7+(Q|fidzDU77BW6xKjNekh(rh%POxI#U86oe7MBL>M+Swt$zg&%oXs!^NkqUo6K&m8%<gdS-mH5<y=+Soi#zB|k%Lpw~txh%}o0&B-Qd!{dg)`E!Y&>k!z&{x3>JfUmCNpMqgztU$cMvUDS5BHAXYx-S+0brws8?lVN_@vk`<Fns6*tbx-Ya+XVhYp1auxJMcn=c<!ZbAcl|Gs>*~Qgj5YHdCj$)5K;(7d!V}wJ_R;X4V)Wm}nfAmuTf}t%TFL^no(uuy$;8)i|e7X{$>5;<svI+feD;v*XLi1ci9BBujPyxKGsd+z^WNWo%tHfWo+J;v7+LVm#(uueg!<_K>MoE$4Oos%Bm!ONK^fxo(=G)Q(KQP+AqhVc4|DL#UK-$-N2vLXyZY7C0c`bha`uKffEk@l#C()3}pDy;HI?ln>;j0Z<t}tA5wuW95z^Xt2vyXJ8CkXnlf?>jk|OPgH|w=7(mKXXht_*{ed4873wrT*O8{^1z2!z8cnR-$T)DU^<-*U|1vuLbD<e?Gq0gV0UAJ1MAe)wP{Z^CqA|X*i$62GNE1eUnIl}6a%==70qklkbsHSatGG@dZqSacL`G<M<U$<1Q^?)9`9s&_-|icB7!T%NN#Hi=C>*{!K?Xpy{a}qNwZ;GXXPaJQ%OGZ1}K$v?d%V}7=TH>JQaWHvh>smvf6i(chS|Sp$K|G20W`1K$A)7A3b3>bV9IiqXr&hX#an4U$mJ?z3+@)3?ecWQu0{PMTn#dh6yrGLYZ$KP3%dz6M-kYYb;tf<vNQ+oU9d7(jkCHMv8G}Z6V!Op$LYkK(HV7TIN<XEBNTh4_(#^Mvf3o%@-_$q7H~S$RbMxD{Dv>t%qUM{t3{51NOKSAS*L)r^yaxfb?|@#RtzUvPThM4Pd8DjmK~a7;Y!FhgdqGeHu#L{BTj2U1ADgS$}2tm%gavbt;v`Mj4uG`bJ?Gv+WxiliXKMOFGy7%xBCM%H@Tn8<Z>HPlbezh-$NesgVU@O|PdAZniZHPK?s-yHMx-KFQ<SC<|y%5{Z=K^#WqyNNtYvIu>8wT)ZJnp=$3ZowzmQc;g2^{F`@XgSL6}08xlE9EX~Mq%)u~%t8+~;_FeF#mpg$BsKt{ooRfhSxzw7*Qt;K<B^(20ewfGQaj*m#XZKAXn?a5y`oPBo;3zP=<uh*i%#@{Ael)x)C%T+j_PK(6V%KcZzQ!d89^E!TOi)IgXd@zm0+f}+<^u7iksS<3|vQ!sInTtlin$k7zJc5co4D)uCfb85}NZ|^DH2GxNwY}(t~>yR@UAWLhcphC(9$MRV5Xo4DK0Yb{3*6q@98-;ZnK5D}!9pZB@u!lKt>di*1WXTIKOrd^kH}IfDt@Gq8K>lP{PQO|U7cnDp5`sRAKsF2pko4#nw<wn<P-0Cs2s+tsP2{!Uiw`5jHKyqE7{`5!4)v9y@P-4z1)EJo_#L@}_-2d-MOhc}0a91b8QoIw7KC_54INBqhVjfeSUNWx~EpVQ+e;&#kyF~uD+E&5O=BxtrOcy*=tRs={^rNEk#5QjA;vfvY?CT~cdvHDtraOOZtMZtI8$=Vs31<VZ>(&99P>Y)=^_YW3?T{0rWh=$g+D`Zztes?|{)R$UOAVCJ%K?t!h6@?au$;ar43^UL3F|54PN(Pk*(QSy#v-oyV1p<a8R0YZQ2DQ<1N=$C5QU~U#kI>>5;*4p|C|kb9^t+6M<aTH8B4G)l(O4qSPHKg81Yazg&J00gQkAgKJ@-eTl{O|WWt}oLJY^!65;PO6e8OabKvi%Qo1{AoQ0tu&oZ;Dj^5)s94UsYoPO@asHq?<X&Yp-z(0OnLt1zX2sEZq@Qh|Re<VY;lHM|N;!ZoNfl4upOA|-VV!{+OEZ$Ey#JptXPr)}uvN-%n$bI-zpB9;j&;cy1PO-$7hagU{ec^*+rxRW}YP|&8?SG-{aB2UC3@(Dw)j^^m-#4MEa01pImGnLU#ydbo1WExVGUdw+ClJs1!S|(q>1KMtwa-R#uvu!@6<dltqT^6~g6*dgbPEDW7eJdhPfqMU<HwZ%xGMuMe!@#$}O7xDY`FkJwbb5Vg#%XmvoZse-H<#+efb^yvV3)D!puq!fW~iVX8Kz|hOPBh(&1QkUkkC$oa?n!=B_58yPFfdZp*U-xNqZt&lZgoob7DnWJ*|jqZ`d@Vb`}B!auQ*Pg}xn_{mQ@qm((e@4fEAwy1ztP!3BlKgjjXVoP;cA$oya+a(GEP(HFOzG%F@?fDJnRd3T~ci0udQ>3^98<oCFHn-P#!FZkv5_QO8SAb{^sXVOa>IHE$qXNuzU`jmcDy$H;UwFgwp9-ezf`oACFC)EYEBhXawPs#bc^fZ**^%$+Qs{OOz0~Jk7HBDs2W{LiymLsEXmZl&;#G^(0^#YXhK?lVEpc)vtW;1b4#(+jM2qDldpcIn()Fqc!qd5Fh9Deypq8p^b2oFsqR>5vL#kD*WSmg^0E5Hlb2GodyTU*<*Y>{;p`Q3iHP0?mVt_BkW;kg1)r0`8={Wdb~1T3VRO(ijg@zBwV;s<gfgF_Y7$gD3?wTF-oa<$S7_0IY{1577wtmDbm|H)u&%yk~ZF}5&&$-=dzJA_KJpOHe{x;disgh1OkrEFEaxwG|v#&K~)lwhDxeyFh7(xioCiJht}RAdB$vm;eV9ZH=(@!C%L52Y5BT^vwcG4{J@7Rx`3t$s{W<pJzoLE%H55pgwMym3PI*NLRz>PyL$m`Iv1(i=Q#gnyZ{G4kp8D>pmV9JljwS;hs}bfd>a3Pn|~3VCJZT@;cml&_5{TR3I-3X);afrKtXx7=fvfyR9FpiJdru;5*y*|ly=;T@Pr7${2efXAa$+A4%&<WnOx3zj{z%TX%X%0!M@ux>0i;38pGrq#UCVEn2VPQszJSceuh#mF#Lo6me?(Jg@}rSgnR03sR~aP6iZ+1wLBRNQRv{7t0LIT=OJe#M%^M9*N59d;0JCG4n+r##x(*t2-IyOC8)FC-@_;CGc=u~4d(N6>ltOmf60b$;2RL`Q9#INLvpCx*>%#kDP5rZMs7v#Sxf@RtT#pf7uIzza4_S_62ESVJ?eLa1%%88jL+uv!@W7qyUU3S=woA<q&a6hI?6H*=y&?FUVA1TF0<653@lnpkU)^Wg|-%Z_u|-FkXQ&uj%Nr>h{gEX;{Gc_oOL>pz^%rNqEo&oD5{xEa8nEMsZ%21|B`^=}nR!-^WEDK=aHM6ZWkapNnMUy9(Zyf%%gg-U~7ZKb@oo-}WDi&b_3WBVd0RlZSevZa+o1?IRq(Z)(YB%ddR+PaSo=om|H^{PwST4lgUapUqK&0Jkf(6CamwYvTy!=dZyds=&c(h57N0X|?REuOMdQ1`=7rr<jZsbfs4Mza|ZBN!$GZI4(JZ<WR%)LFCvYv#EOD!JxEpb{D5SH{A&aL{90LV<6S0h3(J3ahIBMNT06bHkZvl&NGEydhD>(hQY`X5paXh9jdS-pNmRWYrOMDAtTf1W%|Lfv@6yxbYjC<In=EH^$WxCjcF;2MuBr5~cwGh{%Bf<0VB+!M!=7;{$ts$!c*xPtjgEUlu#zGgv|Pq-PgUBio4$_<2YWDv)-9zEgcFeW(VmN@UE^mIA{hSMkzJzcN#H9htK2V!zzo8%!jq(X#3)uf8~HtXFtNW^D;tit{s#+%m60M7C3?dS-k;$UnNZRTWXJ8eVE86Q{%jCvEtuQA2>DAooF#ex`wxx$^H`RT<8$gdQ_kEk_TumxtD*uSc_wNZGeSR(j$xP7bN6VFGcyN@OQ`jqVth(wOA%g`z*3Y0r&$2D^Y4DP38?99(<p);=w)EilNaOL6nJ=#n_hM3Gn9Qay^IVie|(da#yjp!z5^7Ftq*CkmHAjDc>g&aA7FLSk(tJOva5ncq#$eHue>sd%ato?b|N-E$u41Y;Q?#-ud?TS68En<)1R@L3XBgppw|qM-pOT?MiL*aKZh$`nu?s+p`8Y7mfR#hX({K~m+=cKkuih$iVsr4K#gz+mN<NNNtN(|W@HSFeCwf1TEVNwhOGDd`AG;7Hlb;rU80bUjj6=#p~{k#y+t5?;HmW(&x$EG4hjiTtoa@<LqNVwDuo16>_wa*zu|gDgG)&;Aw7rs5pr2;{zX%xViUu<;$!P1OR~7?IO<llbeZ$x?Q0MVlq8;!YVJ1yUD&zKo$BP~4~jFwb6b*ROfSj*}!|#8`5P6^8;^_mY@a{z9`}FkYPT=3P;CqALO5Wt9|Ihnr!g%5q@>D3ykrEHo?*;e$tjNi=4Yoh&PIi*~j98qd3VX^FC+Oq2*1HYI<k7#751oV?@*fFL@A3~_;;bJ(F#%@343s<%{-my}Z{W(kl?h;awSVrd-D)D(2}Is#Iez$}6Z8!rff`jVO%Uf|2AQM8?Ct<h|#WFgL&A!s0NGtrAcBdl0lR@Nkh|1-(Ri;^W;k{(AN19I6S?V{xon@&ZO+!bMQa3VC-^?6qQa-Jc#9__<Qb_-oFbhW+X_@t!BYL4N`J%1EZD{E%d2;{sE6?_=~&B=Kpx)F(WV_#TKmB%+dT2sv=B{!)G{BEYbaDS7jF$!3NVaDi!v4xGXR;N8Bn<#-N9LkCl4q{1SaA>nRDgxswqCoAM3c}e}bEBX*?Oh8==pljAPZd!zqPdI_P`d*_V|=Jdq<p=Qo`#`)1Hh(a5J(lwPZLi?qm``#)D!26Z9X&6S83|@KJG<t{Dh=9<Yah&Em@H!l(><fz0H(0IB+=?<Q5QfVl!<U@kW+!_i%fn3Yfu!O4h+SED_OT#=;$i1KUj3R=>rQBB+TrM{UuPHUo{r(2a)|qw?9M50T6OzxnX?-TN(2_0b?Iin7JNG4tpAl5PISxt#1aP2^#0z7Avam}J2>YK-A{oI1HBt4;|OMkdqaa~}x_^4tIW|CJruVE')))
_DONOR_DEFAULT = "route0"
_DONOR_MAP = {'BAKERY|BAKERY': 'route0', 'BAKERY|PIZZA_SHOP': 'route1', 'FARMERS_MARKET|ICE_CREAM_SHOP': 'route2'}

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
