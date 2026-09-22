# 🧰 Reproducible setup
from pathlib import Path
import base64, hashlib, importlib.util, math, tarfile, zlib
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_colwidth", 120)

print("🧠 MODE      : controlled challenger")
print("🧬 ROUTE     : frozen V22 / 719 actions")
print("📉 DELTA     : exact marginal execution-loss ranking")
print("🛡️ CONTRACT  : SELL-slot permutation only")
print("🏆 TARGET    : top-1% competitive robustness, not an unverified score claim")

# 📊 Upstream measured evidence — V22, not V23
baseline = pd.DataFrame([
    ["old public v21", 1, 46, -7839.7609],
    ["current route only", 36, 46, 1838.1739],
    ["V22 endpoint price impact", 44, 46, 3508.9348],
], columns=["policy", "wins", "games", "mean_margin"])
baseline["win_rate"] = baseline["wins"] / baseline["games"]
display(baseline)

fig, ax = plt.subplots(figsize=(9.2, 3.8))
ax.barh(baseline["policy"], baseline["win_rate"], color=["#64748b", "#0ea5e9", "#10b981"])
ax.axvline(0.5, linestyle="--", linewidth=1.2, color="#334155")
ax.set_xlim(0, 1)
ax.set_xlabel("Strict-future replay win rate")
ax.set_title("V22 evidence: route refresh first, market controller second")
ax.grid(axis="x", alpha=0.2)
plt.tight_layout()
plt.show()

print("⚠️  V23 is intentionally absent from this chart: no fresh score has been measured yet.")

# 🧬 3. Materialize the frozen V23 production artifact
WORK = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
MAIN_PATH = WORK / "main.py"
ARCHIVE_PATH = WORK / "submission.tar.gz"

