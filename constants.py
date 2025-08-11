# constants.py をこの内容に置き換えてください

import sys

IS_WINDOWS = sys.platform == "win32"
FONT_FAMILY = "Meiryo UI" if IS_WINDOWS else "sans-serif"

# --- ゲーム内固定データ ---
RAW_ECHO_STATS_DATA = {
    "main_stats": {
        "4": [{"name":"HP%","value":33.0,"key":"hp_percent"},{"name":"攻撃力%","value":33.0,"key":"atk_percent"},{"name":"防御力%","value":41.5,"key":"def_percent"},{"name":"クリティカル率","value":22.0,"key":"crit_rate"},{"name":"クリティカルダメージ","value":44.0,"key":"crit_damage"},{"name":"治療効果アップ","value":26.4,"key":"heal_bonus"}],
        "3": [{"name":"気動ダメージアップ","value":30.0,"key":"aero_dmg_up"},{"name":"焦熱ダメージアップ","value":30.0,"key":"fusion_dmg_up"},{"name":"電導ダメージアップ","value":30.0,"key":"electro_dmg_up"},{"name":"凝縮ダメージアップ","value":30.0,"key":"glacio_dmg_up"},{"name":"消滅ダメージアップ","value":30.0,"key":"havoc_dmg_up"},{"name":"回折ダメージアップ", "value":30.0, "key":"spectro_dmg_up"},{"name":"共鳴効率","value":32.0,"key":"resonance_efficiency"},{"name":"攻撃力%","value":30.0,"key":"atk_percent"},{"name":"HP%","value":30.0,"key":"hp_percent"},{"name":"防御力%","value":38.0,"key":"def_percent"}],
        "1": [{"name":"HP%","value":22.8,"key":"hp_percent"},{"name":"攻撃力%","value":18.0,"key":"atk_percent"},{"name":"防御力%","value":18.0,"key":"def_percent"}]
    },
    "fixed_main_stats": {
        "4":{"name":"攻撃力(数値)","value":150,"key":"atk_flat"},
        "3":{"name":"攻撃力(数値)","value":100,"key":"atk_flat"},
        "1":{"name":"HP(数値)","value":1520,"key":"hp_flat"}
    },
    "sub_stat_values": {
        "HP%":{"key":"hp_percent","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]},
        "攻撃力%":{"key":"atk_percent","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]},
        "防御力%":{"key":"def_percent","values":[8.1,9.0,10.0,10.9,11.8,12.8,13.6,14.7]},
        "クリティカル率":{"key":"crit_rate","values":[6.3,6.9,7.5,8.1,8.7,9.3,9.9,10.5]},
        "クリティカルダメージ":{"key":"crit_damage","values":[12.6,13.8,15.0,16.2,17.4,18.6,19.8,21.0]},
        "HP(数値)":{"key":"hp_flat","values":[320,360,390,430,470,510,540,580]},
        "攻撃力(数値)":{"key":"atk_flat","values":[30,30,40,40,50,50,60,60]},
        "防御力(数値)":{"key":"def_flat","values":[40,40,50,50,60,60,70,70]},
        "共鳴効率":{"key":"resonance_efficiency","values":[6.8,7.6,8.4,9.2,10.0,10.8,11.6,12.4]},
        "通常攻撃ダメージアップ":{"key":"normal_attack_dmg_up","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]},
        "重撃ダメージアップ":{"key":"heavy_attack_dmg_up","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]},
        "共鳴スキルダメージアップ":{"key":"resonance_skill_dmg_up","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]},
        "共鳴解放ダメージアップ":{"key":"resonance_liberation_dmg_up","values":[6.4,7.1,7.9,8.6,9.4,10.1,10.9,11.6]}
    }
}
ECHO_DATA = RAW_ECHO_STATS_DATA
ECHO_SUB_STAT_TYPES = list(ECHO_DATA["sub_stat_values"].keys())

# --- UI選択肢用定数 ---
ATTRIBUTES = ["", "気動", "焦熱", "電導", "凝縮", "消滅", "回折"]
WEAPON_TYPES = ["", "迅刀", "長刃", "増幅器", "手甲", "拳銃"]
SKILL_CATEGORIES = ["", "基本攻撃手段", "共鳴スキル", "共鳴回路", "共鳴解放", "変奏スキル", "終奏スキル", "その他"]
ACTIVATION_TYPES = ["通常攻撃", "重撃", "共鳴スキル", "共鳴解放", "変奏スキル", "終奏スキル", "音骸スキル"]
BUFF_EFFECT_TYPES = ["単純加算", "スタック形式", "ステータス変換", "ダメージ倍率アップ", "共鳴エネルギー獲得(固定)", "共鳴エネルギー獲得(変動)"]
BUFF_TIMINGS = ["発動時", "命中時"]
BUFF_TRIGGERS = [
    "常時", 
    "通常攻撃", 
    "重撃",
    "共鳴スキル",
    "共鳴解放",
    "変奏スキル",
    "終奏スキル",
    "音骸スキル",
    "回復効果"
]
TRIGGER_SOURCES = ["自身発動", "チーム内キャラ発動"]
BUFF_TARGETS = ["自身", "チーム全員", "チーム内キャラクター1人"] 
CONSTELLATION_LEVELS = [0, 1, 2, 3, 4, 5, 6]

# --- 異常効果定義 ---
ABNORMAL_DAMAGE_BASE_LV90 = 1103
ABNORMAL_EFFECTS = {
    "騒光効果": {"attr_coeff": 1.0, "type": "stacking_dot", "max_stacks": 60},
    "風蝕効果": {"attr_coeff": 1.5, "type": "stacking_dot", "max_stacks": 9},
    "斉爆効果": {"attr_coeff": 19.0, "type": "detonation"},
    "虚滅効果": {"attr_coeff": 10.0, "type": "detonation"},
}
ABNORMAL_STACK_MULTIPLIERS = {
    "騒光効果": [1, 1.811, 2.624, 3.436, 4.249, 5.06, 5.873, 6.685, 7.496, 8.309],
    "風蝕効果": [1, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20],
    "斉爆効果": [1], "虚滅効果": [1]
}

# --- ステータスキー定義 ---
ATTRIBUTE_NAME_TO_RES_KEY = {"気動": "aero", "焦熱": "fusion", "電導": "electro", "凝縮": "glacio", "消滅": "havoc", "回折": "spectro"}

# --- ▼▼▼ ここから修正 ▼▼▼ ---
ADDITIONAL_STATS = {
    "ダメージ倍率アップ": "skill_multiplier_bonus",
    "変奏スキルダメージアップ": "intro_skill_dmg_up",
    "終奏スキルダメージアップ": "outro_skill_dmg_up",
    "全属性ダメージアップ": "all_damage_up", "通常攻撃ダメージアップ": "normal_attack_dmg_up", "重撃ダメージアップ": "heavy_attack_dmg_up",
    "共鳴スキルダメージアップ": "resonance_skill_dmg_up", "共鳴解放ダメージアップ": "resonance_liberation_dmg_up",
    "音骸スキルダメージアップ": "echo_skill_dmg_up", # 追加
    "協同攻撃ダメージアップ": "synergy_attack_dmg_up", # 追加
    "騒光効果ダメージアップ": "spectro_effect_dmg_up", "風蝕効果ダメージアップ": "aero_effect_dmg_up", 
    "斉爆効果ダメージアップ": "fusion_effect_dmg_up", "虚滅効果ダメージアップ": "havoc_effect_dmg_up", 
    "ダメージブースト": "generic_dmg_boost",
    "通常攻撃ダメージブースト": "normal_attack_dmg_boost", "重撃ダメージブースト": "heavy_attack_dmg_boost",
    "共鳴スキルダメージブースト": "resonance_skill_dmg_boost", "共鳴解放ダメージブースト": "resonance_liberation_dmg_boost",
    "変奏スキルダメージブースト": "intro_skill_dmg_boost", "終奏スキルダメージブースト": "outro_skill_dmg_boost", 
    "音骸スキルダメージブースト": "echo_skill_dmg_boost", # 追加
    "協同攻撃ダメージブースト": "synergy_attack_dmg_boost", # 追加
    "気動ダメージブースト": "aero_dmg_boost",
    "焦熱ダメージブースト": "fusion_dmg_boost", "電導ダメージブースト": "electro_dmg_boost", "凝縮ダメージブースト": "glacio_dmg_boost",
    "消滅ダメージブースト": "havoc_dmg_boost", "回折ダメージブースト": "spectro_dmg_boost", "騒光効果ダメージブースト": "spectro_effect_dmg_boost",
    "風蝕効果ダメージブースト": "aero_effect_dmg_boost", "斉爆効果ダメージブースト": "fusion_effect_dmg_up", "虚滅効果ダメージブースト": "havoc_effect_dmg_boost",
    "防御無視": "def_shred", "耐性ダウン": "res_shred", "被ダメージアップ": "dmg_taken_up",
    "気動耐性ダウン": "aero_res_shred", "焦熱耐性ダウン": "fusion_res_shred",
    "電導耐性ダウン": "electro_res_shred", "凝縮耐性ダウン": "glacio_res_shred", "消滅耐性ダウン": "havoc_res_shred", "回折耐性ダウン": "spectro_res_shred",
    "気動耐性無視": "aero_res_ignore", "焦熱耐性無視": "fusion_res_ignore", "電導耐性無視": "electro_res_ignore",
    "凝縮耐性無視": "glacio_res_ignore", "消滅耐性無視": "havoc_res_ignore", "回折耐性無視": "spectro_res_ignore",
    "基礎HP": "base_hp", "基礎攻撃力": "base_atk", "基礎防御力": "base_def", "治療効果アップ": "heal_bonus", "必要共鳴エネルギー": "resonance_energy_required",
}

def _build_stat_lookups():
    name_to_key, key_to_name = {}, {}
    for attr, key_prefix in ATTRIBUTE_NAME_TO_RES_KEY.items():
        name_to_key[f"{attr}ダメージアップ"] = f"{key_prefix}_dmg_up"
        key_to_name[f"{key_prefix}_dmg_up"] = f"{attr}ダメージアップ"
    sources = [ECHO_DATA["sub_stat_values"].values()] + list(ECHO_DATA["main_stats"].values()) + [ECHO_DATA["fixed_main_stats"].values()]
    for source in sources:
        for item in source:
            name, key = item.get("name"), item.get("key")
            if name and key and name not in name_to_key:
                name_to_key[name] = key
                key_to_name[key] = name
    for name, key in ADDITIONAL_STATS.items():
        if name not in name_to_key:
            name_to_key[name] = key
            key_to_name[key] = name
    return name_to_key, key_to_name

STAT_NAME_TO_KEY, STAT_KEY_TO_NAME = _build_stat_lookups()
ALL_STAT_TYPES = sorted(list(STAT_NAME_TO_KEY.keys()))

STAT_CATEGORIES = {
    "基礎ステータス": ["HP%", "攻撃力%", "防御力%", "HP(数値)", "攻撃力(数値)", "防御力(数値)"],
    "クリティカル": ["クリティカル率", "クリティカルダメージ"],
    
    "与ダメージアップ": [
        "全属性ダメージアップ",
        "気動ダメージアップ",
        "焦熱ダメージアップ",
        "電導ダメージアップ",
        "凝縮ダメージアップ",
        "消滅ダメージアップ",
        "回折ダメージアップ",
        "通常攻撃ダメージアップ",
        "重撃ダメージアップ",
        "共鳴スキルダメージアップ",
        "共鳴解放ダメージアップ",
        "変奏スキルダメージアップ",
        "終奏スキルダメージアップ",
        "音骸スキルダメージアップ",   # 追加
        "協同攻撃ダメージアップ",   # 追加
        "風蝕効果ダメージアップ",
        "斉爆効果ダメージアップ",
        "虚滅効果ダメージアップ",
        "騒光効果ダメージアップ",
    ],
    "ダメージブースト": [
        "ダメージブースト",
        "気動ダメージブースト",
        "焦熱ダメージブースト",
        "電導ダメージブースト",
        "凝縮ダメージブースト",
        "消滅ダメージブースト",
        "回折ダメージブースト",
        "通常攻撃ダメージブースト",
        "重撃ダメージブースト",
        "共鳴スキルダメージブースト",
        "共鳴解放ダメージブースト",
        "変奏スキルダメージブースト",
        "終奏スキルダメージブースト",
        "音骸スキルダメージブースト", # 追加
        "協同攻撃ダメージブースト", # 追加
        "風蝕効果ダメージブースト",
        "斉爆効果ダメージブースト",
        "虚滅効果ダメージブースト",
        "騒光効果ダメージブースト",
    ],
    "デバフ・耐性関連": sorted([name for name in ALL_STAT_TYPES if any(s in name for s in ["耐性", "無視", "ダウン", "防御無視", "被ダメージアップ"])]),
    "その他": ["共鳴効率", "治療効果アップ", "ダメージ倍率アップ"]
}

DAMAGE_TYPES = [
    "通常攻撃", "重撃", "共鳴スキル", "共鳴解放", "変奏スキル", "終奏スキル",
    "音骸スキルダメージ", "協同攻撃ダメージ", # 追加
    "気動ダメージ", "焦熱ダメージ", "電導ダメージ", "凝縮ダメージ", "消滅ダメージ", "回折ダメージ", 
    "騒光効果ダメージ", "風蝕効果ダメージ", "斉爆効果ダメージ", "虚滅効果ダメージ", "その他ダメージ"
]
DAMAGE_TYPE_TO_KEY_MAP = {
    "通常攻撃": "normal_attack_dmg_up", "重撃": "heavy_attack_dmg_up", 
    "共鳴スキル": "resonance_skill_dmg_up", "共鳴解放": "resonance_liberation_dmg_up", 
    "変奏スキル": "intro_skill_dmg_up", "終奏スキル": "outro_skill_dmg_up",
    "音骸スキルダメージ": "echo_skill_dmg_up", # 追加
    "協同攻撃ダメージ": "synergy_attack_dmg_up"  # 追加
}
ATTRIBUTE_DMG_UP_MAP = {
    "気動ダメージ": "aero_dmg_up", "焦熱ダメージ": "fusion_dmg_up", "電導ダメージ": "electro_dmg_up", 
    "凝縮ダメージ": "glacio_dmg_up", "消滅ダメージ": "havoc_dmg_up", "回折ダメージ": "spectro_dmg_up", 
    "騒光効果ダメージ": "spectro_effect_dmg_up", "風蝕効果ダメージ": "aero_effect_dmg_up", 
    "斉爆効果ダメージ": "fusion_effect_dmg_up", "虚滅効果ダメージ": "havoc_effect_dmg_boost"
}
DAMAGE_TYPE_TO_BOOST_KEY_MAP = {
    "通常攻撃": ["normal_attack_dmg_boost"], "重撃": ["heavy_attack_dmg_boost"], 
    "共鳴スキル": ["resonance_skill_dmg_boost"], "共鳴解放": ["resonance_liberation_dmg_boost"], 
    "変奏スキル": ["intro_skill_dmg_boost"], "終奏スキル": ["outro_skill_dmg_boost"], 
    "音骸スキルダメージ": ["echo_skill_dmg_boost"], # 追加
    "協同攻撃ダメージ": ["synergy_attack_dmg_boost"], # 追加
    "気動ダメージ": ["aero_dmg_boost"], "焦熱ダメージ": ["fusion_dmg_boost"], 
    "電導ダメージ": ["electro_dmg_boost"], "凝縮ダメージ": ["glacio_dmg_boost"], 
    "消滅ダメージ": ["havoc_dmg_boost"], "回折ダメージ": ["spectro_dmg_boost"], 
    "騒光効果ダメージ": ["spectro_effect_dmg_boost"], "風蝕効果ダメージ": ["aero_effect_dmg_boost"], 
    "斉爆効果ダメージ": ["fusion_effect_dmg_up"], "虚滅効果ダメージ": ["havoc_effect_dmg_boost"]
}
# --- ▲▲▲ 修正ここまで ▲▲▲ ---

EFFECT_NAME_TO_ATTR_DMG_TYPE = {"騒光効果":"回折ダメージ", "風蝕効果":"気動ダメージ", "斉爆効果":"焦熱ダメージ", "虚滅効果":"消滅ダメージ"}
EFFECT_NAME_TO_BOOST_KEY = {"騒光効果":"spectro_effect_dmg_boost", "風蝕効果":"aero_effect_dmg_boost", "斉爆効果":"fusion_effect_dmg_boost", "虚滅効果":"havoc_effect_dmg_boost"}

# --- DICTIONARY KEYS ---
KEY_NAME = "name"; KEY_KEY = "key"; KEY_VALUE = "value"; KEY_COST = "cost"
KEY_MAIN_STAT = "main_stat"; KEY_SUB_STAT = "sub_stat"; KEY_SUB_STATS = "sub_stats"
KEY_CHARACTER = "character"; KEY_CHARACTER_NAME = "character_name"; KEY_CHARACTER_DATA = "character_data"
KEY_WEAPON_DATA = "weapon_data"; KEY_WEAPON_NAME = "weapon_name"; KEY_WEAPON_RANK = "weapon_rank"; KEY_WEAPON_TYPE = "weapon_type"
KEY_ECHO_LIST = "echo_list"; KEY_HARMONY1_DATA = "harmony1_data"; KEY_HARMONY2_DATA = "harmony2_data"
KEY_HARMONY1_NAME = "harmony1_name"; KEY_HARMONY2_NAME = "harmony2_name"
KEY_ECHO_SKILL_NAME = "echo_skill_name"; KEY_ECHO_SKILL_DATA = "echo_skill_data"
KEY_INNATE_STATS = "innate_stats"; KEY_SKILLS = "skills"; KEY_SKILL = "skill"; KEY_SKILL_DATA = "skill_data"
KEY_SKILL_CATEGORY = "skill_category"; KEY_MULTIPLIER = "multiplier"; KEY_ATTRIBUTE = "attribute"
KEY_ACTIVATION_TYPES = "activation_types"; KEY_DAMAGE_TYPES = "damage_types"; KEY_CONCERTO_ENERGY = "concerto_energy"
KEY_RESONANCE_ENERGY_GAIN_FLAT = "resonance_energy_gain_flat"
KEY_RESONANCE_ENERGY_GAIN_SCALING = "resonance_energy_gain_scaling"
KEY_BUFFS = "buffs"; KEY_CONSTELLATION = "constellation"; KEY_CONSTELLATIONS = "constellations"
KEY_ACTIVE_BUFFS = "active_buffs"; KEY_STACKS = "stacks"; KEY_LEVEL = "level"
KEY_IMAGE_FILE = "image_file"; KEY_BASE_HP = "base_hp"; KEY_BASE_ATK = "base_atk"; KEY_BASE_DEF = "base_def"
KEY_EFFECT_DATA = "effect_data"; KEY_DESCRIPTION = "description"; KEY_TRIGGER = "trigger"; KEY_TARGET = "target"
KEY_EFFECTS = "effects"; KEY_IS_DEFAULT = "is_default"
KEY_RESONANCE_ENERGY_REQUIRED = "resonance_energy_required"

THEME = {
    "ImprovedContrast": {
        "bg_base": "#1E1E1E", "bg_sub": "#2D2D2D", "bg_sidebar": "#252526",
        "bg_hover": "#3E3E3E", "accent_fg": "#007ACC", "accent_hover": "#0097FB",
        "accent_text": "#9CDCFE", "text_main": "#FFFFFF", "text_sub": "#A0A0A0",
        "border": "#555555", "graph_bg": "#252526", "graph_face": "#2D2D2D",
        "graph_text": "#FFFFFF", "graph_line1": "#0097FB", "graph_line2": "#FFC66D",
    }
}

GRAPH_LABELS = {
    "total_damage_and_dps": "Total Damage & DPS", "total_damage": "Total Damage",
    "time_seconds": "Time (s)", "dps": "DPS", "damage_distribution_by_char": "Damage Distribution by Character",
    "no_damage_data": "No Damage Data", "damage_distribution_by_skill": "Damage Distribution by Skill Type",
    "clear_time_by_hp": "Estimated Clear Time by Enemy HP", "enemy_hp_millions": "Enemy HP (Millions)",
    "clear_time_seconds": "Clear Time (s)"
}

# --- DICTIONARY KEYS (続き) ---
KEY_RARITY = "rarity"
KEY_CATEGORY = "category"
KEY_YOMIGANA = "yomigana"

# --- データ管理用カテゴリ ---
RARITY_LEVELS = ["", "★5", "★4", "★3"]
ECHO_SKILL_CATEGORIES = ["", "コスト4", "コスト3", "コスト1"]
HARMONY_CATEGORIES = ["", "気動", "焦熱", "電導", "凝縮", "消滅", "回折", "サポート", "その他"]
STAGE_CATEGORIES = ["", "逆境深塔", "廃墟", "その他"]