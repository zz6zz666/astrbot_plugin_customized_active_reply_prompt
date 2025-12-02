from astrbot.api.event import filter, AstrMessageEvent 
from astrbot.api.star import Context, Star, register 
from astrbot.api.provider import ProviderRequest 
from astrbot.api.platform import MessageType 
from astrbot.api import logger, AstrBotConfig 
import re 

@register("customed_reply_prompt", "zz6zz666", "自定义群聊主动回复提示词", "1.0.0") 
class CustomedReplyPromptPlugin(Star): 
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
            
    @filter.on_llm_request(priority=-10)    # 优先级设为-10，确保在其他处理后（包括long term memory）执行 
    async def process_user_prompt(self, event: AstrMessageEvent, req: ProviderRequest): 
        """ 
        在群聊场景下，当启用主动回复功能时， 
        匹配user字段最末尾的Please react to it.... 并进行替换 
        """ 
        # 检查是否是群聊消息
        if event.get_message_type() != MessageType.GROUP_MESSAGE: 
            logger.debug(f"非群聊消息，跳过提示词替换")
            return 
        
        # 检查是否启用了主动回复功能
        if not self._is_active_reply_enabled(event): 
            logger.debug(f"主动回复功能未启用，跳过提示词替换")
            return 

        if req.contexts and len(req.contexts) > 0: 
            # 直接获取最后一个消息（在主动回复场景下，这里应该是user字段） 
            ctx = req.contexts[-1] 
            
            # 确保是user角色且content是字符串类型 
            if ctx.get("role") == "user" and isinstance(ctx.get("content"), str): 
                content = ctx.get("content") 
                
                # 从字符串末尾开始反向搜索（只需找最后一次出现） 
                match = re.search(r'(?i)please react to it.*\Z', content) 
                if match: 
                    # 从配置中读取替换提示词 
                    replace_text = self.config.get("activate_reply_prompt", "") 
                    # 只有当替换文本不为空时才进行替换 
                    if replace_text.strip(): 
                        content = content[:match.start()] + replace_text 
                        ctx["content"] = content 
                        logger.info(f"已替换为自定义主动回复提示词") 

    async def terminate(self): 
        """插件卸载时的清理工作"""
        logger.info("自定义主动回复提示词插件已卸载")