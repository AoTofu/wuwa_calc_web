# calculator.py
import copy
import traceback
from collections import defaultdict
import random
import numpy as np
from constants import (
    ECHO_DATA, DAMAGE_TYPE_TO_KEY_MAP, DAMAGE_TYPE_TO_BOOST_KEY_MAP, ATTRIBUTE_DMG_UP_MAP, ATTRIBUTE_NAME_TO_RES_KEY,
    ABNORMAL_DAMAGE_BASE_LV90, ABNORMAL_EFFECTS, ABNORMAL_STACK_MULTIPLIERS, EFFECT_NAME_TO_ATTR_DMG_TYPE, EFFECT_NAME_TO_BOOST_KEY,
    KEY_NAME, KEY_KEY, KEY_VALUE, KEY_COST, KEY_MAIN_STAT, KEY_SUB_STAT, KEY_SUB_STATS,
    KEY_CHARACTER, KEY_CHARACTER_NAME, KEY_CHARACTER_DATA, KEY_WEAPON_DATA, KEY_WEAPON_NAME, KEY_WEAPON_RANK,
    KEY_ECHO_LIST, KEY_HARMONY1_DATA, KEY_HARMONY2_DATA, KEY_INNATE_STATS, KEY_SKILLS, KEY_SKILL, KEY_SKILL_DATA,
    KEY_MULTIPLIER, KEY_ATTRIBUTE, KEY_ACTIVATION_TYPES, KEY_DAMAGE_TYPES, KEY_CONCERTO_ENERGY,
    KEY_BUFFS, KEY_CONSTELLATION, KEY_CONSTELLATIONS, KEY_ACTIVE_BUFFS, KEY_STACKS, KEY_LEVEL,
    KEY_BASE_HP, KEY_BASE_ATK, KEY_BASE_DEF, KEY_EFFECTS, KEY_TARGET, KEY_RESONANCE_ENERGY_REQUIRED, KEY_RESONANCE_ENERGY_GAIN_FLAT,
    KEY_RESONANCE_ENERGY_GAIN_SCALING
)
from app_types import Build, BuffEffect, Action, CalculationResult, RotationPhaseResult, ActiveBuffTarget
from itertools import combinations, product, permutations
from typing import Dict, List, Tuple, Set, Optional

def _apply_stat_conversion(stats: Dict[str, float], effect: BuffEffect, rank: int) -> Dict[str, float]:
    source_val = stats.get(effect.get("source_stat"), 0)
    threshold = effect.get("threshold", 0)
    if source_val <= threshold: return stats
    per_unit = effect.get("conversion_per_unit", 1)
    if per_unit == 0: return stats
    gains = effect.get("conversion_gain_unit", [0]*5)
    gain_unit = gains[rank-1] if isinstance(gains, list) else gains
    max_gains = effect.get("max_gain", [float('inf')]*5)
    max_gain = max_gains[rank-1] if isinstance(max_gains, list) else max_gains
    bonus = ((source_val - threshold) / per_unit) * gain_unit
    stats[effect["dest_stat"]] += min(bonus, max_gain)
    return stats

def _apply_harmony_effects(raw_stats: Dict[str, float], h1_data: Dict, h2_data: Dict):
    if not h1_data or not h1_data.get(KEY_NAME): return # ハーモニー1がなければ何もしない
    
    h1_buffs = h1_data.get(KEY_BUFFS, {})
    h2_buffs = h2_data.get(KEY_BUFFS, {}) if h2_data else {}
    h1_name = h1_data.get(KEY_NAME)
    h2_name = h2_data.get(KEY_NAME) if h2_data else None

    def _apply_single_set_effect(harmony_data_obj, set_key_to_apply, has_flag_key):
        """特定のセット効果（例: "2セット効果"）を適用するヘルパー"""
        # --- ▼▼▼ ここから修正 ▼▼▼ ---
        # フラグがTrueの場合にのみ、セット効果を検索・適用
        if harmony_data_obj.get(has_flag_key, False):
            set_data = harmony_data_obj.get(KEY_BUFFS, {}).get(set_key_to_apply)
            if isinstance(set_data, dict) and KEY_BUFFS in set_data:
                for buff_data in set_data.get(KEY_BUFFS, {}).values():
                    for effect in buff_data.get(KEY_EFFECTS, []):
                        if "stat_to_buff" in effect:
                            raw_stats[effect["stat_to_buff"]] += effect.get(KEY_VALUE, 0)

    # ハーモニー1とハーモニー2が同じ名前の場合
    if h1_name and h2_name and h1_name == h2_name:
        _apply_single_set_effect(h1_data, "2セット効果", "has_2set_effect")
        _apply_single_set_effect(h1_data, "3セット効果", "has_3set_effect")
        _apply_single_set_effect(h1_data, "5セット効果", "has_5set_effect")
    else:
        # 異なるハーモニーを2つ装備している場合、または1つしか装備していない場合
        _apply_single_set_effect(h1_data, "2セット効果", "has_2set_effect")
        _apply_single_set_effect(h1_data, "3セット効果", "has_3set_effect")

        if h2_buffs and h2_name:
            _apply_single_set_effect(h2_data, "2セット効果", "has_2set_effect")
            _apply_single_set_effect(h2_data, "3セット効果", "has_3set_effect")
    # --- ▲▲▲ 修正ここまで ▲▲▲ ---

