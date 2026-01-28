#!/bin/bash

# =================================================================
# 脚本名称: setup_dds.sh
# 功能: 自动化编译 iceoryx, cyclonedds 并配置环境
# =================================================================

# 遇到错误立即停止
set -e

# 获取当前绝对路径作为工作根目录
cd teleai_dds_wrapper/third_party
WORKSPACE=$(pwd)
ICEORYX_INSTALL_DIR="${WORKSPACE}/iceoryx/install"
CYCLONEDDS_INSTALL_DIR="${WORKSPACE}/cyclonedds/install"

echo "开始安装系统依赖项..."
sudo apt update
sudo apt install -y cmake libacl1-dev libncurses5-dev pkg-config maven git vim python3-pip

# --- 1. 下载并编译 iceoryx ---
echo "正在处理 iceoryx..."
if [ ! -d "iceoryx" ]; then
    git clone https://github.com/eclipse-iceoryx/iceoryx.git -b release_2.0
fi
cd iceoryx
mkdir -p build
cmake -Bbuild -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="${ICEORYX_INSTALL_DIR}" \
      -DROUDI_ENVIRONMENT=on \
      -DBUILD_SHARED_LIBS=ON \
      -DINTROSPECTION=ON \
      -Hiceoryx_meta
cmake --build build --config Release --target install
cd "${WORKSPACE}"

echo "正在处理 cyclonedds..."
if [ ! -d "cyclonedds" ]; then
    git clone https://github.com/eclipse-cyclonedds/cyclonedds.git
fi
cd cyclonedds
mkdir -p build
cmake -Bbuild -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX="${CYCLONEDDS_INSTALL_DIR}" \
      -DENABLE_ICEORYX=On \
      -DBUILD_EXAMPLES=On \
      -DCMAKE_PREFIX_PATH="${ICEORYX_INSTALL_DIR}"
cmake --build build --config Release --target install
cd "${WORKSPACE}"

# --- 5. 配置环境变量 (写入 .bashrc) ---
echo "正在配置 .bashrc..."

# 定义标记，防止重复写入
MARKER_START="# >>> TELEAI DDS SETUP START >>>"
MARKER_END="# >>> TELEAI DDS SETUP END >>>"

# 准备环境变量内容
ENV_BLOCK=$(cat <<EOF
$MARKER_START
# Iceoryx
export PATH="${ICEORYX_INSTALL_DIR}/bin:\$PATH"
export LD_LIBRARY_PATH="${ICEORYX_INSTALL_DIR}/lib:\$LD_LIBRARY_PATH"

# CycloneDDS
export CYCLONEDDS_URI="file://${WORKSPACE}/../configs/cyclonedds.xml"
export CYCLONEDDS_HOME="${CYCLONEDDS_INSTALL_DIR}"
export PATH="${CYCLONEDDS_INSTALL_DIR}/bin:\$PATH"
export LD_LIBRARY_PATH="${CYCLONEDDS_INSTALL_DIR}/lib:\$LD_LIBRARY_PATH"
$MARKER_END
EOF
)

# 清除旧的标记块并写入新块
sed -i "/$MARKER_START/,/$MARKER_END/d" ~/.bashrc
echo "$ENV_BLOCK" >> ~/.bashrc

# --- 6. 安装 Python 绑定 ---
echo "正在安装 cyclonedds-python..."
export CYCLONEDDS_HOME="${CYCLONEDDS_INSTALL_DIR}"
pip install git+https://github.com/eclipse-cyclonedds/cyclonedds-python@master

echo "--------------------------------------------------"
echo "恭喜！编译与配置已完成。"
echo "请手动执行: source ~/.bashrc"
echo "警告：请勿移动本库"
echo "测试说明:"
echo "python -m verify_all_types"
echo "--------------------------------------------------"