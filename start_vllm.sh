#!/bin/bash

PROJECT_ROOT="your_root_path" # e.g., /mnt/data/codes/
LOG_DIR="${PROJECT_ROOT}/your_log_path" # e.g., logs/qwen
MODEL_CACHE_DIR="your_cache_path" # e.g., "/mnt/data/models/vllm_cache"
VENV_PATH="your_env_path" # e.g., "/mnt/data/anaconda3/envs/vllm"
MODEL_NAME="your_path" # e.g., "/mnt/data/models/Qwen3.5-9B"
QUANTIZATION=""
SERVED_MODEL_NAME="qwen3.5-9b"

PORT=8001
TP_SIZE=1
GPU_ID=0
MAX_SEQS=128
MAX_LEN=40960
GPU_UTIL=0.95


log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_DIR}/vllm_mgr.log"; }
error() { log "❌ ERROR: $1"; exit 1; }
warn() { log "⚠️ WARNING: $1"; }

check_cmd() {
    command -v "$1" &>/dev/null || error "未找到命令: $1，请安装后重试"
}


check_gpu_memory() {
    local min_gb=8
    if [[ -n "$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i 0 2>/dev/null)" ]]; then
        local free_gb=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0 | awk '{print int($1/1024)}')
        if [[ $free_gb -lt $min_gb ]]; then
            warn "GPU 显存不足！当前空闲: ${free_GB}GB < 建议 ${min_gb}GB"
            read -p "是否继续？(y/N): " -n 1 -r
            echo
            [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
        fi
    else
        warn "nvidia-smi 未找到，跳过 GPU 检查"
    fi
}

ACTION=${1:-start}

mkdir -p "${LOG_DIR}" || error "无法创建日志目录: ${LOG_DIR}"

case "$ACTION" in
    start)
        log "🚀 开始启动 vLLM 服务..."

        check_cmd python
        check_cmd nvidia-smi
        [[ -d "${VENV_PATH}" ]] || error "虚拟环境不存在: ${VENV_PATH}"

        if lsof -i :${PORT} &>/dev/null; then
            warn "端口 ${PORT} 已被占用！"
            lsof -i :${PORT} | tail -n +2 | awk '{print "  PID:", $2, "=>", $1}'
            read -p "是否强制终止并继续？(y/N): " -n 1 -r
            echo
            [[ $REPLY =~ ^[Yy]$ ]] && kill -9 $(lsof -t -i :${PORT}) || exit 1
        fi

        check_gpu_memory


        START_CMD="
            export CUDA_VISIBLE_DEVICES=${GPU_ID};  # ←←← 关键：指定使用的GPU
            export VLLM_MODEL_CACHE_DIR='${MODEL_CACHE_DIR}';
            nohup conda run -n vllm --no-capture-output \\
                python -m vllm.entrypoints.openai.api_server \\
                    --model '${MODEL_NAME}' \\
                    --quantization '${QUANTIZATION}' \\
                    --trust-remote-code \\
                    --dtype auto \\
                    --tensor-parallel-size ${TP_SIZE} \\
                    --max-model-len ${MAX_LEN} \\
                    --max-num-seqs ${MAX_SEQS} \\
                    --gpu-memory-utilization ${GPU_UTIL} \\
                    --port ${PORT} \\
                    --served-model-name '${SERVED_MODEL_NAME}' \\
                    > '${LOG_DIR}/vllm.log' 2>&1 &
            echo \$! > '${LOG_DIR}/vllm.pid'
        "

        log "正在启动服务... (日志: ${LOG_DIR}/vllm.log)"
        bash -c "$START_CMD"

        for i in {1..100}; do
            sleep 1
            if curl -sf http://localhost:${PORT}/v1/models &>/dev/null; then
                log "✅ vLLM 服务启动成功！模型: ${SERVED_MODEL_NAME} | 端口: ${PORT}"
                exit 0
            fi
            printf "."
        done
        error "服务启动超时！请检查 ${LOG_DIR}/vllm.log"
        ;;

    stop)
        if [[ -f "${LOG_DIR}/vllm.pid" ]]; then
            PID=$(cat "${LOG_DIR}/vllm.pid")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID" && log "⏹️ 已停止 vLLM (PID: $PID)"
            else
                warn "PID $PID 不存在，清理残留"
            fi
        else
            warn "未找到 vllm.pid，尝试通过端口终止"
        fi
        # 备份终止
        pkill -f "vllm.*api_server" && log "⏹️ 已终止所有 vLLM 进程" || log "⚠️ 无 vLLM 进程运行"
        rm -f "${LOG_DIR}/vllm.pid"
        ;;

    restart)
        $0 stop && sleep 2 && $0 start
        ;;

    status)
        if [[ -f "${LOG_DIR}/vllm.pid" ]]; then
            PID=$(cat "${LOG_DIR}/vllm.pid")
            if kill -0 "$PID" 2>/dev/null; then
                echo "🟢 vLLM 正在运行 (PID: $PID)"
                echo "   日志: tail -f ${LOG_DIR}/vllm.log"
                echo "   API:  curl http://localhost:${PORT}/v1/models"
                exit 0
            fi
        fi
        echo "🔴 vLLM 未运行"
        ;;

    logs)
        if [[ -f "${LOG_DIR}/vllm.log" ]]; then
            tail -n 50 "${LOG_DIR}/vllm.log"
        else
            echo "⚠️ 日志文件不存在: ${LOG_DIR}/vllm.log"
        fi
        ;;

    systemd)
        log "📦 生成 systemd 用户服务文件..."
        SERVICE_FILE="${HOME}/.config/systemd/user/vllm-table-critic.service"
        mkdir -p "$(dirname "$SERVICE_FILE")"
        
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=vLLM for Table-Critic (刘家成)
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=${PROJECT_ROOT}
Environment="VLLM_MODEL_CACHE_DIR=${MODEL_CACHE_DIR}"
ExecStart=${VENV_PATH}/bin/python -m vllm.entrypoints.openai.api_server \\
    --model '${MODEL_NAME}' \\
    --quantization '${QUANTIZATION}' \\
    --trust-remote-code \\
    --dtype auto \\
    --tensor-parallel-size ${TP_SIZE} \\
    --max-model-len ${MAX_LEN} \\
    --max-num-seqs ${MAX_SEQS} \\
    --gpu-memory-utilization ${GPU_UTIL} \\
    --port ${PORT} \\
    --served-model-name '${SERVED_MODEL_NAME}'
Restart=always
RestartSec=10
StandardOutput=append:${LOG_DIR}/vllm.log
StandardError=append:${LOG_DIR}/vllm.log

[Install]
WantedBy=default.target
EOF

        systemctl --user daemon-reload
        log "✅ systemd 服务已生成！使用以下命令管理："
        echo "  systemctl --user enable vllm-table-critic   # 开机自启"
        echo "  systemctl --user start vllm-table-critic    # 启动"
        echo "  systemctl --user status vllm-table-critic   # 查看状态"
        ;;

    *)
        echo "用法: $0 {start|stop|restart|status|logs|systemd}"
        echo "示例:"
        echo "  $0 start      # 启动服务"
        echo "  $0 systemd    # 生成 systemd 服务（推荐生产环境）"
        exit 1
        ;;
esac