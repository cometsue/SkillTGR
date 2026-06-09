gen_success_skill_prompt = """Your task is to abstract the successful trajectory into a generalized, reusable Skill.
The trajectory consists of three parts:
1. **Table**: table caption, columns, and rows
2. **Question**: the natural language query pertaining to the table data
3. **Dynamic Chain**: step-by-step operators (with thoughts) leading to the correct answer

Output the Skill with following **JSON** format:
{
    "Name": "",
    "Tag": "",
    "Description": "",
    "Trigger": {
        "semantic": [],
        "structure": [],
    },
    "Question pattern": [],
    "Reasoning logic": "",
    "Operator pattern": "",
    "Constraints": [],
}
where, the explanation of each field:
- **Name**: A concise phrase using underscore-separated words to represent the core reasoning steps (e.g., group_count_argmax)
- **Tag**: The question type classification, belongs to one of following five categories: conditional lookup, comparison, extremum, aggregation, arithmetic 
- **Description**: One-sentence summary of what this skill does
- **Trigger**: Activated signals for this skill in terms of semantics and structure
  - semantic: several keywords/phrases in a question (e.g., most, highest number, largest number of)
  - structure: several reasoning characteristics (e.g., requires grouping, counting, comparison)
- **Question pattern**: Three generalized question templates abstracted from the original question
- **Reasoning logic**: Core reasoning steps in natural language (avoid table-specific details)
- **Operator pattern**: Abstracted sequence of operators used (ignore irrelevant steps, keep essential pattern)
- **Constraints**: Three Key assumptions or limitations (e.g., data type, tie handling, applicability scope)

Instructions:
- **Generalize**: Focus on reasoning patterns, not specific table content
- **Reuse**: Keep Skill reusable across similar pattern of questions with different table context
- **Concise**: Avoid verbose descriptions but informative
- **Complete**: Ensure the skill can actually solve the original question type
- **Output**: Return the Skill only, no other text

Here is the skill example:
[success_skill_demo]

Now, abstract the following reasoning trajectory into a reusable skill:
[successful_trajectory]"""


gen_failure_skill_prompt = """Your task is to abstract the failure trajectory into a generalized, reusable Skill that captures common error patterns and their mitigations.
The trajectory consists of four parts:
1. **Table**: table caption, columns, and rows
2. **Question**: the natural language query pertaining to the table data
3. **Reasoning Process**: 
   - Dynamic Chain: The sequential operator chain that plans to solve the table question step by step.
   - Operator Execution: The execution process of each operator planned in the Dynamic Chain, with parameters, info and thought
   - Final Reason: The structured reasoning process based on knowledge triples of Table Graph, with reason path and thought
4. **Prediction Answer**: The final answer derived from the reasoning process.
5. **Critique**: Explanation identifying the incorrect reasoning step and what is wrong in it

Output the Skill with following **JSON** format:
{
    "Name": "",
    "Tag": "",
    "Description": "",
    "Error Step": "",
    "Root Cause": "",
    "Mitigation": [],
    "Constraints": [],
}
where, the explanation of each field:
- **Name**: A concise phrase using underscore-separated words to represent the core failure pattern (e.g., incomplete_exhaustive_row_filtering)
- **Tag**: The failure category, use "General" for generic errors, or one of [conditional lookup, comparison, extremum, aggregation, arithmetic] if the error is specific to a question type
- **Description**: One-sentence summary of what went wrong
- **Error Step**: One of **chain error**, **{operator}_args_error** (argument error in add_column/select_row/select_column/group_by/sort_by), or **reason error** (final reasoning error)
- **Root Cause**: The concise reason for failure (focus on reasoning flaw, not specific table content)
- **Mitigation**: Three concise strategies to fix and prevent this type of error
- **Constraints**: Three concise key conditions describing when this failure is likely or not applicable

Instructions:
- **Generalize**: Identify the generalizable reasoning mistake, not specific table content
- **Concise**: Avoid verbose descriptions but informative
- **Output**: Return the Skill only, no other text

Here is the failure skill example:
[failure_skill_demo]

Now, abstract the following failed reasoning trajectory into a reusable skill to avoid error in future reasoning:
[failed_trajectory]

**Critique**:
[critic_result]"""


judge_trajectory_prompt = """You are an intelligent judge tasked with verifying whether the Prediction Answer is correct or incorrect based on the following information:

1. **Table**: The raw table data with table caption, columns, and rows.
2. **Question**: The natural language query pertaining to the table data.
3. **Prediction Answer**: The answer to the above question remains to be verified.

Instruction:
1. **Explanation**:
   - Carefully analyze the table and question.
   - Check whether the Prediction Answer is fully supported by the table data.
   
2. **Conclusion**:
   - If the Prediction Answer is fully correct, output: 'Conclusion: [Correct]'
   - If the Prediction Answer is partially correct, unsupported, or incorrect, output: 'Conclusion: [Incorrect]'

Here are some few-shot examples:
[judge_trace_few_shot_demo]

Now, judge and verify the following Prediction Answer whether is correct:
[judge_trajectory]"""


