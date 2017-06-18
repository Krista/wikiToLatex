import re
import wikitextparser as wt
from pprint import pprint

from xml.etree import ElementTree as ET
#import urllib2

#response = urllib2.urlopen('http://www.example.com/')
#html = response.read()

medz = "\t"

##vypise obsah kde level vyznaci TABULATORY
def print_structure(a):
    for i in a.sections:
        print(medz * i.level, end="")
        print(i.title.strip())
        print(medz * (i.level + 1), end="")
        links(i.wikilinks)

#vypise wikilinky ktore su v poli a
def links(a):
    for i in a:
        print(i, end="")
    print()

#vypise wikilinky s odsekom podla levelu
def print_links(a):
    for i in a.wikilinks:
        print(medz * i._indent_level, end="")
        print(i.target.strip())

########################################################################################################################

# prvy odsek dostane nazov introduction a zvysne su zaradene do kapitol
# a podkapitol podla levelu
# vracia latexovy string
def titul(str, lev):
    if str=='':
        return "\chapter*{Introduction}"
    titl = ["","\n\chapter", "\n\section", "\n\subsection"]
    pom = titl[lev-1] + "{" + str + "}"
    return pom

# z wikitextu vyberie nadpisy, skonvertuje do latexu a prislusny obsah k nemu vlozi za nim
# ak ma sekcia podkapitoly, v .contents je aj ten text,
# preto chceme zobrat len prvu cast - i.contents.split("===")
# vratime ako zoznam sekcii
def simplePrint(a):
    full = []
    for i in a.sections:
        text = ""
        p = i.title.strip()
        if p in ignorlist: #casti ktore nechceme mat v dokumente
            continue
        text += titul(i.title.strip(), i.level) + "\n"
        text += i.contents.split("===")[0]
        #text += linkToItalic(i.wikilinks, i.contents.split("===")[0])
        full.append(text)
    return full


# v texte vsetky wikilinky nahradi LaTeXovym \textit pripadne
# ak sa jedna o obrazok alebo file skonvertuje obrazky
def convertLinks(links, text):
    pom = text
    for i in links:
        sub = i[2:-2].split("|")
#            if sub[0].startswith("Category"): # odkazy na konci - chceme vymazat -- mazeme celu sekciu
#                pom = pom.replace(i.string, "")
        if sub[0].startswith(("Image","File")):  # formatujeme obrazok
            #print(i.string)
            pom = convertPict(i.string, pom)
        else: #normalna wikilinka -snad
            repl = sub[1] if len(sub) > 1 else sub[0]
            pom = pom.replace(i.string, "\\textit{" + repl + "}")
    return pom

# TODO treba stiahnut obrazky - nahradit text TU BUDE OBRAZOK
# prerobi wikilinku na prikaz v latexe
def convertPict(link, text):
    sub = link[2:len(link)-2].split(":")
    pom = sub[1].split("|")
    name = pom[0].split("-")[-1].strip()
    #picture = "\includegraphics[width=6cm]{" + name + "}"
    picture = "\\begin{figure}\n\centering\n\includegraphics[width=6cm]{picture/obr.jpg}\n" #pos = pom[1]
    if len(pom) > 2:
        desc = pom[2]
        picture += "\caption{" + desc + "}\n"
    picture += "\\end{figure}"
    text = text.replace(link, picture)
    #text = text.replace(link, "\nTU BUDE OBRAZOK\n")
    return text

#nahradi bold vo wiki = ''' ... ''' latexovou verziou \textbf{}
def convertBold(text):
    kde = 1
    pom = text.split("'''")
    for i in range(len(pom)):
        if i % 2 == kde:
            pom[i] = "\\textbf{" + pom[i] + "}"
    return ''.join(pom)

#nahradi italic vo wiki = '' ... '' latexovou verziou \textit{}
# najskor musi byt zavolane convertBold
def convertItalic(text):
    kde = 1
    text = text.split("''")
    for i in range(len(text)):
        if i % 2 == kde:
            text[i] = "\\textit{" + text[i] + "}"
    return ''.join(text)


# odstrani z textu riadky, ktore su v {{}} a nevieme ich zparsovat (zatial parsujeme len cit*)
# - su to napr. poznamky na zlepsenie clanku
def removeUnnesesery(text):
    s = re.findall("(\{\{(?!cit).*?\}\})", text, re.IGNORECASE)
    print("toto sme odstranili:", end ="")
    for i in s:
        print(i)
        text = text.replace(i,"")
    return text

# prerobi html znacku &mdash na "-"
def removeDash(text):
    text = text.replace("&mdash;", "-")
    return text

