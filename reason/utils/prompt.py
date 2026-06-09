select_column_fs = """Your task is to use f_select_column() operator to select relevant columns according to the given table and question.
You should reason it step-by-step following the "Observation->Thought->Action" process, where,
- Observation: Given the Table schema (including column names and example cell values) and the Question
- Thought: Analyze the relationship between the question and the table columns
  - Lexical matching: similar words of the question link to columns
  - Value matching: column value of the question link to columns
  - Semantic matching: semantic sentence of the question link to columns
- Action: Call the operator f_select_column() with the selected column names.

Here are some few-shot examples:

#Example 1
Step1: Observation
Table schema:
/*
column : competition | total matches | cardiff win | draw | swansea win
row 1 : league | 55 | 19 | 16 | 20
row 2 : fa cup | 2 | 0 | 27 | 2
row 3 : league cup | 5 | 2 | 0 | 3
*/
Question: Are there any Cardiff wins when the number of draws is greater than 27?

Step2: Thought
Lexical matching:
no cardiff wins -> cardiff win
a draw -> draw

Value matching:
27 -> draw

Semantic matching:
None

Step3: Action
f_select_column([cardiff win, draw])

#Example 2
Step1: Observation
Table schema:
/*
column : season | champions | runner - up | third place | top goalscorer | club
row 1 : 1993 - 94 | sparta prague (1) | slavia prague | ban\u00edk ostrava | horst siegl (20) | sparta prague
row 2 : 1994 - 95 | sparta prague (2) | slavia prague | fc brno | radek drulák (15) | drnovice
row 3 : 1995 - 96 | slavia prague (1) | sigma olomouc | baumit jablonec | radek drulák (22) | drnovice
*/
Question: who was the top goalscorer in the season 2010 - 2011?

Step2: Thought
Lexical matching:
season 2010 - 2011 -> season
the top goal scorer -> top goalscorer

Value matching:
2010 - 2011 -> season

Semantic matching:
the top goal scorer for ... was david lafata -> top goalscorer

Step3: Action
f_select_column([season, top goalscorer])

#Example 3
Step1: Observation
Table schema:
/*
column : crew | open 1st viii | senior 2nd viii | senior 3rd viii | senior iv | year 12 single scull | year 11 single scull
row 1 : 2009 | stm | sta | sta | som | stm | splc
row 2 : 2010 | splc | som | som | sth | splc | splc
row 3 : 2011 | stm | stu | stu | sta | stm | splc
*/
Question: Which crew had a senior 2nd viii value of som and a senior iv value of stm in the year 2013?

Step2: Thought
Lexical matching:
the crew -> crew
a senior 2nd viii of som -> senior 2nd viii
senior iv of stm -> senior iv

Value matching:
som -> senior 2nd viii
stm -> senior iv

Semantic matching:
None

Step3: Action
f_select_column([crew, senior 2nd viii, senior iv])

Now, process the following table and question."""



