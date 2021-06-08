from utils.pcrclient import pcrclient, ApiException
from asyncio import Lock
from copy import deepcopy
from traceback import format_exc
from utils.playerpref import decryptxml
from utils.sender import *
from discord.ext import tasks
from bot import bot

import os
import json

_config = None
_binds = None
_cache = None
qlck = Lock()
lck = Lock()
_clients = {}


async def query(id: str, client):
    async with qlck:
        while client.shouldLogin:
            await client.login()
        res = (await client.callapi('/profile/get_profile', {
            'target_viewer_id': int(id)
        }))
        return res['user_info']


def initialize(config):
    global _config, _binds, _cache, _clients
    _config = config
    if not os.path.exists(_config['binds_file']):
        with open(config['binds_file'], 'w') as f:
            json.dump({}, f)
    with open(config['binds_file'], 'r') as f:
        _binds = json.load(f)
    _cache = {}
    for server in config['playerprefs']:
        acinfo = decryptxml(config['playerprefs'][server])
        _clients[server] = pcrclient(acinfo['UDID'],
                                     acinfo['SHORT_UDID'],
                                     acinfo['VIEWER_ID'],
                                     acinfo['DL_BDL_VER'].decode(),
                                     '' if acinfo['TW_SERVER_ID'] == '1' else acinfo['TW_SERVER_ID'],
                                     _config['proxy'])
        print('TW-{} client started'.format(server))


bot.remove_command('help')


@bot.command(name='help')
async def _jjc_help(ctx):
    _sv_help = '''[bind uid server] 绑定竞技场排名变动推送，默认双场均启用，仅排名降低时推送
[query uid1 server1 uid2 server2 ...] 查询竞技场简要信息
[watch 11/33 on/off] 打开或者关闭11或者33的推送
[private on/off] 启用或关闭私聊推送
server: 1 2 3 4(台一~台四)
============下面用不太到===========
[delete] 删除竞技场排名变动推送绑定
[delete id1 server1 id2 server2 ...] 删除指定竞技场排名变动推送绑定
[querystatus] 查看排名变动推送绑定状态

如果需要邀请机器人到其他频道请私 lostkevin#2185'''
    await ctx.send(_sv_help)


@bot.command(name='bind')
async def on_arena_bind(ctx, pcr_id: str, server: str):
    """
        ctx: discord context
        pcr_id : 
    """
    if server not in _clients:
        return await ctx.send("不支持查询该服务器")
    uid = str(ctx.author.id)
    try:
        await query(pcr_id, _clients[server])
    except:
        return await ctx.send("未查询到九码,绑定失败!")
    async with lck:
        last = _binds[uid] if uid in _binds else None
        if last is None:
            next_data = [(server, pcr_id)]
        elif (server, pcr_id) in last['data']:
            return await ctx.send('该九码已经绑定了')
        else:
            next_data = last['data'] + [(server, pcr_id)]
        _binds[uid] = {
            'uid': uid,
            'gid': ctx.channel.id,
            '11': last is None or last['11'],
            '33': last is None or last['33'],
            'data': next_data,
            'is_private': last is not None and last['is_private']
        }
        save_binds()
    await ctx.send('竞技场绑定成功')


