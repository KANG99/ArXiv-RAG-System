#!/bin/bash
set -e

export AIRFLOW_HOME=/opt/airflow

echo "清理历史残余 PID..."
ps aux | grep airflow | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
rm -f ${AIRFLOW_HOME}/airflow-*.pid
sleep 2

echo "执行 Airflow 3.x 数据库迁移..."
airflow db migrate

echo "正在启动 Airflow 3.x 一体化多微服务集群..."

# 1. 后台异步启动 3.x 强制需要的 DAG 解析器
airflow dag-processor > ${AIRFLOW_HOME}/logs/dag_processor.log 2>&1 &
PID_PROCESSOR=$!

# 2. 后台异步启动 3.x 调度器
airflow scheduler > ${AIRFLOW_HOME}/logs/scheduler.log 2>&1 &
PID_SCHEDULER=$!

# 3. 后台异步启动触发器
airflow triggerer > >(tee -a ${AIRFLOW_HOME}/logs/triggerer.log) 2>&1 &
PID_TRIGGERER=$!

# 4. 后台异步启动 前端 API 服务
airflow api-server --port 8080 > ${AIRFLOW_HOME}/logs/api_server.log 2>&1 &
PID_API=$!

echo "进程启动完毕，看门狗已就绪。正在监控核心组件健康状况..."

# 建立常驻循环：任何一个组件意外死掉，立即让容器退出并报错
while true; do
    if ! kill -0 $PID_PROCESSOR 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 致命错误: dag-processor 进程已崩溃 (PID: $PID_PROCESSOR)！"
        exit 1
    fi
    if ! kill -0 $PID_SCHEDULER 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 致命错误: scheduler 进程已崩溃 (PID: $PID_SCHEDULER)！"
        exit 1
    fi
    if ! kill -0 $PID_TRIGGERER 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 致命错误: triggerer 进程已崩溃 (PID: $PID_TRIGGERER)！"
        exit 1
    fi
    if ! kill -0 $PID_API 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 致命错误: api-server 进程已崩溃 (PID: $PID_API)！"
        exit 1
    fi
    sleep 5
done
