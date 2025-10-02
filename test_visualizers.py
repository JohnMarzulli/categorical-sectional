if __name__ == "__main__":
    import os
    import sys

    # Ensure the parent directory is in sys.path so 'managers' can be imported
    # This is only needed if running the unit tests directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from visualizers import flight_rules_visualizer
from meteorology.types.metar import Metar


def test_get_condition_from_metar(metar_report: str) -> str:
    """
    From a METAR, get the condition

    Args:
        metar (str): The METAR to test getting a condition from
    Returns:
        str: The expected condition

    >>> test_get_condition_from_metar(None)
    'INVALID'
    >>> test_get_condition_from_metar("")
    'INVALID'
    >>> test_get_condition_from_metar('')
    'INVALID'
    >>> test_get_condition_from_metar("KBVS")
    'VFR'
    >>> test_get_condition_from_metar("00000KT 2SM BR CLR 17/15 A3001 RMK A01")
    'IFR'
    >>> test_get_condition_from_metar("KBVS 121955Z AUTO 00000KT 2SM BR CLR 17/15 A3001 RMK A01")
    'IFR'
    >>> test_get_condition_from_metar("KUIL 121953Z AUTO 00000KT 1 1/4SM HZ OVC021 14/11 A3000 RMK AO2 SLP158 T01440111")
    'IFR'
    >>> test_get_condition_from_metar("KHQM 121953Z AUTO 13004KT 1 1/2SM HZ BKN020 OVC028 16/12 A2999 RMK AO2 SLP160 T01610122")
    'IFR'
    >>> test_get_condition_from_metar("KAST 121955Z AUTO 01005KT 1 1/4SM HZ BKN025 OVC033 16/12 A2998 RMK AO2 SLP150 T01610122")
    'IFR'
    >>> test_get_condition_from_metar("KPDX 121953Z 00000KT 3/4SM R10R/5000FT HZ BR VV014 15/11 A2999 RMK AO2 SLP155 T01500106")
    'LIFR'
    >>> test_get_condition_from_metar("KSEA 121953Z 22003KT 3/4SM FU OVC006 13/11 A3001 RMK AO2 SLPNO FU OVC006 T01280111")
    'SMOKE'
    >>> test_get_condition_from_metar("KAWO 121956Z AUTO 12003KT 1 1/2SM BR CLR 14/12 A3001 RMK AO2 SLP167 T01440122")
    'IFR'
    >>> test_get_condition_from_metar("KELN 121953Z AUTO 15005KT 1SM HZ VV015 24/08 A2992 RMK AO2 SLP120 T02440078")
    'IFR'
    >>> test_get_condition_from_metar("KPSC 121953Z 21005KT 1/2SM HZ FU VV017 26/06 A2991 RMK AO2 SLP124 T02560056 RVRNO")
    'SMOKE'
    >>> test_get_condition_from_metar("KSFF 122000Z 03004KT 3/4SM HZ FU VV006 24/04 A2997 RMK AO2 T02390039")
    'SMOKE'
    >>> test_get_condition_from_metar("KLWS 121956Z 30004KT 8SM CLR 25/03 A2994 RMK AO2 SLP131 T02500033")
    'VFR'
    >>> test_get_condition_from_metar("KMLP 121953Z AUTO 00000KT 4SM HZ CLR 22/M01 A3016 RMK AO2 SLP110 T02171006")
    'MVFR'
    >>> test_get_condition_from_metar("KMSO 121953Z 00000KT 10SM CLR 26/03 A3000 RMK AO2 SLP140 T02560028 $")
    'VFR'
    >>> test_get_condition_from_metar("KHLN 121953Z VRB03KT 10SM CLR 27/03 A3001 RMK AO2 SLP148 T02670028")
    'VFR'
    >>> test_get_condition_from_metar("KBTM 121953Z AUTO VRB03KT 10SM CLR 27/M02 A3012 RMK AO2 SLP149 T02671022")
    'VFR'
    >>> test_get_condition_from_metar("KLVM 121953Z AUTO 24012KT 10SM CLR 29/M01 A3005 RMK AO2 SLP138 T02891006")
    'VFR'
    >>> test_get_condition_from_metar("KCOD 121956Z AUTO VRB06KT 10SM CLR 27/M01 A3010 RMK AO2 SLP148 T02721006")
    'VFR'
    >>> test_get_condition_from_metar("KBIL 121953Z 22006KT 10SM CLR 27/02 A3000 RMK AO2 SLP127 T02720022")
    'VFR'
    >>> test_get_condition_from_metar("KSHR 121953Z AUTO VRB04KT 10SM CLR 28/02 A3005 RMK AO2 SLP148 T02830017")
    'VFR'
    >>> test_get_condition_from_metar("KGCC 121953Z AUTO 36010KT 10SM CLR 25/M01 A3007 RMK AO2 SLP148 T02501011")
    'VFR'
    >>> test_get_condition_from_metar("KMLS 121953Z AUTO 26009KT 10SM CLR 27/02 A2994 RMK AO2 SLP128 T02720017")
    'VFR'
    >>> test_get_condition_from_metar("KDIK 121956Z AUTO 02005KT 10SM CLR 26/01 A2992 RMK AO2 SLP125 T02560006")
    'VFR'
    >>> test_get_condition_from_metar("KHEI 121953Z AUTO VRB06KT 10SM CLR 26/01 A2996 RMK AO2 SLP133 T02560011")
    'VFR'
    >>> test_get_condition_from_metar("KBIS 121952Z VRB04KT 10SM CLR 24/07 A2990 RMK AO2 SLP121 T02440072")
    'VFR'
    >>> test_get_condition_from_metar("KMBG 121952Z AUTO 30005KT 10SM CLR 22/12 A2990 RMK AO2 SLP122 T02170117")
    'VFR'
    >>> test_get_condition_from_metar("KJMS 121956Z AUTO 00000KT 10SM SCT033 20/11 A2988 RMK AO2 SLP119 T02000111")
    'VFR'
    >>> test_get_condition_from_metar("KABR 122000Z AUTO 35005KT 10SM -RA SCT009 BKN075 OVC095 14/12 A2994 RMK AO2 P0000 T01440122")
    'VFR'
    >>> test_get_condition_from_metar("KFAR 122003Z 25005KT 10SM SCT008 OVC014 14/13 A2990 RMK AO2 T01440128")
    'MVFR'
    >>> test_get_condition_from_metar("KMOX 121955Z AUTO 34010KT 10SM SCT025 BKN050 16/11 A2991 RMK AO2")
    'VFR'
    >>> test_get_condition_from_metar("KBRD 121953Z AUTO 29006KT 10SM OVC018 15/12 A2988 RMK AO2 SLP120 T01500117 $")
    'MVFR'
    >>> test_get_condition_from_metar("KMSP 122000Z 29006KT 10SM SCT022 OVC034 17/13 A2986 RMK AO2 T01720128")
    'VFR'
    >>> test_get_condition_from_metar("KDLH 121955Z 27004KT 10SM OVC012 15/12 A2985 RMK AO2 SLP112 T01500117")
    'MVFR'
    >>> test_get_condition_from_metar("KRPD 121955Z AUTO 29004KT 10SM OVC013 16/14 A2986 RMK AO2 T01590140")
    'MVFR'
    >>> test_get_condition_from_metar("KEAU 122000Z 28005KT 5SM HZ FEW009 OVC015 17/14 A2984 RMK AO2 T01670139")
    'MVFR'
    >>> test_get_condition_from_metar("KOSH 121953Z 17008KT 10SM OVC021 21/17 A2984 RMK AO2 SLP097 T02060167")
    'MVFR'
    >>> test_get_condition_from_metar("KMSN 121953Z 18009KT 2SM -DZ BR OVC005 19/19 A2984 RMK AO2 TWR VIS 2 1/2 CIG 004V009 SLP103 P0000 T01890189")
    'LIFR'
    >>> test_get_condition_from_metar("KVOK 121956Z 28006KT 10SM FEW005 SCT014 OVC022 18/18 A2984 RMK AO2A SLP107")
    'MVFR'
    >>> test_get_condition_from_metar("KAEL 121955Z AUTO 30003KT 10SM BKN023 BKN030 BKN085 16/13 A2988 RMK AO2")
    'MVFR'
    >>> test_get_condition_from_metar("KFRM 121956Z AUTO 30007KT 10SM BKN023 BKN110 17/12 A2991 RMK AO2 SLP131 T01720117")
    'MVFR'
    >>> test_get_condition_from_metar("KOTG 121956Z AUTO 23005KT 10SM BKN011 BKN019 OVC075 14/13 A2993 RMK AO2 RAE33 CIG 006V014 SLP138 P0005 T01440128")
    'MVFR'
    >>> test_get_condition_from_metar("KSUX 121952Z 32004KT 10SM FEW014 OVC039 17/13 A2993 RMK AO2 RAB37E48 SLP133 P0000 T01670133")
    'VFR'
    >>> test_get_condition_from_metar("KFSD 122001Z VRB06KT 10SM BKN016 BKN022 BKN060 17/13 A2993 RMK AO2 T01720133")
    'MVFR'
    >>> test_get_condition_from_metar("KMHE 121953Z AUTO 32009KT 10SM SCT027 OVC049 18/12 A2994 RMK AO2 SLP138 T01830117")
    'VFR'
    >>> test_get_condition_from_metar("KPIR 121953Z AUTO 36005KT 10SM BKN070 20/11 A2993 RMK AO2 SLP132 T02000106")
    'VFR'
    >>> test_get_condition_from_metar("KPHP 121955Z AUTO 33010G18KT 10SM CLR 24/10 A2995 RMK AO2 SLP133 T02390100")
    'VFR'
    >>> test_get_condition_from_metar("KRAP 121952Z 33013G20KT 10SM CLR 25/02 A3000 RMK AO2 SLP145 T02500017")
    'VFR'
    >>> test_get_condition_from_metar("KCDR 121953Z AUTO 32009G16KT 10SM CLR 24/02 A3001 RMK AO2 SLP156 T02440022")
    'VFR'
    >>> test_get_condition_from_metar("KCPR 121953Z 00000KT 10SM CLR 26/M01 A3014 RMK AO2 SLP155 T02561006")
    'VFR'
    >>> test_get_condition_from_metar("KRIW 121953Z AUTO 09007KT 10SM CLR 24/00 A3016 RMK AO2 SLP156 T02440000")
    'VFR'
    >>> test_get_condition_from_metar("KIDA 121953Z 27007KT 10SM CLR 26/M02 A3015 RMK AO2 SLP177 T02561022")
    'VFR'
    >>> test_get_condition_from_metar("KBVS 130035Z AUTO 00000KT 2SM HZ CLR 15/13 A2996 RMK A01")
    'IFR'
    >>> test_get_condition_from_metar("KUIL 122353Z AUTO 00000KT 1SM HZ OVC021 17/11 A2996 RMK AO2 SLP144 T01670111 10167 20139 58010")
    'IFR'
    >>> test_get_condition_from_metar("KHQM 122353Z AUTO 28006KT 1 1/2SM HZ OVC027 17/12 A2996 RMK AO2 SLP148 T01670122 10172 20150 56009")
    'IFR'
    >>> test_get_condition_from_metar("KAST 122355Z AUTO 24005KT 1 1/4SM BR OVC022 14/12 A2996 RMK AO2 SLP143 T01440122 10172 20144 56006")
    'IFR'
    >>> test_get_condition_from_metar("KPDX 122353Z 00000KT 1/2SM R10R/5000FT HZ FU VV016 18/11 A2995 RMK AO2 SLP140 T01780111 10183 20133 56011")
    'SMOKE'
    >>> test_get_condition_from_metar("KSEA 122353Z 27004KT 1SM FU SCT007 OVC024 15/12 A2996 RMK AO2 SLPNO FU SCT007 FU OVC024 T01500117")
    'SMOKE'
    >>> test_get_condition_from_metar("KAWO 122356Z AUTO 32006KT 1 1/4SM BR CLR 14/12 A2996 RMK AO2 SLP151 T01440122 10156 20128 56012")
    'IFR'
    >>> test_get_condition_from_metar("KELN 130010Z AUTO 31011KT 1/2SM HZ VV015 25/02 A2990 RMK AO2 T02500022")
    'LIFR'
    >>> test_get_condition_from_metar("KPSC 122353Z 18008KT 1/2SM HZ FU VV004 26/03 A2987 RMK AO2 SLP110 T02610033 10267 20228 56009 RVRNO")
    'SMOKE'
    >>> test_get_condition_from_metar("KSFF 122353Z 02003KT 1/4SM HZ FU VV020 25/04 A2993 RMK AO2 SLP125 T02500039 10267 20178 55008")
    'SMOKE'
    >>> test_get_condition_from_metar("KLWS 122356Z 28006KT 1/2SM HZ VV015 27/02 A2990 RMK AO2 SLP117 T02670017 10283 20217 55009")
    'LIFR'
    >>> test_get_condition_from_metar("KMLP 122353Z AUTO 00000KT 1 1/4SM HZ CLR 19/01 A3015 RMK AO2 SLP110 T01940006 10222 20194 55002")
    'IFR'
    >>> test_get_condition_from_metar("KMSO 122353Z 26005KT 10SM CLR 29/04 A2993 RMK AO2 SLP118 T02940039 10300 20200 56012 $")
    'VFR'
    >>> test_get_condition_from_metar("KHLN 122353Z AUTO VRB04KT 10SM CLR 32/M02 A2994 RMK AO2 SLP119 T03221022 10322 20206 56012")
    'VFR'
    >>> test_get_condition_from_metar("KBTM 122353Z AUTO 27006G14KT 10SM CLR 28/M07 A3008 RMK AO2 SLP143 T02781072 10289 20228 56005")
    'VFR'
    >>> test_get_condition_from_metar("KLVM 122353Z AUTO 26011KT 10SM CLR 29/M03 A3002 RMK AO2 SLP131 T02891033 10306 20239 55003")
    'VFR'
    >>> test_get_condition_from_metar("KCOD 122356Z AUTO 13012KT 10SM CLR 26/00 A3007 RMK AO2 SLP145 T02610000 10278 20239 53002")
    'VFR'
    >>> test_get_condition_from_metar("KBIL 122353Z 23010KT 10SM FEW200 29/01 A2996 RMK AO2 SLP114 T02940011 10300 20239 55005")
    'VFR'
    >>> test_get_condition_from_metar("KSHR 122353Z AUTO 19006KT 10SM CLR 28/03 A3002 RMK AO2 SLP140 T02780028 10300 20244 55005")
    'VFR'
    >>> test_get_condition_from_metar("KGCC 122353Z AUTO 25004KT 10SM CLR 26/M03 A3006 RMK AO2 SLP143 T02611028 10272 20217 55001")
    'VFR'
    >>> test_get_condition_from_metar("KMLS 122353Z AUTO 18006KT 10SM CLR 30/02 A2989 RMK AO2 SLP111 T03000017 10300 20233 56010")
    'VFR'
    >>> test_get_condition_from_metar("KDIK 122356Z AUTO 24006KT 10SM CLR 26/03 A2991 RMK AO2 SLP123 T02610028 10272 20239 56002")
    'VFR'
    >>> test_get_condition_from_metar("KHEI 122353Z AUTO 00000KT 10SM CLR 26/03 A2996 RMK AO2 SLP138 T02560033 10272 20233 53001")
    'VFR'
    >>> test_get_condition_from_metar("KBIS 122352Z AUTO 22004KT 10SM CLR 26/05 A2990 RMK AO2 SLP123 T02610050 10272 20217 53001 $")
    'VFR'
    >>> test_get_condition_from_metar("KMBG 122352Z AUTO 00000KT 10SM CLR 24/11 A2992 RMK AO2 SLP124 T02390111 10256 20183 53005")
    'VFR'
    >>> test_get_condition_from_metar("KJMS 122356Z AUTO 24007KT 10SM CLR 22/11 A2988 RMK AO2 SLP118 T02170106 10228 20161 53003")
    'VFR'
    >>> test_get_condition_from_metar("KABR 122353Z AUTO 00000KT 10SM CLR 19/13 A2994 RMK AO2 SLP139 60011 T01890128 10200 20139 53004")
    'VFR'
    >>> test_get_condition_from_metar("KFAR 122353Z AUTO 22005KT 10SM CLR 16/13 A2989 RMK AO2 SLP124 60015 T01560128 10172 20128 55001")
    'VFR'
    >>> test_get_condition_from_metar("KMOX 130035Z AUTO 32006KT 10SM OVC034 15/11 A2994 RMK AO2")
    'VFR'
    >>> test_get_condition_from_metar("KBRD 130035Z AUTO 28004KT 10SM SCT026 OVC038 15/12 A2989 RMK AO2 T01500117 $")
    'VFR'
    >>> test_get_condition_from_metar("KMSP 130023Z 32007KT 10SM SCT023 BKN029 OVC050 17/12 A2990 RMK AO2 T01670122")
    'MVFR'
    >>> test_get_condition_from_metar("KDLH 130023Z 30006KT 8SM FEW018 SCT024 OVC034 14/12 A2986 RMK AO2 DZE11 P0000 T01390122")
    'VFR'
    >>> test_get_condition_from_metar("KRPD 130035Z AUTO 27004KT 1 3/4SM DZ OVC006 14/14 A2989 RMK AO2 P0001 T01410140")
    'IFR'
    >>> test_get_condition_from_metar("KEAU 122356Z 27007KT 10SM OVC042 17/13 A2987 RMK AO2 SLP114 60000 T01670133 10172 20161 53011")
    'VFR'
    >>> test_get_condition_from_metar("KOSH 130044Z 27013KT 10SM BKN009 BKN013 OVC021 18/17 A2984 RMK AO2 RAB2359E17 P0001 T01830167")
    'IFR'
    >>> test_get_condition_from_metar("KMSN 130027Z VRB04KT 10SM FEW007 SCT012 OVC022 17/17 A2988 RMK AO2 DZE27 P0001 T01670167")
    'MVFR'
    >>> test_get_condition_from_metar("KVOK 122356Z AUTO 28005KT 10SM OVC040 17/17 A2987 RMK AO2 SLP118 60006 T01650165 10194 20165 52012")
    'VFR'
    >>> test_get_condition_from_metar("KAEL 130035Z AUTO 00000KT 10SM SCT060 OVC080 14/13 A2993 RMK AO2")
    'VFR'
    >>> test_get_condition_from_metar("KFRM 122356Z AUTO 21005KT 10SM OVC065 14/13 A2994 RMK AO2 RAB01E15 SLP142 P0000 60002 T01440133 10172 20144 51009")
    'VFR'
    >>> test_get_condition_from_metar("KOTG 122356Z AUTO 26005KT 10SM OVC075 15/13 A2996 RMK AO2 SLP147 60008 T01500128 10167 20133 53008")
    'VFR'
    >>> test_get_condition_from_metar("KSUX 122352Z AUTO 31005KT 10SM CLR 18/13 A2996 RMK AO2 SLP143 60000 T01780128 10189 20150 53008")
    'VFR'
    >>> test_get_condition_from_metar("KFSD 122356Z 31010KT 10SM FEW031 BKN055 18/11 A2995 RMK AO2 SLP143 T01830111 10206 20144 53008")
    'VFR'
    >>> test_get_condition_from_metar("KMHE 122353Z AUTO 32004KT 10SM OVC036 18/12 A2998 RMK AO2 SLP151 T01780117 10194 20172 53009")
    'VFR'
    >>> test_get_condition_from_metar("KPIR 122353Z AUTO 29003KT 10SM CLR 22/11 A2994 RMK AO2 SLP134 T02170106 10233 20144 53003")
    'VFR'
    >>> test_get_condition_from_metar("KPHP 122355Z AUTO 02005KT 10SM CLR 26/04 A2997 RMK AO2 SLP140 T02560039 10267 20194 53009")
    'VFR'
    >>> test_get_condition_from_metar("KRAP 122352Z 35008KT 10SM CLR 24/M01 A3002 RMK AO2 SLP152 T02441006 10261 20222 53009")
    'VFR'
    >>> test_get_condition_from_metar("KCDR 122353Z AUTO 06006KT 10SM CLR 26/04 A3003 RMK AO2 SLP156 T02610039 10272 20217 53006")
    'VFR'
    >>> test_get_condition_from_metar("KCPR 122353Z AUTO 27007KT 10SM CLR 25/M02 A3012 RMK AO2 SLP152 T02501017 10261 20211 56002")
    'VFR'
    >>> test_get_condition_from_metar("KRIW 122353Z AUTO 12008KT 10SM CLR 26/M02 A3011 RMK AO2 SLP142 T02561017 10261 20206 56008")
    'VFR'
    >>> test_get_condition_from_metar("KIDA 122353Z AUTO 24007KT 10SM CLR 27/M02 A3010 RMK AO2 SLP163 T02721017 10278 20217 56009")
    'VFR'
    """

    metar: Metar = Metar(metar_report)

    return metar.get_category()


def test_get_color_from_condition(category: str) -> str:
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [tuple] -- The color (also a tuple) and if it should blink.

    >>> test_get_color_from_condition('VFR')
    'GREEN'
    >>> test_get_color_from_condition('MVFR')
    'BLUE'
    >>> test_get_color_from_condition('IFR')
    'RED'
    >>> test_get_color_from_condition('LIFR')
    'MAGENTA'
    >>> test_get_color_from_condition('SMOKE')
    'WHITE'
    >>> test_get_color_from_condition('')
    'OFF'
    >>> test_get_color_from_condition('INOP')
    'OFF'
    >>> test_get_color_from_condition(None)
    'OFF'
    """

    return flight_rules_visualizer.get_color_from_condition(category)


if __name__ == "__main__":
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")
