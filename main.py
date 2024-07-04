import asyncio
import os
from json import load, dump
from sys import exit
from tqdm import tqdm
from yaml import safe_load
from utils.logger import setup_logger
from utils.aio_calls import AioHttpCalls
from utils.decoder import Decoder
from utils.extension_parser import ExtensionParser
from multiprocessing import Pool

with open('config.yaml', 'r') as config_file:
    config = safe_load(config_file)

VALIDATORS_WHITELIST = ['initvaloper10cyjklstjzx89r9ezfdylm8q35k56czhtj4wy2', 'initvaloper10jqqj8cswcraswmd5pqka7qj5d4k2ghcwxprgf', 'initvaloper10p2t99q9z07was8adfu0ek3yxae8qkf3zs9rcd', 'initvaloper10rem5g6ygjmzvmfpmavvxt5wnnkvtejnj093x7', 'initvaloper10s6y674t8avne2hnzpr77s60kvgc3d4me54uff', 'initvaloper122r525yk36g862ucq75qm907s7lxykeezh3vdy', 'initvaloper1273lz4rm8u6e7u5crlta0aww8ygq8669l9t8wc', 'initvaloper1276e0zxh4n5gx6qqjp5qwlxk8q7mrj4cunt553', 'initvaloper127954rf84m7njy5vrkce7rwen60xf7uyjwep34', 'initvaloper1290v7f5jh3smyxkuedatmcrl4f3v8z36xvgc3m', 'initvaloper12c3rph23r52ux34m5ne00zzahvnwcxqgpwm8fd', 'initvaloper12etze50d3kng9j63q62gruzpqnq7hkf87vxu9z', 'initvaloper12gd56g9tu4zv8sme4c5kuhsw7pv9weuusugx5p', 'initvaloper12nrey53kr2kphu3zpj766rwf403ppf2hd84swr', 'initvaloper12nutq3nctahc6ng6f5lq2u6sew46ysm8dll97r', 'initvaloper12ygz083ccaxl0y8870yukdg53tyql922pzlvss', 'initvaloper136txl0wgxe06fhhu85927gxge5k68mu8pfg47g', 'initvaloper139xmefccx0nnjz3l6s2dez5r4a72t82zgqdxtt', 'initvaloper13lxemqz60jknxwh2nlxp2wx29hqk044gunslkd', 'initvaloper13mglw0n7dusn38nsj6k7wxl8gkqta7dcklvhm6', 'initvaloper13nwzm5dfd26ue74jr6sc39gyn3qze0rjahfguc', 'initvaloper13rk0k6h0qg2d4tay5mx8fl00w8m2y4lnr67r3k', 'initvaloper13ru2p6eear5f4djhfs2p09n3xw2gzsldlfs3hd', 'initvaloper140hljshwuqd0qt5tjmwk3jruh63jn9vc5mje6u', 'initvaloper146uhx74n9zfwrs82e4lnwhf8rjnfptnehp6eyg', 'initvaloper14cmqnrstxg97vvtqgqju0k47ekdjwl4m95qf60', 'initvaloper14d8muxjg8h79z8t3wavyqr5tw46ychgkval44l', 'initvaloper14ee4rhk9gsezwdx2ka4eksaeyvt0qnwqrn9ctd', 'initvaloper14fr0slyjutp7kndpqz4puj97f8rmy4fxhtsjq4', 'initvaloper14gprw26ha0u8u9nw0nktjqxzu2n8r9gnnu4jk5', 'initvaloper14lz3qm9dclh4teuemzp6wdswjx5uja42s8xjxn', 'initvaloper14qekdkj2nmmwea4ufg9n002a3pud23y8l3ep5z', 'initvaloper14vddg3vwes24rtchhtakxvvck50hmkfrj70l84', 'initvaloper14wa479q4v80nsq2deyq625myszhrhggqw6jrmx', 'initvaloper14x58fjv7k3czdhhajfdwrhpzvuvhv983vq0ydk', 'initvaloper14xxje6d9mv8k8mhfwj7ddg8g2g6xm4rnldafgg', 'initvaloper14ypwpqy9hxalkvhg6ruahm46lu9n7rngk3ftt7', 'initvaloper153x3euxtvd440huqd6ajjdxg840ndu7p6k9jwg', 'initvaloper15d79aryy92yjf4pz5cxfrmarf5ykz2d0gdcg5n', 'initvaloper15lmulm2hmu4axd472ezk6wdqeq425czzgkp3cz', 'initvaloper15mrqk7mqsafsrll4kad4fz4eannm0w9w3kxvfc', 'initvaloper15s0r9g85u05sjpu3h8ndzfsv7382sqy9q2wdwh', 'initvaloper162t8pejm79wkukcs0yctx0ep5t2c97txptugp4', 'initvaloper165ezg620k3fjn9p90792e4s548e668ekkltrqk', 'initvaloper166ft076vure7s8h7cxhmz6vqxa5zankxqu9r9j', 'initvaloper169589j85fwrcqupp9rxlj6ak2l6ek429pjqtgn', 'initvaloper169yx6dqutfwlf78agrdsgptq7nf7z3tdtnhvc2', 'initvaloper16h7khua5xkwxsp9g80l7zgyv8k5g837qr0av46', 'initvaloper16krwrukclve06sjsd5fsrvw059c8x9cyzmqzs5', 'initvaloper16v0acl85kvcst3292l89wgdgewrgttyt9647ge', 'initvaloper16we96acr8p3y7khq3held9pa6n9jdpwhthf5fk', 'initvaloper178wwgl7xcvvmaagcdfxr9nfxmhq4rhstnc5ner', 'initvaloper17ejf0ty2lvfm42kksht9ra8qnkutg4tq5d6tfn', 'initvaloper17lct3zjj83ykx86qcrjpjqc5pg96rxqdwww7uc', 'initvaloper17x9yd8lg28mvfse3evj3m6slfsrj209aqwws96', 'initvaloper186j55s8d26paq398qwc6cqry3v2rhtrxqdgggh', 'initvaloper18e9sql942n09vsn60vzrld26csryqwu9z4g9zm', 'initvaloper18eltknswajterrnzjtarwhzuqwv3x68qj5tsmv', 'initvaloper18g9shzlg8n45eq4ahcg32hrsqcyshlk97k6dsc', 'initvaloper18gtqadftw9pfqv6x2svwdqkfsw7hjptdj6xp0h', 'initvaloper18m5xwp0mgq840sq0udutjpax7ngyymgx4ux903', 'initvaloper18qclh0e4g7pt5vh3tfa4zkz97y2dw85ugvzg8v', 'initvaloper18uamly9vsqceywt0wv2d4v670ch5k32xvz4q5e', 'initvaloper199hk0cd48jwa98spyzgawrjzr83jaddxwzeaue', 'initvaloper19a3rcrgwvdsdx2uha0jp9eggt9xkqh4hthavtm', 'initvaloper19j6aw3lqs0qh97f9tlvhvgeufcr83a3wh0sxtn', 'initvaloper19xeuyx7gheh68rwl7g30y56n7hzz653g8c0lpm', 'initvaloper19y8aqjcwy408twm2uf8x3tufc8h3g93qfvxtuk', 'initvaloper19ygu4aqk7m8v40vwn8anngjj54yfraqee0veyc', 'initvaloper19ysahly6mv7yusdu539m8gf5hpfsza0z3zmxmh', 'initvaloper19zg4rdjsedv5g2vfs4h54u8tjny5ytclzsvplu', 'initvaloper1a2w88q4agnfzyrvj5uapafxzx49gxfyhccyyy9', 'initvaloper1a3py04e59zlrxuf29gcl090pvrn24xhu337xc6', 'initvaloper1a4apzg3cknavjjhk0nznrltvp07era7cye0t8t', 'initvaloper1a6dlnt2zctqx3xlz9up6a3svsea890j0uqfg64', 'initvaloper1a6u55kgafscnsqxgxszhqadw5zzmupqcymc96h', 'initvaloper1a88l3m9x09utlrhcmp99uraqa4y3xqs50s0lre', 'initvaloper1ad0hendnwxspy6t47kxtf8nsj8lhz4kfsrw6mk', 'initvaloper1af27v4j05tznnq7knm6xyxafj0scz9du87dmaq', 'initvaloper1ahtmxlg3unfk9s40gxw2qg9584k5pk67mq5el5', 'initvaloper1ajhvag6yejt8a2ns0sjrq9ftm05ej9yrmfl5kk', 'initvaloper1av99dwjjjzf65xc9m02mwur7ja2esypt7c4mae', 'initvaloper1c2t9qekcxmhd5gk3dw9fh3qqgl99gmell0qdhd', 'initvaloper1c8rqn5wuz9fcvcmyqaxvartlnlwuw2glkkszsz', 'initvaloper1c92gafu7r30alc8ystgzqy236vyczs950d4mkl', 'initvaloper1cjywjplzpx3pzkc9ex2xywe7fkf4g5s7a9l5dn', 'initvaloper1cq2q7p4sanqya62899fyjfn34wr2xdu3k2chcd', 'initvaloper1cq7s4rc2nauhg4x4k64f0z5accqt4jrvwcm03j', 'initvaloper1d9g5zkk55778ttqq40k63nusx45a74uugfy284', 'initvaloper1davz40kat93t49ljrkmkl5uqhqq45e0tj5qncz', 'initvaloper1ddx0l92r4427ws0u05nwdhdqs6k3h0l9l39qwg', 'initvaloper1dhnjy5c9rd5auaeqjdxamgg962n4rmlrqvxu32', 'initvaloper1dj3euve963lczzjkj8rlex33asj2kuj85hc3pp', 'initvaloper1dntcr3jpuwdkx74s4tnw8a0gp2mugum7j37ppv', 'initvaloper1dtm7mx37xwp9znmcaygapltdpe5nmw9pqn2029', 'initvaloper1du9e3tujprk5ekwla20rddqmkjjl8kq4csmcyk', 'initvaloper1dv4y43sqgv7fg5lucwyte26556954tpuk5ledf', 'initvaloper1dw2q67hx28acl55rlnza7hxrrp9sytsewa6pcx', 'initvaloper1dztk8zf6fwaxxezknm0rg7u7ghsg20d94ez82a', 'initvaloper1e8w7p3x7e0aj3ky3mjh33aymznhwsle4hkc6ag', 'initvaloper1e9dn9p00v0hvyr4nc7zvletyntnpd4zyf07vph', 'initvaloper1ec4jfj5m7h03xw56tjd2d7vp97e5q0h2n8qkuc', 'initvaloper1ecuyrz6l7taex6se3ueuhjm0wlkpjf75gt08jj', 'initvaloper1fvnx4nwuufyvdrpeqw4fj20p4yqkm2vkw5mkfs', 'initvaloper1egz6xdd7g9u6lqqg24z8sdnxka7fpx0usuhe8v', 'initvaloper1epyc2uz3pes8xg7rxh23r9nj009eaex373a9ap', 'initvaloper1et4z07h5edecndvrfuh9fe3pcgf7m3a8ul6qvq', 'initvaloper1etx55kw7tkmnjqz0k0mups4ewxlr324t0xv9m5', 'initvaloper1euaxg49c5glux3errwe60gv0cgz3x5d6c4ndpd', 'initvaloper1f4hsk30wv9rrm6zv0q5j224phx2nv60x5zclg6', 'initvaloper1f5z88al43m7jf574kf3avqxw5pedu0kqfrmjal', 'initvaloper1f9zejgpgmmhk6m2wk2wmk5f4fuk36ve2vqtw7z', 'initvaloper1fce4xcsrlv2fc7cedarefcguq2jf0t8vd2jdr6', 'initvaloper1fd8jgtm5ydna7az5tndcm5nef22ee5e959nfdt', 'initvaloper1frantxpyzg8xthuhpdh3hrpcvu56ua6z5mqjcz', 'initvaloper1fsdpxly2myeq07whq4svr0nyt8ku2j3t023t07', 'initvaloper1fzxl2dymlark57cydp9l44mk0westhlldrs3wx', 'initvaloper1ga278hzgemjyasymze564z8alymnfaq4tpfaql', 'initvaloper1gajf4yz9d8xjjwdq569dyda66rtw2p7kes22en', 'initvaloper1ghafr9ul6ex5kw3aellqlpa0lresme8snep8k4', 'initvaloper1guf2jtsae9ycj46a8aktj05dtpaju7zczxpll0', 'initvaloper1gxy3d8kyxss0dqlyu50dmpkn3gc2kuxurhc80t', 'initvaloper1h6p086gahktqeryeaq84t02wlr69zr88vxal7s', 'initvaloper1hfaq8nc4e865zt05amkzznfxpt6af0u0lfqd2y', 'initvaloper1hqqsjt05yqsqglyhgymcpgeh34lnkhh6zcasgq', 'initvaloper1hsezv8vcy8ha335wwf9a3d2dmwn7cf33x7x3qf', 'initvaloper1hvm946vglp3nh48sz4rf46lk7mehnw4e2lez8j', 'initvaloper1hwawsmpey9yc96par8x5lju3y9qt409lmysm7v', 'initvaloper1hzlnym8y2wxew8zeww7mmt5pn4v8dk0dcukk90', 'initvaloper1j3rzvgz3prqv4gtqcsyk60rj64qlpyensrhd9u', 'initvaloper1j4tkeajj4ldta970rhe8gj89u23zkumrhmftp7', 'initvaloper1j65h5afhcynwm7u4xnrjskhlztzmfrz8umh4y9', 'initvaloper1ja05avdr0hkvtmh0lsp7afrq6283sffy6szt94', 'initvaloper1jdg7s6m49376p878u92j4c64nxpcvsev2shngz', 'initvaloper1jfvc8wr2j3srketkvgx2lj34ksxet82gh5wvdu', 'initvaloper1jka3wgy73qvx00t27nv3skcvarrnys8dve9zqn', 'initvaloper1jndcyfat605k42a2ug3pcw772q04t7mw0plqq9', 'initvaloper1jspsp87jz6txchejatv4wl30sa78k4vtmmcqxa', 'initvaloper1jt9w26mpxxjsk63mvd4m2ynj0af09cslej8vvr', 'initvaloper1k47y23rektgcany97l97ql3clu36xj2ccgkklu', 'initvaloper1k88epq8dmmmqp0lu0dp28mmrw0n9r48zzncpzs', 'initvaloper1kcxn0tehelc3rac9u8ss9au2xl048xvfntrsx5', 'initvaloper1khea05wwtedrj78exaddk55jzwrjvxcng3zhnm', 'initvaloper1kpaw7xzsacdmu4sw3x9k0wmyt8duujn7kgtg26', 'initvaloper1kqssefqj25hn4m5q43fymlcyustrfuls5cslmv', 'initvaloper1kuaqagx4qwdsaruapsageu7ngd7964x7wh3d8a', 'initvaloper1kvzzw2x563nmau0agawx2m9teg536nk2fsez4z', 'initvaloper1kyh8gjevs8zf0q0lj4mxwzyjj9ke0j0tyeprzz', 'initvaloper1l6e93pwsja3jjq6m6nl2lkgguasp4l56h5xgnu', 'initvaloper1lc05quxdqkzjc672l0zdlhcrulpltz2vxvrwcg', 'initvaloper1ldu27jcv6jl745c3zhd3gft9aedgqucnaf00qq', 'initvaloper1lhu8qfsvspn85dr9sf8dqka5vj8hzgsptapvn4', 'initvaloper1lkamjtpt75js46m2zdnletxuquxzg0u72q2wlw', 'initvaloper1lksvlqlj38yafqc6kuywdjr72z69fps2aj6csd', 'initvaloper1lmtmkfu4wmhefh6ruppt4q6ucdys4x94tnchay', 'initvaloper1lvrcfvk546ceezdcpt9le20fgp4vv90kaq0lx9', 'initvaloper1lwf56jz3nr8njw58j2gdcmzvv6kqnc50mq4pss', 'initvaloper1lxn0k3zv568m89hvman69tjc5vmtwle2erux5a', 'initvaloper1m07fvq8flvc3ltjlgk30nznfdjf4hx9nwcpdy9', 'initvaloper1m5kukxflp7zstrq3ng5q4p75trkx68ru6s7c9e', 'initvaloper1m8y3ent7urj9guwqf0p03cq68eu39h22v37v43', 'initvaloper1m98l5cwp4tf4f73hk3r5l2mlpz0w7zwm5h8yxx', 'initvaloper1mmmn8ym7yd6q58v8excjvhwtlts42j43hzq6rq', 'initvaloper1msyna4xsp78y2cl47qqnk0g33lnyv2xmwkkwzt', 'initvaloper1vsutqyhz5v5yevl2a0y87gxpgesv3ty2q582fn', 'initvaloper1mx892rj285rmukyp34g5xfmwhww3dze4995s5x', 'initvaloper1ndhac5sje84xzcea9vxtgspwrjsmlukfzfdg69', 'initvaloper1ngq6fh3x82nv5c8zm93vrkueavd2zgecq2mrze', 'initvaloper1nnwv2mg8wfg4yrapuwl6xv477m55ekzjgj0jcq', 'initvaloper1nqn66n855ksq63f4cn5zzvuuf5q9ynak7lcpf4', 'initvaloper1ntqep3yp6ad44mx4m0n2p9umynprrlft07p7m8', 'initvaloper102e4pmzkqltzp8hrq8xk3gmshc6w7qvpuh39jf', 'initvaloper1p4378lu3ycdug07nry8fmpqmmqek5u7sth3pd5', 'initvaloper1p6645q547rnec57fp4g2pgvm4ukdvrn6uw2rg4', 'initvaloper1pcdwg5g83j6z3hfta8ggg4q96y0x8vhxy5rcw0', 'initvaloper1pcjpgd3ynwkgw2ap7vwsc8zgks2qzeuhtkxaf4', 'initvaloper1pdaka5724xnyaygprep54j54j8gndhqmefct82', 'initvaloper1pescpz7czmw36rrdmpkd2pcu4m0xjj9h84p572', 'initvaloper1phrpnyshp0vqj2uwse6xeljn8kryv6q0q07jrv', 'initvaloper1pqsc3j82ckahdk65wqfdgu2cgah6hpl0vxvha6', 'initvaloper1pw752a7usv085ht99hurr5mah62kewmg7uk3ex', 'initvaloper1q2al59gylz40jms6emey6ps8leuguhs7kvqhag', 'initvaloper1q422p5m0gej7gp43385thsfpmjuwql72zz9w56', 'initvaloper1q8qa3x0py3kz85nsl3pydj7hpjpsjwfafuz4vw', 'initvaloper1qf5s6w62l7c9x46ml9lm3dku93kkafxsmhr5gw', 'initvaloper1qf6a3gqmq3kumy6237cujeggz5c2e4gvkpe8xu', 'initvaloper1qgkk2e3k9r3l5pcqxlwxcv7yhqhgu5cd70ush3', 'initvaloper1qh2g60rmshzhmd46pyccaarg2z7xpdey22kwc7', 'initvaloper1qz30lp48lkdhcx2uw34v3mulc6se3wmw8jhaqw', 'initvaloper1r3cuy3q2gxh0mpj2nu0cnpqtutaxx9z87r6qtt', 'initvaloper1r5j5mx98tykgls43ru47xytml0jc7359nd40pm', 'initvaloper1r7prex0t0g72kp443nrjmadkgsc2fuf8aye87l', 'initvaloper1r7x9kldt6nat78shrz3537c4guuhsrl40ztvy2', 'initvaloper1rg3w5xmc82p9lse0j8rjzxs4tmjxzjek6zt9tu', 'initvaloper1ruczecxjech3gmtsq7nnk85ac75nuteh0jqpyd', 'initvaloper1rvtusq2f3yysp8ek5jh9esj2cs7yas3gw488af', 'initvaloper1s659a3eup2etjk9ugy874h2cnd3kpvpj4yzg9c', 'initvaloper1sa5yy0tnuwcg0ewtrt870w2gfnjlasps3es58s', 'initvaloper1skxhd8y72faq4r99x8362ftum39hlaamy9sm4e', 'initvaloper1sv5jej44xns6jem05yvexuq95dyzt0nkafhajd', 'initvaloper1svpwakq97ypkxr2uqy2hdq8huenmrnvhsn4vaz', 'initvaloper1t0ftzre7j3de4g5h8kwevxv9xaujzlcymw2z2d', 'initvaloper1terwkjfmxvax5a0qdpcq2ue9krkm9m505c7hsd', 'initvaloper1tk6mgghdzq3axjle4srutcva63sshapj4plg6r', 'initvaloper1trna7qqnn65kdsul6pl6dcmmajn9ajgtx88twh', 'initvaloper1uc4ytdfyfzmljmk7cz2wcewrhj5dnfm653enp5', 'initvaloper1udd59c570kmrta9y58cmg6wyxrkc79a2aj0zuz', 'initvaloper1ultt4jk0us0rwm42mew05zcsnv6s5zaufrufvw', 'initvaloper1unm3hv8rd0kvdmv48f3a008fpyqs4pm6cpq52a', 'initvaloper1usjplh0waqwx8fq6aqah22gyu70v27u03t2dvy', 'initvaloper1uu3tjg7z283gselp90zhgy7xxrh5lxctdmazeg', 'initvaloper1uxujz225sxhpwnud967hnelcmu3yahwswdk8lq', 'initvaloper1uz7awcv673d09wkj22hgj35mk0ajf6upjnxzl0', 'initvaloper1v3gaeq64hctwq447jwqm27p3hpa2qydc7e9ez7', 'initvaloper1v3lq8c6grs828kjjgq4mrkxnsk2dl452y5mggz', 'initvaloper1vaxz9hyn8sq5vk3jgdhkge8xefuhz6xta2wkul', 'initvaloper1vcnp3rf2duwgh45nqxruykw5pcxns7fskpdyuf', 'initvaloper1vlwm654rj37lqvz43p6kmzqkjs5z0r2vhl6hvm', 'initvaloper1vnkvt6ffe6l72qpgu2r3huyusv2tjy8n6w43qm', 'initvaloper1vrzt4n95xhgkl5metpkvkf4gn4yfd6sllvx2uc', 'initvaloper1vspyaf52cnanw58ntsj35u430dvntmzdhkefak', 'initvaloper1w0swmr55ch7dqpg6ju4whegs6dh8lhnkp2qgyj', 'initvaloper1we4tsdvz2glpn9ldn5a27ztcccukfkq39d65wc', 'initvaloper1wenfvna7qazm3l56sagqe00w8m50rs94jsl5jc', 'initvaloper1wm2ahs5mdtdvls577cevx682hqsxvw7yrk3tuu', 'initvaloper1wpayju4jcn2mhv6yewclf6rcq9fyqzvamx3zdr', 'initvaloper1x5wgh6vwye60wv3dtshs9dmqggwfx2ldfn4nfa', 'initvaloper1x7j4d9ccds889yxecuylp803d0h6lrfnv30k9y', 'initvaloper1xjkejmre437mf868jhwjaf92p06cwryr390epm', 'initvaloper1xjthhujpzpws3u78nxm0dvkdks8cp3yf85the7', 'initvaloper1xwqpyhxsh5fenq2agpwcz6s3g0avypuuu23zz2', 'initvaloper1xxae4payg8jvs6tk9p8y5zdx43fn30zx6mje5c', 'initvaloper1xz8a6r34lzqswcsasw0y23j6n3khhf8z9cckvp', 'initvaloper1y00mjnttdespdcpzwlpntsypdfnm8m43z8akdf', 'initvaloper1ygfhd4gdjxjjup4339jn86chvqgtrq5klydu2k', 'initvaloper1yqje8ypwe6sr6plxwxf7nfhdej8hyc0vrwr27t', 'initvaloper1yrwd4pvdkwg7rkqgspwnvfsxkjtl3zzjexcljg', 'initvaloper1yt5szx09w2d9n7gus0p84jr52agdwuskz4ufjj', 'initvaloper1z4r0s9mh45ratamurz4u78ayhel3pyem406f03', 'initvaloper1zg3j59erlat3yuwcqfchgtr7l4f2qhc8z3gxfp', 'initvaloper1zpvqgwgxqpz64zckshsa65nqzan7lmqtg3uh8u', 'initvaloper102x9xckcckqhf34zq35m93wukazg3rr8fl0jpz', 'initvaloper1kzs47dd6jhkx68wcjquv5z4g3wn2x5rhv3kz7v', 'initvaloper19pspxs0j2lcp90m9xzxx9zfstsc2ew382wu3r3']

