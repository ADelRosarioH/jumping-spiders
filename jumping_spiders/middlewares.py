from pkg_resources import resource_string as load
import random
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

class RandomUserAgentMiddleware(UserAgentMiddleware):

    def __init__(self, settings, user_agent='Scrapy'):
        super(RandomUserAgentMiddleware, self).__init__()
        self.user_agent = user_agent
        user_agent_list_file = settings.get('USER_AGENT_LIST')
        if not user_agent_list_file:
            # If USER_AGENT_LIST_FILE settings is not set,
            # Use the default USER_AGENT or whatever was
            # passed to the middleware.
            ua = settings.get('USER_AGENT', user_agent)
            self.user_agent_list = [ua]
        else:
            try:
                with open(user_agent_list_file, 'r') as f:
                    self.user_agent_list = [line.strip() for line in f.readlines()]
            except:
                user_agents = load('jumping_spiders', user_agent_list_file)
                self.user_agent_list = [line.strip() for line in user_agents.splitlines()]

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(crawler.settings)
        crawler.signals.connect(obj.spider_opened,
                                signal=signals.spider_opened)
        return obj

    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agent_list)
        spider.logger.debug('User-Agent: %s', user_agent)
        if user_agent:
            request.headers.setdefault('User-Agent', user_agent)