def calculate_base_stats(build: Build) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    char, weapon, echoes = build.get(KEY_CHARACTER_DATA,{}), build.get(KEY_WEAPON_DATA,{}), build.get(KEY_ECHO_LIST,[])
    raw = defaultdict(float, {"crit_rate":5.0, "crit_damage":150.0, "resonance_efficiency":100.0})
    for stat in char.get(KEY_INNATE_STATS, []): raw[stat[KEY_KEY]] += stat[KEY_VALUE]
    for echo in echoes:
        if not echo or not echo.get(KEY_COST): continue
        cost = str(echo[KEY_COST])
        if echo.get(KEY_MAIN_STAT): raw[echo[KEY_MAIN_STAT][KEY_KEY]] += echo[KEY_MAIN_STAT][KEY_VALUE]
        if cost in ECHO_DATA["fixed_main_stats"]:
            fixed_stat = ECHO_DATA["fixed_main_stats"][cost]; raw[fixed_stat[KEY_KEY]] += fixed_stat[KEY_VALUE]
        for sub in echo.get(KEY_SUB_STATS, []): raw[sub[KEY_KEY]] += sub[KEY_VALUE]
    _apply_harmony_effects(raw, build.get(KEY_HARMONY1_DATA,{}), build.get(KEY_HARMONY2_DATA,{}))
    if weapon and KEY_SUB_STAT in weapon and weapon[KEY_SUB_STAT] and KEY_KEY in weapon[KEY_SUB_STAT]: 
        raw[weapon[KEY_SUB_STAT][KEY_KEY]] += weapon[KEY_SUB_STAT].get(KEY_VALUE, 0)
    base_hp, base_atk, base_def = char.get(KEY_BASE_HP,0), char.get(KEY_BASE_ATK,0) + weapon.get(KEY_BASE_ATK,0), char.get(KEY_BASE_DEF,0)
    bases = {"hp": base_hp, "atk": base_atk, "def": base_def}
    final_display = {"HP": bases["hp"] * (1 + raw["hp_percent"] / 100) + raw["hp_flat"], "攻撃力": bases["atk"] * (1 + raw["atk_percent"] / 100) + raw["atk_flat"], "防御力": bases["def"] * (1 + raw["def_percent"] / 100) + raw["def_flat"], "クリティカル率": raw["crit_rate"], "クリティカルダメージ": raw["crit_damage"], "共鳴効率": raw["resonance_efficiency"],"全属性ダメージアップ": raw["all_damage_up"], "気動ダメージアップ": raw["aero_dmg_up"],"焦熱ダメージアップ": raw["fusion_dmg_up"],"電導ダメージアップ": raw["electro_dmg_up"],"凝縮ダメージアップ": raw["glacio_dmg_up"],"消滅ダメージアップ": raw["havoc_dmg_up"],"回折ダメージアップ": raw["spectro_dmg_up"]}
    return final_display, dict(raw), bases

def apply_buffs(raw_stats: Dict[str, float], active_buffs: Dict[str, any], current_char_name: str, all_buff_data: Dict, constellation: int, weapon_rank: int, ignored_buff_key: Optional[str] = None) -> Dict[str, float]:
    buffed = defaultdict(float, raw_stats)
    for buff_key, buff_status in active_buffs.items():
        if buff_key == ignored_buff_key: continue
        info = all_buff_data.get(buff_key)
        if not info or info.get(KEY_CONSTELLATION, 0) > constellation or info.get("is_transient", False):
            continue
        target_type = info.get(KEY_TARGET, "自身")
        owner = info.get("owner")
        is_applicable = False
        if target_type == "自身" and owner == current_char_name: is_applicable = True
        elif target_type == "チーム全員": is_applicable = True
        elif target_type == "チーム内キャラクター1人":
            if isinstance(buff_status, dict) and buff_status.get("target_char") == current_char_name: is_applicable = True
        if not is_applicable: continue
        for effect in info.get(KEY_EFFECTS,[]):
            value = effect.get(KEY_VALUE, [0]*5)
            value = value[weapon_rank-1] if isinstance(value, list) else value
            if effect.get("type") == "単純加算": buffed[effect["stat_to_buff"]] += value
            elif effect.get("type") == "スタック形式":
                per_stack = effect.get("effect_per_stack", [0]*5)
                value_per_stack = per_stack[weapon_rank-1] if isinstance(per_stack, list) else per_stack
                stack_count = buff_status if isinstance(buff_status, int) else 1
                buffed[effect["stat_to_buff"]] += value_per_stack * stack_count
            elif effect.get("type") == "ステータス変換": buffed = _apply_stat_conversion(buffed, effect, weapon_rank)
            elif effect.get("type") == "ダメージ倍率アップ": buffed[effect["stat_to_buff"]] += value
    return buffed

def _get_default_target(current_char_name: str, team_builds: List[Build]) -> str:
    """単体対象バフのデフォルトターゲット（通常は次のキャラクター）を返す"""
    team_members = [b[KEY_CHARACTER_NAME] for b in team_builds if b.get(KEY_CHARACTER_NAME)]
    if not team_members: return ""
    if len(team_members) <= 1:
        return current_char_name if current_char_name else team_members[0]
    try:
        current_index = team_members.index(current_char_name)
        next_index = (current_index + 1) % len(team_members)
        return team_members[next_index]
    except ValueError:
        return team_members[0]

def _get_character_efficiency(character_name: str, base_raw: Dict, active_buffs: Dict, all_buffs: Dict, build: Build) -> float:
    """
    指定されたキャラクターの、特定のバフ状態における共鳴効率を計算して返す。
    この関数は calculator 内で完結するように引数を調整。
    """
    if not build:
        return 100.0

    # 与えられた時点のバフを適用
    buffed_raw_stats = apply_buffs(
        base_raw,
        active_buffs,
        character_name,
        all_buffs,
        build.get(KEY_CONSTELLATION, 0),
        build.get(KEY_WEAPON_RANK, 1)
    )
    
    return buffed_raw_stats.get("resonance_efficiency", 100.0)