critic_columns_fs = """Your task is to verify whether the selected columns are sufficient and minimal for answering the given question.
You should reason step-by-step following the "Observation -> Thought -> Action" process:
- Observation: You are given the Table schema, the Question, and the previously Selected columns.
- Thought: Verify the selected columns using the following checks and return the Verified column set:
  - Minimal sufficiency check: For each selected column, consider If this column is removed, can the question still be answered? Remove the column if redundant and Retain it if necessary.
  - Missing column check: Determine whether any required column is missing for answering the question.
  - Verified column set: Refine the column set that are both sufficient and minimal to answer the question.
- Action: Call the operator f_select_column() with the verified column set.

Here are some few-shot examples:

#Example 1
Step1: Observation
Table schema:
/*
table caption : a competition
column : competition | total matches | cardiff win | draw | swansea win
row 1 : league | 55 | 19 | 16 | 20
row 2 : fa cup | 2 | 0 | 27 | 2
row 3 : league cup | 5 | 2 | 0 | 3
*/
Question: Are there any Cardiff wins when the number of draws is greater than 27?
Selected columns: [competition, total matches, cardiff win]

Step2: Thought
Minimal sufficiency check:
If remove column "competition" -> the question can still be answered using [total matches, cardiff win] -> redundant
If remove column "total matches" -> the question can still be answered using [cardiff win] -> redundant
If remove column "cardiff win" -> cannot identify the condition  -> necessary

Missing column check:
Add column "draw" -> column "draw" is required to identify which number of draws is greater than 27

Verified column set:
[cardiff win, draw]

Step3: Action
f_select_column([cardiff win, draw])

#Example 2
Step1: Observation
Table schema:
/*
column : season | champions | runner - up | third place | top goalscorer | club
row 1 : 1993 - 94 | sparta prague (1) | slavia prague | ban\u00edk ostrava | horst siegl (20) | sparta prague
row 2 : 1994 - 95 | sparta prague (2) | slavia prague | fc brno | radek drulák (15) | drnovice
row 3 : 1995 - 96 | slavia prague (1) | sigma olomouc | baumit jablonec | radek drulák (22) | drnovice
*/
Question: who was the top goalscorer in the season 2010 - 2011?
Selected columns: [season, top goalscorer, club]

Step2: Thought
Minimal sufficiency check:
If remove column "season" -> cannot identify the condition  -> necessary
If remove column "top goalscorer" -> cannot identify the condition  -> necessary
If remove column "club" -> the question can still be answered using [season, top goalscorer] -> redundant

Missing column check:
None

Verified column set:
[season, top goalscorer]

Step3: Action
f_select_column([season, top goalscorer])

#Example 3
Step1: Observation
Table schema:
/*
column : crew | open 1st viii | senior 2nd viii | senior 3rd viii | senior iv | year 12 single scull | year 11 single scull
row 1 : 2009 | stm | sta | sta | som | stm | splc
row 2 : 2010 | splc | som | som | sth | splc | splc
row 3 : 2011 | stm | stu | stu | sta | stm | splc
*/
Question: Which crew had a senior 2nd viii value of som and a senior iv value of stm in the year 2013?
Selected columns: [senior 2nd viii, senior iv]

Step2: Thought
Minimal sufficiency check:
If remove column "senior 2nd viii" -> cannot identify the condition  -> necessary
If remove column "senior iv" -> cannot identify the condition  -> necessary

Missing column check:
Add column "crew"  -> column "crew" is required to identify which crew satisfies the condition.

Verified column set:
[senior 2nd viii, senior iv, crew]

Step3: Action
f_select_column([senior 2nd viii, senior iv, crew])

Now, process the following table and question."""


