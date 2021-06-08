from bot import bot


async def send_msg(**kwargs):
    # in discord, only exist private(DM) and group(channel)
    if 'channel_id' in kwargs:
        kwargs['message_type'] = 'group'
    elif 'user_id' in kwargs:
        kwargs['message_type'] = 'private'
    if 'message_type' in kwargs:
        if kwargs['message_type'] == 'group':
            return await send_group_msg(**kwargs)
        elif kwargs['message_type'] == 'private':
            return await send_private_msg(**kwargs)
    return -1


async def send_group_msg(**kwargs):
    channel = bot.get_channel(kwargs['channel_id'])
    if not channel:
        print('channel not found, args:{}'.format(kwargs))
        return -1
    if 'message' in kwargs and isinstance(kwargs['message'], str) and len(kwargs['message']) > 0:
        message = await channel.send(kwargs['message'])
        return message.id


async def send_private_msg(**kwargs):
    assert 'user_id' in kwargs
    user = await bot.fetch_user(int(kwargs['user_id']))
    if not user:
        print('user not find, try to get: {}'.format(kwargs['user_id']))
        return -1
    if 'message' in kwargs and isinstance(kwargs['message'], str) and len(kwargs['message']) > 0:
        message = await user.send(kwargs['message'])
        return message.id


def at_person(**kwargs) -> str:
    if not 'user_id' in kwargs:
        return ''
    return '<@{}>'.format(kwargs['user_id'])