def _calculate_shared_bonuses(buffed_raw_stats: Dict[str, float], enemy_info: Dict, damage_types: List[str]) -> Tuple[float, float, float]:
    char_lv, enemy_lv = 90, enemy_info.get(KEY_LEVEL, 90)
    def_ignore = buffed_raw_stats.get("def_shred", 0) / 100
    defense_bonus = (800 + 8 * char_lv) / (800 + 8 * char_lv + (8 * enemy_lv + 792) * (1 - def_ignore))
    enemy_res_name = next((dt.replace("ダメージ","") for dt in damage_types if dt.endswith("ダメージ")), None)
    enemy_res = enemy_info.get(enemy_res_name, 10)
    res_shred = buffed_raw_stats.get("res_shred", 0)
    if enemy_res_name and ATTRIBUTE_NAME_TO_RES_KEY.get(enemy_res_name):
        res_key_suffix = ATTRIBUTE_NAME_TO_RES_KEY.get(enemy_res_name)
        res_shred += buffed_raw_stats.get(f"{res_key_suffix}_res_shred", 0)
    res_ignore = buffed_raw_stats.get(f"{enemy_res_name}_res_ignore", 0) / 100 if enemy_res_name else 0
    final_res = enemy_res * (1 - res_ignore) - res_shred
    resistance_bonus = 1 - (final_res / 100) if final_res >= 0 else 1 - (final_res / 200)
    dmg_taken_bonus = 1 + buffed_raw_stats.get("dmg_taken_up", 0) / 100
    return defense_bonus, resistance_bonus, dmg_taken_bonus

def calculate_skill_damage(final_stats_with_buffs: Dict[str, float], buffed_raw_stats: Dict[str, float], skill: Dict, enemy_info: Dict, char_attribute: str = None, rng_mode: bool = False) -> Tuple[float, Dict]:
    details = {} if not rng_mode else None
    try:
        ref_map = {"atk": "攻撃力", "hp": "HP", "def": "防御力"}
        ref_stat_key = ref_map.get(skill.get(KEY_ATTRIBUTE, "atk"), "攻撃力")
        ref_stat_value = final_stats_with_buffs.get(ref_stat_key, 0)
        if details is not None: details["参照ステータス"] = f"{ref_stat_key}: {ref_stat_value:,.2f}"

        multiplier_bonus = buffed_raw_stats.get("skill_multiplier_bonus", 0)
        skill_multiplier = skill.get(KEY_MULTIPLIER, 0)
        final_multiplier = (skill_multiplier + multiplier_bonus) / 100
        if details is not None: details["スキル倍率"] = f"({skill_multiplier}% + {multiplier_bonus}%) = {final_multiplier * 100:.2f}%"

        base_damage = ref_stat_value * final_multiplier
        if details is not None: details["基礎ダメージ"] = f"{base_damage:,.2f}"

        damage_types = skill.get(KEY_DAMAGE_TYPES, [])
        if not any(dt.endswith("ダメージ") for dt in damage_types) and char_attribute:
            damage_types.append(f"{char_attribute}ダメージ")

        total_dmg_up = buffed_raw_stats.get("all_damage_up", 0)
        elemental_dmg_up = sum(buffed_raw_stats.get(ATTRIBUTE_DMG_UP_MAP.get(t), 0) for t in damage_types if t in ATTRIBUTE_DMG_UP_MAP)
        skill_type_dmg_up = sum(buffed_raw_stats.get(DAMAGE_TYPE_TO_KEY_MAP.get(t), 0) for t in skill.get(KEY_DAMAGE_TYPES, []))
        damage_up_bonus = 1 + (total_dmg_up + elemental_dmg_up + skill_type_dmg_up) / 100
        if details is not None: details["与ダメージバフ補正"] = f"1 + ({total_dmg_up:.1f}% + {elemental_dmg_up:.1f}% + {skill_type_dmg_up:.1f}%) = {damage_up_bonus:.3f}"

        total_dmg_boost = buffed_raw_stats.get("generic_dmg_boost", 0) + sum(buffed_raw_stats.get(key, 0) for t in damage_types for key in DAMAGE_TYPE_TO_BOOST_KEY_MAP.get(t, []))
        damage_boost_bonus = 1 + total_dmg_boost / 100
        if details is not None: details["ダメージブースト補正"] = f"1 + {total_dmg_boost:.1f}% = {damage_boost_bonus:.3f}"

        crit_rate = min(buffed_raw_stats.get("crit_rate", 5.0), 100.0)
        crit_damage_val = buffed_raw_stats.get("crit_damage", 150.0)
        
        if rng_mode:
            is_crit = random.random() < (crit_rate / 100.0)
            crit_bonus = 1 + (crit_damage_val / 100.0) if is_crit else 1.0
        else:
            crit_bonus = 1 + ((crit_rate / 100) * (crit_damage_val / 100))
            if details is not None: details["会心補正(期待値)"] = f"1 + ({crit_rate:.1f}% * {crit_damage_val:.1f}%) = {crit_bonus:.3f}"

        defense_bonus, resistance_bonus, dmg_taken_bonus = _calculate_shared_bonuses(buffed_raw_stats, enemy_info, damage_types)
        if details is not None:
            details["防御補正"] = f"{defense_bonus:.3f}"
            details["耐性補正"] = f"{resistance_bonus:.3f}"
            details["被ダメージアップ補正"] = f"{dmg_taken_bonus:.3f}"

        final_damage = base_damage * damage_up_bonus * damage_boost_bonus * crit_bonus * defense_bonus * resistance_bonus * dmg_taken_bonus
        return (final_damage if final_damage > 0 else 0, details)
    except Exception:
        if not rng_mode: traceback.print_exc()
        return (0, {"エラー": "計算中に例外発生"} if not rng_mode else None)