reason_fs = '''Your task is to think the question with knowledge triples step by step, and then reason them to return the answer.

You are given:
- **Question**: A natural language question about the table.
- **Table caption**: The title of the table.
- **Knowledge triples**: A set of (row, column, cell) triples extracted from the table graph
- **Salient rows**: A list of row ids that are likely relevant to the question. [*] represents all rows.
- **Group Info**: The group column and a list of (value, count) tuples to support answering the question.
- **Sort Info**: The sorted column with corresponding ranked row IDs and its maximum/minimum cell values to support question answering.
- **Skills**: Retrieved prior experiences relevant to the question, including both successful reasoning patterns to follow and failed reasoning errors to avoid.

Instructions:
1. Each (row, column, cell) triple denotes an UNDIRECTED edge labeled by the column, connecting the row node to the cell node, meaning the row’s value in that column is the given cell.
2. **Salient rows** are prioritized hints to guide your search, but not the exclusive source of truth; always verify your reasoning using the provided Knowledge triples.
3. **Group Info** provides the grouped column and a list of (value, count) statistics to support counting or comparison, but not the exclusive source of truth; always verify your reasoning using the provided Knowledge triples.
4. **Sort Info** provides the sorting column, the ranked row(s), and the corresponding maximum or minimum cell value to support ordering or extremum-based reasoning, but not the exclusive source of truth; always verify your reasoning using the provided Knowledge triples.
5. **Skills** provide both successful and failed reasoning experiences from similar questions. Use successful patterns as guidance and avoid failed ones, but do NOT rely on them directly; they are only heuristic references. All reasoning must be verified and grounded in the provided Knowledge triples.
6. Please return the Output with three sections:
  - enclosed by '<paths>' and '</paths>': You must use ONLY the provided knowledge triples according to the given question to return the reasoning paths consist of multiple triples.
  - enclosed by '<thought>' and '</thought>': Think step by step according to the given question and the generated reasoning path, then return the chain-of-thought text.
  - enclosed by '<answer>' and '</answer>': Return the pure final answer based on the chain-of-thought text.
7. If there exist multiple answers, please separate them with '|'. Do NOT return extra text.

Here are some examples:

Example 1
Question: What number bike is the only one to use equipment zabel - vmc?
Table caption: a bike match
Knowledge triples: [(row1, equipment, ktm - ayr), (row1, bike no, 1), (row2, equipment, ktm - ayr), (row2, bike no, 3), (row3, equipment, zabel - vmc), (row3, bike no, 2)]
Salient rows: [row3]
Group Info: None
Sort Info: None
Output:
<paths>(row3, equipment, zabel - vmc), (row3, bike no, 2)</paths>
<thought>The question asks for the "bike number" that uses equipment "zabel - vmc". From the paths, row3 is the row where the equipment equals "zabel - vmc". Following the same row, the bike number in row3 is 2. Therefore, the answer is "2"</thought>
<answer>2</answer>

Example 2
Question: Which team was the away team playing at the Brunswick Street Oval venue?
Table caption: Match info
Knowledge triples: [(row1, away team, footscray), (row1, venue, western oval), (row2, away team, essendon), (row2, venue, windy hill), (row3, away team, hawthorn), (row3, venue, brunswick street oval)]
Salient rows: [row3]
Group Info: None
Sort Info: None
Output:
<paths>(row3, venue, brunswick street oval), (row3, away team, hawthorn)</paths>
<thought>The question asks which "away team" was playing at the venue "Brunswick Street Oval". From the paths, row3 is associated with the venue "brunswick street oval". In the same row, the away team is "hawthorn". Therefore, the answer is "hawthorn"</thought>
<answer>hawthorn</answer>

Example 3:
Question: How much lower was the popular vote in the 1937 election compared to that of the 1943 election?
Table caption: election data
Knowledge triples: [(row1, year of election, 1937), (row1, % of popular vote, 5.6%), (row4, year of election, 1943), (row4, % of popular vote, 31.7%)]
Salient rows: [row1, row4]
Group Info: None
Sort Info: None
Output:
<paths>(row1, year of election, 1937), (row1, % of popular vote, 5.6%), (row4, year of election, 1943), (row4, % of popular vote, 31.7%)</paths>
<thought>The question asks for the difference in popular vote between the 1937 and 1943 elections. From the paths, the 1937 election row has a popular vote of 5.6%, and the 1943 election row has a popular vote of 31.7%. Subtracting the earlier value from the later value gives 31.7% − 5.6% = 26.1%. Therefore, the answer is "26.1%"</thought>
<answer>26.1%</answer>

Now, process the following table and question.'''