_AGENT_B85_PARTS = [
    'c-oD8XP=_V^6>lp6uK&Z(4BoS>k&+VIg5hsZ&jiq2nYxmKl_7moU`ZLd*{W7bXVv~T~$bb|Nh;M#eIUyaF%bw7)wcIln-g6U%wmL&JujgQcx|Q',
    's2RQ{vs@Yyw^OX0A^iOIja&&n-O%_QXGxm+m@b(<%eyZc+Cfl#b}V+k|I;_vsg|_y@bQdpF?R@I!$_+6O_4T|CGb8=^GUo%O|teMq9F)ANAT_%',
    '0;k!6vG*}5?~~LIU12!EXE3TPsY{<GdfZE<b-f-Et=2bF(Jb?)@5&svViZMCmx6J<^gd0WrYidzgHL#q(+uG+pJaKcEn#UemT+IeO(x%Vs$_kz',
    '`;Y6V&lD8#LsGp3du$1=!0m3!P&D(3_y(nkqQpsz;*0)_$9^WRGL;3($L$Q;6Is{bJpp@5@g%64K2@-<tQmqw^oNfZ6yf^mN!k!h>EMa#39cEu',
    'VEp{{{rmTCo^CY5^0AC5q!Q0>oTl%e*K1Q#pVu44T0O51io|~V_HACm$a=Rk^r5$zKNXGPP4GJSllKI@(LLHGct`(}%_Ofkc>(<9^ZxGt|Bw4H',
    'WMmXu?KS4u)&|Hd2*IgCdt+BWRIHN<wi{!AMI4;dW3$Swd)8?@of*OCM37**CpGFzszr=7XJSUgy6W%312%&<Gs!>)KH-%zQ6U8>^nZ6!)8a>w',
    '4w1EBVanvR2CrLk4zOD8^5Zhi`%ASt9$Wa!{y>=G^+agRNs|w)H2M(4Rc4eEn?d4ej4Hssd_Fq>9}GqhWT!IHh8q-bj_d6%=4P<$gH*)GvTCp+',
    '1Iq#>^bf-dilOd!PbGyDp;VfKaHf1L$=l^<-OUwNrk05pf$V|&h$!rwwZquH6jvv`g=uypinPz<<_?m*NaRe+B|aV`#ObC<w9{%LsHoGG)#S|Q',
    '$POGd^OJ2m=S)Xb7^#oiwN>hrj;fdKh0X`h^VFX119B~p7Hp1=s0t$2&845W)@B)}fJ_F+3-Z!kAi-vTu`Cn2dLRG}vAoz&m&TqCvmvqYAO*n3',
    'xL9sPtsbtxdSOJHa(<5!Xyk&U1v`RR35d>|7F%?C96i}9#A!+E$wzxs?Bp60LJkd<8Ji7$B-t}6cN)m_8H%Q=1%#xWUYh4g%8ksyeq!H49lkWy',
    'o#-qx43zL@3T~vs3T5`9R$|c**mf_399{QPi$6&5gR)%ImU2s;=t!!it~aqH97`_OLb*GbnuCSI^o1a$V|z)8ZF&_YzjKITr*%?$J=jWGU_Rcl',
    '@)3TIigUCOPbhp>9V?#u&Kv#!ur3Z`EABx`xQMV29!G*Xm1Nf3riKKI7xENBI%1_w1#7E)&23tl&A3?u3Lv?zKgE$!mesNlsl?i_2zD}RvcPD$',
    '$;h0=o76P2%!kQJzPHGkqzKnodouI4FNIo3EAX*(I4zD<AgH??J*2mj>GH0(W|Bc1YJ`HYQ;+WAB3bgEjVGzCYsFGcxMi`Zt_I}tzUgMMnr%+d',
    'ZM@x)v5~s~asPJAn8<b-o*+myx8pAPQD&7*WlQtC0CUowK`t?ij<fq|=VNTr2}W_`O+jw9=cP?HC_G5frkxzcsK9<YHG1}7v7Jy`Bf7d&k2VA=',
    'iA+H4196yd`s;XL>StGLyi3tas4q_slz9jQk2c(rr|D5YRyo&dr-Lct)nqWVrh93~&<EooUEDoLEi7WJUbtjEuSL>Aq8?g?cfox@*-RloF76~K',
    'E?d<)4aT#hMZ7pGXr)y(c!|&*2|Gm#BiWJzy_J6o#gZgK8J%4P0MnXdr9;WGe1P?|Ve-a<lue(>5<Ug0>3XZI862DiyT=uD?AzPA5HE~d-G&_j',
    'L~Lqq^YK`IS`S>>z}%m7!Dzb5LeoHhCWeJ0-4c!;eICi!{z;c>KGidT*gYl;8q9)P17K7rZsM)tsmXMzCHr_rWZ@EYry<SQu3F`!HVZj}gc4jx',
    'YK6L#J1{*7R6}}SY#ohee2~NP2ZdzDr6EW`<fM@kx-G^*a}QElZM3WK!q%$UZV+j0z+8c1ghZ>S&L#^neyq8huAYmCjny&1t+T6CfO3Jb9c_V1',
    'sc_b6-Dngb=QFp*!j;&tt}aizX@1rgJ4J)mh85S&C6uST9|P?w!l83GYw6&iKdNr(Z7eLFKibtmw+>42bwQ0K^22aW>22G)4rfMI^wEuvw|hVy',
    'AHysL7pDVp7{6dc#Hv~9kzEa+GE1E4m{p6wr<L4rno}cu2GwwGQvzFYOV)M;mOc4rW1E2nW!IK@=e*R{MS|X>hsnm6%TU%w3uqLc*k}t$bJfDA',
    '00v9Z6#=?iY8@jre+iN3SXxN7%!HmPC2K9jJRYGZ6x66za?wQs3N87i85j=$;?f>sZD2Fa(!K3qEcwg3Rp>aHg`{R1ji1F#Zc$9d`57U*2{oKT',
    'cS0!l#5VK%T(Q^33)*Wq9V;lW@)j>;48R6}PB`zD@ivn9VDU|()`~QP%M0BAa%J)0IIIu|Eb#EMp4Mg<=a@wQW4T3NVb{$DiM>d7$#H!=qbRPX',
    'B35Bpwim@s2a8l@I8PvBBdbHDazU=v+65dIE?k~HnRu=-8v-IZ>CL6;ywwfLFk_F$l3ZHWh|0FyLAqn4UBI5ZLXA7ksEEY!m8`g{oT5`JuF!d@',
    'X&7-_FQJ={!e9oT3=x~u@lc{Zn2eTBE~Qy#TsOq-@`yTdVkF|8I8A0%O~lt=PqU?bbfb)P*y4tjLCr<Z?I$1@N3-itb|e_%vKET;(%GfH%x}0M',
    '-4p<a=6MK_PMAv7Nv$;r_h5%@tOI66nnJ9(7)k>X+|O6AePDu@O0L|UArvA)C+v{f!Rn?ho^je}JxHA~tl1^gBc-htlg%mW?d@dJGyb{}<m}0C',
    'Bs8t=y1pV}j6b)DNsDmI0$NW#odQ!Wx0F+lGPhi<6+4gsWTwxH5zt!fWqs5@%0#|>aOanq0!CXStf~Ptv}y$nAiYztnw;6dSZ+9=c`wUJU8G80',
    'dudp4?LHf+Q?3mh^=3Mp-qk~y;^}OagPV1hXCf=pzYC=FPWX_-&x?sv!m`?2YYZZ~n#zvD04<vq(e5DVBvipFX)~}tmG)^2@;7F7z@ccZ{2+z3',
    '_=7b#6l*q)UEm#`o|F%CV^@Wj{>H%%ZJY*`OKg*HYK=u?e;o^aj3XM7cTMof?Qnjz1kzJX^yj17)(0upS)N!OhSOkETN$E^YBJ<yTF*@@2p8S#',
    'vXa18u*5Q5@C5X?Bs<Q}=IKC!%tf}SQ&T&6b(d-&i9E|}Q#lt+jd}Ad?SZNu4p6ABEswd5mRpyXXSfe&%2Ed4ezT580^l5&^`7oe)S-f-r;|-^',
    'E33h$TrX}?Bf{z;*d!x-tz4J}vI(Y^)4a_!v>VhpVls1V>`)Gn$k8rcCh2ZjUhe~Rr*T2*?kcNRrj=|`DiNi^=2T4OX2alSzAK%eZPn%KyaFCv',
    '_Cczo){==hn{4c+X^@|)xRLL6PLl1M=MmwR;7v1Yz7c4H#HN=UO-_0LwieGdx)q{mr0m$Z&E(QC)^I$F%udo=7#xJ0d=3DrK(l&U4}{K%ht^`k',
    '>NFdR%(PYAKm&BNtm>)GAXXhFjGp7KJQ-p;vq>OXD@WG}0T-y#rn^G7A9A7Vj~rY#{p1J@15!vECj47xfYu`lu#<4TgLZbd3@bQMq5>-Ao)k#x',
    'Y^Z7=Dq?xs3qxd342)v|Y<5cGWVyeR)zi7o3T181#6!jL0a&w4JHV!BWPHia9;Cu?rrn{IwQMH|$GJE?Y}Y`u2~umTA@1c%pQ0mG9T$itMa@QO',
    'Y}=edvfdK4amO~+qh&s^RqeJ@7~A`7Rp4^be&e!clqkGP7sg~Q#Dm-2;X$elu}Ydu36x?VD>XP3z^n;sHe2;tdJRM-WiMZfz=l5}^pAC*fyUy8',
    'z})6eZGv%HA*NraN{l1qr-e%IM7XUcOhok4Q4SZnr3Gd>vr75gtUov8U^ttt!&O;<H&C{>IN??d>*N>PJ@?U~H@hUp$29+N)X8@b__!F3M+^#C',
    'm6muRhmOegCR>zRxoA*75n(Qr8~6Km&r27QLoMU9cio(USn2drrQohs=EzB6m76!)Qm-Ud{AGK6XloU5Qn7ZK+-PKEu+6anAI#}+u2AuD2CYQ2',
    'OnDlpmaM%jl$hAQ8iW`2Vot|4+w{<A7Id}!@|b}%WHBo{C&i9t_4r=AB50Ccv*pa3t?{A}!U4)FR~3LuuzhjVD8R~e+7Ou3Qr%#gV9#wf#CS=V',
    'adIMBT~hXFwILQKr?E}8TiITNtj7-agVYcix#&?urn}DK5YA5gsRoK>p>DWS8zwBY<)6&fr{E!8%hgi3?IJHFD@P|qV(|W4v8m~FjrONz9L-5t',
    '%+@2vKwvX9S`dGrm`Y^U8G_Y$5_phmmqz<kFxt_8TJSOpL2`ZxcFC06qG7{@>DETd2J#Rvk|~G)4V>h8ps<8gg_;((k_3l>G*V%6h!V<<yN*RD',
    'n?^i3nl6H%;Og?a+@|$B{2<j|*Txp!T|#+2#v-y@=`Gr^ivOIhk3-<BcOf{*-wCMb?85cRDJMT}%iTo=awrO{VDh?QPNUgqMhfJ201?4yTu%0J',
    '`4mkqlpa<$?O1eLlb`-nU9ZV_G$4zShLT%ZiAjK`t0BK$RCQ%&%UK=vU#KHA+a;<ktTf!)M1FpTsx_q#LYe5X7%}0e-rFn8$jlO$R@=@}n+SyR',
    '^qI+(*t6e>%26|XzQiyp78?Q?c3Sdgt@o~MuqUc*V7p;q-d5~lL~?Qh6=4<zfV$O*+|i9Jr523of=35Ubvb?dW-T#h0{dQJRPrM#*QY0rVG>7L',
    'H7gJrTVw`-TC^{p7nMP;kcaE%QY&Tm_R$W#Y{t84R%6g8kvdKe1u6pi<Hji08uupCbSTcYPZLgJS1NXTrWQg#S_iv4kmGy7p_G}l^FleM=q(`H',
    'zQl^LBUFg(j8dR5?=A5T*SNSa=hsXt*(w7BH(JB~kH#xsbwW{`mdLqU7;DXP5}|N<q2~%^EFseb6I2l=>c-+uv61SdTQJx^$lHFNPs3n3Y{Ho=',
    'R5{F-ZixwIFH|SC<*T&|Iue!@d03<tz>^At%91}7tpw-F=rn*&hy!mT;>6i^3v{T`u5PrUyDU4KMB5GIXPpL~Jg&<ws=>>Qu$_&FemJ|Q8v@{l',
    '4(m8kB%nlmTCB2M(#3T0V=j`t;<LmaBSfkUa~HgEA;Zp-fzqJdJnYz6D+5ft{3BEV1M!1+*kFgkEISNN)^elQPWUHBtyXk#_Ryax`yi{rG&nj$',
    'n)`CoITTX~wK&BGT!|pzRCAN<*7<hMi+_tkXhpz*`GeG&V=EsB==L}&%BXo_geQn}RM!`Awj3x4;>V8KRTV7gFNJl#y*XC3ITB&bZrKltm{F{7',
    'fe;mD`^TER3ew9=111~MrR3CEY(F!&OobRLFXffPrl98~6_ln8#n0CVX_(Z(?X&_n=)z89d6(*87cp-W(^tDA9hsfumOCqH^(9jeW?9fL0HIxb',
    'Htj;CfWF?5Om9>><@$$Uv`)>Uoko7x%PqnomCl%rL47zD2Q!8rbX$IEFbo;Wpb4xxyS4BnfUr#B*g8n#`m(p!n%i_kUt>nu$PM-7wl7&4PHLlY',
    'ER48uGuB6GbypmWkkt01nEqCWkMxR!EFO$AP}&`;NW~?NPGgbP279U*l(TYxu*;1HsnxtnX2`Oz*2i0;6^R#7Vbd822(kg=`PveSxza&p`q&Ok',
    '0O@7;6feb2F3=bkJJXT6%M|0=Zon(y-98}WrP}=5d#<5bTsIf)x{^3LYn*9@LxfQklqpUc^?2nZ7HZRk7-38FJk)gLbxO3**ns70<Lty4qY`>#',
    'EvQw7pnXxnii)(%cemcg*3=Vb39Vevh_bGt=VwnSp4ax5D&McUiRJVF(oJhOH2Q@qCq!5Ca6Z;F@gBHono)r(D*@CF6<pfb1IKic<{O22A4;9A',
    'p~G?p1FCwcTA>bgqm8~2eA=xE8$$=vW-Ln;gH;YRs%sJ`1pL*MfAXBwNV8rx46O4du3~H0*>7V3OYu+L8kj5t2mb;A`sIn7EKC#oligd*jN+w7',
    'uZON*?5EeOn7TTQqVZ`NN|Sqk%5a)EA{4yTGhK-mhOPDK)n1C{5MqY+qu@Dg1(H<r(n%fGwF#XToYKB;q{%iywm_r99=oYMu%+`$s0a>Q3pEKP',
    '$N-iH53QOttS$M=DW>O1W3ZcaV#cDXljv-Ba5q|V8-0-CqFO04vLf4_aHeU#S{m1oT}C<|_a}CFER6BvxG~07X{|Yr75#E!drA%BBkW@mu#rMj',
    '5SzQXnGVFHC+mhhpQR`)oH(V*M#zOH+%QiO*+WbmFiyNSZ7}0*CNY{?m&m*aR{SM<OmKZU77I<gDY*2K_2sg^ME1>Y^jHWO+HS?+A{zC|LMn#Y',
    'Q;{mLy8<&Wg^?p_Zl{_Zcebeu1cK$G)vy<0IqEb|tJq-$;ibxKM`l6?g~sHAoLF?tOa*loCUQzWNL6YooJS@>w@VKc!w4_({dNzhV{UhyXkRWC',
    'eGIfS`Iypo7ps}J*4fke<gX95@sjOKG1Z)*doZF%k+`xL$L8JKp6R!9dn{cd4}Pt%>Tk$b;sdP;%UPF0jChh?4El3EZ{}DW7_JA|aI-#HGDB=Z',
    '8?_FTYR8|FuvCQ^pN<Eu?N3w^A{aSx5o8-~Bx5St4g<q>F}#ICWzk~x=lB|l+3WV4fR*{0XvIS~JD*?1xQ_SZZ1%KI)C&EzK<CQ{FdG%odd6X_',
    'UZ>Q3wlVVl%U-B|R02?)F5*K+8|@E@KUZ4SqFH2=flYijQxh&#vp0LsWM8GkxYU^|IG%JX%wo9Nf@(uYsOGe+tf%-X8$i@t1TXOdbq=UXu#-oU',
    'P<l7b@?;>rL5bEf+35$;8OtQ{yX^#!>75fNXmA#B5*&Kc!+6PGV#o)nTnWV!X@bz|9jL95n_Y@21q|imuuc(Pa{bXqA{85K)QSp;6^f1y=E-wR',
    'P!X{KZv2rEnlum0qH`!ZCQ+FOfM5nfwAR`YjNU8^hL*405MNN|P&e5gh>L^}${e$ix)5?Rh!Jhp+;I#iim01a<B=Q?b-R-Q-pnoHyUT9q?khZv',
    'zd8pI%|2(E?g1Q?qcXJ1$5voN7)nl(jj!vw-llbO=t-*EKFrhOeyALiXHkJZCqsErWJeth3uU}iUXlkJJfaIau=1}5$r09_HKtsq+7ZHa>ba+;',
    'f*oxVM^z5Vt9uQPZj&v#6=kQROet9D*c6iub(wO_KV*%>d~;&9j^E3=lZOrmW5Q*9V%j}H^2@tQra{cQYQ;3h+O`{)BRdkok##8uaLm)m&rNH~',
    'T*wKc1DN4QxINp-AKg+g)QmRg{#1b;h1Sdg)rSInUc?1<WC4Y6sL@*36-T1RMSE(sA;!w11A)OaT(D}2BU}XAv1B0L>6|y))A~WG7=cH64w)9|',
    'QlY$ztTOdBR&L_G*bIYPE3!LnR)pR#<!=C1w08d3zglw5l@)FE0S9on%s3vdi8%!XEIiOoWVU9Ihx3<m-s+T_C?AL!&D}8BIcMo(i`xg?kdW<*',
    'y=~9P7qUi*Oc9#9r|MzYNfu|-`Eb&;;J%;5%EhPT%e|1X=mZY6X`q>i(ffGN9;llxJ84**p`4Xejge96fU2c_CCUe}U8MxZ7An`Whvh<h9C-4)',
    '>DxvAlyErpP+*I_P@#)PBs&%B!EB#JtlsDZvl^e8&53ZZqL<Z66dD?9ezra4JK(l+afL{C+ONxptUr|8#E9;wIDm9X*i2fTad<t=FzaXSIvG~Z',
    'gZ4rBh^C!M9X?rR6KRF{WP!Eu%X(kI(A2ywE$jXc<-lpg4WQe0Y|uoK#k!X<C88Ux!49j#EUWZ7{z4z$s2dI|w^oPHL=<1$@pDG(JLz>4OPe*o',
    '+p|XkuAS=HLXh0l80S=`z{1C9O0W>s*YPP`OZ%G+T@K8K<Ze;oiZ%Z$2gfT#X1fuN>~bOiZ5lnW!oUwF9Y_gX)QFi`p%t^*tw}WOrGTqSXCATp',
    '@N^36mzBQ^`XO@4X4VuzjC0l{uyFc9Xab2@MfV451d`}124`pdAmwGN0kWQNTm~7I0j9D$Z*xRREpoGSFiTF-7p{{GGfT+Qo1uA>cMb7aEekoP',
    'VjerI#$g*s<fDYUg^rTwl`*q02TMAZt`US9$_|aLqO@S}L8^WhtuEgnl~%21+H>q&T9>=-cKk6a1+>I~;+Acii|y>}F-TQ}Ft`e>*dhZ()bcWW',
    'Se*eS09^{?X}?--I^p0ti>JfOZNRapaGb_V!(Cps;n%Y+hSVElYqwn2$ER9V-8P~UWOf7TXk={fKT4PKHtM$c;7Jb(p#ac12&>DG9ghm7TxPLY',
    'Sq0$rOiCjY7sd-O&3;FXt+JyK(3fU|%NXl9ZYOHT1~&N7n|vgavl4JIF4h*9P@9~)i;a$be8rrdW8ZapVU?E83?k_4dIo4mhN$E!YisSCUp{=8',
    '1gE0Ev<eNknO3kh9f(WEAvIMH*NUGAr(4}YudY^lD<Os1AG6ZtV<oJ|#xkR2!@#x$gxh9o%iF_=Ii5Jpfoe*LLCgb9+q;DT_Jd^OIDC)_F!LrA',
    '?#Ci78;;3vwKW1(==nUsYu$N}s4j;=GiYT;(;mvLm7c#}Jr$*X*N#nFO`B)Wu|y0UjpySFf#Z&~>DZFAsUOx{-e{4s9S@xQnx#HS`4?WYyiT?>',
    'e+7xub5?(`w<5i|S1Eu5+KfjW)NhS1+df?^1rNvbHUvTCabedq7R6OF)8UNyw93`Uu%4_g+g{+@p=9h7CRRC%7LMIOaG6>^AG7U5gUQh=JOV{m',
    '%PgK0!Y!!b1OPm8+3!QaExJAAD$3sR!s7DWOddz`Np%jSRC-!ngo?e&iB8q2kK;%d&YJKlsW$Me5cdL?GGg$ktn`io)8>L_vfYe!P92dguZ2>S',
    '*Y{pXJqd^~p-HyV`*3U9I=$&3mtJ|64Eq<{aI{}^(ZI+e89Xu%bSS=E$%$Gq5;OAjgH*37hl`yOyM>aw6TvQlj1a{cq?cr8Xl8PmMf?4ED{e-i',
    'si381Two*`hs3tQ^>9COS<kadf-5b9!(jjl%iUpf44%iEk(mfr$F)FsQ@P0I;rM)tq4F6Ti%4fQtnE>@*PK-PrdJd74*(k6;4_?@jzKB`xrJ&R',
    '2b!z0AFpH4R~Mz&#md?R6xl|@Ap82Ij&=NY_KX#b9*@l3Mz~OkB-8y?XYJ+c?Umb{3@DmkH1-p-*C1n7`eN>2>e4XEiAgeV)Ep5#r4B$`<)C&B',
    '9TCcY`)m|s0~a7+h+&jS=0q@ahz#cWSdh!8(J;a$cb5r09UpRSCY?f!MRYBMfGLhare2_N94rdey)%c>DR$P)sl(t9BLpO{Jg(D5B#Zka&jm&F',
    'xjD?*A>Qu>%A{EH;?M`E5u_f?jkaVq7)LnqmHzo7?I3g@W5@s$QvL<(CR#39&SAVC1;ULA+d!%#vawrDFjE85f$5}|45t^7Wq)njUU6L`tPqu5',
    'ziJ4jw`l<T8M7#Cpn1ID2a3gdRL|DI4Ur(_9nzdf^ft%v(o78|;~j}i?dHiIgw{z>u@C88tQ~Dr^syXR*UE4wb{GU}VPjtPuS!XAeKNy6v-<o&',
    '#>B=<MW~jBYZ-|_Si78c%It2EI^_KtWS&_otu6zTf}sN8Fr<du*P|<N9zZ}IuhzA89pm6b=Rl74%Yb+=)5c*LTIyl8HS5HWHMR$7_WYo$$2h)K',
    'FBtA`8VSAa1?%p_tm8qPsv}505#L7uS%6!|gFXy$jht!|PbWq@BLsGoltNuzdF2@-!~Pn*zhvm@0>W#hVUQV6*3PQ*H(?bSvzwk*B$K&1KV!}1',
    'Vzw=b-K4VMrS3_ogIg1K`kWk}qp8be)hx#BGP{j8<woZW8iPn8JX^ZhgOqET3T7-SsX;3mYL&2kh8_5GNmkn>N7mq#FJq2P=X>XDBo~FJg~I|M',
    '`cQgdSh<>$CEU7AouL7i0`Zo85X$xGxL1Obqxr!uW8$3NbhRvA{Ft)4wmtc1DC<%^HO$g$)tT_wrI!`T<?*HS+%*So#ZF?zwziEN{Sj<QkLPH*',
    'yvWQD^3*9#<{>50YZ^6Z8*EiX($7xZ5z;$~*{NRO_7c|6L35e!RLk@7>*-9tOQlxxL#R)V=E;T`mAwjzSY!kK6?#yU!}zG%sZT?WerD=a(2L)-',
    'dT>4rm8!avoyuL&Kbe3@Sc~PNRx}DpiT1vCv9J%4O|Oev`2u$J!0^d^f#1xshbUv1g?d48SBD7{ZV(f#Gyp5Jy0r<VmuL7`wTNJx*e*te&0vDg',
    'Te-+3y_qJ^VID(5IR#P~_Y~$YFkoj^@w&HQ*VGndt}~n(=@|4Nb@K9KWxO2FVxjA5dOoo^^|b0jZCRz*L|mPhr_vViwtH%sj;7#gATTbb96grY',
    '9#efoP6gB)zr8Huy`Z>piE?(tVu$=<5VQb%i*Ge6GuZ-9BdyC;q;<-s(p^I*Rw%FV(wa$93DeF1O6MR6lZclS%{N3RRZ}%wYdFZjwG<*T+X!u?',
    'vH&%fEJ|Iy*qBi;zonM-`3FY8gA6T5flf_Y&WgzM=>gP?_O(r8hVW)>2SU!A1?|JA&`Gby0oU3+b?Oy<nZrQd?x)igq56&4(GCvSdf_};@3Uoa',
    '3&e3^l9BY*Ae+*otlOBG4C*w81`VL5F^$cSNx!|!7VZ6n4JhStpY$U`G;RtIkxlP9p)p;5?z3_?HJ>l?by(!!s)#~iB~2aIC4Pyx5uKPv%u-<7',
    '=k&pG?+{4+7|T#GjAiP*mE+1WKAGIJ)m)1T_0!a@t(&X;M`O^aZX-%|UfYIiWm4kVXCBAlY^S6}gtOy#eimtsGOhX`kR-bmhsclD<;@BRu18ui',
    'pU>L3WW73?EurQ#SH)#`Zx`I7KEw-<olp{B%T1D8v|qJ`O3;uEx7irP_#J?|>0KP@0zs}<m{(h%4maS*IfYNx0i79-fHM_`UO%RoO_u!-ov#U{',
    ')+m0clq`khKq`gORmQ{*IseLwAcXBUbM?+D<gAHdCac8*+HTQ}$DCcq&LZfbdVo){{@4{1CRD3MKJw#9g*TGx*z0Eo`hwEA!^spkF?lp|bCEd4',
    '3^+kplYHpRACM|wg*If1F82dQMXF9JTd-~nu!gt`v`=v(vFzZaVhyWxxoO609iZrhQNihob%UD&Tp>n>k>oQR^zws64VL#s_f&PL-UKTdaI_)y',
    'Li~7KTwqX~2)7sXWRZZ;%ILI@Ducni5|9`6h(sIImZ|u`S-Lwpj_AwLul7g!a}o11IJG;1o`gBFikBPd?PQ!A(Tkw`>N1+G!8UVAh3NRqXx5YM',
    ')(G4#b}4ut5Zl#E46GExC8T^_B1$0Hrc-t>SsahoYo`XU0y@dFpxYk~fW5yo%~k6KE>+NkWPVkFG}6Tz38KBvKOZBt9o~=hy8@X**WrYmk2Kl-',
    'd9%reY9YIiW!rX{*d%y5oK0;a<t|j6&)oGkYQ;fKBfQG5Yqci$ayy@URTd}HEvNuZ!To+^D2>h$k=sqDxPNxO6hvQb^C5ds&j%e^Uqgu!p%+^U',
    'O>z!RsZ>9AOb;N}(JE1L%l9HFyB<N+AjeCv5k<ShoN(CU)4+Us+72T;-S24eV_Ibmsxul^#90G`iNsTRS)&1?{>p05B0Bq?F#x(_|8QIwbkBq6',
    '2X=z1n!f2b5VOuErjf+TALVqsjS0!}>1@ox(-E`Gr9KX0e2D1#Zec2=w5F@J8lBOr-vy^*oA4$d>~r)g)E?IMiXaZ{#xf1T<f&LG+Eku4OYQ)M',
    '{HK@}7Z>LpO6-S2rCPLd<qgS*1t(8+Pp?WROk#oJp`1Rf7^bo|CeA@fB}h*1Q1Te5YPsGqnHt*dJXVms`q9uo%yB7@I}Y0I5M8i54-OVP%?wwb',
    '9|2~KS*O7YWv8Wnw`!18l82M4wDsJ7ggjHGV+O}{G{aiy*szz4g+i3B%=>+f*hzh?l_}JhQ&wIk=f@xjxc(9F`pFIv-)_iEI~fO&?M_(Mqeuz^',
    'C}C(^YK6)wtV?ivmlgcAZpJHZ%A6i8DWNVPh<$VdL|TjbqT(1AY+M_sQX9Fp=w!nt$+&mq&^HMB`S`i<_njqvWWGbtw|Q?+$B22Q)$I;^s4x0$',
    '-YyNA1Uc`O2Br4(XUxYN^mnR8l*sRY`M_B6hc60ye?NSQ>%Z^j*08?+@WDSb-WNq%-mYWNk2@Sz8VtHO!1x<r5`LfijwJmAB)jbr*}Vd$;1^)*',
    'Mp2PefiZ5=6YsF8C+v_Ml&CT>7)-A4(by+~=vS80@7SWB2--xe+qtjy6E+V2$+dSG{{$nd)hp0DOg#1{!+!{=U2ipSoW3nJ8v7!b)W2{_b-S$_',
    'qwxD8lmE=<i(rKqko8u5N(^pf;r}Ax_pcs`^S3!g5cqsZmPq1iBJf|n<Jm)T{df)zh+eBS@#YY{s~Kg!ef!1>qHn$wEYN0@o$$ja3;XNu@<nE+',
    'SZGI61?aCEdy?prOi48@M&*R(WM1N|$N2Tn5UxM+_uU46UU9x7gKpEjyOv;hw7m<)vWzFD@7{NBEjNNsdK{xD466v>9q3O&_xt}q<#YU<#@Bg|',
    'rC;A8m@~K6Il%kJgU<bn$LV#3=cIyuy?D&IzOisTe<5~!ara$hjE!J;T2v&{dO+Od@f?A!@V~zIO2gsz-w*xYAXkjan;zh=8|3XBh%ZxbFQwdX',
    'ORDb+>O1Hi^Ka<)8`Aq56<@LbCrpp|e?xVCO3V}(4+(2N<n&m6^kyNd1>TIw8}@XnE6iTFndl9d_aF7bnNLtm!3RIlT}5)Ae?|O2dcA3SvcEC>',
    'hVgdaL+G*f;O?D=+vu+=n%`G$t`|PUrwA%|8-ebWkFS+5inLVcH^Dsw@Wc1Hu$KY+la1VF2(B)0*SC1k8<88IZ|nJ#6!hb%+CNyo-F~k0-}U+Q',
    'i7TDk2;{BoN&nL^ZbLr>*Ai47{Pi@Oo37_qJsa0og1{HwA8+`e2a!7uzaI2|d#wF$#(10m>#ry7-@o5Ab4U7=yCo^Y+!M`JR6l&WW=d~<XBqp?',
    '^|(KLdyj*wT|KA$f<2G<dMEl|{f*#V8FvETuk^l({@4EZFZcIDiJYKYKCrIxf=d{NX8iDxdtG>3j<2!fcKv7k`QGYcO#=V^T9?6a!qreT<Eyz`',
    'joT9RAHLhzYoXVdy3mJg%wHQx1viWfUYB;A4PE`_$4x_zDUheIDD?Xte4Z9@LwR+qSJ?SGn>Y2{sQrf^^u-w8CjVi!-~NvIuJ{`pzdsp5-c9x9',
    'cb}vl;<~=-Ha7&FkzV4u`OVW6zsT+nr~EhPy-mBhKKkZ?_sxgdTm}BNQQm{aQ<PUaS4qOxmEOJ}H<-I56vnjX*SnrHKB8~d@IZTfoAK8}-`}sC',
    '*~0hxCj12WgMsUQ=plJA`RfhUb?|!eii_73{4HqS#-8qQRp768^MC65hcEmYPak7{My0znt}p*RlybxO51ZJJw;k+(`9JJOFYVdFW3|7Y!ukE}',
    'zBX^>&31lV?N2oys+QEx*k}tsB}>?tAoM1F>FT(?tJeO>8}7Du^{Kn>`66CI{Q?yq(D{1=e_!<*g-_Oh>Y5HdnEcFDo`0OCT9UdGUN@Pg@X(&;',
    'xo?a5_1(*(yd?7XJ14iv-v0QN?mJ7rZp{9E?iODVUSH+(M)~h=u~1Mvv@suo-f$z=y*J|fGZXw@2>#dDb`4F>`1ZztDg19@d|AMa;t$^|xZgtk',
    'ZDr8a6a;nWX_c`A@F3~0NgfYhRQIO4he3SW!%OEkM}Jty_4~(H!?*)V>eFbwFREs}C&5p~e%#any=FXa|Mj13<DM?vW_nxN1JVb6FOTXi+$;5l',
    '<Y+*6PWIhXREPWy{TFoCJ?^Hbf8JZ)$^LB_SBOU{e_g`$>)nH8PcEJV`#s@ZZRY!b;ovT(=SFaihj$}?#ln|~J`&@XVm~9}KO5h#?|8lX3=>a-',
    'f9Uf%{sjuYZ9-q-*O%?*Uy__JIHG@j+2;OzuX(1#D@GSU)eCAr?$ysjTeoWu`E^@|e|klnsA$Zi)Pi0)oqF3p&{s+K&jr;Vv%UK9pJ)2Q{|a$c',
    '$KPSDZ%qHZ4n6q#lP#}k{bwj|B&z=huqgZ=0AVot6ZQhq8@Rzpo~AxiuA4|-Qoh$EbKQ`x&gbm|*VteSs%LNehrq8dasTiM+nuCHtRd~ZDW+FO',
    'diPjC(VV%sQ@Q80XPlmydohdEY~e9-zrK%ndILYV>@O{tUsvkCA1$1hGe20lCgz_EyhWmou1MC7zZ%3l2cEjFZ2SJ-(~jO*y>b8Py|=Yr;jaLZ',
    'H<aOj0)At|i*BE?`u1mRerN8B5dO~GyR`ljb07c2+&l26yguF;{Zi0f{pP(JcF+3_ZRb@tH);^{vJT1gvOPt4l(%1M(@!<Ng}vK6Z=<<}A}{0E',
    '>B`e3Z}L$2TSo9Gmc9HS{$=cT{~BwqmVP~i;rl-fM}J>K`d8C=7|ny}*NF=A>xl~U+sO>~yzYG&-@kt+ZpT$<j{0#gxVAgZ5`4VCG5a5%$2jn}',
    'Fy>?Tx6hyVfO$O@LX-^Cx)0t-3Z~D?kZ;E~u%=+x9w@gnjO)1<H`G6UE#}&&xq^68je9V;4e>9?=fMxUA$(kA|E5z$yh3X`<2uL*{Po<48?M_i',
    '755zdy4dI88HV6NdZEh`gXOaY!`zv^)n3=UF-y8Og7(kTCp<*L?QD$OY8dNYOI?q?_{x9Xx{|(bYo@p3`7~Yk5)E(okyc){v@?a<*z*LApHFFj',
    'd)q1h(Xif|4!4m0{X<g4?~h>M1&3SOXMj&Tfc`9Pw>#!W^tnCUZTk)o`wc-~iqrqGAocc`C+jct$d{DzZQ||T<FpOb_ts>2^nZR_J6!Lz=1aMc',
    '+4p(3jr}q52h7b$%|8I{xBr;^(BS-?(yOKPy7|L*kNvmi=%cap1^n(C=tDD~A^eKvPWg%ApSF}gn1Jpyo{oE0%hPS2c8h+c{z_*(A29{%v-RTT',
    '$WP6@sqasGkth5A6N}zfa3}OI8&P4bH`eZ$UUa>9{3o+-5%-a)yrKB`lf%!rdpkL2emjHay?+0nyJ#;H{G){YTO;z$r{>%W(wFSO{~AQSa{W<N',
    'y!AgnL;YLT@oHv$mKk>*zU0q;iwL)&-|r2&E05RyT<j0Od-TDc3;AhkUfOk)s9_2yX?*5Es(foJO4t6jH`9v<H$J_~n=M@ld`V;<qPk_vs^EG^',
    'Zz!OD;P;*m-<SHOgLlXA?|r-5u}E*7-!I|p-aGL<n^=!<_7+thos*}>J~~^^vw7~VtuM92-D>`=N%X~>o>+ceiCo(e&l`{4(cjhZC87U!3w~=T',
    'JpwUt`|!p-7yf5U=B@Ahcf!XnCDiAGf@g8^<LmhAaloIQ-2c|a`5UIsX8>;_uSU4cESFx{XztjJWSUn`@-%ID+pnblL#zMO4!(W+{|xKknE',
]
EXPECTED_MAIN_BYTES = 19278
EXPECTED_MAIN_SHA256 = "25bc5e4e0dcb9d059e61d52d1d725609e2f61af30bf047257187da32e1332768"