def calculate_abnormal_status_damage(effect_name: str, stacks: int, buffed_raw_stats: Dict[str, float], enemy_info: Dict) -> float:
    try:
        effect_info = ABNORMAL_EFFECTS[effect_name]
        base_dmg = ABNORMAL_DAMAGE_BASE_LV90
        attr_coeff = effect_info["attr_coeff"]
        stack_multipliers = ABNORMAL_STACK_MULTIPLIERS.get(effect_name, [1])
        if effect_name == "騒光効果" and stacks > 10:
            stack_mult = stack_multipliers[-1] + (stacks - 10) * 1.812
        else:
            stack_mult = stack_multipliers[min(stacks, len(stack_multipliers)) - 1]
        initial_damage = base_dmg * attr_coeff * stack_mult
        boost_key = EFFECT_NAME_TO_BOOST_KEY.get(effect_name)
        boost_bonus = 1 + buffed_raw_stats.get(boost_key, 0) / 100
        damage_types = [EFFECT_NAME_TO_ATTR_DMG_TYPE.get(effect_name)]
        defense_bonus, resistance_bonus, dmg_taken_bonus = _calculate_shared_bonuses(buffed_raw_stats, enemy_info, damage_types)
        final_damage = initial_damage * boost_bonus * defense_bonus * resistance_bonus * dmg_taken_bonus
        return final_damage if final_damage > 0 else 0
    except Exception: traceback.print_exc(); return 0