add_column_demo = """To answer the question, we can first use f_add_column() to add more columns to the table.

The added columns should have these data types:
1. Numerical: the numerical strings that can be used in sort, sum
2. Datetype: the strings that describe a date, such as year, month, day
3. String: other strings

/*
col : week | when | kickoff | opponent | results; final score | results; team record | game site | attendance
row 1 : 1 | saturday, april 13 | 7:00 p.m. | at rhein fire | w 27–21 | 1–0 | rheinstadion | 32,092
row 2 : 2 | saturday, april 20 | 7:00 p.m. | london monarchs | w 37–3 | 2–0 | waldstadion | 34,186
row 3 : 3 | sunday, april 28 | 6:00 p.m. | at barcelona dragons | w 33–29 | 3–0 | estadi olímpic de montjuïc | 17,503
*/
Question: what is the date of the competition with highest attendance?
The existing columns are: "week", "when", "kickoff", "opponent", "results; final score", "results; team record", "game site", "attendance".
Explanation: The question asks about the date of the competition with highest score. Each row is about one competition. We extract the value from column "Attendance" and create a different column "Attendance number" for each row. The datatype is Numerical.
Answer: f_add_column(Attendance number). The value: 32092 | 34186 | 17503

/*
col : rank | lane | player | time
row 1 :  | 5 | olga tereshkova (kaz) | 51.86
row 2 :  | 6 | manjeet kaur (ind) | 52.17
row 3 :  | 3 | asami tanno (jpn) | 53.04
*/
Question: how many athletes come from Japan?
The existing columns are: rank, lane, player, time.
Explanation: The question asks about the number of athletes from japan. Each row is about one athlete. We need to know the country of each athlete. We extract the value from column "Player" and create a different column "Country of athletes" for each row. The datatype is String.
Answer: f_add_column(country of athletes). The value: kaz | ind | jpn

/*
col : year | competition | venue | position | notes
row 1 : 1991 | european junior championships | thessaloniki, greece | 10th | 4.90 m
row 2 : 1992 | world junior championships | seoul, south korea | 1st | 5.45 m
row 3 : 1996 | european indoor championships | stockholm, sweden | 14th (q) | 5.45 m
*/
Question: what was the ranking in 1991?
The existing columns are: year, competition, venue, position, notes.
Explanation: The question asks about the rank in 1991, we need to know the rank of each competition. We extract the value from column "position" and create a different column "rank" for each row. The datatype is numerical.
Answer: f_add_column(rank). The value: 10 | 1 | 14

/*
col : iso/iec standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2008) | 7
*/
Question: how many times were the standards published in 2008?
The existing columns are: iso/iec standard, title, status, description, wg.
Explanation: The question asks about the number of times the standards were published in 2008. We need to know the year of each standard. We extract the value from column "status" and create a different column "year of standard" for each row. The datatype is datetype.
Answer: f_add_column(year of standard). The value: 2005 | 2008 | 2008

/*
col : match | date | ground | opponent | score1 | pos. | pts. | gd
row 1 : 1 | 15 august | a | bayer uerdingen | 3 – 0 | 1 | 2 | 3
row 2 : 2 | 22 july | h | 1. fc kaiserslautern | 1 – 0 | 1 | 4 | 4
row 3 : 4 | 29 september | h | dynamo dresden | 3 – 1 | 1 | 6 | 6
*/
Question: how many times they play in August?
The existing columns are: match, date, ground, opponent, score1, pos., pts., gd.
Explanation: The question asks about the number of times they play in August. We need to know the month of each match. We extract the value from column "date" and create a different column "month" for each row. The datatype is datetype.
Answer: f_add_column(month). The value: august | july | september

/*
col : place | player | country | score | to par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | - 4
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | -- 3
row 3 : t3 | david canipe | united states | 69 + 69 = 138 | - 2
*/
Question: what score David Canipe of the United States has?
The existing columns are: place, player, country, score, to par.
Explanation: The question asks about the score that David Canipe of the United States havs. We need to know the score values of each player. We extract the value from column "score" and create a different column "score value" for each row. The datatype is numerical.
Answer: f_add_column(score value). The value: 136 | 137 | 138

/*
col : code | county | former province | area (km2) | population; census 2009 | capital
row 1 : 1 | mombasa | coast | 212.5 | 939,370 | mombasa (city)
row 2 : 2 | kwale | coast | 8,270.3 | 649,931 | kwale
row 3 : 3 | kilifi | coast | 12,245.9 | 1,109,735 | kilifi
*/
Question: what is the population of Kwale in 2009? 
The existing columns are: code, county, former province, area (km2), population; census 2009, capital.
Explanation: The question asks about the population of Kwale in 2009. We need to know the population of each county. We extract the value from column "population; census 2009" and create a different column "population" for each row. The datatype is numerical.
Answer: f_add_column(population). The value: 939370 | 649311 | 1109735"""


