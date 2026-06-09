# Copyright 2024 The Chain-of-Table authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import openai
from openai import OpenAI
import time
import numpy as np
import re
import json


use_api = False #!!!
qwen_vllm_no_think = True

# ministral(vllm), qwen(api) no think
extra_body={"enable_thinking": False}


if qwen_vllm_no_think:
    # qwen(vllm) no think
    extra_body = {"chat_template_kwargs": {"enable_thinking": False}}



class LLM:
    def __init__(self, model, key, base_url):
        self.model = model
        self.key = key
        self.base_url = base_url

    def get_model_options(
        self,
        temperature=0.0,
        top_p=1.0,
        max_tokens=1024,
        n=1
    ):
        return dict(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n=n
        )

    def generate_plus_with_score(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()

        messages = [
            {
                "role": "system",
                "content": "I will give you some examples, you need to follow the examples and complete the text, and no other content.",
            },
            {"role": "user", "content": prompt},
        ]
        gpt_responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        client = OpenAI(api_key=self.key, base_url=self.base_url)

        while gpt_responses is None:
            try:
                gpt_responses = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stop=end_str,
                    extra_body=extra_body,
                    stream=False,
                    **options
                )
                error = None
                if use_api:
                    time.sleep(0.5)

            except Exception as e:
                print(str(e), flush=True)
                error = str(e)
                if "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                else:
                    time.sleep(5)
                retry_num += 1
        if error:
            raise Exception(error)

        results = []
        for i, res in enumerate(gpt_responses.choices):
            text = res.message.content
            # 这个输出的置信度是固定可计算的，后续可参考改为每个token的平均logprobs
            fake_conf = (len(gpt_responses.choices) - i) / len(gpt_responses.choices)
            results.append((text, np.log(fake_conf)))

        return results


    def generate_graph_reason(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        messages = [
            {
                "role": "system",
                "content": "I will give you some examples, you need to follow the examples and complete the text, and no other content.",
            },
            {"role": "user", "content": prompt},
        ]
        responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        client = OpenAI(api_key=self.key, base_url=self.base_url)

        while responses is None:
            try:
                responses = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stop=end_str,
                    # extra_body={
                    #     "chat_template_kwargs": {"enable_thinking": False},
                    # }, # qwen vllm no_think
                    # extra_body={"enable_thinking": False},
                    extra_body=extra_body,
                    stream=False,
                    # presence_penalty=0.0,
                    # frequency_penalty=0.0,
                    **options
                )
                error = None
                if use_api:
                    time.sleep(0.5)
            except Exception as e:
                print(str(e), flush=True)
                error = str(e)
                if "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                else:
                    time.sleep(5)
                retry_num += 1

        if error:
            raise Exception(error)

        results = []
        for i, res in enumerate(responses.choices):
            text = res.message.content
            paths_match = re.search(r"<paths>(.*?)</?paths>", text, re.S)
            paths_content = paths_match.group(1).strip() if paths_match else "error"
            think_match = re.search(r"<thought>(.*?)</?thought>", text, re.S)
            think_content = think_match.group(1).strip() if think_match else "error"
            answer_match = re.search(r"<answer>(.*?)</?answer>", text, re.S)
            answer_content = answer_match.group(1).strip() if answer_match else "error"
            result = {
                'text': text,
                'paths': paths_content,
                'thought': think_content,
                'answer': answer_content
            }
            results.append(result)

        return results


    def generate_plus_with_score_final_query(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {"role": "user", "content": prompt},
        ]
        gpt_responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        client = OpenAI(api_key=self.key, base_url=self.base_url)
        while gpt_responses is None:
            try:
                gpt_responses = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stop=end_str,
                    extra_body=extra_body,
                    stream=False,
                    **options
                )
                error = None
                if use_api:
                    time.sleep(0.5)

            except Exception as e:
                print(str(e), flush=True)
                error = str(e)
                if "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                else:
                    time.sleep(5)
                retry_num += 1
        if error:
            raise Exception(error)

        results = []
        for i, res in enumerate(gpt_responses.choices):
            text = res.message.content
            # 这个输出的置信度是固定可计算的，后续可参考改为每个token的平均logprobs
            fake_conf = (len(gpt_responses.choices) - i) / len(gpt_responses.choices)
            results.append((text, np.log(fake_conf)))

        return results


    def generate(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        options["n"] = 1
        result = self.generate_plus_with_score(prompt, options, end_str)[0][0]
        return result