def _process_phase(phase_sequence: List[Action],
                    team_builds: List[Build],
                    team_stats: Dict,
                    all_buffs:Dict,
                    enemy_info: Dict,
                    initial_concerto_energy: Dict[str, float], # 型を修正
                    initial_resonance_energy: Dict[str, float],
                    time_marks: List[bool],
                    rng_mode: bool = False,
                    ignored_buff_key: Optional[str] = None,
                    manually_disabled: Optional[Set[str]] = None,
                    manually_set_stacks: Optional[Dict[str, int]] = None) -> RotationPhaseResult:
    
    # ▼▼▼ ここからが修正点 ▼▼▼
    # 関数冒頭で、空のシーケンスの場合のデフォルトリターン値を定義
    if not phase_sequence:
        return {
            "log": [], 
            "total_damage": 0.0, 
            "total_time": 0.0,
            "final_concerto_energy": initial_concerto_energy,
            "final_resonance_energy": initial_resonance_energy
        }
    # ▲▲▲ ここまで ▲▲▲
    log, total_dmg, concerto_energy = [], 0, initial_concerto_energy
    active_buffs_carry_over = {} 
    manually_disabled = set()
    manually_set_stacks = {}
    team_char_names = {b[KEY_CHARACTER_NAME] for b in team_builds if b.get(KEY_CHARACTER_NAME)} 
    char_concerto_energy = initial_concerto_energy.copy()
    char_resonance_energy = initial_resonance_energy.copy()

    for action in phase_sequence:
        # --- ▼▼▼ ここから修正 ▼▼▼ ---
        # 変数名を current_char_name に統一
        current_char_name = action.get(KEY_CHARACTER)
        if not current_char_name:
             if action.get(KEY_SKILL) in ABNORMAL_EFFECTS:
                 current_char_name = team_builds[0][KEY_CHARACTER_NAME] if team_builds else ""
             else: continue

        build = next((b for b in team_builds if b[KEY_CHARACTER_NAME] == current_char_name), None)
        if not build: continue
        
        _, base_raw, base_values = team_stats[current_char_name]


        skill_data_for_current_action = action.get(KEY_SKILL_DATA) # 現在のアクションのskill_dataを取得
        skill_name_for_current_action = action.get(KEY_SKILL, "")
        activation_types_for_current_action = skill_data_for_current_action.get(KEY_ACTIVATION_TYPES, []) if skill_data_for_current_action else []
        is_healing_skill_executed = skill_data_for_current_action.get("is_healing", False) if skill_data_for_current_action else False

        # --- ▼▼▼ ここから修正 ▼▼▼ ---
        # 1. バフの適用 (持続バフと一時バフ) は、ダメージ計算より前に行う

        # 1a. 持続バフの適用 (前のアクションからの引き継ぎと、このアクションで発動するon-cast/常時バフ)
        active_persistent_buffs = active_buffs_carry_over.copy() 
        
        if current_char_name:
            for buff_key, buff_data in all_buffs.items():
                if buff_data.get("is_transient"): continue # 持続バフのみ対象
                
                is_triggered_by_this_action_on_cast = False
                owner = buff_data.get("owner")
                for trigger in buff_data.get("trigger", []):
                    event, source, timing = trigger.get("event"), trigger.get("source"), trigger.get("timing", "発動時")
                    
                    source_match = (source == "自身発動" and owner == current_char_name) or \
                                 (source == "チーム内キャラ発動" and owner in team_char_names)

                    event_match = (event == "常時") or \
                                  (event in activation_types_for_current_action) or \
                                  (event.startswith("スキル: ") and event.replace("スキル: ", "") == skill_name_for_current_action) or \
                                  (event == "回復効果" and is_healing_skill_executed)

                    if source_match and event_match and (timing == "発動時" or event == "常時"):
                        is_triggered_by_this_action_on_cast = True
                        break 
                
                if is_triggered_by_this_action_on_cast:
                    if buff_key not in manually_disabled:
                        effects = buff_data.get(KEY_EFFECTS, [])
                        is_stackable = effects and effects[0].get("type") == "スタック形式"
                        if is_stackable:
                            stack_count = manually_set_stacks.get(buff_key, effects[0].get("max_stacks", 1))
                            if stack_count > 0:
                                active_persistent_buffs[buff_key] = stack_count
                            else:
                                if buff_key in active_persistent_buffs:
                                    del active_persistent_buffs[buff_key]
                        else:
                            active_persistent_buffs[buff_key] = True
                    else:
                        if buff_key in active_persistent_buffs:
                            del active_persistent_buffs[buff_key]
            
            action[KEY_ACTIVE_BUFFS] = active_persistent_buffs # このアクションに適用される持続バフの状態

        # 1b. 一時的バフの適用 (このアクションがトリガーする一時バフを final_buffed_raw_stats に適用)
        #     この部分は、active_persistent_buffs をベースに一時バフを加算する
        final_buffed_raw_stats = apply_buffs(base_raw, active_persistent_buffs, current_char_name, all_buffs, build.get(KEY_CONSTELLATION, 0), build.get(KEY_WEAPON_RANK, 1), ignored_buff_key)
        
        # transient_buff_manual_settings はUIの可視化と _recalculate_all_actions_state での管理のみに使用される
        # 実際の適用はapply_buffs (持続) と以下の追加ロジック (一時) で行う
        
        manual_settings = action.get('transient_buff_manual_settings', {'disabled': set(), 'stacks': {}})
        
        # visible_buffs_for_display に含まれるべき一時バフの情報をここで収集し、適用する
        if current_char_name:
            for buff_key, buff_data in all_buffs.items():
                if not buff_data.get("is_transient"): continue # 一時的バフのみを対象
                if buff_key in manual_settings.get('disabled', set()): continue # 手動で無効化されていたらスキップ

                is_triggered_by_this_action_on_cast = False
                owner = buff_data.get("owner")
                for trigger in buff_data.get("trigger", []):
                    event, source, timing = trigger.get("event"), trigger.get("source"), trigger.get("timing", "発動時")
                    source_match = (source == "自身発動" and owner == current_char_name) or \
                                   (source == "チーム内キャラ発動" and owner in team_char_names)
                    event_match = (event == "常時") or \
                                  (event in activation_types_for_current_action) or \
                                  (event.startswith("スキル: ") and event.replace("スキル: ", "") == skill_name_for_current_action) or \
                                  (event == "回復効果" and is_healing_skill_executed)

                    if source_match and event_match and (timing == "発動時" or event == "常時"):
                        is_triggered_by_this_action_on_cast = True
                        break 
                
                if is_triggered_by_this_action_on_cast:
                    for effect in buff_data.get(KEY_EFFECTS, []):
                        if effect.get("type") == "スタック形式":
                            stack_count = manual_settings.get('stacks', {}).get(buff_key, effect.get("max_stacks", 1))
                            if stack_count > 0:
                                per_stack = effect.get("effect_per_stack", [0]*5)
                                value_per_stack = per_stack[build.get(KEY_WEAPON_RANK, 1)-1] if isinstance(per_stack, list) else per_stack
                                final_buffed_raw_stats[effect["stat_to_buff"]] += value_per_stack * stack_count
                        elif "stat_to_buff" in effect:
                            value = effect.get(KEY_VALUE, [0]*5)
                            value = value[build.get(KEY_WEAPON_RANK, 1)-1] if isinstance(value, list) else value
                            final_buffed_raw_stats[effect["stat_to_buff"]] += value
        
        # 2. ダメージ計算
        damage = 0
        details = {} if not rng_mode else None # rng_modeならdetailsはNone
        
        if skill_name_for_current_action in ABNORMAL_EFFECTS:
            stacks = action.get(KEY_STACKS, 1)
            damage = calculate_abnormal_status_damage(skill_name_for_current_action, stacks, final_buffed_raw_stats, enemy_info)
        else:
            if skill_data_for_current_action: # skill_dataがNoneでない場合のみダメージ計算を試みる
                final_stats_with_all_buffs = {
                    "HP": base_values["hp"] * (1 + final_buffed_raw_stats.get("hp_percent", 0) / 100) + final_buffed_raw_stats.get("hp_flat", 0),
                    "攻撃力": base_values["atk"] * (1 + final_buffed_raw_stats.get("atk_percent", 0) / 100) + final_buffed_raw_stats.get("atk_flat", 0),
                    "防御力": base_values["def"] * (1 + final_buffed_raw_stats.get("def_percent", 0) / 100) + final_buffed_raw_stats.get("def_flat", 0)
                }
                char_attribute = build.get(KEY_CHARACTER_DATA, {}).get(KEY_ATTRIBUTE)
                
                damage, details = calculate_skill_damage(final_stats_with_all_buffs, final_buffed_raw_stats, skill_data_for_current_action, enemy_info, char_attribute, rng_mode=rng_mode)
            # else: skill_data_for_current_actionがNoneならdamageは0のまま (これは正しくない)

        # 3. エネルギー計算
        concerto_energy_gain = skill_data_for_current_action.get(KEY_CONCERTO_ENERGY, 0) if skill_data_for_current_action else 0
        
        if "終奏スキル" in activation_types_for_current_action: concerto_energy_gain = 0
        
        # 共鳴エネルギー獲得は、skill_dataがNoneでも発動しうる
        calculated_resonance_gain = action.get("manual_resonance_gain", 0) # manual_resonance_gainをデフォルト値として使用
        
        if skill_data_for_current_action: # スキルに紐づくエネルギー獲得
            executor_efficiency = _get_character_efficiency(current_char_name, base_raw, active_persistent_buffs, all_buffs, build)
            gain_flat = skill_data_for_current_action.get(KEY_RESONANCE_ENERGY_GAIN_FLAT, 0)
            gain_scaling = skill_data_for_current_action.get(KEY_RESONANCE_ENERGY_GAIN_SCALING, 0)
            calculated_resonance_gain += (gain_scaling * (executor_efficiency / 100.0)) + gain_flat

        total_gain_for_teammates = defaultdict(float)
        for buff_key, buff_data in all_buffs.items():
            if buff_data.get("is_transient"): continue # エネルギー獲得バフは一時的でないもののみ
            if buff_key in manually_disabled: continue 

            is_triggered_for_energy = False
            owner = buff_data.get("owner")
            for trigger in buff_data.get("trigger", []):
                event, source = trigger.get("event"), trigger.get("source")
                source_match = (source == "自身発動" and owner == current_char_name) or (source == "チーム内キャラ発動" and owner in team_char_names)
                event_match = (event == "常時") or \
                              (event in activation_types_for_current_action) or \
                              (event.startswith("スキル: ") and event.replace("スキル: ", "") == skill_name_for_current_action) or \
                              (event == "回復効果" and is_healing_skill_executed)

                if source_match and event_match and (trigger.get("timing") == "発動時" or event == "常時"):
                    is_triggered_for_energy = True; break
            
            if is_triggered_for_energy:
                target_type = buff_data.get(KEY_TARGET, "自身")
                target_chars_for_energy_gain = []
                if target_type == "自身": target_chars_for_energy_gain.append(owner)
                elif target_type == "チーム全員": target_chars_for_energy_gain = list(team_char_names)
                elif target_type == "チーム内キャラクター1人":
                    target_char = action.get("target_selections", {}).get(buff_key) or _get_default_target(current_char_name)
                    target_chars_for_energy_gain.append(target_char)

                for effect in buff_data.get(KEY_EFFECTS, []):
                    value = effect.get(KEY_VALUE, 0)
                    if effect.get("type") == "共鳴エネルギー獲得(固定)":
                        for char in target_chars_for_energy_gain:
                            if char == current_char_name: calculated_resonance_gain += value
                            else: total_gain_for_teammates[char] += value
                    elif effect.get("type") == "共鳴エネルギー獲得(変動)":
                        for char in target_chars_for_energy_gain:
                            receiver_build = next((b for b in team_builds if b.get(KEY_CHARACTER_NAME) == char), None)
                            _, receiver_base_raw, _ = team_stats[char]
                            receiver_efficiency = _get_character_efficiency(char, receiver_base_raw, active_persistent_buffs, all_buffs, receiver_build)
                            energy_gain = value * (receiver_efficiency / 100.0)
                            if char == current_char_name: calculated_resonance_gain += energy_gain
                            else: total_gain_for_teammates[char] += energy_gain
            
        action["concerto_energy_gain"] = action.get("manual_concerto_gain", concerto_energy_gain)
        action["resonance_energy_gain"] = action.get("manual_resonance_gain", calculated_resonance_gain) # calculated_resonance_gainは既にmanual_gainを含む

        if current_char_name:
            if "終奏スキル" in activation_types_for_current_action:
                char_concerto_energy[current_char_name] = 0
            char_concerto_energy[current_char_name] += action["concerto_energy_gain"]
            
            char_resonance_energy[current_char_name] += action["resonance_energy_gain"]
        
        for char, gain in total_gain_for_teammates.items():
            char_resonance_energy[char] += gain

        if "共鳴解放" in activation_types_for_current_action and current_char_name:
            char_resonance_energy[current_char_name] = 0

        for char, energy in char_resonance_energy.items():
            char_build = next((b for b in team_builds if b.get(KEY_CHARACTER_NAME) == char), None)
            if char_build:
                max_e = char_build.get(KEY_CHARACTER_DATA, {}).get(KEY_RESONANCE_ENERGY_REQUIRED, 1)
                char_resonance_energy[char] = min(energy, max_e)
        
        if current_char_name:
            char_concerto_energy[current_char_name] = min(char_concerto_energy.get(current_char_name, 0), 100.0)
        
        action["concerto_energy_total"] = char_concerto_energy.get(current_char_name, 0)
        action["resonance_energy_total"] = char_resonance_energy.get(current_char_name, 0)

        # 4. UI表示用バフと一時的バフを決定 (visible_buffs_for_display)
        visible_buffs_for_display = active_persistent_buffs.copy()
        
        action['transient_buff_manual_settings'] = {
            'disabled': {k for k in manually_disabled if all_buffs.get(k, {}).get("is_transient")},
            'stacks': {k: v for k, v in manually_set_stacks.items() if all_buffs.get(k, {}).get("is_transient")}
        }

        if current_char_name:
            for buff_key, buff_data in all_buffs.items():
                if not buff_data.get("is_transient"): continue

                is_triggered_by_this_action_on_cast = False
                owner = buff_data.get("owner")
                for trigger in buff_data.get("trigger", []):
                    event, source, timing = trigger.get("event"), trigger.get("source"), trigger.get("timing", "発動時")
                    
                    source_match = (source == "自身発動" and owner == current_char_name) or \
                                   (source == "チーム内キャラ発動" and owner in team_char_names)
                    
                    event_match = (event == "常時") or \
                                  (event in activation_types_for_current_action) or \
                                  (event.startswith("スキル: ") and event.replace("スキル: ", "") == skill_name_for_current_action) or \
                                  (event == "回復効果" and is_healing_skill_executed)
                    
                    if source_match and event_match and (timing == "発動時" or event == "常時"):
                        is_triggered_by_this_action_on_cast = True
                        break
                
                if is_triggered_by_this_action_on_cast:
                    if buff_key not in manually_disabled:
                        effects = buff_data.get(KEY_EFFECTS, [])
                        is_stackable = effects and effects[0].get("type") == "スタック形式"
                        if is_stackable:
                            stack_count = manually_set_stacks.get(buff_key, effects[0].get("max_stacks", 1))
                            if stack_count > 0:
                                visible_buffs_for_display[buff_key] = stack_count
                            else:
                                if buff_key in visible_buffs_for_display:
                                    del visible_buffs_for_display[buff_key]
                        else:
                            visible_buffs_for_display[buff_key] = True
                    else:
                        if buff_key in visible_buffs_for_display:
                            del visible_buffs_for_display[buff_key]
            
            action['visible_buffs_for_display'] = visible_buffs_for_display

        total_dmg += damage
        if not rng_mode:
            log.append({KEY_CHARACTER: current_char_name, KEY_SKILL: skill_name_for_current_action, KEY_SKILL_DATA: skill_data_for_current_action, "damage": damage, "total_damage": total_dmg, "concerto_energy": concerto_energy, "calculation_details": details})
    
        total_time = float(time_marks.count(True)) if time_marks else len(phase_sequence) * 1.5
        return {
            "log": log, 
            "total_damage": total_dmg, 
            "total_time": total_time,
            "final_concerto_energy": char_concerto_energy,
            "final_resonance_energy": char_resonance_energy
        }

