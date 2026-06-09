from trajectory import generate_trajectory
from llm import LLM
from prompt import judge_trajectory_prompt, critic_failed_trajectory_prompt, gen_success_skill_prompt, gen_failure_skill_prompt
from few_shot_demo import judge_trace_few_shot_demo, critic_trace_few_shot_demo, success_skill_demo, failure_skill_demo
import pandas as pd
import os
from tqdm import tqdm
import multiprocessing as mp


def judge_trajectory(trajectory, llm, llm_options):
    prompt = judge_trajectory_prompt.replace("[judge_trace_few_shot_demo]", judge_trace_few_shot_demo)
    prompt = prompt.replace("[judge_trajectory]", trajectory)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    results = []
    for i, res in enumerate(responses):
        results.append(res)
    judge_result = results[0]

    return judge_result


def critic_failed_trajectory(trajectory, llm, llm_options):
    prompt = critic_failed_trajectory_prompt.replace("[critic_failed_trajectory_demo]", critic_trace_few_shot_demo)
    prompt = prompt.replace("[critic_failed_trajectory]", trajectory)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    critic_result = responses[0][0]

    return critic_result


def gen_success_skill(success_trajectory, llm, llm_options):
    prompt = gen_success_skill_prompt.replace("[success_skill_demo]", success_skill_demo)
    prompt = prompt.replace("[successful_trajectory]", success_trajectory)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    raw_skill = responses[0][0]

    return raw_skill


def gen_failure_skill(failure_trajectory, critic_result, llm, llm_options):
    prompt = gen_failure_skill_prompt.replace("[failure_skill_demo]", failure_skill_demo)
    prompt = prompt.replace("[failed_trajectory]", failure_trajectory)
    prompt = prompt.replace("[critic_result]", critic_result)
    responses = llm.generate_plus_with_score(prompt, llm_options)
    raw_skill = responses[0][0]

    return raw_skill

def process_one_trajectory(arg):
    trainset_trace_path = "skill/data/trajectory/trainset"
    trainset_trace_file, trajectory, ids, is_correct, llm, llm_options = arg

    try:

        if int(is_correct) == 1:
            success_raw_skill = gen_success_skill(trajectory, llm, llm_options)
            save_success_skill_path = f'skill/data/raw_skill/trainset/success/{ids}.txt'
            with open(save_success_skill_path, 'w', encoding='utf-8') as f_success:
                f_success.write(success_raw_skill)
            f_success.close()
            process_info = f'save success skill in {ids}.txt'
            return process_info

        elif int(is_correct) == 0:
            critic_result = critic_failed_trajectory(trajectory, llm, llm_options)
            save_failed_critic_path = f'skill/data/trajectory/trainset/critic_failed/{ids}.txt'
            with open(save_failed_critic_path, 'w', encoding='utf-8') as f_critic:
                f_critic.write(critic_result)
            f_critic.close()

            failure_raw_skill = gen_failure_skill(trajectory, critic_result, llm, llm_options)
            save_failed_skill_path = f'skill/data/raw_skill/trainset/failure/{ids}.txt'
            with open(save_failed_skill_path, 'w', encoding='utf-8') as f_failure:
                f_failure.write(failure_raw_skill)
            f_failure.close()

            process_info = f'save failure skill in {ids}.txt'
            return process_info

    except Exception as e:
        print(f"Error in {trainset_trace_file}: {e}", flush=True)
        process_info = f"Error in {trainset_trace_file}: {e}"
        return process_info