#TODO - referencie v texte treba prerobit na bibliograficke odkazy
# a zaznamy v REF prerobit na latexove bibitem
def convertRef(text):
    bibtech = "\\begin{thebibliography}{9}\n"
    s = re.findall("(\<ref\>.*?\<\/ref\>)", text, re.IGNORECASE)
    poc = 0
    for i in s:
        text = text.replace(i, "\cite{refer" + str(poc) + "}")  # len toto chceme mat v texte
        #spracovavam 1 referenciu
        ref = re.sub("\<\/*ref\>", "", i) #odstranim <ref><\ref>
        lin = re.findall("(http.* )", i)
        lin = re.findall("(?P<url>http[s]?://[^\s]+)",ref)
        #lin = re.sub("(\{\{)", "", lin)
        #lin = re.sub("(\}\}.*)", "", lin)
        bibtech += "\n\n\\bibitem{refer" + str(poc) + "}\n" #zaciatok bibitemu

        poc += 1
        for l in lin: #latexove formatovanie http
            ref = ref.replace(l, "\\texttt{" + l + "}")

        if not ref.startswith("{{"): #neformatujeme
            bibtech += ref
        else:
            rozloz = ref[2:-2].split("|")
            ref = ""
            for z in rozloz[1:]: #tu sa skaredo snazim odkusnut prvu cast po =
                r = z.split("=")
                w = "=".join(r[1:])
                if len(w) > 0:
                    ref += w + ", "
            bibtech += ref[:-2]
    bibtech += "\n\n\\end{thebibliography}"
        #print(ref)
        #text = text.replace(i,"(TODO - referencia na literaturu)")
    return bibtech, text

# odrazkove zoznamy prerobi na latexovy format (vo wikitexte zacina *)
def convertItemize(text):
    lines = text.split("\n")
    for i in range(len(lines)):
        if lines[i].startswith("*"):
            lines[i] = "\n\\begin{itemize} \n \item {" + lines[i][1:].strip() + "}"
            i += 1
            while i < len(lines) and lines[i].startswith("*"):
                lines[i] = "\n\item {" + lines[i][1:].strip() + "}"
                i += 1
            lines[i-1] += " \n\\end{itemize}\n"
    #treba najst prvy vyskyt a potom while kym to plati
    return '\n'.join(lines)

# to iste ako itemize ale zoznam je cislovany (vo wikitexte zacina #)
def convertEnumerate(text):
    lines = text.split("\n")
    for i in range(len(lines)):
        if lines[i].startswith("#"):
            lines[i] = "\n\\begin{enumerate} \n \item {" + lines[i][1:].strip() + "}"
            i += 1
            while i < len(lines) and lines[i].startswith("#"):
                lines[i] = "\n\item {" + lines[i][1:].strip() + "}"
                i += 1
            lines[i-1] += " \n\\end{enumerate}\n"
    #treba najst prvy vyskyt a potom while kym to plati
    return '\n'.join(lines)

#nefunguje - pouzivame ignorlist
def removeSection(name, q):
    for sec in range(len(q.sections)):
        if q.sections[sec].title == name:
            del q.sections[sec]

########################################################################################################################
#
# f = open("nonogram.wiki", 'r')
# text = f.read()
#
# w = re.sub("(<!--.*?-->)", "", text)  ##wikistranka bez komentarov
# f2 = open("output", 'w')
# f2.write(w)


#html = ET.parse("nonogram.wiki")
ignorlist = ['See also', 'External links', 'References', 'Example'] # mozeme dat aj ako argument

# # TODO nahrad
f = open("output", 'r') # docasne.. aby sme nemuseli stale stahovat
w = f.read()

q= wt.parse(w) #carovnym nastrojom zparsujeme stranku

wikilinks = [] #pokope vsetky linky
for i in q.wikilinks:
    wikilinks.append(i.target)

#q.string = removeUnnesesery(q.string) #rozne poznamky
#q.string = convertRef(q.string)
bibtech = []

textArray = simplePrint(q)

#for i in textArray:
i = ''.join(textArray)
i = convertLinks(q.wikilinks, i)
i = removeUnnesesery(i)
i = removeDash(i)
b, i = convertRef(i)
bibtech.append(b)
i = convertBold(i)
i = convertItalic(i)
i = convertItemize(i)
i = convertEnumerate(i)

i += b

f = open("bakalar.tex", 'w')
f.write(i)
f.close()

r = re.findall("(\{\{.*?\}\})", w)
s = re.findall("(\{\{(?!cit).*?\}\})", w, re.IGNORECASE)

toto = re.findall("(\[\[.*\]\])", i)
print(toto)