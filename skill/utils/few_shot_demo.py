judge_trace_few_shot_demo = """
##Example 1
Table:
/*
table caption: Pan-democracy camp
column : election | number of popular votes | % of popular votes | total elected seats | +/-
row 1 : 1988 | 139,982 | 22.16 | 61 / 264
row 2 : 1991 | 170,757 | 32.11 | 83 / 272  | 22
row 3 : 1994 | 242,557 | 35.34 | 121 / 346 | 38
row 4 : 1999 | 271,251 | 33.45 | 122 / 390 | 1
row 5 : 2003 | 459,640 | 44.67 | 194 / 400 | 72
row 6 : 2007 | 445,781 | 39.15 | 127 / 405 | 30
row 7 : 2011 | 464,512 | 39.34 | 103 / 412 | 18
*/

Question:
which election was the first to reach over 40% of the popular vote?

Prediction Answer:
2003

Explanation: Based on the original table, the question asks for the first election where the percentage of popular votes exceeded 40%.
The table shows the percentage of popular votes for each election:
1988: 22.16%
1991: 32.11%
1994: 35.34%
1999: 33.45%
2003: 44.67%
2007: 39.15%
2011: 39.34%
The first election to reach over 40% is the 2003 election with 44.67% of the popular vote.
Therefore, the Prediction Answer of 2003 is correct.

Conclusion: [Correct]

##Example 2
Table:
/*
table caption: Lori Chalupny
column : goal | date | location | opponent | lineup | min | assist/pass | score | result | competition
row 1 : 1 | may 9, 2004  | usaalbuquerque nm | mexico   | on 70' (off lilly)  | 19  | tarpley    | 3–0 | 3–0 | friendly
row 2 : 2 | jun 26, 2005 | usavirginia beach | canada   | 90.start            | 12  | unassisted | 1–0 | 2–0 | friendly
row 3 : 3 | jan 30, 2007 | chnguangzhou      | china pr | 90.start            | 46+ | unassisted | 1–0 | 2–0 | four nations tournament
row 4 : 4 | may 12, 2007 | usafrisco tx      | canada   | off 72' (on wagner) | 28  | tarpley    | 3–1 | 6–2 | friendly
row 5 : 5 | sep 18, 2007 | chnshanghai       | nigeria  | 90.start            | 1   | wambach    | 1–0 | 1–0 | world cup – group b
row 6 : 6 | sep 30, 2007 | chnshanghai       | norway   | 90.start            | 58  | unassisted | 3–0 | 4–1 | world cup final - third place playoff
row 7 : 7 | aug 18, 2008 | chnbeijing        | japan    | 90.start            | 44  | rodriguez  | 2–1 | 4–2 | olympics tournament
row 8 : 8 | sep 20, 2008 | usabridgeview il  | ireland  | 90.start            | 19  | tarpley    | 1–0 | 2–0 | friendly
*/

Question:
how many consecutive friendly competitions did chalupny score in?

Prediction Answer:
0

Explanation: 
We can see that Chalupny scored in the following consecutive friendly competitions:
On May 9, 2004, against Mexico.
On Jun 26, 2005, against Canada
These two instances represent consecutive friendly competitions in which Chalupny scored. Therefore, the Prediction Answer of 0 is incorrect.

Conclusion: [Incorrect]

##Example 3
Table:
/*
table caption: 2007\u201308 Hazfi Cup
column : date | home team | score | away team | notes
row 1 : 17 december 2007 | foolad            | 4-4 | esteghlal ahvaz | foolad progress 8-7 on penalties
row 2 : 21 december 2007 | rah ahan          | 2-2 | steel azin      | rah ahan progress 5-2 on penalties
row 3 : 21 december 2007 | zob ahan          | 1-1 | esteghlal       | esteghlal progress 3-1 on penalties
row 4 : 21 december 2007 | bargh shiraz      | 1-0 | paykan tehran   |
row 5 : 21 december 2007 | shahin bushehr    | 2-2 | saba battery    | shahin bushehr progress 6-5 on penalties
row 6 : 24 december 2007 | pas hamedan       | 3-0 | persepolis      |
row 7 : 26 february 2008 | moghavemat sepasi | 1-2 | sepahan         |
row 8 : 4 march 2008     | sanaye arak       | 0-1 | pegah gilan     |
*/

Question:
what is the average score of all home team members for all dates?

Prediction Answer:
2.125

Explanation: To calculate the average score of all home team members, we need to sum up the scores for the home teams and divide by the total number of home teams listed.
Here are the scores for the home teams from the table:
Foolad: 4
Rah Ahan: 2
Zob Ahan: 1
Bargh Shiraz: 1
Shahin Bushehr: 2
Pas Hamedan: 3
Moghavemat Sepasi: 1
Sanaye Arak: 0
The total score is 4+2+1+1+2+3+1+0=144 + 2 + 1 + 1 + 2 + 3 + 1 + 0 = 144+2+1+1+2+3+1+0=14.
There are 8 home teams in total.
Therefore, the average score is 1.75.

Conclusion: [Incorrect]"""


