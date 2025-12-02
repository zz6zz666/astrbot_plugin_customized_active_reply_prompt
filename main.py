from astrbot.api.event import filter, AstrMessageEvent 
from astrbot.api.star import Context, Star, register 
from astrbot.api.provider import ProviderRequest 
from astrbot.api.platform import MessageType 
from astrbot.api import logger, AstrBotConfig 
import re 

@register("customized_reply_prompt", "zz6zz666", "自定义群聊主动回复提示词", "1.0.0") 
class CustomizedReplyPromptPlugin(Star): 
    def __init__(self, context: Context, config: AstrBotConfig): 
        super().__init__(context) 
        self.config = config  # AstrBotConfig继承自Dict，可以直接使用字典方法访问 
        logger.info("自定义主动回复提示词插件已初始化") 
    
    def _is_active_reply_enabled(self, event: AstrMessageEvent) -> bool: 
        """
        检查是否启用了主动回复功能
        """
        try: 
            # 获取配置信息，与long_term_memory.py中的cfg方法保持一致
            cfg = self.context.get_config(umo=event.unified_msg_origin) 
            active_reply = cfg["provider_ltm_settings"]["active_reply"] 
            return active_reply.get("enable", False) 
        except Exception as e: 
            logger.error(f"获取主动回复配置失败: {e}") 
            return False 

    @filter.on_llm_request(priority=-100)    # 优先级设为-100，确保在long_term_memory处理之后执行 
    async def replace_reply_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
        """
        在long_term_memory.py处理后，替换主动回复提示词
        """
        # 检查是否是群聊消息
        if event.get_message_type() != MessageType.GROUP_MESSAGE: 
            logger.debug(f"非群聊消息，跳过主动回复提示词替换")
            return
        
        # 检查是否启用了主动回复功能
        if not self._is_active_reply_enabled(event): 
            logger.debug(f"主动回复功能未启用，跳过提示词替换")
            return
        
        # 从配置中读取替换提示词
        replace_text = self.config.get("activate_reply_prompt", "")
        # 只有当替换文本不为空时才进行替换
        if not replace_text.strip():
            logger.debug(f"替换文本为空，跳过替换")
            return
        
        # 匹配LTM中设置的提示词格式，定位到"please react to it"处
        match = re.search(r'(?i)please react to it.*\Z', req.prompt)
        if match:
            # 替换整个提示词部分
            req.prompt = req.prompt[:match.start()] + replace_text
            logger.info(f"已替换自定义主动回复提示词")
        else:
            logger.debug(f"未找到LTM添加的主动回复提示词模式")

    async def terminate(self): 
        """插件卸载时的清理工作"""
        logger.info("自定义主动回复提示词插件已卸载")
