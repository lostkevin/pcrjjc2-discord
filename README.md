# pcrjjc2 for Discord
本repo是[pcrjjc2](https://github.com/cc004/pcrjjc2)的discord机器人.

支持绑定一个用户绑定多个PCR账号以及击剑自动提醒.

**本项目基于AGPL v3协议开源，由于项目特殊性，禁止基于本项目的任何商业行为**

## 用法说明
1. 首先获得一个discord API的token
2. 复制一份 /data/data/tw.sonet.princessconnect/sharedprefs/tw.sonet.princessconnect.v2.playerprefs.xml   **一般需要root**
    + 切换账号会导致xml失效, 取出playerpref后,删除再引继:
        1. /data/data/tw.sonet.princessconnect/sharedprefs/tw.sonet.princessconnect.v2.playerprefs.xml
        2. /data/data/tw.sonet.princessconnect/files/savedData 文件夹
3. 在项目根目录下新建config.json,内容如下:
```
{
    "token": "", //DISCORD API TOKEN
    "proxy": null, //如果需要代理,请参考原repo
    "playerprefs": {
        "1": "台1 playerpref.xml的路径, 台2\3\4同理"
    },
    "binds_file": "binds.json" //用于存储用户绑定状态
    "max_enemy": -1 //如果非负,表示黑名单UID最大数量(0为不启用)
}
```
binds.json的格式说明:
```
{
   "uid1": {
        "uid": str,  # discord user id, 与key相同
        "gid": int,  # discord 频道ID, 每个用户仅支持在一个群组中推送消息
        "11": bool,  # 是否推送11排名下降
        "33": bool,  # 是否推送33排名下降,
        "data": List[str, str]  # (服务器, 九码)
        "enemy": List[str]  # 黑名单UID
        "is_private": bool  # 私聊推送开关
    }
}
```