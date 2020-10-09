import requests
from bs4 import BeautifulSoup as BS
file_name = ""  # zjednoduseni predavky nazvu souboru (nemusi propadat vsema funkcema jako parametr)


def csv_export(dict_in):
    import csv
    with open(str(file_name)+".csv", "a+", newline="") as file:
        writer = csv.DictWriter(file, dict_in.keys())
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(dict_in)
    file.close()


def remove_html_tags(text):
    import re
    text = text.replace("\t", "")
    text = text.replace("\n", "")
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def page_scraper_zahranici(url_in):
    response = requests.get(url_in)
    soup = BS(response.text, "html.parser")
    links = []
    tables = soup.find_all("table")
    for i in range(len(tables)):
        cols = tables[i].find_all("td")
        for j in range(len(cols)):
            cells = cols[j].find_all("a")
            if cells:
                if "okrsek" in str(cells):
                    links.append(cells)

    for i in range(len(links)):
        temp_str = str(links[i]).replace("amp;", "")
        link_ok = "https://volby.cz/pls/ps2017nss/" + str(temp_str[temp_str.find('href="') + 6:temp_str.find('">')])
        scrape_vyber(link_ok)


def page_scraper_kraj(code_in):  # republika in

    response = requests.get("https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ")
    soup = BS(response.text, "html.parser")
    tables = soup.find_all("table")
    xlinks = []
    for i in range(len(tables)):
        cols = tables[i].find_all("tr")
        for j in range(2, len(cols), 1):
            cells = cols[j].find_all("a")
            if "kraj" in str(cells[0]):  # filtr ceske kraje
                xlinks.append(cells[2])

    for k in range(len(xlinks)):
        if code_in == 0:
            if "amp;" in str(xlinks[k]):
                temp_str = str(xlinks[k]).replace("amp;", "")
                link_ok = "https://volby.cz/pls/ps2017nss/" + \
                          str(temp_str[temp_str.find('href="')+6:temp_str.find('">X')])
                page_scraper_obec(link_ok)
        else:
            if "xkraj="+str(code_in)+"&" in str(xlinks[k]):
                if "amp;" in str(xlinks[k]):
                    temp_str = str(xlinks[k]).replace("amp;", "")
                    link_ok = "https://volby.cz/pls/ps2017nss/" + str(
                        temp_str[temp_str.find('href="') + 6:temp_str.find('">X')])
                    page_scraper_obec(link_ok)


def page_scraper_obec(url_in):  # kraj in
    if "vyber" in str(url_in):
        scrape_vyber(url_in)
    else:
        response = requests.get(url_in)
        soup = BS(response.text, "html.parser")
        xlinks = []
        tables = soup.find_all("table")
        for i in range(len(tables)):
            col = tables[i].find_all("tr")
            for j in range(2, len(col), 1):
                cells = col[j].find_all("td")
                xlinks.append(cells[2])

        for k in range(len(xlinks)):
            temp_str = str(xlinks[k]).replace("amp;", "")
            link_ok = "https://volby.cz/pls/ps2017nss/" + \
                      str(temp_str[temp_str.find('href="') + 6:temp_str.find('">X')])
            if "vyber" in str(link_ok):
                scrape_vyber(link_ok)
            else:
                page_scraper_okrsek(link_ok)


def page_scraper_okrsek(url_in):  # obec link in
    response = requests.get(url_in)
    soup = BS(response.text, "html.parser")
    links = []
    tables = soup.find_all("table")
    for i in range(len(tables)):
        col = tables[i].find_all("tr")
        for j in range(1, len(col), 1):
            rows = col[j].find_all("td")
            for k in range(len(rows)):
                cells = rows[k].find_all("a")
                if cells:
                    links.append(cells)

    for i in range(len(links)):
        temp_str = str(links[i]).replace("amp;", "")
        scrape_vyber("https://volby.cz/pls/ps2017nss/" +
                     str(temp_str[temp_str.find('href="') + 6:temp_str.find('">')]))


def scrape_vyber(link_in):  # vstup jen vyber
    response = requests.get(link_in)
    soup = BS(response.text, "html.parser")
    tables = soup.find_all("table")

    scraped_votes = {}
    code = str(link_in[link_in.find("obec=") + 5:link_in.find("obec=") + 11])
    names = remove_html_tags(str(soup.find_all("h3"))).split(',')

    try:  # vyjimka pro stranky odlisneho templatu jako treba Praha Benice
        district = names[2]
        if district[-1:].isalnum() == False:
            district = district[:-1]
        scraped_votes.update({"Code": code})
        scraped_votes.update({"Location": names[1][7:]})
    except IndexError:
        district = "--"
        scraped_votes.update({"Code": code})
        scraped_votes.update({"Location": names[1][7:-1]})

    scraped_votes.update({"District": district})

    print(code, names[1][7:], district)

    try:
        for i in range(0, len(tables), 1):
            rows = tables[0].find_all("tr")
            for j in range(1, len(rows), 1):
                cells = rows[j].find_all("td")
                registered = cells[0].getText()
                envelopes = cells[1].getText()
                valid = cells[3].getText()
    except IndexError:
        for i in range(0, len(tables), 1):
            rows = tables[0].find_all("tr")
            for j in range(2, len(rows), 1):
                cells = rows[j].find_all("td")
                registered = cells[4].getText()
                envelopes = cells[5].getText()
                valid = cells[7].getText()

    scraped_votes.update({"Registered": registered})
    scraped_votes.update({"Envelopes": envelopes})
    scraped_votes.update({"Valid": valid})

    for i in range(1, len(tables), 1):
        rows = tables[i].find_all("tr")
        for j in range(2, len(rows), 1):
            cells = rows[j].find_all("td")
            party = cells[1].getText()
            amount = cells[2].getText()
            if (party != "-") or (amount != "-"):
                scraped_votes.update({str(party): int(amount)})
    csv_export(scraped_votes)


def main():
    import sys
    global file_name

    print('''\n---=== VOLBY 2017 - RESULT SCRAPER ===---\n\n1 - Hlavní město Praha\n2 - Středočeský kraj
3 - Jihočeský kraj\n4 - Plzeňský kraj\n5 - Karlovarský kraj\n6 - Ústecký kraj\n7 - Liberecký kraj
8 - Královéhradecký kraj\n9 - Pardubický kraj\n10 - Kraj Vysočina\n11 - Jihomoravský kraj\n12 - Olomoucký kraj
13 - Zlínský kraj\n14 - Moravskoslezský kraj\n99 - Zahraničí
0 - Celá Česká republika vč. zahraničí (TRVÁ VÍC JAK HODINU + MOŽNOST ODPOJENÍ ZE STRANY SERVERU)\n''')

    selection = input("Zadejte kód kraje: ")
    confirm = None

    while confirm is not True:
        if selection.isdigit() is True:
            if -1 < int(selection) < 15:
                file_name = input("Pod jakým jmenem chcete .csv souboru uložit? ")
                page_scraper_kraj(selection)
                confirm = True
            elif int(selection) == 99:
                file_name = input("Pod jakým jmenem chcete .csv souboru uložit? ")
                page_scraper_zahranici("https://volby.cz/pls/ps2017nss/ps36?xjazyk=CZ")
                confirm = True
            else:
                selection = input("Chybný kód kraje! Cislo? ")
        elif (selection == "k") or (selection == "K"):
            print("Konec programu.")
            sys.exit()
        else:
            selection = input("Chybný kód kraje! Cislo? ")


if __name__ == "__main__":
    main()
