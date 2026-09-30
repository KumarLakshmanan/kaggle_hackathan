import copy
import json
import zlib
import base64

_DONOR_ROUTES = json.loads(zlib.decompress(base64.b85decode('c%1EhU5{K>a^!#MXFjk$N$QOwwI#xoS|BM4UV#`4;4v0h*ao!YCu9EmqPsrsy(c3hBJ<oPwd;LivAU}6`97JEk&*v(@%w-L=imPN^5UD{{_Emj|ML64{q^^YZ+^S@`R&J#7oT5T{LjDq`@j6}i*J7W{Nm!@{_^|(`s?2=zWMF9i$DGH&wu{;!^3yKeEaF*#l^2b+`s*F@#6OLi^E?&-rs+>ynXrk^WR^rfBL6~51)R>fBT1bAMP(6f696B__((}z5DU)`->MB-#+|$@!~4H{qcwU`=1~GFtp?2!!O%*{C4s4yKn#Tm!FS6_4q@--hce`^y1X$^{eft*S#2?bpGI>DVs+wKS!VSr(fQ^|L)H}zy0{>m&dL<4?B$i=3&FH$PT`L`|Z8azc8c2R}Vk+)3R2!k2$yD+qa@`$4}znd;97BL-xz#48-MpT(m#lzkm1%ES7QPU=xm;X6fzW*OGUJc~VUZ`{*>pU{Qgmotm}`)9TgJFp+WphsTy|p0Ip*`Q^Bj$f~uvcvujd=bmRYAM52a+Yu^HdR%VSz{U?9#;-HOn;$aAfB9S7P}T{3`hnH+PKPBJ_+?8kEeH$Bdu|x-INfoW$LFhIzAg+io9{T>!>9KccQDUv+z+2FKX|<DpJ(8&^kd0*>y5@P#n?eGu%{Q{QhAmEB@=pVfO>3UK$qWk1{7RLQv*6as`SI;=Y|(8tH`rHwZ)TLQYC{XG!(woxUrXJ9sg$hO1yv1-#z}x`H_eB@9)3;^yh!L|M2PE`*;6iJmSv31V8Ak8DPmLzjd+*hPUB<`*{EU{r00TE>F%yaDKw2a{qRm+2sly4OGLqO0B<aRC!O6M}saqXUu6A0{0?2KaCFN&j};hJ5QFMd7fs1eLL0O^9gfUTRXRQITdEk=xh)7*ExCC`3TzOR+*Zcoo~1}!~ef2^;`bMO?uB~hr0xwv}eo^6?V~NMjdg2J)2{E!pqOa8=5^&UjN8c8juHNa?3FXPTBCoB_oG}C9-{LIESrO8%|&`&b5||CIHeJCgU9RWDh24Y{zm$%{~3#4{tyGQxDo8qkLWk9Y4$(?sKyzJX(7mR!EWK*GjW_a(M$gcyle}_EkRL;PSY^(TKCdpzwli;DH})jb(xmdf@*1*ERb=0EizKg)vWL0Af3(Z9=xk7Xl{=*2?t`F|k6x#CpZ-h|5W1h~3fJX34Fh>a)7m(ByMG!zg=Ei`K*+Y2C$f%$X&(xpwkn^lbNfN2Qvc;MFVa8eNEDq0_00-Nu)38QqO{<2urXyEVph&HI7{{FYZ_s7tE|*}-r)!8NkWngJ#lGh<qIr8R8URSA9^3=+c0+7{FLYC<?4dL}zqpbd4M*-+itT-uVau-ZW2=bT@Rh!nH}67WIplJ7n|{JedfV{?pWSpce;CAU0jB*yqwj_o*{h8x5+3;i<&5?Fr5gF2?*NP=mbhPPh<$ST{1a~9e&8)hwg?7W{XBt#;4ag6hrP|qG4qH_B}EtIO(0ItCAjTdprL;<&W!|W<wH|H_OmoPE9cD8q;p|WR06<zE!5a&jCh`R!A@_G0b0V$`0nXD4fkr(@}pUq67;4NKBj!_Z!V6s90-D@I7O2AL>AOkCMV!G`2+=kbY{6a4X)ER$nV)V&#&L(BSG6CMfZ66ZjVCr1>z595%ZRRX6Jw1c*ccsGA%Og@;dHE?s<{22+%|InMT~0p-yOf+g+ETM{#;FM4`O9&L=IzvsLuK7=WRMYhGHvvokD@pdttdgwSJnjCrPF*lCEI^>e}DY+;q9+~y8rOupTXKj&VhQ~T*m-pA>w!i23iC}SH1Vl`Pky~ZIYwR^|RND&@QGwxAE6=TrpGJ9=VUQ!nR=Icfnb5-tT%5^eh(!emCRr*$VZ~xZ}c{43a~{vccX<`ZGrjY{kY!CLUyinu&Ss_$0Ix*!7;WqpdMrW*vrABpG{X-}#a>Xxya@cK+cMCj!=6aw+yh3#m1P-_pY$cV@H?K-c5nR6iHv_2J?D#fv+`3O~Wo$1mUpta7ceIWT(nq*1xsbB>L^fBVy+znd`0_YV&r?^mB%zE7{#*ym;Nlg=oUCx%4MtNzf);<Yk-8OL;h89*2!MPk2W2_E8M-##48AJD|;amN@M@~p4+y@M8iKLMC>DwLZd;fC=+E01kj<~pbJt>20xxt@>GeF}~mhvcyuP_W8}T@H5X!vFCdlGu1~`j4D`!wiY3s`9~LBhom8Oi$I>HL&qCLamNAG|$6nW}5nN{YS8bczoPKw3#iwW<Wf7(^Q_+W=5@R<PHG0mmULxv6jrzxYbCO6<ue^OffnR*@`P$Q8;8H7Wbx<N=#kMHm`@wCFR$E>k{lYdNxj6Io|Zq&|-c1dXt6sUG4)G_yt${^9vfjU*>nccr{$M$OjV#0g;U9@mK>TCOSvVc+#PK|DHk-L^4DrbUEU`tJC4^c;dF&-kApCu)VsZ4hMTfeS^7UH2*cul!TzW-c&R%%>ndi-^ma~r^Sj2(LtlY{dt+h`y#(3;x#WeH5-#9PBk#L7KbS%z}X(Aap;Tv1Xj6`uIZ!Fz_k@*(o;L~agrt=z5LKaL3&A~IOm2_&2D$bi0-Jv$%}Hl((Ld80PSovVk<)waohvFOa|r_pcXA#(2vqxwhcejf;1abdCk4e1{#%Tc%`wAR@Nh;{Q52@W$P;^tTRQhx8OaCb5|kigIx>8drCNg0bAfLeiIiQS|ASSc|GCg$(2^jDJXkC*2*YYN6+T)Or_@mI8S&$JTx`U1lc&9?D7JCJnxYlVQn%QI8wWAGZ@e~Vx?A`tseB~B@}qPPk(&({vVHlBuyR3$>oQixy)hYyIcXa79Wbixfpi?kZ({sO+Ag}%Sa&6igi$an=+#nCLDuUOP9ut+Cj0=JskHACvh_XO~xl{HUbOtfvqrba`p(ug%ONML3AcrcyQEE<>2)UzXwE&!B9n)Tl>AGI8vRR?z7xtFTgP&q)=&F2|9(3eCjF=Mpb76n`si#il;oDY4B`m65u$gQ5w;{&M=W&MoK@#W8~3X^We0STk^A@z+|P&eFSFhwF_e20G?>f(mVh8Fe$r5_<>z-QV($+hgvGyj-)I@wgrtpmYDLMND{~;Bg#>dW9+gvafB<qCiiK96qAN_TjALj2Nb<R913UdscAhGf14&@`Z>S`xiZb}V6zpJZwQ=!^j?5fSWKWd8nShnc_NM{?>TGX+Q}rqnq*%0@S$49m(G7xu9p)1<?hwokP<U8`Yg&dJX<o|U?*t}2<I**aKgPw4$J3tx<(tq2rl|mQi2Vvc(XlCjcBgLV9x3xG^#-s>ggvm1A>{mF6dQVfGjo(nC&94o->`M)?k8ZIW;5*jIOqM9x>|<sK!S)!o3sD<XL%@#!jy=btRN#lXf1Sh%5mn%<>jHwtP+~KIPe6Um@DoW8EIJQJxWTxa<TDcwlTh5^sDKVxo*w3BDG{t}xfgjgJ#SK$=;SRSL=DfM&3h;YbllsIByT4X;fMhV;p$<7EJ40a3ng5o!SgWsS68?yOeej9n80_Y09W=%VBW+dw?rCW;MuIah}7;iy*0S3ob!&B)_Ye4xtXm+28WXndfLaqHX$5d0}6aUI6px75Ooi_=kA?f}0(FlC&iboO&YRcs;qEI!47OoVD5NoPzVAkhjzucF=8mesPF$c45*u$Liij&eY;RX9@wh+*;)Ovj>dcZge#i4UtUz}@tUpT*(iiY-Z!u|j+4_@FP)9|1bxCQ<!VST93BZvA5%+xnr=V2ARaduKa$`B>jCodjLV-$1RVWM{z9N&(j1O1`!31&@S<Qm5%HCy?97YdZBt^_6T~gOw@64#^2PBxjqhCnPk%<lZT5KrTNqG@UQmoU06Ic+$b;)rpgJEK*+CtO_DWo??f9h`3gH8atfAP;p?(<9p-g8wXzf;rrJHCEneM%&K401%(pywt<gd0hhsYf}VRgEK`77Q?`)mChDEJy-0?CxZjs^k_DxqJq=Rhl1^pH1aWS<9RyCwa$<AUBcLA}0K071_8|O6YWX%N#GM+IjX1p6q3KSQU8=to{ssc20mCh%P&myYFKP*l5?%@yfiUor@ZR<65BJ}He*j~qFeVfU2rGZJ$yvlgp-JS0RQi!zh>DO1rBH)#Pk4u^q!-n>x?#bdyx;op1NXHS|GLguA~K&UCz+Je#A%L_mSb`b&OsGul7U<%T!Kyn8k`K@f=$a6b^C10MFuk-zft;i?N0F(!`r(t_wM%DF{V1-#xFsAK)Q5{4sS~n`HPIz#4<V8isK_g)Hct2bf}7{2EfZhu0PaFFb^$#;q8`x06=#|r>8}z^N_WtgWK9zo;B~+u}2OSj0*+l25=Twaz??0M`$&0Le^RfocTST*^OCH;qOe>2`jwu&B2o6)G6=FSDy5q+A3q5sO9e=5*6!&k{}n|Lo5|^$ui^TwFSgVidc91_zGtgu&J$@yOp$#`6Wg2Z}}3eXL6@wC)Lf^A?7ASSzEM{k&iM!!u)~*Jsw&JCNWE4_A-6=W#IlbpO)I;f}RrH3aYW3xA=KA7}(U)S_+jjLJw-0i6oCR#rLY50}Z~?tFJ&<f@~2+A<-Nk^g)_uSPDQfy>F_OTdCIt_G>g2F-wGMWK@PBQXmu?83e5SPqKR?3Cf(a5Gu}rm%>1WkI)&n$!d6AQpf`7`C+leKM@51XFUVogXVojLJcrFJL}qBRMMmcS7d<>9OPo*u*v1cjt5)_#I?k|5apJ!6BiPVg&7fL>!KW>w?N&njyL0uH2t=2iELm>yNlJXJIRk6a?%_l(vKhOnWL%;z-4DfbSjKh@>KxEFrGZ1W!~WFL9v%%M#iL8`xjV&Ad;GV^1FB66EmXi_qazU$l%8wX^rOs2D-mRK&GFQobUK_HJKrBTgQ2hjm(R^mu^A^Z>VL+f=oTf2JkynzKOjjNW8zH+YjPYp!Ai`ir9_l&>=zW>uR33kI&&`0ws|cw$8T(#*bi_yA-W2vnyD_4hmUhO}#0H)Kykq9;e3~0gA^l%AU3xDHmBJJ48YeNl-nqX$qDsOP4^LKd2d@7*0fx5RgB?fY^e6c06W9=Jd)(fxV?q_w#fMhX7&LoFzJ|c#Z7k=oX$S5pfl2GK0&7M8}K6z+j;Y$^$5gu)&fY>N$3ZYlOr~6ru)~k|_fNKfJ;g$fj2j1^6zYF@>xkbGeOPcpRLEjWyWa&hQjJ{&Hp`(9ttsqVvx)Q~WYOCrrwaQ|D<yr=L;?3WJmQksS~jPM)1KnfZt~>6i2rDnT18j)iI=w7@u~K+^Qz#T1s}RaW4E@zSFG%N2m~Auf5qY|+<W<yOjG%RYaB1_`Nv+fwyjm4eB@XbB%6)+Dp+pF8#$mo+$t(*)R|WQuh9uF_0r=%K!TT7;|d0EKsHkrn7N!Zpcy4NjBg<3x+~6#Jl|k!yKvqRk<)<5?`48u0RjSvb?&(}_b?D^j(jiTLSA#IOZRGx!<OSCED+<Df)U900_T93oX08#q<yI$9h&E1mQhiUyPDCmNAnT(@O4Sh@<pIv|>_p&eJEI|hMJrN5YNsintUpPJbM4j-w&lOOuH?}qUmZLr6biM*@b$zpBjY&2c<S_lTskF-`uXdPgp4G0Cz4PZ>LIQiDo^<?p?WmDpw;n(lbCbeV0SQZ68eI$j3OMQoku_m5wWcN6dh8I&?0{|t9ERehMsm-%$iRl8ETff_L-nq|7;I;+@dPkDpZaN~%LJO3<i~4GiU&(o`5Sa5?(^^@^k+{r04!x3-7r4MBkVRh0h*Pk$CtO@y!1sHi{c>Xw*s3B?{UiwTrFg`%>_ILZ#Ik*p5yid9?@UJto83D+4?74MdeKrQdDE0*;xtpx8Xkf-Li;6yiZE{NB}U`*L<1|6ej=5#qT3xMJt+1U4#WI*zuT!!7El_`LZF7drCm#+<tGo>n#u<hz%f3{ak_PGL(4za5f92j&GYg(yH(R-rX;}-A0=1!+FFT5geRp@lwxDl@&b?W+3q$&BrgB$Sb$obbNL&-E4~+&OQXk`Q<3C9lI>9^WJJTAEMt;=2RaC*jp0x#;GB%Q?-zsff~F$zka~wCOQ1n{&f8vnFWbgP-B@&lVC+WNJeSFlO*v7;6H){dJ0j)|X4F~y0=Cj&NTBRYO<+Z<`C1PbCx}rnD+1tOF0Q}r1mHBXx#$vdI9IF;XFzHto$|g}LXTd>O^`7og5_}|a--vLw?nAIeYI2h1u)hVYI0S)feXS-(4hUI^~jaqtZmNl9uS^`=?!f11hOe${gfNat~cgL!y#Gx5eH@{!2nkBw1>oCi)83*enAFYh&dU=mQrR|F%P$duvfTCAP@mA9Y|x+j<(f_!v?vrPJ1Rd0gS%54q{^Z%As%%_k>d-s#ExR)OO`cMWC?@YocW4^H^i58weMdz#Ep3-*B?2s2KAyvzpa7KV*;CJCAldBP|#j0>aQ4<W9^^MV&A}k<GPOW;<B4giJ+kSSvOjf3xW~c#(UtB>a;GtUFdTq6b>Q_#@k;)P4!&UDu}ejp#x6EL0)$m05IZH16tlQL*oA^;7Oj%sJ5T3NYicejF-vIpiMOj?7dGjiB}KjH2(#WPFSiloCyu|BqJnfHrbla|8<HJ~&jH8T#X$v5*Up_aK^uj60z)LW^x18ZoI%fYuiZqJoL>4ZSXmgF+AJ=w&AJ`hzDNlAYC#iJ3{wkz*9p@~TiqQYg?4<A6o58%3l5=lB5~0YH8c+Q_619YZ8yrpA`dfiF)lM__}mJbHq<N9=q@=8I4*_tNSEHc}#t>9B#|u)#UYmA-dt96ZF>=OW|55F~qL0T2ZzKJw)0!8_x%VdRP;gW#&_1fTt|TC}39@eTl<lSP^ZQJ6r0XQw*OJiJR;?kKyMsaSxFo!K4$O^1lb1eW#aGH)LLVkqz7P;Y1(l0X`qsIWvD`f<_>X-ZCEo<u=}-*F18#lttGo6ra5g~77&n6Q_0LO78`6|=aK$Z>YY5<%|ZwB?gr(l$<T?XG4+I769d%QMH}(L#3Am<iD@Z;=@b_>#;#i@dl*04HjSOUf>wIw)YV<E+*Kzf*)csH;qE<Z{Yh>6Fk23svQh7BbqsKFhQNOfVoa)T2tFU9Nnb!e&MkX+wH=DH`hfy@Y0FX-sSy<p_!?t-?5pQDv|m=9P>L07z809-Fr$@8$HB1#DN%W0Z}riao?l1HAGr{-11aHzC3=(MKW`8%*MAnk7O=`80A$Brw1}@H$RH7)BU?0;-5FN23_%9%6WM1{TnE#?}EFlYy+jC)4+|VDUo+q_Qf}*JXNPJ=0|>+)TY5Q@qXrwmCtCMgJm^1FlUwYoeEoV{$kf^8cJ8R5L9FiK8&HU|r;Ib!%1C^TkuBOnZL0f@xwCnQaDeJ&SWQ)T%%n^HOk{Inoqr2QY*@)Huzm$@QRnQx0H~#Lpo8Mv9f#ka4Aywkw1IY!%O4qzl<vXA!Eit(;!&Dxqo1h-{}gF}?%yY#H+F=5{o<C%aAXVHxkxBqL6p8VMW#VLBIXmCGEVsKZL!4K+ZaN(pBnn-H=N(-3F+>pO7yct{PiYO+k#$Os-`44j>#!G@==2924mBT>r7!XRGuI%mq*0Ri1wal)>>1Rif;hnAl?m*HXk1VaAGAjFlKAO&mws{$*s?t?*cfQSJP6htHn?!L9cW>8;gBppR_$`JdoRGy$Pq3?ziLW?=v#Y6{@;2)Z{Xi!Wh1;rt^)Aiw%9cD$R))=~>%8)e!ddw|R1k`#Od6+6%eGJ;-20GF7i%6J*<v=sJ46bwHiSU)EAJSO^cUCQ?%f`Os&>0UaShfTw1{qf{Mpj6`%j}DmP2^;&QE$x>I4#>y8Bc+FtT{}PPOUQ+lv2h$A;z4+4I*-^GyHT&VunHsK7Ne(P)h3fanY2d21$H|Xtj0{^qP<|!4wKa=nO=!MMsC-g6A4v2$Tv!{B%u1Snt{3Y+mJV1lm!o@)cu?j*l$LKe6~X0xP5WNHOZ*F@qMefyG23q>_zCS|VM24i($maeY~}FJr4S%%krDXY@Fe$`LDXxd_*z5BJ$mCy{Ke$kWIjOt5mh!lSGXBp*5@N}s?{`%p73{{U$rNg0kP!Z8w9BrBt!22#(UEAur%-6`jih3@=q>Yr2KVz^_ZD}O@}kfw}Sj;ACyISa;sw+e2*Lr4JpnOJ#)HPM$%Q^pUMZ%WQUmT|+vEGRKv!c=RA$<-l4>SN+O%)9MyDQqHjJ<?kUM7q3s{#O{Q(f1fnu}Cdy&#%;uo_C+I+`H`RkM2?2qfyG&vRH=0uLEB6{7d3=P8=qZu%eTzl*1`a?ArD&YYQ-OkYxRk6CJN<VAzv2l)*|a%gC=sLy)kn@6=j$Zq-BYkgFLjK!CZ(<$^Yn3ShIXt&MwFO{N4lh;mE3r`7FS5|yC72~*X`iK~VM?YnvK0FBEUtXeb-uVom<g;H*!j)tKrU~fJK{voR%7c4eUAlf%K;Yu-i!MqWM63ca}0oh<GC`k%7ngp6S06z)M2vrZk>?SJc%GNa}y(jsR#d1JdK|3doK{%-^@1gQ7VGnS&Dq?$^ZwKTWIP4Q-Fyj6Fg)($_(UO!oacj~t$Pd&{c{(i8@QmgpO_rot4$WMam=qVC7L}bIu>@2jj>%TChHe8EMbnq%_X=KsVwvRBrUF+3p75oVcG)_HLe;|Gw$O-=XyiBzAnbq;p*#o4ro)pRFGzZiBD>+4E6f0IG`34Brl?yqjo6cr_RUTXD^~@z5+E4iz#=UWJNdDj4jst%SAiu=W4_??+Bsyx+dR1?^;lUZ<9G*jY)Ov~O)PQhBvpu3J65Xj=@Ef8jU8BI7o64m%u^}+sDY%3$T5b-_<aD#3?u;VoJ`bwh{mVK9p%dkXf+j<5n1wr%*N44o3hu<)F43|EFER%mNIt{@7Df_)2dDElG+$j74$ayR1=U%D-vBsJdm_AMof6`pZcZqW!!`&w^|M1#))mTBCi~$gq|~#RRYZu<kS@5t5~u_yGJd7UaPWw$f?fryWHG}h)W&N7o?z)SwDg}mYfBdE(?v0%(8Yid+GYw$vcz^Y^3_!<cTB<jW_8zhe3^{mJi}C8-IL|du1hqvl>1nWeB@+Fg|nL>PIOlMuh0nDn<Fg<T+LJ8lpBI;S}><fcW1lj(}y=nJz0;F?q96(W-*xpPIhFK2XG<4!xb>B(5a}kE|Jrkd*|UT(DrDkRhMABc-+5QQB1`<{sZe+ZZc7)tmf&B=qLOAV-!!#v>AuQwD$Xv=9P$z1E}#FU?MEC<;dcqe!z}$ZlX7txOA14_?b!F6|><yU1mZm=19{IKlm<9$2eD7mGzD^8Vuz2Ya4KUgOp<8bgS|nbl9hO>?b#BP3uKuNSussVf9C1~NX3Yf?Hj)P6=8s*d(P$A(~_RNI0O6p~k-EOZtJ9oPpm=Mzo$py)muYd7X^R~K_C6rvLX*dZ1?eL^U*GfWPCWta(n7u-~i;0V~6T_9AFXi?JlR(X($v}CO7Y*E(|scbcTnOT|(9b%RKagK7WkK@P(-<z%(Y)%>1Y__5cTUHDF4hu%(TTcPxZDbzP_pZNq;+E39b=6`KO0=1Tk`T;_3u#k$1SF&lBZ6PVYnD@e9G`kbtau0RD$otMye#1uY@4#L+9kQOiii}&VO@*Yig7%E>0?f(PC$#CtO`wtgad)q2l$mmViV=Zxr`8y)9sEr1hp#4KpDNlSX#>l>x9bj&R{lrW>1Y~Iu#Exnk%Y2sGDC+gXp-tSDT3t=Vl>OHEx^JrwUxVaDeY4z)OrIdn$ae0c?nZWeHlZj3YW7(6u558svIU*8OBuBY0C#Dc=h1C+A^0dv+PINCzSz7L3ZUFgsUKJCN#4L0gg~BTD&VGzK`>EP09jt%B6J7azXa^Z0-CcXP*81qh78>8g_5AwWtZ!^#Pt7P{!c^^V7wOVt?YGLXe#!~slHvP5tA<y9e{f>!_zQUjdShiB)i;cpAj*gtf4GlWdqBBQ!E<sj9#>tPNgtku7G!<kEh!5T4mU@m88lx%1UCBdQD0?WKpiir<gwqCXUg<kE0Bt@y}XQd0pFa<*s^4u+i8%jN!hNjP<=2DbY&e$<A3!(!b0a6vug%iA&lv{-9S66^?jz3~oA!1@3S;l9?PNIY{mY9xf0unZjsc|HLI9vs-#+;&3fuqHaxhpFr=H(u;Uih-MU9aIXKuKoq9C~oJz(lHo-%F`8Z+pdx^FiZu(1Wvz8y!deiOV<XET0YEY=bA-D$6bpLR#Zxu}?&<ps$zt?;*k!1-9nI`$(AX^dw4Rs+ig}IUbR`+jR9yO+aiT>@NC+>eHp#)kRj8UE#Qa&M`Yw+tE?-l(;)3jlMv(r~>EI=iAO@q>I*88xvC7bmiN(A3i)VWsKtoB!h%YdFTvZaTPLb@rBnT;dO4AqJ!8DIIX~bWVf85%o-1ULryn09g>6~ybz6HuWZnSAJ;-M!Pt+6g|WOR5Ka^_Nlwc67R@vPrX0Zo^OZg=c7rK{+XKL6|D*TDukI1@5Fr@!3Po@5CKz(q=(IF8va%8o6jZ|I!1RH)cG&7Z8dQH(t>x{>MZaOy&eq7vErU_Mn5Z=N_e4D^h%}K!oaGhSQc5{KVeAj07!9!`aFpgHpO7Szq)UYCJERF2^AsS_gV8=Y_?r!f+5V24H>kQp^eF^!3cB{uhDqeXCz6?x<Mm7+QtmXLAORS4`A4=TD>=Ks15#nuJ)CQsisT;%m}MEVmfa0SVz*?qfxsH^EYB|#$sACjTqWcXxq6wb9nVKq+d=*P)YA+;<{WbEaHl&VhUO%{+YJ1#j3htp0q;R&^49h_=RQ&*K66yJQ)j@hqb69|3mTRtO6DvPbIQf&j(0>*m%l~H3z6?u!8uld_b!88L@tAuzTO)W$^u{VLlJOB++YG)F3MXW)p$JuA>lkRk9t6&49|PK`|8V`=2%gOnr+Rv6L?FvI@FoEfxq&pv#Oa!ngFFX!pb!0P$TOgvP@BB8)8_dMtp}O!l;mN^#DPq`#$zU9Yxw~%xG>R$jC6IU0B{o07mDlqWb}CXe{BzaU<`o@d)_85@H%1;vG_%rt6j2D43Ekw4{#m3R+i%GUr!oh{>z`&M+l>QCwHJFhnJensG*bwiTOOu9s4q2m1sj;|eGYISU0)Y;Q)A9{~rc@yG=Nhj=9)?=)1IhL$1nN6AUX?EnMrZOn-_9w>NHZ!3?w6Hkscvk2^=g!ur)pj05}zs(?8r$AMPyf_6$_|@c#!!*eOHsd@+lW0Z)wo6Nb@th=PDSc!L6C4QRHY>3gqua*|=S&;im;gDBP%8n0kMH#QKqr5=%o^rxMYqOs8p1N+qpz+n?&zf2ApL|2*j%w61xLhR)NL%nLt>fCyZ}|~jGno~MnR;b*<{pV7TuF*OJ+ome3Eo`N6SY+5i0SQS%rABI0q?{DW@ZB2s{b0c8ZzRw}>*0xTgoq3PDJMo6Q++ppU>9QeJI5Fi$>RzZXi<Bq21<>hHO*Vwn?#a&X9@>16V;@29y0`w)rtc{Q(Y<Z_DkO+w4Cop{Cq_yM`WUSW9+Z=|x#tWX_KL%ZDMp&gzQq>eO<_BtIjQiq6FVuO^SK09f1Ll-azdOhz@SB!C&ah9_DCiRhT9bF@*l5#MOgG>qn0Rk@Oi4s<oW+Lzr-${JpfJ`VOv{zUoI<B@Z6SNF!xWiT!VxPPyX`v->SqN7Kz4Yv>d=+t(^TWd=X-oKCmRc?Ts?LICBynUVBC;YO^D{PcnSPxhaD^N$xP3hi4fqtv*C?bFIU5;JtKun-b>YIt(B$mN|B-CPQg&(FxuuO?+YDj924x$W*yPnaQ|rV>OMqYvq;_Fj-%C5low!{h^4wJ|djyG(KC>e^EvXRILDvfZE5q!4a*~;pNc~r6jXA4#Js~i(L#wEwO&0NEmY>CLzo7jgkUGGGGH*$G*ve*|ne3C=N#^t`D$`h)+{796S-_ZP*^vu^ILbGR6o#`9TtV?L#(t=<QV8Xnl&QS6{iJm-eJ&euKz?I@OVZrYtG=rU1AUb;Vk8`%Vg+~J$8MDwwsKU~o9%VB+1B)%1<`+zXkbl@#VFqu`wDZ#({mAyVV&s!?`*;aioSAGsH6q$4}YYd%bOM*gWL6g`sLmG@BaMl!|{HI-N-pJr5lJ0ogG(}i7zN%20kh)2$0GnU|fNjL`-%{Ifv7qvO5L9#8W@OI*r7(^l!C>+L<Xd<XOP)VVpfITBYx3MrSL6>MW-Q47Oaoy`j%8W?<*j+*!)rw!otmi1xa*I*|1i9m3O-mSKWeaVbh!Ns%P?1-nYz*^ieyEepjWt_sEcbyC60Z2uVmctYzE1Fja6rKu1YXfMd4^CQW#M?=X{D~VjKL%$@M$Y&r2XqcJUaJ%?BR@gbnR;FCUBzJijgKpdT!eV?^=8!VSliac!mOO4Ru(#RBao`C0%HZd~^6;EYu?{xS;$cOcko=b~D-Eolt1BO@dDfs4=G2Xi|8eXKxY#J8i7o7ri|;KIv;-2I_o)|8Zse)?U~z-y^NSb8^-JvNA^NpmGdIIjge?4ZX4C46N$1FsxN^+BZ2*_?0^9`|MxY>Y`Y`;d>Z;#dy&=7_qs)Ao16w8LIka*Db+P!DRT5L_1vlGYq4MopgJ6xw97i%yw<f7%*_^)YyKI!PGNcf-#=7>G&YWKA12hbfpL#+)JQ2Pjx1o$qFqdU}1g|4r3XQ?0C2$URYN=mbT(vx7-)5I~ld}rp02D#X0#4mgl&*e!bTajV;ETVlN3BCi9wv=M_*`+(#%k1o3^>ei^tK(^{txUec9D9AwuHzOX4s1v)+h>UX&~lsKB|x{?t?VPkCv85)__^>oa{+zQM~MeKEfNz*ddvglf{2qn=@jG3*NmMP3QB&wspDv-di5$0o=C@fsbtcbBybmI^G%{;5|_gl0&g9kTd-4s}90mqbHcLXD^anv3jVG6+?qB5&X?_>O&{5zw`<W0~p03&+kOb>HMcS*z(>bEAcdN>!|+8n_qjFqyEUo^L+Kyhm!cx5KjxA>Mq4U*0$Yw=;GpI!kDXA_I9n>3vVl0GAuH%g>V1JgJ(g8wv4QS2tE5Q+-n$*z4L~VEIt1-<}H$~KX79#^}NUM<Ll3#|Ni;K#qa;|pMU%7<;6F@F`7u^1ur06!h*L`H79ZjA0PMjr*}WTed^f5uPf!?^V=VPxWE6|OJO<#XpcYTQ?Z^t?W9p2nvz90*|QE*rk~$_{Pc^WClLj#;a6k_Ps{?*Kb(BKd=+v&LB}QaDjsW`KoRlV;|!!U_aE=yKl}t1%Q$kd2|+pT@N3CCRL49v3DvMTlunL|3OtQbNhE3nbe%w?H!dZzYOO934j>up5M}R9I=DrhfsG$Rfk1DDH$P;KKc|KD3XC8dL6zjGKR1kboNk?BriS^tFwAVe0qJ4;={?3B%(G5HDnFP|T6Y}yEB#n9-g=|eIJ;nA(*gm{GN5EaO%;s7fP!2LJ+r$F==iA85BI{*J1bcfNdJ{=CKAgxv?@wBHp(eeze2<#hUD3a@Q11GSIYs-sy9S>Qo7%m98_?A3?8Z%_e_32wf?eE<vmRv?MQ5p4GP?g?EEx3m_LUCUY(zLo@VCiG`;pxnUU$%j+v&tHWtdZOt*NX^iJL?Q**QP4W||8|2sCNddok;UYxa8mm=4mF+)@gfc~nI2xr+G66RDl^b}KzvRTm&%B2Eyz@k$&{BX(0;b4hupBhfeepbUtko{h3$!MnJ{~bqj)_SCk?O2X1b0MLp7!DyBWx#Uq{V;2|0R^Vq0ec=;p1<CV(QKYv-Y6mA#<H&@9VtYbV>H69N4yO@@T0A<Ob|j3+<*VNW<Ll3am}CH1`N!0O522Nk1qsH6s(o&9b#gIfQj{rCQ(cpL+p;$HcM_5RiD+hh9;lm8AjQQTC^skffny#lI93TB{I{v-Rm8d9ilbGuF-`k7P_6G1;*R9A+8LT>y*x5GvLPw$cA|wRuRntl)UjB)(j<@T1%#)uE1BQzAA+@hNz?6vY6Ia6T<nbSqV9j1=&#D*`$=t)<EFru=*y1)<ZRV;x37F$`Xkv1FD%Nw>)Vi#`so_?Kps>)FftBI;$NM(0NeD6dXw~ZPW1fD*#z#`*6-eduGF|WskA?5ROG7$2gA(_3SYwX*&(IP^wx3xB|a7Uc@C6g$g+Kp&L7Xi7#PdbnR^KMnh%Kh^nQX(24L6cO{pD+~b%4fC5=1pd<S@EI_O*3EtABWT}dVJt*@Z89LIRVT2YIup%d>%YM&ocpb?v^nyU0@#iK+pFGE5?;GC1Z66ZjVCr1>z595%ZRRX6Jw34M3<*;&k5D?YSD4H*FtD3}N^rWIg<VjW{G7}V&NvkT{IyhIvv_J`94hN}BZCaneP@lnsGC`6EYs?;d}U3Ll_`Z|G$J*?w%TKcbKuM7bvh=rr8;^1OjLW-d(WJYEe1KE3>NgxUN1uHRuo*%am7q=d*nXK3fqE--vwvMdB5vL(6d~cniFi6vlZ%}aU_ke5G03)WrMw!^k<G5*ouvdOuR&D?+a;}tt|z1y&IMM$PjQTbWO${+LzVVLvNKf7?4+wK|NpzC}F%>Xd$(R@LPKL<Iars0q8oYDrXA-J}IsSIc#vGZ6sRnk_N1DtwcEq-woZAB6xcG*&%xW_NPOCH(`?RA09s5uOg_4KA!HgQW=vbPYj8iSN)-p#cO5wGLGp0Gk`Eej6tWP1}wp$&H!j)^tfXT4SCjA``$r|zn=h1ITgxHk#NKKpq0lqEptu9jm~eykzCJ5={}`JEa*`;G@cwiV3)45_Fac0HXfY*sC=I=L!?-Id~m9ltOzGrdaBN@fsLmTYIU@sd8PtMsj1(tz_^?i)IzkGExu+zJbBYpp44VWt!v~CQ1MW(ngnAlnWb^7kt{2^&XSp8bR4o3SGJ;X$VM#gO(~U_x|nTV51C7|JOSHp^lY5Ca=huIp~d?2^(G7NyW9sX@C&Z?=NB}5zs&DC2nGS+m9_0A4gw+>)8nxQN=$T)nDL}T`TjkHB8X&&O6W4Ho3uEdnJBU8ooOHr+pDDFulj~xTtLp0grK|LR5UNm0rY6!$q+@S#fl2iL8HKZtQAR1Ok~EG*wk!HVlAcPo?aZLlmJI03wclx9QtBEfmLp#Yx<}(aBT&d^wf@goTLdzFF#%i7-gJD!>MMsJ7Yw5)ZyesIbLaYcmaTRHX5;&A&NNefnFv9a|=+5h8iHd&RI14PzzXDIO;X`HXCSEp5c|oK3Z9ii1O>ZoRqDvoUqOm!QO)REY4kps1J5681E_J1O{w@xA;w5aA<)zpy&03n<rOVF{hyH{a7obU>!Z1!!wnhM~l>AiVzJ=O*26@PA9v(z#q?hBu7}AOa_kB!m_|@7)z}<TRrH}ODJ$t3G^wDq^Tn=2^Ex5A_}Or_)rYa#kd=Qe1qC)>S-)rCY927tb_8~lo_os;TXhPx-@Ro4vLNL;kb8Xk)RYnlkv%#jljZuU@Jt4eLEPp)-R?@G$IAjnPlO?QA3r3*E9Sc5HSWr6<u!a_m<*Fb#}VXa*MqH$ApkVrEMkX6h88)t2h`{oegZJNk}W6@_44fGh8zTCJ4t-8qvPaFp*qFN<YM7<k4L7;Ixuk^0T18WTnh~1ZM5E3u4{?o@mU{JO7!~K<GsHfn9G>50jb%VyS35lClih7Bv1?V#<3WNg$VuC`U<-vCG=T5w7%_+@}RnOd8s4g=bqFQ1l9MD4e;ccFR=!ZNCz;I_{#$m1%Ydo2{UHL*V?Q_X4z6iwX2bL$)rnh%<Wnp0g&dolOGF$>?^+6GRh!gbV`Ae^suR68&wtSLTQkGcx)t$~BBIV9{Q4S_Aw~Z05$2+F!!wLMDz1F8Wkb6C0=;0Ki+_(tV!@w={;qs-r*s#A}1^5bt_qcyoxWy4+YK7Vy|b7(M4TO)a?u!E!1_5YSw0>O4MH#@XpGYm9`W+zkw%rDVknz)Bycm!rBZ%8E)82pzQ%kzheI<H?Cupo^-~#vpUEz`?Dr8;|rT50p4uc5VkeLuP8OP%^5-WeYr5n1<wr&WTo_uIzeMh!C1#P=+vRSp>1t^EJG_*O_%BmyVYll*LN<x<!BnjG;9$hPfYGK{|HL8Qd>=+F+8B7i<IZ`(M-{^wP1e3%%eLAb$m<#N1>(R_M`*&OK9)z)9m{fQ)wMHXuGX!CTSL`{Nw$Dx9p!G7I<>!eb0WxBRL>B8gN5A+pcnGacwjsP>V($0Sq|Z4&e<T7hl-Evt!KkxP_{XOXl08iun<fN&-+*K{l(cZYcB#ztD#8(#lZemLJ|<(8JOCy863y>xug7wC@w&G1%^@%juumFLS!(%*W<e`qw=q`c?eVb6U)XpWo;Y&x<ol<R?7O^MNf&y@nUy=l9%ZV8XDh0?6qwWm<t$bmYynM~8;s2Y)W9f(NIxglNK^f)2K38wo_RmbLn6hqVb!pzyrfS4!!T3)X>IbFvj*evz=Rb{>f=_60aL&!v2t32gBnOtWUNm6o5q!4U*cjLi6Z1{q(e0+BMof(GU=wHsubGL@&3Md?uN2GeGJNL%ibwmmvT<*&u$)eXVR}<vWC4I~!4B}LEI|v~B7$r<nPNUFlfbX(l+aog|a?rQQBkt6ww8i1Y4o!E;@lv6#@HY@q4Tx?b*TQKIc~Q%Blwec11%!2%gp<}s-2M089~^=y#0kX(!pdK5au&Z(*b;dmC4nSqqM|rLxz-@~6W(ER>O~nZ680i}GGf`#N3IBhUFZ23GRG<>o|IC@Y2K2SXmZZTK`CgGm0Tuaf=&ctiwyFD{mE5!`wUHB)<u#ubes5!(e0%{_f<;D1p8F5q;MaQRvn|r+j2$zB4c&3e2kRxeq?OA#%}7T9{@iOx%f~=!929|-L_j!0+0??6nk2jI*(O*+PJMb^9*;twmovCU_dDNF@UVV5;h91Is&GFzp>U|;B4^m%<fZRuBuv3SoMu>4wf*dPWjS)D)2@)cgx=}kzUndfE6hEIGAAZAk5v*CAQ`_vsz*i>~5cH;Sd9MwN;?^d6rpNJZ_}2p5ARmH}kS}$thOJkm~2;qa2VhY2f&dM-;+8TE#G3NR1LyEW(~zJCxzq%hZd01r=V-Tl~Dj3~V)kfOzjLXi>GS&Fc{k%I82+zgPdn-B(~RLGB16lxWfq`XJ3oEQO|+HaOMQt<?4c+c+ALm?%Q^G%CXoDG-XD3<6gEC)xFqglWz>3>BxrOMsvvN$m2#IS~Ly1*?W6+r&Q+?yIw&floqn#A2EoFhe`*+Fn%B$OSj&U{)BG`qhmU<CM#c9TT{CNWn(Gd5w(|5zySSc|b-N3zZqsX6tUvK)EmzVG~)0qH*Dxj$yY5H?YgyC2m)?<Ofw|nxVzsHgZ*80208g^;Cn)+Xs5}#AyMH#(2tsZcGjNYh!5bRh^MSsYjs~bT+0p^GhAXdOcw^rNX}JYIl!&pje=sZJIq)Sn&NhBgF6=mqDHsQ~q!+F@Ns@^GO#MghUTO&SmVHbA$Y2h9E>Gd?v=~Z1>P>DWJ-TJqz=LRq~Im+^d&vY%z!sLgT8yKG~;XUOtk~Iq9^jivX+{B>O=ES{f#D4)WcK;XueyVEcO{iL{6?EYk{woU+#5lqnG^oigWHV2%exSQ*z+Tk4cEF7i?$2`meTN8QMm6)%G2xFFu9IM|tX!nt|&#Z6=?0nHZ-sVxI(CnBGiwSqx)?c6dp*`7x!I3svg_#F8%(P)b0#tT&5T@(!n>4pWTDD|VH#mBd=A9Jm%=IDE-&Xi>W(Evti1hmWC5WWj&6e%;EojA5Disz9fz?s@uo`wN`=k6*`C*2%qm%!4o-kJO*&#9o9z74*kq58)Hk9H(&IKZfD8E*ZG=r<oeCvBIWZ&an?dIr#90aR3(qXp?Q(VNt7cF~HOn3NYZZ=k$w@1IdEqf5Z0ukyL;oEL0U)?ek=PsdR$ZO;4!8bl<9pI2<y!{4vJas_r;EhVP7^oU<SJ0BqK7jP$~N#R4uA?aXWrP=>1c_h!~^g@Mj^|Ee)GtAQVc>-+KnIWKx0*wz|OM3!sF`*#A$Ql)=l89?Vd6HP;nc;5ChFr$gPuU~x0a&NOTazA_bPpJJE9yuA9F^qRsUq{hHAR=+BI0RfVjsC0aS{v3c%&ECZ50}p(gmO;h*WD#&DFb)kxNuIGeY{!+)rj#IHbKoHp$STeRqdiO>{#k+kXcR0fQgoiGtl3if%aR|8Gh=y<p)GnhC(9wXS4rsi)=($VQATa_&!hP#T=_xP$o3J3LhFA25DJDP13mq7i!EJ1fZhxGZgHnK6+<fc4V2jx3a5Z6t<MrmJCYwTfcv6mk~%e=fO?e}&%PUiuRV(6bm1rNg7%7v#E1$G$?S&P!8k(CPCtHf_ClZ~&g1+`u0%K}}?>u06F^4%cO8r@Xgh*R7U5`<mdan3Sn3#Ft_76P9qsGv2Nbia)RYu}5bhRkz5Ud4s}+eDuuLA5;*wDxuilM;dXC<kY#>R`!Q0j>bvfpw*mfVQ@G~E)L<plch#^7`C<h>Q$lIUG(mwx()>@!(mB}=T|$Gw*w^ug3b;`dPq#1wLD4_5~WRf2G?YGph6YQrXd(%Sqe!<jwqQs7t2_Y#N8C}*Hh*)3K!-=ds}PMh>oE=K50q6exo-jHQ~Th{fv|CrYYr8ZHEWc&YjDl@&N#9Q54`}8q3f8m4q!#c1fK%6FmU3vPohr=pdLjhJLO3F6_8I8wB{OG$W968e-r{yMzRQln1&EAlSF~(~(z%cKxDVF?d5@ekWl5Mqent@Y8qiz6X2Gk|~q6nnm(pn*jzU%1+k=Y_*!Q_3&`AAH~%o48JSzOZg7lP5>e+n~Rhy*|#7#C9sUDKr>B5$ivo}uzl!Zu4o%F&_%Gv#1uXDZ6nT-s1Z+43(Is61yV^ROfdMlH~jqk1g-@+L92JZI=m@Gx?#pZPVCsAr<XS^F;L1S1YEzk|6!jOU&lc#N{E7`ir|4i*v1(;Te?EwaGGRJJG4p~m?0rkj4co|0oM~GZ)rcCc4h!gJh~3kl>sJVOfig76D#*b9PFBn?9fc3bzqmNRRkY-fHTDbSfB+M08$v;7GEF{1nHquwLs>gW~FHC0>a8UY$u4Ys3jPFK`RlUh*p>ZEmQ^sMmVzh7E7&cojdeik9lPU@#Am$xwGfQvNC^%2XgVswhtn(0#Tn(mRwRHzIrvmI4RrV)W%s-y-w93Ru=h<=wA42$h`Hq-9)KL%MIY(Z`UXL&Q?z;sd#hv<GQNPnUOlv%L<(2lB686x#svx^a>ft7J5SKZ00%+q;HiZXa-K8%`u>*+{_(O47r_BU)bhyCxnN*E72rnY!ZcZS{bAJ_874x*ky*I!(i@wbJT~S?CT8$UeNjPf*L1Cm0cK`UURoL<BTMZTr-m#^q~4+g?y8uqIuA3Mk8e}x=jJKs>H>5**0sqh^>d~U26xgw#BE1AK!j@uu9gBZNKEqmIi>u-h{uoZNjp}rIN?hXiRPD3F7>cXxjs(4!Dshg3-W$B%v2@1E~A1+fV>=kY-xRNl$f#nf`7L(g4>A+IQ0u2ew;bd3F&adRnGeB?ZGA7{9WRE&y<Gr`pBnY9^#|ep$Q{M7QK>VwiAt>B*WXnFv`kf(mH8wj4q<aP|n2#>dOi0o2c<m2te5>LSb?Bfv+l<dnsOh^KI4BOhW@&!9p+j<z#wa4S@&i83;Qhp;_$0Pw)^=4~hCe%ky#ek^KkYl2XW$@Gy}(!X4m*tg-pZgvVb1=E4Ykc_=fSZMK(<f^i@P<jg6EXi=&o}3fM#0huOAY`A?(VkfObFQ$at#%kn5sMm{`_cp&^$kX;LGqUdOQ80Z#Ib^YnaMj@o1afin<3+E_13z-x7u@sK#x;MJ6=OH?u>9tG(}s6Le6B^I;w>%G?+n~CmMiD7T9R=45I_+bM<I(Lj?d9Bqr%)3yxkVT;;)&nP(|oNO4WaMGE)>$^967HruT%yOL!q2dqy^dA$-Pukj{0m<@bNpAcNwaO?;$(_wK2kAWXFN_<w$AB-Bo74L_SAp)^oIfkzQaCA?q9h~|QF|jZpHBYsrqm5|jb^;%fp5UC~thb>Rkt`JcR7W}Xz?);tNqIWGD{+L<8f<-dL~J;4yr90pYtDDc!8Wrp1BmxcJaq|2wQP#qHOnA{B&Estw8(ZUWD0m=O7S7|g%sBzgf%D1>?)UL<S&RSU>ZRi(?Z?>_U0KOL!BEE{TfC$E$$2UUea8rj0cocqsxb6ZYH^fU|q0^3CLXTpd3AL13Yv)s!;;Gi+%{M81Szbn;%l<#5wZJu*q`-r}v3A`$&oZpd?s*`pT<u)-nx`q;k=lN@^>UM~D)e0hB@jDTYUCmsV_*QwDJ_j|;echK~V_wvIU*-QUP7@B`@uC;~8WtYQ`^jXkvA#v80qwX6eB^0A8Oi1JMe=n1)>p(hE=cfjoO$^;gpi(zt8Pled!dzFnbOF>`&XK=^?3%}MZ2ED1J1bm=&Kw1D@U~n`9i>+zf=|^^4z2b&nh=VUh9lZ$bL}C8p@#U}bRI;8MP4!oBq%(Ir6@)U2#RD6h@`a_7y~loFxncq{@<Q?!mpZ3=uf2j3=QyMI_FdTweJ~*8#b?nnmAyqSU`kGA04`uylD$I=y1Nvr9(V+v)|3$9VFd^P`b4M*2-wIgB=|0}&aT1BX<YTjL5bXuS6{`Y&C(FSx#TMe-r6o~&Z18F0Tl<AQrLqp>(uYo=3}(47#?YmKVeo+$|L0@&-^}V`d%!S?~7>rLg`>iB>!9)x)=bD?qe~?n9N*`o@Vi`!Sm~yqWs)$#LoSoR$TY+W*O-NO=v=-To*b}p!_GZo#apZy9KE842+uM&b2qC@6kY9rR6;{IeQo^2FFjkBqTp*tq?g~WU2A04n2AR^I5>IfhQPQf<-G?Km}Ks^KbV&eZ}#?Ge&oc&CAn*QtldQNj-K;7Cxk&t3%85=1}b|8VSw}xR#5BEeDoO!1bD(g-!Go{o%;wavY{oJD__+Cxgd5S=l>L&pEVBR5K#r0EvEfIPTnsWC7#}?)hb4A7@12KPnl0ujpp>=4M(Z$mgO!=b{3LvVhmBF`HjpYm&SXuDs*L8ccq~O&;y^_33?;aZ(|8Qjx@ikRa2jZ;0RmG_z0!09ZrF{vu5Hf|&#(ZJkiAAD>d0f+Xd0^ulLIxpsgVm~ws+Xw5Q@CsvHq((tpbvF0pnp6oE2eq9M|mO4Oi0)TTlMiO%^W!PFXlSOLm9Iu18zVy71Xhud4-{sgabCsn%N;7afp0b#$gyIZczr<nO&xtMoQg~r{1kSXCMBSfO4LSuycs_OMP;Pl@naj%P{n)#6P6|t~+|VlXDYr5Hw9)e>B2a{~yRq-0@_Q{E$Q|i{>}$(BnX-lJs815BgxGSP{)~ai;+7OBVVmre`1xc(fFLZ|s5;3$IWdG{HC-DbOJ=vwdA7wUzuS6ifIfChkMF%0L;hbraefm(-%`+7@OI-WZ{1J_=(zl{v36b7-Uzq5@@B!MpHuEH{6-StuLB|LRDe~jREx+E(=>vW#qe45Do6Z@^1nl`FT^xe0v>RA0T>e*ryW;?=37R`7TESSb-M$-*y>y*AGLtc7@oW~2b0@V)&SDZYxG+pW)Xel{Ye8Njte!&N9H3C9B5!RuqDxRL3#FK{UWb^S{Wc3`XupNs0`X+Y{wL}nAB7(#Nv1}sKh_m1k*G*a0{8<O})v8QtXzwtWOD+KxC|&r<K_cp;E6guKI$uMT047Z9K1V92#j-ZFh?8%QL9)jo{tmh1?vmw{UxiAT&HPdJr>b!EN{mFAKR)=-y(Uzw~M$06FXi5)zMDA~t;i*lVYSPx}_n5DMiONyGBujvLa$6cE~>kW3dSb8xZ>0;Xx{T&a;!Iy@JeB1~*>YxNxjMT0^*CZPyTg@xbXNdPU*Z{06|t;8Juyi=4;vtzdY9|3<6Ip_xXlEWju4ty~I;<@r3qWa;T#YZ_+%c%&7dYm|TbJ#h!2^mGksKCQuG&u95N**SFXF##(nDXk$xD^AqoR84UDKIRr9svZbC8I5cpg{vKFwmCxoWax`02f=yu0z}atB)Xvz;u`+_19|1#qEHEBbp?CI6S@}d()HOgK4A`B7?7xEltV3Zvs`4AdrDLEG>aD&!)4Pg+I=`d?Ux492*hUh^rpPNjDBz@dnDAifD-!U29<_`;ZHoHBK8+p7UvVYy1&@5&5xar)rgxBcGQ~6Et`)S6yf?3cgm^L3WUdz)v{6kwxaC!i+dDJjemL2F!6K&M<2sB9!a`G^D9ibX$S*j%69a)&;qHzNvttno+hu_K3f=nMMhrSD=B=-Zpc?*4sCe%G<iknPa{9hhH^$LuQohLuu&Na@*rKqCP=xnXl*f_`MsE%fV<3w}m>9l))tf$c$_}&v77?e-l<6GtB&CiJZexqhuB;I5Lwi4svw<2Wz-gAS{80g%4l~D>d2P+GLIe#*m|o?=cuJVQ32;B9dD#Ja1K)jM}egwQqc7;YtD?1XzfA2IBUFV=1HzWRNcQTdTYY&mQbmk?QL#V;Z?t0aoeLCoZ$xQ#7rK*WH{WH`RQ%PWX0urodMmz#uMsHM=@4Cqx*sqkm4+K)7&g=9K64XS+z^u^mx_TsbcDWSsjzWlR*Z-s3v)qRYrYK+zEkMX0dbX<A8={DcJAGDlL4ae_O|0EwKq;*(uCW8YRExO51Rns5c&Z#MIApXaIzwH1<YLz5+8qarNSzn^9+h2)4pe?n9;6#o*)uEvwn28^!g;0RmfY!povsR%|>T#11$pg-NsTfxjG$rm-{kRs~yhoMtkMjSFM>78pF6cb*al}>RT=oA~;#JX{}Ag!g4w~oR`UY&u_4(w4ESU!o@$X2>})akct+fi}Kdf2}i=B2FW4oSQpB{l-l_=0!R37XE~=5Eed5x`q<i^`L58U}KB8rHbqe9!~BhAmTvakEu;KOw<1Q5RnyLISkJL2kk;!VCw80)>mA#l1)2$;idAQ$v{5GeaA*!ekZc8j;rx5K&1}b=bYVec>^f!K!SEeF%IAn9YdS;2XWb<AaMEndyo9Z{&H^U4A!#0?!@J$%<KBUGIQ%Xs{s!$8Plei)c>X1|9v+J`n)neb@+Dk8{`t!MX|j*CzB(Dw+je)JZT=kg-<kS5Ih3H_||63EKgJBfYADRt5ss3b_1#QtNWv_M5q!gZzhm4#ZVU{_^y>kWR8zf;d%KybCjXYhw~2b&qO|r`!PeBF|DtP~3{xCGo!nTNMNG%*cfy^Erlhstnq2k|kRq(kcqQD8^o=J!t%{Pd)Ec=>P#(c)6lQv^d@)u|Qj1yOvB0Nu+7!M3QDeN|oSonM}c8f-`Ym{c0&jd^UKmCbZvF&y?O(wp2K@#5}{U_M;iC76*P;GNy1Y!L7maoarUR&wA_!h;xP&?50jWgUlc{M$V^M90=SprNu0lll-+RY(uPNC!sZSLTz_mh1FG1yPLH`<M!xP<thf=Qger9ryItX7}8?5U5#dGqjC)ahh!sR4$1`GJ;TA_|8N8+b+KuW8=VS^2`*5J-heJV1h!-gux1pvPowM*$sj5$`NXJaN1j!2Lui&-Fi`KT6V*y$1C!pt-*L|5-L)w^gsM>cWk<1!aVvfeV91pM1z8!A3E>w-nM8t^oG3$vt}X!(v>{Z)<eDXu1`=olQWPi{JVZy_gd9<0u}z~CO9?<axC&-kPz*5v1f1V4GGsx_5Rr=kla_Ka3S%x5<LgA-&I54##3c21fvB~0E~7mWa&Adk7lntN)7p0kkFyG>j_{?N3$(zioJb4>h0Vw<CY#e@tiV*pU{X!eW<iMZN@PuSwyeVR8nhQ<myU@zd(g?&Ed^UL^Kp1Vp$fcNx(^x4yOXe~R??u#Te%2%0)cvPKJvMzNqx#$_D#IR9hVo}>I6=ikaA_7p6g39I!tM+F?t4b4%5m%POb~|$@U<dpb6vCsUbU;w{Uf%Wk=wN!L7)A=~6y3NZHtl+vZb>;42wS*g+&&Hj#g@K=_#xMWJbK1aa2<t=&)-2SoHy=NjmZZQcm%=rorMC5nP6J`?B<$(;d7m^F$^%FW=8cjd1J4d&_!fgNiEgqMqTtE5!NFh?TT5$q(Mbi_m;&!|R`jOdM0^z);F#$8lY!LXEF1T9?!kI;N%ERcN!Qi$zWa|Hk+C6&;3eEw!&QgCZzVNun4JcB;;G?9b=Ent76$Q0pcDm&vzI0*Zwr3k_zY(;My5xkKr1^QDG$Q8qogTHg?6rL9?>1vopALeibAeuXzO|Oh~)0Nj0Tdu92LK9JA1sxxoz;P|r*9~9ynuRDXL$TajONJ6(4A+<Ph?5g~2XBKoJ#4~7?gke>0iUe7oGAW|=2o(C;s9f^oO_~YIteedZb+D!sO$l}X?9QnGetvfO^#@6?62M!yI4WaBdI0cl?K)On?`6F1B#q~=4GI9v~*L)f%xjfNt$>dk}$tIy3jcRq@&0Hnt5io)Tad`RwW1y?eiOeCB%5-;aN1TEB48G;pm|-+TTec74kn2<~+=BCYu|XBJtP_Q%qZU_57(}%ob(-7Rw!O>Ps|<R3?e08xCX^dGqq}{aa~ev|?5q^tUjjzGu<I45+!<&6U_GY)!IoG(%iC_tW4J!con@u8VB7@t-87Ar_WtdY2{)&ka{PA_qe&u!W|@Mle-`t}!MWCc&eYSgK>Ac1Q{nHnD;jIL#`FID;+5Dcfu-;}2@f7;Y=m^)30S(v^rvs7BhDfexGwJsb$h%$;gv88dUHF$Odk^+mg{&d@w@aQ&%;QLpz)pCcdkS{zt!6oJPB94RAg8U+Wfr3RiFU6kw{o3oy{CwIWD$y}CK!DV@+{W#|4my{`W<&uqi{psv#c5^Obf{Ei@K9|hMraC6-+}M}TfB!!msg&>')))
_DONOR_DEFAULT = "route0"
_DONOR_MAP = {'BAKERY|BAKERY': 'route0', 'BRUNCH_SPOT|BRUNCH_SPOT': 'route1'}

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