raw = zlib.decompress(base64.b85decode("".join(_AGENT_B85_PARTS).encode("ascii")))
assert len(raw) == EXPECTED_MAIN_BYTES
assert hashlib.sha256(raw).hexdigest() == EXPECTED_MAIN_SHA256
compile(raw, str(MAIN_PATH), "exec")
MAIN_PATH.write_bytes(raw)

with tarfile.open(ARCHIVE_PATH, "w:gz") as archive:
    archive.add(MAIN_PATH, arcname="main.py")
with tarfile.open(ARCHIVE_PATH, "r:gz") as archive:
    assert archive.getnames() == ["main.py"]

print("✅ ARTIFACT   : main.py materialized")
print(f"📦 BYTES      : {len(raw):,}")
print(f"🔐 SHA-256    : {hashlib.sha256(raw).hexdigest()}")
print(f"🗜️  ARCHIVE    : {ARCHIVE_PATH}")


# 🔬 4. Import the challenger and audit route / market structure
spec = importlib.util.spec_from_file_location("v23_agent", MAIN_PATH)
v23 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v23)

sell_orders = []
multi_sell_turns = []
for step, action in enumerate(v23._ACTIONS):
    sells = [o for o in (action.get("market") or []) if v23._is_sell(o)]
    sell_orders.extend([(step, o[1], int(o[2])) for o in sells])
    if len(sells) >= 2:
        multi_sell_turns.append((step, sells))