@bot.command(name='query')
async def on_query_arena(ctx, *args):
    uid = str(ctx.author.id)
    async with lck:
        if len(args) == 0:
            if uid not in _binds:
                return await ctx.send('您还未绑定竞技场')
            else:
                data = _binds[uid]['data']
        else:
            assert len(args) % 2 == 0
            data = [(args[2 * i + 1], args[2 * i])
                    for i in range(len(args) // 2)]

        for (server, pcr_id) in data:
            if server not in _clients:
                continue
            try:
                res = await query(pcr_id, _clients[server])
                await ctx.send(f'''{res['user_name']} 台{server}:\n竞技场排名：{res["arena_rank"]}\n公主竞技场排名：{res["grand_arena_rank"]}''')
            except ApiException as e:
                await ctx.send(f'查询出错，{e}')


@bot.command(name='delete')
async def delete_arena_sub(ctx, *args):
    uid = str(ctx.author.id)
    if uid not in _binds:
        return await ctx.send('您还未绑定竞技场')
    if len(args) == 0:
        async with lck:
            _binds.pop(uid)
            save_binds()
        return await ctx.send('删除竞技场订阅成功')
    if len(args) % 2 != 0:
        return await ctx.send('格式输入错误,请参考帮助')
    data = [(args[2 * i + 1], args[2 * i])
            for i in range(len(args) // 2)]
    async with lck:
        for t in data:
            if list(t) not in _binds[uid]['data']:
                continue
            _binds[uid]['data'].remove(list(t))
        save_binds()
    return await ctx.send('删除竞技场订阅成功')


@bot.command(name='querystatus')
async def send_arena_sub_status(ctx):
    uid = str(ctx.author.id)
    if uid not in _binds:
        await ctx.send('您还未绑定竞技场')
    else:
        info = _binds[uid]
        await ctx.send(f'''
    当前竞技场绑定ID：{info['data']}
竞技场订阅：{'开启' if info['11'] else '关闭'}
公主竞技场订阅：{'开启' if info['33'] else '关闭'}
推送渠道: {'私聊' if info['is_private'] else '频道'}''')


@tasks.loop(seconds=80)
async def on_arena_schedule():
    bind_cache = {}
    async with lck:
        bind_cache = deepcopy(_binds)

    for user in bind_cache:
        info = bind_cache[user]
        for (server, pcr_id) in info['data']:
            try:
                res = await query(pcr_id, _clients[server])
                name = res['user_name']
                res = (res['arena_rank'], res['grand_arena_rank'])

                if user not in _cache or pcr_id not in _cache[user]:
                    if user not in _cache:
                        _cache[user] = {}
                    _cache[user][pcr_id] = res
                    continue

                last = _cache[user][pcr_id]
                _cache[user][pcr_id] = res
                destination = {'user_id': info['uid']} if info['is_private'] else {
                    'channel_id': info['gid']}
                if res[0] > last[0] and info['11']:
                    await send_msg(
                        **destination,
                        message=f'{name}的竞技场排名发生变化：{last[0]}->{res[0]}，降低了{res[0]-last[0]}名。'
                                + ('' if info['is_private']
                                   else at_person(user_id=user))
                    )

                if res[1] > last[1] and info['33']:
                    await send_msg(
                        **destination,
                        message=f'{name}的公主竞技场排名发生变化：{last[1]}->{res[1]}，降低了{res[1]-last[1]}名。' +
                        ('' if info['is_private'] else at_person(user_id=user))
                    )
            except:
                print(f'对{pcr_id}的检查出错\n{format_exc()}')

on_arena_schedule.start()


@bot.command('watch')
async def change_arena_sub(ctx, arena_type, state, *args):
    if state not in ['on', 'off'] or arena_type not in ['11', '33']:
        return await ctx.send('参数错误')
    uid = str(ctx.author.id)
    async with lck:
        if uid not in _binds:
            await ctx.send('您还未绑定竞技场')
        else:
            _binds[uid][arena_type] = state == 'on'
            save_binds()
            await ctx.send(f'{arena_type} {state}')


@bot.command('private')
async def on_change_annonce(ctx, state):
    uid = str(ctx.author.id)
    async with lck:
        if uid not in _binds:
            await ctx.send('您还未绑定竞技场')
        else:
            _binds[uid]['is_private'] = state == 'on'
            save_binds()
            await ctx.send('send through {}'.format('private' if state == 'on' else 'channel'))
    pass


def save_binds():
    with open(_config['binds_file'], 'w') as f:
        json.dump(_binds, f, indent=4)
