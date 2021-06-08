from bot import bot
from plugins.jjc_watcher import initialize

if __name__ == '__main__':
    import json
    with open('./config.json') as f:
        config = json.load(f)
    initialize(config)
    bot.run(config['token'])
