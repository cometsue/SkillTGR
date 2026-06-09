# SkillTGR

Code for SkillTGR framework

---

## Quick Start

SkillTGR requires **two separate environments**: one for the vLLM API service and one for the main framework.

---

### Step 1: Deploy LLM API Service

#### 1.1 Create and Activate the vLLM Environment

```bash
conda create --name vllm python=3.11 -y
conda activate vllm
pip install vllm==0.17.0
```

#### 1.2 Configure the Startup Script

Before launching the service, open `start_vllm.sh` and update the following variables to match your environment:

```bash
PROJECT_ROOT="your_root_path"       # Root directory of the project
LOG_DIR="${PROJECT_ROOT}/your_log_path"  # Directory to store logs
MODEL_CACHE_DIR="your_cache_path"   # Directory where model weights are cached
VENV_PATH="your_env_path"           # Path to the vllm conda environment
MODEL_NAME="your_model_path"        # Path or name of the LLM to serve
```

#### 1.3 Start the vLLM Service

```bash
bash start_vllm.sh
```

> ✅ Make sure the vLLM API service is running successfully before proceeding to the next step.

---

### Step 2: Set Up Main Environment

#### 2.1 Create and Activate the SkillTGR Environment

```bash
conda create --name SkillTGR python=3.11 -y
conda activate SkillTGR
pip install -r requirements.txt
```

#### 2.2 Download SentenceBERT Model

Download the [SentenceBERT](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) model and place it in the `skill/sentencebert/` directory.

#### 2.3 Extract Skill Database

Extract `chroma.tar.gz` in the `skill/skillbank/testset/skill_db/` directory to obtain `chroma.sqlite3`:

```bash
tar -xzf skill/skillbank/testset/skill_db/chroma.tar.gz -C skill/skillbank/testset/skill_db/
```

#### 2.4 Configure and Run

Open `run.sh` and select the target dataset by modifying the `dataset_name` variable:

```bash
# Available options: "wikitq", "tabfact"
dataset_name="wikitq"
```

Then launch the framework:

```bash
bash run.sh
```