select_row_demo = """Using f_select_row() api to select relevant rows in the given table that answer the question.
Please use f_select_row([*]) to select all rows in the table.

/*
col : home team | home team score | away team | away team score | venue | crowd | date
row 1 : st kilda | 13.12 (90) | melbourne | 13.11 (89) | moorabbin oval | 18836 | 19 august 1972
row 2 : south melbourne | 9.12 (66) | footscray | 11.13 (79) | lake oval | 9154 | 19 august 1972
row 3 : richmond | 20.17 (137) | fitzroy | 13.22 (100) | mcg | 27651 | 19 august 1972
row 4 : geelong | 17.10 (112) | collingwood | 17.9 (111) | kardinia park | 23108 | 19 august 1972
row 5 : north melbourne | 8.12 (60) | carlton | 23.11 (149) | arden street oval | 11271 | 19 august 1972
row 6 : hawthorn | 15.16 (106) | essendon | 12.15 (87) | vfl park | 36749 | 19 august 1972
*/
Question : which away team has the highest score?
Explanation: The question aims to find out the away team that achieved the highest score among all the records in the table. We need to compare the away team scores in each row to determine the answer. Use * to represent all rows in the table.
Answer: f_select_row([*])

/*
col : rank | airline | country | fleet size | remarks
row 1 : 1 | caribbean airlines | trinidad and tobago | 22 | largest airline in the caribbean
row 2 : 2 | liat | antigua and barbuda | 17 | second largest airline in the caribbean
row 3 : 3 | cubana de aviaciã cubicn | cuba | 14 | operational since 1929
row 4 : 4 | inselair | curacao | 12 | operational since 2006
row 5 : 5 | dutch antilles express | curacao | 4 | curacao second national carrier
row 6 : 6 | air jamaica | trinidad and tobago | 5 | parent company is caribbean airlines
row 7 : 7 | tiara air | aruba | 3 | aruba 's national airline
*/
Question : How many fleets the company has can determine whether it can be the second national carrier of curacao?
Explanation: the question wants to check a record in the table. we cannot find a record to perfectly answer the question, the most relevant row is row 5, which describes dutch antilles express airline, remarks is uracao second national carrier and fleet size is 4.
Answer: f_select_row([row 5])

/*
col : actor | character | soap opera | years | duration
row 1 : tom jordon | charlie kelly | fair city | 1989- | 25 years
row 2 : tony tormey | paul brennan | fair city | 1989- | 25 years
row 3 : jim bartley | bela doyle | fair city | 1989- | 25 years
row 4 : sarah flood | suzanne halpin | fair city | 1989 - 2013 | 24 years
row 5 : pat nolan | barry o'hanlon | fair city | 1989 - 2011 | 22 years
row 6 : martina stanley | dolores molloy | fair city | 1992- | 22 years
row 7 : joan brosnan walsh | mags kelly | fair city | 1989 - 2009 | 20 years
row 8 : jean costello | rita doyle | fair city | 1989 - 2008 , 2010 | 19 years
row 9 : ciara o'callaghan | yvonne gleeson | fair city | 1991 - 2004 , 2008- | 19 years
row 10 : celia murphy | niamh cassidy | fair city | 1995- | 19 years
row 39 : tommy o'neill | john deegan | fair city | 2001- | 13 years
row 40 : seamus moran | mike gleeson | fair city | 1996 - 2008 | 12 years
row 41 : rebecca smith | annette daly | fair city | 1997 - 2009 | 12 years
row 42 : grace barry | mary - ann byrne | glenroe | 1990 - 2001 | 11 years
row 43 : gemma doorly | sarah o'leary | fair city | 2001 - 2011 | 10 years
*/
Question : how many years did seamus moran and rebecca smith each spend in their respective soap operas?
Explanation: The question aims to find out the duration of time that Seamus Moran and Rebecca Smith spent in their soap operas respectively. We need to look at the relevant rows in the table that describe them, which are row 40 for Seamus Moran and row 41 for Rebecca Smith to get the answer.
Answer: f_select_row([row 40, row 41])

/*
col : years | displacement | engine | power | torque
row 1 : 1999 - 2004 | 4.0l (242cid) | power tech i6 | - | 3000 rpm
row 2 : 1999 - 2004 | 4.7l (287cid) | powertech v8 | - | 3200 rpm
row 3 : 2002 - 2004 | 4.7l (287cid) | high output powertech v8 | - | -
row 4 : 1999 - 2001 | 3.1l diesel | 531 ohv diesel i5 | - | -
row 5 : 2002 - 2004 | 2.7l diesel | om647 diesel i5 | - | -
*/
Question : Which Jeep Grand Cherokee model with the OM647 diesel i5 engine has the third lowest displacement value among all the listed models?
Explanation: The question is aimed at finding out the specific Jeep Grand Cherokee model that is powered by the OM647 diesel i5 engine and has the third lowest displacement value. To answer this, we need to consider the first three lowest displacement values and all the rows where the power is the OM647 diesel i5 engine.
Answer: f_select_row([row 5, row 4, row 1])"""