logger = setup_logger(log_level=config['log_lvl'])

decoder = Decoder(bech32_prefix=config['bech_32_prefix'], logger=logger)

extension_parser = ExtensionParser(logger=logger)

async def get_validators(session: AioHttpCalls):
    validators = await session.get_validators(status=None)
    if validators:
        filtered_valdiators = []
        for validator in validators:
            if validator['valoper'] in VALIDATORS_WHITELIST:
                validator['wallet'] = decoder.convert_valoper_to_account(valoper=validator['valoper'])
                validator['valcons'] = decoder.convert_consenses_pubkey_to_valcons(consensus_pub_key=validator['consensus_pubkey'])
                validator['hex'] = decoder.conver_valcons_to_hex(valcons=validator['valcons'])
                validator['total_signed_blocks'] = 0
                validator['total_missed_blocks'] = 0
                validator['total_proposed_blocks'] = 0
                validator['total_oracle_votes'] = 0
                validator['total_missed_oracle_votes'] = 0
                filtered_valdiators.append(validator)
    
        return filtered_valdiators

async def get_slashing_info(validators, session):
    task = [session.get_slashing_info_archive(validator['valcons']) for validator in validators]
    results = await asyncio.gather(*task)
    for validator, result in zip(validators, results):
        validator['slashing_info'] = result
    return validators

