// script.js (完成版)

// -----------------------------------------------------------------------------
// DataManager モジュール (data_manager.py のWeb版)
// -----------------------------------------------------------------------------
const dataManager = {
    // データ保持用
    data: {},
    config: {},
    dataKeys: ["characters", "weapons", "harmony_effects", "echo_skills", "builds", "scenarios", "stage_effects"],

    // File System Access API用
    dataDirHandle: null,
    isInitialized: false,

    /**
     * DataManagerを初期化する。File System Access APIが利用可能かチェックする。
     */
    async initialize() {
        if (!('showDirectoryPicker' in window)) {
            console.warn("File System Access API is not supported. Using fallback mode.");
            this.isInitialized = true;
            return false;
        }

        try {
            this.dataDirHandle = await window.showDirectoryPicker({ id: 'wuwa-calc-data-dir', mode: 'readwrite' });
            await this._verifyDirectoryPermissions();
            await this._loadAllData();
            this.isInitialized = true;
            document.getElementById('data-folder-status').textContent = `フォルダ '${this.dataDirHandle.name}' を読み込みました`;
            document.getElementById('data-folder-status').classList.add('loaded');
            console.log("DataManager initialized successfully with File System Access API.");
            return true;

        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn("Directory selection was cancelled by the user.");
            } else {
                console.error("Error initializing DataManager:", error);
                await customModals.alert("読込エラー", "データフォルダの読み込み中にエラーが発生しました。\n詳細はコンソールを確認してください。");
            }
            return false;
        }
    },

    /**
     * ディレクトリへの書き込み権限を確認・要求する
     */
    async _verifyDirectoryPermissions() {
        const options = { mode: 'readwrite' };
        if (await this.dataDirHandle.queryPermission(options) === 'granted') {
            return true;
        }
        if (await this.dataDirHandle.requestPermission(options) === 'granted') {
            return true;
        }
        throw new Error("User did not grant readwrite permission to the directory.");
    },

    /**
     * 全てのJSONファイルをディレクトリから読み込む
     */
    async _loadAllData() {
        try {
            const fileHandle = await this.dataDirHandle.getFileHandle('config.json');
            const file = await fileHandle.getFile();
            this.config = JSON.parse(await file.text());
        } catch (e) {
            console.warn("config.json not found or failed to parse. Initializing with empty config.");
            this.config = {};
        }

        for (const key of this.dataKeys) {
            try {
                const fileHandle = await this.dataDirHandle.getFileHandle(`${key}.json`);
                const file = await fileHandle.getFile();
                const content = await file.text();
                this.data[key] = content ? JSON.parse(content) : {};
            } catch (e) {
                if (e.name === 'NotFoundError') {
                    console.warn(`'${key}.json' not found. Initializing with empty data.`);
                    this.data[key] = {};
                } else {
                    console.error(`Error loading '${key}.json':`, e);
                    this.data[key] = {};
                }
            }
        }
    },

    /**
     * データを取得する
     */
    getData(key, defaultValue = {}) {
        return this.data[key] || defaultValue;
    },

    /**
     * 指定されたキーのデータをファイルに保存する
     */
    async saveData(key, value) {
        if (!this.dataDirHandle) {
            console.warn("Save cancelled: No directory handle.");
            alert("保存機能を利用するには、まずデータフォルダを選択してください。");
            return false;
        }

        this.data[key] = value;
        try {
            await this._createBackup(key);
            const fileHandle = await this.dataDirHandle.getFileHandle(`${key}.json`, { create: true });
            const writable = await fileHandle.createWritable();
            await writable.write(JSON.stringify(this.data[key], null, 4));
            await writable.close();
            console.log(`Successfully saved ${key}.json`);
            return true;
        } catch (error) {
            console.error(`Failed to save ${key}.json:`, error);
            return false;
        }
    },

    /**
     * タイムスタンプ付きのバックアップを作成する
     */
    async _createBackup(key) {
        try {
            const mainFileHandle = await this.dataDirHandle.getFileHandle(`${key}.json`);
            const backupDirHandle = await this.dataDirHandle.getDirectoryHandle('backup', { create: true });

            const now = new Date();
            const timestamp = now.toISOString().slice(0, 19).replace(/[-:T]/g, ''); // YYYYMMDDHHMMSS
            const backupFileName = `${key}_${timestamp}.json`;

            const newFileHandle = await backupDirHandle.getFileHandle(backupFileName, { create: true });
            const writable = await newFileHandle.createWritable();
            await writable.write(await mainFileHandle.getFile());
            await writable.close();
        } catch (error) {
            if (error.name !== 'NotFoundError') {
                console.error(`Backup failed for ${key}:`, error);
            }
        }
    }
};

