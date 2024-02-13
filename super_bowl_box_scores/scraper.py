from dataclasses import dataclass
from enum import Enum
import sys

from bs4 import BeautifulSoup, NavigableString, Tag
import requests


URL = 'https://www.footballdb.com/seasons/super-bowls.html'


class Conference(str, Enum):
    AFC = "AFC"
    NFC = "NFC"
    NFL = "NFL"
    AFL = "AFL"

@dataclass
class Team:
    name: str
    box_score: list[int]
    conference: Conference

    def serialize(self) -> str:
        return ",".join(
            [self.name, self.conference.value, *[str(s) for s in self.box_score]]
        )

def transform_row_to_team(row: Tag) -> Team:
    td_s = row.find_all('td')

    raw_name: str = td_s[0].find_all('span')[1].text
    if Conference.AFC in raw_name:
        conference = Conference.AFC
    elif Conference.NFC in raw_name:
        conference = Conference.NFC
    elif Conference.NFL in raw_name:
        conference = Conference.NFL
    elif Conference.AFL in raw_name:
        conference = Conference.AFL
    else:
        raise Exception(f"Unexpected Confrence, {raw_name}")
    name = raw_name.split(" ")[0]

    box_score = [int(quarter.text) for quarter in td_s[1:5]]

    return Team(name=name, box_score=box_score, conference=conference)


def transform_table_to_teams(table: Tag) -> tuple[Team, Team]:
    # Skip first result because it's the table header
    _, first_row, second_row = table.find_all('tr')

    first_team = transform_row_to_team(first_row)
    second_team = transform_row_to_team(second_row)

    return first_team, second_team


def main() -> None:
    page = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )

    soup = BeautifulSoup(page.text, 'html.parser')

    data_page = soup.find("div", {"id": "leftcol"})
    if data_page is None:
        print("Couldn't find div with id=leftcol")
        sys.exit(1)
    if isinstance(data_page, NavigableString):
        print("Expected <div>, found string")
        sys.exit(1)

    tables = data_page.find_all('table')
    
    games = [transform_table_to_teams(table) for table in tables]
    
    super_bowl = 58
    for (team1, team2) in games:
        with open(f"sb_{super_bowl}.csv", 'w') as f:
            f.write("Name,Conference,Q1,Q2,Q3,Q4,OT\n")
            f.write(f"{team1.serialize()},\n")
            f.write(f"{team2.serialize()},\n")

        super_bowl -= 1

if __name__ == "__main__":
    main()