async def get_delegators_number(validators, session):
    task = [session.get_total_delegators(validator['valoper']) for validator in validators]
    results = await asyncio.gather(*task)
    for validator, result in zip(validators, results):
        validator['delegators_count'] = result
    return validators

async def get_validator_creation_info(validators, session):
    task = [session.get_validator_creation_block(validator['valoper']) for validator in validators]
    results = await asyncio.gather(*task)
    for validator, result in zip(validators, results):
        validator['validator_creation_info'] = result
    return validators

async def check_valdiator_tomb(validators, session):
    task = [session.get_validator_tomb(validator['valcons']) for validator in validators]
    results = await asyncio.gather(*task)
    for validator, result in zip(validators, results):
        validator['tombstoned'] = result if result is not None else False
    return validators

async def fetch_wallet_transactions(validators, session):
    task = [session.get_gov_votes(validator['wallet']) for validator in validators]
    results = await asyncio.gather(*task)
    for validator, result in zip(validators, results):
        validator['governance'] = result
    return validators

async def get_all_valset(session, height, max_vals):
    valset_tasks = []
    if max_vals <= 100:
        page_max = 1
    elif 100 < max_vals <= 200:
        page_max = 2
    elif 200 < max_vals <= 300:
        page_max = 3
    else:
        page_max = 4

    for page in range(1, page_max + 1):
        valset_tasks.append(session.get_valset_at_block_hex(height=height, page=page))
    valset = await asyncio.gather(*valset_tasks)
    
    merged_valsets = []

    for sublist in valset:
        if sublist is not None:
            for itm in  sublist:
                merged_valsets.append(itm)

    return merged_valsets