critic_trace_few_shot_demo = """
**Table**:
/*
table caption: Lori Chalupny
column : goal | date | location | opponent | lineup | min | assist/pass | score | result | competition
row 1 : 1 | may 9, 2004  | usaalbuquerque nm | mexico   | on 70' (off lilly)  | 19  | tarpley    | 3–0 | 3–0 | friendly
row 2 : 2 | jun 26, 2005 | usavirginia beach | canada   | 90.start            | 12  | unassisted | 1–0 | 2–0 | friendly
row 3 : 3 | jan 30, 2007 | chnguangzhou      | china pr | 90.start            | 46+ | unassisted | 1–0 | 2–0 | four nations tournament
row 4 : 4 | may 12, 2007 | usafrisco tx      | canada   | off 72' (on wagner) | 28  | tarpley    | 3–1 | 6–2 | friendly
row 5 : 5 | sep 18, 2007 | chnshanghai       | nigeria  | 90.start            | 1   | wambach    | 1–0 | 1–0 | world cup – group b
row 6 : 6 | sep 30, 2007 | chnshanghai       | norway   | 90.start            | 58  | unassisted | 3–0 | 4–1 | world cup final - third place playoff
row 7 : 7 | aug 18, 2008 | chnbeijing        | japan    | 90.start            | 44  | rodriguez  | 2–1 | 4–2 | olympics tournament
row 8 : 8 | sep 20, 2008 | usabridgeview il  | ireland  | 90.start            | 19  | tarpley    | 1–0 | 2–0 | friendly
*/

**Question**:
how many consecutive friendly competitions did chalupny score in?

**Dynamic chain**:
f_select_row() -> f_select_column() -> f_group_column()

**Operator Execution**:
Execution 1: 
Operator: f_select_row(row1, row2, row4, row8)
Parameter and Info: ['row1', 'row2', 'row4', 'row8'] are salient rows relevant to the question
Thought:
Select relevant rows.
The question aims to find out the number of consecutive friendly competitions in which Chalupny scored. We need to look at the rows where the competition type is "friendly" and check the dates to determine if they are consecutive. The relevant rows are row 1, row 2, and row 4. So we use f_select_row(row1, row2, row4, row8).

Execution 2: 
Operator: f_select_column(goal, date, competition)
Parameter and Info: ['goal', 'date', 'competition'] are relevant columns to the question
Thought:
Lexical matching:
scored in -> goal
consecutive -> date
friendly competitions -> competition

Value matching:
friendly -> competition

Semantic matching:
The question asks for the number of consecutive friendly competitions where Chalupny scored. The "competition" column identifies "friendly" matches, the "goal" column confirms she scored, and the "date" column determines the chronological order to check consecutiveness. Strictly based on the provided schema and explicit question parts ("consecutive", "friendly", "score"), the relevant columns are goal, date, and competition. So we use f_select_column(goal, date, competition).
  
Execution 3: 
Operator: f_group_column(competition))
Parameter and Info: group the column 'competition', and compute the count of each unique value: [('friendly', 4), ('four nations tournament', 1), ('world cup – group b', 1), ('world cup final - third place playoff', 1), ('olympics tournament', 1)]
Thought:
The question is asking to count the number of consecutive friendly competitions. Since 'competition' column indicates relevant information for each rows, so we need to group by the "competition" column.

**Final Reason**:
Reason paths:
(row1, competition, friendly), (row2, competition, friendly), (row4, competition, friendly), (row8, competition, friendly)
Thought:
Based on the reason paths, we can count that row1, row2, row4, and row8 satisfy the condition, so the total number of friendly competitions is 4.

Prediction Answer:
4

Critique:
The question ask the consecutive number of friendly competitions, row1 and row2 are consecutive, so the answer is 2. Therefore, Step **Final Reason** is incorrect.

Conclusion: [Incorrect] Step **Final Reason**"""


