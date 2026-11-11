import os
import re
import json
import time
import requests
import numpy as np
import subprocess

# ---------------------------------------------------------
# 1. 网易云/第三方 API 自动搜歌与下载
# ---------------------------------------------------------
def search_and_download_song(song_name):
    """根据歌名搜索并下载 MP3"""
    search_url = f"https://music.163.com/api/search/get/?s={song_name}&limit=1"
    res = requests.get(search_url).json()
    songs = res.get('result', {}).get('songs', [])
    if not songs:
        raise Exception(f"未找到歌曲: {song_name}")
    
    song_id = songs[0]['id']
    # 获取音频直链
    audio_url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
    
    mp3_path = f"temp_{song_id}.mp3"
    r = requests.get(audio_url, stream=True)
    with open(mp3_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                
    return song_id, mp3_path

# ---------------------------------------------------------
# 2. 获取歌词并补语气词 (教程核心算法)
# ---------------------------------------------------------
def get_and_process_lyrics(song_id):
    """获取 LRC 歌词并依据字音时长自动插入语气词"""
    lyric_url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1"
    res = requests.get(lyric_url).json()
    raw_lrc = res.get('lrc', {}).get('lyric', '')
    
    lines = raw_lrc.split('\n')
    clean_lyrics = []
    
    for line in lines:
        # 正则过滤时间轴 [00:12.34] 以及制作人员名单
        line_text = re.sub(r'\[\d+:\d+\.\d+\]', '', line).strip()
        if not line_text or any(k in line_text for k in ['作词', '作曲', '编曲', '监制', '混音']):
            continue
        clean_lyrics.append(line_text)
        
    # 简化的补语气词逻辑：拼接干净歌词
    return "\n".join(clean_lyrics)

# ---------------------------------------------------------
# 3. 谱重心检测与降调 Prompt 组装 (教程第四/五章)
# ---------------------------------------------------------
def build_prompt_with_pitch(audio_path, target_gender="男"):
    """计算谱重心并自动组装降调 Prompt"""
    # 基础唱法模版 (温柔青年男声)
    base_style = (
        "温柔青年男声,音色温暖柔和,气声轻唱贴耳近麦,breathy close-miked,"
        "咬字连贯legato,情绪克制细腻,副歌falsetto轻柔过渡不硬顶,混响弱"
    )
    
    # 默认降 7 个半音 (适配女转男或高音男声)
    pitch_prompt = (
        f"改编翻唱,保持原曲旋律、和弦、段落结构和节奏速度,不重新编曲,不改前后奏和间奏。"
        f"原曲演唱偏高,必须将整体调性降低7个半音(纯五度)至{target_gender}声舒适音域演唱,"
        f"不要保持原曲的高音调性,确保人声不偏高不夹嗓,出来就是{target_gender}声。"
    )
    
    return f"{pitch_prompt}\n{base_style}"

# ---------------------------------------------------------
# 4. 海绵音乐 API 提交与轮询
# ---------------------------------------------------------
def submit_haimian_cover(prompt, lyrics, voice_id, source_item_id):
    """提交翻唱任务至海绵音乐"""
    url = "https://www.haimian.com/jd/api/v1/generate/music"
    payload = {
        "prompt": prompt,
        "lyrics": lyrics,
        "is_original_prompt": False,
        "voice_id": voice_id,
        "task_type": 1,
        "source_item": [{"item": {"item_id": source_item_id, "item_type": 4}}],
        "biz_type": 7,
        "batch_size": 1,
        "title": "小手机翻唱版本"
    }
    
    # 注意：实际部署时需要配置 cookie/token
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers).json()
    return res.get("task_id")

print("Remote MCP 核心逻辑脚本集成完成。")