route_stats = pd.DataFrame({
    "metric": ["route actions", "SELL orders", "turns with >=2 SELLs", "market-order cap"],
    "value": [len(v23._ACTIONS), len(sell_orders), len(multi_sell_turns), 10],
})
display(route_stats)

product_mix = pd.DataFrame(sell_orders, columns=["step", "product", "quantity"]).groupby("product").agg(
    orders=("quantity", "size"), units=("quantity", "sum")
).sort_values("orders", ascending=False)
display(product_mix)

print(f"🧬 ROUTE ACTIONS       : {len(v23._ACTIONS)}")
print(f"💸 SELL ORDERS         : {len(sell_orders)}")
print(f"🔁 MULTI-SELL TURNS    : {len(multi_sell_turns)}")
print("✅ This mechanism is exercised repeatedly; it is not dead code.")

# 🌊 5. Visualize the official nonlinear premium-product curves
premium = ["STRAWBERRY", "MELON", "MILK", "WOOL"]
rows = []
for product in premium:
    for surplus in range(0, 181):
        rows.append([product, surplus, v23._market_price(product, 10_000 + surplus)])
curve = pd.DataFrame(rows, columns=["product", "surplus", "quote"])

fig, ax = plt.subplots(figsize=(9.4, 4.2))
for product, grp in curve.groupby("product"):
    ax.plot(grp["surplus"], grp["quote"], linewidth=2.2, label=product)
