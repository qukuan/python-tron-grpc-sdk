import grpc
import logging
import base58
from api import api_pb2_grpc
from api import api_pb2
from core import Tron_pb2


# =======================
# 配置
# =======================
# TRON gRPC 节点地址
TRON_GRID_GRPC_ENDPOINT = 'grpc.trongrid.io:50051'

# 你的 TRONGRID API Key
TRON_GRID_API_KEY = "f412f159-e0a8-415a-b8d7-123456789" 

# 你想要查询的TRON地址（演示）
TRON_ADDRESS = "TTTTTTTTTTTTTTTTTTTTTTT123456789"

# 日志输出格式、级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


# ===========================
# gRPC 连接 功能演示函数
# ===========================
def get_latest_block_height(stub: api_pb2_grpc.WalletStub, metadata: list):
    """连接到 TRON gRPC 节点并获取最新的区块高度。"""
    try:
        logging.info("正在调用 GetNowBlock 方法获取最新区块...")
        request = api_pb2.EmptyMessage()
        response: Tron_pb2.Block = stub.GetNowBlock(request, metadata=metadata)
        block_height = response.block_header.raw_data.number
        logging.info(f"✅ 获取最新区块成功! 当前区块高度: {block_height}")
        return True
    except grpc.RpcError as e:
        logging.error(f"❌ 获取最新区块失败! gRPC 错误: {e.code()} - {e.details()}")
        return False
# 可以自己拓展：增加重试连接 网络延迟 异常时自动重连，全局Client



def get_account_info(stub: api_pb2_grpc.WalletStub, metadata: list):
    """获取地址的账户信息，演示主要是TRX余额。"""
    if not TRON_ADDRESS:
        logging.warning("未配置目标地址 (TRON_ADDRESS)，跳过账户查询。")
        return False
        
    try:
        logging.info(f"正在调用 GetAccount 方法查询地址: {TRON_ADDRESS}...")
        
        try:
            address_bytes = base58.b58decode_check(TRON_ADDRESS)
        except ValueError:
            logging.error(f"❌ 无效的TRON地址格式: {TRON_ADDRESS}")
            return False

        # 使用 `Tron_pb2.Account`
        # 因为 Account 是一个核心数据结构，定义在 core/Tron.proto 中。
        request = Tron_pb2.Account(address=address_bytes)
        
        # 调用远程方法，并传入元数据
        response = stub.GetAccount(request, metadata=metadata)
        
        # 余额以 SUN 为单位 (1 TRX = 1,000,000 SUN)
        balance_in_sun = response.balance
        balance_in_trx = balance_in_sun / 1_000_000
        
        logging.info(f"✅ 查询账户成功! 地址 {TRON_ADDRESS} 的余额为: {balance_in_trx:,.6f} TRX")
        return True
    except grpc.RpcError as e:
        logging.error(f"❌ 查询账户失败! gRPC 错误: {e.code()} - {e.details()}")
        return False


# 你可以去TRON官方开发文档 阅读gRPC API 相关接口进行更多功能开发，和SDK是一致的，官方tronprotocol原GitHub仓库复刻而来


def main():
    """主函数，建立连接并调用服务。"""
    logging.info(f"正在准备连接到 TRON gRPC 节点: {TRON_GRID_GRPC_ENDPOINT}...")
    
    # 准备 gRPC 元数据 (携带API Key)
    grpc_metadata = []
    if TRON_GRID_API_KEY and TRON_GRID_API_KEY != "YOUR_API_KEY_HERE":
        # 将元数据键改为全小写
        grpc_metadata.append(('tron-pro-api-key', TRON_GRID_API_KEY))
        logging.info("API Key 已配置，将随请求发送。")
    else:
        logging.warning("API Key 未配置。连接公共节点可能会失败或受到速率限制。")

    # --- 创建 gRPC 信道 ---
    # 选项1: 非加密信道
    channel = grpc.insecure_channel(TRON_GRID_GRPC_ENDPOINT)

    # 选项2: 加密信道
    # 如果上面的非加密方式失败，请注释掉上面一行，并取消下面两行的注释
    # credentials = grpc.ssl_channel_credentials()
    # channel = grpc.secure_channel(TRON_GRID_GRPC_ENDPOINT, credentials)
    
    # 创建一个 gRPC 存根 (Stub)
    stub = api_pb2_grpc.WalletStub(channel)
    
    logging.info("gRPC 信道和存根创建成功。")

    # --- 执行任务 ---
    print("-" * 60)
    get_latest_block_height(stub, grpc_metadata)
    print("-" * 60)
    get_account_info(stub, grpc_metadata)
    print("-" * 60)
    
    # 关闭信道
    channel.close()
    logging.info("gRPC 信道已关闭。")


if __name__ == '__main__':
    main()