def process_extension(tx: str):
    try:

        extension_validators = extension_parser.parse_votes_extension(tx=tx)
        data = {}
        for validator in extension_validators:
            valcons = decoder.convert_consenses_pubkey_to_valcons(address_bytes=validator['validator_address'])
            data[valcons] = 1 if validator['pairs'] else 0
        return data
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

async def parse_signatures_batches(validators, session: AioHttpCalls, start_height, batch_size=300):

    rpc_latest_height = await session.get_latest_block_height_rpc()
    if config.get('end_height'):
        rpc_latest_height = config['end_height']
    if not rpc_latest_height:
        logger.error("Failed to fetch RPC latest height. RPC is not reachable. Exiting.")
        exit(1)

    with tqdm(total=rpc_latest_height, desc="Parsing Blocks", unit="block", initial=start_height) as pbar:

        for height in range(start_height, rpc_latest_height, batch_size):
            end_height = min(height + batch_size, rpc_latest_height)
            max_vals = config.get('max_number_of_valdiators_ever_in_the_active_set') or 125

            signature_tasks = []
            valset_tasks = []
            tx_tasks = []
            
            for current_height in range(start_height, end_height):
                signature_tasks.append(session.get_block_signatures(height=current_height))
                if max_vals > 100:
                    valset_tasks.append(get_all_valset(session=session, height=current_height, max_vals=max_vals))
                else:
                    valset_tasks.append(session.get_valset_at_block_hex(height=current_height, page=1))
                tx_tasks.append(session.get_extension_tx(height=current_height)) 
            
            blocks, valsets, txs = await asyncio.gather(
                asyncio.gather(*signature_tasks),
                asyncio.gather(*valset_tasks),
                asyncio.gather(*tx_tasks)
            )

            if config['multiprocessing']:
                try:
                    with Pool(os.cpu_count() - 1) as pool:
                        parsed_extensions = pool.map(process_extension, txs)
                except (Exception, KeyboardInterrupt) as e:
                    logger.error(f"Failed to process block extension. Exiting: {e}")
                    pool.close()
                    exit(1)
            else:
                parsed_extensions = []
                for tx in txs:
                    parsed_extensions.append(process_extension(tx))

            for block, valset, extension in zip(blocks, valsets, parsed_extensions):
                if block is None or valset is None or extension is None:
                    logger.error("Failed to fetch block/valset info. Try to reduce batch size or increase start_height in config and restart. Exiting")
                    exit(1)

                for validator in validators:
                    if validator['hex'] in valset:
                        if validator['hex'] == block['proposer']:
                            validator['total_proposed_blocks'] += 1
                        if validator['hex'] in block['signatures']:
                            validator['total_signed_blocks'] += 1
                        else:
                            validator['total_missed_blocks'] += 1
                        if extension.get(validator['valcons']):
                            validator['total_oracle_votes'] += 1
                        else:
                            validator['total_missed_oracle_votes'] += 1

            # print(end_height)
            # print(start_height)
            # print('----')
            metrics_data = {
                'latest_height': end_height,
                'validators': validators
            }
            with open('metrics.json', 'w') as file:
                dump(metrics_data, file)
            
            pbar.update(end_height - height)