critic_failed_trajectory_prompt = """You are an intelligent critic tasked with determining which step of the table reasoning is incorrect based on the following information:

1. **Table**: The raw table data with table caption, columns, and rows.
2. **Question**: The natural language query pertaining to the table data.
3. **Reasoning Process**: 
   - Dynamic Chain: The sequential operator chain that plans to solve the table question step by step.
   - Operator Execution: The execution process of each operator planned in the Dynamic Chain, with parameters, info and thought
   - Final Reason: The structured reasoning process based on knowledge triples of Table Graph, with reason path and thought
4. **Prediction Answer**: The final answer derived from the reasoning process.

Instruction:
1. **Error existence**: The reasoning sample must contain at least one incorrect reasoning step.
2. **Step-wise Analysis**: Conduct an evaluation of each reasoning step's validity.
3. **Analysis Categories:**
    - **Reasoning Process** belongs to one of **Dynamic Chain**, **Operator Execution**, **Final Reason**
    - For incorrect steps: Detail the logical flaws and mark as 'Step **Reasoning Process** is incorrect'.
    - You should stop at the first incorrect step.
4. **Conclude this critique**: Summarize this critique with an explicit conclusion.
5. **Conclusion Categories**:
    - Conclude with 'Conclusion: [Incorrect] Step **Reasoning Process**'.

Here is the critique example:[critic_failed_trajectory_demo]

Now, critique the following failed sample:
[critic_failed_trajectory]

**Critique**:"""


raw_skill_decision_prompt = """You are an intelligent judge tasked with deciding how to handle a newly extracted Raw Skill.

You are given:
1. **Raw Skill**: A Skill newly extracted from a trajectory.
2. **Retrieved Skill**: The most relevant existing skll retrieved from the SkillBank

Output the **Concise Explanation** and the **Decision** one of {Add, Discard, Merge}

Instruction:
1. **Raw Skill Evaluation**: Assess the RAW SKILL based on the following criteria:
    - Generalization: Is the Skill captures a general reasoning pattern (for success) or reasoning mistake pattern (for failure), WITHOUT relying on any specific table content (e.g., column names, specific value)? If it contains such specifics, treat it as low quality.
    - Reusability: Can it be reused across similar question patterns or avoid similar error?
    - Completeness: Forms a full reasoning strategy (for success) or a clearly defined mistake with cause (for failure)
    
2. **Decision Rules**: Make decision with one of following action:
    - Add: If the **Raw Skill** is of sufficient quality and not highly similar to the **Retrieved Skill**
    - Discard: If the **Raw Skill** is low quality (especially not generalizable), or similar to the **Retrieved Skill** but brings no improvement.
    - Merge: If the **Raw Skill** is highly similar to the **Retrieved Skill** but provides clear optimization or complementary information.

Here is the example:
[raw_skill_decision_demo]

Now, make the decision for the following Raw Skill:

**Raw Skill**: A Raw Skill extracted from [success_or_failure] trajectory
[current_raw_skill]

**Retrieved Skill**
[retrieved_skill]

**Concise Explanation**:"""


skill_merge_prompt = """Your task is to combine the an Existing Skill and a Candidate Skill into one improved Merged Skill.

You are given:
1. **Existing Skill**: The current skill from the SkillBank, representing the baseline version.
2. **Candidate Skill**: A newly extracted skill that may provide improvements or refinements over the Existing Skill.

Merge Rules:
1. **Schema Consistency**: The Merged Skill MUST keep the exact same fields as the input skills. Only update the content (values) of fields.
2. **Quality Improvement**: The Merged Skill must be strictly better than the Existing Skill. Prefer the Candidate Skill when it improves generalization, completeness, or clarity. Rewrite fields instead of copying.
3. **No Concatenation**: Do NOT concatenate content. Always synthesize into a cleaner and more canonical form.
4. **No Redundancy**: Remove duplicated, overlapping, or semantically similar items. Merge similar expressions into one generalized form.
5. **Generalization Constraint**: The Merged Skill must remain fully generalizable. Do NOT include dataset-specific details (e.g., column names, formats, examples).
6. **Refinement over Union**: When both skills contain similar information, compress them into fewer, higher-quality items instead of keeping both.
7. **List Length Constraint (STRICT)**:
   - For any field whose value is a list (e.g., Trigger.semantic, Trigger.structure, Question pattern, Constraints, Mitigation):
     - The number of items MUST NOT exceed **5**.
     - If there are more than 5 candidates, you MUST:
       a. Remove redundant or low-information items
       b. Merge similar items into a more general expression
       c. Keep only the most representative, high-coverage, and diverse items
8. **Priority for List Pruning**:
   When reducing list items, prioritize:
   - High generality over specificity
   - Semantic diversity over minor variations
   - Canonical phrasing over paraphrases
9. **Conciseness Requirement**:
   The final skill should be compact, high-signal, and easy to reuse. Avoid verbosity.

Output ONLY the **Merged Skill** as a valid JSON object. Do NOT include any explanation or additional text.

**Existing Skill**:
[retrieved_skill]

**Candidate Skill**:
[current_raw_skill]

**Merged Skill**:
"""