group_column_demo = """To answer the question, we can first use f_group_column() to group the values in a column.

/*
col : rank | lane | athlete | time | country
row 1 : 1 | 6 | manjeet kaur (ind) | 52.17 | ind
row 2 : 2 | 5 | olga tereshkova (kaz) | 51.86 | kaz
row 3 : 3 | 4 | pinki pramanik (ind) | 53.06 | ind
row 4 : 4 | 1 | tang xiaoyin (chn) | 53.66 | chn
row 5 : 5 | 8 | marina maslyonko (kaz) | 53.99 | kaz
*/
Question: How many athletes are from Japan?
The existing columns are: rank, lane, athlete, time, country.
Explanation: The question is asking to determine the number of athletes from Japan. Since each row represents an individual athlete and the "country" column indicates the origin of each athlete, we need to group by the "country" column to check if there are any athletes from Japan. We can use the f_group_column(country) operation to group the athletes based on their country to analyze this situation.
Answer: f_group_column(country).

/*
col : district | name | party | residence | first served
row 1 : district 1 | nelson albano | dem | vineland | 2006
row 2 : district 1 | robert andrzejczak | dem | middle twp. | 2013†
row 3 : district 2 | john f. amodeo | rep | margate | 2008
row 4 : district 2 | chris a. brown | rep | ventnor | 2012
row 5 : district 3 | john j. burzichelli | dem | paulsboro | 2002
*/
Question: How many districts are democratic and which ones are they?
The existing columns are: district, name, party, residence, first served.
Explanation: The question is aimed at finding out the exact number of districts that have a democratic party affiliation as well as identifying those specific districts. Since each row represents information about a district and the "party" column indicates the political party of that district, we need to group by the "party" column to count and identify the democratic districts. We can use the f_group_column(party) operation to group the districts based on their party to analyze this situation.
Answer: f_group_column(party)."""


sort_column_demo = """To answer the question, we can first use f_sort_column() to sort the values in a column to get the order of the items. The order can be "large to small" or "small to large".

The column to sort should have these data types:
1. Numerical: the numerical strings that can be used in sort
2. DateType: the strings that describe a date, such as year, month, day
3. String: other strings

/*
col : position | club | played | points | wins | draws | losses | goals for | goals against | goal difference
row 1 : 1 | malaga cf | 42 | 79 | 22 | 13 | 7 | 72 | 47 | +25
row 10 : 10 | cp merida | 42 | 59 | 15 | 14 | 13 | 48 | 41 | +7
row 3 : 3 | cd numancia | 42 | 73 | 21 | 10 | 11 | 68 | 40 | +28
*/
Question: What is the position of CD Numancia when the positions are sorted from highest (first place) to lowest (last place)?
The existing columns are: position, club, played, points, wins, draws, losses, goals for, goals against, goal difference.
Explanation: The question is asking to determine the actual position of CD Numancia when the positions of the clubs are arranged in the order from the highest position (first place) to the lowest position (last place). Since there is a "position" column indicates the standing of each club, we need to sort the data with the order "large to small" to see where CD Numancia actually lies in the ranking. The datatype is Numerical.
Answer: f_sort_column(position), the order is "large to small".

/*
col : year | team | games | combined tackles | tackles | assisted tackles |
row 1 : 2004 | hou | 16 | 63 | 51 | 12 |
row 2 : 2005 | hou | 12 | 35 | 24 | 11 |
row 3 : 2006 | hou | 15 | 26 | 19 | 7 |
*/
Question: Who had the least amount of tackles in 2006?
The existing columns are: year, team, games, combined tackles, tackles, assisted tackles.
Explanation: The question is asking to determine who indeed had the least amount of tackles in 2006. To find out, we need to sort the data based on the "tackles" column in the order of "small to large". This will allow us to see the player who had the least amount of tackles in 2006 as well as the order of tackles from the least to the most for each year's data. The datatype is Numerical.
Answer: f_sort_column(tackles), the order is "small to large"."""



