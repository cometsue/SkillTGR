##VLLM
base_url='http://localhost:8001/v1'
openai_api_key='EMPTY'
model_name='qwen3.5-9b'
#model_name='ministral3-8B-instruct'

##Data
first_n=-1

##Dir
dataset_name="wikitq" # "wikitq", "tabfact"
dataset_path="reason/data/${dataset_name}/test_lower_refined.jsonl"
table_graphs_path="reason/data/${dataset_name}/graphs"
statement_embs_path="reason/data/${dataset_name}/test_statement_embs.pkl"

##result_dir
result_label="qwen3.5-9b"
results_dir="results/${dataset_name}/${result_label}"


##Script
python reason/reason_main.py \
--dataset_name $dataset_name \
--dataset_path $dataset_path \
--table_graphs_path $table_graphs_path \
--statement_embs_path $statement_embs_path \
--results_dir $results_dir \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n
if [ $? -ne 0 ]; then
    echo "Error in reason/reason_main.py"
    exit 1
fi