// -----------------------------------------------------------------------------
// Searchable Popup モジュール
// -----------------------------------------------------------------------------
const searchablePopup = {
    isOpen: false,
    _resolve: null,

    setup() {
        const overlay = document.getElementById('searchable-popup-overlay');
        const closeBtn = document.getElementById('popup-close-btn');
        const searchInput = document.getElementById('popup-search');

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) this.close(null);
        });
        
        closeBtn.addEventListener('click', () => this.close(null));
        searchInput.addEventListener('input', (e) => this._filter(e.target.value));
    },

    open(title, options) {
        return new Promise(resolve => {
            this._resolve = resolve;
            this.isOpen = true;

            document.getElementById('popup-title').textContent = title;
            document.getElementById('popup-search').value = '';
            this._renderList(options);

            document.getElementById('searchable-popup-overlay').classList.add('visible');
            document.getElementById('popup-search').focus();
        });
    },

    close(selectedValue) {
        if (!this.isOpen) return;
        this.isOpen = false;
        document.getElementById('searchable-popup-overlay').classList.remove('visible');
        if (this._resolve) {
            this._resolve(selectedValue);
            this._resolve = null;
        }
    },

    _renderList(options) {
        const listContainer = document.getElementById('popup-list');
        listContainer.innerHTML = '';
        this._currentOptions = options;

        options.forEach(opt => {
            const button = document.createElement('button');
            button.className = 'popup-list-item';

            const displayName = (typeof opt === 'object') ? opt.name : opt;
            button.textContent = displayName;
            button.dataset.value = displayName;

            if (typeof opt === 'object' && opt.attribute) {
                const attrClass = {
                    "気動": "aero", "焦熱": "fusion", "凝縮": "glacio",
                    "電導": "electro", "消滅": "havoc", "回折": "spectro"
                }[opt.attribute] || '';

                if (attrClass) {
                    button.classList.add(`attr-${attrClass}`);
                }
            }

            button.addEventListener('click', () => this.close(button.dataset.value));
            listContainer.appendChild(button);
        });
    },

    _filter(searchTerm) {
        const term = searchTerm.toLowerCase();
        const listContainer = document.getElementById('popup-list');
        listContainer.childNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const text = node.textContent.toLowerCase();
                const yomigana = this._currentOptions.find(o => o.name === node.dataset.value)?.yomigana?.toLowerCase() || '';
                node.style.display = (text.includes(term) || yomigana.includes(term)) ? '' : 'none';
            }
        });
    }
};
// -----------------------------------------------------------------------------
// Custom Modals モジュール
// -----------------------------------------------------------------------------
const customModals = {
    // 汎用的な確認ダイアログ
    confirm(title, text) {
        return new Promise(resolve => {
            const overlay = document.getElementById('confirm-overlay');
            document.getElementById('confirm-title').textContent = title;
            document.getElementById('confirm-text').textContent = text;
            overlay.classList.add('visible');

            const okBtn = document.getElementById('confirm-ok-btn');
            const cancelBtn = document.getElementById('confirm-cancel-btn');

            const cleanup = (result) => {
                overlay.classList.remove('visible');
                okBtn.onclick = null;
                cancelBtn.onclick = null;
                resolve(result);
            };

            okBtn.onclick = () => cleanup(true);
            cancelBtn.onclick = () => cleanup(false);
        });
    },

    // 汎用的な通知ダイアログ
    alert(title, text) {
        return new Promise(resolve => {
            const overlay = document.getElementById('alert-overlay');
            document.getElementById('alert-title').textContent = title;
            document.getElementById('alert-text').textContent = text;
            overlay.classList.add('visible');

            const okBtn = document.getElementById('alert-ok-btn');
            
            const cleanup = () => {
                overlay.classList.remove('visible');
                okBtn.onclick = null;
                resolve();
            };

            okBtn.onclick = () => cleanup();
        });
    },

    // (注: promptは元のコードになかったが、変更指示のコードで使われているため追加)
    prompt(title, text) {
        return new Promise(resolve => {
            const overlay = document.getElementById('save-build-overlay');
            const titleEl = document.getElementById('save-build-title');
            const input = document.getElementById('save-build-input');
            const confirmBtn = document.getElementById('save-build-confirm-btn');
            const cancelBtn = document.getElementById('save-build-cancel-btn');
            
            titleEl.textContent = title;
            // promptにはテキストがないので、inputのplaceholderで代用
            input.placeholder = text;
            input.value = '';
            overlay.classList.add('visible');
            input.focus();
    
            const cleanup = (value) => {
                overlay.classList.remove('visible');
                confirmBtn.onclick = null;
                cancelBtn.onclick = null;
                overlay.onclick = null;
                input.onkeyup = null;
                resolve(value);
            };
    
            confirmBtn.onclick = () => cleanup(input.value);
            cancelBtn.onclick = () => cleanup(null);
            overlay.onclick = (e) => { if (e.target === overlay) cleanup(null); };
            input.onkeyup = (e) => { if (e.key === 'Enter') cleanup(input.value); };
        });
    }
};
// -----------------------------------------------------------------------------
// Character Editor モジュール
// -----------------------------------------------------------------------------
const characterEditor = {
    _resolve: null,
    _characterData: null,
    _activeTab: 'skills',

    setup() {
        // --- メインモーダルのボタンイベント ---
        document.getElementById('char-editor-save-btn').addEventListener('click', () => this._onSave());
        document.getElementById('char-editor-cancel-btn').addEventListener('click', () => this._onCancel());
        document.getElementById('character-editor-overlay').addEventListener('click', (e) => {
            if (e.target.id === 'character-editor-overlay') this._onCancel();
        });

        // --- タブ切り替えイベント ---
        document.getElementById('char-editor-tabs').addEventListener('click', (e) => {
            if (e.target.matches('.tab-button')) {
                this._activeTab = e.target.dataset.tab;
                document.querySelectorAll('#char-editor-tabs .tab-button').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.renderActiveTab();
            }
        });

        // --- タブコンテンツ内の動的イベント（イベント委任）---
        document.getElementById('char-editor-tab-content').addEventListener('click', e => {
            const button = e.target.closest('button');
            if (!button) return;

            const action = button.dataset.action;
            const index = parseInt(button.dataset.index, 10);

            if (this._activeTab === 'skills') {
                if (action === 'edit-skill') this._openSkillEditor(index);
                if (action === 'delete-skill') this._deleteSkill(index);
                if (action === 'new-skill') this._openSkillEditor(-1);
            }
        });
    },

    open(charName, charData) {
        return new Promise(resolve => {
            this._resolve = resolve;
            this._characterData = JSON.parse(JSON.stringify(charData)); // 安全なディープコピー
            this._activeTab = 'skills'; // 常にスキルタブから開始

            document.getElementById('character-editor-title').textContent = charName ? `'${charName}' を編集中` : '新規キャラクター作成';
            
            this.render(); // UI全体を描画
            document.getElementById('character-editor-overlay').classList.add('visible');
        });
    },

    render() {
        // 基本情報フィールドを描画
        const fieldsContainer = document.getElementById('char-editor-main-fields');
        fieldsContainer.innerHTML = `
            <div class="form-row"><label>名前</label><input id="char-editor-name" type="text" value="${this._characterData.name || ''}" readonly></div>
            <div class="form-row"><label>読み仮名</label><input id="char-editor-yomigana" type="text" value="${this._characterData.yomigana || ''}"></div>
            <div class="form-row"><label>レアリティ</label><select id="char-editor-rarity">${["★5", "★4", "★3"].map(o=>`<option ${o===this._characterData.rarity ?'selected':''}>${o}</option>`).join('')}</select></div>
            <div class="form-row"><label>属性</label><select id="char-editor-attribute">${["気動","焦熱","凝縮","電導","消滅","回折"].map(o=>`<option ${o===this._characterData.attribute ?'selected':''}>${o}</option>`).join('')}</select></div>
            <div class="form-row"><label>武器種</label><select id="char-editor-weapon_type">${["迅刀","長刃","増幅器","手甲","拳銃"].map(o=>`<option ${o===this._characterData.weapon_type ?'selected':''}>${o}</option>`).join('')}</select></div>
            <div class="form-row"><label>基礎HP</label><input id="char-editor-base_hp" type="number" value="${this._characterData.base_hp || 0}"></div>
            <div class="form-row"><label>基礎攻撃力</label><input id="char-editor-base_atk" type="number" value="${this._characterData.base_atk || 0}"></div>
            <div class="form-row"><label>基礎防御力</label><input id="char-editor-base_def" type="number" value="${this._characterData.base_def || 0}"></div>
        `;

        // アクティブなタブを描画
        document.querySelectorAll('#char-editor-tabs .tab-button').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === this._activeTab);
        });
        this.renderActiveTab();
    },

    renderActiveTab() {
        switch (this._activeTab) {
            case 'skills': this.renderSkillsTab(); break;
            case 'buffs': this.renderBuffsTab(); break;
            case 'constellations': this.renderConstellationsTab(); break;
        }
    },

    renderSkillsTab() {
        const content = document.getElementById('char-editor-tab-content');
        const skills = this._characterData.skills || [];
        
        let skillRowsHtml = skills.map((skill, index) => `
            <div class="data-item-row">
                <span class="data-item-name">${skill.name || '無題のスキル'}</span>
                <div class="data-item-actions">
                    <button data-action="edit-skill" data-index="${index}" title="編集">✏️</button>
                    <button data-action="delete-skill" data-index="${index}" title="削除">🗑️</button>
                </div>
            </div>
        `).join('');

        content.innerHTML = `
            <div class="data-editor-toolbar"><button class="action-button" data-action="new-skill">+ 新規スキル</button></div>
            <div class="scrollable-list">${skillRowsHtml}</div>
        `;
    },

    async _openSkillEditor(index) {
        const isNew = index === -1;
        const skills = this._characterData.skills || [];
        const skillData = isNew 
            ? { name: '', multiplier: 100.0, attribute: 'atk', activation_types: [], damage_types: [], concerto_energy: 0 }
            : skills[index];

        // ここでスキル編集用のモーダルを表示する
        // 今回は簡略化のため、いくつかの主要な項目だけを編集できるようにする
        const newName = prompt("スキル名を入力:", skillData.name);
        if (newName === null) return; // キャンセルされた
        
        const newMultiplier = prompt("スキル倍率(%)を入力:", skillData.multiplier);
        if (newMultiplier === null) return;

        try {
            const updatedSkill = { ...skillData, name: newName, multiplier: parseFloat(newMultiplier) };
            
            if (isNew) {
                skills.push(updatedSkill);
            } else {
                skills[index] = updatedSkill;
            }
            this._characterData.skills = skills;
            this.renderSkillsTab(); // UIを再描画
        } catch(e) {
            await customModals.alert("入力エラー", "倍率は数値で入力してください。");
        }
    },

    async _deleteSkill(index) {
        const skills = this._characterData.skills || [];
        if (index < 0 || index >= skills.length) return;

        const confirmed = await customModals.confirm("削除確認", `スキル '${skills[index].name}' を本当に削除しますか？`);
        if (confirmed) {
            skills.splice(index, 1);
            this._characterData.skills = skills;
            this.renderSkillsTab();
        }
    },

    renderBuffsTab() {
        const content = document.getElementById('char-editor-tab-content');
        content.innerHTML = `<p class="placeholder-text">固有バフの編集は現在開発中です。</p>`;
    },
    
    renderConstellationsTab() {
        const content = document.getElementById('char-editor-tab-content');
        content.innerHTML = `<p class="placeholder-text">凸効果の編集は現在開発中です。</p>`;
    },

    _onSave() {
        // フォームからデータを収集して _characterData を更新
        this._characterData.name = document.getElementById('char-editor-name').value;
        this._characterData.yomigana = document.getElementById('char-editor-yomigana').value;
        this._characterData.rarity = document.getElementById('char-editor-rarity').value;
        this._characterData.attribute = document.getElementById('char-editor-attribute').value;
        this._characterData.weapon_type = document.getElementById('char-editor-weapon_type').value;
        this._characterData.base_hp = parseFloat(document.getElementById('char-editor-base_hp').value);
        this._characterData.base_atk = parseFloat(document.getElementById('char-editor-base_atk').value);
        this._characterData.base_def = parseFloat(document.getElementById('char-editor-base_def').value);
        
        this._close(this._characterData);
    },
    
    _onCancel() { this._close(null); },

    _close(data) {
        document.getElementById('character-editor-overlay').classList.remove('visible');
        if (this._resolve) {
            this._resolve(data);
            this._resolve = null;
        }
    }
};