add_column_react = """Your task is to use f_add_column() operator to extend the table for answering the question.

The added columns should have these data types:
1. Numerical: the numerical strings that can be used in sort, sum
2. Datetype: the strings that describe a date, such as year, month, day
3. String: other strings

You should reason it step-by-step following the "Observation -> Thought -> Action" process, Here are some few-shot examples:

#Example 1
Step1: Observation
Table:
/*
column : rank | lane | player | time
row 1 :  1 | 5 | olga tereshkova (kaz) | 51.86
row 2 :  2 | 6 | manjeet kaur (ind) | 52.17
row 3 :  3 | 3 | asami tanno (jpn) | 53.04
*/
Question: how many athletes come from Japan?

Step2: Thought
Question analysis:
The question asks about the number of athletes from japan. Each row is about one athlete. We need to know the country of each athlete.

Extraction source:
We extract the value from column "player" and create a different column "country of athletes" for each row. The datatype is String.

Step3: Action
f_add_column(country of athletes). The value: kaz | ind | jpn

#Example 2
Step1: Observation
Table:
/*
column : iso/iec standard | status | wg
row 1 : iso/iec tr 19759 | published (2005) | 20
row 2 : iso/iec 15288 | published (2008) | 7
row 3 : iso/iec 12207 | published (2008) | 7
*/
Question: how many times were the standards published in 2008?

Step2: Thought
Question analysis:
The question asks about the number of times the standards were published in 2008. We need to know the year of each standard.

Extraction source:
We extract the value from column "status" and create a different column "year of standard" for each row. The datatype is datetype.

Step3: Action
f_add_column(year of standard). The value: 2005 | 2008 | 2008

#Example 3
Step1: Observation
Table:
/*
column : place | player | country | score | to par
row 1 : 1 | hale irwin | united states | 68 + 68 = 136 | - 4
row 2 : 2 | fuzzy zoeller | united states | 71 + 66 = 137 | -- 3
row 3 : 3 | david canipe | united states | 69 + 69 = 138 | - 2
*/
Question: what score David Canipe of the United States has?

Step2: Thought
Question analysis:
The question asks about the score that David Canipe of the United States havs. We need to know the score values of each player.

Extraction source:
We extract the value from column "score" and create a different column "score value" for each row. The datatype is numerical.

Step3: Action
f_add_column(score value). The value: 136 | 137 | 138

Now, process the following table and question."""



