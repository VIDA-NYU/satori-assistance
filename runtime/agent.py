class Agent:
    def __init__(self, server, pipelines, config):
        self.server = server
        self.pipelines = pipelines
        for pipeline in self.pipelines:
            self.server.register_pipeline(pipeline)
        
        if 'triggers' in config:
            for trigger in config['triggers']:
                server.register_trigger(trigger['stream'], interval=trigger['interval'])

    async def start(self):
        await self.server.start()