// -----------------------------------------------------------------------------
// メインアプリケーションロジック
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {

    // --- グローバル状態変数 ---
    let pyodide = null;
    let calculatorModule = null;
    let recalculateHelper = null;
    let exportersModule = null;
    let graphHelper = null;
    let currentDataType = 'characters'; // どのデータタブを選択しているか

    let appState = {
        team_builds: [],
        rotation_initial: [],
        rotation_loop: [],
        currentRotationView: 'initial'
    };
    
    const GAME_DATA = {
        ECHO_DATA: { "main_stats": { "4": [{ "name": "HP%", "value": 33, "key": "hp_percent" }, { "name": "攻撃力%", "value": 33, "key": "atk_percent" }, { "name": "防御力%", "value": 41.5, "key": "def_percent" }, { "name": "クリティカル率", "value": 22, "key": "crit_rate" }, { "name": "クリティカルダメージ", "value": 44, "key": "crit_damage" }, { "name": "治療効果アップ", "value": 26.4, "key": "heal_bonus" }], "3": [{ "name": "気動ダメージアップ", "value": 30, "key": "aero_dmg_up" }, { "name": "焦熱ダメージアップ", "value": 30, "key": "fusion_dmg_up" }, { "name": "電導ダメージアップ", "value": 30, "key": "electro_dmg_up" }, { "name": "凝縮ダメージアップ", "value": 30, "key": "glacio_dmg_up" }, { "name": "消滅ダメージアップ", "value": 30, "key": "havoc_dmg_up" }, { "name": "回折ダメージアップ", "value": 30, "key": "spectro_dmg_up" }, { "name": "共鳴効率", "value": 32, "key": "resonance_efficiency" }, { "name": "攻撃力%", "value": 30, "key": "atk_percent" }, { "name": "HP%", "value": 30, "key": "hp_percent" }, { "name": "防御力%", "value": 38, "key": "def_percent" }], "1": [{ "name": "HP%", "value": 22.8, "key": "hp_percent" }, { "name": "攻撃力%", "value": 18, "key": "atk_percent" }, { "name": "防御力%", "value": 18, "key": "def_percent" }] }, "fixed_main_stats": { "4": { "name": "攻撃力(数値)", "value": 150, "key": "atk_flat" }, "3": { "name": "攻撃力(数値)", "value": 100, "key": "atk_flat" }, "1": { "name": "HP(数値)", "value": 1520, "key": "hp_flat" } }, "sub_stat_values": { "HP%": { "key": "hp_percent", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] }, "攻撃力%": { "key": "atk_percent", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] }, "防御力%": { "key": "def_percent", "values": [8.1, 9, 10, 10.9, 11.8, 12.8, 13.6, 14.7] }, "クリティカル率": { "key": "crit_rate", "values": [6.3, 6.9, 7.5, 8.1, 8.7, 9.3, 9.9, 10.5] }, "クリティカルダメージ": { "key": "crit_damage", "values": [12.6, 13.8, 15, 16.2, 17.4, 18.6, 19.8, 21] }, "HP(数値)": { "key": "hp_flat", "values": [320, 360, 390, 430, 470, 510, 540, 580] }, "攻撃力(数値)": { "key": "atk_flat", "values": [30, 30, 40, 40, 50, 50, 60, 60] }, "防御力(数値)": { "key": "def_flat", "values": [40, 40, 50, 50, 60, 60, 70, 70] }, "共鳴効率": { "key": "resonance_efficiency", "values": [6.8, 7.6, 8.4, 9.2, 10, 10.8, 11.6, 12.4] }, "通常攻撃ダメージアップ": { "key": "normal_attack_dmg_up", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] }, "重撃ダメージアップ": { "key": "heavy_attack_dmg_up", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] }, "共鳴スキルダメージアップ": { "key": "resonance_skill_dmg_up", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] }, "共鳴解放ダメージアップ": { "key": "resonance_liberation_dmg_up", "values": [6.4, 7.1, 7.9, 8.6, 9.4, 10.1, 10.9, 11.6] } } },
        ECHO_SUB_STAT_TYPES: ["HP%", "攻撃力%", "防御力%", "クリティカル率", "クリティカルダメージ", "HP(数値)", "攻撃力(数値)", "防御力(数値)", "共鳴効率", "通常攻撃ダメージアップ", "重撃ダメージアップ", "共鳴スキルダメージアップ", "共鳴解放ダメージアップ"],
        ABNORMAL_EFFECTS: ["騒光効果", "風蝕効果", "斉爆効果", "虚滅効果"]
    };

    // --- Pythonヘルパーコード ---
    const pythonRecalculateHelper = `
import copy
from collections import defaultdict
from calculator import apply_buffs, calculate_base_stats
from constants import (
    KEY_CHARACTER_NAME, KEY_SKILLS, KEY_BUFFS, KEY_CONSTELLATION, KEY_WEAPON_RANK,
    KEY_WEAPON_DATA, KEY_HARMONY1_DATA, KEY_HARMONY2_DATA, KEY_ECHO_SKILL_DATA,
    KEY_CHARACTER_DATA, KEY_ACTIVATION_TYPES, KEY_SKILL, KEY_TARGET, KEY_EFFECTS,
    KEY_CONCERTO_ENERGY, KEY_RESONANCE_ENERGY_REQUIRED, KEY_RESONANCE_ENERGY_GAIN_FLAT,
    KEY_RESONANCE_ENERGY_GAIN_SCALING, KEY_SKILL_DATA, ABNORMAL_EFFECTS
)

def _get_character_efficiency(character_name, base_raw, active_buffs, all_buffs, build):
    from calculator import apply_buffs
    if not build: return 100.0
    buffed_raw_stats = apply_buffs(base_raw, active_buffs, character_name, all_buffs, build.get("constellation", 0), build.get("weapon_rank", 1))
    return buffed_raw_stats.get("resonance_efficiency", 100.0)

def gather_all_data_for_builds(team_builds, all_game_data):
    all_buffs = {}
    all_skills = defaultdict(list)
    for build in team_builds:
        char_name = build.get("character_name")
        if not char_name: continue
        char_data = build.get("character_data", {})
        all_skills[char_name].extend(char_data.get("skills", []))
        for key, buff_data in char_data.get("buffs", {}).items():
            all_buffs[f"char_{char_name}_{key}"] = {**buff_data, "owner": char_name}
    return all_buffs, dict(all_skills)

def recalculate_rotation_state(team_builds, rotation_initial, rotation_loop, all_game_data):
    if not team_builds: return {"initial": [], "loop": []}

    all_buffs, _ = gather_all_data_for_builds(team_builds, all_game_data)
    team_stats_cache = {b[KEY_CHARACTER_NAME]: calculate_base_stats(b) for b in team_builds if b.get(KEY_CHARACTER_NAME)}
    
    all_actions = rotation_initial + rotation_loop
    active_buffs_carry_over = {}
    char_concerto_energy = defaultdict(float)
    char_resonance_energy = defaultdict(float)
    team_char_names = {b[KEY_CHARACTER_NAME] for b in team_builds}

    for action in all_actions:
        current_char_name = action.get("character")
        build = next((b for b in team_builds if b.get(KEY_CHARACTER_NAME) == current_char_name), None)
        if not build or not current_char_name in team_stats_cache: continue
        
        _, base_raw, _ = team_stats_cache[current_char_name]
        skill_data = action.get(KEY_SKILL_DATA, {}) or {}
        activation_types = skill_data.get(KEY_ACTIVATION_TYPES, [])
        
        active_persistent_buffs = active_buffs_carry_over.copy()
        action['active_buffs'] = active_persistent_buffs
        
        calculated_concerto_gain = skill_data.get(KEY_CONCERTO_ENERGY, 0)
        char_concerto_energy[current_char_name] += calculated_concerto_gain
        action['concerto_energy_total'] = char_concerto_energy[current_char_name]
        
        executor_efficiency = _get_character_efficiency(current_char_name, base_raw, active_persistent_buffs, all_buffs, build)
        gain_flat = skill_data.get(KEY_RESONANCE_ENERGY_GAIN_FLAT, 0)
        gain_scaling = skill_data.get(KEY_RESONANCE_ENERGY_GAIN_SCALING, 0)
        calculated_resonance_gain = (gain_scaling * (executor_efficiency / 100.0)) + gain_flat
        char_resonance_energy[current_char_name] += calculated_resonance_gain
        max_resonance = build.get(KEY_CHARACTER_DATA, {}).get(KEY_RESONANCE_ENERGY_REQUIRED, 1)
        char_resonance_energy[current_char_name] = min(char_resonance_energy[current_char_name], max_resonance)
        action['resonance_energy_total'] = char_resonance_energy[current_char_name]
        action['resonance_energy_gain'] = calculated_resonance_gain
        
        active_buffs_carry_over = active_persistent_buffs.copy()

    initial_len = len(rotation_initial)
    return {"initial": all_actions[:initial_len], "loop": all_actions[initial_len:]}
`;

    const pythonGraphHelper = `
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import os
from pyodide.http import pyfetch
import matplotlib.font_manager as fm

# 非同期関数として定義
async def setup_japanese_font():
    font_path = '/home/pyodide/NotoSansJP-VariableFont_wght.ttf'
    
    if not os.path.exists(font_path):
        try:
            response = await pyfetch("assets/NotoSansJP-VariableFont_wght.ttf")
            with open(font_path, "wb") as f:
                f.write(await response.bytes())
            fm.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = 'Noto Sans JP'
        except Exception as e:
            print(f"日本語フォントの読み込みに失敗: {e}")
            # フォールバック
            plt.rcParams['font.family'] = 'sans-serif'
    
    plt.rcParams['axes.unicode_minus'] = False

# こちらも非同期関数として定義
async def generate_graph(results, theme_colors):
    await setup_japanese_font()
    
    initial_log = results['initial_phase']['log']
    loop_log = results['loop_phase']['log']
    
    if not initial_log and not loop_log:
        return None

    full_log = initial_log + loop_log * 5
    if not full_log: return None

    time_points = np.arange(1, len(full_log) + 1) * 1.5 # 仮で1アクション1.5秒
    cumulative_damage = np.cumsum([log['damage'] for log in full_log])
    dps = cumulative_damage / time_points

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.set_facecolor(theme_colors['surface'])
    ax.set_facecolor(theme_colors['background'])

    ax.plot(time_points, dps, color=theme_colors['primary'], marker='o', markersize=3)

    ax.set_title("DPSの推移", color=theme_colors['text_primary'])
    ax.set_xlabel("時間 (秒)", color=theme_colors['text_primary'])
    ax.set_ylabel("DPS", color=theme_colors['text_primary'])
    ax.tick_params(colors=theme_colors['text_secondary'])
    for spine in ax.spines.values():
        spine.set_edgecolor(theme_colors['border'])
    ax.grid(True, color=theme_colors['border'], linestyle='--', linewidth=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    return base64.b64encode(buf.read()).decode('utf-8')
`;

    // --- 初期化関数 ---
    async function initializePyodide() {
        showStatus("Pyodideを初期化中...");
        pyodide = await loadPyodide();
        showStatus("Pythonライブラリ(numpy, matplotlib)を読み込み中...");
        await pyodide.loadPackage(["numpy", "matplotlib", "pillow"]);

        showStatus("Pythonモジュールを読み込み中...");
        const [calcCode, constCode, appTypesCode, exportersCode, guiWidgetsCode] = await Promise.all([
            fetch('./calculator.py').then(res => res.text()),
            fetch('./constants.py').then(res => res.text()),
            fetch('./app_types.py').then(res => res.text()),
            fetch('./exporters.py').then(res => res.text()),
            fetch('./gui_widgets.py').then(res => res.text())
        ]);
        pyodide.FS.writeFile("app_types.py", appTypesCode, { encoding: "utf8" });
        pyodide.FS.writeFile("constants.py", constCode, { encoding: "utf8" });
        pyodide.FS.writeFile("gui_widgets.py", guiWidgetsCode, { encoding: "utf8" });
        pyodide.FS.writeFile("calculator.py", calcCode, { encoding: "utf8" });
        pyodide.FS.writeFile("exporters.py", exportersCode, { encoding: "utf8" });

        pyodide.FS.writeFile("recalculate_helper.py", pythonRecalculateHelper, { encoding: "utf8" });
        pyodide.FS.writeFile("graph_helper.py", pythonGraphHelper, { encoding: "utf8" });

        pyodide.runPython(`
            import app_types
            import constants
            import gui_widgets
            import calculator
            import exporters
            import recalculate_helper
            import graph_helper
        `);

        calculatorModule = pyodide.pyimport("calculator");
        exportersModule = pyodide.pyimport("exporters");
        recalculateHelper = pyodide.pyimport("recalculate_helper");
        graphHelper = pyodide.pyimport("graph_helper");

        showStatus("準備完了！", true);
    }
    
    // --- UI表示関数 ---
    function showFrame(frameKey) {
        document.querySelectorAll('.content-frame').forEach(f => f.classList.remove('visible'));
        document.querySelectorAll('.nav-button').forEach(b => b.classList.remove('active'));
        document.getElementById(`frame-${frameKey}`).classList.add('visible');
        document.getElementById(`btn-${frameKey}`).classList.add('active');
        
        if (frameKey === 'data_editor') {
            if (dataManager.isInitialized) {
                renderDataEditorTabs();
                renderDataList(currentDataType);
            } else {
                const tabContainer = document.getElementById('data-editor-tabs');
                const listContainer = document.getElementById('data-list-container');
                tabContainer.innerHTML = '';
                listContainer.innerHTML = '<p class="placeholder-text">「データフォルダを選択」ボタンからデータを読み込んでください。</p>';
            }
        }
    }

    // --- データ管理画面 (Data Editor) ロジック ---
    function renderDataEditorTabs() {
        const tabContainer = document.getElementById('data-editor-tabs');
        tabContainer.innerHTML = '';
        const dataTypesJp = {
            "characters": "キャラクター", "weapons": "武器", "harmony_effects": "ハーモニー",
            "echo_skills": "音骸スキル", "builds": "ビルド", "scenarios": "シナリオ", "stage_effects": "ステージ効果"
        };

        dataManager.dataKeys.forEach(key => {
            const button = document.createElement('button');
            button.className = 'tab-button';
            button.dataset.type = key;
            button.textContent = dataTypesJp[key] || key;
            if (key === currentDataType) {
                button.classList.add('active');
            }
            tabContainer.appendChild(button);
        });
    }

    function renderDataList(dataType) {
        const listContainer = document.getElementById('data-list-container');
        listContainer.innerHTML = '';
        const data = dataManager.getData(dataType, {});

        for (const itemName in data) {
            const row = document.createElement('div');
            row.className = 'data-item-row';
            row.innerHTML = `
                <span class="data-item-name">${itemName}</span>
                <div class="data-item-actions">
                    <button data-action="edit" data-key="${dataType}" data-name="${itemName}" title="編集">✏️</button>
                    <button data-action="delete" data-key="${dataType}" data-name="${itemName}" title="削除">🗑️</button>
                </div>
            `;
            listContainer.appendChild(row);
        }
    }

    // --- キャラクター準備画面 (Character Setup) ロジック ---
    function createCharacterPanels() {
        const container = document.querySelector('.team-container');
        if (!container) return;
        container.innerHTML = '';

        for (let i = 0; i < 3; i++) {
            const panel = document.createElement('div');
            panel.className = 'character-panel';
            panel.dataset.panelIndex = i;
            panel.innerHTML = `
                <div class="panel-header"><div class="char-image"></div><h2 class="panel-title">キャラクター ${i + 1}</h2></div>
                <div class="item-images"><div class="item-image"></div><div class="item-image"></div><div class="item-image"></div><div class="item-image"></div></div>
                <div class="build-details">
                    <label>キャラクター:</label><button class="selector-button" data-type="character">キャラクターを選択</button>
                    <label>武器:</label><div class="input-row"><button class="selector-button" data-type="weapon" disabled>武器を選択</button><label class="switch"><input type="checkbox"><span class="slider"></span></label></div>
                    <label>ビルド:</label><select data-type="build"><option>ビルド読込</option></select>
                    <label>凸数:</label><select data-type="constellation">${[...Array(7).keys()].map(n => `<option>${n}</option>`).join('')}</select>
                    <label>武器ランク:</label><select data-type="rank">${[...Array(5).keys()].map(n => `<option>${n + 1}</option>`).join('')}</select>
                    <label>ハーモニー①:</label><select data-type="harmony1"><option></option></select>
                    <label>ハーモニー②:</label><select data-type="harmony2"><option></option></select>
                    <label>音骸スキル:</label><select data-type="echo_skill"><option></option></select>
                </div>
                <div class="echo-inputs-container" id="echo-container-${i}"></div>
                <textarea class="status-display" id="status-display-${i}" readonly>ステータスはPythonモジュールの読み込み後に計算されます...</textarea>
                <button class="save-build-button">💾 現在の装備をビルドとして保存</button>
            `;
            container.appendChild(panel);

            const echoContainer = document.getElementById(`echo-container-${i}`);
            echoContainer.innerHTML = [...Array(5).keys()].map(j => `
                <div class="echo-widget" data-echo-index="${j}">
                    <div class="echo-top-row">
                        <span class="echo-title">音骸 ${j + 1}</span><label class="echo-label">Cost:</label>
                        <select class="echo-cost-menu" id="echo-cost-${i}-${j}"><option>4</option><option>3</option><option>1</option></select>
                    </div>
                    <div class="echo-main-stat-row">
                        <label class="echo-label">Main:</label><select id="echo-main-stat-${i}-${j}" style="flex-grow:1;"></select><label class="switch"><input type="checkbox"><span class="slider"></span></label>
                    </div>
                    <div id="echo-fixed-stat-${i}-${j}" class="echo-fixed-stat"></div>
                    <div class="echo-sub-stats-grid">
                        ${[...Array(5).keys()].map(k => `
                        <div class="echo-sub-stat-row">
                            <select id="echo-sub-type-${i}-${j}-${k}"><option value="">- サブステ${k + 1} -</option>${GAME_DATA.ECHO_SUB_STAT_TYPES.map(t => `<option value="${t}">${t}</option>`).join('')}</select>
                            <select id="echo-sub-value-${i}-${j}-${k}" style="width:80px;"></select><label class="switch"><input type="checkbox"><span class="slider"></span></label>
                        </div>`).join('')}
                    </div>
                </div>
            `).join('');

            createEchoInputWidget(i);
        }
    }
    
    function createEchoInputWidget(panelIndex) {
        for (let j = 0; j < 5; j++) {
            const costVal = document.getElementById(`echo-cost-${panelIndex}-${j}`).value;
            const mainStatMenu = document.getElementById(`echo-main-stat-${panelIndex}-${j}`);
            const currentMainStat = mainStatMenu.value;
            const mainStatOptions = GAME_DATA.ECHO_DATA.main_stats[costVal] || [];
            mainStatMenu.innerHTML = mainStatOptions.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
            if (mainStatOptions.some(s => s.name === currentMainStat)) {
                mainStatMenu.value = currentMainStat;
            } else if (mainStatOptions.length > 0) {
                mainStatMenu.value = mainStatOptions[0].name;
            }

            const fixedStatLabel = document.getElementById(`echo-fixed-stat-${panelIndex}-${j}`);
            const fixedStat = GAME_DATA.ECHO_DATA.fixed_main_stats[costVal];
            fixedStatLabel.textContent = fixedStat ? `固定: ${fixedStat.name} +${fixedStat.value}` : '';

            for (let k = 0; k < 5; k++) {
                const typeMenu = document.getElementById(`echo-sub-type-${panelIndex}-${j}-${k}`);
                const valueMenu = document.getElementById(`echo-sub-value-${panelIndex}-${j}-${k}`);
                const currentSubType = typeMenu.value;
                const subValueOptions = GAME_DATA.ECHO_DATA.sub_stat_values[currentSubType]?.values || [];
                const currentValue = valueMenu.value;
                valueMenu.innerHTML = subValueOptions.map(v => `<option value="${v}">${v}</option>`).join('');
                if (subValueOptions.includes(parseFloat(currentValue))) {
                    valueMenu.value = currentValue;
                }
            }
        }
        updatePanelStats(panelIndex);
    }
    
    async function updateUIWithOptions() {
        const usernameInput = document.getElementById('username');
        usernameInput.value = dataManager.config.username || '';
        usernameInput.addEventListener('input', (e) => {
            dataManager.config.username = e.target.value;
        });

        document.querySelectorAll('.character-panel').forEach(panel => {
            const harmonies = Object.keys(dataManager.getData('harmony_effects', {}));
            const echoSkills = Object.keys(dataManager.getData('echo_skills', {}));

            const harmonySelect1 = panel.querySelector('[data-type="harmony1"]');
            const harmonySelect2 = panel.querySelector('[data-type="harmony2"]');
            const echoSkillSelect = panel.querySelector('[data-type="echo_skill"]');

            [harmonySelect1, harmonySelect2].forEach(sel => {
                sel.innerHTML = '<option value=""></option>' + harmonies.map(h => `<option value="${h}">${h}</option>`).join('');
            });
            echoSkillSelect.innerHTML = '<option value=""></option>' + echoSkills.map(es => `<option value="${es}">${es}</option>`).join('');
        });
    }

    async function onCharacterSelect(panelIndex) {
        const charactersWithOptions = Object.values(dataManager.getData('characters', {}))
            .map(c => ({ name: c.name, yomigana: c.yomigana || '', attribute: c.attribute }));

        const selectedCharName = await searchablePopup.open("キャラクターを選択", charactersWithOptions);

        if (selectedCharName) {
            const panel = document.querySelector(`.character-panel[data-panel-index="${panelIndex}"]`);
            panel.querySelector('[data-type="character"]').textContent = selectedCharName;

            const charData = dataManager.getData('characters', {})[selectedCharName];
            const charImageEl = panel.querySelector('.char-image');
            if (charData && charData.image_file) {
                charImageEl.style.backgroundImage = `url(images/characters/${charData.image_file})`;
                charImageEl.style.backgroundSize = 'cover';
            } else {
                charImageEl.style.backgroundImage = 'none';
            }

            const weaponButton = panel.querySelector('[data-type="weapon"]');
            weaponButton.disabled = false;
            weaponButton.textContent = '武器を選択';

            const buildSelect = panel.querySelector('[data-type="build"]');
            const allBuilds = dataManager.getData('builds', {});
            const charBuilds = Object.keys(allBuilds).filter(bName => allBuilds[bName].character_name === selectedCharName);
            buildSelect.innerHTML = '<option value="">ビルド読込</option>' + charBuilds.map(b => `<option value="${b}">${b}</option>`).join('');

            updatePanelStats(panelIndex);
        }
    }

    async function onWeaponSelect(panelIndex) {
        const panel = document.querySelector(`.character-panel[data-panel-index="${panelIndex}"]`);
        const charName = panel.querySelector('[data-type="character"]').textContent;
        if (!charName || charName === 'キャラクターを選択') return;

        const charData = dataManager.getData('characters', {})[charName];
        if (!charData) return;

        const weaponType = charData.weapon_type;
        const weapons = Object.values(dataManager.getData('weapons', {}))
            .filter(w => w.weapon_type === weaponType)
            .map(w => ({ name: w.name }));

        const selectedWeapon = await searchablePopup.open(`${weaponType} を選択`, weapons);
        if (selectedWeapon) {
            panel.querySelector('[data-type="weapon"]').textContent = selectedWeapon;

            const weaponData = dataManager.getData('weapons', {})[selectedWeapon];
            const weaponImageEl = panel.querySelector('.item-images .item-image:nth-child(1)');
            if (weaponData && weaponData.image_file) {
                weaponImageEl.style.backgroundImage = `url(images/weapons/${weaponData.image_file})`;
                weaponImageEl.style.backgroundSize = 'cover';
            } else {
                weaponImageEl.style.backgroundImage = 'none';
            }
            updatePanelStats(panelIndex);
        }
    }

    function loadBuildToPanel(panelIndex, buildName) {
        if (!buildName) return;
        const buildData = dataManager.getData('builds', {})[buildName];
        if (!buildData) return;

        const panel = document.querySelector(`.character-panel[data-panel-index="${panelIndex}"]`);
        const charData = dataManager.getData('characters', {})[buildData.character_name];
        const weaponData = dataManager.getData('weapons', {})[buildData.weapon_name];

        const charImageEl = panel.querySelector('.char-image');
        if (charData && charData.image_file) {
            charImageEl.style.backgroundImage = `url(images/characters/${charData.image_file})`;
            charImageEl.style.backgroundSize = 'cover';
        } else {
            charImageEl.style.backgroundImage = 'none';
        }

        const weaponImageEl = panel.querySelector('.item-images .item-image:nth-child(1)');
        if (weaponData && weaponData.image_file) {
            weaponImageEl.style.backgroundImage = `url(images/weapons/${weaponData.image_file})`;
            weaponImageEl.style.backgroundSize = 'cover';
        } else {
            weaponImageEl.style.backgroundImage = 'none';
        }

        panel.querySelector('[data-type="character"]').textContent = buildData.character_name || 'キャラクターを選択';
        panel.querySelector('[data-type="weapon"]').textContent = buildData.weapon_name || '武器を選択';
        panel.querySelector('[data-type="constellation"]').value = buildData.constellation ?? 0;
        panel.querySelector('[data-type="rank"]').value = buildData.weapon_rank ?? 1;
        panel.querySelector('[data-type="harmony1"]').value = buildData.harmony1_name || '';
        panel.querySelector('[data-type="harmony2"]').value = buildData.harmony2_name || '';
        panel.querySelector('[data-type="echo_skill"]').value = buildData.echo_skill_name || '';

        const echoList = buildData.echo_list || [];
        for (let i = 0; i < 5; i++) {
            const echoData = echoList[i];

            if (echoData) {
                const costSelect = document.getElementById(`echo-cost-${panelIndex}-${i}`);
                costSelect.value = echoData.cost;

                const mainStatMenu = document.getElementById(`echo-main-stat-${panelIndex}-${i}`);
                const mainStatOptions = GAME_DATA.ECHO_DATA.main_stats[echoData.cost] || [];
                mainStatMenu.innerHTML = mainStatOptions.map(s => `<option value="${s.name}">${s.name}</option>`).join('');
                mainStatMenu.value = echoData.main_stat?.name || '';

                const fixedStatLabel = document.getElementById(`echo-fixed-stat-${panelIndex}-${i}`);
                const fixedStat = GAME_DATA.ECHO_DATA.fixed_main_stats[echoData.cost];
                fixedStatLabel.textContent = fixedStat ? `固定: ${fixedStat.name} +${fixedStat.value}` : '';

                const subStats = echoData.sub_stats || [];
                for (let k = 0; k < 5; k++) {
                    const subStatData = subStats[k];
                    const typeMenu = document.getElementById(`echo-sub-type-${panelIndex}-${i}-${k}`);
                    const valueMenu = document.getElementById(`echo-sub-value-${panelIndex}-${i}-${k}`);

                    if (subStatData) {
                        typeMenu.value = subStatData.name || '';
                        const subValueOptions = GAME_DATA.ECHO_DATA.sub_stat_values[subStatData.name]?.values || [];
                        valueMenu.innerHTML = subValueOptions.map(v => `<option value="${v}">${v}</option>`).join('');
                        valueMenu.value = subStatData.value || '';
                    } else {
                        typeMenu.value = '';
                        valueMenu.innerHTML = '';
                    }
                }
            } else {
                document.getElementById(`echo-cost-${panelIndex}-${i}`).value = '4';
            }
        }
        updatePanelStats(panelIndex);
    }

    async function saveBuildFromPanel(panelIndex) {
        const buildName = await customModals.prompt("ビルドを保存", "ビルド名を入力してください:");

        if (!buildName) return;

        const allBuilds = dataManager.getData('builds', {});
        if (allBuilds[buildName]) {
            const overwrite = await customModals.confirm(
                "上書き確認",
                `ビルド名'${buildName}'は既に存在します。上書きしますか？`
            );
            if (!overwrite) return;
        }

        const currentBuild = getBuildFromPanel(panelIndex);
        if (!currentBuild) {
            await customModals.alert("保存エラー", "キャラクターが選択されていないため、ビルドを保存できません。");
            return;
        }

        const buildToSave = {};
        for (const key in currentBuild) {
            if (!key.endsWith('_data')) {
                buildToSave[key] = currentBuild[key];
            }
        }
        buildToSave.character_name = currentBuild.character_name;

        allBuilds[buildName] = buildToSave;
        const success = await dataManager.saveData('builds', allBuilds);

        if (success) {
            await customModals.alert("成功", `ビルド'${buildName}'を保存しました。`);
            const panel = document.querySelector(`.character-panel[data-panel-index="${panelIndex}"]`);
            const buildSelect = panel.querySelector('[data-type="build"]');
            const charBuilds = Object.keys(allBuilds).filter(bName => allBuilds[bName].character_name === currentBuild.character_name);
            buildSelect.innerHTML = '<option value="">ビルド読込</option>' + charBuilds.map(b => `<option value="${b}">${b}</option>`).join('');
            buildSelect.value = buildName;
        } else {
            await customModals.alert("失敗", "ビルドの保存に失敗しました。");
        }
    }

    function getBuildFromPanel(panelIndex) {
        const panel = document.querySelector(`.character-panel[data-panel-index="${panelIndex}"]`);
        if (!panel) return null;

        const charName = panel.querySelector('[data-type="character"]').textContent;
        if (!charName || charName === 'キャラクターを選択') {
            return null;
        }

        const weaponName = panel.querySelector('[data-type="weapon"]').textContent;
        const charData = dataManager.getData('characters', {})[charName] || {};
        const weaponData = dataManager.getData('weapons', {})[weaponName] || {};
        const harmony1Name = panel.querySelector('[data-type="harmony1"]').value;
        const harmony2Name = panel.querySelector('[data-type="harmony2"]').value;
        const echoSkillName = panel.querySelector('[data-type="echo_skill"]').value;
        const harmony1Data = dataManager.getData('harmony_effects', {})[harmony1Name] || {};
        const harmony2Data = dataManager.getData('harmony_effects', {})[harmony2Name] || {};
        const echoSkillData = dataManager.getData('echo_skills', {})[echoSkillName] || {};

        const echoList = [];
        for (let j = 0; j < 5; j++) {
            const cost = document.getElementById(`echo-cost-${panelIndex}-${j}`).value;
            const mainStatName = document.getElementById(`echo-main-stat-${panelIndex}-${j}`).value;
            const mainStatInfo = GAME_DATA.ECHO_DATA.main_stats[cost]?.find(s => s.name === mainStatName) || null;

            const subStats = [];
            for (let k = 0; k < 5; k++) {
                const type = document.getElementById(`echo-sub-type-${panelIndex}-${j}-${k}`).value;
                const value = document.getElementById(`echo-sub-value-${panelIndex}-${j}-${k}`).value;
                if (type && value) {
                    const key = GAME_DATA.ECHO_DATA.sub_stat_values[type]?.key;
                    subStats.push({ name: type, value: parseFloat(value), key: key });
                }
            }
            echoList.push({
                name: "",
                cost: parseInt(cost),
                main_stat: mainStatInfo,
                sub_stats: subStats
            });
        }

        return {
            character_name: charName,
            character_data: charData,
            weapon_name: weaponName,
            weapon_data: weaponData,
            constellation: parseInt(panel.querySelector('[data-type="constellation"]').value, 10),
            weapon_rank: parseInt(panel.querySelector('[data-type="rank"]').value, 10),
            harmony1_name: harmony1Name,
            harmony1_data: harmony1Data,
            harmony2_name: harmony2Name,
            harmony2_data: harmony2Data,
            echo_list: echoList,
            echo_skill_name: echoSkillName,
            echo_skill_data: echoSkillData
        };
    }

    async function updatePanelStats(panelIndex) {
        if (!pyodide || !calculatorModule) return;
        const statusDisplay = document.getElementById(`status-display-${panelIndex}`);
        const buildData = getBuildFromPanel(panelIndex);

        if (!buildData) {
            statusDisplay.value = "キャラクターを選択してください...";
            return;
        }

        try {
            const buildProxy = pyodide.toPy(buildData);
            const resultProxy = calculatorModule.calculate_base_stats(buildProxy);
            const final_stats = resultProxy[0].toJs();
            resultProxy.destroy();
            buildProxy.destroy();

            let displayText = '';
            for (const [key, value] of final_stats) {
                if (['HP', '攻撃力', '防御力'].includes(key)) {
                    displayText += `${key.padEnd(10)}: ${Math.round(value).toLocaleString()}\n`;
                } else if (value > 0) {
                    displayText += `${key.padEnd(10)}: ${value.toFixed(1)}%\n`;
                }
            }
            statusDisplay.value = displayText;

        } catch (error) {
            statusDisplay.value = `計算エラー:\n${error}`;
            console.error(error);
        }
    }
    
    // --- ローテーション画面 (Rotation Editor) ロジック ---
    function setupRotationEditor() {
        const selectorPanel = document.getElementById('skill-selector-panel');
        selectorPanel.innerHTML = '';

        appState.team_builds.forEach(build => {
            const charName = build.character_name;
            const charData = build.character_data;

            const column = document.createElement('div');
            column.className = 'skill-column';

            const header = document.createElement('div');
            header.className = 'skill-column-header';
            header.textContent = charName;
            column.appendChild(header);

            (charData.skills || []).forEach(skill => {
                const button = document.createElement('button');
                button.className = 'skill-button';
                button.textContent = skill.name;
                button.addEventListener('click', () => addAction(charName, skill));
                column.appendChild(button);
            });
            selectorPanel.appendChild(column);
        });
        renderRotationList();
    }
    
    function addAction(charName, skill) {
        const action = {
            character: charName,
            skill: skill.name,
            skill_data: skill,
        };
        if (appState.currentRotationView === 'initial') {
            appState.rotation_initial.push(action);
        } else {
            appState.rotation_loop.push(action);
        }
        recalculateAndRender();
    }

    function renderRotationList() {
        const listId = appState.currentRotationView === 'initial' ? 'initial-rotation-list' : 'loop-rotation-list';
        const listContainer = document.getElementById(listId);
        const rotationData = appState[appState.currentRotationView === 'initial' ? 'rotation_initial' : 'rotation_loop'];
        listContainer.innerHTML = '';

        (rotationData || []).forEach((action, index) => {
            const row = document.createElement('div');
            row.className = 'action-row';

            const concertoTotal = action.concerto_energy_total || 0;
            const resonanceGain = action.resonance_energy_gain || 0;
            const resonanceTotal = action.resonance_energy_total || 0;
            const activeBuffs = action.active_buffs ? Object.keys(action.active_buffs).length : 0;

            row.innerHTML = `
                <div class="action-row-top">
                    <div class="action-char-icon"></div>
                    <span class="action-name">${action.character}: ${action.skill}</span>
                    <button class="action-delete-btn" data-index="${index}">🗑️</button>
                </div>
                <div class="action-row-bottom">
                    <div class="energy-display"><span class="energy-label">協奏 E</span><span class="energy-value">${concertoTotal.toFixed(1)}</span></div>
                    <div class="energy-display"><span class="energy-label">共鳴 E (+${resonanceGain.toFixed(1)})</span><span class="energy-value">${resonanceTotal.toFixed(1)}</span></div>
                    <div class="buff-list">${[...Array(activeBuffs)].map(() => `<div class="buff-icon"></div>`).join('')}</div>
                </div>
            `;
            listContainer.appendChild(row);
        });
    }

    async function recalculateAndRender() {
        if (!pyodide || !recalculateHelper || !dataManager.isInitialized) return;

        const teamCharacterNames = appState.team_builds.map(b => b.character_name);
        if (teamCharacterNames.length === 0) {
            console.warn("recalculateAndRender: No characters in team_builds.");
            return;
        }

        const fullTeamBuilds = appState.team_builds.map(build => {
            const charData = dataManager.getData('characters', {})[build.character_name] || {};
            const weaponData = dataManager.getData('weapons', {})[build.weapon_name] || {};
            const harmony1Data = dataManager.getData('harmony_effects', {})[build.harmony1_name] || {};
            const harmony2Data = dataManager.getData('harmony_effects', {})[build.harmony2_name] || {};
            const echoSkillData = dataManager.getData('echo_skills', {})[build.echo_skill_name] || {};

            return {
                ...build,
                character_data: charData,
                weapon_data: weaponData,
                harmony1_data: harmony1Data,
                harmony2_data: harmony2Data,
                echo_skill_data: echoSkillData
            };
        });

        const resultProxy = recalculateHelper.recalculate_rotation_state(
            pyodide.toPy(fullTeamBuilds),
            pyodide.toPy(appState.rotation_initial),
            pyodide.toPy(appState.rotation_loop),
            pyodide.toPy(dataManager.data)
        );
        const newRotations = resultProxy.toJs({ dict_converter: Object.fromEntries });
        resultProxy.destroy();

        appState.rotation_initial = newRotations.initial || [];
        appState.rotation_loop = newRotations.loop || [];

        renderRotationList();
    }

    // --- 計算結果画面 (Output View) ロジック ---
    async function runCalculationAndShowResults() {
        if (!pyodide || !calculatorModule) {
            alert("計算モジュールが初期化されていません。");
            return;
        }
        showStatus("最終ダメージ計算を実行中...");

        const resultProxy = calculatorModule.process_rotation(
            pyodide.toPy(appState.team_builds),
            pyodide.toPy(appState.rotation_initial),
            pyodide.toPy(appState.rotation_loop),
            pyodide.toPy({ level: 90 }),
            pyodide.toPy({}),
            "",
            null,
            pyodide.toPy([]),
            pyodide.toPy([])
        );
        const results = resultProxy.toJs({ dict_converter: Object.fromEntries });
        resultProxy.destroy();

        await renderOutputView(results);
        showStatus("計算完了！", true);
        showFrame('output_view');
    }

    async function renderOutputView(results) {
        const initial_phase = results.initial_phase;
        const loop_phase = results.loop_phase;

        if (!initial_phase || !loop_phase) {
            console.error("Calculation result is missing expected phases.", results);
            alert("計算結果の形式が正しくありません。");
            return;
        }

        const initialDamage = initial_phase.total_damage;
        const loopDamage = loop_phase.total_damage;
        const initialLog = initial_phase.log;

        const summaryContainer = document.getElementById('tab-content-summary');
        summaryContainer.innerHTML = `
            <h3>計算サマリー</h3>
            <p>初動ダメージ合計: ${initialDamage.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}</p>
            <p>ループダメージ合計 (1周): ${loopDamage.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}</p>
            <p>合計 (初動 + 5ループ): ${(initialDamage + loopDamage * 5).toLocaleString('ja-JP', { maximumFractionDigits: 0 })}</p>
        `;

        const graphPlaceholder = document.getElementById('graph-placeholder');
        graphPlaceholder.textContent = 'グラフを生成中...';

        const themeColors = {
            surface: '#1C243C', background: '#121828',
            primary: '#3B82F6', text_primary: '#F0F4FF',
            text_secondary: '#A8B5D1', border: '#3A476F'
        };

        const graphData = {
            initial_phase: { log: initialLog },
            loop_phase: { log: loop_phase.log }
        };

        const base64Image = await graphHelper.generate_graph(pyodide.toPy(graphData), pyodide.toPy(themeColors));

        if (base64Image) {
            graphPlaceholder.innerHTML = `<img src="data:image/png;base64,${base64Image}" alt="計算結果グラフ" style="max-width: 100%; height: auto;">`;
        } else {
            graphPlaceholder.textContent = 'グラフの生成に失敗しました。';
        }

        const detailsContainer = document.getElementById('tab-content-details');
        const logHtml = initialLog.map(log => `<p>${log.character}: ${log.skill} - ${log.damage.toFixed(0)}</p>`).join('');
        detailsContainer.innerHTML = logHtml;
    }

    // --- ユーティリティ ---
    function setupStatusDisplay() {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'pyodide-status';
        statusDiv.style.position = 'fixed';
        statusDiv.style.bottom = '10px';
        statusDiv.style.left = '10px';
        statusDiv.style.padding = '5px 10px';
        statusDiv.style.backgroundColor = 'var(--color-surface)';
        statusDiv.style.border = '1px solid var(--color-border)';
        statusDiv.style.borderRadius = '6px';
        statusDiv.style.fontSize = '12px';
        statusDiv.style.zIndex = '1000';
        statusDiv.style.opacity = '0';
        statusDiv.style.transition = 'opacity 0.5s';
        document.body.appendChild(statusDiv);
    }

    function showStatus(message, fadeOut = false) {
        const statusDiv = document.getElementById('pyodide-status');
        if (statusDiv) {
            statusDiv.textContent = message;
            statusDiv.style.opacity = '1';
            if (fadeOut) {
                setTimeout(() => { statusDiv.style.opacity = '0'; }, 3000);
            }
        }
    }
    
    function initializeUI() {
        const abnormalContainer = document.querySelector('.abnormal-effects');
        if (!abnormalContainer) return;
        abnormalContainer.innerHTML = abnormalContainer.firstElementChild.outerHTML;
        GAME_DATA.ABNORMAL_EFFECTS.forEach(effect => {
            const label = document.createElement('label');
            label.innerHTML = `<input type="checkbox" checked> ${effect}`;
            abnormalContainer.appendChild(label);
        });
    }

    // -----------------------------------------------------------------------------
    // イベントリスナーのセットアップ
    // -----------------------------------------------------------------------------
    setupStatusDisplay();
    createCharacterPanels();
    initializeUI();
    searchablePopup.setup();
    characterEditor.setup();

    // サイドバーナビゲーション
    document.querySelectorAll('.nav-button').forEach(b => b.addEventListener('click', (e) => showFrame(e.target.id.replace('btn-', ''))));
    document.getElementById('btn-exit').addEventListener('click', () => {
        if (confirm('アプリケーションを終了しますか？')) {
            alert('このタブを閉じてください。');
            window.close();
        }
    });

    // データフォルダ選択
    document.getElementById('select-data-folder-btn').addEventListener('click', async () => {
        const success = await dataManager.initialize();
        if (success) {
            await updateUIWithOptions();
            if (document.getElementById('frame-data_editor').classList.contains('visible')) {
                renderDataEditorTabs();
                renderDataList(currentDataType);
            }
        }
    });

    // キャラクター準備画面のイベント
    document.querySelector('.team-container').addEventListener('click', (e) => {
        const panel = e.target.closest('.character-panel');
        if (!panel) return;
        const panelIndex = panel.dataset.panelIndex;

        if (e.target.matches('[data-type="character"]')) onCharacterSelect(panelIndex);
        if (e.target.matches('[data-type="weapon"]')) onWeaponSelect(panelIndex);
        if (e.target.matches('.save-build-button')) saveBuildFromPanel(panelIndex);
    });
    
    document.querySelector('.team-container').addEventListener('change', (e) => {
        const panel = e.target.closest('.character-panel');
        if (panel) {
            const panelIndex = parseInt(panel.dataset.panelIndex, 10);
            if (e.target.matches('[data-type="build"]')) {
                loadBuildToPanel(panelIndex, e.target.value);
            } else {
                 createEchoInputWidget(panelIndex); // ビルド読込以外でも更新
            }
        }
    });
    
    document.getElementById('proceed-button').addEventListener('click', () => {
        appState.team_builds = [];
        for (let i = 0; i < 3; i++) {
            const build = getBuildFromPanel(i);
            if (build) {
                appState.team_builds.push(build);
            }
        }
        if (appState.team_builds.length === 0) {
            alert("キャラクターを1人以上設定してください。");
            return;
        }
        setupRotationEditor();
        showFrame('rotation_editor');
    });

    // ローテーション画面のイベント
    document.getElementById('tab-btn-initial').addEventListener('click', () => {
        appState.currentRotationView = 'initial';
        document.getElementById('tab-btn-initial').classList.add('active');
        document.getElementById('tab-btn-loop').classList.remove('active');
        document.getElementById('initial-rotation-list').classList.add('visible');
        document.getElementById('loop-rotation-list').classList.remove('visible');
    });
    document.getElementById('tab-btn-loop').addEventListener('click', () => {
        appState.currentRotationView = 'loop';
        document.getElementById('tab-btn-initial').classList.remove('active');
        document.getElementById('tab-btn-loop').classList.add('active');
        document.getElementById('initial-rotation-list').classList.remove('visible');
        document.getElementById('loop-rotation-list').classList.add('visible');
    });
    document.getElementById('rotation-editor-panel').addEventListener('click', e => {
        if (e.target.classList.contains('action-delete-btn')) {
            const index = parseInt(e.target.dataset.index, 10);
            const list = appState.currentRotationView === 'initial' ? appState.rotation_initial : appState.rotation_loop;
            if (list) list.splice(index, 1);
            recalculateAndRender();
        }
    });
    document.getElementById('run-calculation-btn').addEventListener('click', runCalculationAndShowResults);

    // 計算結果画面のイベント
    document.getElementById('output-tabs').addEventListener('click', (e) => {
        if (e.target.matches('.tab-button')) {
            const tabName = e.target.dataset.tab;
            document.querySelectorAll('#output-tabs .tab-button').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('visible'));
            document.getElementById(`tab-content-${tabName}`).classList.add('visible');
        }
    });

    // データ管理画面のイベント
    document.getElementById('data-editor-tabs').addEventListener('click', e => {
        if (e.target.matches('.tab-button')) {
            currentDataType = e.target.dataset.type;
            renderDataEditorTabs();
            renderDataList(currentDataType);
        }
    });
    
    document.getElementById('data-list-container').addEventListener('click', async e => {
        const button = e.target.closest('button');
        if (!button) return;
        const { action, key, name } = button.dataset;

        if (action === 'edit') {
            if (key === 'characters') {
                const data = dataManager.getData(key, {});
                const editedData = await characterEditor.open(name, data[name]);
                if (editedData) {
                    data[name] = editedData;
                    if (await dataManager.saveData(key, data)) {
                        await customModals.alert("成功", `'${name}' を保存しました。`);
                        renderDataList(key);
                    } else {
                        await customModals.alert("失敗", "データの保存に失敗しました。");
                    }
                }
            } else {
                await customModals.alert("未実装", "このデータタイプのエディタは現在開発中です。");
            }
        } else if (action === 'delete') {
            const confirmed = await customModals.confirm("削除確認", `'${name}' を本当に削除しますか？この操作は元に戻せません。`);
            if (confirmed) {
                const data = dataManager.getData(key, {});
                delete data[name];
                if (await dataManager.saveData(key, data)) {
                    await customModals.alert("成功", `'${name}' を削除しました。`);
                    renderDataList(key);
                } else {
                    await customModals.alert("失敗", "データの削除に失敗しました。");
                }
            }
        }
    });
    
    document.getElementById('add-new-item-btn').addEventListener('click', async () => {
        if (currentDataType !== 'characters') {
            await customModals.alert("未実装", "現在、キャラクターの新規追加のみサポートされています。");
            return;
        }

        const newItemName = await customModals.prompt("新規キャラクター", "新しいキャラクターの名前を入力してください:");
        if (!newItemName || !newItemName.trim()) return;

        const data = dataManager.getData(currentDataType, {});
        if (data[newItemName]) {
            await customModals.alert("エラー", `名前 '${newItemName}' は既に存在します。`);
            return;
        }

        const newDataTemplate = { name: newItemName, rarity: "★5", yomigana: "", base_hp: 0, base_atk: 0, base_def: 0, resonance_energy_required: 125, weapon_type: "", attribute: "", innate_stats: [], skills: [], buffs: {}, constellations: {}, image_file: "" };
        const newData = await characterEditor.open(null, newDataTemplate);

        if (newData) {
            data[newItemName] = newData;
            if (await dataManager.saveData(currentDataType, data)) {
                await customModals.alert("成功", `'${newItemName}' を追加しました。`);
                renderDataList(currentDataType);
            } else {
                await customModals.alert("失敗", "データの追加に失敗しました。");
            }
        }
    });
    
    // --- アプリケーション起動 ---
    showFrame('char_setup');
    await initializePyodide();

});