select_rows_react = """Your task is to use f_select_rows() operator to select relevant rows according to the given table and question.
You should reason it step-by-step following the "Observation -> Thought -> Action" process:
- Observation: You are given Table and the Question.
- Thought: Analyze which rows are relevant for answering the question. Structure your reasoning using the following steps:
  - What the question means: Explain what information the question is asking for.
  - What each row represents: Briefly describe what information each row contains based on the given knowledge triples.
  - Select which rows: Decide which rows are needed to answer the question. You may use the following reasoning strategies: 
    (1) Condition filtering: select rows that satisfy conditions mentioned in the question.
    (2) Entity matching: select rows that contain entities mentioned in the question.
    (3) Global reasoning: if the question requires comparison, aggregation, or ranking across rows(e.g., highest, lowest, maximum, minimum), then all rows may need to be selected.
- Action: Call the operator f_select_rows() with the selected rows. If All rows are needed for reasoning, please use: f_select_rows([*])

Here are some few-shot examples:

#Example 1
Step1: Observation
Table:
/*
column : home team | home team score | away team | away team score | venue | crowd | date
row 1 : st kilda | 13.12 (90) | melbourne | 13.11 (89) | moorabbin oval | 18836 | 19 august 1972
row 2 : south melbourne | 9.12 (66) | footscray | 11.13 (79) | lake oval | 9154 | 19 august 1972
row 3 : richmond | 20.17 (137) | fitzroy | 13.22 (100) | mcg | 27651 | 19 august 1972
row 4 : geelong | 17.10 (112) | collingwood | 17.9 (111) | kardinia park | 23108 | 19 august 1972
row 5 : north melbourne | 8.12 (60) | carlton | 23.11 (149) | arden street oval | 11271 | 19 august 1972
row 6 : hawthorn | 15.16 (106) | essendon | 12.15 (87) | vfl park | 36749 | 19 august 1972
*/
Question : which away team has the highest score?

Step2: Thought
What the question means:
The question asks for the away team with the highest score. 

What each row represents:
Each row represents a match record containing an away team and its score.

Select which rows:
Since the maximum value can only be determined after examining every row's score, all rows are required for the comparison. Therefore, every row may contribute to identifying the highest score.

Step3: Action
f_select_rows([*])

#Example 2
Step1: Observation
Table:
/*
column : rank | airline | country | fleet size | remarks
row 1 : 1 | caribbean airlines | trinidad and tobago | 22 | largest airline in the caribbean
row 2 : 2 | liat | antigua and barbuda | 17 | second largest airline in the caribbean
row 3 : 3 | cubana de aviaciã cubicn | cuba | 14 | operational since 1929
row 4 : 4 | inselair | curacao | 12 | operational since 2006
row 5 : 5 | dutch antilles express | curacao | 4 | curacao second national carrier
row 6 : 6 | air jamaica | trinidad and tobago | 5 | parent company is caribbean airlines
row 7 : 7 | tiara air | aruba | 3 | aruba 's national airline
*/
Question : How many fleets the company has can determine whether it can be the second national carrier of curacao?

Step2: Thought
What the question means:
The question asks which company is the second national carrier of curacao and wants to know how many fleets that company has.

What each row represents:
Each row represents an airline with its fleet size and additional remarks describing the airline.

Select which rows:
To answer the question, we need to find the airline that is described as the second national carrier of curacao. Looking at the remarks field in each row, only row5 contains the remark "curacao second national carrier", which directly matches the condition in the question. This row also contains the fleet size needed to answer the question. Therefore, only row5 is required.

Step3: Action
f_select_rows([row 5])

#Example 3
Step1: Observation
Table:
/*
column : actor | character | soap opera | years | duration
row 1 : tom jordon | charlie kelly | fair city | 1989- | 25 years
row 2 : tony tormey | paul brennan | fair city | 1989- | 25 years
row 3 : jim bartley | bela doyle | fair city | 1989- | 25 years
row 4 : sarah flood | suzanne halpin | fair city | 1989 - 2013 | 24 years
row 5 : pat nolan | barry o'hanlon | fair city | 1989 - 2011 | 22 years
row 6 : martina stanley | dolores molloy | fair city | 1992- | 22 years
row 40 : seamus moran | mike gleeson | fair city | 1996 - 2008 | 12 years
row 41 : rebecca smith | annette daly | fair city | 1997 - 2009 | 12 years
row 42 : grace barry | mary - ann byrne | glenroe | 1990 - 2001 | 11 years
*/
Question : how many years did seamus moran and rebecca smith each spend in their respective soap operas?

Step2: Thought
What the question means:
The question asks how many years Seamus Moran and Rebecca Smith each spent in their respective soap operas.

What each row represents:
Each row represents an actor, the soap opera character they played, and the duration of time they spent in the show.

Select which rows:
To answer the question, we need to find the rows corresponding to the two actors mentioned in the question: Seamus Moran and Rebecca Smith. By examining the actor field in each row, row40 corresponds to Seamus Moran and row41 corresponds to Rebecca Smith. These rows contain the duration information needed to answer the question. Therefore, only row40 and row41 are required.

Step3: Action
f_select_rows([row 40, row 41])

Now, process the following table and question."""
