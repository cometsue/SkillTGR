from operators import *


operator_parameter_dict = {
    "add_column": (
        "addColumn",
        add_column_func,
        {},
        dict(
            temperature=0.0,
            top_p=1.0,
            max_tokens=256,
            n=1
        ),
    ),
    "select_column": (
        "selectColumn",
        select_column_func,
        {},
        dict(
            temperature=0.0,
            top_p=1.0,
            max_tokens=1024,
            n=1
        ),
    ),
    "select_row": (
        "selectRow",
        select_row_func,
        {},
        dict(
            temperature=0.5,
            top_p=1.0,
            max_tokens=256,
            n=4
        ),
    ),
    "group_column": (
        "groupColumn",
        group_column_func,
        dict(skip_op=[]),
        dict(
            temperature=0.0,
            top_p=1.0,
            max_tokens=256,
            n=1
        ),
    ),
    "sort_column": (
        "sortColumn",
        sort_column_func,
        dict(skip_op=[]),
        dict(
            temperature=0.0,
            top_p=1.0,
            max_tokens=256,
            n=1
        ),
    ),
}

possible_next_operator_dict = {
    "<init>": [
        "add_column",
        "select_row",
        "select_column",
        "group_column",
        "sort_column",
    ],
    "add_column": [
        "select_row",
        "select_column",
        "group_column",
        "sort_column",
        "<END>",
    ],
    "select_row": [
        "select_column",
        "group_column",
        "sort_column",
        "<END>",
    ],
    "select_column": [
        "group_column",
        "sort_column",
        "<END>",
    ],
    "group_column": [
        "sort_column",
        "<END>",
    ],
    "sort_column": [
        "<END>",
    ],
}


plan_full_demo_simple = """Here are examples of using the operations to answer the question.


/*
col : date | division | league | regular season | playoffs | open cup | avg. attendance
row 1 : 2001/01/02 | 2 | usl a-league | 4th, western | quarterfinals | did not qualify | 7,169
row 2 : 2002/08/06 | 2 | usl a-league | 2nd, pacific | 1st round | did not qualify | 6,260
row 5 : 2005/03/24 | 2 | usl first division | 5th | quarterfinals | 4th round | 6,028
*/
Question: what was the last year where this team was a part of the usl a-league?
Function Chain: f_add_column(year) -> f_select_row(row 1, row 2) -> f_select_column(year, league) -> f_sort_column(year) -> <END>

*/
col : rank | lane | athlete | time
row 1 : 1 | 6 | manjeet kaur (ind) | 52.17
row 2 : 2 | 5 | olga tereshkova (kaz) | 51.86
row 3 : 3 | 4 | pinki pramanik (ind) | 53.06
*/
Question: How many athletes are actually from India?
Function Chain: f_add_column(country of athletes) -> f_select_row(row 1, row 3) -> f_select_column(athlete, country of athletes) -> f_group_column(country of athletes) -> <END>

/*
col : week | when | kickoff | opponent | results; final score | results; team record | game site | attendance
row 1 : 1 | saturday, april 13 | 7:00 p.m. | at rhein fire | w 27–21 | 1–0 | rheinstadion | 32,092
row 2 : 2 | saturday, april 20 | 7:00 p.m. | london monarchs | w 37–3 | 2–0 | waldstadion | 34,186
row 3 : 3 | sunday, april 28 | 6:00 p.m. | at barcelona dragons | w 33–29 | 3–0 | estadi olímpic de montjuïc | 17,503
*/
Question: When is the competition with highest points scored played?.
Function Chain: f_add_column(points scored) -> f_select_row(*) -> f_select_column(when, points scored) -> f_sort_column(points scored) -> <END>

/*
col : iso/iec standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2011) | 7
*/
Question: How many standards are published in 2011
Function Chain: f_add_column(year) -> f_select_row(row 3) -> f_select_column(year) -> f_group_column(year) -> <END>"""



plan_select_column_demo = """If the table only needs a few columns to answer the question, we use f_select_column() to select these columns for it. For example,
/*
col : code | county | former province | area (km2) | population | capital
row 1 : 1 | mombasa | coast | 212.5 | 939,370 | mombasa (city)
row 2 : 2 | kwale | coast | 8,270.3 | 649,931 | kwale
row 3 : 3 | kilifi | coast | 12,245.9 | 1,109,735 | kilifi
*/
Question: What is its exact population of momasa？
Function: f_select_column(county, population)
Explanation: The question is asking to know the exact population figure of Mombasa. We need to look at the "county" and "population" columns to check if Mombasa meets the population criteria and to obtain its specific population value."""


plan_add_column_demo = """If the table does not have the needed column to answer the quesion, we use f_add_column() to add a new column for it. For example,
/*
col : rank | lane | player | time
row 1 :  | 5 | olga tereshkova (kaz) | 51.86
row 2 :  | 6 | manjeet kaur (ind) | 52.17
row 3 :  | 3 | asami tanno (jpn) | 53.04
*/
Question: how many athletes come from Japan?
Function: f_add_column(country of athlete)
Explanation: The question asks about the number of athletes from japan. Each row is about one athlete. We need to know the country of each athlete. We extract the value from column "Player" and create a different column "Country of athletes" for each row. The datatype is String."""


plan_select_row_demo = """If the table only needs a few rows to answer the question, we use f_select_row() to select these rows for it. For example,
/*
table caption : jeep grand cherokee.
col : years | displacement | engine | power | torque
row 1 : 1999 - 2004 | 4.0l (242cid) | power tech i6 | - | 3000 rpm
row 2 : 1999 - 2004 | 4.7l (287cid) | powertech v8 | - | 3200 rpm
row 3 : 2002 - 2004 | 4.7l (287cid) | high output powertech v8 | - | -
row 4 : 1999 - 2001 | 3.1l diesel | 531 ohv diesel i5 | - | -
row 5 : 2002 - 2004 | 2.7l diesel | om647 diesel i5 | - | -
*/
Question: Which Jeep Grand Cherokee model equipped with the OM647 diesel i5 engine has the third lowest displacement value among all the listed models?
Function: f_select_row(row 1, row 4, row 5)
Explanation: The question aims to identify the specific Jeep Grand Cherokee model that has the OM647 diesel i5 engine and also determine which one among them has the third lowest displacement value."""


plan_group_column_demo = """If the question is about items with the same value and the number of these items, we use f_group_column() to group the items. For example,
/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
*/
Question: How many districts are actually democratic and which ones are they?
Function: f_group_column(party)
Explanation: The question is asking to accurately determine the number of districts that have a democratic party affiliation and also identify those specific districts. We need to look at the "district" and "party" columns to analyze and count the number of districts where the party is "dem". """


plan_sort_column_demo = """If the question is about the order of items in a column, we use f_sort_column() to sort the items. For example,
/*
col : position | club | played | points
row 1 : 1 | malaga cf | 42 | 79
row 10 : 10 | cp merida | 42 | 59
row 3 : 3 | cd numancia | 42 | 73
*/
Question: What is the position of CD Numancia when the positions are sorted from highest (first place) to lowest (last place)?
Function: f_sort_column(position)
Explanation: The question wants to check about who in the last position. We need to know the order of position from last to front. We sort the rows according to column "position"."""