async def main(initial = True):
    async with AioHttpCalls(config=config, logger=logger, timeout=800) as session:
        if not os.path.exists('metrics.json'):
            print('------------------------------------------------------------------------')
            logger.info('Fetching latest validators set')
            validators = await get_validators(session=session)
            if not validators:
                logger.error("Failed to fetch validators. API is not reachable. Exiting")
                exit(1)
            if config['metrics']['validator_creation_block']:
                print('------------------------------------------------------------------------')
                logger.info('Fetching validator creation info')
                validators = await get_validator_creation_info(validators=validators, session=session)
            if config['metrics']['jails_info']:
                print('------------------------------------------------------------------------')
                logger.info('Fetching slashing info')
                validators = await get_slashing_info(validators=validators, session=session)
            if config['metrics']['governance_participation']:
                print('------------------------------------------------------------------------')
                logger.info('Fetching governance participation')
                validators = await fetch_wallet_transactions(validators=validators, session=session)
            if config['metrics']['delegators']:
                print('------------------------------------------------------------------------')
                logger.info('Fetching delegators info')
                validators = await get_delegators_number(validators=validators, session=session)

            print('------------------------------------------------------------------------')
            logger.info('Fetching tombstones info')
            validators = await check_valdiator_tomb(validators=validators, session=session)
            print('------------------------------------------------------------------------')
             
            if config.get('start_height'):
                logger.info(f'Start height not provided. Trying to fetch lowest height on the RPC')

            start_height = config.get('start_height', 0)
            rpc_lowest_height = await session.fetch_lowest_height()

            if rpc_lowest_height:
                if rpc_lowest_height > start_height:
                    start_height = rpc_lowest_height
                    print('------------------------------------------------------------------------')
                    logger.error(f"Config or default start height [{config.get('start_height', 0)}] < Lowest height available on the RPC [{rpc_lowest_height}]")
            else:
                logger.error(f'Failed to check lowest height available on the RPC [{rpc_lowest_height}]')
                exit(1)

            logger.info(f'Indexing blocks from the height: {start_height}')
            print('------------------------------------------------------------------------')

            await parse_signatures_batches(validators=validators, session=session, start_height=start_height, batch_size=config['batch_size'])
        else:

            with open('metrics.json', 'r') as file:
                metrics_data = load(file)
                validators = metrics_data.get('validators')
                latest_indexed_height = metrics_data.get('latest_height', 1)
                print('------------------------------------------------------------------------')
                logger.info(f"Continue indexing blocks from {metrics_data.get('latest_height')}")
                await parse_signatures_batches(validators=validators, session=session, start_height=latest_indexed_height, batch_size=config['batch_size'])

# async def update_slash_info():
#     with open('metrics.json', 'r') as file:
#         metrics_data = load(file)
#         for validator in metrics_data['validators']:
#             async with AioHttpCalls(config=config, logger=logger, timeout=800) as session:
#                 slashing_upd = await session.get_slashing_info_archive(valcons=validator['valcons'])
#                 validator['slashing_info'] = slashing_upd
#         with open('metrics.json', 'w') as file:
#             dump(metrics_data, file)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n------------------------------------------------------------------------')
        logger.info("The script was stopped")
        print('------------------------------------------------------------------------\n')
        exit(0)