success_skill_demo = """{
"Name": "group_count_argmax",
"Tag": "extremum",
"Description": "Find the category with the highest frequency within a row subset",
"Trigger": {
    "semantic": ["most", "highest number", "largest number of"],
    "structure": ["ask for category", "requires counting", "involves comparison"]
},
"Question pattern": [
    "Which [category] had the most [entities] in the top N?",
    "What [grouping attribute] is most represented among the top N ranked items?",
    "How many [categories] appear in the top N, and which appears most frequently?"
],
"Reasoning logic": "count occurrences of each group -> compare counts -> return max group(s)",
"Operator pattern": "add_column (optional) -> select_row -> select_column -> group_column -> argmax(count)",
"Constraints": ["group key must be categorical", "count is based on row frequency", "must consider tie cases"],
}"""


failure_skill_demo = """{
"Name": "incomplete_exhaustive_row_filtering",
"Tag": "General",
"Description": "Failing to exhaustively apply a filtering condition to all rows before performing downstream reasoning tasks.",
"Error Step": "select_row_args_error",
"Root Cause": "Apply row selection on only part of the table that matches the condition",
"Mitigation": [
    "Exhaustive scan required: always scan every row in the table when filtering, do not stop at the first N matches",
    "Verify completeness: after filtering, confirm the number of selected rows matches the total occurrences in the original table",
    "Avoid premature termination: do not assume filtering is complete because one or several matching rows have been found",
],
"Constraints": [
    "Applies when the filter condition is not spatially contiguous in the table",
    "More likely when rows are not sorted by the filter column",
    "Does not apply when the question asks for a single 'first' or 'last' occurrence only"
],
}"""


raw_skill_decision_demo = """**Raw Skill**: A Raw Skill extracted from successful trajectory
{
    "Name": "filter_group_max",
    "Tag": "conditional lookup",
    "Description": "Find the maximum value of a numeric column for rows matching a specific categorical condition",
    "Trigger": {
        "semantic": ["last", "most recent", "latest", "when ... was ..."],
        "structure": ["requires filtering", "requires finding maximum", "involves date or time sequence"]
    },
    "Question pattern": [
        "What was the last [time period] where [entity] was [condition]?",
        "When did [entity] stop being [condition]?",
        "Find the most recent [time period] associated with [condition]"
    ],
    "Reasoning logic": "Filter rows based on the categorical condition -> Identify the target numeric column (e.g., year) -> Select the row with the maximum value in that column -> Return the value",
    "Operator pattern": "select_column -> filter_row -> group_column -> argmax(target_column)",
    "Constraints": ["The target column must be sortable (e.g., dates, years)", "The condition column must be categorical", "If no rows match the condition, the skill fails"]
}

**Retrieved Skill**
{
    "Name": "filter_group_count",
    "Tag": "aggregation",
    "Description": "Count occurrences of specific values within a column after filtering based on semantic attributes of those values",
    "Trigger": {
        "semantic": ["how many times", "count", "number of", "italian", "nationality", "specific name pattern"],
        "structure": ["requires filtering by value property", "involves counting rows", "aggregation on a single column"]
    },
    "Question pattern": [
        "How many times did a [nationality] [entity type] win/perform [action]?",
        "Count the number of [entity type] from [nationality] who [action] in the table.",
        "What is the total count of [action] by [entity type] matching [attribute]?"
    ],
    "Reasoning logic": "Identify the target column containing the entity names -> Filter rows where the entity name matches the specified attribute (e.g., nationality) -> Group by the entity name (or count directly) -> Sum the occurrences",
    "Operator pattern": "f_select_column(target_column) -> f_group_column(target_column) -> filter_by_semantic_attribute -> sum_count",
    "Constraints": ["Target attribute (e.g., nationality) must be inferable from the value in the target column", "Each row represents a single independent event for counting", "No explicit attribute column exists; inference relies on value analysis"]
}

**Concise Explanation**:
The **Raw Skill** is of sufficient quality and not highly similar to the **Retrieved Skill**

**Decision**:
Add"""

