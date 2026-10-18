"""
Netezirea drumului (post-procesare) prin metoda „line of sight”
(string pulling): din fiecare punct sărim direct la cel mai îndepărtat
punct următor al drumului care se vede în linie dreaptă, adică segmentul
dintre ele trece doar prin celule libere.

Rezultatul: drum mai scurt și mult mai puține viraje, ceea ce
ajută robotul fizic (fiecare viraj introduce erori de poziționare).
"""


def netezeste(graf, puncte):
    if len(puncte) <= 2:
        return list(puncte)
    rezultat = [puncte[0]]
    i = 0
    while i < len(puncte) - 1:
        # cel mai îndepărtat punct vizibil din puncte[i]
        j = len(puncte) - 1
        while j > i + 1 and not graf.segment_liber(puncte[i], puncte[j]):
            j -= 1
        rezultat.append(puncte[j])
        i = j
    return rezultat