ax.set_title("Nonlinear post-equilibrium quote cliffs")
ax.set_xlabel("Inventory above equilibrium")
ax.set_ylabel("Sell quote ($)")
ax.grid(alpha=0.2)
ax.legend(ncol=2)
plt.tight_layout()
plt.show()

floor_distance = {}
for product in premium:
    for surplus in range(0, 1000):
        if v23._market_price(product, 10_000 + surplus) == 1:
            floor_distance[product] = surplus
            break
print("🧨 $1 FLOOR DISTANCES:", floor_distance)

# ⚔️ 6. Compare V22 endpoint proxy vs V23 exact execution loss

def v22_endpoint_proxy(obs, order):
    if not v23._is_sell(order):
        return float("-inf")
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = obs.get("market", {})
    inventory = market.get("inventory", {})
    prices = market.get("prices", {})
    current_inventory = int(inventory.get(item, 10_000))
    current_quote = float(prices.get(item, v23._market_price(item, current_inventory)))
    later_quote = float(v23._market_price(item, current_inventory + quantity))
    return quantity * max(0.0, current_quote - later_quote)

# A boundary example where V22 charges a quote drop that occurs after the final unit executes.
example_inventory = {k: 10_000 - 95 for k in v23._MARKET_PARAMS}
example_prices = {k: v23._market_price(k, example_inventory[k]) for k in example_inventory}
example_obs = {"market": {"inventory": example_inventory, "prices": example_prices}}
example_order = ["SELL", "MELON", 6]

