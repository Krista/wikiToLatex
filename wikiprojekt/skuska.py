import re
import wikitextparser as wt
from pprint import pprint

from xml.etree import ElementTree as ET
#import urllib2

#response = urllib2.urlopen('http://www.example.com/')
#html = response.read()

medz = "\t"

def titul(str, lev):
    if str=='':
        return "\chapter*{Introduction}"
    titl = ["","\n\chapter", "\n\section", "\n\subsection"]
    pom = titl[lev-1] + "{" + str + "}"
    return pom

#v texte vsetky wikilinky nahradi LaTeXovym \textit
def linkToItalic(links, text):
    pom = findItemize(text)
    for i in links:
        sub = i[2:len(i)-2].split("|")
        if sub[0] in wikilinks:
            if sub[0].startswith("Category"):#odkazy na konci - chceme vymazat
                pom = pom.replace(i.string, "")
            if sub[0].startswith(("Image","File")):  # formatujeme obrazok
                #print(i.string)
                pom = addPic(i.string, pom)
            else: #normalna wikilinka -snad
                repl = sub[1] if len(sub) > 1 else sub[0]
                pom = pom.replace(i.string, "\\textit{" + repl + "}")
    pom = convertWikiBoldItalic(pom)
    return pom

def addPic(link, text):
    sub = link[2:len(link)-2].split(":")
    pom = sub[1].split("|")
    name = pom[0].split("-")[-1].strip()
    picture = "\includegraphics[width=6cm]{" + name + "}"
    #pos = pom[1]
    if len(pom) > 2:
        desc = pom[2]
        picture += "\caption{" + desc + "}"
    #text = text.replace(link, picture)
    text = text.replace(link, "\nTU BUDE OBRAZOK\n")
    return text


def convertWikiBoldItalic(text):
    kde = 1
    #if text.startswith("'''"):
    #    kde = 0
    pom = text.split("'''")
    for i in range(len(pom)):
        if i % 2 == kde:
            pom[i] = "\\textbf{" + pom[i] + "}"
    pom = ''.join(pom)
    pom = pom.split("''")
    for i in range(len(pom)):
        if i % 2 == kde:
            pom[i] = "\\textit{" + pom[i] + "}"
    return ''.join(pom)


##vypise obsah kde level vyznaci TABULATORY
def print_structure(a):
    for i in a.sections:
        print(medz * i.level, end="")
        print(i.title.strip())
        print(medz * (i.level + 1), end="")
        links(i.wikilinks)

def links(a):
    for i in a:
        print(i, end="")
    print()

def print_links(a):
    for i in a.wikilinks:
        print(medz * i._indent_level, end="")
        print(i.target.strip())

#vypiseme do suboru nadpis a prislusny text
def simplePrint(a):
    f = open("bakalar.tex", 'w')
    for i in a.sections:
        p = i.title.strip()
        if p in ignorlist:
            continue
        f.write(titul(i.title.strip(), i.level))
        f.write("\n")
        #ak ma sekcia podkapitoly, v .contents je aj ten text, preto chceme zobrat len prvu cast - i.contents.split("===")
        f.write(linkToItalic(i.wikilinks, i.contents.split("===")[0]))
    f.close()

def odtranBordel(text):
    text.replace("&mdash;", "-")
    s = re.findall("(\{\{(?!cit).*?\}\})", text, re.IGNORECASE)
    for i in s:
        print(i)
        text = text.replace(i,"")
    return text

def findRef(text):
    s = re.findall("(\<ref\>.*?\<\/ref\>)", text, re.IGNORECASE)
    for i in s:
        ref = re.sub("\<\/*ref\>", "", i) #odstranim <ref><\ref>
        lin = re.findall("(http.* )", i)
        for j in lin:
            ref.replace(j, "\\texttt{" + j + "}")
        # if not ref.startswith("{{"):
        #     rozloz = ref.split()
        #     for j in rozloz:
        #         if j.startswith("http"):
        #             j = "\texttt{" + i + "}"
        #     ref = ''.join(rozloz)
        # else:
        #     rozloz = ref[2:-2].split("|")
        #     for x in range[1..len(rozloz)-1]:
        #
        #     if rozloz[0] == "Cite book":

        print(ref)
        text = text.replace(i,"(TODO - referencia na literaturu)")
    return text

def findItemize(text):
    lines = text.split("\n")
    for i in range(len(lines)):
        if lines[i].startswith("*"):
            lines[i] = "\n\\begin{itemize} \item {" + lines[i][1:].strip() + "}"
            i += 1
            while i < len(lines) and lines[i].startswith("*"):
                lines[i] = "\item {" + lines[i][1:].strip() + "}"
                i += 1
            lines[i-1] += " \\end{itemize}\n"
    #treba najst prvy vyskyt a potom while kym to plati
    return ''.join(lines)

def removeSection(name, q):
    for sec in range(len(q.sections)):
        if q.sections[sec].title == name:
            del q.sections[sec]
# f = open("nonogram.wiki", 'r')
# text = f.read()
# w = re.sub("(<!--.*?-->)", "", text)
# ##wikistranka bez komentarov
# f2 = open("output", 'w')
# f2.write(w)


#html = ET.parse("nonogram.wiki")
ignorlist = ['See also', 'External links']
f = open("output", 'r')
w = f.read()

q= wt.parse(w)

q.string = odtranBordel(q.string)
q.string = findRef(q.string)

wikilinks = []
for i in q.wikilinks:
    wikilinks.append(i.target)

q.tables.clear()

simplePrint(q)

r = re.findall("(\{\{.*?\}\})", w)
s = re.findall("(\{\{(?!cit).*?\}\})", w, re.IGNORECASE)