def process_rotation(team_builds: List[Build], initial_sequence: List[Action], loop_sequence: List[Action], enemy_info: Dict, all_buff_data_pre_gathered: Dict, stage_effects_name: str, data_manager, time_marks_initial: List[bool], time_marks_loop: List[bool], ignore_buff: Optional[str] = None) -> CalculationResult:
    all_buffs = all_buff_data_pre_gathered if all_buff_data_pre_gathered is not None else {}
    if stage_effects_name and data_manager:
        stage_data = data_manager.get_data("stage_effects", {}).get(stage_effects_name, {})
        for k, v in stage_data.get(KEY_BUFFS, {}).items(): all_buffs[f"stage_{k}"] = {**v, "owner": "Stage"}
    
    team_stats = {b[KEY_CHARACTER_NAME]: calculate_base_stats(b) for b in team_builds if b.get(KEY_CHARACTER_NAME)}
    
    initial_concerto_energy = defaultdict(float)
    initial_resonance_energy = defaultdict(float)
    
    initial_phase_result = _process_phase(initial_sequence, team_builds, team_stats, all_buffs, enemy_info, initial_concerto_energy, initial_resonance_energy, time_marks=time_marks_initial, ignored_buff_key=ignore_buff)
    
    final_concerto_energy = initial_phase_result.get("final_concerto_energy", defaultdict(float))
    final_resonance_energy = initial_phase_result.get("final_resonance_energy", defaultdict(float))
    
    loop_phase_result = _process_phase(loop_sequence, team_builds, team_stats, all_buffs, enemy_info, final_concerto_energy, final_resonance_energy, time_marks=time_marks_loop, ignored_buff_key=ignore_buff)
    
    # ▼▼▼ ここが修正点 ▼▼▼
    # もし結果がNoneや期待しない形だった場合でも、デフォルトの空の結果を返すようにする
    return {
        "initial_phase": initial_phase_result or {},
        "loop_phase": loop_phase_result or {"log": [], "total_damage": 0.0},
        "simulation_stats": None
    }
    # ▲▲▲ ここまで ▲▲▲