print("🧪 BOUNDARY EXAMPLE:", example_order)
print("📐 V22 endpoint proxy :", v22_endpoint_proxy(example_obs, example_order))
print("🎯 V23 exact loss     :", v23._execution_loss_score(example_obs, example_order))
print("💡 Interpretation     : V23 scores only quotes actually paid to the 6 executed units.")

# 🧪 7. Mechanism diagnostic — deterministic state sweep
# IMPORTANT: this is NOT a win-rate test. It asks whether V23 is behaviorally distinct
# while preserving the same route and order multiset.

def apply_v22_slots(obs, action):
    action = v23._copy_action(action)
    market = list(action.get("market") or [])
    rows = [
        (v22_endpoint_proxy(obs, order), -index, list(order))
        for index, order in enumerate(market)
        if v23._is_sell(order)
    ]
    if len(rows) < 2:
        return action
    rows.sort(reverse=True)
    ranked = iter(row[2] for row in rows)
    action["market"] = [next(ranked) if v23._is_sell(order) else order for order in market]
    return action

records = []
for surplus in range(-100, 201, 5):
    inventory = {k: 10_000 + surplus for k in v23._MARKET_PARAMS}
    prices = {k: v23._market_price(k, inventory[k]) for k in inventory}
    obs = {"market": {"inventory": inventory, "prices": prices}}
    for step, _ in multi_sell_turns:
        action = v23._ACTIONS[step]
        old_market = apply_v22_slots(obs, action)["market"]
        new_market = v23._impact_slots(obs, action)["market"]
        records.append([surplus, step, old_market != new_market])

