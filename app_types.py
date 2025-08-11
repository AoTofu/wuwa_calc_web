# app_types.py
from typing import TypedDict, List, Dict, Literal, Optional, Any, Set

# --- 基本的なデータ型 ---
StatKey = str
StatName = str
BuffType = Literal["単純加算", "スタック形式", "ステータス変換", "ダメージ倍率アップ"]
AttributeName = Literal["", "気動", "焦熱", "電導", "凝縮", "消滅", "回折"]
SkillCategory = Literal["", "基本攻撃手段", "共鳴スキル", "共鳴回路", "共鳴解放", "変奏スキル", "終奏スキル", "その他"]

class Stat(TypedDict):
    key: StatKey
    value: float
    name: Optional[StatName]

class TriggerCondition(TypedDict):
    event: str  # 例: "通常攻撃", "共鳴スキル", "スキル名"
    source: str # 例: "自身発動"
    timing: Optional[str] # 例: "発動時", "命中時"

# --- 音骸関連 ---
class EchoStat(TypedDict):
    key: StatKey
    value: float
    name: StatName

class Echo(TypedDict):
    name: str
    cost: int
    main_stat: Optional[EchoStat]
    sub_stats: List[EchoStat]

# --- データファイル構造 ---
class SkillData(TypedDict):
    name: str
    multiplier: float
    attribute: Literal["atk", "hp", "def"]
    activation_types: List[str]
    damage_types: List[str]
    concerto_energy: float
    resonance_energy_gain_flat: Optional[float]
    resonance_energy_gain_scaling: Optional[float]
    skill_category: SkillCategory
    is_healing: Optional[bool] # 回復効果の有無

class BuffEffect(TypedDict):
    """
    単一のバフ効果を定義する型。
    'type'の値によって、他のキーの意味合いが変わる。
    """
    type: BuffType # "単純加算", "共鳴エネルギー獲得(固定)" など

    # type: "単純加算", "スタック形式", "ダメージ倍率アップ" で使用
    stat_to_buff: Optional[StatKey]
    
    # type: "単純加算", "ダメージ倍率アップ", "共鳴エネルギー獲得(固定)", "共鳴エネルギー獲得(変動)" で使用
    # - 単純加算など: ステータスの増加量
    # - 共鳴エネルギー獲得: エネルギーの獲得量
    value: Optional[Any] # float or List[float]

    # type: "スタック形式" で使用
    effect_per_stack: Optional[Any] # float or List[float]
    max_stacks: Optional[int]

    # type: "ステータス変換" で使用
    source_stat: Optional[StatKey]
    dest_stat: Optional[StatKey]
    threshold: Optional[float]
    conversion_per_unit: Optional[float]
    conversion_gain_unit: Optional[Any] # float or List[float]
    max_gain: Optional[Any] # float or List[float]

class BuffData(TypedDict):
    description: str
    trigger: List[TriggerCondition]
    target: str
    effects: List[BuffEffect]
    constellation: Optional[int]
    owner: Optional[str]
    source_type: Optional[str]
    source_name: Optional[str]
    buff_key_name: Optional[str]
    icon_key: Optional[str]
    icon_type: Optional[str]
    is_transient: Optional[bool] # Trueの場合、トリガーされたアクションでのみ有効

class ConstellationData(TypedDict):
    buffs: Dict[str, BuffData]
    skills: List[SkillData]

class CharacterData(TypedDict):
    name: str
    base_hp: float
    base_atk: float
    base_def: float
    resonance_energy_required: Optional[float]
    innate_stats: List[Stat]
    skills: List[SkillData]
    buffs: Dict[str, BuffData]
    image_file: str
    weapon_type: str
    attribute: AttributeName
    constellations: Dict[str, ConstellationData]

class WeaponData(TypedDict):
    name: str
    base_atk: float
    sub_stat: Dict[str, Any]
    weapon_type: str
    effect_data: BuffData
    image_file: str

class HarmonySetEffect(TypedDict):
    buffs: Dict[str, BuffData]
    skills: List[SkillData]
    has_2set_effect: Optional[bool]
    has_3set_effect: Optional[bool]
    has_5set_effect: Optional[bool]

class HarmonyData(TypedDict):
    name: str
    buffs: Dict[Literal["2セット効果", "3セット効果", "5セット効果"], HarmonySetEffect]
    image_file: str


class EchoSkillData(TypedDict):
    name: str
    skills: List[SkillData]
    buffs: Dict[str, BuffData]
    image_file: str

class StageEffectData(TypedDict):
    name: str
    skills: List[SkillData]
    buffs: Dict[str, BuffData]
    image_file: str

# --- ビルドとローテーション関連 ---
class Build(TypedDict):
    character_name: str
    character_data: CharacterData
    weapon_name: str
    weapon_data: WeaponData
    constellation: int
    weapon_rank: int
    harmony1_name: str
    harmony1_data: HarmonyData
    harmony2_name: str
    harmony2_data: HarmonyData
    echo_list: List[Echo]
    echo_skill_name: str
    echo_skill_data: EchoSkillData

class ActiveBuffTarget(TypedDict):
    target_char: str

class Action(TypedDict):
    character: Optional[str]
    skill: str
    source: str
    skill_data: Optional[SkillData]
    active_buffs: Dict[str, Any]
    target_selections: Optional[Dict[str, str]]
    triggered_single_target_buffs: Optional[List[str]]
    # NEW: 一時的バフの手動設定（無効化、スタック数）を保持
    transient_buff_manual_settings: Optional[Dict[str, Any]]

class LogEntry(TypedDict):
    character: str
    skill: str
    skill_data: SkillData
    damage: float
    total_damage: float
    concerto_energy: float
    calculation_details: Optional[Dict[str, Any]]

class RotationPhaseResult(TypedDict):
    log: List[LogEntry]
    total_damage: float
    total_time: float
    final_concerto_energy: Dict[str, float]
    final_resonance_energy: Dict[str, float]

class SimulationStats(TypedDict):
    simulations_count: int
    total_damage_avg: float
    total_damage_max: float
    total_damage_min: float
    total_damage_median: float
    total_damage_std_dev: float  # 標準偏差
    dps_avg: float
    dps_max: float
    dps_min: float

class CalculationResult(TypedDict):
    initial_phase: RotationPhaseResult
    loop_phase: RotationPhaseResult
    # NEW: シミュレーション統計情報を追加
    simulation_stats: Optional[SimulationStats]

# --- AppState ---
class AppStateData(TypedDict):
    team_builds: List[Build]
    rotation_initial: List[Action]
    rotation_loop: List[Action]
    enemy_info: Dict[str, Any]
    calculation_results: Optional[CalculationResult]
    stage_effects_name: str
    available_abnormal_effects: Set[str]
    loaded_time_marks: Optional[List[bool]]

class SharableResult(TypedDict):
    # 計算結果そのもの
    calculation_results: CalculationResult 
    
    # 計算の前提条件
    team_builds: List[Build]
    rotation_initial: List[Action]
    rotation_loop: List[Action]
    enemy_info: Dict[str, Any]
    stage_effects_name: str
    
    # --- ▼▼▼ ここから修正 ▼▼▼ ---
    # UIの状態
    time_marks: List[bool] # チェックボックスの状態をTrue/Falseのリストで保存
    active_comparison_sources: Dict[str, str] # (panel_idx, source_type) のタプルキーを文字列化した辞書
    # --- ▲▲▲ 修正ここまで ▲▲▲ ---
    
    # メタデータ
    saved_by: str
    character_names: List[str]