def run_simulation_with_rng(num_simulations: int, num_loops: int, team_builds: List, initial_sequence: List, loop_sequence: List, enemy_info: Dict, all_buffs: Dict, time_marks_initial: List[bool], time_marks_loop: List[bool]):
    total_damages = []
    team_stats_cache = {b[KEY_CHARACTER_NAME]: calculate_base_stats(b) for b in team_builds if b.get(KEY_CHARACTER_NAME)}
    
    # 時間計算
    total_time = time_marks_initial.count(True) + (time_marks_loop.count(True) * num_loops)
    if total_time == 0:
        total_time = (len(initial_sequence) + len(loop_sequence) * num_loops) * 1.5
    if total_time == 0: total_time = 1 # ゼロ除算防止

    for i in range(num_simulations):
        # _process_phaseをRNGモードで呼び出す
        initial_phase_result = _process_phase(initial_sequence, team_builds, team_stats_cache, all_buffs, enemy_info, 0.0, time_marks=time_marks_initial, rng_mode=True)
        loop_phase_result = _process_phase(loop_sequence, team_builds, team_stats_cache, all_buffs, enemy_info, 0.0, time_marks=time_marks_loop, rng_mode=True)
        
        total_damage = initial_phase_result["total_damage"] + (loop_phase_result["total_damage"] * num_loops)
        total_damages.append(total_damage)
    
    damages_np = np.array(total_damages)
    stats = {
        "simulations_count": num_simulations,
        "total_damage_avg": np.mean(damages_np), "total_damage_max": np.max(damages_np),
        "total_damage_min": np.min(damages_np), "total_damage_median": np.median(damages_np),
        "total_damage_std_dev": np.std(damages_np), "dps_avg": np.mean(damages_np) / total_time,
        "dps_max": np.max(damages_np) / total_time, "dps_min": np.min(damages_np) / total_time,
    }
    return stats