diag = pd.DataFrame(records, columns=["surplus", "step", "ranking_changed"])
summary = pd.DataFrame({
    "synthetic route-state cases": [len(diag)],
    "ranking changes": [int(diag["ranking_changed"].sum())],
    "change rate": [float(diag["ranking_changed"].mean())],
})
display(summary)

by_surplus = diag.groupby("surplus")["ranking_changed"].sum().reset_index()
fig, ax = plt.subplots(figsize=(9.4, 3.6))
ax.plot(by_surplus["surplus"], by_surplus["ranking_changed"], linewidth=2)
ax.set_title("Where exact integration changes SELL-slot priority")
ax.set_xlabel("Shared synthetic inventory displacement from equilibrium")
ax.set_ylabel("Changed route turns")
ax.grid(alpha=0.2)
plt.tight_layout()
plt.show()

print(f"🔬 TEST CASES      : {len(diag):,}")
print(f"🔀 RANKING CHANGES : {diag['ranking_changed'].sum():,}")
print(f"📊 CHANGE RATE     : {diag['ranking_changed'].mean():.1%}")
print("⚠️  This proves behavioral distinction, not competitive uplift.")

# ✅ 9. Invariant tests across route actions and deterministic market states
forbidden_tokens = (
    "CanonicalTeamNames", "CanonicalTeamIds", "SubmissionIds", "EpisodeId",
    "Seb (allegedly)", "roma",
)
source = MAIN_PATH.read_text(encoding="utf-8")
for token in forbidden_tokens:
    assert token not in source, token

assert len(v23._ACTIONS) == 719

checked = 0
for surplus in (-100, -25, 0, 25, 60, 100, 160, 220, 400):
    inventory = {k: 10_000 + surplus for k in v23._MARKET_PARAMS}
    prices = {k: v23._market_price(k, inventory[k]) for k in inventory}
    obs = {"market": {"inventory": inventory, "prices": prices}}
    for step, _ in multi_sell_turns:
        action = v23._ACTIONS[step]
        out = v23._impact_slots(obs, action)
        assert len(out["market"]) == len(action["market"])
        for idx, order in enumerate(action["market"]):
            if not v23._is_sell(order):
                assert out["market"][idx] == order
        before_sells = sorted(tuple(o) for o in action["market"] if v23._is_sell(o))
        after_sells = sorted(tuple(o) for o in out["market"] if v23._is_sell(o))
        assert before_sells == after_sells
        checked += 1

print("🛡️  INVARIANT AUDIT : PASS")
print(f"🧪 CASES CHECKED    : {checked}")
print("🔒 NON-SELL SLOTS   : unchanged")
print("💰 SELL MULTISET    : unchanged")
print("🕵️ IDENTITY FIELDS : absent")

# 🧯 10. Runtime smoke — full Kaggriculture schema when the package is available
schema_smoke = []
engine_version = "not installed in this runtime"
try:
    import kaggle_environments
    from kaggle_environments import make
    engine_version = getattr(kaggle_environments, "__version__", "unknown")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 230_807}, debug=False)
    for seat, state in enumerate(env.reset()):
        action = v23.agent(state.observation)
        assert set(action) == {"farmer", "hands", "market"}
        assert isinstance(action["farmer"], list)
        assert isinstance(action["hands"], list)
        assert isinstance(action["market"], list) and len(action["market"]) <= 10
        schema_smoke.append({
            "seat": seat,
            "farmer": action["farmer"],
            "hands": len(action["hands"]),
            "market_orders": len(action["market"]),
        })
    print("✅ KAGGRICULTURE SCHEMA SMOKE : PASS")
    display(pd.DataFrame(schema_smoke))
except ModuleNotFoundError:
    print("🟡 KAGGRICULTURE SCHEMA SMOKE : SKIPPED (package absent in this runtime)")
    print("➡️ Kaggle notebook runtime should execute this branch with kaggle-environments installed.")

print("⚙️ ENGINE VERSION:", engine_version)

# 🏁 12. Final release card
release = {
    "policy": "v23_exact_marginal_impact_slots",
    "status": "CHALLENGER — fresh competitive score required",
    "route_actions": len(v23._ACTIONS),
    "main_bytes": len(MAIN_PATH.read_bytes()),
    "main_sha256": hashlib.sha256(MAIN_PATH.read_bytes()).hexdigest(),
    "submission": str(ARCHIVE_PATH),
    "archive_members": ["main.py"],
    "v22_reference_evidence": "44/46 strict-future replay cases; not an official LB score",
    "new_measured_evidence": {
        "synthetic_route_state_cases": int(len(diag)),
        "ranking_changes": int(diag["ranking_changed"].sum()),
        "ranking_change_rate": float(diag["ranking_changed"].mean()),
        "invariant_cases": int(checked),
    },
    "kaggle_schema_smoke": "PASS" if schema_smoke else "SKIPPED in current runtime",
    "ready_to_submit_for_challenger_evaluation": True,
}

print("🏆════════════════════════════════════════════════════════════🏆")
print("   🧠⚡🌾 V23 EXACT MARGINAL IMPACT — RELEASE CARD")
print("🏆════════════════════════════════════════════════════════════🏆")
for key, value in release.items():
    print(f"🔹 {key}: {value}")
print("\n🐈‍⬛ DECISION: SUBMIT AS CHALLENGER; PROMOTE ONLY ON FRESH EVIDENCE.")