def generate_build_combinations(
    selected_costs: List[str],
    eff_subs_per_echo: int,
    sub_level_index: int,
    selected_eff_subs: Dict[str, str], # name -> priority ("通常", "優先", "必須")
    selected_eff_mains: Dict[str, List[str]],
    full_search_mode: bool
):
    """
    【v3】各音骸が完全に独立したサブステを持つ組み合わせを生成する。
    メインステとサブステの重複は許容する。
    """
    
    # 1. サブステプールを優先度別に分類
    sub_pools = {"必須": [], "優先": [], "通常": []}
    for sub_name, priority in selected_eff_subs.items():
        sub_data = ECHO_DATA["sub_stat_values"].get(sub_name)
        if sub_data and len(sub_data["values"]) > sub_level_index:
            stat_obj = {"name": sub_name, "key": sub_data["key"], "value": sub_data["values"][sub_level_index]}
            sub_pools[priority].append(stat_obj)

    all_subs_pool = sub_pools["必須"] + sub_pools["優先"] + sub_pools["通常"]
    if not all_subs_pool:
        return

    # 2. コスト組み合わせごとにループ
    for cost_combo_str in selected_costs:
        costs = [int(c) for c in cost_combo_str.split('-')]
        
        # 3. 各音骸のメインステータスの候補リストを作成
        main_stat_options_per_echo = []
        for cost in costs:
            cost_str = str(cost)
            valid_mains = selected_eff_mains.get(cost_str, [])
            options = [s for s in ECHO_DATA["main_stats"].get(cost_str, []) if s["name"] in valid_mains]
            if not options: break
            main_stat_options_per_echo.append(options)
        
        if len(main_stat_options_per_echo) != 5: continue

        # 4. メインステータスの全組み合わせを生成
        main_stat_builds = product(*main_stat_options_per_echo)

        for main_stat_set in main_stat_builds:
            # --- 5. サブステータスの組み合わせ生成 (各音骸で独立) ---
            sub_stat_options_for_all_echos = []

            for i in range(5): # 5つの音骸それぞれに対してループ
                # --- ▼▼▼ ここからが新しいロジック ▼▼▼ ---
                # **メインとサブの重複を許容するため、重複チェックは行わない**
                
                sub_sets_for_this_echo = []
                
                if full_search_mode:
                    # 全探索モード: プール全体から組み合わせを生成
                    if len(all_subs_pool) >= eff_subs_per_echo:
                        sub_sets_for_this_echo = list(combinations(all_subs_pool, eff_subs_per_echo))
                else:
                    # 優先度モード
                    must_haves = sub_pools["必須"]
                    if len(must_haves) > eff_subs_per_echo: continue

                    num_needed = eff_subs_per_echo - len(must_haves)
                    if num_needed == 0:
                        sub_sets_for_this_echo = [tuple(must_haves)]
                    elif num_needed > 0:
                        priority_pool = [s for s in sub_pools["優先"] if s not in must_haves]
                        normal_pool = [s for s in sub_pools["通常"] if s not in must_haves]
                        
                        fill_pool = priority_pool + normal_pool
                        if len(fill_pool) >= num_needed:
                            fill_combos = combinations(fill_pool, num_needed)
                            for combo in fill_combos:
                                sub_sets_for_this_echo.append(tuple(must_haves) + combo)
                
                if not sub_sets_for_this_echo:
                    # この音骸で有効なサブステセットが作れなければ、このメインステセットは無効
                    break
                
                sub_stat_options_for_all_echos.append(sub_sets_for_this_echo)
            
            # 5つの音骸すべてでサブステ候補が作れたかチェック
            if len(sub_stat_options_for_all_echos) != 5:
                continue
            
            # --- ▲▲▲ 新しいロジックここまで ▲▲▲ ---

            # 6. 5つの音骸、それぞれのサブステ候補リストから組み合わせを生成
            all_sub_stat_builds = product(*sub_stat_options_for_all_echos)
            
            for sub_stat_tuple_of_tuples in all_sub_stat_builds:
                echo_list = []
                for i in range(5):
                    echo_list.append({
                        "name": f"OptimizedEcho{i+1}", "cost": costs[i],
                        "main_stat": main_stat_set[i],
                        "sub_stats": list(sub_stat_tuple_of_tuples[i])
                    })
                
                yield {"cost_combo": cost_combo_str, "echo_list": echo_list}

def generate_owned_echo_builds(owned_echos: Dict[str, List[Dict]], cost_combo_str: str):
    """
    所持している音骸のプールから、指定されたコスト組み合わせに合致する
    全ての装備パターンを生成するジェネレータ。
    """
    costs_to_find = [int(c) for c in cost_combo_str.split('-')]
    
    # 各コストで必要な音骸の数をカウント
    required_counts = {4: costs_to_find.count(4), 3: costs_to_find.count(3), 1: costs_to_find.count(1)}
    
    # 各コストのプールから、必要な数だけ音骸を選ぶ組み合わせを生成
    cost4_combos = list(combinations(owned_echos.get("4", []), required_counts[4]))
    cost3_combos = list(combinations(owned_echos.get("3", []), required_counts[3]))
    cost1_combos = list(combinations(owned_echos.get("1", []), required_counts[1]))
    
    # 組み合わせが存在しない場合は終了
    if not cost4_combos and required_counts[4] > 0: return
    if not cost3_combos and required_counts[3] > 0: return
    if not cost1_combos and required_counts[1] > 0: return

    # productを使って、各コストの組み合わせをさらに組み合わせる
    # 例: c4の組み合わせ * c3の組み合わせ * c1の組み合わせ
    all_cost_product = product(
        cost4_combos if required_counts[4] > 0 else [()],
        cost3_combos if required_counts[3] > 0 else [()],
        cost1_combos if required_counts[1] > 0 else [()]
    )

    for product_tuple in all_cost_product:
        # product_tupleの中身をフラットなリストにする
        final_echo_list = [echo for combo in product_tuple for echo in combo]
        if len(final_echo_list) == 5:
            yield final_echo_list
                
                
                
                
                
                